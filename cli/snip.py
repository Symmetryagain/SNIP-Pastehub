#!/usr/bin/env python3
"""snip - command line client for Snip Share.

Single file, Python 3.8+, standard library only.

Quick start:
  snip login --server http://HOST:8080 -u alice     # asks for password
  echo "hello" | snip push -t "greeting" --tag Note  # prints the new post id
  snip list                                          # your own posts
  snip show 3f2a                                     # raw content (id prefix ok)
  snip rm 3f2a

Environment variables:
  SNIP_SERVER    server URL (overrides the saved one)
  SNIP_TOKEN     API token (tok_...), skips `snip login` entirely
  SNIP_CONFIG    config file path (default ~/.config/snip/config.json)
  SNIP_USERNAME  / SNIP_PASSWORD  non-interactive `snip login`
"""
import argparse
import datetime as dt
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

__version__ = "1.0.0"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_NOT_FOUND = 4
EXIT_NETWORK = 5

FULL_ID_RE = re.compile(r"^[0-9a-f]{32}$")
PAGE_SIZE = 500


class CliError(Exception):
    def __init__(self, message, code=EXIT_ERROR, status=None):
        super().__init__(message)
        self.code = code
        self.status = status


# ---------------------------------------------------------------- output

def _write(stream, text):
    # Always emit UTF-8 regardless of locale, so CJK content survives pipes.
    buf = getattr(stream, "buffer", None)
    if buf is not None:
        stream.flush()
        buf.write(text.encode("utf-8"))
        buf.flush()
    else:
        stream.write(text)


def out(text=""):
    _write(sys.stdout, text + "\n")


def err(text):
    _write(sys.stderr, text + "\n")


def out_json(obj):
    out(json.dumps(obj, ensure_ascii=False, indent=2))


def fmt_time(value):
    try:
        t = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value or ""
    if t.tzinfo is None:  # server stores naive UTC
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone().strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------- config

def config_path():
    path = os.environ.get("SNIP_CONFIG")
    if path:
        return path
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "snip", "config.json")


def load_config():
    path = config_path()
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        raise CliError("cannot read config %s: %s" % (path, e))
    return cfg if isinstance(cfg, dict) else {}


def save_config(cfg):
    path = config_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, mode=0o700, exist_ok=True)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------- http

def normalize_server(url):
    url = url.strip().rstrip("/")
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url
    return url


class Client:
    def __init__(self, server, token=None, timeout=30):
        self.server = normalize_server(server)
        self.token = token
        self.timeout = timeout
        self._post_cache = None

    def request(self, method, path, json_body=None, form=None, params=None, token=None):
        url = self.server + "/api" + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json", "User-Agent": "snip-cli/" + __version__}
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        auth = token or self.token
        if auth:
            headers["Authorization"] = "Bearer " + auth

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
        except urllib.error.HTTPError as e:
            raise self._http_error(e)
        except urllib.error.URLError as e:
            raise CliError("cannot reach %s: %s" % (self.server, e.reason), EXIT_NETWORK)
        except OSError as e:  # timeouts, connection resets
            raise CliError("cannot reach %s: %s" % (self.server, e), EXIT_NETWORK)

        if not body:
            return None
        try:
            return json.loads(body.decode("utf-8"))
        except ValueError:
            raise CliError("unexpected non-JSON response from %s (wrong --server?)" % url)

    @staticmethod
    def _http_error(e):
        detail = None
        try:
            payload = json.loads(e.read().decode("utf-8"))
            if isinstance(payload, dict):
                detail = payload.get("detail")
        except Exception:
            pass
        if isinstance(detail, list):  # FastAPI validation errors
            detail = "; ".join(
                "%s: %s" % (".".join(str(x) for x in d.get("loc", [])), d.get("msg"))
                for d in detail if isinstance(d, dict)
            )
        msg = "HTTP %s: %s" % (e.code, detail or e.reason)
        if e.code == 401:
            return CliError(msg + " (run `snip login` again or check SNIP_TOKEN)", EXIT_AUTH, e.code)
        if e.code in (404, 410):
            return CliError(msg, EXIT_NOT_FOUND, e.code)
        return CliError(msg, EXIT_ERROR, e.code)

    # -- helpers

    def fetch_posts(self, mine):
        posts, skip = [], 0
        while True:
            params = {"skip": skip, "limit": PAGE_SIZE}
            if mine:
                params["mine"] = "true"
            page = self.request("GET", "/posts/", params=params) or []
            posts.extend(page)
            if len(page) < PAGE_SIZE:
                return posts
            skip += PAGE_SIZE

    def resolve_id(self, ref):
        """Accept a full id, a unique prefix (>= 4 hex chars) or a /post/<id> URL."""
        ref = ref.strip().lower()
        m = re.search(r"/post/([0-9a-f]+)", ref)
        if m:
            ref = m.group(1)
        if FULL_ID_RE.match(ref):
            return ref
        if not re.match(r"^[0-9a-f]{4,31}$", ref):
            raise CliError("invalid post id %r (need a full id or >= 4 hex chars)" % ref, EXIT_USAGE)
        if self._post_cache is None:
            self._post_cache = self.fetch_posts(mine=False)
        matches = [p for p in self._post_cache if p["id"].startswith(ref)]
        if not matches:
            raise CliError("no post matches id prefix %r" % ref, EXIT_NOT_FOUND)
        if len(matches) > 1:
            raise CliError("ambiguous id prefix %r: %s" % (ref, ", ".join(p["id"][:12] for p in matches)))
        return matches[0]["id"]


