---
title: REPO-11 仓库分析：Cognee（topoteretes/cognee）
aliases:
  - 外部仓库分析-11
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-11 Cognee（topoteretes/cognee）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/topoteretes/cognee |
| Star | 29849★（任务简报口径，2026-08-07，未独立核对） |
| 语言/许可 | Python（核心）+ Next.js（前端）+ TypeScript（MCP）/ Apache-2.0 |
| 视频对应 | 无（补充发现批次） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone 失败（connection reset），经 gh-proxy 下载 main 分支 tarball（无 .git、无 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：Cognee 是「开源 AI 记忆平台」（README 标题：The Open-Source AI Memory Platform for Agents）——「Ingest data in any format, and Cognee continuously builds a self-hosted knowledge graph that gives your agents persistent long-term memory across sessions. Cognee combines vector embeddings, graph reasoning, and cognitive-science-grounded ontology generation」（`README.md`）。宣称四大卖点：Company Brain、知识基础设施、持久学习 agent、可靠可信 agent（审计/OTEL）。

**源码实证**：核心 API 为 `remember` / `recall` / `forget` / `improve` 四操作（`README.md` 与 `cognee/api/v1/remember/remember.py:632` 一致）——`remember` 双模式：无 session_id 走「add+cognify+improve 永久图」；有 session_id 走会话缓存 + 后台 `improve()` 桥接进图（remember.py:662-676 docstring 明示「session memory (fast cache, syncs to graph in background)」）。**认知科学 grounding 是本体论（ontology）解析而非认知模型**——README 的「cognitive-science-grounded ontology generation」实为 OWL 本体 + 模糊匹配（`modules/ontology/`，`CLAUDE.md`「ONTOLOGY_RESOLVER=rdflib，MATCHING_STRATEGY=fuzzy 80%」）。定位与 Kairos「记忆服务认知存续」的第一性原理框架不同，cognee 是**知识图基础设施**而非认知模型。

## 架构与核心机制（源码实证）

### A. 分层架构（`CLAUDE.md`「Layer Structure」）
`API (cognee/api/v1/)` → 主函数（add/cognify/search/memify）→ 管线编排（`modules/pipelines/`）→ 任务层（`tasks/`）→ 领域模块 → 基础设施适配器（LLM/数据库）。三库分离：**关系库 SQLite/Postgres**（元数据与状态）+ **向量库 LanceDB/ChromaDB/PGVector**（嵌入）+ **图库 Ladybug（默认）/Neo4j/Neptune**（知识图），经 `GraphDBInterface`/`VectorDBInterface` 适配器接口切换。

### B. 摄取管线：add → cognify → improve（`api/v1/remember/remember.py:632`；`api/v1/cognify/cognify.py:43`）
1. `add()`：ingest_data → 存原始数据到存储（S3/local）→ 建 Dataset + Data 记录（关系库）
2. `cognify()`：`classify_documents` → `extract_chunks_from_documents`（TextChunker，可切句/段/词/行）→ `extract_graph_from_data`（LLM 用 Instructor 结构化输出提取实体/关系，`tasks/graph/extract_graph_from_data.py`）→ `summarize_text` → `add_data_points`（落图 + 向量库）
3. `improve()`（memify）：`memify_pipelines/`——`apply_feedback_weights.py`（反馈权重）、`apply_frequency_weights.py`（频率权重）、`consolidate_entity_descriptions.py`（实体描述巩固）、`create_triplet_embeddings.py`（三元组嵌入）、`global_context_index.py`（全局上下文索引）——**这是其「持续学习」的实质：以反馈/频率权重 + 实体级描述巩固 + 三元组嵌入的图后处理**

### C. 图模型（`infrastructure/engine/models/`）
`DataPoint`（所有图节点基类，版本化 + metadata）、`Edge`（source/target/type）、`Triplet`（SPO）；`shared/data_models.py` 的 `KnowledgeGraph` 容器。**溯源戳记机制**：`_stamp_provenance_deep`（`tasks/graph/extract_graph_from_data.py:47-73）递归为所有 DataPoint 戳记 `source_pipeline`/`source_task——「从哪个管线/任务产出」的结构化溯源（比 Kairos 见证锚定的关系层注记更工程化）。

