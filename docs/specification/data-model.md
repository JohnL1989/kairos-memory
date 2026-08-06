---
title: Kairos 数据模型设计
aliases:
  - 数据模型
  - Data Model
tags:
  - kairos
  - design
  - data-model
created: 2026-07-20
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 数据模型设计

> **定位**：定义 Kairos 系统的核心数据存储结构。架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4 定义了存储层的行为约束，本文定义具体的 Schema 设计。
>
> **存储后端**：标准模式 PostgreSQL + pgvector，轻量模式 SQLite + sqlite-vec。
>
> **记忆生命周期权威状态机**：本文涉及三套记忆状态，三者描述不同维度的生命周期，互不冲突：
> - `memories.status`（运行时生命周期）：active → stale → archived（含子态 suppressed）→ superseded。控制检索可见性——suppressed 不可检索但数据保留，superseded 被新版本取代。
> - `memory_states.state`（状态变更审计轨迹）：值与 `memories.status` 相同，每次状态转换写入一行。`memories.status` 是当前态，`memory_states` 是历史变迁。
> - `extinction_status`（知识生命周期）：active → extinct（知识不再有效）→ fossilized（保留为历史化石）。独立于运行时可见性——已灭绝但 active 的记忆仍可检索。仅影响认知层的知识可信度评估。
>
> 三者正交：一条记忆可同时为 `status=active`（可检索）、`extinction_status=extinct`（知识无效）、`memory_states.state=active`（当前态）。详见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 遗忘调度器与 extinction 关系。

---

## §1 核心记忆表

### memories（主记忆表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | 全局唯一记忆 ID |
| `path` | TEXT | NOT NULL, UNIQUE(path, version) | kairos:// 路径。同路径多条记忆通过递增 version 写入（首次写入 version=1，后续写入 version 递增） |
| `version` | INTEGER | DEFAULT 1 | 版本号，更新时递增 |
| `content` | TEXT | NOT NULL | 记忆内容 |
| `content_summary` | TEXT | — | 记忆摘要（由升华管道生成，用于中层检索。v0.1.0 统一 1536 维单向量；128 维摘要向量与 2048 维全量向量为 v1.1+ 检索深度分级目标，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.9） |
| `is_sensitive` | BOOLEAN | DEFAULT FALSE | 敏感信息标记。为 true 时 content 字段自动 AES-256-GCM 加密存储（S-07）、导出时脱敏 |
| `content_hash` | TEXT | NOT NULL | SHA-256(content) |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 语义向量。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3，原生 1024 维线性投影至 1536），DDL 以 1536 为准 |
| `memory_types` | JSONB | NOT NULL | JSON 数组：["episodic", "semantic", "procedural"] 可组合，一条记忆可同时属于多类型。叙事特殊规则由 `identity_relevance` 参数承载，非独立类型（认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.2） |
| `identity_relevance` | FLOAT | DEFAULT 0, [0,1] | 身份关联程度参数——叙事记忆特殊规则（巩固速率自我参照调制/遗忘身份注册表保护/检索自洽偏向）的触发维度，非独立记忆类型（认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.2） |
| `contract` | TEXT | NOT NULL, DEFAULT 'ondemand' | 契约类型：permanent / ondemand / environmental / temporary / intention（临时契约写回 LTM 带 TTL，到期自动清除；**intention 意图契约**为前瞻记忆专用——位于 `kairos://_system/intentions/`，激活优先级低于常驻但高于按需，不受遗忘调度器评估，意图完成/取消后降级为 ondemand，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 前瞻记忆段）。**写时默认建议值语义**：本列值为写入时的默认建议（基于内容类型与路径推断），运行时由策略层预测器按激活权重覆盖（架构 §3.1/§3.7——契约是连续激活权重的离散投影，非写时绑定死标签） |
| `hall` | TEXT | DEFAULT 'processing' | 知识加工区：processing / validation / canonical |
| `solution_branch_id` | UUID | — | 所属解决方案分支 ID（同一记忆的多种语境化表征） |
| `distill_level` | INTEGER | DEFAULT 0, [0,4] | 蒸馏层级：0=碎片 / 1=会话 / 2=日总结 / 3=体系 / 4=元规则 |
| `extinction_status` | TEXT | DEFAULT 'active' | 知识灭绝状态：active / extinct（已灭绝）/ fossilized（已化石化） |
| `extinct_at` | TIMESTAMPTZ | — | 灭绝时间（extinction_status=extinct 时设置） |
| `extinct_reason` | TEXT | — | 灭绝触发事件描述（外部环境变更记录） |
| `lma_urn` | TEXT | — | 逻辑记忆地址 URN（MTL 二层映射的永久逻辑地址，格式：urn:kairos:lma:<uuid>），首次写入时分配，物理迁移不变 |
| `sync_version` | INTEGER | DEFAULT 0 | 端云同步本地版本号 |
| `provenance` | TEXT | NOT NULL | 来源：external_calibration / internal_inference / user_input / system_generated / exploration |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | active / stale / archived（含子态 suppressed）/ superseded。`suppressed` 为 `archived` 子态（被抑制路径不可检索，数据仍存在） |
| `is_identity` | BOOLEAN | DEFAULT FALSE | 身份注册表标记。v0.1.0 构造论实现：初始赋予由见证锚定写入触发（冷启动锚点），持续有效性由叙事连贯性检测器驱动双向更新（自洽度上升→置信度提升；持续下降→经宪法解释层判例降级）。使用权重永远无法将其置为 false（S-10 见证豁免） |
| `identity_confidence` | FLOAT | DEFAULT 0.5, [0,1] | 身份建构置信度——初始赋予后由叙事自洽度时间序列驱动更新（加强建构/降级审查的输入） |
| `identity_reviewed_at` | TIMESTAMPTZ | — | 最近一次身份重评时间（叙事连贯性检测器触发或宪法解释层审查） |
| `identity_review_count` | INTEGER | DEFAULT 0 | 身份重评累计次数（审计与降级提案依据） |
| `is_structure` | BOOLEAN | DEFAULT FALSE | 是否为结构性记忆（认知完整性轴）。**双向同步**：与 `structural_value` 同步——`is_structure=true` ↔ `structural_value=2`（写入时按 `structural_value` 判定结果同步，保持后向兼容） |
| `structural_value` | INTEGER | DEFAULT 0 | 半定量结构标记（新增，0/1/2）：0=非结构 / 1=疑似结构 / 2=确认结构。判定条件与遗忘调度器分级行为见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 结构性记忆守护（L1：被 ≥2 条 causal 引用/路径高分叉/叙事线断裂风险；L2：外部校准标记/手动标注/L1+引用计数 ≥ 阈值）。v1.1 三维连续度量上线后降级为快速索引（D-311 衔接） |
| `structural_value_reasons` | JSONB | DEFAULT '[]' | 升档原因列表（新增），如 `["causal_ref_count_ge_2", "external_calibration_tagged"]` |
| `structural_value_updated_at` | TIMESTAMPTZ | — | 最近一次升/降档时间（新增） |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | 软删除标记，API 软删除操作设置此标记（保留审计痕迹） |
| `calibration_confidence` | FLOAT | DEFAULT 0.5, [0,1] | 校准置信度 |
| `vad_v` | FLOAT | DEFAULT 0, [-1,1] | 情感效价（Valence） |
| `vad_a` | FLOAT | DEFAULT 0, [-1,1] | 情感唤醒度（Arousal） |
| `vad_d` | FLOAT | DEFAULT 0, [-1,1] | 情感支配度（Dominance） |
| `decontextualization_level` | FLOAT | DEFAULT 0, [0,1] | 去语境化程度，升华时递增 |
| `heat_score` | FLOAT | DEFAULT 1.0, [0,1] | 热度评分，用于排序权重调制 |
| `expires_at` | TIMESTAMPTZ | — | 临时契约自动清除时间（仅 temporary 契约有效，到期后台 forgetAfter 硬删除——数据不可恢复。清理前写入审计日志（标记 `expiry_cascade_delete`，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 forgetAfter）——不留审计痕迹的场景仅限捕获阶段拒绝的输入。与 POST /v1/memories/{id}/expire 的「到期归档」不同：temporary 硬删除不可恢复，适用于明确的临时数据治理策略） |
| `locked_until` | TIMESTAMPTZ | — | 锁定保护截止时间（`POST /v1/memories/{id}/lock` 设置，到期自动解锁） |
| `encoding_context` | JSONB | — | 编码情境（时空上下文/任务目标/关联记忆ID）。**`conditions` 子结构约定（外部理念吸收，changelog 0.0.39）**：条件性经验（「适用于什么场景/哪个用户/哪个网站或工具版本」的经验）应在 encoding_context 中记录显式 `conditions` 子结构——`{applies_to: ["<用户/网站/工具版本标识>"], prerequisites: ["<前提条件>"], exceptions: ["<不适用场景>"]}`。用途：(a) 写入时约束经验固化——无条件约束的经验不得在升华管道中被去语境化为通用规律（对应「一条经验是否携带适用范围」的写入判定）；(b) 检索时按当前环境匹配 conditions——环境不匹配的候选在排序中降权（v1.1 落地为独立过滤维度，v0.1.0 作为 encoding_context 的约定子结构，不新增列）。与 `domain`（领域路由标签）互补：domain 是粗粒度领域分类，conditions 是细粒度适用条件。v0.1.0 仅要求写入时填充（升华管道 L1 阶段识别条件性表述时录入），检索侧不做强制过滤 |
| `occurred_at` | TIMESTAMPTZ | — | **事件时间**——记忆所描述的事实实际发生的时间（区别于 `created_at` 事务时间：写入时间）。由轻量级时间戳后处理（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 event_time 提取）回填，可空（无法判定事件时间的记忆不填）。双时态模型（认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 双时态声明）：事件时间归逻辑-因果轴/物理轴输入，事务时间由衰减子轴承载。竖切 v0.1.0-slice 落列为可空字段 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 创建时间（**事务时间**——记录写入系统的时间，与 `occurred_at` 事件时间区分） |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 最后更新时间 |
| `superseded_by` | UUID | REFERENCES memories(id) ON DELETE SET NULL | 被取代的新记忆 ID（修正场景）。注意：临时契约硬删除时该 FK 自动置 NULL |
| `parent_memory_id` | UUID | REFERENCES memories(id), NULLABLE | 版本链直接前驱版本。首次写入时为 NULL（版本链模型，架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 版本链模型） |
| `root_memory_id` | UUID | REFERENCES memories(id), NULLABLE | 版本链根节点。首次写入时指向自身，后续版本共享同一 root（全链遍历只需 `WHERE root_memory_id = ? ORDER BY created_at`） |
| `next_version_id` | UUID | REFERENCES memories(id), NULLABLE | 版本链直接后继版本。最新版本为 NULL，提供 O(1) 正向跳转 |
| `is_latest` | BOOLEAN | DEFAULT TRUE | 是否属于版本链最新版本。新版本写入时旧版本自动置 FALSE；检索默认仅返回 is_latest=TRUE |
| `last_access_at` | TIMESTAMPTZ | — | 最后访问时间（用于遗忘曲线计算） |
| `domain` | TEXT | DEFAULT 'general' | 领域标签（用于领域路由检索） |
| `quality_tier` | TEXT | DEFAULT 'world' | 认知质量层级（四层记忆质量层次）：mental_models / observation / experience / world。决定检索优先级和遗忘豁免级别。**权威定义所在（引用勘误）**：[architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §四层记忆质量层次（v1.1+ 规划组件，v0.1.0 仅承载字段与默认值 'world'） |
| `compacted` | BOOLEAN | DEFAULT FALSE | 压缩标记：该记忆是否已被压缩合并进精炼记忆（见 `compaction_snapshots` 表）。`POST /v1/admin/compaction/rollback/{snapshot_id}` 回滚时恢复为 FALSE；已过去 >30 天的压缩不可回滚（RC-07 补充） |
| `compression_trail` | JSONB | DEFAULT '{}' | 逐记忆压缩审计日志（新增）：记录编码/巩固阶段被压缩的认知维度、压缩比、原因、恢复债编号与版本——结构 `{total_compression_ratio, compressed_dimensions: [{dimension, category, compressed_to, compression_ratio, reason, recovery_debt, recovery_version, compressed_at}], last_updated}`。为架构 §10.11 全局 P6 监控的逐记忆粒度展开；检索侧维度丢失不写本字段（记事件总线 `retrieval_dimension_loss`）。能力矩阵见 [capability_matrix.yaml](../references/capability_matrix.yaml) |
| `compacted_at` | TIMESTAMPTZ | — | 压缩发生时间（用于判定 30 天回滚窗口） |

**索引**：
- `idx_memories_path` ON `path`（支持前缀查询）
- `idx_memories_contract` ON `contract`
- `idx_memories_types` ON `memory_types`（JSON 数组索引，使用 GIN）
- `idx_memories_created` ON `created_at`
- `idx_memories_identity` ON `is_identity` WHERE `is_identity = TRUE`
- `idx_memories_status` ON `status`
- `idx_memories_last_access` ON `last_access_at`
- `idx_memories_hall_status` ON `hall`, `status`
- `idx_memories_embedding` 向量索引（pgvector: IVFFlat 或 HNSW）

### memory_relations（关系索引表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `source_id` | UUID | FK → memories(id) | 源记忆 |
| `target_id` | UUID | FK → memories(id) | 目标记忆 |
| `relation_type` | TEXT | NOT NULL | 基础六值：causal / independent / hierarchical（=认知基础「弱层级关系」）/ competitive / part_whole / derived_from。前四类对应认知基础四类关系（因果/部分独立/弱层级/竞争），`part_whole` 为粒度组合关系（父子记忆组成关系，对应认知基础「记忆粒度性质」声明），`derived_from` 为派生关系（mental_model → source，追踪高层认知框架的底层事实来源，对应架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 Mental Model 基于源头的可刷新性）——后两类与前四类对等关系不同属一个分类轴。**语义标记扩展**：架构层 MCP 链接（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3.1 kairos_link）与 ADD-only 提取协议（§7.3g）使用的补充语义标记 `supplement / refutation / reference / contextual / temporal` 作为本列的扩展值同列存储（TEXT 类型，无 CHECK 约束），语义细节记于 `reason` 字段；其中 `temporal` 由轻量级时间戳后处理（架构 §5.2）写入时间关系边。检索按 relation_type 精确过滤，六值与语义标记扩展不互斥——同一对记忆可同时存在不同 relation_type 的关系边（UNIQUE 约束按三元组区分）。 |
| `strength` | FLOAT | DEFAULT 1.0, [0,1] | 关系强度 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
**约束**：UNIQUE(source_id, target_id, relation_type) 防止同一对记忆之间的同类型关系重复插入。
**索引**：`idx_memory_relations_target` ON `target_id`（反向查询「哪些记忆引用了我」）；`idx_memory_relations_type` ON `relation_type`（按关系类型检索）

### knowledge_evolution（知识演化追踪表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `source_id` | UUID | FK → memories(id), NOT NULL | 源知识（演化前的版本） |
| `target_id` | UUID | FK → memories(id), NOT NULL | 目标知识（演化后的版本） |
| `relation_type` | TEXT | NOT NULL | 演化关系：replaces / enriches / confirms / challenges。分别对应：取代（新知识使旧知识过时）、丰富（新知识补充细节）、确认（独立验证已有知识）、挑战（新知识矛盾于旧知识） |
| `confidence` | FLOAT | DEFAULT 0.5, [0,1] | 演化检测置信度 |
| `detection_method` | TEXT | DEFAULT 'jaccard' | 检测方法：jaccard（文本相似度初筛）/ llm（LLM 精确分类）/ manual（手动标注） |
| `detected_at` | TIMESTAMPTZ | NOT NULL | 检测时间 |
| `valid_from` | TIMESTAMPTZ | — | 演化关系有效起始时间（双时态补充，对应架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 as_of 时态查询） |
| `valid_to` | TIMESTAMPTZ | — | 演化关系有效截止时间（NULL=当前有效。`as_of(ts)` 查询按 valid_from ≤ ts AND (valid_to > ts OR valid_to IS NULL) 判定） |
| `created_at` | TIMESTAMPTZ | NOT NULL | 记录创建时间 |

**索引**：UNIQUE(source_id, target_id, relation_type) — 同一对记忆之间的同类型演化关系唯一。
**索引**：`idx_knowledge_evolution_target` ON `target_id`（反向查询「谁演化自谁」）。
**自引用防护**：写入时校验 target_id ≠ source_id，防止自引用演化记录。

> **触发机制**：写入 `memories` 表后，后台触发 Jaccard 相似度计算（对比新内容与已有知识的前 500 chars），候选集门槛与各关系类型的语义判定规则**以架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 知识演化追踪为权威定义**（replaces = Jaccard > 0.7 且语义矛盾；enriches = 0.5-0.7 无矛盾；confirms = >0.7 语义一致；challenges = 同领域低相似度+质疑模式）——本节仅承载表结构，不再复述判定阈值。检测结果写入本表，relation_type=replaces 时自动将 source_id 对应的记忆标记为 `superseded`。**与 Flag 系统的共享**：上述 Jaccard 粗筛阶段（相似度 > 0.7）同时服务于 contradiction Flag 的触发——进入候选集的对会额外经过极性判定（LLM 标注核心主张的正向/负向/中立），极性相反则挂载 contradiction Flag（详见 `memory_flags` 表）。

### memory_flags（Flag 标记表）

Flag 系统为记忆提供临时标记机制——对满足特定条件的记忆挂载自动化标记，驱动后续审查或清理动作。与 `memories.status`（永久状态）不同，Flag 是临时性的、有明确解析条件的元数据标记。详见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 Flag 系统。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id), NOT NULL | 被标记的记忆 |
| `flag_type` | TEXT | NOT NULL | Flag 类型：needs_verify（30天无演化链触发）/ contradiction（Jaccard>0.7+极性相反）/ needs_regeneration（`derived_from` 源变化触发——枚举值大小写与 `memory_relations.relation_type` 的 `derived_from` 一致）。可扩展 |
| `triggered_at` | TIMESTAMPTZ | NOT NULL | Flag 挂载时间 |
| `resolved_at` | TIMESTAMPTZ | — | Flag 解析时间（NULL=当前活跃） |
| `trigger_reason` | TEXT | — | 触发原因描述（如「30天内无演化链活动」「与 memory xxx 极性相反」「源记忆 xxx 被 superseded」） |
| `resolution_reason` | TEXT | — | 解析原因描述（如「外部校准确认」「演化链更新」「宪法解释层裁定 false positive」） |
| `metadata` | JSONB | DEFAULT '{}' | 扩展元数据。contradiction 类型时记录 `{contradicted_with: UUID, jaccard_score: float, polarity_a: str, polarity_b: str}`；needs_regeneration 类型时记录 `{affected_sources: UUID[], valid_sources_ratio: float}` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 记录创建时间 |

