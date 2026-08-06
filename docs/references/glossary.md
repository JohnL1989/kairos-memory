---
title: Kairos 术语表
aliases:
  - Glossary
  - 术语表
tags:
  - kairos
  - references
  - glossary
created: 2026-07-20
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 术语表

> **定位**：Kairos 系统关键术语中英文对照及定义。每条术语附源文档引用，方便追溯完整上下文。

**快速查阅**：使用 Ctrl+F 搜索术语名。定义源自 [foundation/architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)（架构）、[foundation/cognitive-foundation.md](../foundation/cognitive-foundation.md)（认知基础）或 `references/` 算法参考文档。算法参考术语（使用负载计量器、VAD 坐标、价值维度熵等）详见各自算法文档，本文不重复。

---

## 一、系统层级 System Levels

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 外部治理接口 | External Governance Interface | 宪法主权面的同义别名（全库两称并存，非更名完成态）——接收外部校准信号、执行宪法修订与强制冻结，对内部环行使单向旁观 + 至高否决权。与监督平面（审计庭所在面）为**两个正交治理面，并未合并**。全库正文仍以「宪法主权面」为主要表述，两称指同一治理面（见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.4 治理面命名对照与 §1.7） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.7 |
| 身份面 | Identity Plane | 独立正交治理面，以否决权而非排名介入辞典式排序。身份不在此链中（否决查询而非排序），与宪法主权面并列（外部安全高于内部同一性） | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §2.1 / 架构 §1 |
| 元认知层 | Metacognition Layer | 监控、评估、调节下层行为。含检测器族（耦合计监测器、VAD 独立性测试器）、治理器族、自观察记忆 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2 |
| 策略层 | Strategy Layer (PM) | 记忆路由与协调层——预测器、调节器、价值上下文管理器、路径注册表 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3 |
| 存储层 | Storage Layer | 统一长期记忆（LTM），含双副本、路径空间、升华管道、遗忘调度器、关系索引 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| 工作记忆层 | WM Layer | 当前操作缓冲区——模拟隔离区、沙箱验证环、多路径融合、WM调度预处理器 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §6 |
| 接入层 | Access Layer | 外部接口——REST API、CLI、Agent Tool、多源摄取、干扰控制 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 |

