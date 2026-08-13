---
title: Kairos 文档索引
aliases:
  - 文档目录
  - 文档体系
tags:
  - kairos
  - documentation
created: 2026-07-18
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 文档索引

> **当前状态**：**v0.1.0 首版已发布（竖切交付完成）**。Kairos 为全面重新设计的系统，本文档库的竖切组件已有可运行代码（`src/` 下 15 张竖切表、记忆 CRUD/双副本、路径空间、事件总线、三信号检索、遗忘、身份注册表、审计 HMAC 链、校准/降级/冻结、REST 21 端点 + CLI 15 条）；全量 v0.1.0 的 168 项能力（43 核心 + 125 扩展）仍处于架构就绪状态，核心引擎（升华/图谱/WM 等竖切外组件）未启动。代码启动与竖切交付进展见 [changelog](governance/changelog.md)。

> **快速入口：** [系统架构](foundation/architecture-v0.1.0.md) · [认知基础](foundation/cognitive-foundation.md) · [待实现债务清单](governance/debt-collection.md)


---

## 地基文档（为什么 + 是什么）

| 路径 | 内容 |
|:-----|:-----|
| [`foundation/cognitive-foundation.md`](foundation/cognitive-foundation.md) | **认知基础** — 「记忆即使用」第一性原理、多维评分系统（正交性假设）（v0.1.0 承载四轴 + 可及性代理）、三硬一软设计原则 |
| [`foundation/architecture-v0.1.0.md`](foundation/architecture-v0.1.0.md) | **系统架构** — 六层栈、监督平面、全部机制规格。全体系以本文为设计权威 |
| [`foundation/design-philosophy-relations.md`](foundation/design-philosophy-relations.md) | **理念关系图** — 六级排序链+身份面否决权/三硬一软/分域真理观等约束与协作关系 |
| [`foundation/architecture-blueprint-v1.1.md`](foundation/architecture-blueprint-v1.1.md) | **架构蓝图（v1.1+）** — 未来版本详细规划（§5.3–§5.8 等机制；**§5.5 见证→使用仲裁除外**——决策 D-05 已迁入 v0.1.0，主架构 §5.5 为权威定义），**非 v0.1.0 交付范围** |

## 规格文档（具体长什么样）

| 路径 | 内容 |
|:-----|:-----|
| [`specification/claim-implementation-matrix.md`](specification/claim-implementation-matrix.md) | **声明-承载对齐矩阵** — 从认知基础提取的 37 项架构承载声明对应表（含已废弃 C-23，活跃 36 项） |
| [`specification/feature-list.md`](specification/feature-list.md) | **功能清单** — 14 类 **168 项**对外能力枚举 |
| [`specification/data-model.md`](specification/data-model.md) | **数据模型** — 57 张表 Schema + 索引（物理表 57 张：其中 `prompt_dependencies` 为 v1.1+ 预留表、`api_keys` 对应安全规格 §2.1 内部密钥表） |
| [`specification/api-spec.md`](specification/api-spec.md) | **接口规格** — REST API / Agent Tool / CLI / 事件总线（含资源摄取与多模态 Part schema） |
| [`specification/implementation-map.md`](specification/implementation-map.md) | **实现映射** — 70 组件路径映射，从架构到代码模块 |
| [`specification/detailed-design.md`](specification/detailed-design.md) | **详细设计** — 核心组件状态机 + 算法伪代码 + 剥离自架构/认知基础的工程实现（代理公式/去重/实体提取/注意力预算/存储协议/探索治理） |
| [`specification/nfr-specification.md`](specification/nfr-specification.md) | **NFR 规格** — 性能/容量/可用性/资源/安全量化指标 |
| [`specification/requirements-baseline.md`](specification/requirements-baseline.md) | **需求基线** — 功能需求/NFR/约束/部署规模/能力梯度/RTM 表/版本边界 |
| [`specification/system-context.md`](specification/system-context.md) | **系统上下文** — 边界声明 + 外部依赖 |
| [`specification/use-cases.md`](specification/use-cases.md) | **使用场景** — 8 个典型交互场景 |
| [`specification/rl-weight-spec.md`](specification/rl-weight-spec.md) | **RL 权重优化器规格** — 五维权重 + 学习算法 |
| [`specification/operation-catalog.md`](specification/operation-catalog.md) | **操作目录** — 66 项标准操作（OP-001~OP-066），按 ENC/RET/STR 三阶段组织，标注安全红线 |
| [`specification/schema-slice.sql`](specification/schema-slice.sql) | **竖切 DDL** — 14 张物理竖切表可执行建表语句（另含 1 张 FTS5 虚拟表 `memories_fts`，合计 15 张；`slice-implementation-guide` 的「15 张表」即此口径）；data-model 指定的 DDL 唯一承载，全量 57 表 DDL 随实现阶段由 Alembic 迁移承载 |
| [`specification/api-contract/openapi.yaml`](specification/api-contract/openapi.yaml) | **REST 契约骨架** — OpenAPI 3.1，81 路径 / 88 操作（骨架，request/response schema 待补全，见债务 D-428） |
| [`specification/api-contract/mcp-tools.json`](specification/api-contract/mcp-tools.json) | **MCP 工具契约** — 15 工具清单（inputSchema 待补全，见债务 D-428） |

