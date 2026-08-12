---
title: Kairos 技术选型全景
aliases:
  - 技术选型
  - Technology Stack
tags:
  - kairos
  - design
  - technology
created: 2026-07-20
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 技术选型全景

> **⚠ 草稿完善声明**：本文列出的技术栈和版本约束为设计选型目标。当前草稿完善阶段无运行代码，技术选型将在代码启动后最终确认。

> **定位**：Kairos 系统全栈技术选型一览。ADR 记录了「为什么选」，本文记录「选了什么」——含版本约束和兼容矩阵。

---

## 一、后端运行时

| 组件 | 选型 | 版本 | 说明 |
|:----|:-----|:----|:-----|
| 语言 | Python | ≥ 3.11 | 生态成熟，AI/ML 库丰富。目标兼容：3.11–3.13 |
| Web 框架 | Litestar | ≥ 2.0 | 异步优先，类型安全，OpenAPI 自动生成。目标兼容：2.0–2.10+ |
| ASGI 服务器 | Uvicorn | ≥ 0.22 | 与 Litestar 原生集成。目标兼容：0.22–0.30 |
| 任务调度 | APScheduler | ≥ 3.10 | 升华/遗忘/重估等周期性任务的**空闲驱动调度**框架（非 cron 模式——见 ADR-006）。APScheduler 在此以 interval trigger + 负载感知启控实现空闲驱动。目标兼容：3.10–3.11 |
| 密码学 | cryptography | ≥ 42.0 | 敏感字段 AES-256-GCM 加密存储（S-07）、PBKDF2-HMAC-SHA512 密钥派生与 API Key 安全哈希（S-01/S-05）；算法与参数以 [security-specification.md](../security/security-specification.md) 为权威，本表仅登记选型 |
| **CLI 框架** | Click 或 Typer（二选一，W1 定档） | Click ≥ 8.1 / Typer ≥ 0.12 | `kairos` 命令入口（`src/main.py`）的参数解析与子命令编排，承载 `kairos serve` / `kairos db migrate` / `kairos write` / `kairos search` / `kairos forget` 等命令（全量命令契约以 [api-spec.md](../specification/api-spec.md) §3 为单一事实源）；两者择一的最终确认在 W1 项目骨架阶段完成（见 [project-plan.md](../governance/project-plan.md) §二 Phase 0），落点见 [implementation-map.md](../specification/implementation-map.md) 与 [slice-implementation-guide.md](./slice-implementation-guide.md) |

## 二、数据存储

