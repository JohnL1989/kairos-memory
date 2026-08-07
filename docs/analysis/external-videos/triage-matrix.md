---
title: 外部理念 × Kairos 分诊矩阵（主对照分析报告）
aliases:
  - 分诊矩阵
tags:
  - kairos
  - analysis
  - external-videos
  - triage
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# 外部理念 × Kairos 分诊矩阵

> **定位**：本批次（100 个 B站视频 + 10 个 GitHub 仓库）的主对照分析报告。每条外部理念（EV-01~NN）一行，判定与 Kairos 的关系：**已覆盖 / 可吸收 / 张力 / 矛盾**，附出处（`VID-XX @ MM:SS` 或 `REPO-XX`）、Kairos 证据、第一性原理评估与处置建议。

> **方法**：逐视频精读（[笔记](notes/)）→ 候选理念提取 → 本矩阵分诊 → [first-principles-review.md](first-principles-review.md) 原理评估 → [absorption-proposals.md](absorption-proposals.md) 建议清单。分诊口径对齐既有外部理念吸收先例（0.0.32/0.0.35/0.0.36）：已覆盖含「互为印证」（独立实现同一设计）；矛盾须论证不采纳理由。

> **素材边界**：视频素材分三级（A 字幕匹配 / B whisper 转写 / C 降级），见 [README.md](README.md) 素材边界声明。C 级素材不产生 EV 条目。

## 分诊统计（截至 2026-08-07，基于 42/100 份视频笔记 + 10 份仓库笔记）

| 分诊 | 数量 | 占比 | 说明 |
|:--|:--|:--|:--|
| 已覆盖（含互为印证） | 待全量统计 | — | 外部独立实现 Kairos 已有机制 |
| 可吸收 | 待全量统计 | — | 增量空间（见 [absorption-proposals.md](absorption-proposals.md) AP-01~18） |
| 张力 | 待全量统计 | — | 取向冲突需取舍（见 AT-01~07） |
| 矛盾 | 0 | 0% | 无与第一性原理/红线直接冲突且论证不采纳者（暂） |

> 注：首批分诊显示外部理念以「已覆盖/支撑」为主（约 55-65%），「可吸收」约 25-30%，「张力」约 10%，「矛盾」为 0——与既有吸收批次结论一致：Kairos 设计未被外部实践推翻，增量在工程细节与治理路径。

## 分诊矩阵（EV 条目）

### A. 价值与真实性（好用≠真实、双副本、差异检验）

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-01 | 记忆是重建而非检索：查询期主动多步重建+证据累积，理论证明 Active ⊃ Passive | VID-09 @ P1 03:25 | 张力 | [架构](../../foundation/architecture-v0.1.0.md) §5.5 | 挑战「检索即读取」隐含假设；重建产物须过差异检验 | 关联 AP-01 |
| EV-02 | 生成补缺：检索给锚点+生成补缺口+知识覆盖选择（KADS 规避 reranker 自恋偏好） | VID-65 @ 03:05 | 张力 | [架构](../../foundation/architecture-v0.1.0.md) §5.5 | 支撑「检索偏好不得污染真实性」；生成内容须来源标记 | 关联 AP-01 |
| EV-03 | 无保留规则时智能体默默压缩丢细节 | VID-56 @ 07:18 | 已覆盖（实证支撑） | [认知基础](../../foundation/cognitive-foundation.md) §2.2 P6 | 支撑「禁止无声丢失维度信息」 | 印证记录 |
| EV-04 | recall 结果临时注入不写回 transcript，防自我污染 | VID-03 @ 12:17 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §8 S-14 | 支撑语境自指禁令 | 印证记录 |
| EV-05 | 自动记忆必须可查看可纠正（Memory Summary Page） | VID-64 @ 03:34 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §1 宪法主权面 | 支撑见证锚定可审计性 | 印证记录 |
| EV-06 | 智能体直接编辑记忆块（Letta memory blocks） | VID-39 @ 03:07 / REPO-06 | 张力 | [架构](../../foundation/architecture-v0.1.0.md) §5.5 | 挑战价值独立性公理；可吸收「可读可审计」透明性 | AT-02 |
| EV-07 | 闭源不可审计记忆引擎（Supermemory 核心闭源） | REPO-01 | 张力 | [架构](../../foundation/architecture-v0.1.0.md) §1.7 审计庭 | 反面案例，印证审计立场必要性 | AT-06 |
| EV-08 | 记忆不更新越强越危险、一次性情境误升长期偏好 | VID-64 @ 06:36 / 11:12 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §5.5 差异检验 | 支撑「校准优先于使用」与差异检验 | 印证记录 |
| EV-09 | 原始账本单向追加+派生视图过滤注销（不可审计的二手结论不可用） | VID-47 @ 03:01 | 已覆盖（强印证） | [架构](../../foundation/architecture-v0.1.0.md) §7.3g ADD-only | 支撑激活-存储解耦+可审计压缩 | 印证记录 |