## 开发文档（怎么上手开发）

| 路径 | 内容 |
|:-----|:-----|
| [`development/technology-stack.md`](development/technology-stack.md) | **技术选型全景** — Python/Litestar/PostgreSQL/pgvector |
| [`development/development-setup.md`](development/development-setup.md) | **开发环境搭建** — 本地开发步骤 + IDE 配置 |
| [`development/coding-conventions.md`](development/coding-conventions.md) | **开发规范** — 命名/结构/错误处理/日志 |
| [`development/integration-design.md`](development/integration-design.md) | **集成设计** — Agent 全生命周期 + 并发/超时/错误传播 |
| [`development/slice-implementation-guide.md`](development/slice-implementation-guide.md) | **竖切实现指南** — 竖切组件/15 张表/REST+CLI 端点/逐组件实现规格 |
| [`development/engineering-workflow.md`](development/engineering-workflow.md) | **工程流程** — 分支策略/PR 流程/提交规范/CI 门禁/发布流程 |

## 治理文档

| 路径 | 内容 |
|:-----|:-----|
| [`governance/adr.md`](governance/adr.md) | **架构决策记录** — 12 项已采纳 ADR |
| [`governance/debt-collection.md`](governance/debt-collection.md) | **追缴清单** — 已闭环项 + 待实现债务路线图 |
| [`governance/risks.md`](governance/risks.md) | **风险登记册** — 架构风险与哲学张力 |
| [`governance/project-plan.md`](governance/project-plan.md) | **项目计划** — 4 Phase 里程碑（具体周数待代码启动后定） |
| [`governance/changelog.md`](governance/changelog.md) | **变更日志** — 语义化版本变更记录 |
| [`governance/social-calibration-roadmap.md`](governance/social-calibration-roadmap.md) | **社会性校准演进路线图** — v0.1.0→v2.0 里程碑 |
| [`governance/cognitive-architecture-gap.md`](governance/cognitive-architecture-gap.md) | **认知-架构承诺差距表** — 16 项降维/预留/偏离追踪 |
| [`governance/documentation-governance.md`](governance/documentation-governance.md) | **文档治理规范** — 更新联动/交叉引用/状态管理/编号注册 |
| [`governance/release-guide.md`](governance/release-guide.md) | **发布指南** — 版本号/检查清单/发布步骤/许可证 |

## 运维文档

| 路径 | 内容 |
|:-----|:-----|
| [`ops/deployment.md`](ops/deployment.md) | **部署指南** — 三级部署规模（轻量/标准/全量）+ 三级能力梯度（全量/标准/内核），环境变量、Docker 参考 |
| [`ops/configuration.md`](ops/configuration.md) | **配置参数参考** — 227 项参数（2026-08-12 核定；口径：表格行首为 `KAIROS_*` 的参数定义行；含附录 A 全库索引 152 项，总计 379 项）+ 动态调参规则 |
| [`ops/reliability.md`](ops/reliability.md) | **可靠性策略** — RTO/RPO、备份、WAL 归档、LLM 熔断 |
| [`ops/observability.md`](ops/observability.md) | **可观测性设计** — 指标/日志/告警/检测器可见性 |
| [`ops/troubleshooting.md`](ops/troubleshooting.md) | **故障排查** — 常见问题与恢复命令 |
| [`ops/runbook.md`](ops/runbook.md) | **运维手册** — 日常操作/备份/升级/故障应急 |

