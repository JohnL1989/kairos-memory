---
title: REPO-14 仓库分析：Basic Memory（basicmachines-co/basic-memory）
aliases:
  - 外部仓库分析-14
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-14 Basic Memory（basicmachines-co/basic-memory）

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/basicmachines-co/basic-memory |
| Star | 3600★（任务简报口径，2026-08-07，未独立核对） |
| 语言/许可 | Python（FastAPI + MCP + CLI）/ Apache-2.0（LICENSE 文件，未逐行核对） |
| 视频对应 | 无（补充发现批次） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 git clone --depth 1（首次克隆不完整重新克隆成功，有 .git；未记录 commit SHA） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**（`NOTE-FORMAT.md` 更核心）：Basic Memory 是**文件系统式记忆**——「Every document in Basic Memory is a plain Markdown file. **Files are the source of truth** — changes to files automatically update the knowledge graph in the database. You maintain complete ownership, files work with git, and knowledge persists independently of any AI conversation」。架构文档（`DOMAIN_MODEL.md`）：「Basic Memory gives humans and agents **one canonical representation for note knowledge: Markdown**. Other resources may be addressable, but structured note and graph semantics are **derived from Markdown** without making the resulting projections a competing source of knowledge」。

**源码实证**：领域模型（`DOMAIN_MODEL.md` 全篇 + `src/basic_memory/`）：Project（隔离边界）→ Note（用户可见 Markdown 文档）→ Entity（索引化资源表示，图/搜索投影的挂载点）→ Observation（分类语义陈述）→ Relation（有向语义边）→ NoteContent（已接受字节与物化状态的操作记录）。**定位与源码一致且罕见地自洽**：这是「Markdown 为主真相、图谱与搜索为可重建投影」的记忆系统——与 Kairos 双副本思想有结构呼应，但**无自动提取、无遗忘、无衰减、无 LLM 记忆管理**——记忆的形成由**人类作者**（或 LLM 通过 MCP 工具）写入 Markdown，系统只做解析与索引。

## 架构与核心机制（源码实证）

### A. 领域模型与真相层级（`DOMAIN_MODEL.md`）
1. **设计中心**：「Markdown 是源真相」的精确表述（`DOMAIN_MODEL.md`）——其他资源可寻址，但结构化语义从 Markdown 派生，派生投影不构成竞争性知识源
2. **真相权威分阶段**（`DOMAIN_MODEL.md`）：
   - 本地文件优先流：Markdown 文件是**持久权威**——直接人工编辑/CLI/MCP/API 写入都收敛到文件；实体/图/搜索状态从落盘字节调和（reconcile）
   - DB 优先（云风格）流：服务一次派生最终 Markdown 并记录在 `NoteContent`——物化完成前该版本是**操作权威**；工作线程将相同字节物化到存储并记录文件版本/校验和
3. **投影纪律**（`DOMAIN_MODEL.md`）：FTS 行/向量嵌入/块/观察行/关系行**都是派生投影**——可滞后于已接受写入、可重建、删除索引不得改动规范内容——「搜索结果是投影，不成为独立文档」

### B. 笔记格式（`NOTE-FORMAT.md`）
- 文档三部分：YAML frontmatter（title/type/tags/permalink/schema + 自定义字段存 entity_metadata）+ 观察（`- [category] content #tags (context)`）+ 关系（`- relates_to [[Wiki Link]]`）
- 解析器排除：checkbox 列表、Markdown 链接、裸 wiki 链接（后者视为关系）——**观察/关系的语法模式驱动解析，无需 LLM**
- 自定义 frontmatter 字段全部入 entity_metadata 并参与检索过滤