def get_client(args, need_token=True):
    cfg = load_config()
    server = getattr(args, "server", None) or os.environ.get("SNIP_SERVER") or cfg.get("server")
    if not server:
        raise CliError("no server configured: run `snip login --server http://HOST:PORT` "
                       "or set SNIP_SERVER", EXIT_AUTH)
    token = os.environ.get("SNIP_TOKEN") or cfg.get("token")
    if need_token and not token:
        raise CliError("not logged in: run `snip login` or set SNIP_TOKEN", EXIT_AUTH)
    return Client(server, token)


# ---------------------------------------------------------------- input

def split_tags(values):
    tags = []
    for v in values or []:
        for t in v.split(","):
            t = t.strip().lstrip("#").strip()
            if t and t not in tags:
                tags.append(t)
    return tags


def read_source(path):
    """Read content from a file path or '-' (stdin). Returns (text, filename)."""
    if path == "-":
        data, name = sys.stdin.buffer.read(), None
    else:
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            raise CliError("cannot read %s: %s" % (path, e.strerror))
        name = os.path.basename(path)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise CliError("content is not valid UTF-8 text (binary files are not supported)")
    if text.startswith("﻿"):
        text = text[1:]
    return text, name


def default_title(text, filename):
    if filename:
        return filename
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:60]
    return "Snip " + dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def summarize(post, client):
    return {
        "id": post["id"],
        "title": post["title"],
        "tags": post.get("tags") or [],
        "author": (post.get("author") or {}).get("username"),
        "status": post.get("status"),
        "created_via": post.get("created_via"),
        "parent_id": post.get("parent_id"),
        "created_at": post.get("created_at"),
        "updated_at": post.get("updated_at"),
        "url": "%s/post/%s" % (client.server, post["id"]),
    }


# ---------------------------------------------------------------- commands

def cmd_login(args):
    cfg = load_config()
    server = args.server or os.environ.get("SNIP_SERVER") or cfg.get("server")
    if not server:
        raise CliError("please pass --server http://HOST:PORT", EXIT_USAGE)
    client = Client(server)

    if args.token:
        api_token = args.token.strip()
    else:
        username = args.username or os.environ.get("SNIP_USERNAME")
        if not username:
            if not sys.stdin.isatty():
                raise CliError("username required: pass -u USER or set SNIP_USERNAME", EXIT_USAGE)
            username = input("Username: ").strip()
        if args.password_stdin:
            password = sys.stdin.buffer.readline().decode("utf-8").rstrip("\r\n")
        else:
            password = os.environ.get("SNIP_PASSWORD")
            if password is None:
                if not sys.stdin.isatty():
                    raise CliError("password required: use --password-stdin or set SNIP_PASSWORD", EXIT_USAGE)
                password = getpass.getpass("Password for %s: " % username)
        try:
            res = client.request("POST", "/auth/login", form={"username": username, "password": password})
        except CliError as e:
            if e.status == 400:
                e.code = EXIT_AUTH
            raise
        # Exchange the 7-day JWT for the user's long-lived API token.
        api_token = client.request("GET", "/auth/me", token=res["access_token"])["api_token"]

    me = client.request("GET", "/auth/me", token=api_token)
    cfg.update({"server": client.server, "token": api_token, "username": me["username"]})
    path = save_config(cfg)
    if args.json:
        out_json({"server": client.server, "username": me["username"],
                  "is_admin": me["is_admin"], "config": path})
    else:
        out("Logged in as %s @ %s" % (me["username"], client.server))
        err("credentials saved to %s" % path)


def cmd_logout(args):
    cfg = load_config()
    had = cfg.pop("token", None) is not None
    cfg.pop("username", None)
    if had:
        save_config(cfg)
    if args.json:
        out_json({"logged_out": had})
    else:
        out("Logged out." if had else "Not logged in.")


