---
title: VID-05 视频笔记：Agent记忆系统深度拆解（下）：MemOS/OpenViking
aliases:
  - 外部视频笔记-05
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-05 Agent记忆系统深度拆解（下）：MemOS/OpenViking

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1orQJB2Edt |
| UP主 | 唐国梁Tommy |
| 时长 | 25min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；标题虽写 MemOS/OpenViking，实际正文拆解 5 个项目（MemOS、OpenViking、Hansight、Second Me、MetaMem）；whisper 转写可能存在谐音错字（MemOS/MemScheduler/MemCube、Hansight、MetaMem 等专名以字幕近似音为准） |

## 内容提炼
### 核心论点
1. MemOS：记忆不应是被动数据库，而是「主动治理的操作系统级资源」——六层架构（API 层 / MOS Core 核心引擎 / MemScheduler 异步调度器 / MemCube 记忆容器 / MemEri 记忆存储层 / 基础设施层），完整对应操作系统（内核/进程调度器/容器）（00:43-01:56）
2. OpenViking（字节火山引擎，Apache 2.0）：自创品类「上下文数据库 ContextDatabase」——把记忆、资源、技能统一映射到一个虚拟文件系统，Agent 用 ls/find/grep/mkdir/rm/mv 操作上下文；论据：LLM 在训练数据中深度内化了 Unix 手册，文件系统操作语役比向量数据库接口更自然，且目录层级显式可解释（05:24-06:43）
3. Hansight：让 Agent 学习而不只是记住——三层记忆架构有明确认知科学映射（WorldFact=语义记忆、ExperienceFact=情景记忆、MentalModels=程序性知识）+ 中间层 Observations（Consolidation 引擎自动提炼）；「传统 RAG 把所有信息平铺为向量，信息层次被压缩了」（09:36-10:58）
4. Second Me：不做更好的助手，做数字孪生——本地训练反映用户身份/记忆/偏好的个性化模型；关键实验「Lost in the middle」：同时从长上下文检索并执行推理几乎不可能，现有 LLM 有效上下文长度远小于声称长度（14:40-15:15）
5. MetaMem：记忆碎片化不是数据量问题而是结构性问题——LLM 无显式指导时倾向依赖第一个检索到的证据；它不做存储检索，做「怎么用检索到的记忆」的策略增强层（Learning to learn，学会如何学习）（18:56-19:49）