**约束**：UNIQUE(memory_id, flag_type) WHERE resolved_at IS NULL — 同一 Flag 类型在同一记忆上至多一个活跃标记。
**索引**：
- `idx_memory_flags_active` ON `flag_type`, `memory_id` WHERE `resolved_at IS NULL` — 加速活跃 Flag 查询
- `idx_memory_flags_memory` ON `memory_id` — 按记忆查询 Flag 历史

### memory_tags（记忆标签表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id), ON DELETE CASCADE | |
| `key` | TEXT | NOT NULL | 标签键 |
| `value` | TEXT | — | 标签值 |

**索引**：`idx_memory_tags_memory` ON `memory_id`（按记忆查询标签；UNIQUE(memory_id, key, value) 由应用层保证）

---

## §2 记忆版本快照表

### memory_versions（版本快照表，用于显式回滚）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id), NOT NULL | 关联主记忆 |
| `snapshot` | JSONB | NOT NULL | 版本创建时的完整记忆快照（含 content/embedding/metadata 等全部字段） |
| `version_number` | INTEGER | NOT NULL | 对应 memories 表的 version 字段值 |
| `reason` | TEXT | — | 版本快照创建原因（update/rollback_prep/manual） |
| `created_at` | TIMESTAMPTZ | NOT NULL | 快照时间 |

**约束**：UNIQUE(memory_id, version_number) — 每条记忆的每个版本至多一个快照。

> **定位**：`memory_versions` 是显式回滚的物理基础。`memories` 表中的 `superseded_by` 链（§1）是逻辑追踪（记录 OCC 写冲突的解决历史），`memory_versions` 是物理快照（记录用户可回滚的检查点）。两者互补：链回答「发生过什么」，快照表回答「能回到哪里」。

---

## §3 双副本存储

### witness_anchor（见证锚定主副本）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `memory_id` | UUID | PK, FK → memories(id) | 对应记忆 |
| `narrative_coherence_score` | FLOAT | DEFAULT 0, [0,1] | 叙事自洽度 |
| `last_calibrated_at` | TIMESTAMPTZ | — | 最后外部校准时间 |
| `calibration_count` | INTEGER | DEFAULT 0 | 累计校准次数 |
| `anchor_version` | INTEGER | DEFAULT 1 | 见证锚定版本号 |
| `overridden_by_external` | BOOLEAN | DEFAULT FALSE | 是否曾被外部校准覆盖 |

### usage_weight（使用权重影子副本）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `memory_id` | UUID | PK, FK → memories(id) | 对应记忆 |
| `usage_count` | INTEGER | DEFAULT 0 | 累计使用次数 |
| `last_used_at` | TIMESTAMPTZ | — | 最后使用时间 |
| `activation_weight` | FLOAT | DEFAULT 0, [0,1] | 当前激活权重 |
| `use_load_retrieval` | FLOAT | DEFAULT 0 | 检索级负载系数 |
| `use_load_verification` | FLOAT | DEFAULT 0 | 验证级负载系数 |
| `use_load_contribution` | FLOAT | DEFAULT 0 | 贡献级负载系数 |
| `use_load_simulation` | FLOAT | DEFAULT 0 | 模拟级负载系数 |
| `use_load_implicit` | FLOAT | DEFAULT 0 | 内隐级负载系数 |
| `exploration_confidence` | FLOAT | DEFAULT 0, [0,1] | 探索置信度（探索产物专用） |
| `suspect_flag` | BOOLEAN | DEFAULT FALSE | 存疑标记（差异检验未通过） |

### journal_buffer（写入暂存区）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `session_id` | TEXT | NOT NULL | 所属会话 ID（用于分批回放） |
| `raw_content` | JSONB | NOT NULL | 原始对话轮次（role + content），不经过任何过滤/改写 |
| `digest_status` | TEXT | NOT NULL DEFAULT 'pending' | pending / processing / completed / failed |
| `digest_result` | TEXT | — | LLM 消化后的摘要（digest_status=completed 时填充） |
| `retry_count` | INTEGER | DEFAULT 0 | 消化失败重试次数 |
| `error_message` | TEXT | — | 消化失败原因 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 写入时间 |
| `processed_at` | TIMESTAMPTZ | — | 消化完成时间 |

**索引**：INDEX `idx_journal_session` ON `session_id` — 按会话查询暂存条目。
INDEX `idx_journal_status` ON `digest_status` — 按处理状态过滤。

> **定位**：`journal_buffer` 是对话写入与持久存储之间的暂存隔离层。写入流程：原始对话 → journal_buffer（立即写入）→ 触发 digest（LLM 调用）→ digest_result 写入后，由后台管线推进至 `memories` 表。digest 失败时 journal 条目保留可重试，不丢失原始内容。此隔离确保：写入路径不阻塞对话流程（先入 journal 即返回成功），消化路径不与主检索路径争抢资源。

### memory_blocks（上下文块表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `label` | TEXT | NOT NULL, UNIQUE | 块名称（如 `system/persona`、`human/preferences`） |
| `content` | TEXT | NOT NULL | 块内容 |
| `token_limit` | INTEGER | DEFAULT 4096 | 该块的 token 上限 |
| `read_only` | BOOLEAN | DEFAULT FALSE | 禁止 Agent 运行时修改 |
| `source` | TEXT | NOT NULL | system / user / tool / memory |
| `rendering_mode` | TEXT | DEFAULT 'full' | full / summary / tree |
| `priority` | INTEGER | DEFAULT 0 | 块优先级（编译时按优先级降序排列） |
| `version` | INTEGER | DEFAULT 1 | 块版本号，修改时递增 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

### memory_block_versions（上下文块版本表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `block_id` | UUID | FK → memory_blocks(id) | 所属上下文块 |
| `content` | TEXT | NOT NULL | 该版本的内容 |
| `version` | INTEGER | NOT NULL | 版本号 |
| `reason` | TEXT | — | 修改原因 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**索引**：INDEX `idx_block_versions` ON `block_id`, `version` DESC

---

## §4 使用事件表

### usage_events（使用事件总线持久化）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | BIGSERIAL | PK | |
| `event_type` | TEXT | NOT NULL | 枚举见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 事件类型枚举 |
| `source_layer` | TEXT | NOT NULL | 来源层 |
| `memory_id` | UUID | FK → memories(id) | 关联记忆 |
| `context` | JSONB | — | 事件上下文 |
| `severity` | INTEGER | DEFAULT 0, [0,9] | 事件严重级别 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `ttl` | INTERVAL | — | 生存时间，到期自动清理 |