## 二、核心记忆概念 Core Memory

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 五轴度量空间（正交性假设） | Five-axis Metric Space | 认知基础定义的完整价值模型——使用、见证、时间、认知完整性、可及性五轴。**区别于**「五维使用价值向量」（使用价值轴的五个子维度，见 usage-load-algorithm）和「三信号混合检索」（搜索排序的三个信号源：语义+自适应BM25+实体加成，见 architecture [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a） | 认知基础 §1.1 |
| 多重记忆 | Multiple Memory | 同一经验可同时编码为情景/语义/程序三类（叙事自洽度通过 `identity_relevance` 参数而非独立类型承载），三类间有因果/独立/层级/竞争关系 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.2 |
| 潜伏势能 | Latent Potential | 零使用价值记忆的保留依据，由元认知层盲区探测触发重估 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| 升华管道 | Sublimation Pipeline | raw→item→strategy→behavior 四阶段渐进提纯，空闲驱动 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| 遗忘调度器 | Forgetting Scheduler | v0.1.0 以单曲线指数衰减实现（`freshness = 2^(-days_since_last_access / HALF_LIFE)`，阈值判定 active/stale/archived）计算遗忘得分，触发归档；v1.1 升级为二维遗忘曲面（去语境化程度×年龄，使用频率为调制因子） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| 路径空间 | Path Space | 确定性检索手段，`kairos://` 格式，为第一检索入口，向量搜索退居辅助 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| 关系索引 | Relation Index | 四类记忆关系（因果/部分独立/弱层级/竞争）+ 粒度关系（部分-整体）+ 派生关系（derived_from）的独立索引空间 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| 双时态 | Bitemporal | 记忆记录区分事件时间（occurred_at——事实实际发生时间）与事务时间（created_at——记录写入系统时间）双轨；「纠正而不遗忘」由 superseded_by + 版本链 + 知识演化承载；`as_of(ts)` 时间点查询回答「该时点系统已知的事实状态」 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 双时态声明 |
| 构造性生成 | Constructive Generation | 检索即重建的机制延伸——检索线索的表征痕迹不足/缺失/需跨模式组合时，以痕迹为约束、以当前上下文为目标构造缺失表征；产物入模拟隔离区（S-13），转正走沙箱验证环，永不直接注入见证锚定主副本 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.3 构造性生成声明 |
| 结构性记忆 | Structural Memory | 持有结构性内容与压缩轨迹的记忆（`structural_value`/`structural_value_reasons`/`structural_value_updated_at`/`compression_trail` 字段族）——与普通语义记忆区分，受 `is_structure ↔ structural_value` 双向 CHECK 约束 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 结构性记忆 / schema-slice.sql |
| 检索深度分级 | Retrieval Depth Grading | 按任务复杂度与运行时 CRI 状态分级的检索深度——R0 浅层 / R1 中层 / R2 深层；策略层依据当前 CRI 值主动降级（CRI>0.4 降 R1、CRI>0.6 降 R0） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.9 |

## 三、契约与激活 Contracts & Activation

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 常驻契约 | Permanent | 核心规则/宪法级偏好，不参与遗忘评估（S-10 见证豁免保护） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 |
| 按需契约 | Ondemand | 日常写入默认选项，低使用权重时被遗忘 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 |
| 环境契约 | Environmental | 高相关信息（如当天上下文），环境变化时自然过期 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 |
| 临时契约 | Temporary | 中间状态/临时缓存，空闲时优先清理 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 |
| 激活-存储解耦 | Activation-Storage Decoupling | 契约决定激活策略而非存储位置——所有记忆统一管理，激活/检索/衰减策略因契约而异 | 认知基础 P3 |
| 意图契约 | Intention Contract | 前瞻记忆专用——位于 `kairos://_system/intentions/`，不受遗忘调度器评估 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 前瞻记忆段（`kairos://` 意图契约） |
| 归档 | Archived | 系统被动——升华产物/低使用记忆从主存储移至冷存储，可复兴（关联检索触发） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| 抑制 | Suppressed | 归档子态——用户主动定向遗忘操作，将记忆标记为 suppressed（软删除，抑制检索但保留数据，可撤销），位于 Archived 状态空间内 | [api-spec.md](../specification/api-spec.md) §3 |
| 硬删除 | Delete | 用户主动——物理删除数据，仅用于临时契约，不可恢复（清理前写入审计日志 `expiry_cascade_delete`，见架构 §5.2 forgetAfter） | [api-spec.md](../specification/api-spec.md) §3 |

## 四、价值体系 Value System

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 使用价值轴 | Usage Value Axis | 使用价值的多维特征空间——按目的性（检索/验证/贡献）、方式性（模拟/非模拟）、意识性（内隐/外显）区分 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 |
| 见证价值轴 | Witness Value Axis | 外部校准（符合论）+ 内部叙事自洽度（融贯论），同轴双层 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 |
| 时间轴 | Temporal Axis | 物理时间衰减 + 逻辑-因果时间（事件时序/因果关系/程序执行流）正交双轴 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 |
| 认知完整性轴 | Cognitive Integrity Axis | 反例锚点/死胡同路径/组合约束的结构性占位价值，`is_structure=true` 的记忆不参与遗忘 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 |
| 价值独立性公理 | Value Independence Axiom | "好用≠真实"——使用权重与见证锚定结构性冲突，非默认和谐 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.5（蓝图 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §5.3 补充） |
| 记忆压力 | Memory Pressure | 系统对自身记忆资源状态的主动感知与压力驱动行动——四类压力信号（上下文预算利用率/检索失败率/冗余率/遗忘队列积压）触发主动话题/重组/归档建议（保守倾向，不直接执行） | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) D.7 记忆压力声明 |
| 热度层级衰减 | Tiered Heat Decay | 使用价值/时间轴的实证参考基线（市场理念吸收 noah-gen3-type2）——热度组合公式 `热度=1.0+频次×2+新近×10+重要性加分`、层级衰减 ×0.985/0.975/0.965/0.95、父节点传播 `max×0.6+mean×0.3+一致性×0.1`；参考基线非默认值，仅作捕获门控与影子副本置信度累积速率参考（P6 禁止聚合单标量裁决） | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 热度体系实证参考基线声明 |
| 摄入侧情绪保护 | Ingest-side Emotional Burst Protection | 输入信号（用户/环境消息）命中情绪爆发模式时，该轮输入整体进入保护通道（生命周期豁免+升温抑制）；为 D-019(a) 情感调制（记忆自身 VAD）的摄入侧扩展；关键词表由外部校准维护、不自动学习 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) D.12 摄入侧情绪爆发→整轮保护声明 |
| 辞典式排序 | Lexicographic Ordering | 六级辞典式排序链（探索>宪法>校准>认知完整性>时间>间接度）+ 身份面否决权，宪法级不变量 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.3 |
| 见证锚定 | Witness Anchor | 存储层主副本——强一致性，不可篡改，含叙事自洽度字段 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.1-5.2（蓝图 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §5.3 补充） |
| 使用权重 | Usage Weight | 存储层影子副本——最终一致性，可演化，异步合并 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.1-5.2（蓝图 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §5.3 补充） |
| 差异检验 | Differential Check | 使用权重陡升时触发，判断是否需要更新见证锚定 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.5（蓝图 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §5.5 补充） |
| 分域真理观 | Situational Truth Routing | 常规操作→实用论，更新合并→融贯论，冲突校准→符合论；跨域冲突→辞典式排序在不可支配集上标记默认项（决策 D-01） | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §2.1 |
| 并行审查 | Parallel Review | 探索→宪法的执行时序模型（0.0.14 收录，替代原「时序优先」术语）：探索候选产生后进入宪法审查窗口（可配置，默认 100ms），通过后执行；窗口超时未获审查结果默认拒绝执行（fail-close）——探索不被事前审批阻塞，产物的采纳受宪法否决权约束 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §2.1 / 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.3 |
| 保守倾向 | Conservative Bias | 平局→NO-OP，不确定→默认保守，跨域回退→规范真理 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §2.1 |

