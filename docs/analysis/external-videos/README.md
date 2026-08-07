---
title: 外部视频分析批次索引
aliases:
  - 外部视频分析
tags:
  - kairos
  - analysis
  - external-videos
created: 2026-08-07
updated: 2026-08-08
last_reviewed: 2026-08-08
status: draft
---

# 外部视频分析批次索引

> **批次定位**：本目录承载「B站 AI Agent 记忆系统视频 × Kairos」对照分析批次的全部产出——102 个视频的素材边界声明、逐视频精读笔记、外部理念分诊矩阵、第一性原理对照评审与吸收建议清单。**本批次不修改任何核心设计文档**（foundation/specification 零改动），吸收建议止于「建议态」，是否落库由后续批次决策。

> **T-002 关联**：本批次本身是「外部校准源以什么形态进入体系」的实践样本——全部外部理念以「视频字幕/转写 → 笔记 → 分诊矩阵」的受控管道进入，未直接注入设计文档。观察与建议分离，见 [triage-matrix.md](triage-matrix.md) 的 T-002 实例样本节。

## 素材边界声明（重要）

**B站 AI 字幕存在严重内容串台问题（2026-08-07 实测）**：通过公开接口（`x/player/v2`）与 wbi 签名接口（`x/player/wbi/v2`，网页播放器同款）获取的 `ai-zh` 字幕中，**约 65% 的视频字幕内容与视频主题完全无关**（经人工逐视频中段采样核验），甚至出现多个无关视频返回完全相同字幕的情况。串台由 B站 侧 AI 字幕系统导致，任何接口形态均无法规避。

因此本批次素材来源分三级，每份笔记的「素材边界声明」如实标注：

| 级别 | 获取途径 | 可信度 | 数量 |
|:--|:--|:--|:--|
| A. B站 AI 字幕（匹配） | `x/player/v2` + Cookie，人工核验中段内容与主题匹配 | 高（个别错字） | 27 |
| B. 本地 whisper 转写 | yt-dlp 下载音频 + faster-whisper（small/int8）本地转写 | 高（转写质量经抽查） | 73（48 可用 + 25 串台重转写成功 + VID-54 部分降级，见清单素材级别列） |
| C. 素材降级 | 无有效语音 / 20 小时串台合集 / 转写静音 | 不适用（仅元信息） | 2（VID-91 无有效语音、VID-97 串台合集） |

> 过程材料（原始字幕 JSON、音频、弹幕）存于仓库根 `video-work/`（gitignored，不入库）；抓取/转写流程复现步骤见 [process/fetch-guide.md](process/fetch-guide.md)。

## 视频清单（102 个）