**分区**：按 `created_at` 时间分区（月/季），过期分区自动归档或删除。

**建议索引**：`(memory_id, created_at)` — 遗忘调度器的 `WHERE memory_id = X AND created_at > NOW - 30d` 查询依赖此索引

---

## §5 调度与状态表

### sublimation_queue（升华队列）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id) | 被升华的记忆 |
| `stage` | TEXT | NOT NULL | raw / item / strategy / behavior |
| `status` | TEXT | NOT NULL | pending / processing / completed / failed / awaiting_approval |
| `output` | TEXT | — | 升华产物 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `completed_at` | TIMESTAMPTZ | — | |

**索引**：`idx_sublimation_status` ON `status`（空闲调度器按状态轮询）；`idx_sublimation_memory` ON `memory_id`

### forgetting_queue（遗忘队列）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id) | 被遗忘候选 |
| `forgetting_score` | FLOAT | NOT NULL, [0,1] | 遗忘得分 |
| `reason` | TEXT | — | 触发原因 |
| `status` | TEXT | NOT NULL | pending_archive / archived / revoked |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

## §6 审计表

### audit_log（审计日志）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | BIGSERIAL | PK | |
| `timestamp` | TIMESTAMPTZ | NOT NULL | |
| `operator` | TEXT | NOT NULL | 操作者身份 |
| `action` | TEXT | NOT NULL | 操作类型 |
| `target_type` | TEXT | — | 目标类型（memory/config/user/redline） |
| `target_id` | TEXT | — | 目标 ID |
| `content_hash` | TEXT | — | 操作内容的 SHA-256 |
| `previous_hash` | TEXT | — | 上一条审计日志的 HMAC |
| `hmac` | TEXT | NOT NULL | HMAC-SHA256 签名 |
| `details` | JSONB | — | 详细信息 |
| `redline_id` | TEXT | — | 触发的安全红线编号（如有） |

**审计链完整性**：`hmac = HMAC-SHA256(hmac_key, timestamp + operator + action + content_hash + prev_hmac)`——公式权威定义见 [threat-model.md](../security/threat-model.md) HMAC 审计链（5 项输入：时间戳/操作者/动作/内容哈希/上一条 HMAC）；`target_type`/`target_id`/`details` 等字段记录于日志正文并以 SHA256 摘要并入 `content_hash`，不单独作为链输入。字段名 `prev_hmac`（与上一条 `hmac` 同值）

---

## §7 配置表

### config（运行时配置）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `key` | TEXT | PK | 配置键 |
| `value` | TEXT | NOT NULL | 配置值 |
| `scope` | TEXT | DEFAULT 'static' | static / dynamic / override |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_by` | TEXT | — | 更新者 |

### seeds（种子锚点）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `path` | TEXT | NOT NULL, UNIQUE | `kairos://_system/seeds/{name}` |
| `seed_type` | TEXT | NOT NULL | config / identity / calibration |
| `initial_confidence` | FLOAT | NOT NULL, [0,1] | 初始置信度 |
| `current_confidence` | FLOAT | NOT NULL, [0,1] | 当前衰减后置信度 |
| `degradation_level` | FLOAT | DEFAULT 0, [0,1] | 退化程度（0=新种子，1=完全退化） |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | active / degrading / retired |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `last_reviewed_at` | TIMESTAMPTZ | — | 最近一次适配性审查时间 |
| `review_count` | INTEGER | DEFAULT 0 | 累计审查次数 |
| `bias_reset_count` | INTEGER | DEFAULT 0 | 偏置重置次数 |
| `content_snapshot` | JSONB | — | 种子内容的定稿快照 |

### sublimation_outputs（升华输出表，v0.1.0 交付）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id) | 被升华的记忆 |
| `stage` | TEXT | NOT NULL | raw / item / strategy / behavior |
| `output_type` | TEXT | NOT NULL | pattern / rule / insight / preference |
| `content` | TEXT | NOT NULL | 升华产物内容 |
| `confidence` | FLOAT | NOT NULL, [0,1] | 置信度（< SUBLIMATION_CONFIDENCE_FLOOR 不回写） |
| `status` | TEXT | NOT NULL, DEFAULT 'pending_review' | pending_review / approved / rejected / discarded |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