### B. 时间（双轴、时效、更新）

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-10 | 时间有效性写进记忆结构（valid_until/expiration_date/superseded_by） | VID-27 @ 04:21 / VID-10 @ 07:26 / REPO-07 Graphiti | 可吸收 | [认知基础](../../foundation/cognitive-foundation.md) §1.1 时间双轴 | 支撑时间双轴拆法；结构字段与度量衰减互补 | **AP-02** |
| EV-11 | 事实边四时间字段（valid_at/invalid_at/expired_at/reference_time）+ episode 溯源 | REPO-07 Graphiti | 可吸收 | [认知基础](../../foundation/cognitive-foundation.md) §1.1 | 支撑时间轴工程化 | 并入 AP-02 |
| EV-12 | 双时间戳（写入时间/有效时间）按有效时间过滤 | VID-07 @ 04:19 / VID-67 @ 12:11 | 已覆盖 | [认知基础](../../foundation/cognitive-foundation.md) §1.1 | 与 Kairos 时间双轴同构 | 印证记录 |
| EV-13 | 在线 Soft Update（ADD-only+时间戳）+ 冲突离线消解 | VID-61 @ 04:10 | 已覆盖（强印证） | [架构](../../foundation/architecture-v0.1.0.md) §7.3g | 支撑分域真理观（在线轻写/离线重审） | 印证记录 |
| EV-14 | 被推翻旧事实物理删除 | VID-06 / VID-37 Reset | 矛盾（不采纳） | [架构](../../foundation/architecture-v0.1.0.md) §5.2 版本链 | 与「遗忘非删除」与版本化冲突；物理删除丢失审计路径 | AT-03 |

### C. 存储分层与检索

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-15 | 三层存储（短期/中期/长期）热度值自动调度 | VID-12 @ 04:11 / REPO-04 | 已覆盖（热度值单标量除外） | [架构](../../foundation/architecture-v0.1.0.md) §5 存储层 | 支撑分层存储；热度单标量见 EV-16 | 印证记录 |
| EV-16 | 全局热度单标量参与调度 | VID-12 @ 25:01 / REPO-04 / VID-04 | 张力 | [认知基础](../../foundation/cognitive-foundation.md) §2.1 P6 | 挑战禁跨维标量聚合；影子副本内兼容 | AT-01 |
| EV-17 | 快慢双路径检索（熟悉快速路径/陌生慢速回忆） | VID-58 @ 00:24 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §3.9 R0/R1/R2 | 检索深度分级同构 | 印证记录 |
| EV-18 | 候选集集中度（list entropy）作为检索深度触发信号 | VID-58 @ 04:39 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §3.9 | 补充触发信号维度 | **AP-05** |
| EV-19 | 时间作为独立检索维度（四路检索） | VID-05 @ 11:44 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §7.3a | 评估扩四信号 | **AP-12** |
| EV-20 | 混合检索（语义+BM25+实体）多源独立实现 | REPO-05 Mem0 / VID-16 OpenClaw / VID-05 Hansight | 已覆盖（强印证） | [架构](../../foundation/architecture-v0.1.0.md) §7.3a | 三信号检索独立实证（4×独立实现） | 印证记录 |
| EV-21 | 意图检测先验→检索加权（7 类意图） | REPO-03 Memorix | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §3.2 预测器 | 与预测器职责同域 | **AP-11** |
| EV-22 | 任务内跨轮状态传递（轨迹压缩为状态传给下轮） | VID-62 @ 02:13 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §3 策略层 | 未建模任务内循环记忆粒度 | **AP-06** |
| EV-23 | 主题感知写入切分（内容边界替代窗口边界） | VID-61 @ 03:04 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §7.3 写入管线 | 切分粒度增量 | 建议态 |