| 组件 | 选型 | 版本 | 说明 |
|:----|:-----|:----|:-----|
| 主数据库（标准模式） | PostgreSQL | ≥ 15 | 生产级关系数据库 |
| 向量扩展（标准模式） | pgvector | ≥ 0.5 | 向量相似度搜索。**PostgreSQL 17 须配 pgvector ≥ 0.8**（0.7.x 未提供 PG 17 支持），版本组合见 §六 兼容矩阵 |
| 主数据库（轻量模式） | SQLite | ≥ 3.40 | 内置零配置 |
| 向量扩展（轻量模式） | sqlite-vec | ≥ 0.1 | SQLite 向量搜索。嵌入维度统一为 1536（标准模式 text-embedding-3-small；轻量模式 BGE-M3 原生 1024 维，通过线性投影映射至 1536 维（投影方案：固定随机正交投影 $W \in \mathbb{R}^{1536 \times 1024}$，见 ADR-012）——DDL 以 1536 为准，投影层规格见 [adr.md](../governance/adr.md) ADR-012（固定正交投影 + 矩阵随 schema 持久化）与 [data-model.md](../specification/data-model.md) §13.5） |
| **连接池（标准模式）** | asyncpg + 内建连接池 | — | asyncpg 自带高效连接池；外部连接池仅在连接数 >> CPU 核数时介入；轻量模式 SQLite 无连接池 |
| 数据库驱动（轻量模式） | aiosqlite | — | SQLite 异步访问（轻量模式无连接池） |
| **ORM 框架** | SQLAlchemy | ≥ 2.0 | `src/storage/models.py` 的 ORM 定义底座；经 asyncpg（标准模式）/ aiosqlite（轻量模式）两种方言驱动，Alembic 迁移依赖此层 |
| **数据库迁移** | Alembic | ≥ 1.13 | 双模式共用版本链；`kairos db migrate` / `kairos db migrate rollback` 由 Alembic upgrade / downgrade 支撑；FTS5 虚拟表 autogenerate 不识别，需手写 `op.execute()`（见 ADR-011） |
| **关键词检索（标准模式）** | pg_bigm + zhparser | — | PostgreSQL 端 BM25 关键词检索承载（决策 D-12）：zhparser 中文分词 + pg_bigm 双字 bi-gram 索引，与 pgvector 共存于同一库；支撑三信号融合检索的 BM25 分量（权重 0.35，见 [架构 §7.3a](../foundation/architecture-v0.1.0.md)）。两者均需安装扩展 |
| **关键词检索（轻量模式）** | FTS5（SQLite 虚拟表） | SQLite 3.40+ 内置 | 轻量模式 BM25 关键词检索承载；DDL 默认 `tokenize='unicode61'`，精细中文分词经 jieba 自定义 tokenizer 扩展（由 `KAIROS_FTS5_CHINESE_SEGMENTATION` 配置控制，默认 `true`，需扩展已编译方可生效），见 [data-model.md](../specification/data-model.md) §11 与 [schema-slice.sql](../specification/schema-slice.sql) 第 14 节；迁移注意见上 Alembic 行（ADR-011） |

## 三、AI 与嵌入

| 组件 | 选型 | 版本 | 说明 |
|:----|:-----|:----|:-----|
| 文本嵌入模型 | text-embedding-3-small | — | 1536 维，API 调用 |
| 默认嵌入模型（轻量模式） | BGE-M3 | — | 本地轻量嵌入（原生 1024 维，投影方式见上）；标准模式默认为 text-embedding-3-small（1536 维） |
| LLM 接口协议 | OpenAI API 兼容 | — | Provider 可切换 |
| 嵌入缓存 | LRU 缓存 | — | 减少重复调用 |
| 实体提取 NLP | spaCy | ≥ 3.7 | 轻量模式本地实体抽取（见 [configuration.md](../ops/configuration.md) §6.4）；与 LLM 批量提取互补，零外部 API 依赖 |
| 意图分类模型 | intent-t5-small | — | 查询意图分类的模型兜底层（规则层未命中时启用），置信度 < 0.6 降级 `general`；权重路径由 `KAIROS_INTENT_CLASSIFIER_MODEL` 指定（默认 `./models/intent-t5-small`），机制见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.6.1 |
| 时间抽取模型 | timestamp-t5-small | — | 记忆时间戳的异步后处理抽取（不阻塞主摄取路径）；权重路径由 `KAIROS_TIMESTAMP_MODEL_PATH` 指定（默认 `./models/timestamp-t5-small`），机制见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| **本地推理运行时（嵌入）** | sentence-transformers | ≥ 3.0 | BGE-M3 的本地加载与编码入口（轻量模式默认嵌入路径）；传递依赖 transformers + 张量后端 |
| **本地推理运行时（序列到序列）** | transformers | ≥ 4.40 | intent-t5-small / timestamp-t5-small 两个本地小模型的加载与推理入口 |
| **张量后端** | PyTorch | ≥ 2.2 | 上述三个本地模型底座的统一张量后端；以 CPU-only 轮子为基线（GPU 加速为可选部署形态，非运行前提） |

> **本地模型底座（三个）**：轻量模式下系统在本地运行 BGE-M3（嵌入）/ intent-t5-small（意图）/ timestamp-t5-small（时间抽取）三个模型，共用 transformers + PyTorch 运行时；标准模式下嵌入走 text-embedding-3-small API，意图与时间抽取仍为本地小模型。三者的权重完整性校验（SHA-256）尚未落地，威胁分析见 [threat-model.md](../security/threat-model.md) §三a，追缴条目：债务 D-439。