### memory_states（记忆状态转换跟踪表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | NOT NULL | 关联 memories.id |
| `memory_type` | TEXT | NOT NULL | 记忆过程分类（映射至 storage/knowledge/experience/task）：knowledge=语义类（semantic），experience=情景类（episodic），task=程序类（procedural）。与 `memories.memory_types` 的多重认知分类（episodic/semantic/procedural）为不同分类轴——memory_type 是存储内部的过程管理分类，memory_types 是认知模型的记忆类型标记。两者映射关系：knowledge↔semantic，experience↔episodic，task↔procedural |
| `state` | TEXT | NOT NULL | active / stale / archived（含子态 suppressed）/ superseded |
| `previous_state` | TEXT | DEFAULT '' | 转换前状态 |
| `state_changed_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `reason` | TEXT | DEFAULT '' | 转换原因 |
| `source` | TEXT | DEFAULT 'system' | 触发源 |

**约束**：无 UNIQUE 约束——支持同一记忆多次状态转换（保留完整历史）。
**索引**：INDEX(memory_id, state_changed_at) 加速历史查询

### journal_entries（升华原始轮次表，v0.1.0 交付）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `session_id` | TEXT | NOT NULL | 所属会话 |
| `role` | TEXT | NOT NULL | user / assistant / tool |
| `content` | TEXT | NOT NULL | 原始内容 |
| `source` | TEXT | — | 来源标识 |
| `platform` | TEXT | — | 平台标签 |
| `filtered` | BOOLEAN | DEFAULT FALSE | 是否被捕获门控过滤 |
| `captured_at` | TIMESTAMPTZ | NOT NULL | |
| `node_episode_index_map` | JSONB | — | 批量摄取 episode 归因映射 {memory_node_id → episode_index}（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 Episode 归因索引） |

**索引**：`idx_journal_entries_session` ON `session_id`（L1 摘要按会话回查）；`idx_journal_entries_captured` ON `captured_at`

### session_summaries（L1 会话摘要表，v0.1.0 交付）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `session_id` | TEXT | NOT NULL, UNIQUE | |
| `user_id` | TEXT | NOT NULL | |
| `summary` | TEXT | — | 会话摘要 |
| `key_decisions` | JSONB | — | 关键决策列表 |
| `entities` | JSONB | — | 提取的实体列表 |
| `heat_score` | FLOAT | DEFAULT 1.0 | 热度评分 |
| `token_count` | INTEGER | DEFAULT 0 | |
| `start_time` | TIMESTAMPTZ | — | |
| `end_time` | TIMESTAMPTZ | — | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `ttl_days` | INTEGER | DEFAULT 30 | 保留天数 |

### daily_reports（L2 日报告表，v0.1.0 交付）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `user_id` | TEXT | NOT NULL | |
| `report_date` | DATE | NOT NULL | |
| `summary` | TEXT | — | 日摘要 |
| `insights` | JSONB | — | 当日洞察列表 |
| `session_count` | INTEGER | DEFAULT 0 | 当日会话数 |
| `decision_count` | INTEGER | DEFAULT 0 | 关键决策数 |
| `heat_score` | FLOAT | DEFAULT 1.0 | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| UNIQUE(user_id, report_date) | | | |

### weekly_packs（L3 周知识包表，v0.1.0 交付）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `user_id` | TEXT | NOT NULL | |
| `week_start` | DATE | NOT NULL | |
| `patterns` | JSONB | — | 识别到的模式列表 |
| `trends` | JSONB | — | 趋势分析 |
| `key_decisions` | JSONB | — | 本周关键决策 |
| `session_ids` | TEXT[] | — | 归属于本周的会话 ID 列表（统一为本系统 session_id 类型——session_summaries/journal_entries/conversation_messages 的 session_id 均为 TEXT，保持一致） |
| `heat_score` | FLOAT | DEFAULT 1.0 | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| UNIQUE(user_id, week_start) | | | |

### user_profiles（L4 用户画像表，v0.1.0 交付）

用户画像分**静态（static）**与**动态（dynamic）**两层——静态层记录长期稳定事实（偏好、身份、特质），数据来自 L4 profile 的跨周聚合；动态层记录近期活动和当前上下文（正在进行的任务、最近对话主题），数据来自 L1→L3 增量更新。两层共享同一张表，通过 `trait_type`（static/dynamic）区分。检索时静态层权重高于动态层。

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `user_id` | TEXT | NOT NULL | 用户 ID（复合 PK 的一部分） |
| `trait_type` | TEXT | NOT NULL, DEFAULT 'dynamic' | static（长期稳定）/ dynamic（近期活动），见上文说明。复合主键：PRIMARY KEY (user_id, trait_type) |
| `preferences` | JSONB | DEFAULT '{}' | 用户偏好 |
| `traits` | JSONB | DEFAULT '{}' | 用户特征 |
| `skill_summaries` | JSONB | DEFAULT '{}' | 技能摘要 |
| `confidence` | FLOAT | DEFAULT 0.5 | 画像置信度 |
| `version` | INTEGER | DEFAULT 1 | 画像版本号 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `rl_weights` | JSONB | — | RL 权重五维配置：键为 `relevance`/`recency`/`frequency`/`user_feedback`/`trust_score`，初始化不归一化；更新管线经 Bounded Simplex Projection 强制 Σ=1（见 [rl-weight-spec.md](rl-weight-spec.md)）。`entity_boost`（默认 0.05）为配置参数，不参与五维排序，v1.1+ 激活完整加权时并入 |

### retrieval_enhancement_config（检索增强配置参数，v0.1.0 交付）

以下参数控制三信号混合检索、GSPO 聚类去重、MMR 去重三个阶段的行为。所有参数存储在 `config` 表中，key 前缀为 `kairos.retrieval`。config 表键名 = `KAIROS_*` 环境变量名去掉 `KAIROS_` 前缀后转小写点分格式（如 `KAIROS_HYBRID_SEMANTIC_WEIGHT` → `kairos.retrieval.hybrid.semantic_weight`），与 [configuration.md](../ops/configuration.md) §1 环境变量一一对应。

| 参数键 | 值类型 | 默认值 | 范围/取值 | 所属阶段 | 说明 |
|:------|:------|:------|:---------|:--------|:-----|
| `kairos.retrieval.hybrid.semantic_weight` | FLOAT | 0.50 | [0, 1] | 三信号混合检索 | 语义信号融合权重（α_s） |
| `kairos.retrieval.hybrid.bm25_weight` | FLOAT | 0.35 | [0, 1] | 三信号混合检索 | BM25 信号融合权重（α_b） |
| `kairos.retrieval.hybrid.entity_weight` | FLOAT | 0.15 | [0, 1] | 三信号混合检索 | 实体加成信号融合权重（α_e） |
| `kairos.retrieval.hybrid.candidate_pool_size` | INTEGER | 100 | [10, 500] | 三信号混合检索 | ANN 语义检索 top-K 候选池大小 |
| `kairos.retrieval.bm25.adaptive_enabled` | BOOLEAN | true | true/false | 自适应 BM25 | 自适应 BM25 参数调整总开关 |
| `kairos.retrieval.bm25.k1_base` | FLOAT | 1.2 | [0.5, 3.0] | 自适应 BM25 | k1 基值（中长查询使用） |
| `kairos.retrieval.bm25.b_base` | FLOAT | 0.75 | [0.1, 1.0] | 自适应 BM25 | b 基值（中性长度归一化） |
| `kairos.retrieval.bm25.lemmatize` | BOOLEAN | true | true/false | BM25 词形归并 | 写入/检索时的词形归并开关 |
| `kairos.retrieval.entity.boost_per_match` | FLOAT | 0.10 | [0.01, 0.50] | 实体加成 | 每个匹配实体的加成幅度 |
| `kairos.retrieval.entity.boost_max` | FLOAT | 1.50 | [1.0, 3.0] | 实体加成 | 实体加成的上限倍率 |
| `kairos.retrieval.gspo.enabled` | BOOLEAN | true | true/false | GSPO 聚类去重 | GSPO 全阶段总开关 |
| `kairos.retrieval.gspo.similarity_threshold` | FLOAT | 0.85 | [0.7, 0.99] | GSPO 聚类去重 | 聚类语义相似度阈值（余弦相似度） |
| `kairos.retrieval.gspo.cv_threshold` | FLOAT | 0.15 | [0.05, 0.50] | GSPO 聚类去重 | 组内变异系数激活阈值 |
| `kairos.retrieval.gspo.domain_diversify` | BOOLEAN | true | true/false | GSPO 域均衡 | 域均衡处理开关 |
| `kairos.retrieval.gspo.min_per_domain` | INTEGER | 1 | [1, 10] | GSPO 域均衡 | 每个域的最小代表记忆数 |
| `kairos.retrieval.gspo.min_cluster_size` | INTEGER | 2 | [2, 20] | GSPO 聚类去重 | 最小聚类规模（<此值的聚类不执行压缩） |
| `kairos.retrieval.mmr.enabled` | BOOLEAN | true | true/false | MMR 去重 | MMR 去重总开关 |
| `kairos.retrieval.mmr.lambda` | FLOAT | 0.50 | [0, 1] | MMR 去重 | λ 权衡系数（查询相关性 vs 多样性） |
| `kairos.retrieval.mmr.top_k` | INTEGER | 10 | [1, 100] | MMR 去重 | MMR 贪心选择的目标返回数 |
| `kairos.retrieval.cross_encoder.enabled` | BOOLEAN | false | true/false | Cross-encoder 重排 | Cross-encoder 重排序开关（默认关闭需显式启用） |
| `kairos.retrieval.cross_encoder.model` | TEXT | ""（空=不启用） | 模型路径或名称 | Cross-encoder 重排 | Cross-encoder 模型标识（空字符串表示未配置模型） |
| `kairos.retrieval.cross_encoder.top_k` | INTEGER | 20 | [5, 100] | Cross-encoder 重排 | 送入 Cross-encoder 的候选数 |
| `kairos.retrieval.cross_encoder.batch_size` | INTEGER | 8 | [1, 64] | Cross-encoder 重排 | Cross-encoder 推理批次大小 |
| `kairos.retrieval.graph_distance.max_hops` | INTEGER | 3 | [1, 10] | 图谱距离重排 | 图谱 BFS 最大跳数 |

**约束**：(a) `hybrid.semantic_weight + hybrid.bm25_weight + hybrid.entity_weight` 必须等于 1.0——系统启动时校验，不满足则拒绝启动并记录告警；(b) `gspo.similarity_threshold` 必须大于 `mmr.lambda` 中隐含的语义判定阈值（即聚类判同应比 MMR 的去重更严格，否则聚类过度合并），校验为：若 `gspo.similarity_threshold < 0.7` 且 `mmr.enabled = true`，系统在启动时输出警告日志提示「GSPO 阈值过低可能导致过度聚类」；(c) `cross_encoder.top_k` 应当 ≤ `hybrid.candidate_pool_size - gspo 预期压缩后规模`的 2 倍——若 `cross_encoder.enabled = true` 且 `cross_encoder.top_k > hybrid.candidate_pool_size`，系统启动时自动将 `cross_encoder.top_k` 截断至 `hybrid.candidate_pool_size`，并输出调整日志。

## §8 扩展表

### 8.1 conversation_messages（对话消息持久化）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `session_id` | TEXT | NOT NULL | Hermes 会话 ID |
| `role` | TEXT | NOT NULL | user / assistant / tool |
| `content` | TEXT | — | 消息内容 |
| `parts` | JSONB | — | 多模态 Part 数组（TextPart/ImagePart/ToolPart 等，schema 见 [api-spec.md](api-spec.md) §18.2） |
| `tool_call_id` | TEXT | — | 工具调用 ID |
| `tool_calls` | JSONB | — | 工具调用参数 |
| `tool_name` | TEXT | — | 工具名 |
| `timestamp` | FLOAT | NOT NULL | 时间戳 |
| `token_count` | INTEGER | — | Token 计数 |
| `finish_reason` | TEXT | — | 完成原因 |
| `reasoning` | TEXT | — | 推理过程 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

**索引**：
- `idx_conv_session` ON `session_id`（支持按会话查询）
- `idx_conv_timestamp` ON `timestamp`

### 8.2 entities（实体知识图谱）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `user_id` | TEXT | NOT NULL | |
| `name` | TEXT | NOT NULL | 实体名称 |
| `type` | TEXT | DEFAULT 'concept' | project / people / concept / tool |
| `description` | TEXT | — | 实体描述 |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 语义向量。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3，原生 1024 维线性投影至 1536），DDL 以 1536 为准 |
| `metadata` | JSONB | — | 扩展元数据 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| UNIQUE(user_id, name) | | | |

### 8.3 memory_entities（记忆-实体关联）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id) | 关联记忆 |
| `entity_id` | BIGINT | FK → entities(id) | 关联实体 |
| `relation` | TEXT | DEFAULT 'mentions' | 关系类型 |
| `valid_from` | TIMESTAMPTZ | — | 关系有效起始（NULL=不绑定时间） |
| `valid_to` | TIMESTAMPTZ | — | 关系有效截止（NULL=当前有效） |
| `superseded_by` | BIGINT | FK → memory_entities(id) | 被替代关系（自引用）。**RC-04 修正**：此列此前误标为 UUID，与自引用目标 `memory_entities.id`（BIGSERIAL）类型不匹配，无法建立外键 |
| UNIQUE(memory_id, entity_id, valid_from) | | | 时序版本化：同一 memory↔entity 对可随时间有效多条关系 |

### 8.4 memory_chunks（长文本分块索引）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id), ON DELETE CASCADE | 父记忆 |
| `chunk_index` | INTEGER | NOT NULL | 块序号 |
| `content` | TEXT | NOT NULL | 块内容 |
| `text_hash` | TEXT | — | SHA256(content)，用于差分同步比较 |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 语义向量。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3，原生 1024 维线性投影至 1536），DDL 以 1536 为准 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| UNIQUE(memory_id, chunk_index) | | | |

### 8.5 sync_queue（端云同步队列）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id) | 待同步记忆 |
| `operation` | TEXT | NOT NULL | create / update / delete |
| `sync_direction` | TEXT | NOT NULL | upload / download |
| `sync_state` | TEXT | NOT NULL | pending / synced / conflict |
| `local_version` | INTEGER | NOT NULL | 本地版本号 |
| `remote_version` | INTEGER | — | 远端版本号 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `synced_at` | TIMESTAMPTZ | — | |

### 8.6 fact_freshness（事实新鲜度元数据）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `subject_type` | TEXT | NOT NULL | 'memory' |
| `subject_id` | UUID | NOT NULL | 关联记忆 ID（FK → memories.id） |
| `fact_key` | TEXT | NOT NULL | 归一化事实键 |
| `truth_type` | TEXT | NOT NULL | factual / project_fact / environment_fact |
| `validator_kind` | TEXT | DEFAULT 'none' | none / file_exists / command / http / manual |
| `validator_spec` | JSONB | — | 验证参数（命令/URL等） |
| `ttl_days` | INTEGER | DEFAULT 0 | TTL 天数 |
| `last_checked_at` | TIMESTAMPTZ | — | 最后检查时间 |
| `valid_until` | TIMESTAMPTZ | — | 有效期截止 |
| `status` | TEXT | DEFAULT 'needs_live_check' | current / expired / stale / superseded / needs_live_check |
| `stale_reason` | TEXT | DEFAULT '' | |
| `superseded_by` | UUID | — | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

**索引**：`idx_fact_freshness_subject` ON `subject_type`, `subject_id`（按记忆查询事实新鲜度）

### 8.7 proactive_topics（主动话题调度表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `topic` | TEXT | NOT NULL | 话题描述 |
| `summary` | TEXT | — | 话题摘要 |
| `priority` | FLOAT | DEFAULT 0 | 话题优先级，[0,1] 区间数值越大优先级越高（高优先级判据 ≥ 0.7——on_turn_start hook 注入阈值，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 主动话题生成器；勘误：原 INTEGER 0=最高 口径与架构 ≥0.7 阈值互斥，统一为 FLOAT） |
| `evidence_count` | INTEGER | DEFAULT 0 | 累积证据数 |
| `related_ids` | UUID[] | — | 关联记忆 ID 列表 |
| `status` | TEXT | DEFAULT 'pending' | pending / acknowledged / processed / expired |
| `acknowledged` | BOOLEAN | DEFAULT FALSE | 是否已被处理 |
| `generated_at` | TIMESTAMPTZ | NOT NULL | 生成时间 |
| `acknowledged_at` | TIMESTAMPTZ | — | 处理时间 |

---

### 8.8 procedural_playbooks（过程知识 Playbook）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | TEXT | PK | `pb_{uuid}` |
| `scope_id` | TEXT | NOT NULL | |
| `shared_scope_id` | TEXT | — | |
| `task_class` | TEXT | NOT NULL | |
| `title` | TEXT | NOT NULL | |
| `trigger` | TEXT | — | |
| `goal` | TEXT | — | |
| `preconditions` | JSONB | DEFAULT '[]' | |
| `steps` | JSONB | NOT NULL | `[{number, capability_class, action, evidence_required, why, previous_mistakes}]` |
| `pitfalls` | JSONB | DEFAULT '[]' | |
| `verification` | JSONB | DEFAULT '[]' | |
| `cleanup` | JSONB | DEFAULT '[]' | |
| `evidence_anchors` | JSONB | DEFAULT '[]' | |
| `related_skills` | JSONB | DEFAULT '[]' | |
| `environment_constraints` | JSONB | DEFAULT '{}' | |
| `reuse_policy` | JSONB | DEFAULT '{}' | |
| `status` | TEXT | DEFAULT 'candidate' | candidate / needs_review / reviewed / promoted / superseded |
| `confidence` | FLOAT | DEFAULT 0.5 | |
| `success_count` | INTEGER | DEFAULT 0 | |
| `failure_count` | INTEGER | DEFAULT 0 | |
| `stale_count` | INTEGER | DEFAULT 0 | |
| `created_from_episode_id` | TEXT | — | |
| `superseded_by` | TEXT | — | 被替代的新 Playbook ID（本表 id 为 TEXT `pb_{uuid}`，保持一致；RC-04 同类类型错配已在此修正） |
| `last_used_at` | TIMESTAMPTZ | — | |
| `last_verified_at` | TIMESTAMPTZ | — | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |
| `metadata` | JSONB | DEFAULT '{}' | |

**索引**：`idx_playbooks_task_class` ON `task_class`；`idx_playbooks_status` ON `status`（按任务类/状态查询）

### 8.9 procedural_playbooks_fts（Playbook 全文索引——FTS5 虚拟表）

> **性质**：与 `memories_fts` 同为 **FTS5 contentless-external 虚拟表**（SQLite 独有，PostgreSQL 无等价物）——仅存倒排索引，原文通过 `playbook_id` 关联 `procedural_playbooks`。DDL 与同步触发器参照 `memories_fts` 节（§11）与 [schema-slice.sql](schema-slice.sql)；`title/trigger/goal/preconditions/steps/pitfalls/verification` 为被索引文本列。

| 列名 | 类型 | 说明 |
|:----|:-----|:-----|
| `playbook_id` | TEXT | FK → procedural_playbooks(id)（content 外部表关联键） |
| `title` | TEXT | |
| `trigger` | TEXT | |
| `goal` | TEXT | |
| `preconditions` | TEXT | |
| `steps` | TEXT | |
| `pitfalls` | TEXT | |
| `verification` | TEXT | |

### 8.10 playbook_versions（Playbook 版本历史）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | TEXT | PK | |
| `playbook_id` | TEXT | FK → procedural_playbooks(id) | |
| `version` | INTEGER | NOT NULL | |
| `change_type` | TEXT | NOT NULL | create / review / promote / supersede / feedback |
| `change_reason` | TEXT | — | |
| `snapshot` | JSONB | — | 完整 playbook 快照 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

**约束**：UNIQUE(playbook_id, version) — 同 Playbook 的版本号不可重复（与 skill_versions 的 UNIQUE(skill_id, version) 对齐）。

### 8.11 entity_communities（实体社区）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `community_label` | TEXT | NOT NULL | 社区标签（自动生成） |
| `member_entity_ids` | BIGINT[] | NOT NULL | 成员实体 ID 列表（本系统 `entities.id` 为 BIGSERIAL/BIGINT——社区检测的成员即本系统实体表，保持一致；RC-04 同类类型错配已在此修正） |
| `summary` | TEXT | — | 社区摘要（LLM 生成） |
| `detection_algorithm` | TEXT | DEFAULT 'label_propagation' | label_propagation / leiden / manual |
| `confidence` | FLOAT | DEFAULT 0.5 | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

**约束与索引**：UNIQUE(community_label)；`idx_entity_communities_label` ON `community_label`。

---

### 8.12 知识管理扩展表

> **定位**：技能管理系统（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 技能管理系统）、三链路知识图谱（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 三链路知识图谱）和四层记忆质量层次（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2）的数据承载表。以下表均以 PostgreSQL + pgvector 为设计基准。

### 8.13 skills（技能注册表）

技能管理系统的核心存储——将三级技能进化中 L3 Skills 层的结晶技能注册为一等数据实体。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | 技能全局唯一 ID |
| `name` | TEXT | NOT NULL, UNIQUE | 技能名称（如 `git-worktree-cleanup`） |
| `description` | TEXT | NOT NULL | 技能功能描述（用于语义搜索匹配） |
| `category` | TEXT | DEFAULT 'general' | 技能分类（如 devops / data-science / creative / software-development） |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 技能的语义向量——由 `name + description + category` 拼接后生成。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3） |
| `status` | TEXT | NOT NULL, DEFAULT 'experimental' | 生命周期状态：experimental / active / deprecated / superseded / retired / archived |
| `version` | INTEGER | DEFAULT 1 | 技能版本号，每次内容变更递增 |
| `source_playbook_id` | TEXT | FK → procedural_playbooks(id) | 产出此技能的源 Playbook（三级进化 L2→L3 的门禁记录） |
| `source_memory_ids` | UUID[] | — | 关联的原始记忆 ID 列表（完整溯源链） |
| `usage_count` | INTEGER | DEFAULT 0 | 累计被调用次数（find_skills 命中 + 实际执行次数） |
| `success_rate` | FLOAT | DEFAULT 0, [0,1] | 成功率（success_count / usage_count） |
| `success_count` | INTEGER | DEFAULT 0 | 累计成功执行次数 |
| `failure_count` | INTEGER | DEFAULT 0 | 累计失败执行次数 |
| `last_used_at` | TIMESTAMPTZ | — | 最后被调用时间 |
| `last_validated_at` | TIMESTAMPTZ | — | 最后验证时间——Skill 关联的 Playbook 被替代时，此字段置 NULL 触发 `needs_revalidation` |
| `confidence` | FLOAT | DEFAULT 0.5, [0,1] | 综合置信度（初始 0.5；每次 success +0.03，每次 failure -0.08；下限 0.05，上限 0.99） |
| `superseded_by` | UUID | FK → skills(id) | 替代本技能的新技能 ID |
| `metadata` | JSONB | DEFAULT '{}' | 扩展元数据（如环境要求、前置条件、关联工具列表） |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 最后更新时间 |

**索引**：
- `idx_skills_name` ON `name`
- `idx_skills_status` ON `status`
- `idx_skills_category` ON `category`
- `idx_skills_embedding` 向量索引（pgvector: HNSW）
- `idx_skills_success_rate` ON `success_rate` DESC — 加速按成功率排序的检索

**约束**：
- `status` 字段 CHECK：`status IN ('experimental', 'active', 'deprecated', 'superseded', 'retired', 'archived')`
- `superseded_by` 自引用防护：写入时校验 `superseded_by ≠ id`

### 8.14 skill_versions（技能版本历史）

同 playbook_versions 的快照模式——每次技能状态变更记录完整快照，支持版本历史查询和回滚。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `skill_id` | UUID | FK → skills(id), NOT NULL | 关联技能 |
| `version` | INTEGER | NOT NULL | 对应 skills 表的 version 字段值 |
| `change_type` | TEXT | NOT NULL | 变更类型：create / activate / deprecate / supersede / retire / archive / reactivate / feedback |
| `change_reason` | TEXT | — | 变更原因描述 |
| `snapshot` | JSONB | NOT NULL | 变更时的完整技能快照（含 name/description/category/status/confidence 等全部字段） |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 快照时间 |

**约束**：UNIQUE(skill_id, version) — 每个技能版本号至多一个快照。

**索引**：INDEX `idx_skill_versions` ON `skill_id`, `version` DESC

### 8.15 causal_links（因果链路表）

三链路知识图谱 Link-3（Causal）的存储承载——独立于 memory_relations 表，专门存储方向性因果推理关系。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `source_id` | UUID | FK → memories(id), NOT NULL | 原因侧记忆 |
| `target_id` | UUID | FK → memories(id), NOT NULL | 结果侧记忆 |
| `predicate` | TEXT | NOT NULL | 因果谓词：causes / caused_by / enables / prevents。`caused_by` 是 `causes` 的逆向独立存储——支持双方向查询无需 JOIN 两次 |
| `confidence` | FLOAT | DEFAULT 0.5, [0,1] | 因果检测置信度 |
| `detection_method` | TEXT | DEFAULT 'llm' | 检测方法：llm（L1→L2 升华阶段 LLM 检测）/ manual（API 手动标注）/ rule（确定性规则检测，如程序依赖） |
| `evidence` | TEXT | — | 因果证据描述——LLM 检测时附带的原文片段；手动标注时的标注理由 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 最后更新时间 |

**约束**：UNIQUE(source_id, target_id, predicate) — 同一对记忆之间同一谓词类型至多一条因果链路。

**自引用防护**：写入时校验 `target_id ≠ source_id`，防止自引用因果记录。

**索引**：
- `idx_causal_source` ON `source_id` — 加速 `causes/enables` 正向遍历
- `idx_causal_target` ON `target_id` — 加速 `caused_by` 逆向回溯
- `idx_causal_predicate` ON `predicate` — 按谓词类型过滤

> **因果图遍历**：使用 PostgreSQL 递归 CTE（WITH RECURSIVE）实现深度受限的因果链查询——`causal_chain(source_id, max_depth, direction)`：direction='forward' 沿 causes/enables 正向遍历，direction='backward' 沿 caused_by 逆向回溯，默认 max_depth=3。

### 8.16 memory_semantic_knn（语义近邻预计算表）

三链路知识图谱 Link-2（Semantic kNN）的存储承载——为每条记忆预计算余弦相似度最高的 k 条近邻，将昂贵的全库 kNN 从检索热路径移至后台索引维护。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id), NOT NULL | 源记忆 |
| `neighbor_id` | UUID | FK → memories(id), NOT NULL | 近邻记忆 |
| `cosine_similarity` | FLOAT | NOT NULL, [0,1] | 余弦相似度（embedding 向量计算） |
| `knn_rank` | INTEGER | NOT NULL, [1,k] | 近邻排名（1=最相似） |
| `refreshed_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 该近邻边最近一次重算时间 |