| VID | BVID | 标题 | UP主 | 时长 | 素材级别 |
|:--|:--|:--|:--|:--|:--|
| VID-01 | BV1zUTn61EY8 | 7个AI记忆系统从夯到拉 | 小行星AI观测站 | 8min | B|
| VID-02 | BV1nJ396JEmC | Claude Code 上下文压缩与会话恢复 | 唐国梁Tommy | 14min | A |
| VID-03 | BV17KoFBBEqM | Hermes 四层记忆系统持久化 | 唐国梁Tommy | 22min | B |
| VID-04 | BV1p2DyB4Ee3 | 5大Agent Memory工程级对比 | 唐国梁Tommy | 15min | B |
| VID-05 | BV1orQJB2Edt | MemOS/OpenViking 深度拆解 | 唐国梁Tommy | 24min | B |
| VID-06 | BV1z6SXBzEYh | Claude Code 六维记忆体系 | 唐国梁Tommy | 24min | B |
| VID-07 | BV1y5Kp6XEd3 | 生产级Agent记忆系统架构与工程治理 | AI大模型学习study | 12min | B |
| VID-08 | BV1erEA62EU9 | 热门的 AI Agent 记忆框架全拆 | 廖定强AI笔记 | 8min | A |
| VID-09 | BV1BM3169EUS | MRAgent 记忆是重建而非检索 | 白拾的物理AI组会 | 32min | B |
| VID-10 | BV1uiEM6xE9s | 7步设计Agent记忆系统 | 费曼学AI | 17min | B |
| VID-11 | BV1kSMM6nEhV | 5个信号诊断记忆系统 | 费曼学AI | 7min | B |
| VID-12 | BV1Z1jJ6cEVE | MemoryOS 三层存储架构 | 加菲大杂烩 | 44min | A |
| VID-13 | BV1tiuA6mENb | TencentDB Agent Memory v2.0 | 智能体老王 | 4min | B|
| VID-14 | BV1j3gz6vEQQ | Anthropic 官方 Agent Memory | AI变局 | 28min | A |
| VID-15 | BV1TUM26vEAC | pi-hermes-memory 实战 | 程序员暮闲 | 9min | B|
| VID-16 | BV1YXVg69EmC | OpenClaw 三大搜索+七家嵌入 | big叔大 | 4min | A |
| VID-17 | BV136oYBWEU2 | 个人 Agent 记忆系统实现 | 小单说AI | 13min | B|
| VID-18 | BV1XCKL6SEg5 | Agent记忆系统设计 | 赫尔辛根默斯肯人 | 6min | B|
| VID-19 | BV11RGX6bEdc | OpenClaw 三层架构+Dreaming | big叔大 | 6min | A |
| VID-20 | BV1C8LF62EWa | 9K 星：给 AI Agent 加上长期记忆 | AIlazy俊 | 3min | A |
| VID-21 | BV1V9Lp68Ey1 | TencentDB-Agent-Memory 解析 | 鲲鹏Talk | 5min | B|
| VID-22 | BV1vFME6eEHP | Memorix 共享记忆 | 老汤的碳基突围 | 7min | B|
| VID-23 | BV18kDjBxEYR | 某讯 Agent Memory 分层索引 | AGI_Ananas | 5min | B|
| VID-24 | BV1LVMV6nEMt | 构建Agent长期记忆系统（10P） | 小寒说IT | 127min | A（6P 匹配，3P 串台） |
| VID-25 | BV1xoLD6cEEL | 人脑仿生遗忘系统 | 老纪的技术唠嗑局 | 13min | B |
| VID-26 | BV1F7P9zLErb | mem0 开源框架解析 | 加菲大杂烩 | 40min | B|
| VID-27 | BV1H8VQ6DEBB | Mem0 极简路线 | 为什么叫QQ | 12min | A |
| VID-28 | BV1oxNZ6uE6G | Memorix 记忆跟着项目走 | AI技术投降派 | 11min | A |
| VID-29 | BV1NyMk6QEKB | AI面试：如何实现长期记忆 | DeepTalk-Pro | 2min | B|
| VID-30 | BV1FpRaBFENL | 4款记忆方案分清 | Ali厂长 | 5min | A |
| VID-31 | BV1rnM269ErH | OpenClaw 讲透 Agent 记忆 | 小马Bosn | 18min | A |
| VID-32 | BV1tk376oEHn | AutoMem 记忆演化技能 | breezedeus | 29min | B|
| VID-33 | BV1QwGT6MEKQ | OptMem 一行一段永久记忆 | jeffzhengye | 7min | B|
| VID-34 | BV1PU3b6pEVP | 记忆写入全链路 | AI架构师Leo | 14min | B |
| VID-35 | BV1HhGV6kEmt | Metis 原生记忆基础模型 | 熊二等兵 | 18min | B |
| VID-36 | BV1P4Mr6LEem | AutoGenetic Memory | openJiuwen | 1min | B|
| VID-37 | BV1L2gY6jErn | Claude 2026 记忆系统新功能 | AI酷生活 | 3min | A |
| VID-38 | BV1v8PYz1EUt | mem0 代码精读 | 日新月异max | 101min | B|
| VID-39 | BV1k65X6dExY | Letta/MemGPT 持久记忆 | AI技术投降派 | 5min | A |
| VID-40 | BV18yX6BFEHS | Zep 长期记忆系统 | 郭宏志-老郭 | 14min | B|
| VID-41 | BV1nS7X6hECB | supermemory 长期记忆 | 码上成功的小猴 | 1min | B|
| VID-42 | BV1JggX6kEbs | 让AI自动进化的记忆系统 | 新书提拉 | 4min | A |
| VID-43 | BV1vkEj6WE3F | 基于Mem0的上下文和记忆管理 | 人月聊IT | 6min | B|
| VID-44 | BV1NS3h68EVL | 百万上下文只是超大垃圾桶 | 元共格 | 15min | B |
| VID-45 | BV14dTY6bEYF | Hermes 记忆与上下文完全指南 | Andy要上岸机器学习 | 14min | B（whisper） |
| VID-46 | BV1erKP6pEjx | 分层记忆系统设计 | 喵叔的捣奈特 | 20min | B |
| VID-47 | BV1CpgQ61EGn | 从零构建生产级 Agent Memory（一） | 老纪的技术唠嗑局 | 5min | A |
| VID-48 | BV11wga6tEGH | 从零构建生产级 Agent Memory（二） | 老纪的技术唠嗑局 | 5min | B|
| VID-49 | BV15L3F6pEFN | 从零构建生产级 Agent Memory（三） | 老纪的技术唠嗑局 | 4min | B|
| VID-50 | BV1AA3i6TEAU | 从零构建生产级 Agent Memory（四） | 老纪的技术唠嗑局 | 4min | B|
| VID-51 | BV1fp3k6mEJU | 从零构建生产级 Agent Memory（五） | 老纪的技术唠嗑局 | 4min | B|
| VID-52 | BV145326zEAM | 从零构建生产级 Agent Memory（六） | 老纪的技术唠嗑局 | 4min | A |
| VID-53 | BV1wkMB6qEyN | Google Memory Bank 长期记忆 | AI变局 | 21min | B|
| VID-54 | BV18G3z6oE4p | Anthropic Memory+Dreaming | AI变局 | 27min | B（部分降级）|
| VID-55 | BV1LG3F6sEn9 | 短时/长期记忆分层精讲 | AI大模型原理 | 3min | A |
| VID-56 | BV14B3S6SEaw | LLM 记忆做成文件系统（论文） | 熊二等兵 | 13min | A |
| VID-57 | BV1hn5E6kEdW | AgentSwing 动态上下文管理 | Agent智能体深度研究院 | 8min | B |
| VID-58 | BV1WuLH66EHg | RF-Mem 快慢双路径检索 | Agent智能体深度研究院 | 9min | A |
| VID-59 | BV1EnLH6AEz5 | MemCoE 先学怎么记 | Agent智能体深度研究院 | 12min | A |
| VID-60 | BV1VhLH6xEjy | GAM 即时编译式记忆 | Agent智能体深度研究院 | 9min | B |
| VID-61 | BV1dfGh6jE2j | LightMem 三段式处理 | Agent智能体深度研究院 | 8min | B |
| VID-62 | BV1QBgi6EEeV | RE-TRAC 轨迹压缩 | Agent智能体深度研究院 | 11min | A |
| VID-63 | BV1Ty3764E59 | PlugMem 交互历史重构 | Agent智能体深度研究院 | 12min | B|
| VID-64 | BV1rQEB6oEpe | OpenAI Dreaming 记忆 | Agent智能体深度研究院 | 13min | B |
| VID-65 | BV1QEgx6HEyF | MedRGAG 该信查到的还是记得的 | Agent智能体深度研究院 | 10min | B |
| VID-66 | BV1QJ7z6CES8 | SuperMemory 技术架构解析 | AI大白话007 | 4min | B|
| VID-67 | BV1Eg5C6xERt | 四层记忆架构详解（用户补充） | Agent开发实战 | 16min | B |
| VID-68 | BV1eTPEzNEqf | 解决OpenClaw长期记忆4种方法 | 一蛙AI | 11min | B |
| VID-69 | BV1nU96BnE6P | 浅入深出 Agent 系列之八：Agent Memory 管理 | 奇创喵 | 27min | B |
| VID-70 | BV1uvT16aEBx | 01 RAG Agent 短期记忆 | AI_Julie | 15min | B |
| VID-71 | BV1TXTQ65E45 | 04 memory 打分三要素 | AI_Julie | 8min | B |
| VID-72 | BV1gqNc6vEes | 05 Agent memory 的设计 | AI_Julie | 12min | B |
| VID-73 | BV1gRNF6PE48 | 07 吐血整理的Agent memory 设计 | AI_Julie | 18min | B |
| VID-74 | BV1CZNN6iEWq | 08 吐血整理的Agent memory 设计 | AI_Julie | 19min | B |
| VID-75 | BV1cezTBDEgQ | Agent Memory 是什么？【论文精读】 | 日新月异max | 33min | B |
| VID-76 | BV1qnzQBMEnq | 入门Agent Memory【代码精读】 | 日新月异max | 44min | B |
| VID-77 | BV1oa6uBXE8J | MemoryOS 操作系统实现【论文精读】 | 日新月异max | 43min | B |
| VID-78 | BV1hr6EBBEhM | 看Github项目，以MemoryOS为例【代码精读】 | 日新月异max | 70min | B |
| VID-79 | BV1igFTzfE7a | 纯文本agent memory论文串讲【论文精读】 | 日新月异max | 114min | B |
| VID-80 | BV1nWABzwEuG | MemVerse 多模态记忆【论文精读】 | 日新月异max | 63min | B |
| VID-81 | BV1dRNMzLEof | Mindverse 模型即记忆【深度解析】 | 日新月异max | 35min | B |
| VID-82 | BV1XZw9zFEXy | 端到端上下文工程：Zep【代码解读】 | 日新月异max | 31min | B |
| VID-83 | BV1zxL561EcM | 文件存储记忆 memU【代码解读】 | 日新月异max | 33min | B |
| VID-84 | BV1wmGg6NEaz | Metis 原生记忆大模型（用户补充） | 每日Arxiv | 13min | B |
| VID-85 | BV1Z2GP66EWp | 构建生产级Agent Memory系统架构（用户补充） | Ai大模型实战教学 | 12min | B |
| VID-86 | BV1HUjU6QEds | Hermes Agent架构：Memory、上下文与网关（用户补充） | 狡猾的哈基 | 40min | B |
| VID-87 | BV1Bm6bB5EJ3 | OpenClaw是什么（搜索精选） | 小白debug | 6min | B |
| VID-88 | BV1RCGR6yEEw | RAG/Memory 语义检索原理（搜索精选） | 小白debug | 9min | B |
| VID-89 | BV1WV2vBWEkL | Episodic Memory（搜索精选） | 亚马逊云科技 | 3min | B |
| VID-90 | BV1ZA93BtEKW | Claude Code 记忆系统设计（搜索精选） | 五道口纳什 | 21min | B |
| VID-91 | BV1hDEN6EESL | Agent 自主经营环世界（搜索精选） | 徇Official | 60min | C（无有效语音） |
| VID-92 | BV1KwwzzGEvD | OpenClaw graph-memory 插件（搜索精选） | AGI_Ananas | 12min | B |
| VID-93 | BV1xUcZzfEaB | openclaw 图谱记忆（搜索精选） | AGI_Ananas | 9min | B |
| VID-94 | BV19XvDBQE6y | 重新定义 agent Memory（搜索精选） | 慢学AI | 7min | B |
| VID-95 | BV1s81xBZEPn | NeurIPS Plan Caching（搜索精选） | iHang的科研笔记 | 20min | B |
| VID-96 | BV1RczjBPE8K | Agent Skills 对比（搜索精选） | 御风大世界 | 6min | B |
| VID-97 | BV1dE97BrEYX | 20小时 Agent Memory 教程合集（搜索精选） | 大模型小爱 | 1216min | C（串台合集） |
| VID-98 | BV1SSfBBzEWL | Memorix：跨 Agent 记忆桥 | Le_Ho | 1min | A |
| VID-99 | BV11kT16dErg | 02 RAG Agent 长期记忆 | AI_Julie | 12min | A |
| VID-100 | BV12rT164EP9 | 03 RAG Agent 摘要记忆 | AI_Julie | 12min | A |
| VID-101 | BV1XYNc6TEpt | 06 Agent Harness hermes 设计 | AI_Julie | 6min | A |
| VID-102 | BV1H2NM6rExh | 09 Agent memory 设计 面试宝典 | AI_Julie | 19min | A |

