---
title: REPO-07 仓库分析：Zep（getzep/zep + getzep/graphiti）
aliases:
  - 外部仓库分析-07
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-07 Zep（getzep/zep + getzep/graphiti）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/getzep/zep（+ 支撑引擎 https://github.com/getzep/graphiti） |
| Star | 4812★（任务简报口径，2026-08-07；graphiti 未单独核对） |
| 语言/许可 | Go（legacy 社区版）+ Python（graphiti 引擎）/ Apache-2.0（zep 与 graphiti LICENSE 均 Apache-2.0） |
| 视频对应 | VID-40（提及，**无笔记入库**——notes 目录无 VID-40 文件，无法逐条对照声称） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone 超时/中断，经 gh-proxy 下载 zep 与 graphiti main 分支 tarball（均无 .git、无 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径（getzep/zep）**：README 标题即「Zep Cloud: Examples & Integrations」——「This repository is **not** Zep's product or service. It contains example code, framework integrations, and tools for building agent memory with Zep Cloud」（`README.md`）。Community Edition 已弃用，代码移入 `legacy/`（`README.md`）。官方指明：时间知识图谱框架在 **[Graphiti](https://github.com/getzep/graphiti)**（`README.md`）。

**源码实证**：仓库内 `legacy/src/`（Go 社区版）含真实记忆引擎：session/message/记忆模型 + 事实检索，但**记忆提取与检索全部委托给 Graphiti 服务**（`legacy/src/lib/graphiti/service_ce.go`）；`graphiti_core/`（独立下载）是实际的时间知识图谱实现。**核实结论：Zep 的记忆架构 = 薄会话层（Zep CE）+ 时间上下文图（Graphiti）**——图索引与时间有效性机制全部在 Graphiti 侧。

## 架构与核心机制（源码实证）

### A. Zep legacy 社区版（`legacy/src/`，Go）
1. **模型**：`Memory` = Messages + RelevantFacts + Metadata（`models/memory_common.go:86-92`）；`Fact` = UUID + CreatedAt + Fact 文本 + Rating（`models/fact_common.go:9-14`）；`Session` = SessionID + UserID + Metadata + EndedAt（`models/session_common.go:10-22`）
2. **写入**：`memoryDAO.Create`（`store/memory_common.go:93-150`）——消息入库后 `_initializeProcessingMemory` 调 `graphiti.PutMemory`（`store/memory_ce.go:59-72`，**按 session 与 user 两个 group 双写**）
3. **读取**：`memoryDAO._get`（`store/memory_ce.go:15-57`）——取最近 4 条消息（2 轮对话，`maxMessagesForFactRetrieval=4`）调 `graphiti.GetMemory`（MaxFacts=5）取相关事实；`Fact.CreatedAt` 取 `ValidAt`（事实生效时间）优先
4. **即：CE 无自有提取/图逻辑**——记忆语义层完全外置 Graphiti HTTP 服务（`lib/graphiti/service_ce.go` 定义 GetMemory/PutMemory/Search/AddNode 接口）

### B. Graphiti 时间上下文图（`graphiti_core/`，Python）
1. **三类节点 + 边**：
   - `EpisodicNode`（`nodes.py:318-360`）：**原始数据节点**（episode）——content（raw 文本）+ source 类型 + `valid_at`（原始文档创建时间）+ entity_edges 引用——**「episode = ground truth 流，一切派生事实回溯至此」**
   - `EntityNode`（`nodes.py:499+`）：实体节点，带**随演化更新的 summary**（region 摘要）+ name_embedding
   - `EntityEdge`（`edges.py:263-285`）：**事实边**——fact 文本 + fact_embedding + `valid_at`（事实开始为真的时间）/`invalid_at`（停止为真的时间）/`expired_at`（被失效的时间）/`reference_time`（产生该边的 episode 时间戳）+ **episodes 溯源列表**——「**时间有效性写进记忆结构**」的工程实证
   - `SagaNode`（`nodes.py:867`）+ `NextEpisodeEdge`/`HasEpisodeEdge`（`graphiti.py:756-779`）：episode 串成叙事链（saga）