## 五、认知与演进 Cognitive & Evolution

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 弱有界自省 | Weak Self-Reflexivity | 系统认知真实性依赖外部校准供给，有界自省上限受外部供给边界限定 | 认知基础 引论 |
| 他律性约束 | Heteronomy Constraint | 外部校准源充分性决定系统的认知天花板上限 | 认知基础 §三 |
| 惯性校准 | Inertial Calibration | 外部校准中断时系统依赖最后一次校准快照维持内部裁决基准 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.9 |
| 认知关节 | Cognitive Joint | 基于不确定认知所做的可拆卸可替换的设计决策点 | 认知基础 引论 |
| P6 方法论保障 | P6 Principle | 禁止无声丢失维度信息——任何标量化操作须保留多维表征可回溯性 | 认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §2.3 |
| 身份条件与价值条件 | Identity vs Value Conditions | 记录的双轨约束——append-only 保障身份条件，使用权重决定价值条件 | 认知基础 B.1 |
| 种子锚点 | Seed Anchors | 冷启动参考物——`kairos://_system/seeds/`，遵循最小化/可复审/可替换三项约束 | 认知基础 B.2 |

## 六、工程组件 Engineering Components

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 双副本分离 | Dual Copy Separation | 见证锚定（强一致）+ 使用权重（最终一致），S-14 语境自指禁令——内部信号不得作为见证锚定真实性的证据来源 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.1-5.2（蓝图 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §5.3 补充） |
| 事件总线 | Event Bus | 基于数据库表（events，ADR-002）承载的跨层异步通信机制——10 类事件（v0.1.0 首迭代 4 类），优先级 0–9，发布/订阅/背压/优先级规则见架构 §10.10 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 / [adr.md](../governance/adr.md) ADR-002 |
| 沙箱验证环 | Sandbox Verification Loop | WM 层新类型/新价值轴试运行→元审计确认→合并的验证机制 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §6 |
| 模拟隔离区 | Simulation Isolation Zone | WM 层反事实假设空间，模拟产物不可未经实证转正（S-13） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §6 |
| WM调度预处理器 | Reasoning Cortex | WM 子模块——常设最小推理内核，仅用于前瞻监控/事件排序/候选裁剪三类操作 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §6 |
| 健康计数器 | Health Counter | 元认知层独立旁路——仅监测环延迟/死锁/解释衰减，唯一权限触发降级信号 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.2 |
| 注意力调度器 | Attention Scheduler | 横切组件——统一管理全系统注意力资源分配、容量限制、动态调权 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §9 |
| 噪音规则库 | Noise Rule Library | 摄取门禁的纯正则规则集（单字/短确认、语气词、元命令、分隔符与纯标点行，零 LLM 成本），命中不计轮数、不触发使用权重升温；重要性加分表（未完成 5/纠正 4/决策 3/情绪 3/路径变更 2/工具结果 1/寒喧 0/保护 ∞）作编码深度分配参考 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 噪音规则库层 |
| SOUL.md | Agent Persona File | 宿主 Agent 的人格声明文件——承载「我是谁/我偏好什么」的身份与最高行为准则。Kairos 作为 Agent 记忆系统经编译管线读取并注入 LLM 上下文，但不拥有、不自动修改该文件（SOUL 是人与 Agent 的契约，不是系统的产物） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4.3 / [adr.md](../governance/adr.md) ADR-008 |
| 编译器 | Compiler | 编译管线的架构层实现组件——将感知缓冲区原始信息编译为结构化通信单元（L1/L2 净化 + 组装），位于注意力调度器与 WM 层之间；L1 失效可降级（`degraded_L1`/`passthrough`） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 |
| 结构化通信单元 | Structured Communication Unit | 编译管线的产出单元——结构化后的通信/记忆内容载体，携带净化标记与组装元数据 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 |
| 编译净化 | Compilation Purification | 摄取验证门禁的编译环节——L1（原始层净化）与 L2（解析严格度）两级，L1 失效降级路径 `degraded_L1`/`passthrough` | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 摄取验证门禁 |
| 命名配置集 | Named Configuration Set | 12 个特征标志组合空间中唯一受支持的三种配置集（`kairos-minimal`/`kairos-slice`/`kairos-full`）——未命名组合不是合法系统形态，启动时校验并拒绝启动（`invalid_flag_composition` 审计事件） | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 命名配置集与组合约束 |
| 竖切 | Vertical Slice（v0.1.0-slice） | v0.1.0 的首交付范围——统一 LTM + 路径空间 + 三信号混合检索 + 单曲线指数衰减遗忘 + 身份注册表 + 基础审计日志；分层关系「竖切 ⊂ v0.1.0 完整交付目标 ⊂ 认知基础完整愿景」 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 / [feature-list.md](../specification/feature-list.md) 竖切标注 |

