---
title: VID-74 视频笔记：08 吐血整理的 Agent memory 设计（长对话摘要丢失关键信息怎么解决）
aliases:
  - 外部视频笔记-74
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-74 08 吐血整理的 Agent memory 设计

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1CZNN6iEWq |
| UP主 | AI_Julie |
| 时长 | 19min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字 |

## 内容提炼
### 核心论点
1. 长对话做 summary 丢失关键信息的四个核心原因：摘要统一压缩所有内容、平等对待无关细节和核心需求/用户硬约束；分不清早期核心目标和后期临时闲聊（像 prompt 没写好）；没有分层存储——重要静态偏好和临时会话一起压缩，导致上下文不分主次、噪声多；粗颗粒度摘要丢弃细腻的约束、工具参数、否定类需求（如「不要出错、输出简洁」）（01:26 / 01:41 / 02:11 / 02:27）
2. 分层解决方案四件套：working memory 前置隔离（固定目标输出约束完全不参与压缩）+ 分段增量摘要（拒绝一次性全量压缩）+ 语义检索 RAG 兜底（摘要丢细节没关系、向量库有完整原文可补权）+ multi-agent 分工（coordinator/observer/reflect/retriever）（02:36 / 09:58）
3. 幻觉常常不是模型的问题，是保存的信息有毛病：人设或偏好更新后直接替换特定字段而不是叠加——昨天人设没删、今天人设加进去，模型不知道你到底是哪个人设（03:43 / 04:12 / 04:31）
4. 场景决定方案：轻量对话（几十轮、少量工具）只用滑动窗口+system prompt+working memory 固定约束，不需要向量库（客服场景问完即走，没必要存人设）；中长期会话才需要 RAG+摘要；超长期高频工具才需要 multi-agent（10:49 / 12:35 / 14:46）

### 关键机制
- 方案一（working memory 前置隔离）：把绝对不能丢失的信息（用户核心目标、硬性偏好、身份信息、业务约束、禁止项）抽离出来定义成固定字段、每轮注入、不参与摘要压缩、永久常驻系统提示词；靠 update working memory 在对话中实时更新特定字段（直接替换而非叠加）；压缩时只压缩普通聊天内容；低成本守住最高优先级硬性要求，避免摘要吞掉用户最底层诉求；局限是只能存预设信息、无法覆盖零散历史——但这是定义使然（02:44 / 03:28 / 04:33 / 05:01）
- 方案二（分段增量摘要）：不要等上万 token 再统一压缩——context 本身是带窗口的 short memory，滚动分段压缩：设 2k token 阈值（约一页），超过就压缩当前区间历史；多段分段摘要不合并成一段（1-10 压缩一个 summary、11-20 再压缩一个），不会把每段信息都丢掉；每段打时间戳、优先级标志、用户目标约束权重（闲聊低权重，可让 LLM 在 system prompt 里打标）；检索时优先加载高优先级分段摘要、低权重按需取舍——时序逻辑不抹平早期关键信息，大幅降低丢失概率（05:17 / 05:59 / 06:38 / 07:03）
- 方案三（RAG 兜底）：summary 与原始记录都存入向量数据库、不删除；送入 LLM 的是精简摘要；当模型发现摘要信息不足时通过语义检索召回原始上下文——「摘要丢了细节没关系，向量库存有完整原文，可以实时补全遗漏的信息」（07:31 / 08:01 / 08:22）
- 方案四（multi-agent memory）：coordinator 主对话 agent 只拿近期上下文 + memory store 注入的高优先级信息（目标/偏好/约束/实体状态），负责事实回复、不背全部历史；observer agent 订阅会话/工具流、抽取结构化事实写入 memory store；reflect agent 对 memory store 做优先级评估、冲突消解、过时标记，保证主 agent 只看到有效记忆；retriever agent 从原文档向量库（存每轮 request&response 原文）做细节召回（08:36 / 09:05 / 09:20）
- 场景一（轻量对话）：用户输入 → message list → 是否用滑动窗口（截断最早消息保留最近 N 轮）→ 常驻 system prompt + 最近 N 轮 + working memory 固定约束字段（目标/偏好/禁止项）→ 拼装发给 LLM；几十轮结束即完结，不保存偏好、不涉及向量库（10:49 / 11:10 / 11:47）
- 场景二（中长期）：新会话 → 加载 working memory 高频固定信息（markdown 形式、一定不要特别长，含用户偏好设定）+ 可选轻量摘要提纲 → query embedding 检索向量库 top-k 相关片段 → 拼接上下文（system prompt + working memory + chat history + top-k）→ LLM 生成 → 多轮对话原话存入向量库（必须存，以后召回用）（12:35 / 13:12 / 13:56 / 14:19）
- 场景三（超长期 multi-agent）：共享 memory bus 事件队列；主对话 agent 从 memory store 取高优先级约束 + 经 retriever 语义召回向量库原文片段；对话完成后 observer 抽取事实写 memory store；reflect 检查优先级/过时/冲突确保 memory store 又简短又精确；原文存向量库（涉及约束库+原文库两个向量库）（14:46 / 16:37 / 17:32 / 18:12）

