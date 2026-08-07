---
title: VID-72 视频笔记：05 Agent memory 的设计
aliases:
  - 外部视频笔记-72
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-72 05 Agent memory 的设计

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1gqNc6vEes |
| UP主 | AI_Julie |
| 时长 | 12min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字 |

## 内容提炼
### 核心论点
1. Working memory（工作记忆）= user prompt + chat history + system prompt + context 的集合；LLM 是 stateless 的，记忆必须靠 working memory 保存，所以 Agent 的记忆优化点就是 working memory（00:50 / 02:02 / 02:10）
2. context 越短越精确越好：大模型幻觉大部分不是它自己产生的，而是 context 太长、涵盖了太多噪声导致的（03:52 / 04:08）
3. 比较完善的记忆设计：原始 request+reply 原样存入向量库 → 每 10 轮做一次压缩 → 用便宜模型做 summary → 提取事实（facts）存 markdown/向量库 → 每次输入弹 top-k 最相似记录粘到上下文，上下文精确、与问题强相关、又不丢弃重要历史（10:25 / 11:45 / 12:00）
4. 目前比较成功的 agent（code agent）做得越来越好，正是因为它的 memory 系统设计得越来越好（且需要 human in the loop）（02:20 / 02:28）

### 关键机制
- `skill.md`（程序性记忆层）：存处理流程——如智能客服场景：问题来了之后的处理流程（procedural memory）、要访问哪些 memory files、如何操作、skill 的具体步骤，随 context 一起加载（04:31 / 04:52 / 05:05）
- RAG 层：历史会话的 request+reply 不做压缩先原样存入长期记忆；达到一定规模（如 10 条）做一次压缩，把压缩文本存入 semantic memory；也可不用向量搜索而用 keyword 检索，很多场合直接把压缩好的 summary 去重后存进 md 文件（05:16 / 06:24 / 06:57）
- summary 质量要求：做 summary 时要遗弃无关的干扰信息，只保存事实性内容（「事实的选项」），保证 md 文件精确、噪声少、涵盖对话精华——符合人类对话习惯：记住对话精华，第二天从脑子里过滤出相关信息（07:32 / 07:42 / 07:54）
- 只存成功对话：不管成功还是失败都调大模型，但失败的对话不用存进历史、更没必要总结进 top-k；一般是成功的才存进去，更符合逻辑（09:48 / 09:58）
- 压缩管线：每轮对话把 request+reply 原样（含中间 tool code）存入 memory vector store → 每 10 轮（与 current chat history 对齐）把前 10 轮做 summary（可用便宜模型）→ 摘要后提取片段化的事实依据（一条一条 fact）→ 存 markdown 或向量库 → 每次用户输入从里面弹出 top-k 记录粘到上下文（10:25 / 10:56 / 11:12 / 11:45）
- 检索提示：原始 request+reply 向量库只在需要更深入查具体历史时才有意义——summary 已在上下文时再查它意义不大，trace 还是蛮重要的（08:46 / 08:53）

### 可操作细节
- 压缩周期：每 10 轮压缩一次（与 current chat history 的 10 轮对齐，避免重复保存）（10:56 / 11:12）
- 压缩用便宜模型：summary 不消耗主模型能力（11:25）
- top-k 检索：确保高度精确——summary 时遗弃无关干扰信息、只保存事实（07:32 / 08:08）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| `skill.md` 程序性记忆（流程/操作步骤固化加载） | 04:31 / 04:52 / 05:05 | 已覆盖 | 升华管道 raw→item→strategy→behavior（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.10）；strategy→behavior 须经外部确认门控（§D.8） | 支撑：把成功处理流程固化为可复用 skill = 升华管道终段；视频未提门控，Kairos 要求外部确认更严 | 与 VID-67 程序性记忆（13:56）同族 |
| 原始 request+reply 原样保存（含 tool code）+ 定期压缩 | 10:25 / 10:56 | 已覆盖 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；可审计压缩痕迹（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2 硬约束1） | 支撑：原文保留+压缩派生 = 激活-存储解耦+可审计压缩的独立实现 | — |
| 10 轮滚动 summary + 便宜模型 + 提取 facts | 10:56 / 11:25 / 11:45 | 已覆盖 | 可审计压缩（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；升华管道（§1.10） | 支撑：事实提取是 raw→item 的结构化压缩形态 | 轮数阈值是工程参数（VID-73 主张按 token 更合理） |
| context 越短越精确、噪声导致幻觉 | 03:52 / 04:08 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9） | 支撑：context 质量-幻觉因果与 CRI 同向 | — |
| 只存成功对话、失败不存不总结 | 09:48 / 09:58 | 张力 | 认知完整性轴：反例锚点、死胡同路径的拓扑占位价值（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；结构性记忆守护标记 is_structure=true 不参与遗忘调度器（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §0.1） | 挑战：失败路径/死胡同恰恰是认知完整性轴要保留的反例锚点——「只存成功」会丢失认知完整性价值 | 需吸收时论证边界：成功轨迹固化 ≠ 失败观测删除 |
| summary 去重后存 md + keyword 检索（未必向量） | 06:57 / 07:15 | 已覆盖 | 三信号混合检索（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；文件系统-向量索引一致性（§5.16） | 支撑：检索载体可替换（全文/向量），Kairos 三信号已涵盖 | 与 VID-73 keyword/BM25 立场一致 |
| top-k 注入上下文（精确、强相关、不丢重要历史） | 11:45 / 12:00 | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：top-k 投影是 R1 检索层的常规形态 | — |

## 存疑与未验证
- 「只存成功对话」与「trace 还是蛮重要的」两处表述存在轻微张力（失败不存则 trace 不全），视频未调和（未验证）
- 「目前比较成功的 agent 是 code agent、因为 memory 设计得好」为 UP 主观判断，无评测依据（未验证）
- 压缩周期「10 轮」为示例参数，无调优依据（未验证）
- 转写错字：「chart history/chata」（chat history）、「`scale.md``/skill.md``」（``skill.md`）、「reg」（RAG）、「e memory/semantic memory」（semantic memory）、「kwith设计」（keyword 检索）、「top key」（top-k）、「replay」（reply）、「tour」（tool）、「压速」（压缩）、「征流出那些facts」（提取 facts）、「home in the loop」（human in the loop）等，术语以语义还原

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