### D. 遗忘与巩固

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-24 | 遗忘≠删除：ADD-only + 只删摘要不删原文 | REPO-05 Mem0 / REPO-02 OptMem | 已覆盖（强印证） | [认知基础](../../foundation/cognitive-foundation.md) §2.2 硬约束二 | 遗忘受控优化独立实证 | 印证记录 |
| EV-25 | 遗忘决策懒求值（衰减持续、决策访问时执行） | VID-25 @ 09:43 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §5 遗忘调度器 | 降低扫描成本 | **AP-03** |
| EV-26 | 间隔重复复习时刻表 | VID-25 @ 05:00 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §9 注意力调度器 | 与遗忘调度器互补 | **AP-09** |
| EV-27 | sleep-time compute / 梦境 / 离线全局回顾（低峰期批量巩固） | VID-14 / VID-39 / VID-12 / VID-52 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §5 升华管道 | 升华管道外部实证 | 印证记录 |
| EV-28 | 处理完降温（热度更新后主动降温防自我强化） | REPO-04 MemoryOS | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §5.5 | 防陡升假阳性 | **AP-10** |
| EV-29 | 保留期参数化+免疫规则+可解释保留原因 | REPO-03 Memorix | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §5 遗忘调度器 | 保留原因显式化 | 建议态 |
| EV-30 | 显式间隔复习 vs 频率驱动 | VID-25 | 张力 | [认知基础](../../foundation/cognitive-foundation.md) §2.1 | 复习计划 vs 使用驱动 | 建议态 |

### E. 记忆归属与边界

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-31 | 记忆跟着项目走（项目级锚定） | VID-28 @ 01:46 / REPO-03 | 张力 | [架构](../../foundation/architecture-v0.1.0.md) §1 | Kairos 以主体为边界；关联 T-002 | AT-05/AP-13 |
| EV-32 | 五维独立轴记忆模型（kind/scope/state/source/portability+状态机） | REPO-03 Memorix | 可吸收 | [认知基础](../../foundation/cognitive-foundation.md) §1.1 | 五轴正交性独立印证（治理轴集） | 建议态（强） |
| EV-33 | 可推导信息绝不存（代码即权威来源） | VID-06 @ 07:05 / VID-10 @ 03:35 | 已覆盖 | [认知基础](../../foundation/cognitive-foundation.md) §1.3 编码门控 | 支撑编码门控准则 D.6 | 印证记录 |
| EV-34 | 决策理由（推理记忆）显式化为记忆类型 | VID-28 @ 03:49 | 已覆盖 | [认知基础](../../foundation/cognitive-foundation.md) §1.1 认知完整性轴 | 认知完整性承载 | 印证记录 |
| EV-35 | 操作轨迹记忆（改文件/跑命令/踩坑）为一等记忆类型 | VID-20 @ 00:57 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §3.2 前瞻记忆 | 记忆类型增量 | 建议态 |
| EV-36 | 约束记忆带 applies_to 作用域+覆盖式保守更新 | VID-46 @ 13:17 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §3.7 契约 | 呼应契约运行时投影 | 建议态 |

