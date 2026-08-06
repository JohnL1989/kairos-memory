---
title: Kairos 竖切实现指南（v0.1.0-slice）
aliases:
  - slice-implementation-guide
  - 竖切实现入口
tags:
  - kairos
  - development
  - slice
created: 2026-07-31
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 竖切实现指南（v0.1.0-slice）

> **定位**：竖切（v0.1.0-slice）实现者的唯一入口。按竖切组件聚合架构章节、数据模型、API 端点、配置参数、测试用例与验收判据，避免在 5000 行架构文档中逐节翻找。竖切范围与决策见 [feature-list 竖切标注](../specification/feature-list.md) 与 [project-plan 竖切范围](../governance/project-plan.md)。
>
> **实现基线（2026-07-31 决策）**：身份模型=构造论（初始赋予 + 叙事驱动双向更新）；事件总线=4 类；存储后端=SQLite + sqlite-vec 优先（[ADR-001](../governance/adr.md) 实施顺序）；特征标志关系见架构 §0.8「竖切与特征标志的关系」。

---

## 一、竖切组件清单

| # | 组件 | 归属迭代 | 核心架构章节 |
|:-:|:-----|:--------|:------------|
| 1 | 记忆 CRUD + 双副本分离 | W3 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.1-5.2、§7.3、§8（S-14） |
| 2 | 路径空间 | W4 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2、§3.4 |
| 3 | 三信号混合检索 | W5 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a |
| 4 | 遗忘调度器 + 潜伏势能重估 | W6 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2、§10.17 |
| 5 | 身份注册表（构造论） | W7 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2、§1.8、§8（S-10） |
| 6 | 审计日志（HMAC 链） | W8 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.7、§10.10 |
| 7 | 事件总线（4 类） | W4 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10、[ADR-002](../governance/adr.md) |
| 8 | 外部校准 + 降级状态机 | W8 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2、§10.9、§8（S-11） |
| 9 | CLI/API 接入与冷启动 | W1-W2 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1、[api-spec.md](../specification/api-spec.md) |

> **实现落点**：组件 3（三信号混合检索）→ `src/storage/hybrid_search.py`；组件 5（身份注册表）→ `src/storage/identity_registry.py`（见 implementation-map 存储层）。
>
> **计数口径注记**：本清单按实现批次拆 **9 项**；[project-plan.md](../governance/project-plan.md) §一 竖切组件列按功能域记 **6 项**（统一 LTM+路径空间+三信号混合检索+单曲线衰减遗忘+身份注册表+基础审计日志，事件总线与 CLI/API 并入对应组件）——差异属粒度而非范围，两处口径一致。

---

## 二、竖切 Schema 清单（15 张表）

> 从 data-model 全量 57 张表筛出，仅含竖切组件消费的表；字段定义与索引以 [data-model.md](../specification/data-model.md) 为准。竖切外表的字段若被竖切表引用（如 memories 的 `domain`），按 data-model 全量定义保留。15 张表的 SQLite 可执行 DDL 见 [schema-slice.sql](../specification/schema-slice.sql)（data-model §13.4 的 W2「schema 迁移」直接输入，字段语义以 data-model 为准）。

| # | 表 | 服务组件 | 说明 |
|:-:|:---|:--------|:-----|
| 1 | `memories` | 1/2/3/4/5 | 主记忆表（含 is_identity / identity_confidence / identity_reviewed_at / identity_review_count / VAD / contract / hall） |
| 2 | `memory_versions` | 1 | M-01 更新的版本快照（回滚依据） |
| 3 | `witness_anchor` | 1 | 双副本主副本（强一致，见证锚定） |
| 4 | `usage_weight` | 1 | 双副本影子副本（最终一致，使用权重） |
| 5 | `journal_buffer` | 1 | 写入暂存（摄取验证门禁异步化） |
| 6 | `usage_events` | 7 | 事件总线持久化（4 类事件） |
| 7 | `forgetting_queue` | 4 | 遗忘候选队列 |
| 8 | `audit_log` | 6 | 审计日志（HMAC 链） |
| 9 | `config` | 9 | 运行时配置 |
| 10 | `seeds` | 9 | 冷启动种子锚点 |
| 11 | `memory_states` | 1/4 | 状态变更审计轨迹 |
| 12 | `entities` | 3 | 实体表（实体加成简化信号） |
| 13 | `memory_entities` | 3 | 记忆-实体关联 |
| 14 | `memories_fts` | 3 | FTS5 全文索引（BM25 信号） |
| 15 | `schema_version` | 9 | schema 版本管理 |

