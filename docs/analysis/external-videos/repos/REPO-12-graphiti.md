---
title: REPO-12 仓库分析：Graphiti（getzep/graphiti）
aliases:
  - 外部仓库分析-12
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-12 Graphiti（getzep/graphiti）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/getzep/graphiti |
| Star | 29648★（任务简报口径，2026-08-07，未独立核对） |
| 语言/许可 | Python / Apache-2.0 |
| 视频对应 | 无（补充发现批次；[REPO-07 zep](REPO-07-zep.md) 已核实其作为 Zep 时间图引擎的事实边四时间字段，本笔记独立深读完整架构） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone --depth 1（成功，有 .git；未记录 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：Graphiti 是「Build Temporal Context Graphs for AI Agents」框架——「Unlike static knowledge graphs, Graphiti's context graphs track how facts change over time, maintain provenance to source data, and support both prescribed and learned ontology」；「supports incremental data updates, efficient retrieval, and precise historical queries without requiring complete graph recomputation」（`README.md`）。自称比 GraphRAG 强在：增量更新 vs 批处理、显式双时态 + 自动事实失效、混合检索 sub-second 延迟。

**源码实证**：核心类 `Graphiti`（`graphiti_core/graphiti.py`，1793 行）实现 `add_episode`（980 行）→ LLM 提取 → 去重 → 落库 + saga 关联的**增量摄取**；`EntityEdge` 四时间字段（`edges.py:271-282`）；`EpisodicNode` 双时态（`nodes.py:318-360`）；`build_communities` 社区聚合（graphiti.py:1490）；`search_()` 混合检索（`search/search.py` 874 行 + `search_config_recipes.py` 223 行）。**定位与口径一致：时间知识图谱引擎**。与 Zep 的关系（README「Zep vs Graphiti」表）：Zep 是闭源托管平台（专有 Context Graph Engine），Graphiti 是开源自托管引擎——REPO-07 的「Zep CE 弃用」结论在此得到架构侧确认。

## 架构与核心机制（源码实证）

### A. 数据模型（`nodes.py` / `edges.py`）
1. **EpisodicNode**（`nodes.py:318-360`）：原始数据节点——`content`（raw 文本）+ `source`（EpisodeType：message/document 等）+ **`valid_at`（事件时间：原始文档创建时间）** + `created_at`（继承自 Node，事务时间）+ `entity_edges`（该 episode 引用的边列表）+ `episode_metadata`（自定义过滤元数据）——**「episode = ground truth 流，一切派生事实回溯至此」的双时态实证**
2. **EntityNode**（`nodes.py:499-504`）：实体节点——`name_embedding`（名称嵌入）+ **`summary`（「regional summary of surrounding edges」随演化更新的区域摘要）** + `attributes`
3. **EntityEdge**（`edges.py:263-285`）：事实边——`fact` 文本 + `fact_embedding` + **`valid_at`（开始为真）/`invalid_at`（停止为真）/`expired_at`（被失效时间）/`reference_time`（产生该边的 episode 时间）** + `episodes` 溯源列表——「时间有效性写进记忆结构」的完整工程形态（REPO-07 已核实，本笔记确认无变化）
4. **SagaNode**（`nodes.py:867` 附近）+ **NextEpisodeEdge / HasEpisodeEdge**（graphiti.py:756-779）：episode 串成叙事链——`NEXT_EPISODE` 连接相邻 episode，`HAS_EPISODE` 连接 saga↔episode；saga 节点记录 `first_episode_uuid` / `last_episode_uuid`（graphiti.py:771-776）
5. **CommunityNode / CommunityEdge**：社区聚合（build_communities 输出，graphiti.py:1490-1517）

### B. 摄取管线：`add_episode`（graphiti.py:980-1062，注释自述 1793 行的主流程）
1. `_extract_and_resolve_nodes`（604 行）/ `_extract_and_resolve_edges`（631 行）：LLM 提取实体与边，**带实体类型过滤（excluded_entity_types）、预定义 Pydantic 实体/边类型（prescribed ontology）、自定义提取指令**
2. `_extract_and_dedupe_nodes_bulk`（783-812 行）：批量去重
3. `_process_episode_data`（680-781 行）：构建 episodic 边（episode→实体出处）→ 落库（`add_nodes_and_edges_bulk`）→ **saga 关联**（NEXT_EPISODE + HAS_EPISODE + first/last 指针）——**纯增量，无全量重算**
4. 事实失效：新 episode 中与旧事实冲突的边被设置 `invalid_at`/`expired_at`——**「信息变化时旧事实被失效而非删除」**（README「Temporal Fact Management」；`graph_queries.py:40,79-81` 为 valid_at/invalid_at/expired_at 建索引）

