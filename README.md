# Snip Share

> 一个为极客小团队打造的、支持 LaTeX 和 Markdown 的轻量级去中心化同步空间。

Snip Share 不仅仅是一个共享剪切板。它支持完整的 Markdown 语法、复杂的数学公式渲染，并引入了“Fork”机制与强大的多维标签引擎，允许成员在不破坏原帖的情况下进行知识的分类、检索与并行演进。

## ✨ 核心特性

- **多维标签引擎**：内置 `Theory`, `Snippet`, `Bug`, `Note`, `Idea`, `Life` 等全场景分类，支持无缝输入自定义标签。系统采用自动色彩哈希映射（Color Hashing），并在主页提供丝滑的毫秒级内存筛选（支持 AND/OR 逻辑交并集）。
- **极致排版与对齐**：采用 Inter + 霞鹜文楷 + JetBrains Mono 字体栈，专为技术阅读优化。卡片元数据（Metadata）采用底层流式布局，彻底告别视觉死角。
- **数学公式**：完美支持 LaTeX 行内及块级公式渲染（基于 KaTeX/MathJax）。
- **Fork 机制**：一键派生他人的帖子（自动继承标签），支持思路的并行演进。
- **墓碑模式**：作者删除帖子后保留其“存在痕迹”（标签与排版变灰），确保派生贴的溯源链条完整。
- **双轨认证**：网页端 JWT 鉴权 + 终端长期 API Token，为后续 CLI 扩展预留接口。
- **管理员特权**：管理员可查阅被删除的历史存盘，确保团队资产不丢失。

## 🛠 技术栈

- **Frontend**: Vue 3, Vite, Tailwind CSS v4, md-editor-v3
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0
- **Database**: SQLite (单文件存储，支持 JSON 数据列，极致轻量)
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

---

## 👨‍💻 管理员操作

- **添加新成员**：
  ```bash
  docker exec -it snip_backend python add_user.py
  ```

- **数据备份**：
  由于采用的是单文件数据库，直接备份挂载卷中的 `snip_data/snip_data.db` 文件即可，支持热备份。