**竖切外主要表及排除理由**：升华管道 7 张（sublimation_queue / journal_entries / session_summaries / daily_reports / weekly_packs / user_profiles / sublimation_outputs——升华不在竖切）；同步与对话（sync_queue / conversation_messages——端云同步/对话持久化不在竖切）；实体图谱扩展（memory_chunks / entity_communities / skills / skill_versions / playbooks / playbook_versions / procedural_playbooks_fts / causal_links / memory_semantic_knn——分块/社区/技能/图谱遍历不在竖切）；维护与新鲜度（fact_freshness / freshness_inference_log / debounced_tasks / memory_flags / knowledge_evolution——后台维护扩展不在竖切）；权限与加工区（permission_acl / solution_branches / extinction_fossils——P3-25/知识加工区不在竖切）；密钥管理（api_keys——多 Key 轮换/吊销属平台模式，v0.1.0 轻量模式采用 `KAIROS_API_KEY_HASH` 单 Key 环境变量校验（密钥哈希口径，文件权限 600），见 [security-specification.md](../security/security-specification.md) §2.1 的 L/P 适用标注）；上下文块与查询增强（memory_blocks / memory_block_versions / query_analysis_cache / query_time_buckets——编译管线/QueryAnalyzer 不在竖切）；图谱分析（narrative_threads / compaction_snapshots / world_model_rules / prompt_dependencies）；基础设施日志（training_checkpoints / stmt_cache_metrics）；图片（image_blobs——竖切 W-04 仅记录 VAD 元数据，无图片摄取）。

---

## 三、竖切端点清单（REST 21 + CLI 15）

> **口径**：竖切 CLI 15 条为竖切子集；全量 CLI 25 条（api-spec §3）；implementation-map 的 27 条含规划扩展（竖切 15 + 全量增量）——三处口径不同属有意设计，引用时注明档位。

**REST**（方法/路径以 [api-spec.md](../specification/api-spec.md) 为准）：

| 端点 | 服务组件 | 对应功能 |
|:-----|:--------|:--------|
| `POST /v1/memories` | 1 | W-01/W-02/W-04/W-07 |
| `POST /v1/memories/batch` | 1 | W-03 |
| `GET /v1/memories/{id}` | 1 | 读取 |
| `PATCH /v1/memories/{id}` | 1 | M-01 |
| `DELETE /v1/memories/{id}` | 1 | 删除（软删除，依契约分级，见 [api-spec.md](../specification/api-spec.md) §1.5；非 M-03——M-03 显式遗忘为遗忘候选标记，经 CLI `kairos forget` 承载，见 [api-spec.md](../specification/api-spec.md) §3） |
| `POST /v1/memories/{id}/archive` | 4 | M-05（已注册，见 [api-spec.md](../specification/api-spec.md) §1.5） |
| `POST /v1/memories/{id}/restore` | 4 | M-05 恢复（已注册，见 [api-spec.md](../specification/api-spec.md) §1.5） |
| `POST /v1/memories/search` | 3 | R-02/R-03 |
| `GET /v1/memories?q=` | 3 | R-02（关键词检索） |
| `GET /v1/path` | 2 | R-01 |
| `GET /v1/path/tree` | 2 | R-08 |
| `POST /v1/calibrate` | 8 | CAL-01 |
| `POST /v1/freeze` / `POST /v1/unfreeze` | 8 | CAL-03 |
| `POST /v1/degradation/switch` | 8 | CAL-04 |
| `GET /v1/audit-log` | 6 | CAL-05 |
| `GET /health` | 9 | A-01 |
| `GET /v1/config` / `PATCH /v1/config` | 9 | A-02 |
| `POST /v1/seeds` / `GET /v1/seeds` | 9 | A-04/A-05 |