> **LLM 模型路由梯队（Tier 1~4）**：系统内 LLM 调用按能力/成本分四级梯队统一路由（自动升降级 + 双层语义缓存），梯队定义、成本量级与升降级规则见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.9——本表不再重复；模型选择通过 `KAIROS_LLM_*` 系列环境变量配置（见 [configuration.md](../ops/configuration.md)）。

## 四、部署工具链

| 组件 | 选型 | 版本 | 说明 |
|:----|:-----|:----|:-----|
| 容器化 | Docker | ≥ 24.0 | 标准模式部署 |
| 容器编排 | Docker Compose V2 | ≥ 2.20 | 多服务编排 |
| 包管理 | uv + pip | — | 快速依赖安装 |
| 进程管理（轻量模式） | 内置 | — | Python 子进程 |

## 五、开发与测试

| 组件 | 选型 | 版本 | 说明 |
|:----|:-----|:----|:-----|
| 测试框架 | pytest | ≥ 8.0 | 测试执行 |
| 覆盖率 | pytest-cov | — | 覆盖率报告 |
| Mock | pytest-mock | — | 依赖模拟 |
| Docker 测试 | testcontainers | — | 集成测试环境 |
| 静态类型 | mypy | — | 类型检查 |
| 代码格式 | ruff | — | 格式化 + lint |
| 可观测性（追踪） | OpenTelemetry | ≥ 1.20 | 分布式追踪与指标埋点标准；跨组件 trace/metric 统一导出（见 [observability.md](../ops/observability.md)）。**v1.1 目标引入**——v0.1.0 以日志关联追踪为主，不引入 OTel SDK（追缴条目：债务 D-432） |
| 可观测性（指标） | Prometheus | ≥ 2.45 | 拉取式指标采集与告警规则；v0.1.0 经 prometheus_client 直出 `/metrics` 端点（observability 暴露协议——**端点待定义**，在 api-spec §1.8 登记前为设计目标，追缴条目：债务 D-429），v1.1 引入 OpenTelemetry 后切换 exporter（追缴条目：债务 D-432） |
| 可观测性（可视化） | Grafana | ≥ 10.0 | 指标/追踪看板与告警面板。**v1.1 目标引入**——v0.1.0 不编排 Grafana 服务、不交付看板 JSON，运维以结构化日志 + Prometheus 原始指标为准（追缴条目：债务 D-432） |

> **CI/CD 工具链**：本表列开发与测试组件；持续集成/交付的具体工具（GitHub Actions 等）与门禁流水线定义见 [engineering-workflow.md](../development/engineering-workflow.md) §四——技术选型视角此处不重复承载，避免与开发流程规范双源。

## 六、版本兼容矩阵

| Python | PostgreSQL | pgvector | Litestar | Uvicorn | 说明 |
|:------|:----------|:---------|:--------|:--------|:------|
| 3.11–3.13 | 15–16 | 0.5–0.8+ | 2.0–2.10+ | 0.22–0.30 | 标准模式 |
| 3.11–3.13 | 17 | **≥ 0.8** | 2.0–2.10+ | 0.22–0.30 | 标准模式（PG 17 须配 pgvector ≥ 0.8——0.7.x 未提供 PG 17 支持，该组合不可用） |
| 3.11–3.13 | SQLite 3.40+ | sqlite-vec 0.1+ | 2.0–2.10+ | 0.22–0.30 | 轻量模式 |

---
## 七、MCP 协议与多语言 SDK（P3-07）

Kairos 作为记忆基础设施，通过标准化协议和官方 SDK 降低集成门槛，使不同技术栈的 AI Agent（Hermes、Claude Code、Codex、Cursor 等）均可无缝接入。

**MCP（Model Context Protocol）集成战略**：