### 可操作细节
- 分段摘要阈值：2k token（约一页/两页），超过即压缩当前区间（05:59 / 06:04）
- 分段标签：每段打时间戳 + 优先级标志 + 用户目标/约束条件权重（闲聊低权重）（06:38）
- working memory 字段模板：用户核心目标、硬性偏好、身份信息、业务约束、禁止项（08:02 附近 / 03:28）
- 场景选型：轻量=无向量库；中长期=working memory+摘要+top-k；超长期=multi-agent（10:49 / 12:35 / 14:46）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| summary 丢失关键信息的四原因（平等压缩/混淆主次/不分层/粗粒度丢约束） | 01:26 / 02:11 / 02:27 | 已覆盖 | 可审计压缩硬约束（激活-存储解耦+可审计压缩，[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；上下文腐烂 CRI（§1.9） | 支撑：四原因正是「压缩不可无声丢失维度信息」的失败清单——反向证明可审计压缩必要 | 与 VID-72「summary 要遗弃干扰只存事实」互补 |
| working memory 字段直接替换不叠加（防前后不一致幻觉） | 03:43 / 04:31 | 已覆盖 | 可配置 Profile Schema（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.14）；分域真理观：结构化档案更新 vs 事件流追加分域处理（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §C.6） | 支撑：档案字段替换更新与 ADD-only 事件追加在不同分域，无矛盾——「当前真相」与「历史观察」分离 | 视频未做分域区分，Kairos 表述更完整 |
| 分段增量摘要（不合并、打时间戳/优先级权重、检索优先高优先级） | 05:17 / 06:38 / 07:03 | 可吸收 | 时间轴物理衰减+逻辑因果（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；六级辞典式排序链（§2.1）；压缩痕迹可审计（§2.2） | 支撑：「时序逻辑不抹平早期关键信息」= 时间轴保留立场；分段权重=排序链的摘要侧投影 | 可作遗忘/压缩调度的工程参照；优先级标签近似校准分 |
| 摘要不足以语义检索召回原文补权 | 07:31 / 08:22 | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；见证锚定主副本+差异检验（§5.5）；ADD-only（§7.3g） | 支撑：摘要之上原文可回查=见证锚定可审计；按需深检=分级检索 | 与 VID-69 transcript 兜底同族 |
| multi-agent 分工（coordinator 轻上下文 + observer 抽取 + reflect 冲突消解过时标记 + retriever 召回） | 08:36 / 09:20 / 16:37 | 已覆盖 | 宪法主权面与身份面（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §1）；元认知层监测（§2）；真理路由器（§3.2.1）；监督平面审计庭（§1.7） | 支撑：observer 抽取=升华管道；reflect 冲突消解过时标记=校准/遗忘调度；「主 agent 只看到有效记忆」=真理路由器+域路由的职责 | 多 agent 形式是 Kairos 单系统内多面的外部工程化对照 |
| 2k token 滚动分段阈值（约一页） | 05:59 / 06:04 | 可吸收 | 注意力调度器 token 预算分解（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §9） | 支撑：滚动分段是「窗口化压缩」的参数化参照 | 与 VID-73 Observer token 阈值同族 |
| 轻量场景不必上向量库（客服问完即走） | 10:49 / 11:47 / 12:22 | 已覆盖 | 检索深度分级 R0（常驻+窗口够用则不检索，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；记忆即使用（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1） | 支撑：无使用价值则不建记忆 = 记忆即使用的场景化决策 | — |
| reflect 与 observer 分开导致「不及时、多此一举」的疑问 | 18:38 / 18:52 | 可吸收 | 探索预算独立（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §8 S-12） | 支撑：UP 的疑问指向「抽取即检冲突」的同步化设计；Kairos 在线轻写/离线重审的分域设计（认知基础 §C.6）可回答该疑问 | 在线同步检冲突成本高，异步重审是分域真理观的工程理由 |

## 存疑与未验证
- 「multi-agent memory 设计」来源未指明（视频自称是整理的外部设计，图多次画错、UP 自己也对 reflect 分步提出疑问），机制细节（memory bus、双向量库）未给出可验证来源（未验证）
- 「2k token 约一页」为经验换算，不同语言/字体差异未讨论（未验证）
- 「模型产生幻觉的原因可能就是前后信息不一致」为 UP 推断，未给实验支撑（未验证）
- 场景图为手绘示意且 UP 自述「图画得有点问题」（message history 标注错误、multi-agent 图重复叙述），不作为机制依据（未验证）
- 转写错字：「相当数据库」（向量数据库）、「yumbating」（embedding）、「mati agent」（multi-agent）、「相料数据库」（向量数据库）、「get top key」（top-k）、「reflective hash/reflectation」（reflector）、「散装」（拼接）、「绘画」（会话）、「规议化」（归一化）等，术语以语义还原

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