### D. 会话记忆与 agent 记忆（`modules/agent_memory/`，563 行 runtime.py）
- `cognee.agent_memory` 装饰器：`with_memory`（图检索，默认 GRAPH_SUMMARY_COMPLETION 查询）+ `with_session_memory`（会话 trace 反馈检索）+ `save_session_traces`（工具调用轨迹入库）
- 记忆条目判别联合（`memory/entries.py`）：`QAEntry`（问答轮，带 `used_graph_element_ids`——**回答引用了哪些图元素，可审计**）、`TraceEntry`（工具调用步，带 memory_query/memory_context/error）、`FeedbackEntry`（对 QA 的反馈，QAID 链）、`SkillRunEntry`（技能运行记录，success_score ∈[0,1]、feedback ∈[-1,1]）
- 会话缓存后端：sqlite/postgres/redis/fs/tapes（`CACHE_BACKEND`）；`persist_session_trace_after`（默认 null）定期把 N 条 trace 反馈经 memify 物化进知识图谱（runtime.py:508-538）
- 检索上下文上限 `MAX_MEMORY_CONTEXT_LENGTH = 4000`（runtime.py:24）——上下文窗口预算的工程常量

### E. 检索：12+ 种查询类型（```CLAUDE.md```「Available search types」）
GRAPH_COMPLETION（图遍历 + LLM 补全，默认）、GRAPH_SUMMARY_COMPLETION（预计算摘要）、GRAPH_COMPLETION_COT（思维链）、TRIPLET_COMPLETION、RAG_COMPLETION、CHUNKS（向量相似）、CHUNKS_LEXICAL（关键词）、SUMMARIES、CYPHER（直接图查询，需开关）、NATURAL_LANGUAGE（NL→结构化）、TEMPORAL（时间感知）、FEELING_LUCKY（自动选择）——**「自动路由搜索策略」是 recall 的默认取向**。

### F. 多租户与本体
- 权限系统：User → Dataset → Data 层级 + ACL（read/write/delete/share），`ENABLE_BACKEND_ACCESS_CONTROL=True` 时每 user+dataset 可隔离图/向量库；检索按数据集权限过滤（```CLAUDE.md```「Permission Denied on Search 返回空列表防信息泄漏」）
- 本体论：OWL 文件 + rdflib 解析 + 模糊匹配（80% 阈值）grounding 实体抽取