### F. 写入链路与工程

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-37 | 稳定 Memory Key 规范化策略 | VID-34 @ 07:29 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §5 存储层 | 写路径工程细节 | **AP-04** |
| EV-38 | 幂等+乐观锁事务提交（事实源/日志/Outbox 三分） | VID-34 @ 09:49 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §5 | 与 ADD-only 同向 | **AP-04** |
| EV-39 | 索引是派生视图可重建 | VID-34 @ 10:43 / REPO-02 OptMem | 已覆盖（强印证） | [架构](../../foundation/architecture-v0.1.0.md) §5.2 | 影子副本可重建性外部实证 | 印证记录 |
| EV-40 | 八阶段 ADD 管线（单次 LLM 调用提取，prompt 明示 sole operation is ADD） | REPO-05 Mem0 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §7.3g | ADD-only 最强工程实证 | 印证记录 |
| EV-41 | 压缩/重置边界作为主动知识转移事件（Flush Memories） | VID-03 @ 13:52 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §3.7 | 生命周期事件显式化 | 建议态 |
| EV-42 | 固定条数摘要压缩（纯启发式） | VID-24 / VID-45 | 张力 | [认知基础](../../foundation/cognitive-foundation.md) §2.2 硬约束一 | 启发式 vs 可审计压缩 | AT 记录 |

### G. 治理与监控

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-43 | 记忆成熟度评估清单（原始事实/视图/读写决策/审计/回放五问） | VID-47 @ 05:20 / VID-31 @ 15:29 | 可吸收 | [质量](../../quality/acceptance-criteria.md) | 验收工具增量 | **AP-07** |
| EV-44 | write/search 比监控指标（0.84=只写不读） | VID-11 @ 00:13 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §10.5 指标族 | 低成本高诊断价值 | **AP-08** |
| EV-45 | 记忆是认知技能非存储模块（先查后写可训练） | VID-11 @ 01:57 | 张力 | [架构](../../foundation/architecture-v0.1.0.md) §8 S-12 | 记忆操作混入动作空间 vs 探索边界 | AT-05 |
| EV-46 | 三笔账分离（容量/存储/模型实际看见） | VID-44 @ 01:50 | 可吸收 | [认知基础](../../foundation/cognitive-foundation.md) §1.1 | D-313 可及性轴立项论据 | **AP 参考** |
| EV-47 | 后台 Review 兜底（连续 10 轮无写入触发复盘） | VID-03 @ 17:47 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §2.6.3 防抖反射执行器 | 印证 | 印证记录 |
| EV-48 | 谁测的（第三方验证原则）：评测罗生门警示 | VID-8 @ 05:15 | 已覆盖 | [架构](../../foundation/architecture-v0.1.0.md) §1.7 审计庭 | 与 Kairos 外部审计经验同构 | 印证记录 |
| EV-49 | MetaLLM 审查+门控脚手架自动迭代 | VID-11 @ 03:40 | 可吸收 | [架构](../../foundation/architecture-v0.1.0.md) §10.14 | 元认知层增量 | 建议态 |

### H. 论文深读（2026 论文批次，[papers/](papers/) PAPER-01~09）