## 质量文档

| 路径 | 内容 |
|:-----|:-----|
| [`quality/test-strategy.md`](quality/test-strategy.md) | **测试策略** — 单元/集成/E2E 三级 + 安全红线验证 |
| [`quality/acceptance-criteria.md`](quality/acceptance-criteria.md) | **验收标准** — 6 项债务完成条件 + 发布检查项 |
| [`quality/benchmark-plan.md`](quality/benchmark-plan.md) | **性能基准计划** — 延迟/吞吐/磁盘/回归阈值 |
| [`quality/test-plan.md`](quality/test-plan.md) | **测试计划** — 核心路径用例 + E2E + 测试数据 |

## 安全文档

| 路径 | 内容 |
|:-----|:-----|
| [`security/threat-model.md`](security/threat-model.md) | **威胁模型** — STRIDE + LLM 攻击面 + S-01~S-19 + HMAC 审计链 |
| [`security/security-specification.md`](security/security-specification.md) | **安全规格** — 安全需求/认证/加密/隐私/密钥/事件响应 |

## 用户文档

| 路径 | 内容 |
|:-----|:-----|
| [`user/quick-start.md`](user/quick-start.md) | **快速入门** — 约 2 分钟最小闭环教程 |
| [`user/user-guide.md`](user/user-guide.md) | **用户指南** — 上手/核心操作/最佳实践/限制 |

## 参考文档

| 路径 | 内容 |
|:-----|:-----|
| [`references/glossary.md`](references/glossary.md) | **术语表** — 77 条中英文术语对照（7 个分类表），含热度层级衰减/摄入侧情绪保护/噪音规则库/编译器/结构化通信单元/编译净化/检索深度分级/命名配置集/竖切/结构性记忆/准见证锚定/身份面否决权/处理完降温/间隔重复复习/支撑集引用/范围性回滚/上下文腐烂等词条 |
| [`references/error-reference.md`](references/error-reference.md) | **错误参考** — 11 类 43 个错误码 |
| [`references/traceability-map.md`](references/traceability-map.md) | **需求可追溯性映射表** — 43 能力↔37 声明↔债务追踪↔16 差距交叉映射（追踪项以 [debt-collection.md](governance/debt-collection.md) 为权威账目） |
| [`references/domain_keywords.yaml`](references/domain_keywords.yaml) | **领域关键词表** — 领域关键词路由表（中英对照；词频统计待代码启动后引入） |
| [`references/usage-load-algorithm.md`](references/usage-load-algorithm.md) | **使用负载计量算法** |
| [`references/vad-coordinate-algorithm.md`](references/vad-coordinate-algorithm.md) | **VAD 情感坐标算法** |
| [`references/value-dimension-entropy.md`](references/value-dimension-entropy.md) | **价值维度熵值守护算法** |
| [`references/concept-tiers.md`](references/concept-tiers.md) | **概念分级速查表** — L1/L2/L3 三级概念归类 + 一句话类比 + 代码映射 + 依赖图 |
| [`references/capability_matrix.yaml`](references/capability_matrix.yaml) | **认知维度承载能力矩阵** — 各版本对认知维度的承载程度与恢复债编号 |

## 图表文档

| 路径 | 内容 |
|:-----|:-----|
| [`diagrams/system-architecture.html`](diagrams/system-architecture.html) | **系统架构总览图** — 六层栈与核心组件交互的可视化总览（HTML 交互图） |

## 分析文档（外部理念对照批次）

> **目录边界说明**：`docs/analysis/` 为外部视频理念对照分析的**产物目录**（独立批次），随仓库分发、不随审计过程材料归档；其文档计入 `docs/` 全量 md 统计（含于总计 196 份 md），但**不计入「核心文档」权威子集（56 份）**，亦不参与架构/规格权威口径。