def cmd_whoami(args):
    client = get_client(args)
    me = client.request("GET", "/auth/me")
    info = {"server": client.server, "username": me["username"], "id": me["id"], "is_admin": me["is_admin"]}
    if args.json:
        out_json(info)
    else:
        out("%s%s @ %s" % (me["username"], " (admin)" if me["is_admin"] else "", client.server))


def cmd_list(args):
    client = get_client(args)
    posts = client.fetch_posts(mine=not args.all)
    tags = split_tags(args.tag)
    if tags:
        match = all if args.match_all else any
        posts = [p for p in posts if match(t in (p.get("tags") or []) for t in tags)]
    if args.limit:
        posts = posts[:args.limit]

    if args.json:
        out_json([summarize(p, client) for p in posts])
        return
    if not posts:
        err("(no posts)")
        return
    for p in posts:
        cols = [p["id"][:8], fmt_time(p.get("updated_at") or p.get("created_at"))]
        if args.all:
            cols.append("@" + ((p.get("author") or {}).get("username") or "?"))
        title = p["title"]
        if p.get("status") == "deleted":
            title = "[deleted] " + title
        cols.append(title)
        if p.get("tags"):
            cols.append("[" + ", ".join(p["tags"]) + "]")
        out("  ".join(cols))


def cmd_show(args):
    client = get_client(args)
    post = client.request("GET", "/posts/%s" % client.resolve_id(args.id))
    if args.json:
        data = summarize(post, client)
        data["content"] = post.get("content") or ""
        out_json(data)
        return
    content = post.get("content") or ""
    if args.meta:
        s = summarize(post, client)
        out("# %s" % s["title"])
        out("id: %s  author: @%s  updated: %s" % (s["id"], s["author"], fmt_time(s["updated_at"])))
        if s["tags"]:
            out("tags: %s" % ", ".join(s["tags"]))
        out("url: %s" % s["url"])
        out("-" * 40)
    _write(sys.stdout, content)
    if content and not content.endswith("\n") and sys.stdout.isatty():
        _write(sys.stdout, "\n")


def _content_from_args(args, allow_implicit_stdin):
    """Returns (text, filename) or (None, None) if no content was given."""
    if args.content is not None:
        if args.file is not None:
            raise CliError("give either FILE or -c/--content, not both", EXIT_USAGE)
        return args.content, None
    if args.file is not None:
        return read_source(args.file)
    if allow_implicit_stdin and not sys.stdin.isatty():
        return read_source("-")
    return None, None


def cmd_push(args):
    client = get_client(args)
    text, filename = _content_from_args(args, allow_implicit_stdin=True)
    if text is None:
        raise CliError("no content: pass a FILE, '-' for stdin, -c TEXT, or pipe data in", EXIT_USAGE)
    if not text.strip():
        raise CliError("content is empty", EXIT_USAGE)
    payload = {
        "title": args.title or default_title(text, filename),
        "content": text,
        "tags": split_tags(args.tag),
        "created_via": "cli",
    }
    if args.fork:
        payload["parent_id"] = client.resolve_id(args.fork)
    post = client.request("POST", "/posts/", json_body=payload)
    if args.json:
        out_json(summarize(post, client))
    else:
        out(post["id"])  # stdout = id only, so `ID=$(snip push ...)` works
        err("created %r  %s/post/%s" % (post["title"], client.server, post["id"]))


def cmd_edit(args):
    client = get_client(args)
    pid = client.resolve_id(args.id)
    payload = {}
    # edit never reads stdin implicitly: an empty pipe must not wipe the content
    text, _ = _content_from_args(args, allow_implicit_stdin=False)
    if text is not None:
        payload["content"] = text
    if args.title is not None:
        if not args.title.strip():
            raise CliError("title cannot be empty", EXIT_USAGE)
        payload["title"] = args.title
    if args.clear_tags:
        payload["tags"] = []
    elif args.tag:
        payload["tags"] = split_tags(args.tag)
    if not payload:
        raise CliError("nothing to change: give FILE/-c, -t, --tag or --clear-tags", EXIT_USAGE)
    post = client.request("PUT", "/posts/%s" % pid, json_body=payload)
    if args.json:
        out_json(summarize(post, client))
    else:
        out("updated %s  %r" % (post["id"], post["title"]))


