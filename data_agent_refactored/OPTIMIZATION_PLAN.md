# Data Agent Refactored 优化计划

## 目标

当前项目更接近 FastAPI + React 的重构原型，尚未达到原 DataAgent 的功能等价。优化目标分三层：

1. 先让项目稳定启动、可测试、可本地联调。
2. 再补齐基础管理能力的数据一致性、接口契约和迁移机制。
3. 最后按原项目核心链路逐步迁移 NL2SQL、知识检索、SQL 执行、Python 分析和报告生成。

## 当前评估

### 优点

- 后端已经按 `api / models / schemas / services / core` 分层，适合继续演进。
- 前端已有布局、页面、API service 和基础状态管理，能支撑 CRUD 管理界面。
- README 和架构文档明确了目标功能，便于拆分里程碑。

### 主要风险

- 后端当前存在启动阻断问题，不能作为后续开发基线。
- README 中“数据库 schema 与原项目完全兼容”的表述缺少验证，当前也没有迁移脚本和兼容性测试。
- Chat/NL2SQL 只是占位逻辑，原项目核心 workflow 尚未迁移。
- 测试目录为空，缺少最小导入测试、API 契约测试和服务层测试。
- 前后端接口存在协议不一致，例如流式聊天客户端与后端路由不匹配。

## 优化路线

### P0：建立可运行基线

验收标准：

- 后端应用可以被导入并启动到 FastAPI app 初始化完成。
- 不依赖本地 MySQL 也能运行基础导入测试。
- 前端可以完成依赖安装后的构建检查。
- 修复明显的前后端接口协议错误。

任务：

- 修复 SQLAlchemy Declarative 保留名 `metadata`。
- 修复 `CRUDBase[...]` 泛型定义。
- 修复服务层缺失的 SQLAlchemy helper 导入。
- 移除应用导入阶段的 `Base.metadata.create_all()` 副作用，数据库初始化改由迁移或显式脚本承担。
- 修复前端错误导入和流式聊天请求方式。
- 增加最小 pytest 覆盖：应用导入、关键 schema 序列化。

### P1：数据库和接口契约收敛

验收标准：

- 有 Alembic 迁移目录和首版基线迁移。
- SQLAlchemy 模型字段与原项目 schema 有对照表。
- API 返回结构、分页、错误码策略统一。
- CRUD 接口至少有 happy path 和主要失败路径测试。

任务：

- 建立 `docs/schema-compatibility.md`，逐表对比原 Java entity、数据库 schema 和 Python model。
- 引入 Alembic，禁止在运行时隐式创建或变更生产表。
- 统一 `ApiResponse`、分页响应、错误码、404/400/500 处理。
- 为 Agent、Datasource、Knowledge、Chat Session 增加 API 测试。

### P2：基础业务能力补齐

验收标准：

- 数据源支持连接测试、表列表、字段列表和逻辑关系管理。
- Agent 发布、下线、API Key 管理可用。
- 知识、语义模型、预设问题支持完整增删改查和状态切换。
- 文件上传与本地存储能力可用。

任务：

- 迁移 Agent publish/offline/API key 能力。
- 迁移 Datasource type registry、连接测试、schema 初始化能力。
- 迁移 SemanticModel 批量导入、模板下载和启停能力。
- 迁移 AgentKnowledge 文件上传、分块、状态流转和资源清理。

### P3：核心智能链路迁移

验收标准：

- Chat 支持真实流式事件。
- 能完成从自然语言问题到 SQL 生成、SQL 执行、结果解释的闭环。
- 支持业务知识和语义模型参与召回。
- 支持多轮上下文和会话事件。

任务：

- 设计 Python 版 workflow graph，明确节点输入输出契约。
- 迁移 Query Enhance、Intent Recognition、Schema Recall、Table Relation、SQL Generate、SQL Execute、Report Generator。
- 接入 LLM provider 配置和模型可用性检查。
- 接入向量存储、embedding、混合检索和知识召回。

### P4：生产化

验收标准：

- 有 CI：lint、type check、unit test、API test、frontend build。
- 有 Docker Compose 本地环境。
- 有基本认证授权和敏感信息保护。
- 有结构化日志、错误追踪和运行指标。

任务：

- 增加 ruff/black/mypy 或等价工具链。
- 增加 ESLint/Prettier 和前端测试。
- 补充 Dockerfile、docker-compose、环境变量模板。
- 密码和 API key 加密存储，响应中默认脱敏。
- CORS、文件上传、SQL 执行和 Python 执行增加安全边界。

## 推荐执行顺序

1. 完成 P0，确保每次提交都有可运行基线。
2. 做 P1 的 schema 对齐，不要在 schema 未确认前大规模迁移业务。
3. 按“Datasource -> Agent 配置 -> Knowledge -> Chat workflow”的顺序补业务。
4. 每迁移一个原项目模块，同时迁移或重写对应测试。

## 本次已启动的优化范围

本次先处理 P0：

- 后端启动阻断修复。
- 前端明显构建错误修复。
- 前后端流式请求方式初步对齐。
- 增加最小后端测试。

## P1 当前进展

- 已增加 Alembic 配置和 `0001_initial_baseline` 基线迁移。
- 已新增 `docs/schema-compatibility.md`，记录原 Java entity 与 Python model 的兼容性状态。
- 已统一 `HTTPException` 和请求校验错误的 `ApiResponse` 响应格式。
- 已增加 SQLite 隔离 API 契约测试，覆盖 Agent、Datasource、Knowledge、Chat 和错误响应。
