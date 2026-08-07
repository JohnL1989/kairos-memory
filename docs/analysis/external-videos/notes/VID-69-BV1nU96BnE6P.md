---
title: VID-69 视频笔记：浅入深出 Agent 系列之八——Agent Memory 管理
aliases:
  - 外部视频笔记-69
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-69 浅入深出 Agent 系列之八：Agent Memory 管理

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1nU96BnE6P |
| UP主 | 奇创喵 |
| 时长 | 27min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字 |

## 内容提炼
### 核心论点
1. LLM 原生无记忆：模型是 y=f(x)，参数在训练结束时就固定、与输入无关；所谓「有记忆」是把历史对话拼成长序列注入 x，靠注意力机制表现得像有记忆——本质是打补丁（00:33 / 01:13 / 01:48）
2. 第一层补丁（无限拼接历史）有两个缺点：存储空间有限（输入越来越长资源负载过重）；注意力扩散——上下文过长时模型无法把正确注意力放在正确内容上，导致幻觉/回答牛头不对马嘴，因此必须限制 context window（01:49 / 02:26 / 02:43）
3. 滑动窗口（丢旧加新）有一个致命漏洞：旧数据不代表不重要——自我介绍、使用偏好（习惯中文）、语言偏好这些关键信息恰恰在最早的对话里，滑走就全没了（03:48 / 04:14 / 04:56）
4. 主流做法分两派：数据库派（RAG：把记忆当 chunk 存入支持关键词+向量+混合搜索的数据库）与 markdown 派（蒸馏 distill：按结构化条目提取关键信息写入 markdown，transcript 原始消息兜底）；两派在「取」上又分直取（不经过 LLM）与经 LLM 取（ReAct 式 agent 生成搜索方案并判断是否 refine）（05:10 / 06:08 / 10:40 / 12:07）
5. memory 是设计 agent 的重中之重，好的 memory 设计很大程度上决定了 agent 好不好用（27:21）

### 关键机制
- distill 与普通 summarize 的区别：summarize 只是把长的变短的；distill 需要按规范化条目生成结构化信息——这段话的 topic 是什么、关注点 focus、是否揭示用户偏好 preference，然后写进 markdown；本质是一次有结构的压缩；为保险起见把历史消息文档化为 transcript（raw data）兜底，但通常在 markdown 架构下不下沉、只作保底（06:08 / 06:42 / 07:28）
- RAG 派落地：历史消息当 chunk（长文按段落/字数切 chunk），把 topic、用户偏好等元信息嵌入 chunk（chunk = 元信息 + 原文），插入数据库（例：Elasticsearch 同时支持 BM25 关键词搜索、向量 embedding 搜索与混合搜索）（08:37 / 09:56）
- 取的两种套路：直取——把用户 query 直接 embedding 成向量去数据库比对 recall，或用分词器做关键词搜索 + BM25 评分，不经过 LLM、快且不消耗 token；经 LLM 取——做一个 ReAct 模式 agent，由 LLM 分析 query 生成更合适的搜索方案（用什么关键词），recall 后让 LLM reason 判断文档是否足够，不足则 refine query 再去数据库搜（10:40 / 11:12 / 12:07）
- Claude Code 三层记忆分层（UP 转述）：
  1. memory（markdown）：长期、跨会话的记忆内容——用户偏好（如希望用代码回答、少辅助信息）、项目简介（proof）等随项目发展略有变化的稳定内容，几乎不变的记忆单元（12:37 / 13:26）
  2. topics：按主题组织的结构化信息——如 database deployment 主题下记录数据库 type/version/constraint（如 MongoDB 8.0）；升级到 8.1 时更新当前值并把「8.0→8.1」写进 historical 段落，保证记忆可回溯、查 bug 有可追溯性，等于给 LLM 打「记忆提示」让它意识到别处的 8.0 已过时（14:31 / 15:29 / 16:06）
  3. transcript：原生 raw message 兜底——上面总结找不到信息时回原始消息找；但因用 markdown 查找，性能效率不如 RAG（16:46 / 17:21）
- memory 结构化更新：内部按 JSON dict 维护——profile / user preference / constraint（全局约束，如写文件删文件必须提示，不随会话变化）；LLM 做 compress 时按 key 生成结构化 dict 逐项更新，最后落盘才渲染回 markdown 格式，避免直接改文本文件（痛苦且易错）（17:50 / 20:37）
- 冰与火 trade-off：key 定义的两极——predefined（预设 20 个 key 写进 system prompt，最冰最可控；即使 LLM 抽风生成同义词 key 导致 merge 不上，可丢回 LLM 找对应 key）vs 全由 LLM 自定义（动态但不可控：可能生成新 key 如 overview/focus，需判断 append 还是 update、需要更多轮次 LLM 决定）；业界通常取中间态：predefined 的 key 足够广泛，让 LLM 不需要自己造词（21:45 / 22:30 / 24:25）
- memory 与 topics 的加载差异：memory 永远加载进上下文；topics 只在当前内容涉及该主题时才加载；topics 清单轻量写入 memory（known topics + 简短简介，因永远加载所以不能太长）；也可以给 LLM 一个 grep tool 去搜 md 文件（多一次工具调用、多一次 LLM、额外 token 与时间消耗）（24:27 / 26:26 / 27:13）
- 经验参数：主流优秀 agent 采用约 200K token 的上下文窗口（R100K=20 万 token，经大量实践得出；即使有模型宣称支持 100 万，注意力扩散问题仍在）（02:52 / 03:37）