## 目录导航

| 文件 | 职责 |
|:--|:--|
| [triage-matrix.md](triage-matrix.md) | **主对照分析报告**：外部理念 × Kairos 分诊矩阵（EV-01~NN），T-002 实例样本节 |
| [first-principles-review.md](first-principles-review.md) | 第一性原理对照评审：逐原理「支撑/挑战/未触及」评估 |
| [absorption-proposals.md](absorption-proposals.md) | 吸收建议清单（建议态，未登记债务/风险/ADR） |
| [notes/](notes/) | 逐视频精读笔记（VID-XX-<BVID>.md，102 份） |
| [repos/](repos/) | GitHub 仓库源码级深读笔记（REPO-01~15） |
| [papers/](papers/) | 2026 论文深读分析笔记（PAPER-01~10 批次一：PAPER-01~09 源自 AI HOT 学术档案 + 用户映射分析，PAPER-10 G-Memory 为用户直发链接 + 原文 PDF 核验；PAPER-11~21 批次二：2026-08-08 用户直发 13 链接批次，11 篇新论文，2 篇已分析仅交叉引用，素材边界见各笔记） |
| [process/fetch-guide.md](process/fetch-guide.md) | 抓取/转写流程复现记录（不含任何凭据） |

## 批次状态

| 项 | 状态 |
|:--|:--|
| 素材抓取 | ✅ 102 个视频：27 字幕匹配 + 75 whisper 转写（含 2 份降级） |
| 逐视频笔记 | ✅ 102/102（含 2 份全降级标注 + 1 份部分降级标注） |
| 分诊矩阵 / 原理评审 / 吸收建议 | ✅ 汇总完成（triage-matrix EV-01~74 / first-principles-review / absorption-proposals AP-01~52） |
| 论文批次二（13 链接，PAPER-11~21） | ✅ 2026-08-08 完成（0.0.47 批次）：11 份笔记 + 分诊 I 节 EV-60~74 + 吸收建议四d 节 AP-38~52（建议态未落库） |
| 门禁 | 0.0.47 批次收尾时运行 doc-audit.py / deep-audit.py |

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 批次初始化：素材抓取完成（含 B站 AI 字幕串台问题实测记录），目录结构与素材边界声明建立 |
| 0.0.2 | 2026-08-07 | 0.0.42 审计修复：素材统计对齐实际口径（102 个视频：27 字幕 + 75 whisper，C 级降级仅 VID-91/97，VID-54 部分降级）；25 份串台重转写成功的笔记升级为 B 级；清单级别列同步 |
| 0.0.42 | 2026-08-07 | 0.0.2（0.0.42 批次）审计修复：素材统计对齐实际口径（102 视频：27 字幕 + 75 whisper，C 级仅 VID-91/97 全降级 + VID-54 部分降级）；25 份重转写成功笔记升 B 级；清单级别列同步。 |
| 0.0.44 | 2026-08-08 | 0.0.44 批次：PAPER-10（G-Memory）增量（论文批次扩至 10 篇，用户直发链接 + 原文 PDF 核验，papers/ 导航说明同步）；吸收建议 AP-29~37 + PAPER-01~09 增量未覆盖项全量落地至核心设计文档（吸收管线闭环——本批次全部「可吸收」条目已落库）。 |
| 0.0.47 | 2026-08-08 | 0.0.47 批次：13 链接批次（2 篇已分析交叉引用 + 11 篇新论文 PAPER-11~21，第 3 链接 2509.2470 缺位解析为 MemGen 2509.24704）；分诊 I 节 EV-60~74 + 吸收建议四d 节 AP-38~52（建议态未落库）+ 张力 AT-08~09；本批次零改动核心设计文档。 |