## 关键设计决策（README 口径 vs 源码实证对照）
| README 声称 | 源码验证结果 |
|:--|:--|
| 「combines vector embeddings, graph reasoning, and ontology generation」 | **一致**：三库分离（向量+图+关系）+ ontology 模块；「认知科学 grounding」实为 OWL 本体技术，非认知模型 |
| 「persistent long-term memory across sessions」 | **一致（双模式）**：永久图（add+cognify）+ 会话缓存（后台 improve 桥接）——「快缓存 + 慢图」双写架构 |
| 「Learning Agents - learn from feedback」 | **部分一致**：FeedbackEntry/SkillRunEntry + apply_feedback_weights 是显式反馈通道；但无遗忘/衰减机制，图只增不减（`cleanup_unused_data.py` 存在但为清理孤儿数据） |
| 「Reliable and Trustworthy Agents - traceability」 | **一致**：_stamp_provenance_deep 溯源 + QAEntry.used_graph_element_ids 引用记录 + OTEL tracing |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 会话缓存 + 后台图桥接（remember 双模式，remember.py:662-676） | 可吸收 | 双副本（[架构](../../../foundation/architecture-v0.1.0.md) §5.5）+ 使用权重影子副本 | 张力：cognee 的「session 快缓存→后台 improve 同步进永久图」是**升级路径**（会话数据最终并入见证侧），与 Kairos 双副本「使用权重影子副本永不反向写主副本」的隔离防线（架构 §5.5）**方向相反**——cognee 是「快数据最终进真相」，Kairos 是「使用数据永不进真相」 | 对照价值：Kairos 需论证为何不采用「会话→永久」升级（答案：契约是运行时投影，会话参与度本身是使用信号非见证信号） |
| QAEntry.used_graph_element_ids（回答引用图元素可审计） | 可吸收 | 见证价值轴·来源追踪（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 检索审计（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：回答→证据元素的反向引用是「检索用到了什么」的审计形态，与 Kairos 检索链路可观测性同题 | 增量：图元素级引用记录的接口形态 |
| _stamp_provenance_deep 递归溯源戳记（source_pipeline/source_task） | 已覆盖 | 见证锚定主副本（[架构](../../../foundation/architecture-v0.1.0.md) §5.5）+ ADD-only（§7.3g） | 支撑：Kairos 已有来源追踪；cognee 的「递归戳记整棵对象图」是实现细节 | 增量：递归戳记算法（对嵌套 DataPoint 结构统一打标） |
| 三元组嵌入 + 反馈/频率权重图后处理（memify_pipelines/） | 可吸收 | 认知完整性轴（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 升华管道（§1.10） | 支撑：图后处理（三元组级嵌入、频率权重）是「结构增强」的工程形态，与反熵注入器（[架构](../../../foundation/architecture-v0.1.0.md) §10.19）对照 | 增量：频率权重作为结构增强信号（注意与 Kairos「频率≠价值」的使用价值轴口径差异） |
| 12 种查询类型自动路由（FEELING_LUCKY） | 已覆盖 | 检索深度分级 R0/R1/R2 + 三信号混合检索（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：查询类型路由与 Kairos 检索深度分级同构 | Kairos 分级更结构化（固定 R0/R1/R2），cognee 是枚举路由 |
| 每 user+dataset 隔离数据库 + ACL | 已覆盖 | 分域真理路由（[认知基础](../../../foundation/cognitive-foundation.md) §C.6）+ 路径空间硬过滤（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：多租户隔离是 Kairos 路径空间过滤的物理形态 | cognee 用物理隔离（独立库），Kairos 用逻辑过滤（路径前缀） |
| MemorySource 跨系统迁移（Mem0/Zep/Graphiti/Letta 导入） | 可吸收 | 契约是运行时投影（认知基础 §2.2）+ 外部校准源建模（张力 T-002） | 支撑：跨系统记忆导入 = 外部记忆格式的一等建模尝试 | 增量：COGX 记录格式（COGNEE-X 交换）作为记忆互操作格式的参考；与 T-002「外部校准源未建模为一等公民」直接相关 |

## 可吸收增量（具体到机制/参数/接口）
1. **会话缓存 + 后台图同步的工程形态**（`api/v1/remember/remember.py:632`；`infrastructure/session/session_manager.py`）：session 快速写入 + 后台 improve 桥接 + `persist_session_trace_after` 批量物化——Kairos 可对照设计「会话级暂存→永久记忆」的边界（需论证与双副本隔离防线的关系）
2. **QAEntry.used_graph_element_ids**（`memory/entries.py:38`）：回答级别引用记录——检索审计的可落地接口（Kairos 审计庭可要求 recall 响应携带引用）
3. **递归溯源戳记**（`tasks/graph/extract_graph_from_data.py:47-73`）：`_stamp_provenance_deep` 对嵌套图对象统一戳记 source_pipeline/source_task——见证锚定关系层注记的实现参考
4. **memify 图后处理族**（`memify_pipelines/apply_frequency_weights.py` 等）：三元组嵌入 + 实体描述巩固 + 反馈权重——反熵注入器（§10.19）之外的「结构增强」路径对照
5. **本体论 grounding 管线**（`modules/ontology/`）：OWL + 模糊匹配（80%）约束 LLM 实体抽取——Kairos 宪法/辞典约束外部理念落地的技术对照

## 存疑与未验证
- 无 commit SHA（gh-proxy tarball）；star 数未独立核对
- LLM 提取质量依赖提示词与 Instructor 结构化输出，未运行验证（未执行）
- `TEMPORAL` 查询类型的实际时间语义未深读（时间感知实现细节未验证）
- MemorySource/COGX 迁移格式为新增能力（README 未提及），仅见代码路径（`modules/migration/import_source.py` 被 remember.py:760 引用），细节未深读
- 图库 Ladybug 为自研（非主流图库），其能力边界（时间遍历等）未验证

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