### C. 投影实现（源码实证）
- **搜索**（`services/search_service.py`，934 行）：`SearchService.search`（265 行）——支持①精确 permalink ②通配符路径匹配 ③全文检索（title/content）；`retrieval_mode` 枚举路由；**relaxed FTS 回退**（`_is_relaxed_fts_fallback_eligible`，349 行 + `_generate_variants` 372 行——为复合 CJK token 的布尔 OR 变体救援）；`_include_legacy_note_type_spellings`（186 行）
- **索引**（`indexing/` 36 个模块）：`file_indexer.py`、`change_detector.py`、`change_planning.py`、`link_resolution.py`（wiki 链接解析）、`forward_reference_resolution.py`（前向引用）、`batch_indexer.py`——文件变更 → 解析 → 实体 upsert → 投影重建的流水线
- **语义向量**（`repository/`）：`semantic_vector_index.py` / `pgvector_index.py` / `sqlite_vec_index.py` + 嵌入 provider 族（`fastembed_provider.py` / `litellm_provider.py` / `openai_provider.py`）+ 重排 provider（`fastembed_rerank_provider.py` / `litellm_rerank_provider.py`）+ `semantic_chunking.py`——语义搜索是**附加投影**，可滞后可重建
- **Picoschema**（`picoschema/`：parser/resolver/validator/inference/diff）：schema 解析、校验、推断、漂移检测——对 frontmatter schema 的结构化治理
- **架构工程**（`ARCHITECTURE.md`）：composition root 容器模式（ApiContainer/McpContainer/CliContainer）、显式依赖注入（模块不读全局配置）、`persist_accepted_note_snapshot` 单边界写操作（事务内写实体快照 + NoteContent + 图行 + 搜索行，`ARCHITECTURE.md`）

### D. 入口
API（FastAPI v2 routers）+ MCP（工具 → 类型化客户端 → API）+ CLI（Typer）；watch 协调器（`index/watch_coordinator.py`，文件变更监听）