**CLI**：`kairos init`、`kairos write`、`kairos read`、`kairos search`、`kairos ls`、`kairos tree`、`kairos update`、`kairos forget`、`kairos calibrate`、`kairos freeze`、`kairos degradation switch`、`kairos status`、`kairos health`、`kairos db migrate`、`kairos config show`。

---

## 四、逐组件实现规格

### 组件 1：记忆 CRUD + 双副本分离（W3）

- **职责**：记忆写入/读取/更新/软删除；见证锚定（主副本，强一致）与使用权重（影子副本，最终一致）分离；S-14 隔离防线（差异检验不进入降级路径）。
- **架构**：§5.1-5.2（双副本/差异检验）、§7.3 摄取验证门禁（捕获门控：琐碎文本/上下文标记/秘密文本/长度）、§8 S-14。
- **表**：memories / memory_versions / witness_anchor / usage_weight / journal_buffer / memory_states。
- **API**：POST /v1/memories、POST /v1/memories/batch、GET/PATCH/DELETE /v1/memories/{id}。
- **配置**：摄取门禁参数（KAIROS_CAPTURE_MIN_LENGTH、KAIROS_INPUT_LIMIT_*，见 [configuration.md](../ops/configuration.md) §6/§7）。
- **测试**：TC-W01-001~003、TC-W02-001、TC-W04-001、TC-W07-001；S-14 单测（使用权重写回见证锚定被拒绝）。
- **验收**：E2E-01（写入→检索）；双副本分离判据。

### 组件 2：路径空间（W4）

- **职责**：`kairos://` 前缀索引与树状浏览；路径边界确定性隔离（跨路径污染率 0%）。
- **架构**：§5.2 路径空间（B-tree 前缀索引）、§3.4 域路由（竖切仅实现通用路径 + `_user/_project/_session/_scratch/_system` 前缀约束）。
- **表**：memories.path 索引（idx_memories_path）。
- **API**：GET /v1/path、GET /v1/path/tree。
- **测试**：TC-R01-001~003；S-04 路径隔离验证。

### 组件 3：三信号混合检索（W5）

- **职责**：语义（sqlite-vec 余弦）+ BM25（FTS5）+ 实体加成三信号加权融合（α_s=0.50 / α_b=0.35 / α_e=0.15）。GSPO/MMR/Cross-encoder 不在竖切（对应标志 OFF）。
- **架构**：§7.3a 三信号混合检索；实体加成简化方案——实体提取用关键词/规则匹配（详细设计 §9.3 spaCy 简化版），不启用 LLM 实体提取（Deep 模式不在竖切）。
- **表**：memories.embedding / memories_fts / entities / memory_entities。
- **API**：POST /v1/memories/search、GET /v1/memories?q=。
- **配置**：三信号权重与候选池大小（[configuration.md](../ops/configuration.md) §6.1）。
- **测试**：TC-R02-001~002、TC-R03-001~002。
- **首迭代增强（决策）**：QueryAnalyzer（架构 §2.6.1）定位为竖切后**首迭代实现优先级**——本组件竖切交付仅原生检索;首迭代补 QueryAnalyzer 意图分类（规则优先+模型兜底,意图枚举以架构 §2.6.1 五+1 类为权威）与时间锚定（相对/绝对/事件/会话四类解析,含 fallback_query 字段）,作为查询前置增强检索意图理解。事件锚定与 fallback_query 规格见架构 §2.6.1。
- **验收**：1 万条 SQLite 基准语义检索 P50 ≤100ms。

### 组件 4：遗忘调度器 + 潜伏势能重估（W6）