**约束**：
- UNIQUE(memory_id, neighbor_id) — 同一对记忆至多一条近邻边
- CHECK(memory_id ≠ neighbor_id) — 防止自引用近邻
- CHECK(knn_rank ≤ `KAIROS_KNN_K`，默认 k=10) — 排名上限受配置约束

**索引**：
- `idx_knn_memory` ON `memory_id` — 加速「某记忆的所有近邻」查询
- `idx_knn_neighbor_reverse` ON `neighbor_id` — 加速「哪些记忆以该记忆为近邻」查询
- `idx_knn_refreshed` ON `refreshed_at` — 加速后台刷新任务扫描陈旧记录

> **增量更新说明**：新记忆写入时触发全库 kNN 计算，写入本表（最多 k 条记录）。Deep 模式维护任务周期性全量重算（周频）。当日新增记忆数超过 `KAIROS_KNN_INCREMENTAL_THRESHOLD`（默认 100）时，仅对受影响记录做局部重算（该记忆的近邻 + 所有 `neighbor_id = 该记忆` 的行），非全量。

---

### 8.17 v0.1.0 功能承载表

以下四张表为 v0.1.0 新增功能的持久化承载——QueryAnalyzer 查询缓存、时间桶覆盖统计、防抖任务注册、以及自动过期推断日志。

### 8.18 query_analysis_cache（查询分析缓存表）

QueryAnalyzer（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.1）的结构化查询描述符缓存。相同查询在短时间窗口内复用缓存结果，避免重复解析。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `cache_key` | TEXT | NOT NULL, UNIQUE | `SHA256(raw_query + user_id)` |
| `raw_query` | TEXT | NOT NULL | 原始查询文本 |
| `user_id` | TEXT | NOT NULL | 查询发起用户 |
| `intent_type` | TEXT | — | factual_lookup / temporal_query / exploratory_browse / decision_trace / instructional / general |
| `intent_confidence` | FLOAT | — | 意图分类置信度 [0,1] |
| `entities` | JSONB | — | 提取的实体列表 `[{text, type, entity_id, confidence}]` |
| `temporal_constraint` | JSONB | — | 时间约束 `{type, start, end, raw_expression}`，无约束时为 NULL |
| `full_descriptor` | JSONB | NOT NULL | 完整结构化查询描述符（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.1 定义） |
| `hit_count` | INTEGER | DEFAULT 1 | 缓存命中次数 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `expires_at` | TIMESTAMPTZ | NOT NULL | 缓存过期时间（created_at + KAIROS_QUERY_ANALYSIS_CACHE_TTL） |

**索引**：`idx_query_cache_expires` ON `expires_at`（加速过期清理）。

### 8.19 query_time_buckets（时间桶覆盖统计表）

时间覆盖均匀采样（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.1）的时间桶分配与统计记录。每次检索的桶分配结果写入此表，供元认知层监测时间覆盖度。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `retrieval_id` | TEXT | NOT NULL | 检索操作唯一 ID（对应使用事件总线中的 `retrieval_id`） |
| `user_id` | TEXT | NOT NULL | |
| `query_hash` | TEXT | NOT NULL | `SHA256(raw_query)` |
| `bucket_index` | INTEGER | NOT NULL, [0,7] | 时间桶编号（0=最近24h ... 7=6个月以上） |
| `bucket_range_start` | TIMESTAMPTZ | NOT NULL | 桶的时间范围起始 |
| `bucket_range_end` | TIMESTAMPTZ | — | 桶的时间范围结束（Bucket 7 为 NULL=∞） |
| `candidate_count` | INTEGER | DEFAULT 0 | 该桶在候选池中的候选记忆数 |
| `selected_count` | INTEGER | DEFAULT 0 | 该桶被选中为入口点的记忆数 |
| `is_empty` | BOOLEAN | DEFAULT FALSE | 该桶是否为空（无候选记忆） |
| `top_score` | FLOAT | — | 该桶内最高检索得分 |
| `second_score` | FLOAT | — | 该桶内第二名检索得分（用于额外入口点分配判断） |
| `is_constrained` | BOOLEAN | DEFAULT FALSE | 是否因 QueryAnalyzer 时间约束而缩限 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**索引**：
- `idx_time_buckets_retrieval` ON `retrieval_id`
- `idx_time_buckets_user_created` ON `user_id`, `created_at`（加速用户维度的时间覆盖趋势查询）
- `idx_time_buckets_empty` ON `is_empty` WHERE `is_empty = TRUE`（加速空桶率监测）

**元认知层查询示例**（空桶率监测）：
```sql
SELECT
  DATE_TRUNC('hour', created_at) AS hour,
  COUNT(*) AS total_retrievals,
  SUM(CASE WHEN is_empty THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS empty_bucket_rate
FROM query_time_buckets
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour
HAVING SUM(CASE WHEN is_empty THEN 1 ELSE 0 END) * 1.0 / COUNT(*) > 0.5;
```

### 8.20 debounced_tasks（防抖任务注册表）

防抖反射执行器（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.1）的任务注册与去重记录。同一 `(thread_id, task_type)` 的新提交自动取消旧任务。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `thread_id` | TEXT | NOT NULL | 提交任务的对话线程 ID |
| `task_type` | TEXT | NOT NULL | sublimation_trigger / forgetting_scan / entity_extraction / maintenance_light / proactive_topic_gen / latent_reevaluation |
| `task_chain_id` | UUID | NOT NULL | 任务链 ID——同一 `(thread_id, task_type)` 的所有提交/取消/执行共享同一 chain_id |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | pending / delayed / cancelled / executing / completed / failed |
| `after_seconds` | INTEGER | NOT NULL | 延迟执行秒数（默认 3） |
| `scheduled_at` | TIMESTAMPTZ | NOT NULL | 计划执行时间（created_at + after_seconds） |
| `executed_at` | TIMESTAMPTZ | — | 实际执行时间 |
| `cancelled_at` | TIMESTAMPTZ | — | 取消时间（status=cancelled 时设置） |
| `cancel_reason` | TEXT | — | 取消原因（superseded_by_new / timeout / manual / system_shutdown） |
| `superseded_by` | UUID | — | 被哪个新任务取代（FK → debounced_tasks.id） |
| `chain_position` | INTEGER | DEFAULT 1 | 在任务链中的位置序号（1=首次提交，2=第一次替换...） |
| `task_payload` | JSONB | — | 任务负载（任务类型特定的参数） |
| `error_message` | TEXT | — | 执行失败时的错误信息 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**索引**：
- `idx_debounced_lookup` ON `thread_id`, `task_type`, `status`（加速去重检查——WHERE thread_id=X AND task_type=Y AND status IN ('pending','delayed')）
- `idx_debounced_chain` ON `task_chain_id`（加速任务链历史查询）
- `idx_debounced_scheduled` ON `scheduled_at` WHERE `status IN ('pending','delayed')`（加速延迟执行轮询）