| 路径 | 内容 |
|:-----|:-----|
| [`analysis/external-videos/README.md`](analysis/external-videos/README.md) | **外部视频分析批次索引** — 102 视频素材边界声明（B站 AI 字幕串台问题实测）、视频清单、目录导航 |
| [`analysis/external-videos/triage-matrix.md`](analysis/external-videos/triage-matrix.md) | **外部理念 × Kairos 分诊矩阵** — EV 条目（已覆盖/可吸收/张力/矛盾）+ T-002 实例样本 |
| [`analysis/external-videos/first-principles-review.md`](analysis/external-videos/first-principles-review.md) | **第一性原理对照评审** — 八原理逐条「支撑/挑战/未触及」 |
| [`analysis/external-videos/absorption-proposals.md`](analysis/external-videos/absorption-proposals.md) | **吸收建议清单** — AP-01~52 吸收提案 + AT-01~09 张力记录 |
| [`analysis/external-videos/notes/`](analysis/external-videos/notes/) | 逐视频精读笔记（N 份） |
| [`analysis/external-videos/repos/`](analysis/external-videos/repos/) | GitHub 仓库源码级深读笔记（REPO-01~15） |
| [`analysis/external-videos/process/fetch-guide.md`](analysis/external-videos/process/fetch-guide.md) | 字幕抓取/转写流程记录（不含凭据） |

总计：**196 份 md + 3 份 yaml**（= 核心文档 56 份【53 md + 3 yaml：foundation 4 + specification 13(12 md+1 yaml: api-contract/openapi.yaml) + development 6 + governance 9 + ops 6 + quality 4 + security 2 + user 2 + references 9(7 md+2 yaml) + README 1】+ 外部视频分析批次独立目录 [analysis/external-videos/](analysis/external-videos/README.md) 143 份【4 索引/报告 + 15 仓库笔记 + 102 视频笔记 + 21 论文笔记 + 1 流程记录】；审计过程材料不随仓库分发，处置记录见 changelog 各批次）。其中 [foundation/architecture-v0.1.0.md](foundation/architecture-v0.1.0.md) 为核心架构规格（全体系以架构文档为设计权威）。

> **附属资产计数政策**：上列「196 份 md + 3 份 yaml」为 md/yaml 核心口径；`specification/schema-slice.sql`（全量 DDL 承载）、`specification/api-contract/mcp-tools.json`（MCP 工具契约）、`diagrams/system-architecture.html`（架构总览图）等附属资产不计入该计数（openapi.yaml 已计入 3 yaml 之一）。

## 阅读建议