### C. saga 增量摘要（`summarize_saga`，graphiti.py:438-500）
**双水位机制**（docstring 显式声明，graphiti.py:443-458）：
- `last_summarized_at`：**墙钟水位**（过滤语义）——下一次只取 `created_at`（摄取时间）晚于此值的 episode；回填的旧 episode（valid_at 在过去）也能被下次拾取
- `last_summarized_episode_valid_at`：**事件时间水位**——当前摘要覆盖 episode 的最大 `valid_at`，供消费者回答「摘要内容在事件时间上有多新」
- 摘要增量：仅新 episode 参与，旧摘要作为 LLM 上下文传入「no information is lost」（graphiti.py:480-481）；`max_episodes = 200`（graphiti.py:496）

### D. 社区构建（`build_communities`，graphiti.py:1490）
聚类算法找实体社区 → 建 `CommunityNode` 摘要社区内容（LLM）→ 生成名称嵌入 → 落库；`update_communities` 参数控制 add_episode 后是否更新（默认 False，独立触发）——**社区是可选聚合层，非摄取必经路径**

### E. 混合检索（`search/`）
- `search_config_recipes.py:81-108`：`COMBINED_HYBRID_SEARCH_CROSS_ENCODER` —— 边/节点/社区各用 `bm25 + cosine_similarity + bfs` 三信号 + cross-encoder 重排；另有 RRF / MMR 变体
- `search_filters.py:63-75`：`SearchFilters`——`valid_at`/`invalid_at`/`created_at`/`expired_at` 日期区间过滤 + `node_labels`/`edge_types`/`edge_uuids`/`property_filters`——**以事实有效期为检索硬过滤**
- `center_node_uuid` 参数（graphiti.py:1531）：按与中心节点的图距离重排（图距离信号）
- 图存储：Neo4j / FalkorDB / Kuzu（deprecated）/ Neptune 四驱动（`driver/`）

## 关键设计决策（README 口径 vs 源码实证对照）
| README 声称 | 源码验证结果 |
|:--|:--|
| 「Facts have validity windows. When information changes, old facts are invalidated — not deleted」 | **一致**：EntityEdge 四时间字段（edges.py:271-282）+ invalid_at/expired_at 索引（graph_queries.py:40,79-81） |
| 「Explicit bi-temporal tracking」 | **一致**：EpisodicNode.valid_at（事件时间）+ created_at（事务时间）（nodes.py:318-360）——注意双时态**只落在 episode 层**，EntityEdge 的 valid_at 是派生事实的真值窗口而非独立事件时间 |
| 「Incremental Graph Construction ... without batch recomputation」 | **一致**：add_episode 增量摄取（graphiti.py:980）+ saga 增量摘要（graphiti.py:438） |
| 「Hybrid Retrieval: semantic embeddings, keyword (BM25), and graph traversal」 | **一致**：search_config_recipes.py:81-108 三信号 + 图遍历 BFS + 重排器族 |
| 「Both prescribed and learned ontology」 | **一致**：add_episode 的 entity_types/edge_types 参数（prescribed，Pydantic 模型）+ 无类型时的默认抽取（learned） |
| 「Query what's true now, or what was true at any point in time」 | **部分一致**：时间过滤支持按有效窗口查询（search_filters.py:63-75）；但「what was true at time t」依赖调用方自行组合 valid_at/invalid_at 条件，无 as_of(ts) 单接口——**与 Kairos 双时态声明（债务 D-323）的 as_of(ts) 语义形成对照** |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 事实边时间窗口（valid_at/invalid_at/expired_at 结构化失效） | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（时间轴：物理衰减+逻辑因果双轴）+ 双时态声明（债务 D-323） | 支撑：结构化真值有效区间与 Kairos「时间轴是度量」互补；本笔记独立确认 REPO-07 分诊成立 | 与 [REPO-07 zep](REPO-07-zep.md) 分诊同族（该笔记已登记「可吸收」）；三时间字段 > mem0 单字段 |
| episode 溯源（事实边 episodes 列表 + reference_time） | 已覆盖 | 见证价值轴·来源追踪（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 见证锚定主副本（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：episode 即原始证据流，「从哪来」可审计与 Kairos 同题 | Graphiti 不区分见证/使用副本——失效只改时间戳不删内容，与 Kairos 差异检验仍有别 |
| saga 叙事链（NEXT_EPISODE/HAS_EPISODE + first/last 指针） | 可吸收 | 逻辑-因果轴·事件时序/叙事连贯性（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 见证价值轴·叙事自洽度 | 支撑：对话/事件序列的显式链状拓扑与叙事自洽度同向 | 与 [REPO-04-memoryos.md](REPO-04-memoryos.md) 对话链指针分诊同类 |
| saga 增量摘要双水位（墙钟过滤 + 事件时间水位） | 可吸收 | 升华管道 raw→item→strategy→behavior（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）；反熵注入器（[架构](../../../foundation/architecture-v0.1.0.md) §10.19） | 支撑：双水位分离「摄取时间过滤」与「内容事件时间新鲜度」——**与 Kairos 双时态（occurred_at/created_at）严格同构**，是 D-323 声明在摘要场景的工程实证 | 增量：摘要进度双水位的设计模式可直接借鉴 |
| 实体 summary 随演化更新（EntityNode.summary 区域摘要） | 可吸收 | 升华管道（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）；反熵注入器（[架构](../../../foundation/architecture-v0.1.0.md) §10.19） | 支撑：实体级增量摘要 = 碎片→稳定结构的一种粒度 | 与 [REPO-07 zep](REPO-07-zep.md) 分诊一致 |
| 社区聚合（build_communities 聚类 + LLM 摘要） | 可吸收 | 认知完整性轴·组合约束网络连通性（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）；知识加工区（[架构](../../../foundation/architecture-v0.1.0.md) §5.10） | 支撑：主题社区是长期碎片化的结构化缓解 | 与 REPO-07 分诊一致；「update_communities 默认 False 独立触发」说明其成本特性 |
| BFS 图遍历 + center_node_uuid 图距离重排 | 已覆盖 | 三信号混合检索·图谱距离可选信号（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：Kairos 已登记图谱距离为可选第七信号；Graphiti 是「图信号为主」实证 | Kairos 默认关闭图谱距离的取向不变 |
| 双时态（valid_at 事件时间 + created_at 事务时间） | 已覆盖 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1 双时态声明（债务 D-323） | 支撑：Graphiti 是双时态工程实证 | 注意：Graphiti 双时态在 episode 层；EntityEdge 的 valid/invalid 是真值窗口（第三时间维度），Kairos 可对照区分「双时态」与「真值窗口」概念 |
| 时间过滤为检索硬过滤（SearchFilters valid_at/invalid_at/expired_at） | 已覆盖 | 时间过滤（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a，基于 occurred_at 硬过滤，1117 行时间字段口径勘误） | 支撑：两者同为「以事实有效期为检索硬过滤」 | Graphiti 过滤字段覆盖真值窗口；Kairos 过滤事件时间——语义不同（真值 vs 事件），可对照 |
| 增量摄取不重算（add_episode） | 已覆盖 | ADD-only 提取协议（[架构](../../../foundation/architecture-v0.1.0.md) §7.3g） | 支撑：增量是共同取向；差异：Graphiti 可置 invalid_at（结构化失效），Kairos 不覆盖（ADD-only 叠加 + 差异检验裁决） | 与 REPO-07 分诊一致 |

