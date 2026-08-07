---
title: REPO-13 仓库分析：OpenMemory（CaviraOSS/OpenMemory）
aliases:
  - 外部仓库分析-13
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-13 OpenMemory（CaviraOSS/OpenMemory）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/CaviraOSS/OpenMemory |
| Star | 4414★（任务简报口径，2026-08-07，未独立核对） |
| 语言/许可 | TypeScript（Node 引擎 + 服务器）+ Python（SDK）/ Apache-2.0 |
| 视频对应 | 无（补充发现批次） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone --depth 1（成功；HEAD 9fdfc2a，未记录完整 SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：OpenMemory 是「Real long-term memory for AI agents. **Not RAG. Not a vector DB.** Self-hosted, Python + Node」——「cognitive memory engine for LLMs and agents」（`README.md`），宣称可解释轨迹（Explainable traces，看*为什么*被召回）。**⚠️ 状态警告：README 顶部「🚧 This project is currently being rewritten. Expect breaking changes」**（`README.md`）——重写中，API 可能破坏。

**源码实证**：核心在 `packages/openmemory-js/src/`：`memory/hsg.ts`（1354 行，分层扇区图 HSG 引擎）+ `memory/decay.ts`（衰减与压缩）+ `memory/reflect.ts`（反射巩固）+ `temporal_graph/`（时序事实模块）+ `core/db.ts`（SQLite）+ `core/vector/`（valkey/postgres 向量）。Python 包（`packages/openmemory-py/`）为薄客户端 + OpenAI 兼容封装。**「Not RAG」口径部分成立**：HSG 多扇区嵌入 + 路点图 + 衰减 + 反射，确非简单向量检索；但核心仍是「嵌入相似度 + 元信号打分」的向量检索增强，且**衰减/反射/路点等认知机制多为启发式（正则分类、Jaccard 聚类、指数衰减）而非认知模型**。

## 架构与核心机制（源码实证）

### A. 五扇区记忆模型（`memory/hsg.ts:50-120`）
`episodic / semantic / procedural / emotional / reflective` 五类，各带：
- `decay_lambda`（衰减率）：episodic 0.015 / semantic 0.005 / procedural 0.008 / emotional 0.020 / reflective 0.001（`ARCHITECTURE.md`）
- `weight`（扇区权重）：1.2 / 1.0 / 1.1 / 1.3 / 0.8
- `patterns`：**正则模式分类器**（中英双语，如 episodic 匹配「remember when/today/去了/看到」）——内容分类完全正则启发式，无 LLM

### B. 多扇区嵌入 + 平均向量（`ARCHITECTURE.md`「Add Memory Flow」）
内容 → 正则分类（primary + additional 扇区）→ **每扇区独立嵌入**（multi-sector embeddings）→ 计算全部扇区向量的**均值向量**（waypoint 图用）→ 存储记忆节点 + 多扇区向量。>512 token 长文本：512 token 重叠分块（50 重叠）→ 逐块嵌入 → 均值池化聚合。

### C. 衰减系统（`memory/decay.ts`，decay-2.0）
- 核心公式：`salience' = salience × e^(-lambda × days)`（`ARCHITECTURE.md`；decay.ts:288 实际为 `sal * exp(-lam * (dt / (sal + 0.1)))`——**salience 参与衰减速率调节**：高 salience 记忆衰减更慢）
- **hot/warm/cold 分层**（decay.ts:88-95）：最近 6 天 +（coactivations>5 或 salience>0.7）→ hot；最近或 salience>0.4 → warm；否则 cold；各层不同 lambda（hot 0.005 / warm 0.02 / cold 0.05，decay.ts:74-76）
- **冷记忆压缩**（decay.ts:293-341）：`f < 0.7` 时压缩向量（降维均值池化，min 64 维）+ 压缩摘要（`compress_summary`：200 字截断 → 摘要 → 关键词三级，decay.ts:118-129）
- **冷记忆指纹化**（decay.ts:344-360）：`f < 0.25`（cold_threshold）时向量替换为**哈希指纹向量**（`hash_to_vec` FNV-1a 哈希，32 维）+ 摘要替换为 3 关键词——**深度冻结：语义细节丢失、仅保留可识别指纹**
- 查询命中强化（`on_query_hit`，decay.ts:388-435）：`salience + 0.5`（reinforce_on_query）+ 可选向量再嵌入再生（regeneration：仅 ≤64 维指纹向量重新嵌入恢复语义）——**「被使用时复活」机制**
- 24h 调度（`ARCHITECTURE.md`「Scheduled decay process every 24 hours」）；有 active_query 互斥（decay.ts:83-84, 226-229）

