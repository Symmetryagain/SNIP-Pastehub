# Vibe Coding 实践报告：Snip Share 全栈项目

## 项目概览

**Snip Share** 是一个为极客小团队打造的轻量级自托管同步空间，支持完整的 Markdown 语法和 LaTeX 数学公式渲染，并引入 Fork 机制与多维标签引擎，允许成员在不破坏原帖的情况下进行知识的分类、检索与并行演进。

- **开发周期**：2026年4月17日 — 4月18日（2天），11月5日补充代码审查、修复与 CLI
- **总提交数**：15 commits（初版）+ 3 commits（11月5日）
- **代码总量**：约 2350 行（不含文档、`package-lock.json`、node_modules 与构建产物；初版约 1450 行，CLI 约 700 行为后加）
- **开发方式**：100% Agent / AI 驱动（Vibe Coding）

---

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| **前端** | Vue 3, Vite 8, Tailwind CSS v4, md-editor-v3, Pinia, Vue Router 4, Axios |
| **后端** | FastAPI (Python), SQLAlchemy 2.0, Pydantic v2, PyJWT, Passlib (bcrypt) |
| **CLI** | Python 3.8+ 单文件脚本，仅依赖标准库（argparse + urllib） |
| **数据库** | SQLite (单文件存储，JSON 数据列，极致轻量) |
| **部署** | Docker Compose, Nginx (反向代理 + 静态资源托管) |
| **字体** | Inter + 霞鹜文楷 + JetBrains Mono 技术字体栈 |

---

## 功能清单

### 1. 多维标签引擎

- 内置 `Theory`, `Snippet`, `Bug`, `Note`, `Idea`, `Life` 六大默认标签分类
- 支持任意自定义标签的无缝输入
- **色彩哈希自动映射**：基于字符哈希算法为每个标签自动分配 7 色调色盘中的稳定颜色
- **毫秒级内存筛选**：前端纯计算属性实现 AND/OR 逻辑交并集，无需后端请求

### 2. Markdown 编辑与渲染

- 基于 `md-editor-v3`（CodeMirror 内核）的全屏编辑器
- 完整的 Markdown 语法支持（表格、代码高亮、任务列表等）
- LaTeX 行内及块级数学公式渲染（KaTeX/MathJax）
- 详情页一键复制 Markdown 源码

### 3. Fork 派生机制

- 一键 Fork 他人帖子，自动继承标题、内容和标签
- 派生链追踪：UI 展示 Fork 来源，支持跳转溯源
- 墓碑模式保障：即使原帖被删除，派生贴的溯源链条仍然完整

### 4. 墓碑模式（软删除）

- 作者删除帖子后只把状态改为 `deleted`，内容和记录都保留，供管理员查阅
- 列表页显示 `[已删除]` 标记、灰色半透明 + 灰度滤镜视觉表达
- 普通成员访问已删除帖子时，后端返回 410，详情页显示 `410 GONE` 墓碑页（只有占位文案，不显示作者和内容）
- 管理员仍可查阅全部已删除记录

### 5. 双轨认证体系

- **密码会话**：网页端和 `snip login` 用账号密码换取 JWT（7 天有效），属于有状态的持续会话
- **API Key**：参照大模型服务的 API Key 设计，给脚本和 Agent 使用。无状态，每次请求携带 `Bearer tok_...`；只在生成时（`add_user.py` / `init_db.py` / 轮换）展示一次，数据库只存 SHA-256 哈希；旧版本的明文 Key 在启动时原地转为哈希，用户手里的 Key 不受影响
- **Key 管理与使用分离**：`POST /api/auth/token/rotate` 要求密码会话并再次输入密码，API Key 本身不能用于轮换。这样会话泄露换不到永久 Key，Key 泄露也无法把账号主人锁在外面
- **JWT 签名密钥**：首次启动时随机生成并保存在数据卷中（初版写死在代码里，见下文“代码审查与修复”）
- 自动鉴权路由守卫（Vue Router beforeEach）
- 401 自动跳转登录页，410 优雅拦截墓碑响应

### 6. 管理员特权

- Admin 可查看所有贴子（包括已删除状态）
- Admin 可编辑/删除任意用户的贴子
- 命令行工具 `init_db.py`（首次初始化管理员）和 `add_user.py`（添加成员）

### 7. 命令行客户端 `snip`