## 可吸收增量（具体到机制/参数/接口）
1. **saga 增量摘要双水位**（`graphiti.py:443-458`）：`last_summarized_at`（墙钟过滤水位）+ `last_summarized_episode_valid_at`（事件时间水位）——Kairos 升华管道的逐级蒸馏（认知基础 §1.10）可借鉴「摘要进度双水位」以同时回答「摄取侧进度」与「内容侧新鲜度」
2. **事实边三时间字段**（`edges.py:271-282`）：valid_at/invalid_at/expired_at + reference_time——与 [REPO-07 zep](REPO-07-zep.md) 增量 1 合并分诊（该笔记已登记）；本笔记补充：**索引设计**（graph_queries.py:40,79-81 对三时间字段分别建索引）——结构化失效的工程化落地细节
3. **saga 序列组织 + first/last 指针**（`graphiti.py:756-779`）：NEXT_EPISODE/HAS_EPISODE 边 + saga 节点首尾指针——对话序列的显式拓扑（逻辑-因果轴的图落点），REPO-07 增量 3 确认
4. **SearchFilters 时间区间过滤**（`search_filters.py:63-75`）：valid_at/invalid_at/expired_at/created_at 四字段日期过滤 + node_labels/edge_types/edge_uuids/property_filters——Kairos 时间过滤（§7.3a）的多字段对照
5. **prescribed ontology 的 Pydantic 模型接口**（`add_episode` 的 entity_types/edge_types 参数）：开发者预定义实体/边类型 + 排除类型（excluded_entity_types）——Kairos 宪法/辞典对记忆类型的结构化约束的技术参考

## 存疑与未验证
- commit SHA 未记录（浅克隆后未立即记录）；star 数未独立核对
- 「what was true at time t」无 as_of(ts) 单接口——时间点查询需调用方组合过滤条件，未验证组合正确性
- 社区聚类算法具体实现（Louvain 或其他）未深读（`utils/communities.py` 或等价模块未逐行核实）
- 事实失效触发逻辑（新 episode 与旧边冲突时置 invalid_at 的具体判定）未逐行验证（依赖 LLM 提取与去重质量）
- LLM 提取/去重/摘要提示词质量未运行验证（未执行）
- 双时态仅在 episode 层（EntityEdge 无独立 created_at 语义区分），「双时态」与「真值窗口」概念混用需在吸收时澄清

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
