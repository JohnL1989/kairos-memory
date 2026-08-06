---
title: Kairos 文档索引
aliases:
  - 文档目录
  - 文档体系
tags:
  - kairos
  - documentation
created: 2026-07-18
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 文档索引

> **当前状态**：**文档草稿阶段，无运行代码**。Kairos 为全面重新设计的系统，本文档库尚无可运行的完整 Kairos 系统。feature-list 列出的 **168 项能力（43 核心 + 125 扩展；traceability-map 追溯其中 43 项与认知声明的映射）** 处于架构就绪状态，核心引擎代码未启动。

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

## 审计与决策记录（过程产物）

| 路径 | 内容 |
|:-----|:-----|

## 运维文档

| 路径 | 内容 |
|:-----|:-----|
| [`ops/deployment.md`](ops/deployment.md) | **部署指南** — 三级部署规模（轻量/标准/全量）+ 三级能力梯度（全量/标准/内核），环境变量、Docker 参考 |
| [`ops/configuration.md`](ops/configuration.md) | **配置参数参考** — 223 项参数（2026-08-05 核定；口径：表格行首为 `KAIROS_*` 的参数定义行；含附录 A 全库索引 148 项，总计 371 项）+ 动态调参规则 |
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
| [`references/glossary.md`](references/glossary.md) | **术语表** — 67 条中英文术语对照（7 个分类表，不含版本记录；0.0.22 增补「热度层级衰减」「摄入侧情绪保护」「噪音规则库」；0.0.29 增补「编译器」「结构化通信单元」「编译净化」「检索深度分级」「命名配置集」「竖切」「结构性记忆」） |
| [`references/error-reference.md`](references/error-reference.md) | **错误参考** — 11 类 38 个错误码 |
| [`references/traceability-map.md`](references/traceability-map.md) | **需求可追溯性映射表** — 43 能力↔37 声明↔100 追踪项↔16 差距交叉映射 |
| [`references/domain_keywords.yaml`](references/domain_keywords.yaml) | **领域关键词表** — 领域专有词频配置 |
| [`references/usage-load-algorithm.md`](references/usage-load-algorithm.md) | **使用负载计量算法** |
| [`references/vad-coordinate-algorithm.md`](references/vad-coordinate-algorithm.md) | **VAD 情感坐标算法** |
| [`references/value-dimension-entropy.md`](references/value-dimension-entropy.md) | **价值维度熵值守护算法** |
| [`references/concept-tiers.md`](references/concept-tiers.md) | **概念分级速查表** — L1/L2/L3 三级概念归类 + 一句话类比 + 代码映射 + 依赖图（0.0.16 新增） |
| [`references/capability_matrix.yaml`](references/capability_matrix.yaml) | **认知维度承载能力矩阵** — 各版本对认知维度的承载程度与恢复债编号（0.0.16 新增） |

总计：55 份核心文档**（foundation 4 + specification 12 + development 6 + governance 9 + ops 6 + quality 4 + security 2 + user 2 + references 9(7 md+2 yaml) + README 1 = 55，即 **53 份 md + 2 份 yaml**；0.0.16 新增 `concept-tiers.md` 与 `capability_matrix.yaml`；0.0.29 新增 `development/engineering-workflow.md`；审计过程材料（审计报告/审计历史摘要）不随仓库分发，处置记录见 changelog 各批次）**。其中 [foundation/architecture-v0.1.0.md](foundation/architecture-v0.1.0.md) 为核心架构规格（全体系以架构文档为设计权威）。

## 阅读建议

| 目标 | 路径 |
|:-----|:-----|
| 理解 Kairos 是什么 | 本文档（[docs/README.md](README.md) 索引）|
| 理解认知基础 | [foundation/cognitive-foundation.md](foundation/cognitive-foundation.md) §一 → §二 |
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
| 0.0.2 | 2026-08-03 | 08-03 审计修复批次：全库 135 项修复与 15 项决策（D-01~D-15）的索引状态同步，新增 reviews/ 审计记录索引。 |
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
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次索引同步（依 comprehensive-documentation-audit）：0.0.13 版本批次补登；api-spec 注册归档/恢复端点（业务端点 78→80，物理总数 81）；端点计数口径注记；全库正文双空格清零。 |
| 0.0.16 | 2026-08-05 | Marvis 建议落地批次索引同步：新增 [references/concept-tiers.md](references/concept-tiers.md) 与 [references/capability_matrix.yaml](references/capability_matrix.yaml)（核心文档 52→54）；决策记录入「审计与决策记录」索引（详见 [changelog.md](governance/changelog.md) 0.0.16）。 |
| 0.0.17 | 2026-08-05 | Marvis 其余建议批次索引同步：R-1~R-10 处置（详见 [changelog.md](governance/changelog.md) 0.0.17）。 |
| 0.0.18 | 2026-08-05 | 审计归档批次索引同步：reviews 10 份报告归档为 1 份审计历史摘要（决策 D-01~D-27 迁移至 `adr.md`「审计决策迁移」节）;审计索引节 8 行合并为 1 行。 |
| 0.0.19 | 2026-08-05 | 第四轮全库深度审计修复批次索引同步：blueprint 文件名 v1.1+ → v1.1（补登，原缺失）。 |
| 0.0.20 | 2026-08-05 | 第五轮全库深度审计修复批次索引同步：阅读建议补用例/操作目录/算法文档入口行（详见 [changelog.md](governance/changelog.md) 0.0.20）。 |
| 0.0.21 | 2026-08-05 | 系统架构总览图批次索引同步：阅读建议补 `diagrams/system-architecture.html` 入口（独立 HTML 版 §0.4.1 架构图，详见 [changelog.md](governance/changelog.md) 0.0.21）。 |
| 0.0.22 | 2026-08-05 | 外部项目理念吸收批次索引同步（noah-gen3-type2）：配置参数计数同步（正文 220→223、附录 A 148 项不变、总计 368→371）；术语计数同步（glossary 57→60 条，增补热度层级衰减、摄入侧情绪保护、噪音规则库）；详见 [changelog.md](governance/changelog.md) 0.0.22。 |
| 0.0.23 | 2026-08-05 | 内容架构全面审视批次索引同步：认知基础与系统架构结构修复（详见 [changelog.md](governance/changelog.md) 0.0.23）。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次索引同步：implementation-map 索引行组件数 40+→70（3-02）；版本记录补登 0.0.19（2-04，详见 [changelog.md](governance/changelog.md) 0.0.24）。 |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（changelog 0.0.29）：新增 [development/engineering-workflow.md](development/engineering-workflow.md)（核心文档 54→55、53 md + 2 yaml）；glossary 60→67 条同步。 |
| 0.0.30 | 2026-08-06 | 仓库整洁化：审计过程材料移出仓库（reviews/ 目录与 audit-history-summary 移除、scripts/_deep_audit_out.json 纳入 .gitignore）；审计历史索引行移除。 |
| 0.0.31 | 2026-08-06 | 第十一轮全库深度审计修复批次（changelog 0.0.31）：操作目录 53→66 项；术语表推理皮层别名（计数不变）。 |