### D. 单路点图（`ARCHITECTURE.md`「Waypoint Graph」）
- add 时找**单个最佳匹配**（cosine > 0.75）建一条有向链接（跨扇区则双向）
- 查询时 1-hop 图遍历扩展（expandViaWaypoints）
- 强化：查询遍历 +0.05/次，上限 1.0；**7 天剪枝**：weight < 0.05 移除
- 查询评分（`ARCHITECTURE.md`:157）：`composite = 0.6×similarity + 0.2×salience + 0.1×recency + 0.1×waypoint`——新版 hsg.ts 已升级为更复杂的混合评分（`compute_hybrid_score` + token overlap + keyword boost + tag match + project boost，hsg.ts:985-1005，含 z-score 归一化与 sigmoid logit 提升）

### E. 反射巩固（`memory/reflect.ts`）
`cluster()`：Jaccard token 相似度 > 0.8 聚类同扇区记忆（排除 reflective 与已巩固）→ 每簇 ≥2 条 → 提炼新记忆（`sal(c)` 按簇大小/时间评分）——**无 LLM 的启发式巩固**（相似记忆合并为一条新记忆）

### F. 时序事实模块（`temporal_graph/`，types.ts + store.ts + query.ts + timeline.ts）
**重要新发现**：`TemporalFact`（types.ts:1-13）：subject/predicate/object + **`valid_from` / `valid_to`（有效窗口，null=当前有效）** + `confidence` + `last_updated`。`insert_fact`（store.ts:67-130）：插入新事实时自动关闭同一 (subject, predicate) 的旧有效事实——`UPDATE temporal_facts SET valid_to = valid_from_ts - 1`（store.ts:96-104）——**「新事实取代旧事实、旧事实保留历史」的结构化失效**（与 Graphiti invalid_at 同族，但更简单：无事件时间/事务时间区分，直接用插入时间）。查询：`query_facts_at_time`（某时刻的事实状态）、`query_facts_in_range`、`find_conflicting_facts`（冲突事实检测）、`get_facts_by_subject`、`search_facts`、`get_related_facts`、`timeline.ts`（时间线事件流：created/updated/invalidated 变更类型，types.ts:26-33）

### G. 其他
- 反馈评分：查询命中后 `feedback_score = old × 0.9 + score × 0.1`（hsg.ts:1027-1029，移动平均）
- 共激活：top 结果两两组合记录 co-activation 对（hsg.ts:1031-1035）——支持衰减分层的「hot」判定
- 存储：SQLite（默认，memories/vectors/waypoints/embed_logs 表）+ Postgres + valkey 向量缓存；`segments` 分段衰减（decay.ts:247-250）
- 集成：LangChain/CrewAI/AutoGen/MCP/VS Code 扩展 + GitHub/Notion/Drive 连接器（README「Integrations/Sources」）