Kairos 对外暴露符合 MCP 规范的 Tool 接口，将 [12 规范操作集](../foundation/architecture-v0.1.0.md)（架构 §7.3.1）中的 create/search/delete 等 3 个规范操作直接映射为 MCP Tool，连同检索/维护/治理类 9 个（共基础工具集 12），再加关系管理 3 个，共暴露 15 个 MCP Tool（构成口径见 [架构 §7.1a](../foundation/architecture-v0.1.0.md)）。Agent 通过 MCP Client 发现并调用 Kairos 的记忆工具，无需理解内部存储模型。

- **MCP Server 实现**：MCP Server 作为**独立子进程**运行（stdio 传输），由 Agent 的 MCP Client 启动，与 Kairos 主进程通过 localhost HTTP 通信（进程模型与 [integration-design.md](../development/integration-design.md) §七、[api-spec.md](../specification/api-spec.md) §6.8 一致——非主进程内嵌）。Server 端实现完整治理门禁（L1 权限 + L2 宪法约束 + L3 身份否决）
- **Tool 命名规范**：`kairos_<operation>`（如 `kairos_store_memory`、`kairos_search_memories`），完整工具清单（15 个：基础工具集 12——含 create/search/delete 三个规范操作直接映射与检索/维护/治理类 9 个——另加关系管理 3 工具，构成口径见架构 §7.1a）见 [架构 §7.1a MCP Bridge 实现](../foundation/architecture-v0.1.0.md) 与 [api-spec §6.8](../specification/api-spec.md)
- **Clarify 消歧**：MCP Tool 的 `on_pre_execute` hook 在参数不完整时触发 Clarify 步骤，反问补全后执行，保证工具调用的健壮性
- **渐进增强**：MCP 为基线协议，后续版本（v1.1 目标）可扩展为支持 Resources（记忆目录浏览）和 Prompts（检索模板），丰富交互模式（追缴条目：债务 D-443）

**三语言官方 SDK 战略**（P3-07 系，v1.1 目标）：

| SDK 语言 | 定位 | 核心能力 | 最低版本要求 |
|:--------|:-----|:--------|:-----------|
| **Python** | AI/ML 生态首选 | 完整的 15 个 MCP Tool 客户端（基础工具集 12 + 关系管理 3）、async/await 支持、pydantic 模型校验、与 LangChain/LlamaIndex 的 Memory 集成适配器 | Python ≥ 3.10 |
| **TypeScript** | Web/Node.js 生态 | 完整的 15 个 MCP Tool 客户端（基础工具集 12 + 关系管理 3）、Edge Runtime 兼容（Vercel/Cloudflare Workers）、Zod schema 校验、与 Vercel AI SDK 的 Memory Provider 集成 | Node.js ≥ 18 / TypeScript ≥ 5.0 |
| **Go** | 基础设施/CLI 工具生态 | 完整的 15 个 MCP Tool 客户端（基础工具集 12 + 关系管理 3）、低内存占用（< 10MB 运行时）、静态链接单二进制分发、gRPC streaming 支持（v1.1） | Go ≥ 1.21 |

> **版本对齐策略（补充）**：Python SDK 最低版本要求 ≥ 3.10——SDK 为独立交付物，其版本要求与后端运行时（§一，目标兼容 3.11–3.13）互不约束；后端运行仍以 3.11–3.13 为基线。

**SDK 设计原则**：

- **API 一致性**：三语言 SDK 暴露相同的操作语义（15 个 MCP Tool：基础工具集 12 + 关系管理 3），仅语言习惯适配（Python 用 snake_case，TS 用 camelCase，Go 用 PascalCase）
- **零依赖目标**（Go SDK）：除标准库外零外部依赖，确保在任何 Go 环境中 `go get` 即可用
- **渐进式类型安全**：Python 用 pydantic、TS 用 Zod、Go 用 struct tags——编译/校验时捕获参数错误
- **测试共享**：三语言 SDK 共享同一套集成测试用例描述（YAML 格式），各语言 SDK 根据描述生成对应测试代码，确保行为一致性

**File Graph 深层能力（P3-19，与 SDK 战略协同声明；v1.1 目标，v0.1.0 不交付）**：