- 单文件、零依赖，由 Nginx 在 `/cli/snip.py` 提供下载
- 命令：`login` / `logout` / `whoami` / `token rotate` / `list` / `show` / `push` / `edit` / `rm`
- 两种认证方式：`snip login` 保存密码会话；`SNIP_TOKEN` 环境变量提供 API Key，snip 不在本地保存 Key
- 面向脚本和 Agent：所有命令支持 `--json`，错误码区分认证、不存在和网络错误；`push` 只把新 ID 输出到 stdout；ID 可以用前缀或 URL
- 内容可以来自文件、stdin 或 `-c` 参数；`edit` 不会隐式读取 stdin，避免空管道清掉内容
- 后端配合：`GET /api/auth/me`（不返回 Key）、`POST /api/auth/token/rotate`、`GET /api/posts/?mine=true`，创建帖子时可指定 `created_via=cli`

### 8. Docker 一键部署

- 前后端分离的双容器架构（backend + frontend）
- Nginx 反向代理 `/api` 到 FastAPI 后端，`/cli/` 提供命令行客户端下载，其余路径托管 Vue 静态资源
- SQLite 数据存放在挂载卷中，可以用 `sqlite3 .backup` 在线备份（直接复制正在写入的文件可能得到不一致的副本）
- 单条命令完成构建与启动：`docker-compose up -d --build`

---

## 项目结构