2. **摄取管线**（`graphiti.py`）：`add_episode`（980 行）→ LLM 提取节点/边（`_extract_and_resolve_nodes`/`_extract_and_resolve_edges`，604/631 行）→ 批量去重（`dedupe_nodes_bulk`，783-812 行）→ `_process_episode_data`（680-781 行）落库 + saga 关联——**增量更新，无全量重算**
3. **双时态**：EpisodicNode.valid_at（事件时间）与 created_at（事务时间）并存；EntityEdge 四时间字段（valid/invalid/expired/reference）
4. **混合检索**（`search/`）：search_config_recipes.py——`bm25 + cosine_similarity (+ bfs 图遍历)` 多信号，RRF / MMR / cross-encoder / node_distance / episode_mentions 多重排器（COMBINED_HYBRID_SEARCH_CROSS_ENCODER 81-108 行）；`center_node_uuid` 按图距离重排；时间过滤 SearchFilters（search_filters.py:63-65 valid_at/invalid_at/expired_at 日期过滤）
5. **图存储**：Neo4j / FalkorDB / Kuzu / Neptune 四驱动（`driver/`）
6. **社区聚合**：`build_communities`（graphiti.py:1490）——实体社区层级（`CommunityNode`，nodes.py:687）

## 关键设计决策（与视频声称对照）
| 视频声称（VID-40，无笔记可逐条对照） | 源码验证结果 |
|:--|:--|
| 「Zep 的记忆架构」 | **口径更新**：getzep/zep 现为示例/集成仓库；记忆引擎在 legacy（弃用 CE）与 Graphiti（时间知识图）；Zep 产品本体是闭源云平台 |
| 「图索引」 | **一致**：Graphiti 是 Neo4j/FalkorDB 图 + 实体/事实/episode 节点边 + 图遍历（BFS）检索信号（search_config_recipes.py:81-108） |
| 「时间有效性/时间感知」 | **一致（Graphiti 侧）**：EntityEdge 四时间字段（valid_at/invalid_at/expired_at/reference_time，edges.py:271-282）+ 检索时间过滤（search_filters.py:63-65）——「把时间写进记忆结构」在 Zep 生态是真实实现 |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 事实边时间窗口（valid_at/invalid_at/expired_at 结构化失效状态） | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（时间轴：物理衰减+逻辑因果双轴，度量形态）+ 双时态声明（§1.1 债务 D-323：occurred_at/created_at） | 支撑：Kairos 时间轴是衰减度量；Graphiti 的 valid/invalid 窗口是**结构化的真值有效区间**——度量与结构互补 | 与 VID-27 ever-memos validity interval 分诊同族；三时间字段（valid/invalid/expired）比 mem0 的 expiration_date 单字段更完整 |
| episode 溯源（每条事实边回溯原始 episode + reference_time） | 已覆盖 | 见证价值轴·来源追踪（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 见证锚定主副本（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：「从哪来」可审计与 Kairos 见证锚定同题；episode 即「原始证据流」 | Graphiti 不区分见证/使用双副本——「事实边可被时间戳失效但内容不可改」与 Kairos 差异检验仍有别 |
| saga 叙事链（episode 串成 NEXT_EPISODE/HAS_EPISODE 链） | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（逻辑-因果轴：事件时序/叙事连贯性）+ 见证价值轴·叙事自洽度（§1.1） | 支撑：对话序列作为结构线索（链状拓扑）与叙事自洽度同向 | 与 REPO-04 MemoryOS 对话链指针分诊同类（见 [REPO-04-memoryos.md](REPO-04-memoryos.md)） |
| 实体 summary 随演化更新（EntityNode.summary 区域摘要） | 可吸收 | 升华管道 raw→item→strategy→behavior（[认知基础](../../../foundation/cognitive-foundation.md) §A.3）；反熵注入器（[架构](../../../foundation/architecture-v0.1.0.md) §10.19） | 支撑：实体级增量摘要 = 碎片→稳定结构的一种粒度 | 增量：以实体为中心的摘要聚合与 Kairos 反熵注入的对照点 |
| community 社区聚合（build_communities） | 可吸收 | 认知完整性轴·组合约束网络连通性（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）；知识加工区（[架构](../../../foundation/architecture-v0.1.0.md) §5.10） | 支撑：主题社区是长期碎片化的结构化缓解 | 增量：图社区检测（Louvain 类）作为主题化组织形态 |
| BFS 图遍历检索信号 + 节点距离重排 | 已覆盖 | 三信号混合检索（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a，图谱距离为可选第七信号）+ 实体知识图谱（§5.2） | 支撑：Kairos 已登记图谱距离扩展信号，Graphiti 是「图谱距离为主信号」的实证 | Kairos 保持图谱距离为可选（默认关闭）的取向不变 |
| 双时态（valid_at 事件时间 + created_at 事务时间） | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1 双时态声明（债务 D-323，occurred_at/created_at） | 支撑：Graphiti 是双时态的工程实证（EpisodicNode.valid_at/created_at） | 外部印证 Kairos 双时态选型 |
| 增量摄取不重算（add_episode 增量更新） | 已覆盖 | ADD-only 提取协议（[架构](../../../foundation/architecture-v0.1.0.md) §7.3g） | 支撑：增量式更新是两者共同取向（Graphiti 是图侧增量，Kairos 是记录侧增量） | 差异：Graphiti 可对事实边置 invalid_at（结构化失效），Kairos 不覆盖（ADD-only 叠加 + 差异检验裁决） |
| Zep CE 按 user 与 session 双 group 双写（PutMemory 双写） | 可吸收 | 分域真理路由（[认知基础](../../../foundation/cognitive-foundation.md) §C.6）+ 路径空间硬过滤（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：同一消息写入多作用域（user 级 vs session 级）是作用域路由的工程形态 | 增量：消息级多作用域物化（memory_ce.go:59-72）与 Kairos 路径过滤语义的对照 |

