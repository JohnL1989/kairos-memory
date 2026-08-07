---
title: VID-79 视频笔记：纯文本agent memory论文串讲
aliases:
  - 外部视频笔记-79
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-79 纯文本agent memory论文串讲

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1igFTzfE7a |
| UP主 | 日新月异max |
| 时长 | 114min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写存在大量谐音错字（「炸藥/扎要」应为「摘要」，「解鎖/減索/監鎖」应为「检索」，「以萬/一萬」应为「遗忘」，「增傷改差」应为「增删改查」，「配戟/配給」应为「page/页」，「纏時記憶」应为「长期记忆」，「真流」应为「蒸馏」，「項量」应为「向量」等） |

## 内容提炼
### 核心论点
1. 按时间线串讲 9 篇纯文本 Agent Memory 论文：MemGPT(虚拟上下文管理/分页) → MemoryBank(艾宾浩斯遗忘曲线) → LoCoMo(长程对话评测集) → ReadAgent(Gist 摘要二级检索) → MemoryOS(段页式热度管理) → MEM(卡片盒记忆法) → MemoryR1(RL 记忆管理) → LightMem/SimpleMem(压缩与自适应检索)（00:42-01:16）。
2. MemoryBank 首创用艾宾浩斯遗忘曲线建模记忆强度：R = Re^(-t/S)，t 以天计距上次提及的时间，S 为被提及次数；再次提及即 t 归 0 且 S+1（21:51-23:41）。
3. MemoryR1 用强化学习让 agent 学会"增删改查"记忆：memory manager（增加/更新/删除/不操作四操作）+ answer agent 双 agent，结果驱动 RL（PPO/GRPO）微调；奖励用 Exact Match 优于 LM-as-judge（消融结论）（69:01-71:25，77:19-78:46）。
4. LightMem 提出"睡眠时更新"：基于熵的压缩模型做预处理 + 主题分割 + 长期记忆离线（非对话时）更新，把延迟从用户对话中移走（79:25-83:08）。
5. SimpleMem 语义无损压缩三步：信息值过滤（新命名实体比例+语义差异度）→记忆结构化（指代消解+相对时间转绝对时间戳）→三层存储（语义向量/词汇 BM25/符号时间戳实体）；检索数量由查询复杂度分类器动态决定 k_dynamic（94:37-113:35）。

### 关键机制
- MemGPT：prompt 由 system instruction + working context + FIFO 队列组成；通过 function calling（如 working_context.replace 把 boyfriend James 替换为 ex-boyfriend）读写 archival storage/recall storage，本质是"让 LLM 用函数调用来管理自己上下文"（06:42-12:48）。
- LoCoMo 构造管线：双 LLM agent 角色扮演（persona 定义）+ 时间事件图驱动对话生成 + 反思/图片分享 + 人工编辑标注；10 个对话、每个约 600 轮、单对话最高 116K token（29:44-30:20，43:44-45:56）。
- LoCoMo 评测任务：事件问答（单跳/多跳/时序推理/常识世界知识/对抗性防幻觉）+ 事件摘要 + 多模态对话生成（34:52-42:01）。
- ReadAgent：长文本按 max/min words 分页 → 每页 Gisting 摘要成 Gist memory → 大模型先查 Gist 再决定是否深入查具体页（并行版 P 可查多个，串行版 S 只能查一个）；上下文压缩比=实际/原始（46:36-53:02）。
- MEM（Zettelkasten 卡片盒）：note = {原始上下文 ci, 时间戳 ti, 关键词 ki, 标签 gi, 语义描述 xi, embedding ei, 链接 li}；新 note 与 topK 相似 note 由 LLM 判定是否建链；box=同主题 note 集合（63:12-68:35）。
- MemoryR1 训练：先固定 answer agent 用 RL 优化 memory manager（间接奖励），再固定 manager 训练 answer agent（直接奖励）；数据 152 条 QA、3B-10B 模型（71:26-71:46，76:18-76:42）。
- LightMem：压缩子模块输出每个 token 的保留概率（softmax logits），交叉熵超过阈值 τ 才保留（83:53-85:41）；主题分割用注意力分数边界 B1∩B2（86:00-87:23）；复杂度分析：API 调用次数由阈值 th 决定（91:42-93:58）。
- SimpleMem 公式：信息值 h = 新实体比例 + (1-余弦相似度)；检索得分 s = 语义相似 + BM25 + 指示函数(时间等符号约束)×γ；k_dynamic = ⌊k_base×(1+τ·cq)⌋，cq 由轻量分类器预测查询复杂度（101:02-112:58）。