### 关键机制
- MemOS 三类记忆体系：文本记忆（简单文本/向量库通用文本/Neo4j 图数据库树型结构/用户偏好）+ 激活记忆（KV Cache 记忆：高频记忆上下文预编码为 KV Cache 跳过重复 Prefill，支持 HF Dynamic Cache 与 vLLM Paged Attention）+ 参数记忆（高频稳定知识蒸馏为 LoRA 权重、推理零 token 消耗——但当前代码里 dump 方法只写入字面量 Placeholder，「三元组架构实际上缺了一角」）（02:03-02:59）
- MemOS 树型记忆三层：Working Memory 上限 20 条 / Long Term 1500 条 / User Memory 480 条；Working→Long Term 不是晋升而是同时建节点（Working 只是临时镜像，FIFO 淘汰）；层次归属完全由上游 Memorider（LLM 驱动组件）经 Prompt 判断，Memory Manager 只是忠实执行者——「和操作系统调度器应该做决策的直觉相反」（03:04-03:51）
- MemScheduler：生产级异步调度引擎（Rated Streams 内部任务队列、RabbitMQ 跨进程广播、线程池最大 30 个 Worker、五种任务类型）；性能数据：LOCOMO 75.80 分第一、EVO 比 OpenAI Memory 提升 40%、Prefab EVO10 提升 25%（UP 主警示：基线几乎无效才导致百分比极高，需冷静看待）；部署需 Neo4j/Qdrant/Redis/RabbitMQ/MySQL 五套基础设施（03:52-05:22）
- OpenViking L0/L1/L2 分层上下文加载：每个上下文节点自动生成三层内容——L0 约 100 token 一句话摘要、L1 约 2000 token 核心概览、L2 完整原始数据；L0-First 检索：先看 20 个候选节点的 L0（约 2000 token），高相关者追加 L1（4000-6000 token）；对比传统 RAG（每轮检索 2500 token、20 轮对话 25000 token），token 成本降 92%-96%；代价：每次检索至少多一轮 LLM 调用、增加 0.5-2 秒延迟（06:49-07:42）
- OpenViking 检索算法：优先级队列驱动的最佳优先搜索（类 A*）——BFS 均匀展开三层十个子目录要展开 100 个节点、DFS 过于专注单路径，Best First Search 始终展开最高分节点，搜索预算优先分配给最有希望的方向；分数传播机制：子节点最终得分 = 自身与查询相关性 + 父节点得分的加权平均，默认各半（0.5 是「最大熵的安全默认值」，信息不充分时不偏向任何一方）（07:44-08:20）
- OpenViking 工程选型：Python 核心逻辑 + C++ SIMD 向量引擎（比纯 Python 快 10-50 倍，PyO3 调用）+ Go 文件系统服务器 + Rust CLI——四种语言各配其用，但编译环境搭建成本高；项目 0.1.X 早期、ReRank 标记 TODO 未实现，当前效果是在无 ReRank 下达成的；火山引擎 SDK 是非可选依赖（08:26-09:31）
- Hansight 核心操作 Retain/Recall/Reflect：Retain 流水线（分块→LLM 提取结构化事实→实体解析消歧→embedding→创建四种链接：实体/语义/时间/因果→持久化 PostgreSQL→触发 Consolidation）；Recall 四路并行检索——语义检索（PGVector，对措辞变化鲁棒但对精确名称弱）+ BM25 全文检索（PG Trigram，精确词汇高精度但同义词召回低）+ MPFP 图检索（MetaPath Forward Push，次线性时间复杂度和图规模无关、遍历零 LLM 调用，能把「Alice 感冒请假」和「团队会议缺关键人员」这类语义相似度极低但实体/时间关联的记忆强关联）+ 时间检索（独立检索维度）（11:01-12:41）
- Hansight 融合与重排序：四路结果用等权 RRF 融合 + Cross-encoder 重排——「没有做查询自适应的动态权重调整，但依然取得 SOTA，说明朴素方法反而更鲁棒」（12:46-12:57）
- Hansight Consolidation 引擎：Retain 完成后后台异步触发，从新事实自动提炼 Observations——「和人类睡眠期间的记忆巩固功能类比」（海马体与新皮层知识协商、情景记忆到语义记忆转化）（12:59-13:29）；Disposition：给记忆库配置三个性格维度（怀疑度/字面主义/共情力，各 1-5 分），同一知识库不同配置产生不同反思结论（高怀疑=批判分析型、高共情=支持陪伴型），一套知识库支持多应用场景不复制数据（13:30-13:56）
- Second Me L0/L1/L2（含义与 OpenViking 完全不同）：L0 情景记忆（文档/笔记/时间戳→结构化 Insight/Summary，所有 Prompt 注入用户 Bio 上下文，从「了解你的老朋友」视角生成个性化洞察）；L1 语义记忆（身份画像建模，Shade 系统分析私人记忆识别兴趣领域生成多面体特征标签，高度相似 Shade 自动合并为超级 Shade）；L2 程序记忆（模型微调：L0 Note+L1 Bio→数据合成→LoRA 微调个性化权重，R=64/Alpha=16/QKVO+DownUpGate 七投影层，GGUF 部署可 CPU/Apple Silicon 运行）（15:18-17:14）
- Second Me Me Alignment 三种数据合成策略：Self-QA（模拟用户向自己的 AI 提问）、Preference（预测用户行为偏好）、Diversity（数据增广防过拟合）；配 GraphRAG 实体关系提取 + DPO 偏好对齐（16:35-17:00）
- Second Me 宣传澄清：「100% 本地」实为推理 100% 本地，训练数据准备（L0 生成/L1 Bio/Self-QA/Preference 数据生成）必须调 OpenAI/DeepSeek API——端侧 0.5B-3.5B 小模型无法胜任复杂推理，本质是一次性知识蒸馏；「去中心化」Network 实际所有实例注册到中心化服务器，无 DHT/P2P，实际去中心化约 20%（17:17-18:11）
- MetaMem 四阶段训练流水线：Response sampling（同一问题 5 次随机采样）→ Self reflection（分析推理轨迹识别成败关键因素）→ Metamemory learning（比较成败提取可泛化元记忆原则）→ Metamemory evolution（汇总所有操作提案、解决冲突合并相似原则、更新元记忆知识库）；产出自然语言元记忆原则（例：「当记忆包含时间信息时优先考虑最近的数据，除非问题明确询问历史」「交叉验证出现在多个记忆中的事实，单一来源的声明需要更多谨慎」）（19:51-20:34）
- MetaMem Partial Correctness Filter：5 次采样只处理平均奖励在 0-1 之间的样本（有对有错）——全对说明问题太简单无学习价值、全错说明系统性能力不足（元记忆优化无法改变结构性失败）、部分正确信息量最大（同一问题同一检索结果同一元记忆有时成功有时失败，分界线在推理路径选择）；与强化学习策略梯度方法一致，「只有奖励分散的样本才能产生较大的梯度信号」（20:35-21:23）
- MetaMem 符号化优化：不微调任何模型参数，通过 ADD/Update/Delete 三种符号化操作修改元记忆知识库（对应 MAML 内层/外层循环，但 MAML 用梯度反向传播、MetaMem 用自然语言规则操作）——完全可解释、Chaining Free 可迁移到任何 LLM；推理阶段只多注入约 200-500 token 元记忆文本（21:23-22:08 / 23:15-23:27）