## 关键设计决策（README 口径 vs 源码实证对照）
| README 声称 | 源码验证结果 |
|:--|:--|
| 「Not RAG. Not a vector DB」 | **部分一致**：确有向量检索之上的认知机制（五扇区/衰减/路点/反射/时序事实）；但核心检索仍是「嵌入相似度 + 元信号」打分，且扇区分类为纯正则启发式——「认知」定位高于实际复杂度 |
| 「Explainable traces (see *why* something was recalled)」 | **未证实**：README 声称可解释轨迹；源码未见对应召回原因的结构化输出（hsg.ts 返回 score/sectors/path 字段，path 为路点路径——部分支撑） |
| 「Hierarchical Memory Decomposition (HMD) v2」 | **一致（命名）**：`ARCHITECTURE.md` 定义 HMD v2 = 多扇区嵌入 + 单路点图链接；「hierarchical」体现为扇区×衰减×路点的层级而非真实树/层级结构 |
| 衰减「Episodic fastest (0.020), Reflective slowest (0.001)」 | **一致**：hsg.ts:50-120 配置与 `ARCHITECTURE.md` 完全对应 |
| 「Real long-term memory」 | **部分一致**：衰减 + 压缩 + 指纹化 + 再生（被使用复活）是真实遗忘/巩固机制的启发式实现——是本批仓库中唯一有「遗忘」形态的系统 |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 指数衰减 + 分层衰减速率（hot/warm/cold 不同 lambda） | 可吸收 | 时间轴·物理衰减（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）；单曲线指数衰减遗忘（[架构](../../../foundation/architecture-v0.1.0.md) §5 核心） | 支撑：Kairos 已有单曲线指数衰减；OpenMemory 的**分层衰减**（hot/warm/cold）与「salience 调节衰减速率」（decay.ts:286 `lam * (dt/(sal+0.1))`）是超参形态增量 | 增量：分层衰减 + 使用率参与衰减速率调节——但需对照 Kairos「探索预算独立、频率≠价值」原则审查（coactivations 直接推高 salience 是使用信号渗入价值评估，与价值独立性公理有张力） |
| 冷记忆压缩 + 指纹化（f<0.7 降维压缩、f<0.25 哈希指纹） | 可吸收 | 三硬一软·可审计压缩（认知基础 §2.2）；遗忘调度器（[架构](../../../foundation/architecture-v0.1.0.md) §5） | 支撑：分级压缩（截断→摘要→关键词→指纹）是「可审计压缩」的工程实证；指纹化 ≈ 深度遗忘（保留可识别性、丢弃语义） | 增量：多级压缩退化的具体参数（0.7/0.25 阈值、64 维下限）；Kairos 可对照设计「压缩=审计保留」分级 |
| 被使用复活（on_query_hit 再嵌入再生 ≤64 维指纹向量） | 张力 | 价值独立性公理（认知基础 §2.1「好用 ≠ 真实」）+ 双副本隔离防线（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | **张力**：OpenMemory 的「被检索→salience+0.5 强化 + 向量再生」是使用信号直接改写记忆内容（指纹→再嵌入恢复语义）——与 Kairos「使用权重影子副本永不反向写见证锚定主副本」**直接冲突**；再嵌入以摘要（已压缩/失真）为输入，等于用使用事件改变记忆的语义内容 | 这是本批最值得记入张力清单的机制：OpenMemory 以「使用强化」换取可用性，Kairos 以「双副本隔离」换取真实性 |
| 五扇区模型 + 扇区正则分类（episodic/semantic/procedural/emotional/reflective） | 已覆盖 | 记忆类型（[认知基础](../../../foundation/cognitive-foundation.md) §1.2 三种检索配置模式）+ 升华管道（§1.10） | 支撑：扇区分类与 Kairos 记忆类型划分同题；OpenMemory 用正则启发式（零成本），Kairos 用结构性分类 | 可对照：正则分类器的工程边界（无法处理隐含语义）；Kairos 明确不采用纯正则分类 |
| 单路点图（add 时单边链接 + 1-hop 扩展 + 7 天剪枝） | 可吸收 | 实体知识图谱（[架构](../../../foundation/architecture-v0.1.0.md) §5.2）+ 三信号·图谱距离（§7.3a） | 支撑：单路点 = 极简关联结构（每记忆一条最强关联），是图谱距离信号的轻量形态 | 增量：单边链接 + 权重剪枝阈值（0.75 建链 / 0.05 剪枝 / 0.05 强化步长）的具体参数；与 REPO-04 MemoryOS 对话链指针分诊可对照 |
| 时序事实 valid_from/valid_to 自动关闭旧事实（insert_fact） | 可吸收 | 时间轴·逻辑因果（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）；双时态声明（债务 D-323） | 支撑：与 Graphiti invalid_at 同族的结构化失效；无事件/事务时间区分（用插入时间），比 Graphiti 更简但**缺 occurred_at 语义** | 与 [REPO-07 zep](REPO-07-zep.md) / [REPO-12-graphiti](REPO-12-graphiti.md) 分诊合并：三实现（Graphiti 四字段 / OpenMemory 双字段 / mem0 单字段）构成「结构化失效」谱系 |
| 查询命中反馈移动平均（feedback_score = 0.9×old + 0.1×score） | 可吸收 | 使用价值轴（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 差异检验（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：检索命中质量的指数移动平均是使用信号平滑的简单形态 | 注意：OpenMemory 将其写回记忆行（记忆元数据），Kairos 规定使用信号只进影子副本 |
| 反射巩固（Jaccard>0.8 同扇区聚类 → 提炼新记忆） | 已覆盖 | 升华管道（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）+ 知识加工区（[架构](../../../foundation/architecture-v0.1.0.md) §5.10） | 支撑：巩固的启发式形态（无 LLM）；聚类阈值 0.8 的保守性可对照 Kairos 合并判定 | 与 [REPO-06-letta.md](REPO-06-letta.md) 等巩固机制分诊同族 |