**唯一约束（软）**：同一时间点，同一 `(thread_id, task_type)` 最多一条 `status IN ('pending', 'delayed')` 的记录（应用层保证，非 DB 硬约束——因替换操作涉及旧记录的取消而非软删，唯一约束会破坏链式追溯）。

### 8.21 freshness_inference_log（自动过期推断日志表）

freshness.py（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2）的自动过期推断记录。每次推断扫描的结果写入此表，供推断质量监控和审计。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | NOT NULL | 被推断的记忆 ID（FK → memories.id） |
| `inferred_expires_at` | TIMESTAMPTZ | NOT NULL | 推断的过期时间 |
| `inference_rule` | TEXT | NOT NULL | 使用的推断规则（env_idle / ondemand_idle / distilled_idle / linear_extrapolation / skipped_structure / skipped_identity / skipped_temporary） |
| `inference_params` | JSONB | NOT NULL | 推断参数快照（如 `{multiplier: 1.5, idle_days: 45}`） |
| `last_access_at` | TIMESTAMPTZ | — | 推断时的 last_access_at 值 |
| `action_taken` | TEXT | — | expired_to_stale / near_expiry_marked / no_action / archived |
| `previous_status` | TEXT | — | 推断前的记忆 status |
| `new_status` | TEXT | — | 推断后的记忆 status |
| `is_false_positive` | BOOLEAN | DEFAULT FALSE | 是否事后被标记为假阳性（外部校准反转） |
| `false_positive_detected_at` | TIMESTAMPTZ | — | 假阳性确认时间 |
| `false_positive_reason` | TEXT | — | 假阳性原因（如 "user_explicit_access" / "calibration_reversal"） |
| `scan_batch_id` | UUID | NOT NULL | 所属扫描批次 ID（一次 Light 模式扫描的批次标识） |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**索引**：
- `idx_inference_memory` ON `memory_id`, `created_at`（加速按记忆查询推断历史）
- `idx_inference_batch` ON `scan_batch_id`（加速批次级回滚或审计）
- `idx_inference_false_positive` ON `is_false_positive` WHERE `is_false_positive = TRUE`（加速假阳性率监控）
- `idx_inference_action` ON `action_taken`, `created_at`（加速按动作类型统计）

**假阳性率监控查询**（元认知层使用）：
```sql
SELECT
  DATE_TRUNC('day', created_at) AS day,
  COUNT(*) AS total_inferences,
  SUM(CASE WHEN is_false_positive THEN 1 ELSE 0 END) AS false_positives,
  SUM(CASE WHEN is_false_positive THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS false_positive_rate
FROM freshness_inference_log
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY day
HAVING SUM(CASE WHEN is_false_positive THEN 1 ELSE 0 END) * 1.0 / COUNT(*) > 0.15;
```

---

### 8.22 image_blobs（图片二进制存储表）

架构 §7.3i（详细设计见 [api-spec.md](api-spec.md) §18.2）多模态 Part 接口的图片存储载体——data URI 图片解码后以二进制 BLOB 存入本表，原始 data URI 保留在 `memories.content` 的 ImagePart 中作为溯源引用。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id), NOT NULL | 关联记忆 |
| `blob` | BYTEA | NOT NULL | 图片二进制数据（data URI 解码后存储） |
| `mime_type` | TEXT | NOT NULL | MIME 类型（png/jpeg/webp/gif/svg+xml 白名单） |
| `width` | INTEGER | — | 图片宽度（像素） |
| `height` | INTEGER | — | 图片高度（像素） |
| `alt_text` | TEXT | — | 无障碍替代文本 |
| `size_bytes` | INTEGER | NOT NULL | 图片字节数 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 记录创建时间 |

**索引**：
- `idx_image_blobs_memory` ON `memory_id`（加速按记忆查询图片）

---

## §9 解决方案谱系与知识灭绝

### solution_branches（解决方案分支表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | 分支全局唯一 ID |
| `root_memory_id` | UUID | FK → memories(id) | 所属原始记忆 ID |
| `branch_name` | TEXT | NOT NULL | 分支名称（如 concise / detailed / step_by_step） |
| `context_signature` | TEXT | — | 触发此分支的上下文特征（哈希或摘要） |
| `usage_count` | INTEGER | DEFAULT 0 | 分支被检索次数 |
| `last_used_at` | TIMESTAMPTZ | — | 分支最后使用时间 |
| `status` | TEXT | DEFAULT 'active' | active / dormant（休眠）/ merged（已合并） |
| `merged_into` | UUID | — | 合并目标分支 ID |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**约束**：UNIQUE(root_memory_id, branch_name)

**索引**：`idx_solution_branches_name` ON `branch_name`；`idx_solution_branches_root` ON `root_memory_id`

### extinction_fossils（知识化石表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `original_memory_id` | UUID | FK → memories(id) | 原记忆 ID（保留关联） |
| `content_hash` | TEXT | NOT NULL | 原始内容的 SHA-256 哈希（替代原文） |
| `path` | TEXT | NOT NULL | 原路径（保留用于拓扑恢复） |
| `extinct_at` | TIMESTAMPTZ | NOT NULL | 灭绝时间 |
| `extinct_reason` | TEXT | NOT NULL | 灭绝原因（外部环境变更描述） |
| `restore_condition` | TEXT | — | 恢复条件描述（如「pgvector 版本 >= 0.7.0」） |
| `related_fossil_ids` | UUID[] | — | 关联化石 ID 列表（同一灭绝事件链） |

**索引**：`idx_extinction_fossils_original` ON `original_memory_id`（恢复路径按原记忆反向定位）

## §10 注册表结构

注册表不是 SQL 表，而是由编译器维护的树形键值对空间。其逻辑结构如下：

| 根键 | 路径 | 值类型 | 写入权限 | 说明 |
|:----|:----|:------|:--------|:-----|
| HKLA | identity/agent_name | TEXT | 初始化 | Agent 显示名称 |
| HKLA | identity/agent_id | UUID | 初始化 | Agent 全局唯一 ID |
| HKLA | soul/core_tone | ENUM | 宪法修订端口 | 核心语气（professional/concise/friendly） |
| HKCU | profile/name | TEXT | 编译器 | 当前用户名称 |
| HKCU | preferences/code_style | TEXT | 编译器 | 代码风格偏好 |
| HKLM | hardware/cpu/cores | INTEGER | 系统 | CPU 核心数 |
| HKLM | network/status | ENUM | 系统 | 网络状态（online/offline/restricted） |
| HKCS | current_task/id | UUID | 编译器 | 当前任务 ID |
| HKCS | current_task/phase | TEXT | 编译器 | 当前任务阶段 |
---

## §11 P3 基础设施表（v0.1.0 交付）

> **定位**：以下七张表为架构文档 P3-20 ~ P3-25 与 P3-05 的数据承载——覆盖 Schema 版本管理、断点续训检查点、PreparedStatementCache 命中率监测、FTS5 全文索引（memories_fts / skills_fts）、Permission ACL 权限控制、内部密钥表（api_keys，对应安全规格 [security-specification.md](../security/security-specification.md) §2.1）。所有表以 SQLite（轻量模式）为设计基准，PostgreSQL（标准模式）等价替换对应类型（**例外：FTS5 全文索引为 SQLite 独有虚拟表，PostgreSQL 无等价物，标准模式改用 pg_bigm / zhparser，见 `memories_fts` / `skills_fts` 节说明**）。

### schema_version（Schema 版本号管理）

架构 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-23 的前向版本保护机制的数据承载——记录当前数据库的 schema 版本号，启动时与编译进二进制的版本比较。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `version` | INTEGER | PK | 当前 schema 版本号（单调递增） |
| `applied_at` | TIMESTAMPTZ | NOT NULL | 迁移脚本执行时间 |
| `migration_name` | TEXT | NOT NULL | 迁移脚本名称（如 `003_add_quality_tier.sql`） |
| `checksum` | TEXT | NOT NULL | 迁移脚本的 SHA-256 校验和 |

**约束**：单行表——始终只有一条记录。`INSERT` 新版本时自动替换旧记录。

### training_checkpoints（断点续训检查点）

架构 [detailed-design.md](detailed-design.md) §10.5 断点续训机制的数据承载——记录长时间计算任务的进度快照，支持故障后恢复。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `task_type` | TEXT | NOT NULL | 任务类型：rl_weight_optimizer / sublimation_pipeline / entity_extraction / maintenance_deep |
| `task_id` | TEXT | NOT NULL | 任务实例唯一 ID（如 `sublimation_2026-07-27_batch_3`） |
| `checkpoint_index` | INTEGER | NOT NULL | 检查点序号（同一任务内递增，从 1 开始） |
| `progress_cursor` | JSONB | NOT NULL | 进度游标：`{completed_steps: N, processed_memory_ids: [...], current_stage: "L2"}` |
| `state_snapshot` | JSONB | — | 中间状态快照（任务类型特定——RL 权重向量、蒸馏中间产物等） |
| `task_metadata` | JSONB | NOT NULL | 任务元数据：`{started_at, budget_consumed, total_steps}` |
| `checksum` | TEXT | NOT NULL | `state_snapshot` 的 SHA-256 校验和（恢复时验证完整性） |
| `created_at` | TIMESTAMPTZ | NOT NULL | 检查点写入时间 |
| `is_valid` | BOOLEAN | DEFAULT TRUE | 检查点是否有效（校验失败时标记 FALSE） |

**约束**：每 `(task_type, task_id)` 保留最近 `KAIROS_CHECKPOINT_MAX_PER_TASK`（默认 3）条记录——写入新检查点时，若该任务已有 ≥3 条检查点且 `checkpoint_index` 最大者 `is_valid=true`，则覆盖最旧的检查点。

**索引**：`idx_checkpoints_task` ON `task_type`, `task_id`, `checkpoint_index` DESC

### stmt_cache_metrics（PreparedStatementCache 命中率日志）

架构 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-22 PreparedStatementCache 的命中率监测数据承载。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | BIGSERIAL | PK | |
| `connection_id` | TEXT | NOT NULL | 数据库连接标识 |
| `sample_time` | TIMESTAMPTZ | NOT NULL | 采样时间 |
| `hits` | INTEGER | NOT NULL | 采样周期内缓存命中次数 |
| `misses` | INTEGER | NOT NULL | 采样周期内缓存未命中次数 |
| `cache_size` | INTEGER | NOT NULL | 采样时的当前缓存条目数 |
| `evictions` | INTEGER | DEFAULT 0 | 采样周期内 LRU 逐出次数 |
| `hit_rate` | FLOAT | NOT NULL, [0,1] | hits / (hits + misses) |

**索引**：`idx_stmt_metrics_time` ON `sample_time` DESC（加速趋势查询）。

**保留策略**：TTL 7 天——`sample_time < NOW() - 7 days` 的记录由后台维护引擎 Light 模式自动清理。

> **FTS5 无 PostgreSQL 等价物（决策 D-12）**：FTS5 是 SQLite 独有虚拟表机制，PostgreSQL **没有对应的原生全文索引虚拟表**。标准模式的 BM25 全文检索（三信号融合的 0.35 权重分量）改用以下方案之一：(a) **pg_bigm**——二元分词扩展，无需维护词典，分词粒度与 jieba 较接近；(b) **zhparser**——词典驱动的中文分词，需维护词典。两者均需安装扩展。轻量模式保持零依赖（FTS5 + jieba 扩展）。注意：BM25 打分公式在两模式下存在差异，三信号融合的 0.35 权重需在两种模式下**分别标定**。

### memories_fts（记忆内容全文索引——FTS5 contentless-external）

架构 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-21 FTS5 contentless-external 模式的全文索引表——仅存储倒排索引（token 位置），原始内容通过 `rowid` 关联 `memories` 表。

| 列名 | 类型 | 说明 |
|:----|:----|:-----|
| `content` | — (FTS5 虚拟列) | 被索引的文本内容（tokenized）——不存储原文，仅存储倒排索引 |
| `content_summary` | — (FTS5 虚拟列) | 记忆摘要的索引 |
| `path` | — (FTS5 虚拟列) | 路径前缀的索引（支持 `path:kairos/users/*` 列过滤查询） |

**DDL（SQLite）**：
```sql
CREATE VIRTUAL TABLE memories_fts USING fts5(
  content,
  content_summary,
  path,
  content='memories',
  content_rowid='rowid',
  tokenize='unicode61'
);
```

