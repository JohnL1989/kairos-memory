---
title: VID-53 视频笔记：Google 揭秘Agent长期记忆 Memory Bank
aliases:
  - 外部视频笔记-53
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-53 Google 揭秘Agent长期记忆 Memory Bank

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1wkMB6qEyN |
| UP主 | AI变局 |
| 时长 | 21min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配（主体为 Google Agent Platform/ADK 官方英文演讲，开头约 0-6s 为 UP 中文引子） |
| 素材边界声明 | 完整覆盖视频全程（字幕至 1313s）；whisper 转写为逐词碎片（后半段每秒一条），专有名词音译失真（「Injust events」=ingest events、「Shambray fabric」=chambray fabric、「Trieving」=retrieving、「pedantic schema」应为 detailed schema 等），引用参数需以官方文档为准 |

## 内容提炼
### 核心论点
1. Skills 用渐进式披露（progressive disclosure）管理上下文：第一级元数据（level 1 metadata）只含技能标题+何时使用技能的描述，当 agent 决定调用时才把完整元数据加载进上下文窗口——动态管理上下文窗口，只在需要时拉取所需上下文，避免一开始就过载；实测 skills 在 token 管理上比 tools 更高效（02:23-03:11）。
2. 上下文只进不出会污染：会话变长后历史轮次会污染上下文窗口，必须主动丢弃旧上下文——会话内用 context compaction 丢弃过时片段；但首轮可能是超级重要的上下文，不能丢——可用 ADK 策略动态摘要，或用 memories 从内容中抽取有意义信息再注入，两者兼得（丢掉冗余、保留意义）（03:30-04:17）。
3. 记忆生成算法（高层）：turn-by-turn 对话（可以超级啰嗦）→ Memory extraction LLM 抽取值得持久化的内容→候选记忆→对该用户做 consolidation（与已有记忆对比：相似则更新、全新则新增实体）→变更数据库（08:21-09:49）。
4. 记忆是为未来而生：当前交互一般不需要记忆，需要的是下一次交互或下一个会话——所以要把 ingestion 与 processing 解耦，agent 专注响应用户，memory bank 在后台就绪时处理数据抽取（06:41-07:22）。
5. 记忆注入的两种方式：in-time context retrieval（即时按查询检索）vs always-on context（初始化交互——不依赖用户查询，把预计算的、schema 化的结构化记忆先塞进 system instructions 初始化会话，如用户画像）（12:25-13:20、19:51-19:57）。

### 关键机制
- working context 的短暂性：每次模型调用后丢弃、just-in-time 构建；两个实体接入：conversation history（会话存储中的逐轮日志，很长，需 compaction）与 developer-provided content（system instructions、tool definitions、skill definitions，也可以动态）；agentic memories 可注入两个位置——作为工具调用进 session history，或动态加进 system instructions 初始化交互（04:19-05:46）。
- 记忆个性化：memories are personal——不同个体的记忆清晰分离（按 scope：user-level/session-level/pertinent-level），这是 memory bank 与传统数据库的关键差异（07:37-08:00）。
- 默认存储四类：personal information、user preferences、key conversation events、explicit instructions（remember/forget 指令）；可个性化定制或用 few-shot 示例（11:53-12:20）。
- consolidation 实例：用户说「不喜欢 chambray 面料」→首次交互直接新增；下次说「想要竹纤维/棉混纺这类柔软面料」→与新记忆相似→合并（09:49-11:15）。
- schema 驱动 profile generation：开发者定义详细 schema（描述要持久化的信息），memory bank 负责抽取填充与维护，形成 single source of truth；一个 memory bank 可挂多个 profile schema，支持多 agent 场景（13:15-15:07）。
- ingest events：把 ingestion 与 processing 解耦，可配置处理时机（demo 中配置每 10 分钟 inactivity 触发抽取，避免过早抽取），也可手动 flush 提前触发（15:15-15:51）。
- 多模态输入：不保存多模态内容本身，只保存从中提取的文本见解（19:30-19:49）。
- profile 演化分析：每个信息元素带 metadata、time to live、演化历史（从哪些上下文一步步变成现在这样），可分析信息随时间的变化，也可 roll back 到 profile 之前的版本（19:51-21:37）。