### 可操作细节
- MemoryR1：152 条 QA 训练数据即可表现强能力；GRPO 优于 PPO（无需 value 模型、均值消除噪声）（71:26-71:46，77:19-77:48）。
- ReadAgent 分页参数：最短/最长上下文长度两个阈值控制分页粒度（50:02-50:47）。
- LightMem 更新阈值 th：记忆达到阈值才触发一次摘要 API 调用，控制 token 成本（92:20-92:33）。
- MEM：链接生成=新 note 与 topK 近邻拼接+LLM 判定（66:32-67:14）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 艾宾浩斯遗忘曲线建模记忆（MemoryBank） | 21:51-23:41 | 矛盾 | [架构](../../../foundation/architecture-v0.1.0.md) §0.3（推论四：遗忘是工程权衡 loss×P vs noise_cost，非生物模仿） | 挑战：Kairos 明确拒绝生物模仿式遗忘；t/S 两参数仅可视为时间轴"物理衰减"的粗近似，缺失逻辑-因果轴与价值轴 | 可对照引用以澄清 Kairos 立场 |
| RL 记忆管理（MemoryR1：agent 学会增删改查） | 69:01-71:25 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §10.14（RL 权重优化器：同级内二次排序）+ §10.15（自反思元记忆优化） | 未触及：Kairos RL 用于排序调制而非记忆操作决策；"学习记忆操作"可作为策略层远期形态，但需先过宪法主权面权限界定 | 与 T-002 外部校准源主题相关 |
| 卡片盒记忆法（MEM：note+链接+box） | 56:30-68:58 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（关系层：因果链引用/路径父子关系）+ [架构](../../../foundation/architecture-v0.1.0.md) §5.2（存储层组件） | 支撑：note 链接=Kairos 关系层链接；box=主题聚类=路径空间雏形；MEM 是"记忆+链接"组织方式的外部印证 | — |
| 睡眠时离线更新（LightMem） | 79:25-83:08 | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.3（巩固：易变→稳定表征）+ [架构](../../../foundation/architecture-v0.1.0.md) §3（遗忘引擎） | 支撑：Kairos 巩固/遗忘本就是后台批处理；LightMem 的"对话期间零更新、低延迟"经验可吸收为遗忘调度器时序设计参考 | 与 VID-81 睡眠学习同族 |
| 查询复杂度驱动的动态检索数量（SimpleMem） | 110:35-112:58 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §3.9（检索深度分级 R0/R1/R2） | 支撑：Kairos 深度分级为离散档位，SimpleMem 是连续数量自适应；两者可融合（档位内动态 k） | — |
| 熵过滤+指代消解+绝对时间戳（SimpleMem 语义无损压缩） | 103:23-105:29 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §2.2（三硬一软：可审计压缩） | 支撑：指代消解与绝对时间戳即"可审计压缩"的具体算子；Kairos 压缩纪律要求审计性，二者同向 | — |
| 分层存储（语义/词汇/符号三层） | 105:31-106:50 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a（三信号混合检索：语义+BM25+实体） | 支撑：三层=三信号的存储侧对应；Kairos 检索融合与 SimpleMem 分层检索同构 | — |
| 长程对话评测集（LoCoMo）与基准被刷风险 | 27:42-30:20，43:44-45:56 | 已覆盖 | [质量](../../../quality/benchmark-plan.md) §3.11（基准设计红线：经验来源与验证数据分离） | 支撑：Kairos 基准设计内置防污染红线，回应外部"评测集被刷烂"的行业现象 | — |
| 对抗性评测（防幻觉问答） | 39:47-40:21 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（见证价值轴：校准置信度+叙事自洽度） | 支撑：Kairos 以见证锚定对抗幻觉，评测层面有反事实检验（test-strategy §2.7） | — |
| MemGPT 函数调用管理记忆 | 06:42-12:48 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3.1（十二规范操作集） | 支撑：函数化记忆操作=Kairos 规范操作集的早期形态；Kairos 将操作集显式化 | — |

## 存疑与未验证
- 视频年份表述混乱（转写出现 2013/2014/2023/2024 混用），各论文发表年份以 UP 主转述为准，未逐一核对（未验证）。
- 「LoCoMo 600 轮、1.6 万 token、32 个会话页、116K token」等数字系转述，未与数据集原文核对（未验证）。
- 「MEM 发表于 NeurIPS 2025」「SimpleMem 1 月初提出、2000+ star」「MemoryR1 代码未开源、152 条 QA」等信息未验证（未验证）。
- 「MemoryBank 用 LoRA rank=16 在一张 A100 上微调心理学垂域模型」为转述细节，未与原文核对（未验证）。
- 「BALY 是多语言模型」「Silicon Friend」等产品名由谐音转写，无法确认原名（未验证）。
- SimpleMem「原文用 BM25」与「reg 方法的 bm25」表述存在 UP 主口误可能，机制细节以论文为准（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