## 关键设计决策（README 口径 vs 源码实证对照）
| README/文档声称 | 源码验证结果 |
|:--|:--|
| 「Files are the source of truth — changes to files automatically update the knowledge graph」 | **一致**：`DOMAIN_MODEL.md` 真相分层 + indexing/ 文件变更→投影重建流水线 |
| 「The projections (graph/search) are derived from Markdown, not a competing source of knowledge」 | **一致且为全库最强纪律**：`DOMAIN_MODEL.md`「projection may lag / must be rebuildable / deleting index must not mutate canonical content」——**与 Kairos「见证锚定主副本 + 影子副本可重建」的 R-03 声明（架构 §5.5 使用权重影子副本可重建性）同构** |
| 「Basic Memory = knowledge graph in the database」 | **部分一致**：关系图（relations 表 + 解析）存在，但**图是派生投影**；实体/关系没有图数据库后端，语义检索是独立向量投影 |
| 无自动记忆提取/无遗忘/无衰减 | **一致（口径诚实）**：README 未声称自动记忆管理；记忆形成靠人类/LLM 写 Markdown |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 投影纪律：「派生投影可滞后/可重建/删除索引不改规范内容」（`DOMAIN_MODEL.md`） | 已覆盖 | 使用权重影子副本可重建性声明 R-03（[架构](../../../foundation/architecture-v0.1.0.md) §5.5）+ 双副本隔离防线 | 支撑：Basic Memory 是「主真相 + 可重建投影」纪律的完整工程实证（虽然其投影是检索索引而非使用权重） | Kairos R-03 的「影子副本可由事件流重放重建」与 Basic Memory「搜索索引可由 Markdown 重建」是同一纪律的两个实例——**外部实证确认 R-03 的合理性** |
| 真相权威分阶段（文件优先 vs DB 优先操作权威，`DOMAIN_MODEL.md`） | 可吸收 | 契约是运行时投影（认知基础 §2.2）+ 见证锚定主副本（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：Basic Memory 明确「写入阶段决定操作权威」——与 Kairos「见证锚定同步更新通道 vs 影子副本异步修改路径」的写入通道区分同题 | 增量：NoteContent 的 db_version/file_version + checksum 双版本追踪（物化状态机：pending/writing/synchronized/failed/blocked）——Kairos 双副本物化可借鉴 |
| 观察分类语法 `[category]` + 关系语法 `[[wiki]]`（NOTE`-FORMAT.md`） | 可吸收 | 升华管道 raw→item→strategy→behavior（[认知基础](../../../foundation/cognitive-foundation.md) §1.10）+ 记忆类型分类 | 支撑：**作者显式写结构化语义**（人类即提取器）与 Kairos LLM 提取互补——一条「无 LLM 提取」的替代路径 | 张力：Kairos 假定自动提取（管道），Basic Memory 假定人工结构化——两者适用场景不同，可对照但不可直接替代 |
| permalink 稳定标识（frontmatter，移动不失效，`DOMAIN_MODEL.md`） | 已覆盖 | 见证价值轴·来源追踪（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ ADD-only（[架构](../../../foundation/architecture-v0.1.0.md) §7.3g） | 支撑：稳定标识符 + 移动保留 identity 与 Kairos 版本溯源同题 | 增量：external_id 与 file_path 分离（「身份稳定、位置可变」）的字段设计——Kairos 记录身份设计参考 |
| 前向引用解析（forward_reference_resolution.py，关系目标后建也解析） | 可吸收 | 认知完整性轴·组合约束（[认知基础](../../../foundation/cognitive-foundation.md) §1.1）+ 差异检验（[架构](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：关系目标缺失时保留作者原文（to_name）+ 目标出现后解析——「悬空引用可后补」与 Kairos 知识演化候选集同题 | 增量：to_name（未解析目标原文保留）字段——「解析是丰富而非替换」的语义（`DOMAIN_MODEL.md`） |
| relaxed FTS 回退（CJK 复合 token 布尔 OR 变体，search_service.py:349-396） | 可吸收 | 三信号混合检索（[架构](../../../foundation/architecture-v0.1.0.md) §7.3a） | 支撑：检索降级路径（严格失败→宽松重试）的工程形态；CJK 前缀匹配问题的具体处理 | 增量：检索分层回退（strict → relaxed OR）的参数与触发条件 |
| Watch 文件监听 → 自动重索引（watch_coordinator.py） | 已覆盖 | 契约是运行时投影 + 摄取沙箱（[架构](../../../foundation/architecture-v0.1.0.md) §7.3） | 支撑：文件系统事件驱动的增量索引与 Kairos 增量摄取同题 | 差异：Basic Memory 监听外部文件（用户编辑），Kairos 面向 agent 会话 |

## 可吸收增量（具体到机制/参数/接口）
1. **NoteContent 双版本追踪 + 物化状态机**（`DOMAIN_MODEL.md` + `repository/note_content_repository.py`）：`db_version/db_checksum`（已接受内容）+ `file_version/file_checksum`（已物化文件）+ 状态机（pending/writing/synchronized/failed/blocked）——Kairos 双副本「见证锚定主副本 + 使用权重影子副本」的物化一致性追踪参考
2. **稳定身份与位置分离**（`DOMAIN_MODEL.md`:47-56）：`external_id`（稳定 API 身份，移动不变）vs `file_path`（可移动）vs `permalink`（语义地址，按策略变化）——三种标识符的职责分工，Kairos 记录身份设计可对照
3. **关系保留作者原文**（`DOMAIN_MODEL.md`）：relation 目标未解析时保留 `to_name`（作者原文），解析只是丰富不是替换——Kairos 关系层「未解析目标」字段参考
4. **检索分层回退**（`services/search_service.py:349-396`）：严格 FTS 失败 → relaxed 布尔 OR 变体（CJK 前缀救援）——Kairos 检索管线降级路径的具体实现对照
5. **picoschema 漂移检测**（`picoschema/diff.py`）：schema 推断/校验/漂移——Kairos 宪法/辞典对记忆 schema 的结构化治理参考

## 存疑与未验证
- commit SHA 未记录（首次克隆失败后重新克隆）；star 数未独立核对
- README 主文档未逐行深读（重点读了 NOTE-FORMAT/DOMAIN_MODEL/ARCHITECTURE 三份），README 的定位表述与文档口径一致
- 语义向量投影的重建/滞后机制（semantic_vector_sync.py）细节未深读
- watch 文件监听的平台适配（跨平台文件事件）未验证
- 「graphs 是派生投影」是否包含图遍历检索能力（relation 图是否有查询接口）未完全验证——relations 表存在，图查询路由存在（knowledge_router），但图遍历算法未深读
- 该仓库工程化程度高（alembic 迁移 20+ 个版本），说明投影演化频繁——时效性风险：分析基于当前 main

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