- **职责**：单曲线指数衰减遗忘得分（freshness = 2^(-days/HALF_LIFE)）、潜伏势能重估（latent_trigger 事件驱动）、复兴加速。
- **架构**：§5.2 遗忘调度器/潜伏势能重估端口；§10.17 降级契约（skip_forgetting 仅标记不处理）；`KAIROS_FEATURE_FORGETTING_ENGINE` 竖切内 ON。
- **表**：forgetting_queue / memories（last_access_at、heat_score、status）。
- **API**：自动调度 + 手动触发；M-05 归档/恢复端点（`POST /v1/memories/{id}/archive` / `restore`，已注册，见 [api-spec.md](../specification/api-spec.md) §1.5）。
- **配置**：KAIROS_FORGETTING_HALF_LIFE（默认 69 天）、KAIROS_FRESHNESS_ACTIVE_THRESHOLD（0.3）、KAIROS_FRESHNESS_STALE_THRESHOLD（0.1）——见 [configuration.md](../ops/configuration.md) §10。**勘误**：v0.1.0 遗忘算法为 freshness 单曲线（见 [detailed-design.md](../specification/detailed-design.md) §3），不依赖 `KAIROS_AGE_DECAY_CONSTANT`——该参数属于 v1.1 二维遗忘曲面目标（configuration 附录 A 已回填默认 30 天），竖切实现无需定值。
- **测试**：TC-F01-001、TC-F02-001、TC-F03-001。
- **验收**：E2E-02（写入→遗忘→复兴）。

### 组件 5：身份注册表（构造论，W7）

- **职责**：is_identity 初始赋予（见证锚定写入触发，冷启动锚点）；identity_confidence 双向更新（叙事自洽度结构性上升→提升；持续下降→宪法解释层判例降级）；见证豁免（S-10）；身份面否决权经预提交总线承载（§1.8）。
- **架构**：§5.2 身份注册表（动态建构）、§1.8 预提交总线/身份总线监听器（三态状态机）、§8 S-10/S-16。
- **表**：memories（is_identity / identity_confidence / identity_reviewed_at / identity_review_count）+ audit_log（identity_demotion 留痕）。
- **配置**：KAIROS_NARRATIVE_AUDIT_CYCLE_MAX（默认 5 调度周期，>12 启动校验拒绝）、身份注册表监听器参数（[configuration.md](../ops/configuration.md) §0.10）。
- **测试**：S-10 单测（见证豁免不可绕过）；identity_demotion 审计可追溯。
- **验收**：G-03 v0.1.0 判据（双向更新可观测、审计可追溯）。

### 组件 6：审计日志（HMAC 链，W8）

- **职责**：审计记录 + 双字段链（明文 content_hash 链 + HMAC-SHA256 完整性链）；审计庭独立感知通道（原始事件流）。
- **架构**：§1.7 监督平面（审计庭）、§10.10 审计与可追溯性、§8 S-16。
- **表**：audit_log。
- **API**：GET /v1/audit-log（含 HMAC 完整性校验）。
- **测试**：E2E-06（写入→修改→删除→审计链验证）。
- **监督平面注记**：竖切内监督平面部分启用（审计庭快照校验/审计日志比对）；完整监督平面随 `KAIROS_FEATURE_CONSTITUTIONAL_GOVERNANCE` 启用（configuration 同口径）。

### 组件 7：事件总线（4 类，W4）

- **职责**：events 表（usage_events）发布/订阅/背压/优先级；4 类事件：use_event / calibration_signal / degradation_switch / latent_trigger；优先级 0-2 不被背压阻塞；trace_id 全链路可审计。
- **架构**：§10.10 事件枚举与流控；[ADR-002](../governance/adr.md)（数据库表而非消息队列）。
- **表**：usage_events。
- **测试**：事件发布/订阅/ACK/背压/优先级集成测试。
- **验收**：4 类事件全链路可用，trace_id 可审计。

### 组件 8：外部校准 + 降级状态机（W8）

- **职责**：外部校准端口（admin Key 鉴权）；降级状态机（保守静默→受限交叉验证→安全休眠，校准时延驱动）；强制冻结/解冻。
- **架构**：§1.2 外部校准端口/强制冻结、§10.9 降级状态机、§8 S-11。
- **API**：POST /v1/calibrate、POST /v1/freeze、POST /v1/unfreeze、POST /v1/degradation/switch。
- **配置**：DEGRADATION_PERIOD_N/M 及滞回参数（[configuration.md](../ops/configuration.md) §4）；虚拟校准竖切内可选（默认关闭）。
- **测试**：TC-CAL01-001、TC-CAL03-001、TC-CAL04-001（勘误：原 TC-C01-001 前缀已废弃，统一为 TC-CALxx-00x，见 [test-plan.md](../quality/test-plan.md) §3 命名约定）。
- **验收**：E2E-04/05/08。