### 可操作细节
- 分层记忆模板：memory（长期稳定）+ topics（主题结构化，含 historical 段落记录版本变迁）+ transcript（raw 兜底）（12:37 / 16:06）
- 结构化 key 模板：profile / user preference / constraint（全局约束）三类起步；predefined key 写进 system prompt（17:50 / 22:30）
- 检索分档：直取（embedding 或 BM25）≈零 token 快速路径；经 LLM 取（ReAct+refine）≈慢路径（10:40 / 12:07）
- 主题加载：known topics 清单写入 memory 常驻，详情文件按需加载（26:26）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| LLM 无原生记忆、记忆靠注入上下文（y=f(x)） | 00:33 / 01:13 / 01:48 | 已覆盖（互为印证） | 契约是运行时投影（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2 软原则）；检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：外部补丁式记忆 = Kairos「记忆注入上下文」前提的独立陈述 | — |
| 滑动窗口致命漏洞：早期关键信息（自我介绍/偏好）被滑掉 | 03:48 / 04:14 / 04:56 | 已覆盖 | 身份面否决权（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；身份面常驻、Profile Schema（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.14）；时间轴双轴（认知基础 §1.1） | 支撑：身份/偏好类信息必须脱离滑动窗口常驻——正是身份面否决权解决的问题 | 与 VID-67「滑动窗口丢最老」的缺陷批评同族 |
| distill 结构化蒸馏（按条目提取 topic/focus/preference）vs 普通 summarize | 06:08 / 06:42 / 07:28 | 已覆盖 | 可审计压缩硬约束（激活-存储解耦+可审计压缩，[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；升华管道 raw→item（§1.10） | 支撑：按规范化条目提取=有结构压缩=可审计压缩的工程形态；「普通 summarize 会丢结构」正是 Kairos 拒绝无声丢失的立场 | — |
| transcript 原始消息兜底（保底不删） | 07:28 / 16:46 | 已覆盖 | ADD-only 提取协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；见证锚定主副本（§5.5） | 支撑：摘要之上保留原文可回查 = 见证锚定+审计痕迹 | 与 VID-67 Ledger 流水账本同族 |
| 直取（embedding/BM25 零 token）vs 经 LLM 取（ReAct+refine） | 10:40 / 12:07 | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；双模检索架构 Fast Context + Deep Reasoning（§7.3d） | 支撑：不经过 LLM 的快速路径 vs LLM 按需唤醒的深推理路径——与 R0/R1/R2、双模检索几乎一一对应 | 强印证：外部独立设计出同样分级 |
| predefined key vs LLM 自由 key（冰与火） | 21:45 / 22:30 / 24:25 | 可吸收 | 可配置 Profile Schema（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.14） | 支撑：「预设 key 足够广泛让 LLM 不造词」是 Schema 约束分类器的同款思路；「merge 不上丢回 LLM 找 key」是 Schema 校验闭环 | 与 REPO-01 bucket 描述约束分类器可合并吸收 |
| 版本变迁写 historical 段落（8.0→8.1 可回溯） | 15:29 / 16:06 | 已覆盖 | 见证锚定主副本保留历史版本（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5）；ADD-only 新旧观察并存（§7.3g） | 支撑：升级记录可回溯、让模型意识到旧值过时 = 见证版本化的效用论证 | 「给 LLM 打记忆提示」即检索时可见新旧观察 |
| memory 永远加载 vs topics 按需加载 | 24:27 / 26:26 | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9）；身份面常驻（认知基础 §2.1） | 支撑：常驻层 vs 按需检索层的分工与 R0/R1 分级同构 | topics 清单「永远加载所以必须轻量」= R0 常驻预算约束 |
| 注意力扩散 → 必须限制窗口（200K 经验值） | 02:52 / 03:37 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9）；注意力调度器 token 预算分解（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §9） | 支撑：上下文长度与退化（幻觉）的因果主张与上下文腐烂指标同向 | 200K 为经验值，非机制增量 |
| RAG 派把记忆当 chunk + 元信息嵌入 | 08:37 / 09:56 | 已覆盖 | 三信号混合检索（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a）；GSPO 聚类去重（§7.3b） | 支撑：chunk+元信息是检索索引的常规形态；Kairos 以「索引为派生可重建」超越之 | — |

## 存疑与未验证
- 「Claude Code 三层记忆（memory/topics/transcript）」为 UP 主转述，层级命名（topics/transcript/historical 段落）未给出官方文档出处，与 Claude Code 实际实现的对应关系未核实（未验证）
- 「R100K=200K token 是大量实践得出的合适窗口大小」为 UP 主经验判断，无评测依据（未验证）
- 「Elasticsearch 同时支持 BM25+向量+混合搜索」为技术常识性陈述，未在视频中演示（未验证）
- 转写错字较多：「IG/RIG/rig」（RAG）、「Trunk/Chunk」（chunk）、「context spindle」（上下文）、「bmw/bmr5」（BM25）、「disdued/disto/distill」（蒸馏）、「clawed code/crawl code」（Claude Code）、「Proof」（项目简介）、「冰火俩中天」（冰火两重天）、「规议化」（归一化）等，术语以语义还原
- 「transcript 名字起得有点名不副实」为 UP 个人评论，无争议性内容（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