## 七、安全红线 Security Redlines

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 安全红线 | Security Redlines | S-01~S-19 共 19 条不可降级的硬约束，违反即拒绝+审计日志记录 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8 |
| 语境自指禁令（S-14） | Contextual Self-Reference Prohibition | 内部信号不得作为见证锚定真实性的证据来源——使用权重不可无声改写见证锚定 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8 |
| 审计链 | Audit Chain | 双字段链式审计日志——`(a)` 明文链 `prev_content_hash`（供按内容追踪），`(b)` HMAC-SHA256 完整性签名 `hmac = HMAC-SHA256(hmac_key, timestamp + operator + action + content_hash + prev_hmac)`（5 项输入，公式权威定义见 [threat-model.md](../security/threat-model.md) HMAC 审计链；details 等可变信息以 SHA256 摘要并入 content_hash 参与链计算，不单独作为链输入）。同时支持精确定位篡改记录和整体完整性校验 | [threat-model.md](../security/threat-model.md) HMAC 审计链（架构 §10.10 事件总线承载写入，公式定义在 threat-model） |
| 证伪响应 | Falsification Response | 体系聚合可证伪性的架构承载——耦合计监测器 + VAD 独立性测试器 + 聚合审计器 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 |

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 术语表：中英文术语对照与来源引用。 |
| 0.0.2 | 2026-08-04 | 市场理念吸收（2026-08-04 决策）：增补双时态、构造性生成、记忆压力三条术语。 |
| 0.0.3 | 2026-08-04 | 全库深度审计修复：术语来源修正（5 条改指主架构、审计链公式改指 threat-model、意图契约定位）、中英文对照对齐。 |
| 0.0.4~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.4~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：外部治理接口定义重写（监督平面未合并、至高否决权口径）；注意力调度器/模拟隔离区/沙箱/预处理器来源章节修正。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：外部治理接口改别名声明、遗忘调度器单曲线口径、事件总线承载说明、抑制/硬删除补链接与审计痕迹。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次：决策 D-01 引用标注「决策」前缀。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：审计链公式统一为 threat-model 权威 5 项输入；新增「并行审查」术语条目（56→57 条）。 |
| 0.0.22 | 2026-08-05 | 外部项目理念吸收批次（changelog 0.0.22）：增补热度层级衰减（§四）、摄入侧情绪保护（§四）、噪音规则库（§六）三条术语（57→60 条）。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：关系索引补派生关系 derived_from；意图契约引用 §8→§3.2。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（changelog 0.0.26）：辞典式排序落点 §3.2→§3.3（H-01）。 |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（changelog 0.0.29）：D-04 术语表补 7 条（编译器/结构化通信单元/编译净化/检索深度分级/命名配置集/竖切/结构性记忆），60→67 条。 |