```
SNIP-Pastehub/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py          # 会话 / API Key 双轨认证
│   │   │   └── routers/
│   │   │       ├── auth.py      # 登录、/me、API Key 轮换
│   │   │       └── posts.py     # 帖子 CRUD + 权限控制
│   │   ├── core/
│   │   │   ├── config.py        # 环境配置 + JWT 密钥生成/持久化
│   │   │   └── security.py      # 密码哈希 / JWT 编码
│   │   ├── db/
│   │   │   ├── database.py      # SQLAlchemy 引擎与会话管理
│   │   │   ├── migrate.py       # 启动时迁移：明文 API Key → 哈希
│   │   │   └── models.py        # User / Post 数据模型
│   │   ├── main.py              # FastAPI 入口 + CORS + 路由挂载
│   │   └── schemas.py           # Pydantic 请求/响应模型
│   ├── add_user.py              # 管理员添加用户工具
│   ├── init_db.py               # 首次初始化管理员工具
│   ├── Dockerfile
│   └── requirements.txt
├── cli/
│   └── snip.py                  # 命令行客户端（单文件，零依赖）
├── frontend/
│   ├── src/
│   │   ├── api/                 # axios 接口封装（auth, posts）
│   │   ├── router/              # Vue Router 路由表 + 鉴权守卫
│   │   ├── stores/              # Pinia 状态管理（auth store）
│   │   ├── utils/
│   │   │   ├── helpers.js       # 标签色彩哈希、时间格式化
│   │   │   └── request.js       # axios 实例 + 拦截器
│   │   └── views/
│   │       ├── Home.vue         # 帖子列表 + 标签筛选引擎
│   │       ├── Editor.vue       # Markdown 编辑器 + 标签输入
│   │       ├── Login.vue        # 登录页
│   │       └── PostDetail.vue   # 帖子详情 + Fork/编辑/删除
│   ├── nginx.conf               # Nginx 反向代理配置
│   ├── Dockerfile               # 多阶段构建（Node build + Nginx）
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 开发过程分析

### 提交时间线

| 日期 | 内容 | 提交数 |
|------|------|--------|
| 4月17日 | 项目初始化、Docker 环境搭建、README | 8 commits |
| 4月18日 | 博客标签功能（前后端联动）、Bug 修复与优化 | 7 commits |
| 11月5日 | 代码审查：修复密钥硬编码与管理员权限问题；新增 CLI；API Key 改为只展示一次 + 哈希存储；修正文档 | 3 commits |

### 开发节奏

整个项目在 **2 天内** 完成了从零到功能完备的交付：

1. **阶段一（基础设施）**：Git 初始化 → Docker Compose 编排 → FastAPI 骨架 → Vue 骨架 → 数据库模型 → 认证系统
2. **阶段二（核心功能）**：帖子 CRUD → Markdown 编辑器集成 → Fork 机制 → 墓碑模式 → 权限控制
3. **阶段三（增强特性）**：标签引擎（含色彩哈希、AND/OR 筛选） → 字体栈优化 → Bug 修复
4. **阶段四（审查与扩展，11月5日）**：通读全部代码 → 修复安全与权限问题 → 实现 CLI → 部署到服务器并做线上验证

### AI 协作特点

- **快速原型能力**：单个功能（如标签引擎的完整前后端实现）在 2-3 次对话交互内完成
- **Bug 修复精准**：如 tags 字段在 PostUpdate schema 中遗漏、PostCreate 中未保存 tags 等，通过上下文分析精确定位并修复
- **风格一致性**：Tailwind CSS 的原子化样式类在全部 4 个 Vue 组件中保持统一的设计语言
- **安全基础**：bcrypt 密码哈希、JWT 鉴权、路由守卫和分层访问控制在初版就有，但初版有几处“看起来正确、实际无效”的问题，直到后来通读代码时才被发现（见下一节）

---

## 代码审查与修复（11月5日）

初版完成后，对整个仓库做了一次完整审查，发现以下问题并已修复：

| 问题 | 影响 | 修复 |
|------|------|------|
| JWT 签名密钥写死在 `config.py` 中，部署时也没有覆盖 | 帖子接口会返回 `author_id`，任何成员都能拿到管理员 ID，再用这个已知密钥伪造管理员或其他成员的 JWT | 去掉默认值：优先读取环境变量 `SECRET_KEY`，否则首次启动时随机生成，写入数据卷中的 `.secret_key`（权限 600） |
| 前端读取 JWT 中的 `username` 判断管理员，但签发 JWT 时只写入了 `sub` 和 `exp` | 管理员在网页上永远看不到他人帖子的编辑/删除按钮 | JWT 加入 `username`；管理员判断统一放到 Pinia store 的 `isAdmin` getter |
| 后端编辑接口只允许作者本人修改 | 文档写的“管理员可编辑任意帖子”实际无法实现 | 编辑接口加上管理员例外，和删除接口保持一致 |
| API Key 明文存储在数据库 | 数据库一旦泄露，所有人的 Key 都会泄露 | 改为只存 SHA-256 哈希，启动时自动迁移旧数据 |
| 文档描述与实现不符 | 删除时“清空内容”、墓碑页“保留作者和元信息”、“Monaco 风格编辑器”、“去中心化”等说法与代码不一致 | 已按实际实现修正本文、摘要和 README |

这几个问题有一个共同点：代码能运行，界面上也看不出错误，但功能本身不起作用。AI 生成的代码和 AI 写的总结都把它们描述成“已正确实现”。所以对 Agent 产出的代码，仍然需要人工通读或做针对性测试，不能只看总结。

CLI 的第一版实现本身也出过一次设计偏差：为了支持密码登录，`/api/auth/me` 会返回 API Key，`snip login` 还会把永久 Key 存到本地。这把密码会话和 API Key 两条线混在了一起，也违背了“Key 只展示一次”的原始设计。经讨论后改为：`/me` 不再返回 Key，密码登录只保存会话，Key 只能通过需要密码的轮换接口重新生成。

审查中还记录了一些未处理的次要问题：首页只拉取最近 50 条帖子且没有分页；没有数据库迁移工具；`index.html` 引用的 favicon 不存在；仓库里有误提交的 `.pyc` 文件和 Vite 模板残留文件。

---

## 关键指标

| 指标 | 数值 |
|------|------|
| 总开发时长 | ~2 天（初版）+ 1 次审查迭代 |
| 总提交数 | 15（初版）+ 3 |
| 总代码行数 | ~2,350（不含文档与 `package-lock.json`） |
| 后端 Python 文件 | 16 个（其中 4 个为空的 `__init__.py`） |
| 前端 Vue/JS 文件 | 13 个（含未使用的模板组件 `HelloWorld.vue`） |
| CLI | 1 个文件，约 700 行 |
| Docker 镜像 | 2 个（backend + frontend） |
| API 端点 | 8 个（登录、`/me`、Key 轮换、帖子 CRUD） |

---

## 结论

Snip Share 作为一个全栈 Web 应用，在 AI/Agent 驱动开发下实现了：

- **功能完备**：认证、CRUD、Fork 派生、软删除墓碑、多维标签筛选、LaTeX 渲染、命令行客户端等特性齐备
- **架构清晰**：前后端分离、JWT 鉴权、Docker 部署、Nginx 反向代理
- **开发高效**：2 天完成了通常需要 1–2 周手写的全栈交付量
- **需要审查**：初版存在密钥硬编码、管理员判断失效等问题，而 AI 的自述报告称其“均被正确实现”，是在通读代码后才发现的

该项目作为 Vibe Coding 的实践样本，验证了 Agent 驱动开发在中小规模全栈项目中的可行性。在范式化场景（RESTful CRUD、认证鉴权、容器化部署）下，AI 助手能明显降低样板代码的编写成本，让开发者把注意力放在产品特性上。同时，这个项目也说明 AI 产出的代码和总结都需要独立验证，尤其是涉及安全和权限的部分。
