---
title: VID-99 视频笔记：02 RAG Agent 长期记忆
aliases:
  - 外部视频笔记-99
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-99 02 RAG Agent 长期记忆

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV11kT16dErg |
| UP主 | AI_Julie |
| 时长 | 12min（1P） |
| 字幕来源 | B站 AI 字幕（ai-zh），抓取于 2026-08-07，内容与主题匹配度已人工核验 |
| 素材边界声明 | 完整覆盖视频全程；AI 字幕存在个别错字（「唯唯英文be点」「ka dB」「face」应为 ChromaDB/Faiss 等）；视频为 RAG Agent 系列课第 2 节，代码演示（Python 单文件）为主，讲解长期记忆的写入/检索/抽取闭环 |

## 内容提炼
### 核心论点
1. 长期记忆=向量数据库持久化+语义检索召回（即 RAG 基本盘）：写入时对文本 embedding 后连同 user_id/text/vector/importance/时间戳存入向量库；检索时 query embedding 取 top-k，再按时间戳、重要性等打分排序返回（00:04-01:23）。
2. 记忆写入不存原始对话，而是用 LLM 抽取：每轮问答结束后调用 lm_extract_memory，让大模型「分析对话、提取值得长期记住的事实或偏好，每行一条、格式简短，无内容输出 none」，抽取结果逐条 ADD 入库（07:18-09:17）。
3. 检索命中记忆拼入 system message：每轮把 top-k 命中记忆拼进系统提示（「你是助手，以下是该用户的长期记忆，请根据此个性回复」），实现跨轮个性化——「agent 越来越懂用户，就是因为你有了 memory」（06:26-10:44）。
4. 记忆必须精简：杂乱对话全量存入会让记忆系统不干净、对后续问答无用，所以必须用大模型压缩到精华为止（09:01-09:17）。

### 关键机制
- 写入链路：用户消息 → ADD(user_id, text, importance) → embedding → 存向量库（00:11-00:35）。
- 检索链路：query → embedding → 向量相似度取 top-k 候选 → 按时间戳/重要性打分排序 → 返回排序后的 top-k（01:02-01:23）。
- memory item 六字段：user_id（多用户隔离）、text、vector、importance、created_at、last_access（02:20-02:52）。
- 记忆闭环：多轮对话 → LLM 抽取事实/偏好 → 逐条 ADD 入库 → 下轮检索命中 → 拼 system message → 回复后再抽取（05:26-10:44）。
- 工程替换建议：演示用 list+sentence transformer，生产环境可替换为 ChromaDB/Faiss 等向量库与更优质的 embedding 模型（01:29-03:50）。

### 可操作细节
- memory item 六字段：user_id、text、vector、importance、created_at、last_access（02:20-02:52）。
- 抽取 prompt 模板：「分析下边一轮对话，提取关于用户的值得长期记住的事实或者偏好，每行一条格式简短（如：用户偏好沟通风格简洁）；若没有任何记住的内容，直接输出 none」（07:58-08:13）。
- system prompt 模板：「你是一个助手，回答尽量简洁。以下是该用户的长期记忆：……请根据此个性回复」（10:14-10:31）。
- 示例抽取结果：第一轮「我叫阿明/回复简洁/不要用表情符号」→ 抽三条（用户姓名阿明、回复简洁、用户偏好不使用表情符号）入库；第二轮命中后 system message 携带三条记忆（09:40-10:11）。
- 演示数据：importance 与时间戳作为排序因子参与 top-k 重排（00:42-01:16）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 用 LLM 抽取「值得长期记住的事实/偏好」而非存原始对话 | 07:18-08:13 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.10（三级知识生产管道：raw→item）+ §2.2（三硬一软：可审计压缩） | 支撑：外部 LLM 抽取=Kairos item 层加工的工业界对应；「无内容输出 none」≈「非事实不沉淀」的约束 | 外部为黑盒单次抽取，未建模升华分层 |
| 检索排序=语义相似度+时间戳+重要性 | 01:02-01:23 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（五轴度量模型：时间/使用价值）+ [架构](../../../foundation/architecture-v0.1.0.md) §7.3a（三信号混合检索） | 支撑：外部排序维度与 Kairos 时间轴/使用价值轴同向；但外部 importance 为人工传参，Kairos 以度量轴量化 | — |
| last_access 字段：记录每条记忆最近一次查询时间 | 02:45-02:52 | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（使用价值轴）+ §1.9（上下文腐烂） | 支撑：last_access=「记忆即使用」的直接工程信号，可作为使用价值度量/遗忘调度的输入；Kairos 可考虑显式化该信号 | 外部仅记录未使用，用途未说明 |
| 检索命中记忆拼入 system message 注入上下文 | 06:26-10:31 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §4.3（编译管线：系统提示词多阶段动态组装） | 支撑：外部将检索结果注入 system message 与 Kairos 编译管线同构；Kairos 进一步区分等级/契约/见证 | — |
| importance 的赋值来源与校验 | 00:11-00:41 | 张力 | [认知基础](../../../foundation/cognitive-foundation.md) §2.1（六级辞典式排序链） | 未触及：外部 importance 由调用方手工传参，无生成与校验机制；Kairos 的价值评判由排序链+差异检验承担 | 低成熟度演示，系未展开而非缺陷 |

## 存疑与未验证
- 「importance」如何赋值、由谁赋值（用户/LLM/调用方）视频未说明（未验证）。
- 抽取机制未含去重/覆盖逻辑——同一事实跨轮重复抽取会并存多条，视频未讨论（未验证）。
- 排序公式（时间戳/重要性如何加权合并）未给出，仅示意（未验证）。
- 「节省成本/性能」类断言无评测数据（未验证）。
- 字幕错字：「唯唯英文be点」「ka dB」「face」应为 Faiss 等（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
