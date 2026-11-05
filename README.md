# Snip Share

> 一个为极客小团队打造的、支持 LaTeX 和 Markdown 的轻量级自托管同步空间。

Snip Share 不仅仅是一个共享剪切板。它支持完整的 Markdown 语法、复杂的数学公式渲染，并引入了“Fork”机制与强大的多维标签引擎，允许成员在不破坏原帖的情况下进行知识的分类、检索与并行演进。

## ✨ 核心特性

- **多维标签引擎**：内置 `Theory`, `Snippet`, `Bug`, `Note`, `Idea`, `Life` 等全场景分类，支持无缝输入自定义标签。系统采用自动色彩哈希映射（Color Hashing），并在主页提供丝滑的毫秒级内存筛选（支持 AND/OR 逻辑交并集）。
- **极致排版与对齐**：采用 Inter + 霞鹜文楷 + JetBrains Mono 字体栈，专为技术阅读优化。卡片元数据（Metadata）采用底层流式布局，彻底告别视觉死角。
- **数学公式**：完美支持 LaTeX 行内及块级公式渲染（基于 KaTeX/MathJax）。
- **Fork 机制**：一键派生他人的帖子（自动继承标签），支持思路的并行演进。
- **墓碑模式**：作者删除帖子后保留其“存在痕迹”（标签与排版变灰），确保派生贴的溯源链条完整。
- **双轨认证**：账号密码登录建立会话（网页端和 `snip login`，7 天有效）；API Key 无状态，每次请求携带，供脚本和 Agent 使用。Key 只在生成时展示一次，服务器只存 SHA-256 哈希，可以自助轮换。
- **命令行客户端**：单文件、零依赖的 `snip`，支持登录、列表、查看、上传、编辑、删除，提供 `--json` 输出，便于脚本和 Agent 调用。
- **管理员特权**：管理员可查阅被删除的历史存盘，并可编辑或删除任意成员的帖子。

## 🛠 技术栈

- **Frontend**: Vue 3, Vite, Tailwind CSS v4, md-editor-v3
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0
- **Database**: SQLite (单文件存储，支持 JSON 数据列，极致轻量)
- **CLI**: Python 3.8+ 单文件脚本，仅用标准库
- **Deployment**: Docker Compose, Nginx

## 🚀 快速开始

### 0. 前置要求
- 已安装 Docker 和 Docker Compose
- 开放服务器 8080 端口

### 1. 克隆与配置
将代码上传至服务器后，进入项目根目录。

### 2. 启动服务
执行以下命令进行镜像构建与容器启动：
```bash
docker-compose up -d --build
```

### 3. 初始化管理员
容器启动后，必须初始化第一个管理员账号：
```bash
docker exec -it snip_backend python init_db.py
```
根据提示输入 `admin` 账号的密码。

### 4. 访问
打开浏览器访问：`http://你的服务器IP:8080`

> JWT 签名密钥：首次启动时自动生成随机密钥并保存在 `snip_data/.secret_key`（权限 600）。也可以通过环境变量 `SECRET_KEY`（至少 32 个字符）指定。更换密钥会让所有登录会话失效，但不影响 API Key。

---

## ⌨️ 命令行客户端 `snip`

### 安装
客户端由服务器直接提供下载，只需要 Python 3.8+：
```bash
curl -fsSL http://你的服务器IP:8080/cli/snip.py -o ~/.local/bin/snip
chmod +x ~/.local/bin/snip
```
没有 `~/.local/bin` 的话，也可以直接 `python3 snip.py ...`。

### 两种认证方式

**1. 账号密码会话（给人用）**
```bash
snip login --server http://你的服务器IP:8080 -u 用户名          # 交互式输入密码
printf '%s' "$PW" | snip login --server http://... -u 用户名 --password-stdin   # 非交互
```
登录后会话（JWT，7 天有效）保存在 `~/.config/snip/config.json`（权限 600），过期后重新登录。

**2. API Key（给脚本和 Agent 用）**
```bash
export SNIP_SERVER=http://你的服务器IP:8080
export SNIP_TOKEN=tok_xxx
snip list          # 每次调用都带上 Key，不需要登录，也不在本地保存任何东西
```
- 和大模型服务的 API Key 是同一种模式：**只在生成时展示一次**，服务器只存哈希，之后无法再查看。
- 新账号的 Key 由 `add_user.py` 打印一次。丢失或泄露时，用密码会话轮换（会再次要求输入密码）：
  ```bash
  snip login -u 用户名
  snip token rotate      # 新 Key 打印到 stdout，只显示这一次；旧 Key 立即作废
  ```
- API Key 能调用所有帖子接口，但**不能管理 Key**，泄露了也没法把你锁在外面。
- `SNIP_TOKEN` 和本地会话同时存在时，优先使用 `SNIP_TOKEN`。

### 常用命令
| 命令 | 说明 |
|------|------|
| `snip list` / `snip ls` | 列出自己的帖子；`-a` 列出所有人的帖子，`--tag Note` 按标签筛选，`-n 10` 限制条数 |
| `snip show ID` / `snip cat ID` | 输出原始内容（可重定向到文件）；`--meta` 带标题和标签 |
| `cmd \| snip push` | 从 stdin 上传；也可以 `snip push file.md` 或 `snip push -c "文本"`；`-t` 指定标题，`--tag A,B` 打标签 |
| `snip edit ID [FILE]` | 修改内容/标题/标签：`-c`、`-t`、`--tag`、`--clear-tags` |
| `snip rm ID...` | 删除（墓碑模式） |
| `snip whoami` / `snip logout` | 查看当前用户和认证方式 / 清除本地会话 |
| `snip token rotate` | 生成新 API Key（只显示一次）并作废旧 Key，需要密码会话 |

- `ID` 可以是完整 ID、`snip list` 显示的前缀（至少 4 位），也可以是帖子 URL。
- `snip push` 只把新帖 ID 输出到 stdout，可以写成 `ID=$(snip push notes.md)`。
- 所有命令都支持 `--json`。退出码：0 成功，1 错误，2 用法错误，3 认证失败，4 不存在/已删除，5 网络错误。
- 完整帮助：`snip --help`、`snip push --help`。

---

## 👨‍💻 管理员操作

- **添加新成员**：
  ```bash
  docker exec -it snip_backend python add_user.py
  ```

- **数据备份**：
  数据库是单个文件 `snip_data/snip_data.db`。服务运行时直接复制可能得到写入一半的文件，建议使用 `sqlite3 snip_data/snip_data.db ".backup backup.db"`，或者先停掉 backend 容器再复制。`snip_data/.secret_key` 也需要一起备份。

- **更新命令行客户端**：`cli/snip.py` 是挂载进 Nginx 容器的，修改后不需要重建镜像。