**约束**：
- 外部内容表为 `memories`——通过 `content=` 声明关联。**FTS5 的 external content 模式不会自动同步索引**——必须显式建立三个同步触发器（AFTER INSERT / AFTER DELETE / AFTER UPDATE），可执行 DDL 见 [schema-slice.sql](schema-slice.sql) 第 14 节（对应 W2 schema 迁移直接输入）
- 中文分词通过 jieba 自定义 tokenizer 实现——在 FTS5 注册时指定 `tokenize='jieba'`（需编译 jieba tokenizer 扩展）
- 索引优化：`INSERT INTO memories_fts(memories_fts) VALUES('optimize')` 每 `KAIROS_FTS5_OPTIMIZE_INTERVAL` 秒执行一次

### skills_fts（技能全文索引——FTS5 contentless-external）

架构 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-21 FTS5 全文搜索的技能索引承载——加速 `find_skills` 的 Stage 1 语义+全文混合检索。

| 列名 | 类型 | 说明 |
|:----|:----|:-----|
| `name` | — (FTS5 虚拟列) | 技能名称索引 |
| `description` | — (FTS5 虚拟列) | 技能描述索引 |
| `category` | — (FTS5 虚拟列) | 技能分类索引 |

**DDL（SQLite）**：
```sql
CREATE VIRTUAL TABLE skills_fts USING fts5(
  name,
  description,
  category,
  content='skills',
  content_rowid='rowid',
  tokenize='unicode61'
);
```

### permission_acl（Permission ACL 权限控制表）

架构 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-25 基于 Permission ACL 的写入权限控制的数据承载——存储访问控制列表规则。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `path_prefix` | TEXT | NOT NULL | `kairos://` 路径前缀（支持 `*` / `**` 通配符） |
| `principal` | TEXT | NOT NULL | 主体标识（Agent ID / 用户 ID / `*` 通配） |
| `read_perm` | BOOLEAN | NOT NULL, DEFAULT FALSE | 读权限（检索、浏览） |
| `write_perm` | BOOLEAN | NOT NULL, DEFAULT FALSE | 写权限（创建、更新、删除、合并等） |
| `admin_perm` | BOOLEAN | NOT NULL, DEFAULT FALSE | 管理权限（修改 ACL 规则本身） |
| `policy` | TEXT | NOT NULL, DEFAULT 'whitelist' | 策略类型：whitelist（默认拒绝） / blacklist（默认允许） |
| `priority` | INTEGER | NOT NULL, DEFAULT 100 | 规则优先级（0=最高） |
| `inheritance` | TEXT | NOT NULL, DEFAULT 'none' | 继承模式：none / children / full |
| `description` | TEXT | — | 规则用途说明（审计用） |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 规则创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 规则最后修改时间 |

**约束**：
- `write_perm=true` 时 `read_perm` 自动提升为 `true`（能写必能读，应用层保证）
- `admin_perm=true` 时 `read_perm` 和 `write_perm` 均自动提升为 `true`
- `path_prefix` 不得为空字符串
- `principal` 不得为空字符串

**索引**：
- `idx_acl_lookup` ON `path_prefix`, `principal`, `priority`——加速权限检查的候选规则收集
- `idx_acl_principal` ON `principal`——加速按主体查询所有规则

**规则数量限制**：总行数 ≤ `KAIROS_ACL_MAX_RULES`（默认 500）——插入时检查，超限拒绝。

**宪法级路径保护**：`path_prefix` 为 `kairos://_system/` 或 `kairos://_audit/` 的规则，其 `admin_perm=true` 且不可修改（应用层硬编码保护）。

### api_keys（API 密钥表）

安全规格 [security-specification.md](../security/security-specification.md) §2.1 密钥生命周期与 §2.2 权限分级的数据承载——即该节所述「内部密钥表」。与 `permission_acl` 的分工：本表管 **Key 的身份与生命周期**（谁持有、什么级别、是否有效），`permission_acl` 管 **路径粒度的授权**（该主体能访问哪些路径）；鉴权时先查本表解析出 `principal`，再以 `principal` 查 ACL。

**注**：api_keys 为 v0.1.0 核心鉴权承载（对应安全规格 §2.1），非 P3 系蓝图组件，随本节点名保留（原归类注记不删，补此注即可）。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `key_id` | TEXT | PK | 密钥公开标识（如 `ak_7f3d2e`），出现在日志与 `key revoke <key-id>` 命令中，**非机密** |
| `key_hash` | TEXT | NOT NULL, UNIQUE | 加盐 PBKDF2-HMAC-SHA512 摘要（256,000 次迭代，盐取自 `KAIROS_SALT`，与安全规格 §2.1 一致）。**明文 Key 永不落库** |
| `level` | TEXT | NOT NULL | 权限级别：`admin` / `write` / `read`（对应安全规格 §2.2；与 api-spec §1 三级口径一致） |
| `principal` | TEXT | NOT NULL | 关联 `permission_acl.principal` 的主体标识，用于路径级授权 |
| `label` | TEXT | — | 人类可读用途标注（如「CI 流水线」「本地开发」），审计用 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 签发时间 |
| `expires_at` | TIMESTAMPTZ | — | 过期时间；NULL 表示长期有效 |
| `rotated_from` | TEXT | FK → `api_keys.key_id` | 轮换来源 Key；本 Key 由该 Key 轮换生成 |
| `grace_until` | TIMESTAMPTZ | — | 轮换宽限截止（旧 Key 被轮换后置为 `now() + 1 小时`，安全规格 §2.1） |
| `revoked_at` | TIMESTAMPTZ | — | 吊销时间；非 NULL 即立即失效（优先于 `grace_until`） |
| `last_used_at` | TIMESTAMPTZ | — | 最后一次成功鉴权时间（异步更新，允许秒级滞后） |

**有效性判定**（鉴权时按序短路）：
1. `revoked_at IS NOT NULL` → 拒绝（`ERR-AUTH-003`）
2. `expires_at IS NOT NULL AND expires_at < now()` → 拒绝（`ERR-AUTH-002`）
3. `grace_until IS NOT NULL AND grace_until < now()` → 拒绝（已过轮换宽限期，`ERR-AUTH-002`）
4. 否则通过，取 `level` 与 `principal` 进入 ACL 检查

**约束**：
- `level` 取值限于 `admin` / `write` / `read` 三值（CHECK 约束）
- `key_hash` 全局唯一——同一明文 Key 不得重复登记
- `rotated_from` 自引用外键，禁止成环（应用层保证：轮换链深度 ≤ 10）
- 至少保留一个未吊销的 `admin` 级 Key——吊销最后一个 admin Key 的操作必须被拒绝（防自锁）

**索引**：
- `idx_apikey_hash` UNIQUE ON `key_hash`——鉴权主查询路径（每请求一次）
- `idx_apikey_principal` ON `principal`——按主体反查其全部 Key
- `idx_apikey_active` ON `revoked_at`, `expires_at`——过期/吊销清理任务扫描

**审计联动**：`created_at` / `revoked_at` / 轮换事件均须写入审计日志（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8），审计记录中只出现 `key_id`，不得出现 `key_hash`。

---

## §12 叙事线与压缩表（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 对应）

> **定位**：以下四张表为架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 中 Saga 叙事线、双模式 Compaction、三级技能进化（world_model_rules）、及 P3-15 Prompt 依赖关系图的数据承载。

### narrative_threads（Saga 叙事线表）

架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「Saga 命名叙事线」的数据承载——将分散的记忆条目按叙事脉络串联为有命名的叙事线。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | 叙事线全局唯一 ID |
| `name` | TEXT | NOT NULL | 叙事线名称（如「PostgreSQL→CockroachDB 迁移决策」） |
| `description` | TEXT | — | 叙事线摘要（由 summarize_thread() 生成） |
| `memory_ids` | UUID[] | NOT NULL | 组成该叙事线的记忆 ID 有序列表 |
| `thread_type` | TEXT | NOT NULL, DEFAULT 'linear' | 叙事类型：linear / branching / converging |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | 状态：active / completed / archived |
| `root_memory_id` | UUID | FK → memories(id) | 叙事线的起始记忆（冗余，加速查询） |
| `latest_memory_id` | UUID | FK → memories(id) | 叙事线的最新记忆（冗余，加速查询） |
| `coherence_score` | FLOAT | DEFAULT 0.0, [0,1] | 叙事自洽度，由 summarize_thread() 计算 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `completed_at` | TIMESTAMPTZ | — | 叙事线完结时间（status=completed 时非空） |
| `metadata` | JSONB | DEFAULT '{}' | 扩展元数据（领域标签、参与者、影响范围等） |

**叙事线类型**：
- `linear`（默认）：单一线性事件序列——A→B→C
- `branching`：某点分叉——A→B→C₁, C₂
- `converging`：多分支汇聚——A₁, A₂→B→C

**与版本链的关系**：版本链追踪单条记忆的知识演化，叙事线追踪多条记忆的故事脉络。一个叙事线可包含 1 到 N 条记忆，每条记忆可属于多个叙事线。

**索引**：`idx_narrative_root` ON `root_memory_id`；`idx_narrative_status` ON `status`。

### compaction_snapshots（压缩快照表）