File Graph 是 Kairos 路径空间的图论增强层——将 `kairos://` 路径树从纯层级索引升级为带权有向图。机制规格（反向链接追踪 / 多跳图遍历 / 孤立检测 / 中心性计算）已迁至 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-19，本节仅保留 SDK 协同摘要：以上能力通过三语言 SDK 的统一 `kairos_graph_*` 系列方法对外暴露（`kairos_graph_reverse_links` / `kairos_graph_traverse` / `kairos_graph_find_orphans` / `kairos_graph_centrality`），各语言 SDK 提供等价的类型安全接口。v0.1.0 以邻接表单跳查询 + 递归查询实现受限多跳遍历（架构 §0.4 多跳遍历声明）。

> **配置参数**：MCP 与 SDK 参数见 [ops/configuration.md](../ops/configuration.md) §8.8。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 技术选型全景：Python/Litestar/PostgreSQL/pgvector 主技术栈与版本兼容矩阵。 |
| 0.0.2~0.0.46 | 2026-08-08 | （合并占位：changelog 0.0.2~0.0.46 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.51 | 2026-08-08 | round22 审计修复批次（changelog 0.0.51）：§二 投影层补交叉引用（ADR-012 与 data-model §13.5），消除「需自行实现」误导。 |
| 0.0.53 | 2026-08-08 | round23 深度审计修复批次（changelog 0.0.53）：R23-03 OpenTelemetry 行补「（追缴条目：债务 D-432）」、Prometheus 行补「（追缴条目：债务 D-429）」指针。 |
| 0.0.59 | 2026-08-08 | round26 深度审计修复批次（changelog 0.0.59）：U-01 §三 补本地推理运行时（sentence-transformers / transformers / PyTorch）与两个本地小模型（intent-t5-small / timestamp-t5-small）登记 + 三模型底座注记（对应 threat-model §三a 引用）；U-02 §一 补 CLI 框架（Click / Typer，W1 定档）选型行；U-05 Grafana 行补 v1.1 目标与债务 D-432 指针。 |
| 0.0.61 | 2026-08-08 | round27 深度审计修复批次（changelog 0.0.61）：§七 MCP 集成战略句修正「12 规范操作集」遗留矛盾（实为「3 规范操作直接映射 + 检索/维护/治理 9 = 基础工具集 12」+ 关系管理 3 = 15，与 0.0.28/0.0.43 公式一致）；§二 新增关键词检索技术选型行（标准模式 pg_bigm + zhparser / 轻量模式 FTS5，承载三信号融合 BM25 0.35 分量，见架构 §7.3a / data-model §11 / schema-slice §14）。 |
| 0.0.64 | 2026-08-08 | round30 全面深度审计修复批次（changelog 0.0.64，补登）：§一 CLI 框架行去除 `kairos memory *` 误述，改为已登记命令族（serve/db migrate/write/search/forget 等）+ 指向 api-spec §3 CLI 表为单一事实源。 |
| 0.0.66 | 2026-08-09 | round32 全面深度审计修复批次（changelog 0.0.66）：版本记录补登批次——0.0.64 行（CLI 命令族去误述）为前序批次实质变更漏登记，本批补登（governance §4「触及即登记」）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.67 | 2026-08-09 | round33 全面深度审计修复批次（changelog 0.0.67）：§七「MCP Server 实现（勘误）」去除过程标记后缀（零版本标记纪律收敛，正文仅描述当前状态）。 |
| 0.0.80 | 2026-08-09 | round42 全面深度审计修复批次（changelog 0.0.80）：引用/口径收口 + 格式收尾 + 术语登记（glossary 70→76）——详见 changelog 0.0.80 叙述节。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87）：§二 投影措辞补「（投影方案：固定随机正交投影，见 ADR-012）」括注（线性/正交并称消歧）。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：§七 MCP 渐进增强补版本边界（v1.1 目标）与债务 D-443 指针；MCP Server 实现行裸 api-spec 引用链接化。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |


