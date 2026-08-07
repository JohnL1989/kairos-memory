---
title: VID-60 视频笔记：GAM 即时编译式记忆（论文）
aliases:
  - 外部视频笔记-60
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-60 GAM 即时编译式记忆（论文）

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1VhLH6xEjy |
| UP主 | Agent智能体深度研究院 |
| 时长 | 9min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写存在音译错字（「GAM」=General Agentic Memory via Deep Research、「memorizer」=记忆器、「hider」=字幕原词、疑为「header/语境头」、「memgas/MemCoE」为 UP 主此前视频提及的论文、「FE」=分数指标、「quant」=Qwen 等），已按语境转述 |

## 内容提炼
### 核心论点
1. 反直觉点：真正可靠的长期记忆可能不是把过去压缩得更好，而是在需要的时候**重新研究过去**——GAM 的核心 thesis 是记忆不只是一段提前写好的压缩摘要，而应是「轻量索引 + 完整历史库」，运行时由 researcher 针对具体问题生成 Optimized Context（00:05-00:32）
2. 提前压缩的问题：压缩本身就是信息损失；Ahead-of-Time 记忆系统先整理成短 memory 运行时直接用，但用户后来问的可能正是摘要里没保留的细节——「越早决定什么重要，越容易在未来问题上判断错」，未来请求是开放的（00:55-01:31）
3. 借用编译思想：AoT 是提前把历史编译成固定 memory，JIT 是请求来了才按任务编译上下文——GAM 平时不把所有细节压进摘要，而是保留原始 page store（01:40-01:57）
4. 双 Agent 分工：memorizer（离线档案管理，小模型即可）负责生成 memo（轻量结构化摘要追加到全局 memory）+ 生成 hider（把前序上下文补到当前片段前再与原文组成 page 存进 page store）；researcher（在线调查员，必须强模型）负责基于轻量 memory 规划、并行搜索 page store、反思缺口、循环 deep research 直到信息足够，返回 Optimized Context（01:58-03:43）
5. 消融证明「只靠预先压缩 memory 会大量丢细节」：memory without researcher 只有 27.50（退化最严重），researcher without memory 48.27；RULER multi-hop tracing 上 RAG 得 0 而 GAM 超 90——优势来自多步研究和整合而非召回相似文本（07:31-07:49 / 06:23-06:39）

### 关键机制
- researcher 循环：基于轻量 memory 分析信息需求做 planning（决定找哪些事实、用哪些工具、发什么查询）→ 并行搜索 page store → 整合成阶段性报告 → reflection 判断信息是否足够 → 不足生成新的子请求继续下一轮 → 直到足够或达到最大反思深度（03:03-03:43）
- 三类检索工具互补：vector search（语义相似）+ BM25（关键词精确匹配）+ page id direct retrieval（直接取已知相关页面）；researcher 可组合使用，不必只押一条检索路径；工具消融：单用 page ID 28.96、单用 embedding 32.31、单用 BM25 48.64、三工具完整 53.18（03:46-04:02 / 07:05-07:27）
- hider 的用途：直接存原文会丢掉局部语义（单个 session 单独看不知道人物是谁、项目是什么）；hider 相当于给页面加上下文标签，让后续检索更容易找回、更容易解释（02:43-02:59）
- 与普通 RAG 的两点区别：①离线 memory 给完整历史建立可导航结构，不是裸切片检索；②researcher 不是一次检索，而是拆信息需求、组合关键词语义与页面读取、反思缺什么继续搜（04:26-04:47）
- 端到端优化框架：目标是在所有能让 agent 表现最好的上下文里找最短的那个；memorizer 和 researcher 都可通过最终答案 reward 做强化学习优化，client 模型不参与学习（05:14-05:33）
- 模型规模结论：memorizer 对规模不敏感（Qwen2.5-0.5B 还能有不错结果），researcher 对规模非常敏感（0.5B 平均只有 9.08，7B 也明显不够）——工程上「小模型做归档、强模型做研究」（06:43-06:59）