架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「双模式 Compaction」的数据承载——存储滑动窗口和全量压缩产生的快照。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `mode` | TEXT | NOT NULL | 压缩模式：sliding_window / all |
| `source_memory_ids` | UUID[] | NOT NULL | 被压缩的源记忆 ID 列表 |
| `compressed_content` | TEXT | NOT NULL | 压缩后的核心事实摘要 |
| `key_decisions` | JSONB | DEFAULT '[]' | 提取的关键决策及时间点 |
| `change_reasons` | JSONB | DEFAULT '[]' | 变更原因的聚合 |
| `narrative_thread_id` | UUID | FK → narrative_threads(id) | 所属叙事线 |
| `root_memory_id` | UUID | FK → memories(id) | 原版本链根节点 |
| `memory_count` | INTEGER | NOT NULL | 压缩包含的记忆数量 |
| `compressed_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `created_by` | TEXT | NOT NULL, DEFAULT 'system' | system / admin |

**约束**：CHECK(mode IN ('sliding_window', 'all'))。

**索引**：`idx_compaction_root` ON `root_memory_id`；`idx_compaction_thread` ON `narrative_thread_id`。

### world_model_rules（世界模型规则表）

架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「三级技能进化」中 L3 World Model 层的数据承载——跨任务、跨 session 的稳定认知模式规则。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `task_class` | TEXT | NOT NULL | 任务类别 |
| `trigger_condition` | TEXT | NOT NULL | 触发条件描述 |
| `action_template` | TEXT | NOT NULL | 行动模板 |
| `preconditions` | JSONB | DEFAULT '[]' | 前置条件列表 |
| `confidence` | FLOAT | DEFAULT 0.5, [0,1] | 规则置信度 |
| `evidence_count` | INTEGER | DEFAULT 0 | 累积证据计数 |
| `source_playbook_ids` | TEXT[] | — | 来源 Playbook ID 列表 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**索引**：`idx_wm_rules_task` ON `task_class`；`idx_wm_rules_confidence` ON `confidence` DESC。

**激活条件**：同一操作模式在 ≥3 个不同 task_class 下均获 success ≥5 次时，由 Deep 模式维护任务自动创建。

### prompt_dependencies（Prompt 依赖关系图表 — P3，v1.1+）

> **P3 前瞻**：架构 P3-15「Prompt 依赖关系图」的数据承载。v0.1.0 不交付，表结构预留为接口契约。

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `source_type` | TEXT | NOT NULL | 源类型：skill / playbook / directive |
| `source_id` | TEXT | NOT NULL | 源标识符 |
| `source_section` | TEXT | — | 源中引用位置 |
| `target_type` | TEXT | NOT NULL | 目标类型：soul / config |
| `target_id` | TEXT | NOT NULL | 目标标识符 |
| `target_section` | TEXT | — | 目标中引用章节 |
| `detected_at` | TIMESTAMPTZ | NOT NULL | 首次检测到依赖的时间 |
| `last_verified_at` | TIMESTAMPTZ | — | 最后一次验证依赖仍有效 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 依赖当前是否活跃 |

**约束**：UNIQUE(source_type, source_id, target_type, target_id) — 同一对源-目标至多一条活跃依赖。

---

## §13 类型映射与 DDL 基准（RC-04）

> **背景**：本文全部表定义使用 PostgreSQL 方言类型（UUID / JSONB / TIMESTAMPTZ / VECTOR / BIGSERIAL），但 v0.1.0 落地后端为 **SQLite + sqlite-vec**（[ADR-001](../governance/adr.md)、[slice-implementation-guide.md](../development/slice-implementation-guide.md) §实现基线）。此前无任何映射说明，实现者需自行猜测——本节消除该歧义，并给出可执行 DDL 的落地位置。

### 13.1 标量类型映射

| PostgreSQL（标准模式） | SQLite（轻量模式） | 存储/编码约定 | 应用层表示 |
|:----|:----|:-----|:-----|
| `UUID` | `TEXT` | RFC 4122 小写带连字符 36 字符（`8-4-4-4-12`）。**禁止**存 BLOB 或去连字符形式，否则跨模式导出不可互认 | `uuid.UUID` |
| `TEXT` | `TEXT` | UTF-8，无长度上限 | `str` |
| `INTEGER` | `INTEGER` | — | `int` |
| `BIGINT` | `INTEGER` | SQLite `INTEGER` 为 1–8 字节变长有符号整数，值域覆盖 `BIGINT` | `int` |
| `BIGSERIAL` | `INTEGER PRIMARY KEY AUTOINCREMENT` | SQLite 中即 `rowid` 别名；`AUTOINCREMENT` 保证单调不复用（审计表必需，否则删除后 ID 回绕会破坏 HMAC 链的时序假设） | `int` |
| `FLOAT` | `REAL` | IEEE-754 双精度 | `float` |
| `BOOLEAN` | `INTEGER` | 仅 `0` / `1`，附 `CHECK (col IN (0,1))`。**禁止**写入 `'true'` / `'TRUE'` 字符串 | `bool` |
| `TIMESTAMPTZ` | `TEXT` | ISO-8601 UTC 定长：`YYYY-MM-DDTHH:MM:SS.sssZ`（24 字符）。定长保证字典序 == 时间序，可直接用于 `ORDER BY` 与范围扫描 | tz-aware `datetime` |
| `DATE` | `TEXT` | ISO-8601 `YYYY-MM-DD`（10 字符） | `date` |
| `INTERVAL` | `INTEGER` | 存储**整数秒**（仅 `usage_events.ttl` 使用） | `timedelta` |
| `JSONB` | `TEXT` | `json.dumps` 序列化字符串，查询走 JSON1 扩展（`json_extract` / `json_each`）。SQLite 不做 schema 校验，合法性由应用层保证 | `dict` / `list` |
| `BYTEA` | `BLOB` | — | `bytes` |
| `VECTOR(1536)` | `BLOB` | sqlite-vec 约定：1536 × `float32` **小端**紧凑排列 = 6144 字节。维度不符时 sqlite-vec 在查询期报错而非写入期 | `list[float]` / `np.ndarray(dtype=float32)` |
| `UUID[]` | `TEXT` | JSON 数组字符串（`["uuid1","uuid2"]`），查询走 JSON1 `json_each`——与 `JSONB` 映射一致（weekly_packs.session_ids 等数组列） | `list[uuid.UUID]` |
| `TEXT[]` | `TEXT` | JSON 数组字符串（`["s1","s2"]`），查询走 JSON1 `json_each` | `list[str]` |
| `BIGINT[]` | `TEXT` | JSON 数组字符串（`[1,2,3]`），查询走 JSON1 `json_each`（entity_communities.member_entity_ids 等数组列） | `list[int]` |

### 13.2 索引与结构映射

| PostgreSQL | SQLite | 说明 |
|:----|:----|:-----|
| B-tree 索引 | 同名 `CREATE INDEX` | 直接等价 |
| 部分索引 `... WHERE cond` | 同语法 | SQLite ≥ 3.8.0 支持，`idx_memories_identity`、`idx_memory_flags_active` 依赖此特性 |
| `GIN` ON JSONB（`idx_memories_types`） | 表达式索引 `json_extract(memory_types,'$')` 或关联表 | **非等价**：SQLite 无 JSON 数组倒排索引，数组成员查询退化为全表 `json_each` 扫描。v0.1.0 量级（1 万条）可接受，规模化后需拆 `memory_types` 关联表 |
| pgvector `HNSW` / `IVFFlat` | sqlite-vec `vec0` 虚拟表 | **非等价**：pgvector 为近似（ANN），sqlite-vec `vec0` 为精确 brute-force。召回集合可能不同，三信号权重需分模式标定（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a） |
| 全文检索（pg_bigm / zhparser） | `FTS5` 虚拟表 | **非等价**，BM25 打分公式不同，需分模式标定（见 §11 决策 D-12 说明） |
| `PARTITION BY RANGE (created_at)`（`usage_events`） | 无分区 | SQLite 无原生分区。降级方案：保留单表 + `idx_usage_events_created`，由维护引擎按 `created_at` 批量 `DELETE` + `VACUUM` 实现等效归档 |
| `REFERENCES ... ON DELETE` | 同语法 | **必须** `PRAGMA foreign_keys = ON`——SQLite 默认**不**强制外键，连接建立时未开启则所有 FK 静默失效 |
| `DEFAULT now()` | `DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))` | SQLite 无 `now()` 函数；`CURRENT_TIMESTAMP` 返回 `'YYYY-MM-DD HH:MM:SS'`（空格分隔、无毫秒、无 Z），与 §13.1 约定的定长 ISO-8601 格式**不一致**，禁止使用 |

### 13.3 时区与时间戳硬约束

SQLite 无时区类型，故：

1. **写入前归一化**：所有时间戳在应用层转为 UTC 后再序列化，DB 内不存任何本地时间。
2. **禁止依赖 DB 侧时钟做业务判定**：过期判定（`expires_at`、`locked_until`、`grace_until`）一律在应用层用 tz-aware `datetime` 比较，避免两模式行为分叉。
3. **DDL 默认值仅用于兜底**：正常路径由应用层显式赋值，`DEFAULT` 仅防御漏赋值。

### 13.4 可执行 DDL

竖切 15 张表的 SQLite 可执行 DDL 见 [`schema-slice.sql`](schema-slice.sql)（与本文同目录）。该文件是 W2「schema 迁移」里程碑的直接输入，字段语义以本文为准、类型转换以 §13.1 为准；两者不一致时以本文为准并修订 SQL。

**范围声明**：`schema-slice.sql` 仅覆盖竖切 15 张表（[slice-implementation-guide.md](../development/slice-implementation-guide.md) §二），非 v0.1.0 全量 57 张表；余下 42 张表的 DDL 在对应功能进入实现范围时按同一映射规则补齐。

### 13.5 向量线性投影矩阵持久化（RC-05）

轻量模式 BGE-M3 原生产出 **1024 维**向量，经线性投影映射至 **1536 维**以与标准模式（text-embedding-3-small，原生 1536 维）保持同一向量空间（全库 7 处口径一致，见 [technology-stack.md](../development/technology-stack.md) §二、[nfr-specification.md](../specification/nfr-specification.md) §二、[requirements-baseline.md](../specification/requirements-baseline.md) 等）。投影规格此前完全缺失，本段补齐：

- **投影方案**：固定随机**正交投影** $W \in \mathbb{R}^{1536 \times 1024}$，按 schema 版本冻结，不随数据训练、不在运行时随机重生成。正交化近似保持能量，但**不保证余弦相似度严格保序**——融合权重 $\alpha_s = 0.50$ 基于标准模式原生 1536 维调参，轻量模式投影后由 `KAIROS_LITE_PROJECTION_CALIBRATION`（见 [configuration.md](../ops/configuration.md) §6.1）控制是否沿用该权重或回退至 BM25 主导路径（v0.1.0 实现期标定）。
- **持久化位置**：矩阵作为**迁移捆绑资产**随 schema 版本发布，存于 `migrations/0010_embedding_projection.bin`（1536×1024 `float32` 小端 = 6,291,456 字节），由 Alembic 迁移 `0010` 一并写入并打 SHA-256 校验和；**不**作为运行时可写表（避免重启重生成导致历史向量全部失效的数据损坏级风险）。矩阵版本与 `schema_version` 绑定——模式迁移（轻量↔标准）或矩阵版本升级时，须对存量向量执行重投影并写入新列/新表，**禁止原地覆盖**。
- **跨模式互检索**：轻量模式投影后的 1536 维向量与标准模式原生 1536 维向量同处一空间但来源不同，`sync_queue` 端云同步与模式迁移场景下可直接比对余弦距离；矩阵版本不一致时同步前须先对齐矩阵版本。

> 决策依据见 [ADR-012](../governance/adr.md)（投影层固定正交投影 + 矩阵随 schema 持久化）。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 数据模型：55 张表 Schema、索引与记忆状态机（56 个 `###` 条目中 `retrieval_enhancement_config` 为配置参数清单，非物理表）。 |
| 0.0.2 | 2026-08-03 | 表数核定为 **56 张**：`proactive_topics` 小节标题此前被误写为 `\|### proactive_topics`（管道符前缀导致标题不成立、计数遗漏），本次修复标题并重新核定——57 个 `###` 条目中 `retrieval_enhancement_config` 非物理表，故物理表 56 张。同步修复 `memories` 索引列表 4 项误用表格语法、`memory_relations.relation_type` 与 `memory_entities` UNIQUE 约束行的列数。 |
| 0.0.3 | 2026-08-03 | 新增 `api_keys` 表（RC-02）——安全规格 §2.1 声明的「内部密钥表」此前无数据承载，API Key 三级权限、轮换宽限、吊销均无处落地。表数 56 → **57**（58 个 `###` 条目减 `retrieval_enhancement_config`）。同步更新 README、implementation-map、slice-implementation-guide 的表数与竖切排除理由。 |
| 0.0.4 | 2026-08-04 | 市场理念吸收（2026-08-04 决策）：`memories` 新增 `occurred_at`（事件时间，双时态）与版本链四字段（parent/root/next/is_latest，对齐架构 §5.2 版本链模型声明）；`knowledge_evolution` 新增 `valid_from/valid_to`（演化关系有效区间，对齐 §5.2 半开区间时间语义）。表数不变（57）。 |
| 0.0.5 | 2026-08-04 | 全库深度审计修复：`api_keys.key_hash` 哈希算法 SHA-256 → PBKDF2-HMAC-SHA512（256,000 次迭代，与安全规格 §2.1 统一）。 |
| 0.0.6 | 2026-08-04 | 全库深度审计修复——检索配置键名映射声明、§8 编号重排、relation_type 术语注释。 |
| 0.0.7 | 2026-08-04 | 文档职责剥离引用更新（changelog 0.0.9 批次）：`image_blobs`/`schema_info`/`training_checkpoints`/`prepared_stmt_stats`/`memories_fts`/`skills_fts`/`permission_acl` 等表的架构引用改指承接文档（P3-21~23 → blueprint、断点续训 → detailed-design §10.5、ACL → blueprint §P3-25、多模态 → api-spec §18.2）。 |
| 0.0.8~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.8~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：memories.contract 增 intention 意图契约枚举（对齐架构 §8 与 feature-list PM-01）。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：§8 编号重排、FTS5 同步机制勘误、类型错配 3 处、缺失索引/UNIQUE 补齐、数组类型映射、知识演化触发机制改指架构 §5.2、计数与表名勘误。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次：决策 D-12 引用标注「决策」前缀（2 处）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：memory_relations.relation_type 补语义标记扩展说明（supplement/refutation/reference/contextual/temporal）；memories.contract 补写时默认建议值+运行时覆盖注记；proactive_topics.priority 改 FLOAT [0,1]（对齐架构 ≥0.7 判据）；quality_tier 引用改指 blueprint；HMAC 审计链公式统一为 threat-model 权威 5 项输入。 |
| 0.0.16 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.16，建议二/七落地）：memories 表新增 structural_value（0/1/2 半定量）/structural_value_reasons/structural_value_updated_at 三字段与 is_structure 双向同步注记；新增 compression_trail JSONB 逐记忆压缩审计字段。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：顶层章节标题统一数字（一~十三→1~13）与中文序引用同步；前瞻记忆引用 §8→§3.2。 |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（changelog 0.0.29）：S-01 大章标题风格统一——「N、」改「§N」（13 个大章并入 §N 数字序形态，引用零联动）。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：api_keys.level 枚举统一为 read（含 CHECK 约束，与 api-spec §1 三级口径一致）；§8.1 conversation_messages 补 parts 列（对齐 api-spec §18.2 v0.1.0 交付承诺）；journal_entries 补 node_episode_index_map 列（架构 §5.2 Episode 归因索引）；api_keys 表补 v0.1.0 核心鉴权承载注记。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：rl_weights 归一化口径统一（初始化不归一化/更新投影强制 Σ=1）；实体类型存储枚举映射注记；配置键名映射示例修正；表标题 v0.1.0 交付口径；零版本标记收敛。 |
| 0.0.39 | 2026-08-06 | 外部理念吸收批次（changelog 0.0.39）：encoding_context 补 `conditions` 子结构约定（条件性经验适用范围显式化）。 |
