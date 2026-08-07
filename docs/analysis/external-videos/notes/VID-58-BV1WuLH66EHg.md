---
title: VID-58 视频笔记：ICLR26 RF-Mem-熟悉度驱动的快慢双路径记忆检索
aliases:
  - 外部视频笔记-58
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-58 ICLR26 RF-Mem-熟悉度驱动的快慢双路径记忆检索

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1WuLH66EHg |
| UP主 | Agent智能体深度研究院 |
| 时长 | 9min（1P） |
| 字幕来源 | B站 AI 字幕（ai-zh），抓取于 2026-08-07，内容与主题匹配度已人工核验 |
| 素材边界声明 | 完整覆盖视频全程；AI 字幕存在音译错字（「RFMM」=RF-Mem、「persona man」=PersonaMem、「MANGAS」=系列前作记忆系统名、「CENTRIDE」=centroid 等），已按语境转述 |

## 内容提炼
### 核心论点
1. 用户记忆检索不应只有一次性 top-k：熟悉的问题走快速 familiarity 路径，不熟悉或不确定的问题才启动慢速 recollection 路径，在嵌入空间逐步重构证据（00:24-00:38）
2. 论文从认知科学借「recollection-familiarity 双加工理论」：familiarity 是快速熟悉感（看到一张脸立刻觉得认识），recollection 是更慢的情境回忆（把时间地点来源和相关片段重新拼起来）——两种模式映射到检索器（01:07-01:31）
3. 传统一次性相似度 top-k 基本对应 familiarity：快、便宜，但容易只抓表层相似——如问题含「医疗决策」，可能命中几条看起来健康相关的碎片，却漏掉用户长期强调的偏好、循证常规医学和安全性等更完整的背景（01:31-01:49）
4. 路由信号是「把不确定性变成路由信号」：探针检索后算平均相似度 + list entropy（候选集中度），平均相似度高直接快取、低走慢回忆、中间区域熵低快取/熵高慢回忆（01:50-02:28）
5. RF-Mem 的价值不是用巨大额外成本换大幅分数，而是做取舍：多数情况下保持接近 one-shot 的延迟，同时在复杂查询上补足召回——「长期记忆系统的关键不只是记得多，而是在合适问题上用合适深度把记忆唤起来」（06:23-06:45 / 08:57-09:01）

### 关键机制
- 第一步 probe retrieval（探针检索）：用原始问题做一次快速检索，拿候选记忆与相似度分数，计算两个信号——平均相似度（整体有多匹配）与 list entropy（候选结果是否集中）（01:50-02:09）
- 快路径场景示例：问「我之前说过自己常用哪种笔记工具」，历史有明确匹配，top-k 就够（02:29-02:45）
- 慢路径场景示例：问「总结上个月讨论过的技术方案优缺点」，线索分散在多段历史里，表层相似不一定最强，recollection 围绕初步候选继续扩展证据链（02:51-03:07）
- 慢路径在 embedding 空间迭代而非让大模型慢慢想：每轮检索 top-n 候选 → k-means 聚成几簇 → 每个簇的 centroid 代表一个语义方向 → 把当前 query、centroid 和原始 query 残差信息混合生成新的 recollect query（03:16-03:35）
- alpha mix 控制查询稳定性与探索性的平衡：太靠近原始 query 扩不出去，太靠近 centroid 可能飘到无关方向；论文附录敏感性分析显示中等 alpha 往往更稳（03:36-03:50）
- 回忆受显式限制防失控：beam width 控制每轮保留分支数、fan-out 控制每分支扩多少候选、maximum rounds 控制最多走几轮（04:04-04:12）

### 可操作细节
- 主实验参数：B=3（beam width）、F=2（fan-out），并设置上下阈值控制快慢切换（04:12-04:19）
- 实验数据：PersonaMem 上三规模（32K/128K/eM）RF-Mem 全部最高——32K overall accuracy 0.6350，高于 full context 的 0.6129 与 dense retrieval 的 0.5908（05:08-05:30）
- 延迟可控：PersonaMem 32K 下 RF-Mem 检索 5.09ms vs recollection-only 7.09ms；128K 下 4.27ms vs 7.86ms（05:33-05:52）
- 可插拔性：可叠加在 memory bank 这类离线摘要索引上、可接在 HyDE 查询扩展后面、可作为 Search-1 迭代检索中的 retrieval layer——「不是替代所有记忆系统，而是给检索层加一个双路径控制器」（06:45-07:10）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 快慢双路径检索（熟悉快查/陌生慢回忆） | 00:24 | 已覆盖 | 检索深度分级 R0/R1/R2（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：双路径与深度分级同构；RF-Mem 补的是「触发条件」侧 | Kairos 触发靠任务复杂度标记+CRI 降级，RF-Mem 靠候选集信号 |
| 探针检索后以平均相似度+候选集中度（list entropy）做路由信号 | 01:50 | 可吸收 | 检索深度分级触发条件为编译器任务复杂度标记、CRI 驱动降级（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.9） | 支撑：候选集熵是 Kairos 未建模的检索控制信号，可作为 R 级选择的补充信号 | 增量：v1.1 检索参数化批次可评估 |
| 「不确定再花预算」：把不确定性前置到检索控制 | 04:39 / 07:35 | 可吸收 | PM 降级路径与策略层路由（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §3.6 / §3.4） | 支撑：预算按需分配与 Kairos 注意力调度理念一致 | — |
| 表层相似漏掉长尾重要背景（医疗决策例子） | 01:31 | 已覆盖 | 帕累托不可支配前置过滤，禁止单标量聚合（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1 辞典式排序两段链） | 支撑：Kairos 用帕累托前沿防单维坍缩，RF-Mem 用多轮重构防表层相似——同向不同机制 | — |
| 慢路径 embedding 空间聚类迭代（k-means+query 残差混合） | 03:16 | 可吸收 | Kairos 无查询重构机制（检索预处理与结果治理在元认知层，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §2.6） | 未触及：查询迭代式重构是检索预处理新能力 | 与 R2 全面检索执行路径可互补 |
| 检索越强越要防敏感信息被带回、防过度画像 | 08:18-08:39 | 已覆盖 | 19 条安全红线 S-01~S-19（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §8） | 支撑：检索增强必须配治理约束，与宪法主权面一致 | 论文伦理提醒印证 Kairos 红线必要性 |
| 检索器「稳定轻量可插拔」定位（不碾压单指标） | 06:45 / 06:23 | 未触及 | Kairos 无外部检索器集成协议 | 未触及：工程集成形态问题 | 实现期参考 |

## 存疑与未验证
- 论文标题《Evoking User Memory: Personalizing LLMs via Recollection, Familiarity, and Adaptive Retrieval》及 ICLR 2026 poster、作者机构（大连理工/香港城市/华为/中科大）均为字幕转述（未验证）
- 系列前作记忆系统名字幕音译不一（「magus/MANGAS/mamas」），无法确认实际名称（未验证）
- 各项数据（0.6350、5.09ms、B=3/F=2、α 敏感性）为 UP 主转述论文，未核对原文（未验证）
- 「list entropy 只是轻量代理，不能完全理解任务难度和用户意图」为 UP 主引论文的边界陈述（08:01-08:07）（未验证）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
