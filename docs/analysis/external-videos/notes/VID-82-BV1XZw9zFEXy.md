---
title: VID-82 视频笔记：端到端上下文工程实现 Agent Memory：Zep【代码解读】
aliases:
  - 外部视频笔记-82
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-82 端到端上下文工程实现 Agent Memory：Zep【代码解读】

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1XZw9zFEXy |
| UP主 | 日新月异max |
| 时长 | 31min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 转写存在大量谐音错字（「Grafty/Germany/GRAPHITY」应为「Graphiti」，「ZAP/Zapp/Zep」混用，「解鎖/監索」应为「检索」，「重排/籤路」，「涂补」应为「图谱」，「招回」应为「召回」，「羽翼实体」应为「实体」等） |

## 内容提炼
### 核心论点
1. Zep=端到端上下文工程平台，核心 Graphiti 图引擎=时序感知的知识图谱，专为 agent 上下文管理设计，与 Mem0 Graph 同是"图做上下文管理"路线（00:03-02:36）。
2. Zep vs Mem0 Graph 的核心区别：Zep 把图检索到的全部上下文信息都输入给大模型，Mem0 Graph 只输入精简后的关键三元组——因此 Zep 更耗 token、检索与回答时间更长（00:40-01:09）。
3. 双时态知识图谱：物理时态（事件实际发生时间）+ 事务时态（记忆创建/判定作废/过时时间，类比数据库审计）；新提取的边与旧边矛盾且时间重叠时，旧边被标记失效——确保图谱反应现态且保留关系演变记录（06:29-07:27）。
4. Graphiti vs Neo4j：Neo4j 只存时间戳、无法自动推理"事情何时失效"、agent 需自行用 Cypher 推理；Graphiti 在 Neo4j 与 agent 之间加一层前置处理（valid_at/invalid_at + ontology 本体），让 agent 直接拿到结构化关系上下文（13:14-16:11）。
5. 检索流水线三段式：召回（向量/BM25/图广度优先搜索）→ 重排（RRF 倒数字融合 / MMR 最大边界相关性 / Cross-encoder）→ 按 prompt 模板组装注入 LLM（07:30-08:50）。

### 关键机制
- 三层级子图：情境子图（对话文本/JSON 原始数据）、实体子图（实体消歧+实体-关系边）、社区子图（强连接实体聚类，受 GraphRAG 启发）（05:27-06:13）。
- 本体 ontology：default_ontology.py 定义节点类型（User/Preference/Location/Event/Organization/Item/Entity/Document）与边类型（LocatedAt/occurredAt 等），相当于图的语义字典（15:00-15:25，22:26-23:30）。
- 存储与检索：graph.add 摄取→ZepGraph 知识图谱（nodes/edges/episodes 三类）→graph.search 并行查询三类→召回→重排→topK→组装→LLM（27:07-30:02）。
- 工程分层：Python 负责算法/数据摄取/评测（LoCoMo/LongMemEval/Deep Memory Retrieval），Go 负责核心服务（低延迟/连接池/连接复用/epoll/MCP 服务器）（10:49-12:58）。
- 核心文件：zep_evaluate.py（评测+推理入口）、Graphiti 服务实现、ontology.py（实体/边定义）（30:14-31:06）。

### 可操作细节
- 重排模型用 BAAI BGE-M3（UP 主替换为千问 embedding）（08:54-09:19）。
- 图谱底用 Neo4j 图数据库，查询走 Cypher 语言（09:37-09:43，26:21-26:41）。
- 评测：Deep Memory Retrieval（MemGPT 提出）、LongMemEval、LoCoMo；与 MemGPT 对比时用 GPT-4 Turbo（09:46-10:09，11:06-11:12）。
- 快速上手：examples/python/quickstart.ipynb 直接复现（19:04-19:42）。

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| 双时态知识图谱（物理时态+事务时态，旧边失效机制） | 06:29-07:27 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a（时间过滤约束 as_of：occurred_at≤ts 且 created_at≤ts 双时态泛化）+ §7.3g（ADD-only：版本事实不覆写） | 支撑：Kairos 双时态语义与 Zep 同构；"旧边失效"对应 Kairos 记忆状态迁移（§5.5 差异检验） | 高度印证 Kairos 时间轴设计 |
| 全量上下文注入的 token 成本问题（vs 三元组精简） | 00:40-01:09 | 可吸收 | [架构](../../../foundation/architecture-v0.1.0.md) §4.3（编译管线：多阶段组装+哈希缓存）+ §10.4（响应时间常数级联） | 挑战：无裁剪的图上下文注入不可取；Kairos 编译管线+注意力预算（§10）做受控组装 | 反面教训 |
| 召回→重排→组装流水线 | 07:30-08:50 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3a（三信号混合检索）+ §7.3c（MMR 去重阶段） | 支撑：RRF≈三信号融合、MMR 直接对应；Kairos 已内置重排/多样性保障 | — |
| 社区子图（强连接实体聚类） | 05:27-06:13 | 可吸收 | [认知基础](../../../foundation/cognitive-foundation.md) §1.1（认知完整性轴：反例覆盖度/路径密度）+ [架构](../../../foundation/architecture-v0.1.0.md) §5.2（存储层组件） | 未触及：Kairos 无社区发现机制；社区聚类可作为路径空间的结构化组织手段 | 蓝图级候选 |
| Graphiti 在数据库与 agent 之间的前置处理层 | 13:14-16:11 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §2.6（元认知层关联组件：检索预处理与结果治理）+ §2.6.1（QueryAnalyzer 查询理解层） | 支撑：同层定位——检索前预处理、检索后治理；Kairos 把该职能放元认知层 | — |
| 本体 ontology（节点/边语义字典） | 22:26-23:30 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §7.3h（实体抽取双策略：LLM 优先 JSON + 关键字降级） | 支撑：ontology=实体抽取的目标 Schema；Kairos 双策略抽取需显式 Schema 支撑 | — |
| 时间感知失效（valid_at/invalid_at） | 13:45-14:55 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §0.3（逻辑-因果时间轴）+ §5.5（记忆状态迁移） | 支撑：失效时间线=Kairos 逻辑因果时间轴在事实层的体现 | — |
| 端到端上下文工程平台定位 | 03:25-04:42 | 已覆盖 | [架构](../../../foundation/architecture-v0.1.0.md) §4（推理皮层：编译管线）+ §9（注意力调度器） | 支撑：Kairos 上下文组装+Token 预算比 Zep 更完整；Zep 聚焦图侧 | — |

## 存疑与未验证
- 「Open Viking（字节跳动近期项目）」为转写（可能为 OpenViking 或其他项目名），视频仅预告未展开，未验证（未验证）。
- 「Grafty 两天前还在更新」「zebEvaluate.py/surface.c.go/ontology.py 为核心文件」为 UP 主读码转述，文件名存在谐音，未与仓库核对（未验证）。
- 「BAAI BGM3」应为 BGE-M3；「Neo4j 用 Cypher 查询」为通用常识，具体图搜索算子未展开（未验证）。
- 「Deep Memory Retrieval 由 MemGPT 提出」为 UP 主转述，未验证（未验证）。
- Zep Cloud 商业信息（注册登录/API 调用）未验证（未验证）。

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
