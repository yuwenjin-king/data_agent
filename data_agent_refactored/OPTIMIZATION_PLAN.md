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

## 各阶段进展（截至 2026-07-12）

### P0 可运行基线 — ✅ 已完成（提交 df67679 / 63b156f）

- 修复 SQLAlchemy `metadata` 保留字、`CRUDBase[...]` 泛型、服务层 helper 导入。
- 移除应用导入阶段的 `Base.metadata.create_all()` 副作用。
- 前端依赖安装与构建通过（`63b156f` 修复 `ChatOutlined` → `MessageOutlined` 构建阻断）。
- 最小 pytest 覆盖（应用导入、schema 序列化）。

### P1 数据库与接口契约收敛 — ✅ 已完成（提交 df67679）

- Alembic 配置与 `0001_initial_baseline` 基线迁移。
- `docs/schema-compatibility.md`：原 Java entity ↔ Python model 对照。
- 统一 `HTTPException` / 校验错误的 `ApiResponse` 响应格式。
- SQLite 隔离 API 契约测试（Agent / Datasource / Knowledge / Chat / 错误响应）。

### P2 基础业务能力 — ✅ 已完成（提交 df67679）

- Datasource 连接测试、表/字段列表、逻辑关系管理。
- Agent 发布/下线/API Key 管理。
- 知识、语义模型、预设问题 CRUD、状态切换、Excel 批量导入。
- 文件上传与本地存储。

### P3 核心智能链路 — ✅ plan-driven 多步图已落地（593f8ec + Phase A+B，仅 human_feedback 待补）

拓扑（含 chitchat 分支）：

plan-driven 多步图（已对齐原项目，Phase A+B 落地于 b42fbdf / 550a9c9 / 36b4107）：

```
intent → evidence_recall → query_enhance → schema_recall → table_relation
→ feasibility_assessment → planner → plan_executor（循环枢纽）
→ sql_generate → semantic_consistency → sql_execute → plan_executor
→ python_generate → python_execute → python_analyze → plan_executor
→ report_generator
```

- 已迁移节点：feasibility_assessment、planner、plan_executor、semantic_consistency、python_generate、python_execute、python_analyze（原 8 缺口中 7 个，仅 human_feedback 未做）。
- SQL 自愈闭环：sql_execute 失败 / 语义失败均回 sql_generate 重试，全局 `sql_generate_count`≤10 封顶；sql_execute 成功时计数清零并推进 `plan_current_step`。
- Python 分析子链：`app/workflow/code/executor.py` 本地沙箱（subprocess + AST 守卫 + 环境脱敏 + POSIX rlimit + 超时 + stdout 上限），失败重试≤5 后 fallback。
- workflow_service 多步流式：即时下发 `sql` / `sql_result` / `plan` 事件，metadata 单步存标量、多步存列表。
- 每个新节点均有无 LLM fallback，无 LLM / 无 Docker 也能跑通；全套 92 测试通过。

**仍待补齐**：

- `human_feedback`（基于 interrupt 的 Plan 人工审批，需恢复 API + 前端 UI）——本轮明确不做。
- Python 沙箱生产级隔离：当前本地执行器为纵深防御（超时 + rlimit + 脱敏 + AST 守卫），非真正沙箱；生产需接 Docker（`CODE_EXECUTOR_TYPE=docker`，现为 `NotImplementedError` 桩）或 nsjail。

### P4 生产化 — 🟡 大部分完成（722d345 / ec36c0b / f83d379 / 1d62432 / b1d1fe6 / 7d5053a），仅 Docker 全栈待补

已完成：

- **CI（GitHub Actions）**：`ruff check` → `ruff format --check` → `mypy app` → `pytest` → 前端 `npm build`，每次推送/PR 自动跑。
- **工具链**：ruff（lint + format）、mypy（pydantic 插件；Column 噪声码暂关，待模型迁移 `Mapped[...]` 后重开）、pytest（`pythonpath` 配置，bare pytest 可跑）。
- **安全**：ModelConfig 的 LLM `api_key`/`proxy_password` 加密存储 + 用时解密 + 响应脱敏；`maybe_decrypt` 容错兼容历史明文。
- **文件上传**：扩展名白名单、流式大小检查（DoS 防护）、UUID 存储名、健壮路径穿越校验（`relative_to`）；`import_excel` 强制 `.xlsx`。
- **结构化日志**：JSON 行格式 + workflow/SQL/Python 关键路径埋点 + `LOG_LEVEL` 配置。
- **执行安全边界**：SQL 只读校验（已有）；Python 本地沙箱（AST 守卫 + POSIX rlimit + 环境脱敏 + 超时）。

待补：

- Docker Compose 全栈（MySQL + 后端 + 前端）+ Dockerfile + 环境变量模板（本机 Docker 不可用，需本地验证）。
- 认证授权（目前无 auth 中间件）、运行指标（metrics endpoint）、前端 ESLint/Prettier 与前端测试。

## 下一步执行顺序

1. ~~SQL 自愈闭环 + 可行性网关~~（已完成，b42fbdf）。
2. ~~plan-driven 多步架构 + Python 分析沙箱~~（已完成，550a9c9 / 36b4107）。
3. （可选）`human_feedback` 人工审批，或 Python 沙箱接 Docker。
4. ~~进入 P4 生产化~~（CI/lint/mypy/加密脱敏/上传安全/结构化日志 已落地）；剩余 Docker 全栈、auth、metrics、前端测试待补。