## 可吸收增量（具体到机制/参数/接口）
1. **冷记忆多级压缩退化**（`memory/decay.ts:293-360`）：`f<0.7` 向量降维 + 摘要压缩（200字→摘要→关键词三级）；`f<0.25` 哈希指纹化（32 维 FNV-1a）——Kairos「可审计压缩」（认知基础 §2.2）的分级退化工程参数参考（阈值 0.7/0.25、维度下限 64、摘要层级 3）
2. **时序事实自动失效**（`temporal_graph/store.ts:96-104`）：插入新事实时 `valid_to = 新时间-1` 关闭旧事实——结构化失效的最简实现（单表 + 一次 UPDATE），与 Graphiti 四字段（[REPO-12-graphiti](REPO-12-graphiti.md) 增量 2）构成复杂度谱系两端
3. **分层衰减（hot/warm/cold）+ salience 参与衰减速率**（`memory/decay.ts:88-95, 286`）：`lambda_hot 0.005 / warm 0.02 / cold 0.05` + `dt/(sal+0.1)` 速率调节——Kairos 单曲线指数衰减的分层扩展候选（需先审查与价值独立性公理的关系）
4. **查询命中反馈 EMA**（`memory/hsg.ts:1027-1029`）：`feedback = 0.9×old + 0.1×score`——使用信号平滑的简单形态（Kairos 影子副本内可对照）
5. **路点图单边链接 + 剪枝参数**（`ARCHITECTURE.md`）：建链阈值 0.75、强化 0.05/次、上限 1.0、剪枝 <0.05/7 天——轻量关联结构的完整参数集

## 存疑与未验证
- **项目重写中**（`README.md`「currently being rewritten」）——分析基于当前 main 分支，重写分支（rewrite）可能改变全部机制；任务简报 star 数 4414 与仓库现状需核对
- 「Explainable traces」声称未在源码中找到对应实现（仅 score/sectors/path 部分支撑）——存疑
- 衰减调度（24h）与路点剪枝（7d）的调度器实现细节未深读（`ARCHITECTURE.md` 声称 vs 代码调度入口未完全对齐）
- 反射巩固（reflect.ts）的提炼 LLM 调用（若有）未核实——`sal(c)` 评分函数未读全
- 向量后端 valkey/postgres 与 SQLite 的同步一致性未验证
- 中文正则模式仅覆盖部分扇区（episodic/semantic/procedural/emotional 有中文，reflective 未确认）——多语言覆盖不完整

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