## 可吸收增量（具体到机制/参数/接口）
1. **事实边三时间字段**（`graphiti_core/edges.py:271-282`）：`valid_at`（开始为真）/`invalid_at`（停止为真）/`expired_at`（被失效）+ `reference_time`（产生它的 episode 时间）——结构化的真值有效区间，比 Kairos 当前「时间轴为度量」更接近「时间写进结构」；可与 VID-27 validity interval（[笔记](../notes/VID-27-BV1H8VQ6DEBB.md)）合并分诊为同一增量
2. **episode 溯源边**（`nodes.py:325-328` entity_edges + edges.py:267-270 episodes 列表）：每个派生事实携带原始 episode 引用——「从哪来」可回溯的实现细节（Kairos 见证锚定的关系层注记）
3. **saga 序列组织**（`graphiti.py:738-779`）：episode 间 NEXT_EPISODE 边 + saga 节点记录 first/last episode——对话/事件序列的显式拓扑（逻辑-因果轴的图落点）
4. **实体 summary 增量演化 + community 聚合**（`nodes.py:499-504`；`graphiti.py:1490`）：以实体为中心的摘要更新与社区构建——反熵注入器（§10.19）的主题化形态参考
5. **图搜索时间过滤**（`search/search_filters.py:63-65`）：按 valid_at/invalid_at/expired_at 日期区间过滤事实——「以事实有效期为检索硬过滤」的工程形态（Kairos 时间过滤 §7.3a 同为硬过滤，可对比实现）

## 存疑与未验证
- **VID-40 无笔记入库**（notes 目录不存在 VID-40 文件），本笔记无法逐条对照视频声称——仅核实了任务简报提及的「记忆架构与图索引」两点
- Zep Cloud 产品本体为闭源，本笔记仅覆盖 OSS 部分（legacy CE + Graphiti）；平台侧时间推理等能力未验证
- Graphiti 的 LLM 提取/去重/摘要质量依赖提示词（`graphiti_core/prompts/`），未运行验证（未执行）
- legacy CE 的 `MaxFacts=5`、`maxMessagesForFactRetrieval=4` 为代码常量（memory_ce.go:13, 34），行为未运行验证（未执行）
- Graphiti 版本与 star 数未单独核对；两仓库均无 commit SHA（素材限制）
- 「Zep CE 不再支持」与产品转向闭源云平台——开源社区版路线终止的时效性信息（`README.md`）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