### 可操作细节
- MemOS：Working 20 条 / Long Term 1500 条 / User 480 条硬上限；线程池 30 Worker；五套基础设施依赖（03:04-03:12 / 04:02-04:05 / 04:51-04:57）
- OpenViking：L0≈100 token、L1≈2000 token、L2 原始数据；L0-First 先看 20 个候选节点；分数传播父/子权重默认各 0.5；token 成本降 92%-96%、延迟 +0.5-2 秒（06:56-07:42 / 08:11-08:15）
- Hansight：Retain 事实提取是 LLM 最密集环节（单文件 2097 行）；四路检索等权 RRF + Cross-encoder 重排；中文场景向量检索精度可能下降 40%-60%、BM25 几乎完全失效（默认模型英文优化）（11:28-11:30 / 14:07-14:19）
- Second Me：LoRA R=64/Alpha=16、GGUF 部署、推荐 16GB 以上内存（17:00-17:14 / 18:39-18:43）
- MetaMem：5 次采样、Partial Correctness Filter（奖励 0-1）、推理多注入 200-500 token；训练代价：6 张高端 GPU 约 200GB 显存、350 样本 5 epochs 约 3 万次 API 调用（20:39-20:45 / 22:57-23:05）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 记忆作为操作系统级资源：主动调度、容器、进程化治理 | 01:12-01:56 | 已覆盖 | 遗忘调度器承载于存储层（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5）；注意力调度器（§9）；元认知层调节（§2） | 支撑：调度与治理思想与 Kairos 遗忘调度器同向 | Kairos 已把遗忘建模为调度；MemOS 提供「资源治理」整体隐喻 |
| 参数记忆（知识蒸馏进 LoRA 权重，零 token 推理） | 02:42-02:59 | 可吸收 | 三级知识生产管道（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.10）的持久归档终态；探索产物置信度带（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：知识进权重是「升华」的终态方向，但当前只是占位符 | 需注意 MemOS 自认参数记忆未实现；Kairos 纯文档可将其列为未来方向而非现役设计 |
| 记忆层级归属由 LLM（Memorider）经 Prompt 判断，管理器只执行 | 03:35-03:48 | 张力 | 六级辞典式排序链为宪法化裁决，非 LLM 运行时判断（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1） | 挑战：层级归属交给 LLM 会引入不可审计的不确定性，与宪法主权面裁决模型冲突 | 若仅作「提炼建议」而非「层级裁决」则可兼容（Kairos 编译器/元认知层可吸收为建议源） |
| 文件系统范式组织上下文（ls/find/grep/mkdir/rm/mv） | 05:38-06:43 | 已覆盖 | 路径注册表 + R0 浅层检索路径前缀匹配（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；kairos_tree 树状浏览工具（§7.1a） | 支撑：显式路径组织与 Kairos 路径空间设计同构 | 可作为 Kairos 路径空间的交互形态参照；「LLM 内化 Unix 语役」论据支持路径化检索而非纯向量 |
| L0/L1/L2 分层加载（摘要→概览→原始，成本降 92-96%） | 06:49-07:42 | 已覆盖 | 检索深度分级 R0/R1/R2，Token 成本比 0.05×/0.3×/1×（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：分层加载与 Kairos 深度分级同构，外部提供成本量化实证 | 差异：Kairos 明令 R1 摘要「仅用于定位不得作为内容」，OpenViking L1 概览可作内容——Kairos 更严格 |
| Best-First 搜索 + 分数传播（子节点=自身相关+父节点得分加权） | 07:44-08:20 | 可吸收 | 三信号混合检索（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；探索预算分配（S-12） | 支撑：搜索预算择优分配与探索预算思想同向 | Kairos 未声明树形路径空间的最佳优先遍历；可作检索路径注记 |
| 四路并行检索（语义/BM25/图/时间）各补盲区 + 等权融合 | 11:36-12:57 | 可吸收 | 三信号混合检索（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；时间覆盖均匀采样（§2.6.2）；实体知识图谱（§5、§7.1a） | 支撑：「时间作为独立检索维度」与 Kairos 时间轴（物理衰减+逻辑因果双轴）同向；等权融合不引入动态权重，与六级链禁止标量聚合相容 | Kairos 三信号 vs 外部四路：可评估时间检索是否应升为 Kairos 独立检索信号 |
| 有损重构哲学（故意丢失细节换整合质量；人类记忆不是录像机） | 14:21-14:37 | 已覆盖 | 可审计压缩（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2 三硬一软）；见证价值轴对应符合论（§2.1） | 支撑：有损整合不损害见证锚定，与 Kairos 压缩理念同向 | 与 VID-12 批评平铺抽取同立场 |
| Disposition：记忆库级性格配置产生不同反思结论 | 13:30-13:56 | 张力 | 分域真理观（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §C.6）；见证锚定主副本强一致（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.1） | 挑战：同一知识库不同性格产生不同反思结论，若反思结论回写见证锚定会破坏一致性 | 若限定为「使用侧影子副本的解读视角」（不影响见证锚定）则可兼容；与 Kairos 身份面/契约投影时机相关 |
| Lost in the middle：有效上下文远小于声称长度 | 15:00-15:13 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；检索深度 CRI 超阈强制降级（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：为 CRI 概念提供外部实证 | 与 VID-10 同源论据 |
| 个性化模型权重（放大个人特质 vs RLHF 一致高质量，根本张力） | 18:11-18:31 | 可吸收 | 身份面否决权、身份独立于排序链（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；身份条件与价值条件分离（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.1） | 支撑：Second Me 的「优先向你而非完美」与 Kairos 身份面定位同向，但权重级个性化与 Kairos 记忆库形态（非模型参数）不同层 | Kairos 身份承诺由注册表/否决权承载，不依赖模型微调；此差异无需弥合 |
| MetaMem：元记忆策略层（自然语言原则、ADD/Update/Delete 符号化优化、可迁移） | 19:41-23:27 | 可吸收 | 差异检验与见证锚定（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5）；探索预算独立（S-12） | 支撑：「交叉验证多源事实、单一来源需谨慎」与 Kairos 见证锚定/外部校准同向；自然语言可解释原则与 Kairos 宪法/契约可解释性相容 | 张力点：MetaMem 允许 Delete 元记忆规则，Kairos 对见证锚定是 ADD-only 版本化——若元记忆规则属使用侧而非见证侧则可兼容 |
| 「决定记忆系统上限的不是记了多少，而是会不会用」 | 22:11-22:22 | 已覆盖 | 记忆即使用（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1） | 支撑：与 Kairos 第一性原理直接同向 | 外部理念以「使用策略」独立维度重申 Kairos 的「记忆即使用」 |

## 存疑与未验证
- 标题为「MemOS/OpenViking」但正文实际覆盖 5 个项目（MemOS、OpenViking、Hansight、Second Me、MetaMem），「下集」应为系列（下）篇，素材边界以实际内容为准
- 项目名/机构名均为字幕近似音：MemOS（Mem0 团队+上海交大等）、OpenViking（字节火山引擎）、Hansight（Vectorize）、Second Me（Mindverse）、MetaMem（东北大学/清华/北邮，OpenBMB）——拼写未逐一核对（未验证）
- 「LOCOMO 75.80 分第一」「Prefab EVO10 提升 25%」（字幕为 2568，疑为 25.68 或笔误）为 UP 主转述基准数据，未验证（未验证）
- 「token 成本降 92%-96%」为 OpenViking 项目自述，未验证计算口径（未验证）
- 「中文场景向量检索精度下降 40%-60%、BM25 几乎完全失效」为 UP 主对 Hansight 的转述，未验证（未验证）
- Second Me「去中心化约 20%」为 UP 主估算，未验证（未验证）
- MetaMem「6 张 GPU/200GB 显存/3 万次 API 调用」为 UP 主转述训练成本，未验证（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