### 组件 9：CLI/API 接入与冷启动（W1-W2）

- **职责**：REST（Litestar）、CLI（Click/Typer）、配置加载、冷启动种子注入、健康检查、数据库迁移。
- **架构**：§7.1 三种接入方式；[api-spec.md](../specification/api-spec.md) 竖切端点。
- **表**：config / seeds / schema_version。
- **API/CLI**：见第三节清单。
- **测试**：冷启动 E2E-07；各 CLI 命令冒烟测试。

---

## 五、实现顺序与依赖（对应 [project-plan](../governance/project-plan.md)）

```text
W1 骨架（组件 9 前置）→ W2 schema 迁移（15 张表）→ W3 CRUD+双副本（组件 1）
→ W4 路径空间+事件总线（组件 2+7）→ W5 检索（组件 3，依赖 7 的 use_event）
→ W6 遗忘（组件 4，依赖 7 的 latent_trigger）→ W7 身份（组件 5，依赖 6 的审计）
→ W8 校准+降级+审计（组件 6+8）→ W9 基准+文档对齐 → W10 竖切验收
```

关键依赖：事件总线（W4）是 W5/W6 的前置（use_event / latent_trigger）；审计日志（W8）是身份降级（W7）与校准（W8）的前置；`KAIROS_FEATURE_FORGETTING_ENGINE` 在 W6 起置 ON。

---

## 六、开发者阅读路径

| 目标 | 优先阅读 |
|:-----|:--------|
| 系统全貌 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0（总览与速查表） |
| 认知依据（可选） | [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1（度量空间） |
| 竖切范围 | 本文档 + [feature-list 竖切标注](../specification/feature-list.md) |
| 表定义 | [data-model.md](../specification/data-model.md) 对应 15 张表 |
| 表 DDL（可执行） | [schema-slice.sql](../specification/schema-slice.sql) — 竖切 15 张表 SQLite DDL，W2 直接输入 |
| 接口契约 | [api-spec.md](../specification/api-spec.md) 竖切端点 |
| 参数默认值 | [configuration.md](../ops/configuration.md) 对应章节 |
| 验收口径 | [acceptance-criteria.md](../quality/acceptance-criteria.md)「〇、竖切验收标准」 |

---

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 竖切实现指南：组件清单、15 张表、REST/CLI 端点、逐组件实现规格与实现顺序。 |
| 0.0.2 | 2026-08-04 | 挂接 schema-slice.sql 可执行 DDL 引用（§二 引言 + §六 阅读路径），对齐 data-model §13.4。 |
| 0.0.3 | 2026-08-04 | 全库深度审计修复：竖切组件代码落点注记、AGE_DECAY_CONSTANT 待定义状态注记、CLI 计数三档口径说明。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：组件 4 遗忘配置勘误（freshness 三阈值，AGE_DECAY 归 v1.1）；TC-C01-001→TC-CAL01-001；竖切组件计数 9 vs 6 口径注记。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次（changelog 0.0.15，依 comprehensive-documentation-audit P1-02）：M-05 归档端点「待 api-spec 注册」标注移除（已注册，见 [api-spec.md](../specification/api-spec.md) §1.5），组件 4 API 行同步补 restore 配套端点。 |
| 0.0.16 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.16，建议三落地）：组件 3 补 QueryAnalyzer 首迭代增强注记（意图分类规则优先+时间锚定，竖切后首迭代实现优先级）。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：api-spec §三→§3 引用联动。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（changelog 0.0.26）：M-07 存活探针端点 GET /v1/health→GET /health。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：REST 20→21（补 `POST /v1/memories/{id}/restore` 行，M-05 恢复端点）；DELETE 行 M-03 标注修正（软删除语义，M-03 显式遗忘经 CLI `kairos forget` 承载）；组件 6 补监督平面部分启用注记；CLI 全量 24→25 联动（api-spec §3 补注册）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：configuration 章节引用修正（§1→§4/§0.10）；轻量模式认证环境变量统一为 KAIROS_API_KEY_HASH；决策注记去版本号。 |