def cmd_rm(args):
    client = get_client(args)
    results, rc = [], EXIT_OK
    for ref in args.ids:
        try:
            pid = client.resolve_id(ref)
            client.request("DELETE", "/posts/%s" % pid)
            results.append({"ref": ref, "id": pid, "ok": True})
            if not args.json:
                out("deleted %s" % pid)
        except CliError as e:
            rc = e.code
            results.append({"ref": ref, "ok": False, "error": str(e)})
            if not args.json:
                err("%s: %s" % (ref, e))
    if args.json:
        out_json(results)
    return rc


# ---------------------------------------------------------------- parser

EPILOG = """\
id arguments accept a full id, a unique prefix (>= 4 hex chars, as shown by
`snip list`) or a post URL.

exit codes: 0 ok, 1 error, 2 usage, 3 auth, 4 not found/deleted, 5 network.
With --json, results go to stdout as JSON and errors to stderr as
{"error": ..., "code": ...}.

examples:
  snip login --server http://HOST:8080 -u alice
  printf '%s' "$PASSWORD" | snip login --server http://HOST:8080 -u alice --password-stdin
  SNIP_SERVER=http://HOST:8080 SNIP_TOKEN=tok_xxx snip list --json
  git diff | snip push -t "my diff" --tag Snippet
  snip push notes.md --tag Note,Idea
  snip show 3f2a > out.txt
  snip edit 3f2a notes.md
  snip edit 3f2a -t "new title" --tag Bug
  snip rm 3f2a 9c1d
"""


def build_parser():
    # --server/--json are accepted both before and after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--server", default=argparse.SUPPRESS,
                        help="server URL, e.g. http://host:8080 (env SNIP_SERVER)")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="JSON output for scripts/agents")

    p = argparse.ArgumentParser(
        prog="snip", description="Command line client for Snip Share.",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--server", default=None, help=argparse.SUPPRESS)
    p.add_argument("--json", action="store_true", default=False, help=argparse.SUPPRESS)
    p.add_argument("--version", action="version", version="snip " + __version__)
    sub = p.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    def add(name, func, help_text, aliases=()):
        sp = sub.add_parser(name, parents=[common], help=help_text, description=help_text,
                            aliases=list(aliases))
        sp.set_defaults(func=func)
        return sp

    sp = add("login", cmd_login, "log in and save credentials")
    sp.add_argument("-u", "--username")
    sp.add_argument("--password-stdin", action="store_true", help="read password from first line of stdin")
    sp.add_argument("--token", help="log in with an existing API token (tok_...) instead of a password")

    add("logout", cmd_logout, "forget saved credentials")
    add("whoami", cmd_whoami, "show the current user")

    sp = add("list", cmd_list, "list posts (your own by default)", aliases=["ls"])
    sp.add_argument("-a", "--all", action="store_true", help="list everyone's posts")
    sp.add_argument("--tag", action="append", help="filter by tag (repeatable or comma separated)")
    sp.add_argument("--match-all", action="store_true", help="require all --tag values (default: any)")
    sp.add_argument("-n", "--limit", type=int, help="show at most N posts")

    sp = add("show", cmd_show, "print a post's raw content", aliases=["cat", "get"])
    sp.add_argument("id")
    sp.add_argument("--meta", action="store_true", help="print a header with title/tags/url first")

    sp = add("push", cmd_push, "upload a new post from FILE, stdin or -c", aliases=["upload", "add"])
    sp.add_argument("file", nargs="?", help="file to upload, '-' for stdin (default: stdin if piped)")
    sp.add_argument("-c", "--content", help="content text")
    sp.add_argument("-t", "--title", help="title (default: file name or first line)")
    sp.add_argument("--tag", action="append", help="tag (repeatable or comma separated)")
    sp.add_argument("--fork", metavar="ID", help="mark as a fork of post ID")

    sp = add("edit", cmd_edit, "update a post's content, title or tags")
    sp.add_argument("id")
    sp.add_argument("file", nargs="?", help="new content from file, '-' for stdin")
    sp.add_argument("-c", "--content", help="new content text")
    sp.add_argument("-t", "--title", help="new title")
    sp.add_argument("--tag", action="append", help="replace tags (repeatable or comma separated)")
    sp.add_argument("--clear-tags", action="store_true", help="remove all tags")

    sp = add("rm", cmd_rm, "delete posts", aliases=["delete", "del"])
    sp.add_argument("ids", nargs="+", metavar="ID")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args) or EXIT_OK
    except CliError as e:
        if args.json:
            _write(sys.stderr, json.dumps({"error": str(e), "code": e.code}, ensure_ascii=False) + "\n")
        else:
            err("snip: error: %s" % e)
        return e.code
    except KeyboardInterrupt:
        err("interrupted")
        return 130
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, "w")
        except OSError:
            pass
        return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
