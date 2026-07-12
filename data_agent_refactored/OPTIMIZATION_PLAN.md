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

### P3 核心智能链路 — ⚠️ 核心链路已落地（提交 593f8ec），与原项目功能对齐尚有缺口

已迁移（线性链路 + chitchat 分支）：

`intent_recognition → evidence_recall → query_enhance → schema_recall → table_relation → sql_generate → sql_execute → report_generator`

- LangGraph 工作流图、Jinja prompt、LLM/embedding client、内存向量库 + 混合检索、只读 SQL 执行器。
- `workflow_service` 编排：SSE 流式 + 非流式、多轮上下文、消息持久化。
- SQL 执行结果已含 `DisplayStyleBO` 图表配置（`data-view-analyze` prompt）——原项目的图表也由 SQL 节点的 LLM 调用产生，非 Python 绘图，此项已对齐。
- 计划原文 P3 验收均已满足：真实流式事件、NL→SQL→执行→解释闭环、业务知识/语义模型召回、多轮上下文。

**相对原 Java DataAgent 的功能缺口**（原项目为 plan-driven 多步图，非线性）：

缺失节点（8）：

1. `feasibility_assessment` — table_relation 之后的网关，把非"数据分析"类问题短路到 END。
2. `planner` — 产出多步 `Plan` JSON（每步选 SQL/Python/Report 工具）驱动整图。
3. `plan_executor` — 校验 Plan 并按步路由（主循环枢纽），替代当前隐式线性流。
4. `semantic_consistency` — sql_generate 与 sql_execute 之间的 LLM 语义校验闸门。
5. `python_generate` — LLM 生成 pandas 分析代码（禁止绘图/网络/子进程）。
6. `python_execute` — 沙箱执行（原项目：Docker anaconda 镜像、无网络、cap-drop-all、内存/CPU 限制、60s 超时）。
7. `python_analyze` — LLM 汇总 Python stdout 为自然语言分析。
8. `human_feedback` — 基于 interrupt 的 Plan 人工审批（需 `interrupt_before` 编译 + 恢复 API）。

缺失回边/循环：

- `sql_execute → sql_generate` 执行失败重试；`semantic_consistency ↔ sql_generate` 语义失败重试；`sql_generate` 自重试上限 10。
- `table_relation` 自重试上限 3；`python_execute → python_generate` 重试上限 5 + fallback。
- `plan_executor ↔ planner` 修复上限 2；人工拒绝上限 3。
- **`sql_execute → plan_executor`**（当前直连 `report_generator`，坍缩了多步 Plan 模型）。

> 备注：Python 侧节点层已为 SQL 重试做好准备——`sql_generate` 已能读 `sql_regenerate_reason` 走 `sql-error-fixer` prompt，`sql_execute` 失败时已写 reason；只差 graph 回边与 `semantic_consistency` 闸门。

### P4 生产化 — ⬜ 未开始

见上文 P4 任务清单（CI、Docker Compose、lint、加密脱敏、结构化日志）。

## 下一步执行顺序

1. 先补 SQL 自愈闭环（`semantic_consistency` 闸门 + sql_execute 重试回边 + sql_generate 自重试上限）与 `feasibility_assessment` 网关——低风险，节点层已就绪。
2. 再评审是否上 plan-driven 多步架构（planner + plan_executor + Python 分析沙箱）——较大架构变更，需单独确认范围与沙箱安全边界。
3. 每补一个节点，同步补对应单测，并在 `test_graph.py` 增加端到端用例。
