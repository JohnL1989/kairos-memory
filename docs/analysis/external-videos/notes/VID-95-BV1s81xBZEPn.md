---
title: VID-95 视频笔记：NeurIPS 2025 Agentic Plan Caching（APC 计划缓存）
aliases:
  - 外部视频笔记-95
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-95 NeurIPS 2025 Agentic Plan Caching（APC）

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1s81xBZEPn |
| UP主 | iHang的科研笔记 |
| 时长 | 20min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写存在大量同音错字（「tation」应为「planning/agentic」，「语异」应为「语义」，「kword」应为「keyword」，「hate/cache hate」应为「hit/cache hit」，「inviting/invasion」应为「embedding」，「flank action」应为「plan action」，「拉驰篮软织模头」应为「large language model」，「Gone Hermes」等为环境噪声）；论文名「APC」为转写缩写，全名未完整给出 |

## 内容提炼
### 核心论点
1. 问题：agent 循环频繁调用 LLM API（或频繁跑模型），消耗算力/金钱；若有冗余或可复用的操作，可缓存下来，后续相似问题直接从缓存提取而不用重新计算（00:00-01:03）。
2. 两种主流缓存方法及局限：(a) context caching（KV cache）——缓存每次输入中不变的前缀（prompt/context），但高度绑定模型架构无法跨模型迁移，且必须完全匹配（前面一个字符不同就整个失效）；(b) 语义缓存（input-output pair）——只适合问答机器人场景，agent 场景下相似 query 可能完全不同的任务（"帮我分析这个数据集"对不同数据集方法完全不同；"帮我讲解这篇文章"对不同文章任务不同；现实世界取物任务取不同东西策略完全不同），无法泛化（02:21-06:22）。
3. APC 方法（Agentic Plan Caching）：小模型从 query 提取 keyword → 去 cache 匹配 → hit：把存储的 plan template（解决这类问题的通用方法模板）给一个小模型作为 plan model，小模型参考模板生成 plan 并走 ReAct 执行（省去大模型调用）；miss：正常大模型 ReAct/Plan-and-Execute 流程，完成后用另一个小模型提取 keyword+plan template 存入 cache（06:40-09:53）。
4. 为什么用 keyword 而不是直接拿 query 匹配：query 精确匹配命中率低且不够抽象；query 语义相似度匹配（embedding）有大量 false positive/negative、阈值难调，且实体词主导相似度——"特朗普在任上干了什么事"与"拜登在任上干了什么事"关键词应是"某人在任上干了什么事"（任务本体），embedding 却会把特朗普/拜登的人名权重加得极高导致匹配到一堆人名相关而非任务相关的内容（10:23-13:34）。
5. 为什么精确匹配而非模糊匹配：模糊匹配同样要调阈值（阈值设计复杂），且 cache 内容多时引入额外计算量，违背节省计算量的初衷（13:45-14:54）。
6. 为什么只缓存 plan template 而不缓存完整执行历史：实验发现小模型处理非常长的完整执行上下文能力有限，反而提供简短简洁的模板能更好地规划（14:55-15:55）。
7. 效果：省约一半 cost 的同时保持 90% 以上准确率（对比全大模型=准确率/成本上限、全小模型=成本下限）；hit 与 miss 准确率接近（此前语义缓存方法 hit 时准确率反而下降）；warm start 分析：前 20% 的 query 消耗占总成本约 32%（cache 空、命中率低），越往后成本增长越平缓（80%~100% 只增约 12%）；若能离线 warmup（预先用类似问题把 cache 填起来），可进一步降成本降延迟（16:01-20:37）。

### 关键机制
- cache hit 路径：query→小模型提取 keyword→cache 精确匹配→取出 plan template→小模型（作为 plan model）参考模板生成 plan→执行 ReAct 迭代（08:47-09:53）。
- cache miss 路径：query→大模型规划+执行→结果→小模型提取 keyword+plan template→写入 cache（07:45-08:45）。
- keyword 的意义：比 query 更抽象、更能提取关键内容；query 里实体性词会占更大权重干扰匹配（12:19-13:34）。

### 可操作细节
- 缓存单元：keyword → plan template 键值对（08:19-08:45）。
- 匹配方式：keyword 完全一致才算 cache hit（13:45-13:59）。
- warmup 策略：离线预先用类似问题填充 cache（20:05-20:37）。
- 成本曲线数据：前 20% query 消耗约 32% 总成本；80%~100% 只增加约 12%（19:07-19:48）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 缓存"解决一类问题的通用方法模板"而非完整执行历史 | 14:55-15:55 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.10（三级知识生产管道：strategy→behavior 层）+ [架构](../../../foundation/architecture-v0.1.0.md) §3（策略层） | 支撑：plan template=strategy 层记忆的工程形态；「完整历史太长小模型处理不了、模板更好」=Kairos 升华管道压缩固化的同一动机（原始层 vs 升华层） | 强印证 |
| 缓存按"任务类型"（keyword）而非表面相似度检索 | 10:23-13:34 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §2.6.1（QueryAnalyzer 查询理解层）+ §7.3f（spaCy 轻量实体提取） | 支撑：任务本体 vs 实体词干扰的发现，提示检索特征应区分"任务类型维度"与"实体维度"；Kairos 查询理解层可吸收任务类型提取 | 可入 QueryAnalyzer 设计参考 |
| 语义缓存的 false positive/negative 与阈值难题 | 03:15-06:22，11:22-13:34 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a（三信号混合检索）+ §3.9（检索深度分级） | 支撑：单靠语义相似度检索不可靠=Kairos 用三信号混合+分级检索的动机；APC 用精确匹配+抽象关键词规避，Kairos 用信号混合+深度分级规避 | 两种工程策略可对照 |
| 计划缓存复用=agent 间经验共享/自我进化 | 00:32-01:03，17:48-18:09 | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §2.2（探索预算独立：探索投资）+ [架构](../../../foundation/architecture-v0.1.0.md) §3.5（检索预取策略） | 支撑：缓存命中率随使用上升=「越用越省」；Kairos 探索预算独立可吸收"离线 warmup 填缓存"作为探索投资形式 | warmup 与探索预算的预算来源需界定 |
| 近似匹配需调阈值→精确匹配零参数 | 13:45-14:54 | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.7（确定性状态：精确检索的确定性锚点） | 支撑：阈值参数即不确定性来源；Kairos 确定性事实归档（DFA）以精确查询提供零参数路径，与 APC 精确匹配同哲学 | — |
| hit 与 miss 准确率接近（缓存复用不降质） | 17:27-18:09 | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.10（验证确认阶段）+ [架构](../../../foundation/architecture-v0.1.0.md) §5.5（差异检验） | 支撑：缓存复用不降质=可验证的复用标准；Kairos 可审计压缩的验收判据可参照（压缩产物与原文等价性） | — |

## 存疑与未验证
- 论文正式名称、作者、实验基准（数据集/模型规模）视频未给出完整信息，仅以图表带过，无法独立核对（未验证）。
- 「省一半 cost 保持 90% 准确率」「前 20% query 占 32% 成本」等数值为视频转述论文图表，未核对原文数据（未验证）。
- 「warm start/warmup 实验」细节（warmup 用多少样例、来自哪里）未展开（未验证）。
- 视频末尾「Gone Hermes」等为环境噪声/串音，非论文内容（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
