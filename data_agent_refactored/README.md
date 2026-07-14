# Data Agent - 智能数据分析师 (重构版)

基于 **FastAPI + React 重构的企业级智能数据分析平台。

> 📖 **文档导航：
- [架构文档](./ARCHITECTURE.md) - 详细架构图、数据模型、业务流程

---

## 项目简介

Data Agent 是一个基于 AI 的企业级智能数据分析平台，支持自然语言转 SQL、Python 深度分析、智能报告生成等功能。

## 项目特点：
- 🤖 **智能体管理**：创建、配置、管理数据智能体
- 📊 **数据洞察**：自然语言转 SQL，自动数据分析
- 🧠 **知识增强**：业务知识、语义模型、向量检索
- 🔧 **灵活配置**：模型配置、Prompt 配置
- 💬 **智能对话**：多轮对话、流式响应

---

## 项目结构

```
data_agent_refactored/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routers/   # API 路由
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务服务
│   │   ├── core/          # 核心配置
│   │   └── main.py        # 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/   # 公共组件
│   │   ├── pages/       # 页面
│   │   ├── services/   # API 服务
│   │   ├── store/       # 状态管理
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── ARCHITECTURE.md       # 架构文档
└── README.md
```

---

## 功能特性

### 核心功能
- ✅ 智能体管理 (Agent Management)
- ✅ 数据源管理 (Datasource Management)
- ✅ 业务知识管理 (Business Knowledge)
- ✅ 语义模型管理 (Semantic Models)
- ✅ 智能对话 (Chat Interface)
- ⏳ 自然语言转 SQL (Text-to-SQL)
- ⏳ Python 深度分析 (Python Analysis)
- ✅ 模型配置 (Model Config)
- ✅ Prompt 配置 (Prompt Config)

---

## 快速开始

### 方式一：Docker Compose 一键启动（推荐）

需要 Docker 与 Docker Compose。一键拉起 MySQL + 后端 + 前端全栈：

```bash
cd data_agent_refactored
cp .env.docker.example .env          # 配置 CRYPTO_KEY / MySQL 口令（务必随后改成自己的 key）
docker compose up --build
```

- 后端启动前会自动执行 `alembic upgrade head` 建表。
- 访问：前端 http://localhost:8080 ，后端 API http://localhost:8000/docs ，MySQL 暴露在主机 13306。
- nginx 已把 `/api` 反代到后端，并保留 SSE 流式（聊天）。
- `CRYPTO_KEY` 用于密钥加密，**必须跨重启保持不变**，否则历史加密数据无法解密。生成新 key：
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

> 若连接的是已存在的原 DataAgent 数据库，进入 backend 容器执行 `alembic stamp head`（先对照 `docs/schema-compatibility.md`）。

### 方式二：本地手动启动

### 前置条件
- Python 3.9+
- Node.js 16+
- MySQL 5.7+ 或 PostgreSQL
- npm 或 yarn

### 1. 数据库准备

首先确保你有一个可用的数据库。重构版使用 Alembic 管理 schema：

```bash
cd backend
alembic upgrade head
```

如果连接的是已经存在的原 DataAgent 数据库，请先查看
[schema 兼容性文档](./docs/schema-compatibility.md)，确认字段和类型差异后再执行：

```bash
cd backend
alembic stamp head
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务启动后，访问 http://localhost:8000

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务启动后，访问 http://localhost:3000

---

## 技术栈

### 后端技术栈
| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.109+ | 现代 Web 框架 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| Pydantic | 2.0+ | 数据验证 |
| Uvicorn | 0.27+ | ASGI 服务器 |
| PyMySQL | 1.1+ | MySQL 驱动 |

### 前端技术栈
| 技术 | 版本 | 说明 |
|------|------|------|
| React | 18+ | UI 框架 |
| Vite | 5.0+ | 构建工具 |
| Ant Design | 5.0+ | UI 组件库 |
| React Router | 6.0+ | 路由管理 |
| Zustand | 4.0+ | 状态管理 |
| Axios | 1.6+ | HTTP 客户端 |

---

## 文档

- **架构文档**：[ARCHITECTURE.md](./ARCHITECTURE.md)
- **API 文档**：启动后端后访问 http://localhost:8000/docs (Swagger UI) 或 http://localhost:8000/redoc

---

## 数据库

数据库 schema 正在与原项目对齐，当前支持：
- MySQL
- PostgreSQL

兼容性状态见 [docs/schema-compatibility.md](./docs/schema-compatibility.md)。在完成逐表验证前，不建议直接声明已有数据可以无改动迁移使用。

---

## 主要页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 仪表盘 | / | 数据概览 |
| 智能体列表 | /agents | 智能体管理 |
| 智能体配置 | /agents/:id | 配置智能体 |
| 对话 | /chat/:agentId | 与智能体对话 |
| 系统设置 | /settings | 系统配置管理 |

---

## 开发指南

### 后端开发
```bash
cd backend
uvicorn app.main:app --reload
```

### 前端开发
```bash
cd frontend
npm run dev
```

### 前端构建
```bash
cd frontend
npm run build
```

---

## 下一步计划

- [ ] 实现完整的 Text-to-SQL 功能
- [ ] 集成向量数据库集成
- [ ] Python 代码执行环境
- [ ] WebSocket 流式响应
- [ ] 用户认证与授权
- [ ] Docker 容器化部署
- [ ] 添加单元测试和集成测试

---

## 联系方式

如有问题，请查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 获取更多技术细节。
