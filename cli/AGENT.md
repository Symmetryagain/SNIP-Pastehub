# 给 Agent 的使用说明：Snip Share 命令行客户端 `snip`

Snip Share 是我们团队自建的云剪切板 / Markdown 笔记服务，地址 http://139.224.40.140:8080 。
你通过命令行客户端 `snip` 读写其中的内容，身份是委托你的那位用户（用 API Key 认证）。

## 准备（每个新环境做一次）

```bash
curl -fsSL http://139.224.40.140:8080/cli/snip.py -o snip && chmod +x snip   # 需要 Python 3.8+，无其他依赖
export SNIP_SERVER=http://139.224.40.140:8080
echo "SNIP_TOKEN is ${SNIP_TOKEN:+set}"   # 只检查是否已设置，不要打印它的值
./snip whoami                             # 确认认证成功，输出应包含 [API key (SNIP_TOKEN)]
```

- API Key 由运行环境的 `SNIP_TOKEN` 环境变量提供。如果没有设置，请向用户索要，不要猜测，也不要尝试其他方式获取。
- 不能 `chmod` 的话，用 `python3 snip ...` 运行。
- 每次调用都是独立请求，没有会话，不需要登录。

## 命令

所有命令都可以加 `--json` 得到机器可读的输出。需要解析结果时，请始终使用 `--json`。

| 用途 | 命令 |
|---|---|
| 列出我的帖子 | `snip list --json`；可加 `--tag Note`（可重复，默认匹配任意一个）、`--match-all`（要求全部匹配）、`-n 20` |
| 列出所有人的帖子 | `snip list --all --json` |
| 读取内容 | `snip show ID`：原样输出正文，不加任何修饰，适合重定向到文件 |
| 读取内容和元数据 | `snip show ID --json`：比列表结果多一个 `content` 字段 |
| 上传 | `cat file.md \| snip push -t "标题" --tag Note,Idea`；也可以 `snip push file.md` 或 `snip push -c "短文本"` |
| 修改 | `snip edit ID -t "新标题"`、`snip edit ID new.md`、`cat new.md \| snip edit ID -`、`snip edit ID --tag A,B`、`snip edit ID --clear-tags` |
| 删除 | `snip rm ID [ID ...]` |

说明：
- **ID**：可以是完整的 32 位 ID、`snip list` 显示的前缀（至少 4 位），也可以是帖子 URL。
- **push**：stdout 只输出新帖的 ID，提示信息走 stderr，所以可以写 `ID=$(cat x.md | ./snip push -t 标题)`。不给 `-t` 时，标题取文件名或正文第一行。内容为空会被拒绝。
- **edit**：`--tag` 会整体替换原有标签，不是追加。要追加的话，先用 `show --json` 读出现有标签，再连同新标签一起写回。edit 不会自动读取 stdin，要从 stdin 读必须显式写 `-`。
- **多行内容**：用文件或 stdin 传，不要用 `-c`，以免 shell 引号出错。内容必须是 UTF-8 文本，大小不超过 10MB。
- **list --json 的字段**：`id, title, tags, author, status, created_via, parent_id, created_at, updated_at, url`。时间是不带时区后缀的 UTC。

## 退出码和错误处理

使用 `--json` 时，错误以 `{"error": "...", "code": N}` 的形式输出到 stderr。

| 退出码 | 含义 | 你应该怎么做 |
|---|---|---|
| 0 | 成功 | |
| 1 | 一般错误，例如 403 无权修改他人帖子 | 阅读 error 信息，不要反复重试 |
| 2 | 用法错误 | 检查参数 |
| 3 | 认证失败 | 停下来告诉用户，Key 可能已失效。不要尝试 `snip login` 或 `snip token rotate`：那是给人用的命令，需要密码，API Key 无权执行 |
| 4 | 帖子不存在或已被删除 | |
| 5 | 网络错误 | 可以间隔几秒重试 2–3 次 |

## 规则

1. 不要泄露 API Key：不要把它写进输出、日志、帖子内容或命令行参数，只通过环境变量 `SNIP_TOKEN` 使用。
2. 删除对用户来说不可撤销（只有管理员还能看到已删除的内容）。只删除用户明确要求删除的帖子，或者你在本次任务中自己创建的帖子。
3. `list --all` 能看到其他成员的帖子，但它们只能读，修改或删除会返回 403。
4. 服务目前走 HTTP 明文，不要上传密码、密钥等敏感信息。
5. 完整帮助：`snip --help`、`snip push --help` 等。