| 编号 | 外部理念 | 出处 | 分诊 | Kairos 证据 | 第一性原理评估 | 处置建议 |
|:--|:--|:--|:--|:--|:--|:--|
| EV-50 | LLM 整合制造错误记忆（54% 失败率；episodic-only 胜过整合式） | PAPER-01 持续更新衰退 | 已覆盖（强实证支撑） | [架构](../../foundation/architecture-v0.1.0.md) §5.5 / [认知基础](../../foundation/cognitive-foundation.md) §2.2 | 整合步骤本身是错误来源——支撑防御取向；挑战「整合即自演化」叙事 | 关联 AP-19 |
| EV-51 | 检索假设被证伪：查询语义相似≠所需记忆（84% vs 14.4%） | PAPER-02 InMind | 张力 | [认知基础](../../foundation/cognitive-foundation.md) §2.1 间接度 / D-313 | 支撑间接度排序位与可及性轴立项；挑战查询驱动检索唯一入口 | 关联 AP-22 |
| EV-52 | 零 token 记忆操作：轨迹为源+图扩散+时间层级+确定性校准 | PAPER-03 Zero-Mem | 已覆盖（强印证）+ 可吸收增量 | [架构](../../foundation/architecture-v0.1.0.md) §7.3a / §7.3g / §7.3f | 轨迹为源/非 LLM 索引/三信号独立实证 | 关联 AP-27 |
| EV-53 | 证据-修订配对技能演进 + 评估侧隔离 | PAPER-04 SkillHone | 已覆盖（支撑） | [架构](../../foundation/architecture-v0.1.0.md) §5.5 / §8 S-14 | 见证锚定技能层实证；评估侧隔离=S-14 结构性隔离 | 关联 AP-24/26 |
| EV-54 | 成本-保真三 regime：粗摘要悬崖=无声丢失代价形式化 | PAPER-05 ACM | 已覆盖（支撑+互为印证） | [认知基础](../../foundation/cognitive-foundation.md) §2.2 硬约束一 / §1.9 CRI | validated compaction=可审计压缩成本论证；CRI 被列为未解决维度 | 关联 AP-25 |
| EV-55 | 恢复契约六属性 + 同一 API 中断/崩溃两种语义警示 | PAPER-06 REMIT | 已覆盖（强支撑+警示） | [架构](../../foundation/architecture-v0.1.0.md) §2.6.3 / §3.7 | CrewAI 违背书面声明=「契约是运行时投影」实证；契约须覆盖全部恢复路径 | 关联 AP-20/21 |
| EV-56 | GRAM 知识开关：路由而非抹除，物理移除优于抑制 | PAPER-07 GRAM | 可吸收（机制类比） | [架构](../../foundation/architecture-v0.1.0.md) §5.2 检索路径抑制器 / §8 S-19 | 与抑制器同一设计模式两层实现；呼应遗忘复发警示 | 关联 AP-23 |
| EV-57 | 遗忘三样本相对检验：遗忘须在双副本两层都生效 | PAPER-08 遗忘审计 | 可吸收（统计方法论） | [架构](../../foundation/architecture-v0.1.0.md) §1.7 审计庭 / §8 S-19 | 黑盒审计实证化；「内容不可恢复≠行为无痕」边界声明 | 关联 AP-23 |
| EV-58 | Δ-Mem 增量存储：仅存增量而非全量（0.12% 参数开销） | PAPER-09 Δ-Mem | 可吸收（存储模式） | [架构](../../foundation/architecture-v0.1.0.md) §5 记忆版本管理 | 写放大对齐；须过 P6 门禁（可重建+无无声丢失） | 关联 AP-28 |

> **勘误**：用户映射分析（`outputs/kairos-papers-mapping.md`）称「KAIROS_RETRIEVAL_LINK_WEIGHTS 尚未定义」已过时（`configuration.md` 0.0.34 已回填默认值）；D-23 位于 `adr.md` 决策批次表内。

---

## T-002 实例样本（外部校准源进入体系的实践观察）

> 本批次作为「外部校准源以什么形态进入体系」的活样本，记录以下观察（**不修改** [risks.md](../../governance/risks.md)，观察与建议分离）：

| 观察维度 | 本批次实例 |
|:--|:--|
| 来源分类 | 视频（科普/论文解读/产品演示/官方发布）× 仓库（README 口径/源码实证）——来源异质性高 |
| 断言强度 | 视频声称（弱，需源码验证）< README 口径（中）< 源码实证（强）——本批次 10 个仓库中源码级验证 8 个 |
| 可信度标注 | 串台字幕（65%）→ 降级；whisper 转写（中，谐音错字）；字幕匹配（高）；源码（最高）——四级可信度体系在实践中自然形成 |
| 唯一性证明成本 | 每条 EV 的「Kairos 无对应物」断言需人工核实（门禁 check 无法验证缺失）；本批次 49 条 EV 中约 10 条涉及缺失断言，均经人工比对 |
| 时效性 | 视频多为 2025-2026 产物，论文类时效性高（ICML/ACL/WWW 2026），框架类迭代快（Letta legacy、Zep 弃用社区版）——外部校准源需要时效标注 |
| 结论 | 外部校准源的「一等公民化」需要：来源分类、断言强度标注、可信度分级、时效字段、缺失断言核验流程——本批次实践为此积累了实例基础 |

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 基于 42/100 份视频笔记 + 10 份仓库笔记的首批 49 条 EV 分诊；T-002 实例样本节建立；剩余视频笔记完成后补充 |
