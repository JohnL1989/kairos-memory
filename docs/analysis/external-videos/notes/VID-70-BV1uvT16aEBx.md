---
title: VID-70 视频笔记：01 RAG Agent 短期记忆（滑动窗口）
aliases:
  - 外部视频笔记-70
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-70 01 RAG Agent 短期记忆（滑动窗口）

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1uvT16aEBx |
| UP主 | AI_Julie |
| 时长 | 15min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写可能存在谐音错字 |

## 内容提炼
### 核心论点
1. 短期记忆（short memory）即窗口型记忆（window memory）：滑动窗口按 token 数计算，也有按 message 条数计算的；本视频主讲按 token 的实现（00:56 / 01:05 / 01:14）
2. 上下文不能占满：模型长度有限（如 GPT 约 128k），占满有两个代价——token 越多花费越贵；token 输入越多幻觉越明显，所以 chat history 必须控制长度（02:06 / 02:26 / 02:33）
3. 滑动窗口算法极简：插入新消息后若总长度超过 max token 阈值，把最老的那条 pop 掉，否则继续累积（02:39 / 03:08 / 03:14）
4. 按 token 限制有先天不稳：回复长度不可控（一轮就可能超 2k），会导致每一轮都在 pop，最终 memory 里永远只剩最新两条；UP 认为更合理的方式是按条数——保留最近 N 条消息（user 算一条、assistant 算一条，如保留最近 10 条）（13:44 / 14:02）

### 关键机制
- WindowConversationMemory class：add function（把新消息加入，含 role 和 content）→ shrink budget（先算所有 message 的总长度，大于 max token 就把最老的 pop 掉）；count token 用 tiktoken 库的 encode 计算长度（03:59 / 04:18 / 04:31）
- 运行演示一（max token=80）：几乎每一轮都在 pop，system 消息第二轮就被丢弃——「我是阿明」之后的历史被反复挤掉；窗口太小导致崩溃式刷新（07:10 / 08:12）
- 运行演示二（max token=200）：三轮对话（110→184 token）始终没超限，永远不 pop——阈值设太大则滑动窗口形同虚设（08:45 / 09:35）
- 运行演示三（max token=100）：第二轮 pop 一条、第三轮因回答变长再次 pop，历史被冲掉（10:40 / 12:30）
- 参数与业务的关系：回复长度随业务变化，token 阈值应随轮数/业务调整；否则「设置太小每轮 pop 到没东西，设置太大永不 pop」（13:24 / 14:02）
- 边界细节：最终历史应以 user 开头（user/assistant/user/assistant 交替），奇数条更合理，而不是从 assistant 开始（14:24 / 14:37）

### 可操作细节
- 参数化：max token 可按场景调（80/100/200 的演示对比）；或按条数保留最近 N 条（UP 推荐）(02:39 / 13:44)
- tiktoken 计算：tiktoken.encode(text) 后取 len（03:24 / 04:48）
- 学习建议：学代码时把 message history 每轮打印出来看 pop 了什么，比直接调 langchain 默认 prompt 更能理解（11:49 / 12:08）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 上下文越长幻觉越明显 → 必须控制长度 | 02:26 / 02:33 | 已覆盖 | 上下文腐烂 CRI（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.9） | 支撑：视频的 token-幻觉相关主张即 CRI 的经验形态 | 与 VID-73「上下文负载必须降低否则幻觉」同族 |
| 滑动窗口 pop 最老消息（system 消息被挤掉） | 07:10 / 08:12 | 张力（浅） | 身份面否决权（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；R0 常驻层（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 挑战：无差别「丢最老」会把身份/宪法级信息丢光——Kairos 以身份面否决+常驻层解决，视频的演示恰好暴露该缺陷 | 与 VID-69 滑动窗口漏洞（04:14）、VID-67 时间盲区批评同族 |
| 按条数（最近 N 轮）优于按 token 限窗 | 13:44 / 14:02 | 可吸收 | 注意力调度器 token 预算分解（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §9） | 支撑：条数制=轮数级粗粒度预算、token 制=字节级精确预算；视频主张条数制更稳，可作为 R0 窗口预算的默认参数取向 | 工程参数级增量，非机制分歧 |
| token 预算与花费/幻觉的权衡 | 02:06 / 02:33 | 已覆盖 | 注意力调度器 token 预算分解（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §9）；上下文腐烂（认知基础 §1.9） | 支撑：预算约束三动机（长度上限/成本/幻觉）与 §9 预算分解同向 | — |
| 历史以 user 开头奇数条 | 14:24 / 14:37 | 未触及 | — | 未触及：消息序格式细节，不影响机制 | — |

## 存疑与未验证
- 视频为代码演示课（deepseek client 演示），「128k 占满会幻觉」「token 越多越贵」为常识性断言，无评测数据（未验证）
- 演示过程网络中断重跑，个别轮次 token 计数为演示值（54/97/110/184 等），非通用结论（未验证）
- 「langchain 内置 system prompt 导致行为不符合预期」为 UP 个人经验（未验证）
- 转写错字：「shuriken budget」（shrink budget）、「做不掉」（pop 掉）、「tick token」（tiktoken）、「dota environment」（dotenv）、「减缩」（检索）、「阿民/阿明」等，术语以语义还原

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