### 可操作细节
- 论文身份：General Agentic Memory via Deep Research（GAM），北京智源人工智能研究院 + 中国人民大学 + 北京大学 + 香港理工大学（00:34-00:47）
- 律师事务所述比：老办法是助理提前写短摘要；GAM 是平时做目录+完整归档，客户提问时派调查员查原件补证据写专题报告（04:04-04:23）
- 实验四类任务：LoCoMo（长期对话记忆）、HotpotQA（多跳问答+大量干扰文档，56k/224k/448k）、RULER（128k 长上下文）、NarrativeQA（整本书/电影脚本问答）；基线 LangLLM、RAG、A-MEM、mem0、MemoryOS、LightMem（05:35-05:58）
- 代表数字：GPT-4o-mini 上 HotpotQA 56k/224k/448k 分别 63.22/64.56/59.81；RULER multi-hop tracing 93.20，Qwen2.5-2.5B 上也有 90.20（06:00-06:20）
- 测试时计算：max reflection depth 1→5、每轮 retrieved pages 3→20，性能持续提升（07:05-07:17）
- 效率对比：HotpotQA-56k 总耗时 69.32 秒（FE 64.07）vs A-MEM 210 秒（FE 只有 27.04）——不是最快的固定缓存，但效果与成本更均衡（07:52-08:10）
- 自述边界：①deep research 增加 serving 时间，不适合所有低延迟场景；②researcher 依赖强模型，小模型容易规划/反思失败；③若 page 切分、hider 或工具选择出问题，deep research 可能沿错误路径越查越偏（08:18-08:36）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| JIT 记忆观：记忆 = 知道去哪里找、怎么找、找完怎么整合，而非把过去压成一段文本 | 08:48 | 张力 | 「记忆即使用」（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；见证锚定主副本+使用权重影子副本（双副本，架构 [architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5） | 挑战：GAM 的 Optimized Context 是「查询期现造的派生物」，若直接供给模型，其真实性未经见证锚定；与「好用≠真实」公理有张力——需要差异检验后进使用副本，而非直通 | 与 VID-09 同族：查询期重建产物须经双副本仲裁 |
| AoT 压缩 vs JIT 编译的架构取舍（提前决定什么重要 = 未来判断错的风险） | 01:15 | 张力 | 可审计压缩（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2 三硬一软）；ADD-only 写入（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g） | 挑战：Kairos 压缩定位于「可审计」，GAM 主张「尽量不压、查时再编」——两者对保留完整原文的态度不同；Kairos 原档保留+可审计压缩的粒度可吸收 GAM 的「完整历史库」作为 R2 深检索后端 | 候选理念：完整历史库 + 查询期重建，作为压缩摘要的互补层 |
| memorizer（轻量索引）+ researcher（强模型深研）双 Agent 分工 | 01:58 | 可吸收 | 模型路由梯队（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.9）；双模检索 Fast Context + Deep Reasoning（§7.3d） | 支撑：GAM 的 memorizer/researcher 分工与 Kairos Fast/Deep 双模同构；「归档用小模型、研究用强模型」可直接指导模型路由梯队配置 | 已覆盖度较高，增量在「规划-反思循环」的显式化 |
| 规划-搜索-整合-反思循环直到证据足够（deep research 作为检索范式） | 03:03 | 可吸收 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；推理皮层汇聚式多路径融合（§4.2） | 未触及：Kairos R2 深检索未声明「多轮规划-反思」循环结构；GAM 提供具体循环模板 | 候选理念：R2 深检索采用 researcher 式循环 |
| hider 机制：给原文页面加语境前缀，避免局部语义丢失 | 02:43 | 已覆盖 | 编译器/系统提示词多阶段动态组装（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §4.3）；时间覆盖均匀采样（§2.6.2） | 支撑：hider 与 Kairos 上下文组装时的前置注入同思路，属工程细节而非新理念 | — |
| 端到端 RL 优化 memorizer/researcher（client 模型不参与学习） | 05:14 | 已覆盖 | RL 权重优化器（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §10.14）；学习信号的来源与可信度（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.3.1.1） | 支撑：训练端与运行时解耦与 Kairos 学习信号声明一致；reward 来自最终答案属「外部校准」，需经 §1.3.1.1 可信度审查 | — |
| 弱模型无法完成规划-反思（researcher 规模敏感，0.5B 仅 9.08） | 06:43 | 已覆盖 | 模型路由梯队（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.9） | 支撑：印证深检索必须路由到强模型梯队，Kairos 已声明 | — |
| 边界自述：deep research 可能沿错误路径越查越偏 | 08:18 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；检索预处理与结果治理（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §2.6） | 支撑：论文承认的「越查越偏」正是 CRI 噪声聚集阶段的检索侧表现 | 强化 CRI 的检索侧守护必要性 |

## 存疑与未验证
- 论文名「GAM（General Agentic Memory via Deep Research）」及机构列表（智源/人大/北大/港理工）为字幕音译，未核对原文（未验证）
- 全部实验数字（63.22/64.56/59.81、93.20、90.20、27.50/48.27、28.96/32.31/48.64/53.18、69.32s/210s）为 UP 主转述论文，未核对原文（未验证）
- 「hider」一词为字幕原词，无法确认英文拼写（可能为 header/context prefix），机制描述按语境转述（未验证）
- 「memgas」「rfmem」为 UP 主此前视频提及的论文（MemCoE 多粒度记忆、RF-Mem 快慢双路径），非本视频主题，未展开（未验证）
- 「FE」「quant 2.5」「CLIENT 模型」等术语指代按语境推断（FE 疑为效果分数、quant=Qwen）（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