| 目标 | 路径 |
|:-----|:-----|
| 理解 Kairos 是什么 | 本文档（[docs/README.md](README.md) 索引）|
| 快速体验 | [user/quick-start.md](user/quick-start.md)（约 2 分钟最小闭环教程）→ [user/user-guide.md](user/user-guide.md) |
| 理解认知基础 | [foundation/cognitive-foundation.md](foundation/cognitive-foundation.md) §1.1 → §2.1 |
| 理解系统架构 | [foundation/architecture-v0.1.0.md](foundation/architecture-v0.1.0.md) 全文 |
| 查看待实现项 | [governance/debt-collection.md](governance/debt-collection.md) |
| 部署运行 | [ops/deployment.md](ops/deployment.md) |
| 配置系统 | [ops/configuration.md](ops/configuration.md) |
| 编写代码 | [specification/implementation-map.md](specification/implementation-map.md) → [development/coding-conventions.md](development/coding-conventions.md) |
| 查看用例与操作目录 | [specification/use-cases.md](specification/use-cases.md) / [specification/operation-catalog.md](specification/operation-catalog.md) |
| 算法文档 | [references/vad-coordinate-algorithm.md](references/vad-coordinate-algorithm.md) / [references/value-dimension-entropy.md](references/value-dimension-entropy.md) / [references/usage-load-algorithm.md](references/usage-load-algorithm.md) |
| 系统架构总览图 | [diagrams/system-architecture.html](diagrams/system-architecture.html)（浏览器打开，独立 HTML 版 §0.4.1 架构图） |

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | Kairos 文档索引：全库 52 份文档（51 md + 1 yaml）的分层索引、当前状态声明与阅读建议。 |
| 0.0.2~0.0.88 | 2026-08-10 | （合并占位：changelog 0.0.2~0.0.88 批次的变更未逐条登记于本文档，见 [changelog.md](governance/changelog.md) 全景） |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89，批次索引登记）：索引与计数同步（5 份长文档补章节导航、feature-list/claim-matrix 结构归位、债务 D-442→D-444；核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37 零漂移）；README 批次索引登记不计入 changelog 受改清单（0.0.89 显式声明）。 |
| 0.0.90 | 2026-08-11 | round52 全面深度审计修复批次（changelog 0.0.90，批次索引登记）：索引与计数同步（债务 D-444→D-445、architecture/blueprint 补 H1、中英空格三类收口）；核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37 零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.90 显式声明）。 |
| 0.0.91 | 2026-08-11 | 外部理念吸收批次（changelog 0.0.91，批次索引登记）：LongMemEval 记忆能力评测协议落地（benchmark-plan 新增 §3.15 + §3.12 联动、test-plan 预留 TC-LME-001~、acceptance-criteria §一a 测量任务集补充、absorption-proposals 登记 AP-53）；参数计数与核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37/债务 D-445 零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.91 显式声明）。 |
| 0.0.92 | 2026-08-11 | 定稿收尾批次（changelog 0.0.92，批次索引登记）：D-431 十项待定义参数分类处置（8 项 v1.1 域 + 2 项部署时点，竖切核验无待定义）+ documentation-governance §4 设计基线冻结声明（外部吸收边界 0.0.91 止）+ doc-audit.py GBK 编码崩溃修复；参数计数与核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37/债务 D-445 零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.92 显式声明）。 |
| 0.0.93 | 2026-08-11 | round53 全面深度审计修复批次（changelog 0.0.93，批次索引登记）：索引与计数同步（traceability-map 索引行「104 追踪项」改指 debt-collection 权威账目）；核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37/债务 D-445 零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.93 显式声明）。 |
| 0.0.94 | 2026-08-11 | round54 全面深度审计修复批次（changelog 0.0.94，批次索引登记）：索引与计数同步（traceability-map 版本记录登记缺陷收口、deployment 标准级宪法主权面措辞对齐架构 §0.5、documentation-governance §4「触及即登记」操作细节）；核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37/债务 D-445 零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.94 显式声明）。 |
| 0.0.95 | 2026-08-11 | Obsidian frontmatter 闭合缺陷修复批次（changelog 0.0.95，批次索引登记）：索引与计数同步（adr/risks/slice-implementation-guide/acceptance-criteria/benchmark-plan/test-strategy 六份文档 frontmatter 补立即闭合 `---`、门禁 6.16 盲区增强）；核心计数表 57/参数 374/错误码 43/术语 77/端点 88/操作 66/组件 70/功能 168/ADR 12/声明 37/债务 D-445 零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.95 显式声明）。 |
| 0.0.96 | 2026-08-11 | 定稿审查处置批次（changelog 0.0.96，批次索引登记）：四组全量通读低危缺口收口——use-cases 三信号检索误归 v1.1 勘误、D-446 登记（叙事自洽度评估器降级默认分数）、D-430 分类处置（config show 契约登记 + 其余归 v0.1.0 全量阶段）、认知导航表/RTM/OP-054/deployment 环境变量/架构引用与版本标注等机械性修正 7 处；债务 D-445→D-446；参数计数与其余核心计数零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.96 显式声明）。 |
| 0.0.97 | 2026-08-11 | 竖切代码启动批次（changelog 0.0.97）：状态声明由「文档草稿阶段，无运行代码」更新为「竖切代码开发中（W1~W9 已交付）」；竖切组件代码落点指引（src/ + reports/benchmark-baseline-0.1.0.json）。 |
| 0.0.98 | 2026-08-12 | 版本记录双轨制规则修订批次（changelog 0.0.98，批次索引登记）：索引无实质变更；核心计数零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.98 显式声明）。 |
| 0.0.99 | 2026-08-12 | 竖切首迭代批次（changelog 0.0.99，批次索引登记）：索引无实质变更；核心计数零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.99 显式声明）。 |
| 0.0.100 | 2026-08-12 | 竖切验收核对批次（changelog 0.0.100，批次索引登记）：索引无实质变更；核心计数零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.100 显式声明）。 |
| 0.0.101 | 2026-08-12 | 接入层全通道交付批次（changelog 0.0.101，批次索引登记）：索引无实质变更；核心计数零漂移；README 批次索引登记不计入 changelog 受改清单（0.0.101 显式声明）。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |
| 0.1.1 | 2026-08-12 | Hermes Memory Provider 接入批次（changelog 0.1.1，批次索引登记）：配置参数计数 227 + 附录 A 152 = 379（接入层运行参数 5 项登记）；核心计数表 57/参数 379/错误码 43/端点 88/操作 66/组件 70/功能 168/债务 D-447~449；README 批次索引登记不计入 changelog 受改清单（0.1.1 沿用 0.0.89 显式声明）。 |


