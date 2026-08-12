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
status: draft
---

# Kairos 文档索引

> **当前状态**：**竖切代码开发中（v0.1.0-slice，W1~W9 已交付）**。Kairos 为全面重新设计的系统，本文档库的竖切组件已有可运行代码（`src/` 下 15 张竖切表、记忆 CRUD/双副本、路径空间、事件总线、三信号检索、遗忘、身份注册表、审计 HMAC 链、校准/降级/冻结、REST 21 端点 + CLI 15 条）；全量 v0.1.0 的 168 项能力（43 核心 + 125 扩展）仍处于架构就绪状态，核心引擎（升华/图谱/WM 等竖切外组件）未启动。代码启动与竖切交付进展见 [changelog](governance/changelog.md)。

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
| [`ops/configuration.md`](ops/configuration.md) | **配置参数参考** — 227 项参数（2026-08-10 核定；口径：表格行首为 `KAIROS_*` 的参数定义行；含附录 A 全库索引 147 项，总计 374 项）+ 动态调参规则 |
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
| 0.0.2 | 2026-08-03 | 2026-08-03 审计修复批次：全库 135 项修复与 15 项决策（D-01~D-15）的索引状态同步，新增 reviews/ 审计记录索引。 |
| 0.0.3 | 2026-08-04 | 配置参数计数同步（市场理念吸收）：192→193 项正文、总计 340→341 项。 |
| 0.0.4 | 2026-08-04 | 术语计数同步（市场理念吸收）：glossary 53→56 条（增补双时态、构造性生成、记忆压力）。 |
| 0.0.5 | 2026-08-04 | ADR 计数同步：10→12 项已采纳（ADR-011 迁移工具 / ADR-012 向量投影）。 |
| 0.0.6 | 2026-08-04 | 全库深度审计修复：蓝图索引链接文字去重复并标注 §5.5 交付例外（D-05）；数据模型表数口径修正（删除"实交付 55"表述）；新增「审计与决策记录」索引节。 |
| 0.0.7~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.7~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：claim-matrix 37 项计数注记；版本记录模板统一。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：配置参数计数同步（210+148=358）、版本记录跳号占位。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次：决策 D-05 引用标注「决策」前缀。 |
| 0.0.13 | 2026-08-04 | 认知×架构交叉审计修复批次（决策 D-16~D-27）：本条目为 0.0.15 补登（原缺失，见 [changelog.md](governance/changelog.md) 0.0.13）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次索引同步：术语计数 56→57（增补并行审查）；全库 31 份文档 0.0.14 条目登记（详见 [changelog.md](governance/changelog.md) 0.0.14）。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次索引同步（依 comprehensive-documentation-audit）：0.0.13 版本批次补登；api-spec 注册归档/恢复端点（业务端点 78→80，物理总数 81）；端点计数口径注记；全库正文双空格清零。（0.0.25 勘误联动：现行口径为业务端点 85 + 3 无前缀 = 物理 88，见 api-spec 端点计数口径） |
| 0.0.16 | 2026-08-05 | 外部建议落地批次索引同步：新增 [references/concept-tiers.md](references/concept-tiers.md) 与 [references/capability_matrix.yaml](references/capability_matrix.yaml)（核心文档 52→54）；决策记录入「审计与决策记录」索引（详见 [changelog.md](governance/changelog.md) 0.0.16）。 |
| 0.0.17 | 2026-08-05 | 外部建议其余批次索引同步：R-1~R-10 处置（详见 [changelog.md](governance/changelog.md) 0.0.17）。 |
| 0.0.18 | 2026-08-05 | 审计归档批次索引同步：reviews 10 份报告归档为 1 份审计历史摘要（决策 D-01~D-27 迁移至 `adr.md`「审计决策迁移」节）;审计索引节 8 行合并为 1 行。 |
| 0.0.19 | 2026-08-05 | 第四轮全库深度审计修复批次索引同步：blueprint 文件名 v1.1+ → v1.1（补登，原缺失）。 |
| 0.0.20 | 2026-08-05 | 第五轮全库深度审计修复批次索引同步：阅读建议补用例/操作目录/算法文档入口行（详见 [changelog.md](governance/changelog.md) 0.0.20）。 |
| 0.0.21 | 2026-08-05 | 系统架构总览图批次索引同步：阅读建议补 `diagrams/system-architecture.html` 入口（独立 HTML 版 §0.4.1 架构图，详见 [changelog.md](governance/changelog.md) 0.0.21）。 |
| 0.0.22 | 2026-08-05 | 外部项目理念吸收批次索引同步：配置参数计数同步（正文 220→223、附录 A 148 项不变、总计 368→371）；术语计数同步（glossary 57→60 条，增补热度层级衰减、摄入侧情绪保护、噪音规则库）；详见 [changelog.md](governance/changelog.md) 0.0.22。 |
| 0.0.23 | 2026-08-05 | 内容架构全面审视批次索引同步：认知基础与系统架构结构修复（详见 [changelog.md](governance/changelog.md) 0.0.23）。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次索引同步：implementation-map 索引行组件数 40+→70（3-02）；版本记录补登 0.0.19（2-04，详见 [changelog.md](governance/changelog.md) 0.0.24）。 |
| 0.0.25~0.0.28 | 2026-08-06 | （合并占位：changelog 0.0.25~0.0.28 批次的变更未逐条登记于本文档，见 [changelog.md](governance/changelog.md) 全景——其中 0.0.25 含 api-spec 端点计数勘误 80/81 → 85/88，见版本记录 0.0.15 条目联动注记） |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（changelog 0.0.29）：新增 [development/engineering-workflow.md](development/engineering-workflow.md)（核心文档 54→55、53 md + 2 yaml）；glossary 60→67 条同步。 |
| 0.0.30 | 2026-08-06 | 仓库整洁化：审计过程材料移出仓库（reviews/ 目录与 audit-history-summary 移除、scripts/_deep_audit_out.json 纳入 .gitignore）；审计历史索引行移除。 |
| 0.0.31 | 2026-08-06 | 第十一轮全库深度审计修复批次（changelog 0.0.31）：操作目录 53→66 项；术语表推理皮层别名（计数不变）。 |
| 0.0.32 | 2026-08-06 | 第三方分析分诊 + 全量债务 v0.1.0 可实现性评估批次（changelog 0.0.32，未触及本文档，占位登记）。 |
| 0.0.33 | 2026-08-06 | round12/round13 深度审计修复批次（changelog 0.0.33）：删除「审计与决策记录（过程产物）」空节。 |
| 0.0.34 | 2026-08-06 | 第十四轮全库深度审计修复批次（changelog 0.0.34）：治理面计数统一（§0.4.1 图题/结构原则 → 两个正交治理面 + HTML 图题同源联动）；治理输入表述修正；检索权重单一权威（三链路标历史配比、四链路 0.50/0.20/0.10/0.20 唯一默认，configuration 同步）；§10.24 补 D-006/D-008/D-016/D-019；§5.2 节内导航补 5 节点；健康接口/差异检验引用修正；门禁新增 6.17/6.18/6.19。 |
| 0.0.35 | 2026-08-06 | 第三方分析分诊（changelog 0.0.35）：架构 §3.9 补检索深度分级 ↔ 内容读取层级映射注记（R-01，R0 指针/R1 摘要仅定位/R2 全文唯一可用）；无债务登记。 |
| 0.0.36 | 2026-08-06 | 第三方分析分诊（changelog 0.0.36）：架构 §3.3 补使用权重影子副本可重建性声明（R-03）；detailed-design §4 补升华产物 verbatim 拒绝护栏（R-02）；无债务登记。 |
| 0.0.37 | 2026-08-06 | round15 全面深度审计修复批次（changelog 0.0.37）：45 项问题闭环（1 高/19 中/25 低）——M-03 三义统一、MCP 15/术语 68/CLI 25 计数联动、conversation_messages parts 列与 journal_entries episode 归因列补录、P3-19~25 债务补登 D-415~D-421、否决权「默认优先级」口径全库统一、三信号/四链路管线关系声明、意图契约第五契约说明、版本注记纪律收敛、竖切 REST 21 与 CLI 补注册等。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：全面审计 113 项闭环（3 高/64 中/46 低）——推论幽灵引用闭环（认知基础 §2.1 补五条推论）、帕累托三轴口径统一、零版本标记全库收敛；路径空间统一下划线；参数计数 224+146=370、glossary 68→69；35 份文档版本记录同步。 |
| 0.0.40 | 2026-08-07 | 外部视频分析批次（changelog 0.0.40）：新增「分析文档」索引节（[analysis/external-videos/](analysis/external-videos/README.md) 独立目录，100 视频 + 15 仓库对照分析，不纳入核心文档计数）；实测 B站 AI 字幕串台问题；脚本入库 2 个；核心设计文档零改动；详见 changelog 0.0.40。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：分析目录计数 129→131 修正。 |
| 0.0.43 | 2026-08-07 | 文档审计修复批次（changelog 0.0.43）：README 总计数口径修订（184 份 md + 3 份 yaml：新增 specification/api-contract/openapi.yaml 计入 yaml 总数，核心文档 55→56）；补「分析文档」目录边界说明（审计报告 F8）；详见 changelog 0.0.43。 |
| 0.0.44 | 2026-08-08 | 外部理念吸收补落地批次（changelog 0.0.44）：README 计数口径同步（总计 185 份 md + 3 份 yaml、核心 56 份）。 |
| 0.0.45~0.0.46 | 2026-08-08 | round18/round19 审计闭环批次（changelog 0.0.45/0.0.46）：README 计数/索引/零版本标记收敛。 |
| 0.0.47 | 2026-08-08 | 外部论文分析批次（changelog 0.0.47）：分析目录索引与计数同步（132 份）。 |
| 0.0.48~0.0.50 | 2026-08-08 | （合并占位：changelog 0.0.48~0.0.50 批次的变更未实质触及本文档索引/计数，见 [changelog.md](governance/changelog.md) 全景） |
| 0.0.51 | 2026-08-08 | round22 审计修复批次（changelog 0.0.51）：错误参考计数 38→40（新增 ERR-SYS-006/007，对应启动校验审计事件）。 |
| 0.0.52~0.0.56 | 2026-08-08 | （合并占位：changelog 0.0.52~0.0.56 批次的变更未实质触及本文档索引/计数，见 [changelog.md](governance/changelog.md) 全景） |
| 0.0.57 | 2026-08-08 | round25 全面深度审计修复批次（changelog 0.0.57，补登）：版本记录补登 0.0.44~0.0.50 / 0.0.52~0.0.56 段（版本记录链断裂修复），本文档索引/计数无实质变更。 |
| 0.0.59 | 2026-08-08 | round26 全面深度审计修复批次（changelog 0.0.59，补登）：错误码计数 40→42（新增 ERR-CTR-003 / ERR-CTR-004，「11 类 40 个错误码」口径同步）。 |
| 0.0.64 | 2026-08-08 | round30 全面深度审计修复批次（changelog 0.0.64，补登）：配置参数计数同步 370→373（正文 226 + 附录 A 147）。 |
| 0.0.66 | 2026-08-09 | round32 全面深度审计修复批次（changelog 0.0.66）：版本记录补登批次——0.0.57/0.0.59/0.0.64 三行为前序批次实质变更漏登记，本批补登（governance §4「触及即登记」）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.79 | 2026-08-09 | round41 全面深度审计修复批次（changelog 0.0.79）：版本记录 0.0.2 行日期补年份（「08-03」→「2026-08-03」，格式统一）。 |
| 0.0.80 | 2026-08-09 | round42 全面深度审计修复批次（changelog 0.0.80）：引用/口径收口 + 格式收尾 + 术语登记（glossary 70→76）——详见 changelog 0.0.80 叙述节。 |
| 0.0.81 | 2026-08-10 | round43 全面深度审计修复批次（changelog 0.0.81，补登）：VAD 条件激活（G-02）权威落点收敛至架构 §3.2；安全规格 S-07/S-17 语义修正；债务章节导航补全。 |
| 0.0.82 | 2026-08-10 | round44 门禁建议落实批次（changelog 0.0.82，补登）：新增 6.34 changelog 结构纪律 + 6.35 红线语义互斥词对检查。 |
| 0.0.83 | 2026-08-10 | round45 全面深度审计修复批次（changelog 0.0.83，补登）：intention 契约能力粒度切分、P6 监控基线增量制、备份容量满载口径等 3 高 4 中 4 低全闭环。 |
| 0.0.84 | 2026-08-10 | round46 门禁建议落实批次（changelog 0.0.84，补登）：新增 6.36 版本归属互斥 / 6.37 表格范围词一致性 / 6.38 阈值监控自洽性（WARN 级软门禁首轮）。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85）：错误码 42→43（新增 ERR-CTR-005 幂等键冲突）——README §索引 错误参考行计数同步；另补登前序 0.0.81~0.0.84 四行（governance §4「触及即登记」）；frontmatter updated/last_reviewed 同步 2026-08-10。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87）：术语计数 76→77（glossary 补「上下文腐烂」）+ 认知基础引用改数字（§一→§二 → §1.1→§2.1，小节号）。 |
| 0.0.88 | 2026-08-10 | round50 全面深度审计修复批次（changelog 0.0.88）：引用落点错位 5 处（feature-list R-23/R-24/R-27/SF-18 与 data-model QueryAnalyzer 的架构 §2.1→§2.6.x）+ blueprint DERIVED_FROM 版本边界措辞 + 分析批次过时计数 4 处 + concept-tiers 意图契约注记 + use-cases 场景 4 表述精确化；核心计数零漂移。 |
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