### 可操作细节
- level 1 metadata 结构：技能标题+何时使用技能的描述（02:24-02:33）。
- 预抽取 facts：agent 想要控制「存什么」但仍享受 consolidation 与 single source of truth 时，可把预抽取事实交给 memory bank，由它负责合并维护（11:16-11:50）。
- 记忆编排 demo：stream event→不触发抽取→retrieve 用户 profile→塞进 system instructions→传给 LLM→把 LLM 响应回传 memory bank 供下次处理（15:52-16:30）。
- 日本旅行 demo：第一轮对话（计划去日本看樱花、预算优先、重真实体验）被抽取成 profile，下一次新会话中 profile 注入 system instructions，agent 直接给出简洁且符合偏好的回复（17:24-19:30）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 渐进式披露：两级元数据（标题+时机→调用时加载全文） | 02:23-03:11 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §4.3（编译管线：多阶段动态组装）+ §3.9（检索深度分级） | 支撑：Kairos 编译管线按块分级渲染、检索分级注入，与渐进式披露同构；「标题+使用时机」可作为技能条目元数据的最小结构参考 | 增量：元数据结构细节 |
| 上下文只进不出会污染：compaction+动态摘要+记忆抽取三手段 | 03:30-04:17 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.9（上下文腐烂 CRI）+ §4.3（编译管线 token 预算裁剪） | 支撑：Kairos CRI 度量腐烂、编译管线按预算裁剪；外部三手段与 Kairos 激活-存储解耦（摘要走压缩、记忆走存储）一致 | — |
| 记忆为未来而生：解耦 ingestion 与 processing | 06:41-07:22 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §2.2（三硬一软：激活-存储解耦）+ [架构](../../../foundation/architecture-v0.1.0.md) §7.4d（背景/新消息分段单次 LLM 调用） | 支撑：Kairos 升华管道即异步后台处理，「当前交互不需要记忆」与 Kairos 使用/存储解耦立场一致 | 外部为产品化实现 |
| consolidation：相似则更新、全新则新增（针对个体） | 08:21-09:49 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a（三信号混合检索）+ §7.3b（GSPO 聚类去重） | 支撑：Kairos 写入前的查重/合并与 consolidation 职能一致；外部按用户聚合，Kairos 亦支持 scope | — |
| 记忆按 scope 隔离（user/session/pertinent）+ memories are personal | 07:37-08:00 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §5.20.6（P3-17 TeamScope 多租户隔离）+ §5.20（存储层基础设施） | 支撑：Kairos 已登记多租户隔离（v1.1+ 蓝图）；外部「个体记忆分离」为产品级印证 | — |
| schema 驱动 profile + single source of truth | 13:15-15:07 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §5.14（可配置 Profile Schema） | 支撑：Kairos §5.14 正是开发者定义 schema、系统抽取维护的机制；外部印证该设计 | 术语几乎一致 |
| always-on 初始化 vs in-time 检索两种注入方式 | 12:25-13:20 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §3.9（检索深度分级 R0/R1/R2）+ §4.3（编译管线） | 支撑：always-on 对应 Kairos 常驻注入（R0 级），in-time 对应按需检索（R1/R2）；外部两种方式 Kairos 均已覆盖 | — |
| 多模态只存文本见解、不存内容本身 | 19:30-19:49 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3i（多模态消息 Part 统一接口） | 支撑：Kairos 多模态摄取亦以结构化见解入库；外部印证「存见解不存媒体」方向 | — |
| profile 演化可分析、可 rollback（metadata+TTL+演化史） | 19:51-21:37 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §5.5（差异检验：blocked→degraded→pruned→rollback） | 支撑：Kairos 差异检验支持回滚、审计链记录演化；外部产品功能（rollback 到之前版本）是 Kairos 架构机制的简化体现 | — |

## 存疑与未验证
- 转写为逐词碎片且大量专名失真：「Injust events」（=ingest events）、「Shambray fabric」（=chambray fabric）、「Trieving」「pedantic schema」等，按上下文校正（未验证）。
- 前半段（0-2min）UP 中文引子转写混乱（「线索」应为「策略」等），不影响主体（未验证）。
- 「Every ten minutes of inactivity」为 demo 配置参数，非产品默认值；Memory Bank 产品的具体定价/能力边界未与 Google 官方文档核对（未验证）。
- 演讲者（George 等）为 Google Agent Platform 团队成员，具体身份与职级未核实（未验证）。
- 21:44 提到的客户案例公司名（转写「AT&T」）未核实（未验证）。
- 「skills 比 tools 在 token 管理上更高效」为演讲者实测结论，具体基准数据未给出（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
