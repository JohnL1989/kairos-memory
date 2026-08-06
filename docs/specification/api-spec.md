---
title: Kairos 接口规格书
aliases:
  - 接口规格
  - API Specification
tags:
  - kairos
  - design
  - api
created: 2026-07-20
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 接口规格书

> **定位**：定义 Kairos 系统的外部接口——REST API、Agent Tool、CLI 命令和事件总线消息格式。
>
> **基础 URL**：`http://localhost:8010`（可配置）
> **认证**：API Key（read/write/admin 三级），通过 `Authorization: Bearer <key>` 请求头传递。

---

## 1、REST API

### 1.1 记忆写入

**POST /v1/memories**

```json
{
  "path": "kairos://users/{id}/memories/",
  "content": "记忆内容",
  "contract": "ondemand",
  "memory_types": ["semantic"],
  "provenance": "user_input",
  "vad": {"v": 0.5, "a": 0.3, "d": 0.0},
  "relations": [
    {"target_id": "uuid", "relation_type": "causal", "strength": 0.8}
  ],
  "encoding_context": {"task": "review", "session_id": "uuid"}
}
```

**响应** `201 Created`：
```json
{"id": "uuid", "path": "kairos://users/{id}/memories/{uuid}", "version": 1}
```

**错误**：`400`（参数无效）、`401`（认证失败）、`403`（权限不足）、`413`（内容超长）、`422`（语义校验失败，如缺少必填字段）、`429`（请求过多，限流触发）

**POST /v1/memories/batch** — 批量导入（W-03）

**约束**：最大批量 100 条。非幂等——重复提交可能产生重复记录。部分失败返回 207 Multi-Status（成功条数 + 失败详情）。

```json
{
  "items": [
    {"path": "...", "content": "...", "contract": "ondemand", "provenance": "user_input", "memory_types": ["semantic"]},
    {"path": "...", "content": "...", "contract": "permanent", "provenance": "user_input", "memory_types": ["episodic"]}
  ],
  "on_conflict": "skip | overwrite"
}
```

**响应** `207 Multi-Status`：
```json
{
  "success_count": 8,
  "failed_count": 2,
  "results": [
    {"index": 0, "status": "created", "id": "uuid"},
    {"index": 1, "status": "error", "code": "ERR-INPUT-002", "message": "路径格式无效"}
  ]
}
```

### 1.2 记忆检索

**GET /v1/memories?path=kairos://users/{id}/memories/&limit=10&offset=0**

**GET /v1/memories?q=search+query&limit=5**

**GET /v1/memories/{id}**

**POST /v1/memories/search** — 三信号混合检索（语义 + BM25 + 实体加成）

> **维度命名映射表**：本文（api-spec）的检索维度、配置参数（configuration §6.1 三信号混合权重）、RL 权重优化器（rl-weight-spec）三处的命名对应关系如下。注意：三信号混合检索是 v0.1.0 的核心融合策略（见 architecture [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a），时序/信任/热度不作为独立基础维度参与检索——它们的排序调制作用由 RL 重排序层（rl-weight-spec）管理，不在检索请求体中直接配置。
>
| api-spec 搜索维度 | configuration 参数 | rl-weight-spec 维度 | 说明 |
|:----------------|:-----------------|:-------------------|:-----|
| `semantic`（语义向量匹配） | `KAIROS_HYBRID_SEMANTIC_WEIGHT` | `relevance` | 查询与记忆的语义相关性 |
| `bm25`（BM25 全文匹配） | `KAIROS_HYBRID_BM25_WEIGHT` | `relevance`（与 semantic 合并为相关性总分） | BM25 关键词匹配 |
| `entity`（实体加成） | `KAIROS_HYBRID_ENTITY_WEIGHT` | `relevance`（与上两项合并） | 查询实体与记忆实体的交集比例 |
>
> 另见 [ops/configuration.md](../ops/configuration.md) §6.1 三信号混合检索权重参数与 [specification/rl-weight-spec.md](rl-weight-spec.md) RL 二次排序维度。

```json
{
  "query": "搜索内容",
  "mode": "hybrid",
  "weights": {"semantic": 0.5, "bm25": 0.35, "entity": 0.15},
  "limit": 10,
  "filters": {"contract": "permanent", "path_prefix": "kairos://projects/"}
}
```

**响应** `200`：标准检索结果列表（同 GET），加 `explanation` 字段说明各维度贡献。

**GET /v1/memories/heat-top?limit=10** — 热度最高记忆（heat_score 降序）
> 机制：`heat_score` 由后台维护引擎 Light 模式维护（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 后台维护引擎热度衰减——按日衰减 α=0.95，每次访问增量 Δ=0.05；`KAIROS_HEAT_DECAY_ALPHA`/`KAIROS_HEAT_ACCESS_BOOST` 见 configuration §8.3）。热度为检索排序的辅助信号，不作为独立基础排序维度（5D 框架已废弃，见 configuration §8.3 废弃声明）。

**响应** `200`：`{"data": [...], "total": N}`

**响应** `200 OK`：
```json
{
  "data": [
    {"id": "uuid", "path": "...", "content": "...", "contract": "...", "created_at": "..."}
  ],
  "total": 42,
  "path": "kairos://...",
  "meta": {
    "calibration_status": {
      "level": "degraded",
      "last_external_calibration": "2026-07-28T14:30:00Z",
      "days_since_last_calibration": 8,
      "active_mode": "virtual",
      "virtual_calibration_confidence_ceiling": 0.227
    }
  },
  "nudge": {
    "active": true,
    "message": "系统已 8 天未收到你的反馈，当前结果基于自判模式。如需更精确的结果，可对 1-2 条结果给出「准确/不准确」反馈。",
    "level": "subtle",
    "dismissible": true
  }
}
```

> **校准状态与 nudge 字段（0.0.16 新增，建议一）**：`meta.calibration_status` 与 `nudge` 为检索响应的可选元数据——`calibration_status.level` 枚举（healthy/degraded/virtual/dormant）为运营可视化粗粒度映射（见 GET /v1/health/calibration）；`nudge` 为退化态主动校准提示（subtle=7-14 天 / noticeable=14-30 天 / prominent=>30 天无校准），**非阻塞**——作为元数据返回由前端决定呈现，不引入 ask_user 式阻塞交互；用户完成一次校准后 nudge 清除。两字段仅在外部校准静默超过 7 天时出现，正常态省略。

### 1.3 记忆更新

**PATCH /v1/memories/{id}**（内部实现为版本插入，修改历史可审计，详见 [data-model.md](data-model.md) `superseded_by` 链）

**并发冲突**：请求头 `If-Match: {current_version}` 可选。提供时，服务端校验当前版本与请求一致后才执行更新；不一致返回 409 Conflict。不提供时直接更新（最后写入胜出）。

```json
{
  "content": "更新后的内容",
  "vad": {"v": 0.7, "a": 0.4, "d": 0.1}
}
```

**响应** `200 OK`：返回更新后的记忆对象（含新版本号）

**POST /v1/memories/{id}/feedback** — 可信度反馈

```json
{"feedback": "helpful|unhelpful|incorrect", "reason": "可选说明"}
```
**响应** `200`

**POST /v1/memories/{id}/lock** — 锁定保护（禁止修改/删除）

```json
{"reason": "合规保留", "duration_seconds": 2592000}
```
**响应** `200`

**POST /v1/memories/{id}/expire** — 标记过期（设 TTL，到期自动归档）

```json
{"ttl_seconds": 86400}
```
**响应** `200`

**POST /v1/memories/merge** — 语义合并（保留见证锚定，受 S-14 约束）

```json
{"source_ids": ["uuid1", "uuid2"], "strategy": "semantic_overlay"}
```
**响应** `200`：返回合并后新的记忆对象

### 1.4 记忆版本与回滚

**GET /v1/memories/{id}/versions** — 获取记忆版本历史

- 返回该记忆的所有版本快照元数据列表（不含完整内容，仅含 version_number、created_at、reason）
- 数据来源：`memory_versions` 表（详见 [data-model.md](data-model.md) §2）

```json
{
  "versions": [
    {"version_number": 3, "created_at": "2026-07-23T10:00:00Z", "reason": "update"},
    {"version_number": 2, "created_at": "2026-07-22T15:30:00Z", "reason": "update"},
    {"version_number": 1, "created_at": "2026-07-21T08:00:00Z", "reason": "initial"}
  ]
}
```
**响应** `200`

**POST /v1/memories/{id}/rollback** — 回滚到指定版本

```json
{"target_version": 1}
```
- 从 `memory_versions` 表读取目标版本快照，恢复当前记忆内容
- 回滚后 version 递增（不破坏现有版本历史）
- 受 S-08（未授权管理访问拒绝）约束：回滚操作需 admin 权限
**响应** `200`：返回回滚后的记忆对象

### 1.5 记忆导出/删除/定向遗忘

**GET /v1/memories/{id}/export?clearance=export** — 导出记忆（脱敏）
- `?clearance=debug`（仅 localhost 可用）：返回完整内容，含原始 content、嵌入向量、审计字段
- `?clearance=export`（默认，所有网络可用）：返回脱敏摘要——先对敏感字段执行掩码/替换（`is_sensitive=true` 字段按 S-07 掩码），再将 content 截断为前 200 字符 + 元数据，不包含嵌入向量和审计追踪（掩码+截断语义与架构 §8 S-07 及 [security-specification.md](../security/security-specification.md) S-07 一致）
```json
{
  "format": "json | markdown",
  "include_metadata": true
}
```
**响应** `200 OK`：导出格式的记忆完整内容

**DELETE /v1/memories/{id}** — 清除记忆
- permanent（常驻）契约：拒绝删除（返回 403）——常驻记忆不可经常规删除路径移除，仅可经宪法修订端口降级
- ondemand（按需）/environmental（环境）契约：软删除（标记 `is_deleted=true`，保留审计痕迹）
- temporary（临时）契约：硬删除（直接清除，清理前写入审计日志标记 `expiry_cascade_delete`——与架构 §8 临时契约留痕口径一致，见 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8 外部来源铁律）

**POST /v1/memories/{id}/suppress** — 定向遗忘（抑制检索，保留数据）
```json
{"reason": "compliance_erase", "review_id": "uuid"}
```

**POST /v1/memories/{id}/archive** — 归档记忆（竖切功能 M-05，0.0.15 注册）
- 将记忆从活跃存储移至冷存储（`status=archived`），常规检索不再返回，数据保留可恢复
- 语义对齐：对应架构 12 规范操作集 `archive`（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3.1），幂等——已归档记忆重复归档返回成功（200）但不重复操作（见架构 §7.3.1 幂等性清单）
- 契约约束：permanent 契约归档前须经宪法修订端口降级（直接返回 403）；temporary 契约不进入归档（到期由 forgetAfter 硬删除，见架构 §5.2）；其余契约正常归档
- 错误：`404`（记忆不存在）、`403`（permanent 契约拒绝归档）
```json
{"reason": "low_usage"}   // 归档原因（可选，写入审计日志）
```

**POST /v1/memories/{id}/restore** — 归档恢复（竖切功能 M-05 配套）
- 将记忆从冷存储恢复至活跃检索池（`status=active`），重新参与权重计算和语义检索
- 语义对齐：对应架构 12 规范操作集 `restore`（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3），须经潜伏势能重估端口（架构 §5.2）的匹配验证——记忆的语义向量须与当前活跃上下文的盲区方向存在 ≥ 阈值（默认 0.6）的余弦相似度
- 错误：`404`（记忆不存在或非 archived 状态）、`422`（语义匹配验证未通过）
```json
{"reason": "context_reemerged"}   // 恢复原因（可选，写入审计日志）
```

### 1.6 路径操作

**GET /v1/path?path=kairos://users/{id}/** — 路径下记忆列表

**GET /v1/path/tree?path=kairos://users/** — 路径空间树状浏览

**POST /v1/path/suppress** — 路径级检索抑制（S-16/S-17）

```json
{"path_prefix": "kairos://_system/obsolete/", "reason": "compliance"}
```
**响应** `200`

### 1.7 校准与治理

**POST /v1/calibrate** — 发送外部校准信号（CAL-01）
```json
{
  "memory_id": "uuid",
  "narrative_coherence_score": 0.85,
  "source": "user_review"
}
```

**POST /v1/constitution** — 宪法级偏好管理（CAL-02，需 admin Key）
```json
{
  "action": "view | revise",
  "preference_key": "constitutional.preference.name",
  "new_value": "..."
}
```

**POST /v1/degradation/switch** — 降级模式切换（CAL-04，需 admin Key）
```json
{
  "mode": "conservative_silent | limited_cross_validation | safe_hibernation"
}
```
> 机制：三模式状态机的触发/行为/退出条件见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.9（外部校准降级模式状态机）——本端点仅提供显式切换入口，运行时降级由校准时延自动驱动；切换事件写入事件总线（`degradation_switch`）。

**POST /v1/freeze** — 强制冻结（CAL-03，需 admin Key）
```json
{"duration_seconds": 300, "scope": "all"}
```

**POST /v1/unfreeze** — 解冻
> 机制：强制冻结/解冻为宪法主权面的至高权限（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 强制冻结机制 + §10.9 安全休眠态执行路径）——冻结时长受最长冻结时长约束（到期自动解冻，见架构 §0.7 冻结反制）；冻结/解冻事件写入审计日志。

### 1.8 系统管理

**GET /health** — 健康检查（A-01）
```json
{"status": "ok", "components": {"api": "ok", "db": "ok", "scheduler": "running", "embedding": "ok", "sublimation": "idle"}, "uptime_seconds": 3600}
```

**GET /v1/config** — 查看配置（A-02）
**PATCH /v1/config** — 修改运行时配置（A-02）

**GET /v1/memories/stats** — 记忆库报告（总量/按类型/按状态/增长率）
```json
{"total": 900, "by_type": {"semantic": 300, "episodic": 200, "procedural": 400}, "by_state": {"active": 600, "stale": 150, "archived": 80, "suppressed": 40, "superseded": 30}, "growth_7d": {"semantic": 15, "episodic": 8}}
```

**GET /v1/proactive/topics** — 查询待处理主动话题（A-17）
> 机制：话题由后台维护引擎 Deep 模式驱动生成（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 主动话题生成器，含压力信号族扩展 D-324）；Agent 通过 `on_turn_start` hook 检查高优先级（priority ≥ 0.7）未确认话题并注入上下文。

| 参数 | 类型 | 说明 |
|:----|:----|:-----|
| `user_id` | UUID | 可选，按用户过滤 |
| `status` | TEXT | 可选，pending/acknowledged/processed/expired |

**响应** `200`：
```json
{
  "topics": [
    {"id": "uuid", "topic": "话题描述", "summary": "...", "priority": 0, "evidence_count": 5, "status": "pending", "generated_at": "2026-07-23T10:00:00Z"}
  ],
  "total": 3
}
```

**GET /v1/audit-log** — 审计日志查询（CAL-05）。以下参数为查询字符串参数：
```json
{
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "redline_id": "S-xx",
  "limit": 50
}
```

**GET /v1/falsification** — 证伪信号查询（CAL-06）。以下参数为查询字符串参数：
```json
{
  "detector": "coupling | vad_independence | system_aggregation",
  "since": "ISO8601"
}
```

**GET /v1/scheduler/status** — 调度器状态查询（A-03）

**POST /v1/webhooks** — 注册 Webhook 事件订阅（v1.1 预留端点）
```json
{
  "url": "https://agent.example.com/kairos-callback",
  "events": ["use_event", "calibration_signal", "degradation_switch"],
  "secret": "可选签名密钥"
}
```

**响应** `201 Created`：
```json
{"id": "webhook-uuid", "status": "active"}
```

> **升华状态查询**：升华/遗忘/重估状态通过 `GET /v1/sublimation/status` 查询（见下文）。

**POST /v1/seeds** — 种子锚点管理（需 admin Key）
```json
{
  "seed_type": "config | identity | calibration",
  "path": "kairos://_system/seeds/{name}",
  "content": {...},
  "initial_confidence": 0.9,
  "current_confidence": 0.9
}
```

**GET /v1/seeds** — 种子状态查看（A-05）
```json
{
  "seeds": [
    {"path": "kairos://_system/seeds/...", "status": "active", "degradation_level": 0.3}
  ]
}
```

**POST /v1/path/rebuild-index** — 路径索引重建（A-06）

**POST /v1/sublimation/trigger** — 手动触发升华（SF-02）
```json
{"path": "kairos://...", "target_stage": "strategy | behavior"}
```

**GET /v1/sublimation/status** — 升华进度查询（SF-04）
```json
{"queue": [{"id": "uuid", "stage": "raw", "status": "processing"}]}
```

---

## 2、Agent Tool

### Tool: memories_write

```json
{
  "name": "memories_write",
  "description": "向 Kairos 记忆系统写入一条记忆",
  "parameters": {
    "path": {"type": "string", "description": "存储路径"},
    "content": {"type": "string", "description": "记忆内容"},
    "contract": {"type": "string", "enum": ["permanent", "ondemand", "environmental", "temporary", "intention"], "description": "契约类型（五值枚举，与 data-model memories.contract 一致；intention 为前瞻记忆意图契约，仅系统内部 kairos://_system/intentions/ 路径使用，见架构 §3.2 前瞻记忆段）"},
  "memory_types": {"type": "array", "items": {"type": "string", "enum": ["episodic", "semantic", "procedural"]}, "description": "记忆类型列表，一条记忆可同时属于多类型（多重记忆认知模型；叙事特殊规则由 identity_relevance 参数承载，非独立类型）"},
    "vad": {"type": "object", "description": "情感坐标（可选）: {\"v\": float, \"a\": float, \"d\": float}"},
    "provenance": {"type": "string", "enum": ["user_input", "external_calibration", "internal_inference", "system_generated", "exploration"], "description": "来源标识（必填，S-15 要求来源缺失返回 422）"},
    "relations": {"type": "array", "items": {"type": "object"}, "description": "关系列表（可选）: [{\"target_id\": \"uuid\", \"relation_type\": \"causal\", \"strength\": 0.8}]"}
  }
}
```

**响应**：`{"id": "uuid", "path": "kairos://users/{id}/memories/{uuid}", "version": 1}`

**错误**：`422`（缺少 provenance 等必填字段）、`413`（内容超长）、`429`（限流）

### Tool: memories_search

```json
{
  "name": "memories_search",
  "description": "在 Kairos 记忆系统中搜索记忆",
  "parameters": {
    "query": {"type": "string"},
    "path": {"type": "string"},
    "limit": {"type": "integer", "default": 5}
  }
}
```

**响应**：`{"results": [{"id": "uuid", "path": "kairos://...", "score": 0.83}], "total": 5}`

### Tool: path_browse

```json
{
  "name": "path_browse",
  "description": "浏览 Kairos 路径空间",
  "parameters": {
    "path": {"type": "string", "description": "起始路径，默认根"},
    "depth": {"type": "integer", "default": 2}
  }
}
```

**响应**：`{"nodes": [{"path": "kairos://users/", "children": 3}], "truncated": false}`

### Tool: memories_list_recent

```json
{
  "name": "memories_list_recent",
  "description": "列出最近使用的记忆（当前 session）",
  "parameters": {
    "limit": {"type": "integer", "default": 10}
  }
}
```

**响应**：`{"items": [{"id": "uuid", "content": "摘要", "created_at": "ISO8601"}], "total": 10}`

### Tool: memories_merge

```json
{
  "name": "memories_merge",
  "description": "语义合并多条记忆（保留见证锚定，受 S-14 约束）",
  "parameters": {
    "source_ids": {"type": "array", "items": {"type": "string", "format": "uuid"}, "description": "待合并的记忆 ID 列表"},
    "strategy": {"type": "string", "enum": ["semantic_overlay", "chronological_append"], "description": "合并策略"}
  }
}
```

**响应**：`{"merged_id": "uuid", "sources": ["uuid", "uuid"], "status": "merged"}`

**错误**：`400`（source_ids 为空或含无效 ID）、`422`（合并策略非法）、`429`（限流）

---

## 3、CLI 命令

| 命令 | 说明 | 示例 |
|:----|:-----|:-----|
| `kairos init` | 初始化系统（创建配置、目录和数据库） | `kairos init --db sqlite:///$HOME/.kairos/kairos.db` |
| `kairos serve` | 启动服务 | `kairos serve --port 8010` |
| `kairos write <path>` | 写入记忆 | `kairos write kairos://users/default/memories/ --content "..."` |
| `kairos read <path>` | 读取记忆 | `kairos read kairos://users/default/memories/abc` |
| `kairos search <query>` | 搜索 | `kairos search "关键词" --limit 10` |
| `kairos ls <path>` | 列出路径 | `kairos ls kairos://users/default/` |
| `kairos tree <path>` | 树状浏览 | `kairos tree kairos://projects/ --depth 3` |
| `kairos forget <id>` | 显式遗忘 | `kairos forget uuid` |
| `kairos suppress <id>` | 定向遗忘 | `kairos suppress uuid --reason compliance` |
| `kairos health` | 健康检查 | `kairos health` |
| `kairos config` | 配置管理 | `kairos config set KAIROS_DAILY_BUDGET_FEN 20000` |
| `kairos db` | 数据库管理 | `kairos db init` / `kairos db migrate` / `kairos db verify` / `kairos db backup` / `kairos db vacuum` / `kairos db reindex` |
| `kairos stop` | 停止服务 | `kairos stop` |
| `kairos logs` | 查看日志 | `kairos logs --tail 100` |
| `kairos audit verify-chain` | 审计链完整性验证（HMAC 审计链算法见 [threat-model.md](../security/threat-model.md) HMAC 审计链——`hmac = HMAC-SHA256(hmac_key, timestamp + operator + action + content_hash + prev_hmac)`，5 项输入；details 等可变信息以 SHA256 摘要并入 content_hash 参与链计算；支持精确定位篡改记录与整体完整性校验） | `kairos audit verify-chain` |
| `kairos sublimation trigger` | 手动触发升华 | `kairos sublimation trigger --path kairos://projects/x/` |
| `kairos sublimation progress` | 查询升华进度 | `kairos sublimation progress` |
| `kairos calibrate` | 外部校准 | `kairos calibrate --memory-id uuid --score 0.85` |
| `kairos freeze` | 强制冻结 | `kairos freeze --duration 300` |
| `kairos status` | 系统状态 | `kairos status` 显示各层运行状态 |
| `kairos update <id>` | 更新记忆 | `kairos update uuid --content "new content"` |
| `kairos approve <id>` | 审批升华候选 | `kairos approve uuid --accept` |
| `kairos init --init-key` | 生成 API Key（同时生成 SALT/SECRET_KEY/AUDIT_HMAC_KEY） | `kairos init --init-key` |
| `kairos admin key rotate` | 轮换 API Key | `kairos admin key rotate <key_id>` |

---

## 4、事件总线消息格式

### 消息结构

```json
{
  "event_id": "uuid",
  "event_type": "calibration_signal | degradation_switch | use_event | intention_activate | intention_resolve | affective_boost | exploration_budget | latent_trigger | attention_allocation | sublimation_tick",
  "source": "storage_layer | strategy_layer | wm_layer | metacognition_layer | sovereignty_plane",
  "target": "broadcast | specific_layer | specific_component",
  "trace_id": "uuid",
  "priority": 1,
  "payload": {},
  "timestamp": 1700000000000000000
}
```

> **v0.1.0 简化**：`target` 默认为 `broadcast` 时表示全层广播（事件类型隐式决定接收层），`trace_id` 在同步事件中为空。`priority` 范围为 0–9（**0=最高**，校准信号使用 0；v0.1.0 仅使用 0/1/2），事件时效由接收方按 event_type 的预设 TTL 处理（参见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 事件类型原语表）。`timestamp` 为 int64 纳秒（从架构规范，非 ISO8601 字符串）。

> **临时契约声明**：临时契约记忆过期清除时写入审计日志（标记 `expiry_cascade_delete`，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 forgetAfter）——**不留审计痕迹的场景仅限捕获阶段**：入区闸机/摄取门禁拒绝的输入未入库，不产生审计事件。已入库临时记忆的清除必留痕（与架构 §8 外部来源铁律一致）。此行为与 S-15（来源可鉴别）不冲突：临时契约在写入时仍记录 provenance。

**事件类型枚举**（完整定义以 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 为准，此处仅列 v0.1.0 核心类型）：

| event_type | 说明 | 发送者 | 接收者 |
|-----------|:-----|:-------|:-------|
| `calibration_signal` | 外部校准信号注入 | 宪法主权面 | 全层广播 |
| `degradation_switch` | 降级模式切换 | 宪法主权面 | 全层广播 |
| `use_event` | 使用事件提交（影子副本、权重、审计） | WM | 策略+存储+元认知 |
| `intention_activate` | 前瞻保持触发条件匹配 | 策略 | WM |
| `intention_resolve` | 前瞻执行关闭裁定 | WM | 策略→存储 |
| `affective_boost` | 情感基线提升注入 | 策略 | WM |
| `exploration_budget` | 探索预算分配 | 元认知 | 策略 |
| `latent_trigger` | 潜伏势能重估触发 | 元认知 | 存储 |
| `attention_allocation` | 注意力分配日志 | 注意力调度器 | 元认知 |
| `sublimation_tick` | 升华管道轮次推进 | 存储 | 自身 |

---

## 5、记忆读取

### GET /v1/memories/{id}?level=summary|overview|full — 多级读取

**权限**：read

按粒度层级返回记忆内容：

| 层级 | 返回内容 | 适用场景 |
|:----|:---------|:---------|
| `summary` | 前 200 字摘要 + session 标签 | 快速预览 |
| `overview` | 前 800 字 + session 摘要 + 相关片段 | 常规检索 |
| `full` | 全文 + session 完整元数据 + 同 session 片段列表 | 深度分析 |

默认 `overview`。

**响应** `200 OK`：

```json
{
  "id": "uuid",
  "level": "overview",
  "content": "记忆内容（按层级截断）",
  "path": "kairos://users/{id}/memories/{uuid}",
  "session": {"id": "uuid", "label": "会话标签"},
  "metadata": {"created_at": "ISO8601", "contract": "ondemand", "version": 1}
}
```

**错误**：`401`（认证失败）、`403`（权限不足）、`404`（记忆不存在）

---

### POST /v1/sublimation/prompt — 构建蒸馏提示词（两阶段 API 第一阶段）

**权限**：write

```json
{
  "session_id": "session-001",
  "records": [{"role": "user", "content": "..."}]
}
```

**响应**：`200` 返回 `prompt` 文本和 `record_ids` 列表。
调用方将 prompt 传给 LLM，将 LLM 返回结果提交到 `/v1/sublimation/process`。

---

### POST /v1/sublimation/process — 处理蒸馏结果（两阶段 API 第二阶段）

**权限**：write

```json
{
  "raw_response": "LLM 返回的 JSON 结果",
  "record_ids": ["rec-001"],
  "session_id": "session-001",
  "target_level": "L1"
}
```

**响应**：`200` 处理结果

---

### CLI 新增命令

| 命令 | 说明 | 示例 |
|:----|:-----|:-----|
| `kairos read --level summary` | 多级读取 | `kairos read uuid --level summary` |
| `kairos layers ls` | 列出 层级蒸馏各层概览 | `kairos layers ls --level L2` |
| `kairos layers distill` | 手动触发蒸馏 | `kairos layers distill --session-id xxx` |

---

## 6、扩展端点

### 6.1 会话消息 API

**POST /v1/sessions/{id}/messages** — 批量写入会话消息（Hermes on_session_end 调用）

**权限**：write

```json
{
  "messages": [
    {"role": "user", "content": "...", "tool_calls": null, "timestamp": 1234567890.0, "token_count": 150}
  ]
}
```

**响应** `200`：`{"status": "stored", "session_id": "...", "messages": 10}`

**GET /v1/sessions** — 列出最近会话

**权限**：read

**Query**：`?user_id=default&limit=20`

**GET /v1/sessions/{id}/messages** — 读取会话消息（支持游标分页）

**权限**：read

**Query**：`?limit=200&before_id=500`

### 6.2 实体知识图谱 API

**POST /v1/entities/extract** — 从文本提取实体

**权限**：write

```json
{
  "text": "文本内容",
  "user_id": "default"
}
```

**响应** `200`：`{"entities": [{"name": "...", "type": "concept", "description": "..."}], "count": 3}`

**POST /v1/graph/search** — 实体图谱多跳查询

**权限**：read

```json
{
  "query": "pgvector",
  "user_id": "default",
  "limit": 10,
  "relation_type": "causal"
}
```

**响应** `200`：`{"entities": [...], "relations": [...], "hops": 2}`

### 6.3 后台维护 API

**POST /v1/maintenance/run** — 手动触发后台维护（Light/Deep）

**权限**：admin

```json
{"mode": "light | deep", "user_id": "default"}
```

**GET /v1/maintenance/status** — 查看维护引擎运行状态

**权限**：read

**响应** `200`：`{"last_light_at": "...", "last_deep_at": "...", "total_merged": 42, "total_extracted_entities": 156}`

### 6.4 Reflect API（按需深度分析）

**POST /v1/reflect** — 对现有记忆执行按需深度分析

**权限**：read（分析）+ write（写入新洞察）

```json
{
  "query": "分析 Alice 的项目风险",
  "depth": "standard"
}
```

**执行流程**：
1. 对 query 执行三信号混合检索（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a α_s=0.50/α_b=0.35/α_e=0.15），获取相关记忆
2. LLM 分析检索到的记忆，形成结构化洞察
3. 新洞察写入加工区（hall=processing），触发验证流程
4. 返回洞察结果

**响应** `200`：
```json
{
  "insight": "Alice 在 3 个项目中积累了前端架构经验...",
  "related_memories": ["mem_uuid1", "mem_uuid2"],
  "confidence": 0.78,
  "written_to": {"hall": "processing", "memory_id": "new_mem_uuid"}
}
```

**参数**：`depth` — `standard`（默认，快速分析）/ `deep`（更彻底分析，耗时更长）

### 6.5 健康报告与聚合统计

> **被架构引用**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.11（压缩审计端点 `GET /audit/compression`、`GET /audit/compression/summary`）——本章节号变更须同步回改。

**GET /v1/health/detail** — 聚合健康报告

**权限**：read

**响应** `200`：
```json
{
  "total_memories": 900,
  "by_type": {"semantic": 300, "episodic": 200, "procedural": 400},
  "by_state": {"active": 600, "stale": 150, "archived": 80, "suppressed": 40, "superseded": 30},
  "growth_7d": {"semantic": 15, "episodic": 8},
  "flags": {"needs_verification": 5, "contradiction": 2, "p6_deviation": true},
  "rl_weights": {"relevance": 0.40, "recency": 0.20, "frequency": 0.15, "user_feedback": 0.15, "trust_score": 0.10},
  "maintenance": {"last_light": "ISO8601", "last_deep": "ISO8601"}
}
```

**GET /v1/health/calibration** — 校准状态报告（0.0.16 新增，建议一）

**权限**：read

返回外部校准退化状态的详细报告——`level` 枚举（healthy=正常 <7 天 / degraded=7-14 天无校准 / virtual=14-30 天 / dormant=>30 天）为**运营可视化粗粒度映射**（实际降级模式由架构 §10.9 降级状态机按校准时延驱动，刻度粗于状态机周期——运营指示以状态机为准，本报告仅作提示）。

**响应** `200`：
```json
{
  "level": "degraded",
  "last_external_calibration": "2026-07-28T14:30:00Z",
  "days_since_last_calibration": 8,
  "active_mode": "virtual",
  "virtual_calibration_confidence_ceiling": 0.227,
  "recommended_action": "user_calibration_recommended"
}
```
`virtual_calibration_confidence_ceiling` 按衰减公式计算（`0.3 × exp(-λ × days)`，λ=0.02，见架构 §1.2 虚拟校准生成器）。

**GET /v1/health/memory-pressure** — 记忆压力状态（0.0.16 新增，建议四）

**权限**：read

返回四类压力信号指标与当前减压动作级别（架构 §5.2 压力信号族·三级减压动作）：

**响应** `200`：
```json
{
  "status": "elevated",
  "current_action_level": "L1",
  "triggered_at": "2026-08-05T14:00:00Z",
  "metrics": {
    "wm_occupancy": 0.83,
    "retrieval_failure_rate": 0.12,
    "redundancy_ratio": 0.35,
    "forgetting_backlog_ratio": 2.3
  },
  "active_mitigations": ["forgetting_scheduler_2x", "consolidation_skip_strategy_to_behavior"],
  "estimated_recovery": "1h after metrics normalize"
}
```

**GET /audit/compression** — 逐记忆压缩审计查询（0.0.16 新增，建议七）

**权限**：admin

**参数**：`memory_id`（必填）。返回该记忆的 `compression_trail` 压缩审计记录（data-model `memories.compression_trail`）。

**响应** `200`：
```json
{
  "memory_id": "mem_abc123",
  "compression_summary": {"total_compression_ratio": 0.37, "p6_status": "known_exceeded", "fully_carried_dimensions": 3, "partially_carried_dimensions": 2, "fully_compressed_dimensions": 1},
  "compressed_dimensions": [
    {"dimension": "cognitive_integrity_anti_example_coverage", "category": "cognitive_integrity", "compressed_to": "structural_value (0/1/2)", "compression_ratio": 1.0, "reason": "v0.1.0_semiquant_reduction", "recovery_debt": "D-306/D-311/D-312", "recovery_version": "v1.1", "compressed_at": "ISO8601"}
  ]
}
```

**GET /audit/compression/summary** — 压缩审计全局摘要（0.0.16 新增，建议七）

**权限**：admin

**响应** `200`：
```json
{
  "version": "v0.1.0",
  "overall_compression_ratio": {"core_12d": 0.33, "full_14d": 0.43},
  "p6_threshold": 0.30,
  "status": "known_exceeded",
  "dimensions_fully_carried": ["usage_value", "witness_value", "time_physical_decay"],
  "dimensions_partially_carried": ["time_logical_causal", "accessibility"],
  "dimensions_semiquant_reduced": ["cognitive_integrity"],
  "recovery_target": "v1.1",
  "capability_matrix_ref": "references/capability_matrix.yaml"
}
```

**GET /v1/evolution/{id}** — 查询知识演化链

**权限**：read

**响应** `200`：`{"knowledge_id": "...", "chain": [{"source_id": "...", "target_id": "...", "relation_type": "replaces", "confidence": 0.85}]}`

### 6.6 Playbook API

**POST /v1/playbooks** — 创建 Playbook candidate

**权限**：write

```json
{
  "task_class": "deployment",
  "title": "Docker deploy with rollback",
  "trigger": "用户请求部署",
  "goal": "实现零停机部署",
  "steps": [{"number": 1, "capability_class": "shell", "action": "docker build ...", "evidence_required": true, "why": "确保一致性"}],
  "pitfalls": [{"description": "端口冲突", "frequency": 0.3}],
  "verification": ["curl health-check"],
  "cleanup": ["docker rm temp"],
  "related_skills": ["devops"]
}
```

**响应** `201`：`{"id": "pb_abc123", "status": "candidate", "confidence": 0.5}`

**GET /v1/playbooks/search** — 搜索 Playbook

**权限**：read

**Query**：`?query=docker+deploy&task_class=deployment&status=promoted&limit=5`

**POST /v1/playbooks/{id}/feedback** — 记录 Playbook 使用反馈

**权限**：write

```json
{
  "outcome": "success | partial | failed | stale | misleading",
  "evidence": ["health-check passed"],
  "preconditions_checked": ["port 80 free"],
  "steps_completed": [1, 2, 3],
  "model_name": "gpt-4"
}
```

**响应** `200`：`{"id": "pb_abc123", "outcome": "success", "status": "promoted", "confidence": 0.65}`

### 6.7 Recall Funnel API

**GET /v1/search/explain** — 检索附带 recall funnel trace

**权限**：read

**Query**：`?q=docker&include_trace=true`

**响应** `200`：
```json
{
  "results": [...],
  "trace": {
    "stages": {"lexical_candidates": 200, "vector_candidates": 150, "final_candidates": 10, "returned": 5},
    "timings_ms": {"total": 245, "lexical": 30, "vector": 180, "rerank": 35},
    "character_budget": 3000
  }
}
```

### 6.8 MCP Bridge 工具映射

MCP Bridge 不通过 REST API 暴露，而是通过独立的 MCP 服务器进程注册到 Hermes Agent。技术规格见 `src/access/mcp/bridge.py`。工具清单共 **15 个**（基础工具集 12 + 关系管理 3，构成口径见架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a；十二规范操作集见架构 §7.3.1）——下表为 MCP Bridge 工具注册的权威清单。

| 工具 | 功能 | 等价 REST 操作（内部路由映射，部分非独立公开端点） |
|:----|:-----|:--------------|
| `kairos_store_memory` | 存储记忆 | POST /v1/memories |
| `kairos_search_memories` | 三信号混合检索 | POST /v1/memories/search （定义见 §1） |
| `kairos_get_hot_memories` | 热度最高记忆 | GET /v1/memories/heat-top （定义见 §1） |
| `kairos_search_graph` | 图谱检索 | POST /v1/graph/search |
| `kairos_extract_entities` | 实体提取 | POST /v1/entities/extract |
| `kairos_get_memory_traces` | 记忆生命周期历史 | 操作目录 §3 |
| `kairos_feedback_memory` | 可信度反馈 | POST /v1/memories/{id}/feedback （定义见 §1） |
| `kairos_calibrate` | 校准信号 | POST /v1/calibrate |
| `kairos_get_stats` | 记忆库报告 | GET /v1/memories/stats （定义见 §1） |
| `kairos_search_sessions` | 会话搜索 | GET /v1/sessions |
| `kairos_tree` | 路径浏览 | GET /v1/path/tree |
| `kairos_delete_memory` | 软删除记忆 | DELETE /v1/memories/{id} |
| `kairos_link` | 创建两条记忆间的有向关系边（from_uri → uris，支持批量链接；必填 `reason`，可选 `relation_type` 基础六值 + 语义标记扩展、`confidence`，权威枚举见 [data-model.md](data-model.md) memory_relations 表） | —（无独立公开 REST 端点，经 MCP 工具直连关系索引，见架构 §7.1a 关系管理 API） |
| `kairos_unlink` | 移除两条记忆间的指定关系边（按 `relation_type` 精确匹配或 `relation_type=*` 全删；软删除保留审计追溯） | —（同上） |
| `kairos_relations` | 查询某记忆的所有关系边（`{inbound, outbound}`，支持 `relation_type` 过滤与 `direction` 限定） | —（同上） |

### 6.9 知识加工区 API

**POST /v1/halls/promote** — 将记忆从加工区推进到验证区或正式库

**权限**：write

```json
{
  "memory_id": "uuid",
  "target_hall": "validation | canonical",
  "gate_notes": "差异检验通过"
}
```

**响应** `200`：`{"memory_id": "uuid", "from": "processing", "to": "validation", "gate": "passed"}`

**POST /v1/halls/demote** — 将记忆从验证区退回加工区

**权限**：write

```json
{
  "memory_id": "uuid",
  "reason": "差异检验未通过，待重新蒸馏"
}
```

**响应** `200`：`{"memory_id": "uuid", "from": "validation", "to": "processing"}`

**GET /v1/halls/{hall}** — 查询指定区域内的记忆列表

**权限**：read

**Query**：`?user_id=default&limit=20`

### 6.10 端云同步 API

**POST /v1/sync/push** — 推送本地增量修改至服务端

**权限**：write

```json
{
  "user_id": "default",
  "batch": [
    {"memory_id": "uuid", "operation": "update", "sync_version": 5, "content": "..."}
  ]
}
```

**响应** `200`：`{"synced": 10, "conflicts": 1, "conflict_ids": ["uuid"]}`

**冲突解决策略**：以服务端见证锚定为主副本仲裁。终端推送时若 sync_version 冲突（终端版本 < 服务端当前版本），服务端返回 conflict 标记，终端在下一同步周期接收服务端裁决结果（以服务端内容为准）。

**POST /v1/sync/pull** — 拉取服务端增量变更

**权限**：read

```json
{
  "user_id": "default",
  "last_synced_at": "ISO8601",
  "limit": 100
}
```

**响应** `200`：`{"memories": [...], "pulled_version": 42, "has_more": false}`

**POST /v1/sync/export** — 导出完整数据快照（.kairos 格式）

**权限**：read

```json
{"user_id": "default", "include_vectors": true}
```

**响应** `200`：返回 `.kairos` 二进制文件

**POST /v1/sync/import** — 导入数据快照

**权限**：admin

```json
{"file": ".kairos 二进制数据", "mode": "merge"}
```

---

## 7、错误码体系

> **声明**：本表为 HTTP 级错误码常用子集；全量 38 个错误码及其分类（API 返回/内部日志）以 [error-reference.md](../references/error-reference.md) 为权威来源。

> **说明**：以下为 HTTP 级错误码子集。完整内部错误码集（含 DB/LLM/SYS 类）见 [references/error-reference.md](../references/error-reference.md)。调用方应仅按此表处理 API 响应中的错误码。

| 错误码 | HTTP 状态 | 说明 | 恢复建议 |
|:------|:---------|:-----|:---------|
| `ERR-AUTH-001` | 401 | API Key 无效 | 检查 `KAIROS_API_KEY` |
| `ERR-AUTH-002` | 401 | API Key 已过期/被吊销 | 生成新 Key |
| `ERR-AUTH-003` | 403 | 权限不足 | 升级 API Key 级别 |
| `ERR-RATE-001` | 429 | 写入限流 | 等待后重试 |
| `ERR-RATE-002` | 429 | 读取限流 | 等待后重试 |
| `ERR-INPUT-001` | 413 | 内容超长 | 减少内容长度 |
| `ERR-INPUT-002` | 400 | 路径格式无效 | 检查 kairos:// 格式 |
| `ERR-INPUT-003` | 422 | 路径深度超限（超过 10 层） | 减少路径层级 |
| `ERR-INPUT-004` | 422 | 语义校验失败（缺少必填字段，如 content / path） | 检查请求体必填字段 |
| `ERR-SEC-001` | 403 | 安全红线违反 | 检查操作是否符合红线约束 |

> **说明**：`ERR-DB-*`、`ERR-LLM-*`、`ERR-SYS-*` 为内部运维与日志使用码，API 不直接返回。上表仅列出 HTTP 级错误码。完整错误码集见 [references/error-reference.md](../references/error-reference.md)。

---

## 8、叙事线 API

> **定位**：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「Saga 命名叙事线」的外部接口。
> **被架构引用**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2（叙事线端点）——本章节号变更须同步回改。
>
> **v0.1.0 子集声明（0.0.16 决策,建议五）**：本批次落地最小子集——创建/添加记忆/按叙事线检索/手动完结四操作（纯数据库实现,无 LLM 依赖）。`summarize` 端点需 LLM 调用,标注为 v1.1 启用;自动聚合（知识演化自动加入、Deep 聚类创建）与自动完结（90 天空闲）为 v1.1 目标。成员有序列表由 `narrative_threads.memory_ids` 数组承载（不新增 position 列）。

### POST /v1/narrative/threads — 创建叙事线（v0.1.0 子集）

**权限**：write

```json
{
  "name": "项目 A 架构演进",
  "description": "从单体到微服务的迁移过程中的关键技术决策",
  "type": "linear",
  "metadata": {"project": "project-a"}
}
```

**响应** `201`：`{"id": "uuid", "name": "...", "status": "open", "type": "linear", "created_at": "ISO8601"}`

### POST /v1/narrative/threads/{id}/members — 添加记忆至叙事线（v0.1.0 子集）

**权限**：write

```json
{"memory_id": "uuid", "context_note": "这是引入消息队列的关键会议记录"}
```

- 已完结叙事线拒绝新成员（400 `ERR-INPUT-004`）；同一记忆重复添加（已存在于 memory_ids）返回 200 幂等成功。
- **响应** `201`：`{"id": "uuid", "thread_id": "uuid", "memory_id": "uuid", "position": 3, "added_at": "ISO8601"}`（position 为追加顺序序号）

### GET /v1/narrative/threads/{id}/memories — 按叙事线检索记忆（v0.1.0 子集）

**权限**：read

**Query**：`?order=position|occurred_at&limit=50`（默认按 memory_ids 顺序）

**响应** `200`：
```json
{
  "thread": {"id": "uuid", "name": "...", "status": "open"},
  "members": [{"memory_id": "uuid", "memory_summary": "2026-04 决策:引入 RabbitMQ", "occurred_at": "ISO8601", "added_at": "ISO8601"}],
  "total": 3
}
```

### POST /v1/narrative/threads/{thread_id}/summarize — 生成叙事线摘要

**权限**：write

行为：(1) 提取叙事线中所有记忆的 content 和 metadata；(2) LLM 调用生成结构化输出——summary（≤500字）、key_turning_points、coherence_score（0-1）、open_questions；(3) 结果写入 narrative_threads.description 和 coherence_score；(4) 若 coherence_score < 阈值（默认 0.4），触发元认知层低自洽度告警。

**响应** `200`：`{"summary": "...", "coherence_score": 0.85, "key_turning_points": [...], "open_questions": [...]}`

### POST /v1/narrative/threads/{id}/complete — 标记叙事线完结

**权限**：write

叙事线完结后不再参与自动扩展，仅作为历史叙事存档。

**响应** `200`：`{"id": "uuid", "status": "completed"}`

---

## 9、压缩管理 API

> **定位**：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「双模式 Compaction」的管理接口。
> **被架构引用**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2（压缩端点）——本章节号变更须同步回改。

### POST /v1/admin/compaction/run — 手动触发压缩

**权限**：admin

**Query**：`?mode=all` — 全量全局压缩。sliding_window 模式由后台自动触发，不需手动调用。

**响应** `200`：`{"mode": "all", "compressed_count": 150, "snapshot_ids": [...]}`

### POST /v1/admin/compaction/rollback/{snapshot_id} — 展开压缩快照

**权限**：admin

恢复源记忆的 `compacted=false` 状态。已过去 >30 天的压缩不可回滚。

**响应** `200`：`{"snapshot_id": "uuid", "restored_memory_ids": [...]}`

---

## 10、因果链路 API

> **被架构引用**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2（因果链路手动标注端点）——本章节号变更须同步回改。

### POST /v1/causal — 手动标注因果链路

**权限**：write

```json
{
  "source_id": "uuid",
  "target_id": "uuid",
  "predicate": "causes | caused_by | enables | prevents",
  "confidence": 0.8,
  "evidence": "A 导致 B 的原因描述"
}
```

**响应** `201`：`{"id": "uuid", "predicate": "causes", "confidence": 0.8}`

---

## 11、事实三元组直接注入 API（P3，v1.1+）

> **P3 前瞻**：架构 P3-09「事实三元组直接注入」。v0.1.0 不交付，端点预留。

### POST /v1/facts — 直接写入事实三元组

**权限**：write

绕过 LLM 提取管道，(subject, predicate, object) 三元组直接写入实体知识图谱和关系索引。遵循 ADD-only 协议——不覆盖已有事实，以叠加模式追加。同一三元组的重复写入不产生新记录（基于三元组哈希去重）。

```json
{
  "facts": [
    {
      "subject": "kairos://entities/project-alpha",
      "predicate": "uses_technology",
      "object": "kairos://entities/postgresql",
      "confidence": 1.0,
      "source": "connector:github",
      "evidence": "package.json dependency",
      "timestamp": "2026-07-27T10:00:00Z"
    }
  ],
  "options": {
    "bypass_llm_extraction": true,
    "direct_index": true,
    "link_memory_ids": ["mem_123"]
  }
}
```

**响应** `201`：`{"written": 1, "duplicates": 0, "errors": []}`

---

## 12、边类型管理 API（P3，v1.1+）

> **P3 前瞻**：架构 P3-10「自定义边类型签名验证」。v0.1.0 不交付。

### POST /v1/edge-types — 注册新边类型签名

**权限**：admin

**请求体**：

```json
{"type": "causal", "valid_combinations": [["causal", "temporal"]], "description": "自定义边类型签名"}
```

**响应** `201 Created`：`{"type": "causal", "status": "registered"}`

**错误**：`400`（签名格式无效）、`401`（认证失败）、`409`（类型已存在）

### GET /v1/edge-types — 查询已注册边类型签名

**权限**：read

**响应** `200 OK`：

```json
[{"type": "causal", "valid_combinations": [["causal", "temporal"]], "status": "registered"}]
```

**错误**：`401`（认证失败）

### PUT /v1/edge-types/{type} — 更新边类型合法组合

**权限**：admin

> 更新不影响已有边——仅对新写入生效。

**请求体**：

```json
{"valid_combinations": [["causal", "temporal"]], "description": "更新合法组合"}
```

**响应** `200 OK`：`{"type": "causal", "status": "updated"}`

**错误**：`400`（组合非法）、`401`（认证失败）、`404`（类型不存在）

---

## 13、技能管理 API

> **定位**：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「技能管理系统」的外部接口。

### GET /v1/skills — 搜索/列出技能

**权限**：read

**Query**：`?query=docker&category=devops&status=active&include_archived=true&limit=10`

**响应** `200 OK`：

```json
{"items": [{"id": "uuid", "name": "docker", "category": "devops", "status": "active", "confidence": 0.8}], "total": 1}
```

**错误**：`401`（认证失败）

### POST /v1/skills/{id}/supersede — 标记技能被替代

**权限**：write

```json
{"superseded_by": "skill-uuid", "reason": "新技能覆盖了此技能的功能"}
```

**响应** `200`：`{"id": "uuid", "status": "superseded", "superseded_by": "skill-uuid"}`

### POST /v1/skills/{id}/reactivate — 重新激活已归档技能

**权限**：write

从 archived → experimental，置信度重置为 0.5，重新进入验证周期。

**响应** `200`：`{"id": "uuid", "status": "experimental", "confidence": 0.5}`

---

## 14、Connector 管理 API

> **定位**：架构 [detailed-design.md](detailed-design.md) §11.2「Connectors 同步模式」的外部接口。

### POST /v1/connectors/register — 注册外部平台 Connector

**权限**：admin

```json
{
  "connector_type": "gmail | drive | notion | github",
  "config": {
    "auth": {"type": "oauth2", "token": "..."},
    "webhook_secret": "...",
    "filters": {"labels": ["important"], "folders": ["project-alpha"]}
  },
  "sync_options": {
    "full_sync_on_register": true,
    "poll_interval_sec": 300,
    "extract_entities": true,
    "max_items_per_sync": 50
  }
}
```

**响应** `201`：`{"connector_id": "uuid", "status": "active"}`

---

## 15、Profile Schema 管理 API

### PUT /v1/profile/schema — 注册/更新自定义 Profile Schema

**权限**：admin

Schema 版本化——修改后自动递增 `schema_id` 后缀，旧 Schema 保留供历史 Profile 数据回溯。

**请求体**：ProfileSchema JSON 对象（见架构 [detailed-design.md](detailed-design.md) §11.3 ProfileSchema 结构）。

**响应** `200`：`{"schema_id": "developer-v2", "previous_schema_id": "developer-v1"}`

---

## 16、管理导入导出 API

### POST /v1/admin/export — 导出 .kairos 备份包

**权限**：admin

```json
{
  "options": {
    "include_vectors": true,
    "include_journal": false,
    "compression": "deflate"
  }
}
```

**响应** `200`：Content-Type: application/zip，Content-Disposition: attachment; filename="kairos-export-20260727.kairos"

### POST /v1/admin/import — 导入 .kairos 备份包

**权限**：admin

Content-Type: multipart/form-data。`conflict_resolution`：fail / overwrite / skip。

**响应** `200`：`{"imported": 15420, "skipped": 0, "conflicts": 0, "errors": []}`

### POST /v1/admin/consistency-check — 手动触发一致性检查

**权限**：admin

```json
{
  "checks": ["C1", "C2", "C4"],
  "path_prefix": "kairos://users/abc/"
}
```

**响应** `200`：`{"checks_run": 3, "issues_found": 2, "auto_fixed": 1, "details": [...]}`

---

## 17、图谱可视化 API

### GET /v1/graph/render — 导出知识图谱可视化

**权限**：read

**Query**：`?type=mermaid&layout=TD&path_prefix=kairos://projects/alpha/&max_nodes=50`

渲染实体知识图谱、关系索引、因果链路为 Mermaid 图（SVG/PNG 格式）。

**响应** `200`：SVG 或 PNG 二进制数据（Content-Type: image/svg+xml 或 image/png）

---
## 18、资源摄取与多模态

### 18.1 资源摄取 API

接入层提供统一的资源摄取接口 `add_resource`，支持文件、URL、Sitemap、RSS 四类外部资源的声明式注册与定时刷新——将外部知识源的变更自动同步至 Kairos 记忆库。

**资源类型与摄取策略**：

| 资源类型 | `resource_type` | 摄取方式 | 默认契约 | 默认路径前缀 |
|:--------|:---------------|:--------|:--------|:-----------|
| 本地文件 | `file` | 读取文件内容 → 文本提取（PDF/DOCX/Markdown/TXT） | 环境 | `kairos://projects/{id}/files/` |
| 网页 URL | `url` | HTTP GET → HTML→Markdown 提取（可配置 CSS selector 聚焦） | 按需 | `kairos://users/{id}/inbox/web-pages/` |
| Sitemap | `sitemap` | 解析 sitemap.xml → 批量递归抓取子 URL（深度可控） | 环境 | `kairos://projects/{id}/docs/` |
| RSS/Atom Feed | `rss` | 轮询 feed → 增量提取新条目 | 环境 | `kairos://users/{id}/inbox/feeds/` |

**`add_resource` 接口 Schema**：

```text
{
  "resource_type": "file|url|sitemap|rss",
  "uri": "file:///path/to/doc.pdf | https://example.com/page | https://example.com/sitemap.xml | https://example.com/feed.xml",
  "options": {
    "selector": "article.main-content",     // CSS selector 聚焦（url/sitemap 类型）
    "max_depth": 3,                         // Sitemap 递归深度上限（默认 3）
    "extract_entities": true,               // 是否自动触发实体提取（默认 true）
    "chunk_size": 2000,                     // 长文档分块大小（字符，默认 2000）
    "chunk_overlap": 200                    // 分块重叠（字符，默认 200）
  },
  "watch_interval": 3600,                   // 定时刷新间隔（秒），0 或不设置 = 仅摄取一次
  "contract": "permanent|ondemand|environmental|temporary|intention",  // 契约类型（五值枚举，权威定义见 data-model memories.contract；intention 仅系统内部 kairos://_system/intentions/ 路径使用），默认 environmental
  "path_prefix": "kairos://projects/{id}/docs/"         // 目标路径前缀（可选，自动推断）
}
```

**`watch_interval` 定时刷新机制**：

- `watch_interval > 0` 时，资源注册至后台维护引擎（§5）的 **资源监控注册表**（Resource Watch Registry），按配置间隔周期性触发重新摄取
- 重新摄取时执行**增量差异检测**——对比上次摄取内容的 SHA-256 哈希，仅写入变更部分
- Sitemap/RSS 类型：仅抓取自上次摄取后新增或变更的 URL/条目。Sitemap 使用 `lastmod` 字段判断，RSS 使用 `pubDate` 字段判断
- 文件类型：使用 OS 文件系统事件（inotify/ReadDirectoryChangesW）监听变更，无变更时跳过重读
- 刷新失败（网络超时、文件不存在等）时记录至使用事件总线（标记 `resource_refresh_failed`），不阻塞其他资源的刷新周期
- 连续失败 N 次（默认 3）后，资源自动标记为 `stale` 并暂停刷新，等待管理员手动恢复

**高信用源判定**：
- 本地文件（`file://` 协议）和用户显式注册的资源视为高信用源——跳过四层递进式摄取防御（§7.4b）的全部 Stage，但仍通过 S-15 来源可鉴别校验
- URL/Sitemap/RSS 类型经完整摄取验证门禁

**批量注册**：支持通过 `add_resources`（复数形式，接受资源列表数组）批量注册多个资源，原子性保证——任一资源注册失败则整体回滚（不实施部分注册）。

---

### 18.2 多模态消息 Part 统一接口

Kairos v0.1.0 的消息接口统一采用 **Part 抽象**——将文本、图片、工具调用等多种消息形态统一为可组合的 Part 子类型，消除传统消息接口中「text 是字符串、image 是 URL、tool_call 是 JSON」的结构不一致性。

**设计理念**：一条消息（Message）由一个或多个 Part 组成——Part 是消息的最小语义单元。所有 Part 共享统一的序列化/反序列化接口，上层消费方（编译器、存储层、检索管线）仅需处理一种抽象。

**Part 类型体系**：

```text
MessagePart（抽象基类）
    ├─ TextPart          文本片段
    ├─ ImagePart         图片片段（支持 data URI / URL 两种格式）
    ├─ ToolPart          工具调用/返回片段
    ├─ FilePart          文件附件（v1.1 规划）
    └─ AudioPart         音频片段（v1.1 规划）
```

**统一 Schema**——所有 Part 共享的基类字段：

```text
Part {
  "type": "text" | "image" | "tool_call" | "tool_result",
  "index": int,              // Part 在消息内的序位（0-based）
  "metadata": {              // 通用元数据（可选）
    "role": "user" | "assistant" | "tool",
    "timestamp": int64,
    "encoding": "utf-8" | "base64"
  }
}
```

**TextPart**——纯文本片段：

```text
TextPart {
  "type": "text",
  "text": string,            // 文本内容（UTF-8）
  "language": "zh" | "en" | "auto",  // 语言标记，默认 auto
  "truncated": bool           // 是否因长度限制被截断
}
```

**示例**：
```json
{
  "type": "text",
  "index": 0,
  "text": "请分析这段代码的性能瓶颈",
  "language": "zh"
}
```

**ImagePart**——图片片段，支持两种输入格式：

```text
ImagePart {
  "type": "image",
  "format": "data_uri" | "url",
  // 格式一：data URI（适合小图片、截图、内联图片）
  "data_uri": string | null,   // "data:image/png;base64,iVBORw0K..."
  // 格式二：远程 URL（适合大图片、外部链接）
  "url": string | null,        // "https://example.com/diagram.png"
  "mime_type": string,         // "image/png" | "image/jpeg" | "image/webp" | ...
  "width": int | null,         // 图片宽度（像素）
  "height": int | null,        // 图片高度（像素）
  "alt_text": string | null,   // 无障碍替代文本
  "size_bytes": int | null     // 文件大小（字节）
}
```

**格式判定规则**：
- `format = "data_uri"` 时，`data_uri` 必填，`url` 可为空
- `format = "url"` 时，`url` 必填，`data_uri` 可为空
- 两者同时存在时以 `format` 声明的格式为准，另一字段作为备用引用

**ImagePart 处理管线**：

```text
ImagePart 输入
    │
    ├─ format = "data_uri"
    │     ┌─ Base64 解码
    ├─ MIME 类型验证（白名单：png/jpeg/webp/gif/svg+xml）
    ├─ 尺寸检查：≤ 最大尺寸配置值
    └─ 可选：生成缩略图（≤ 最大缩略图尺寸配置值）
    │
    └─ format = "url"
          ┌─ URL 白名单/域名验证（可选，通过配置控制）
          ├─ HEAD 请求验证资源可达性（超时 3s）
          ├─ 下载至临时存储（≤ 最大尺寸配置值）
          └─ 失败 → 保留 URL 引用，content 字段标记为 "image_unavailable"
```

**存储策略**：
- data URI 图片：解码后以二进制 BLOB 存入 `image_blobs` 表，原始 data URI 保留在 `memories.content` 的 ImagePart 中作为溯源引用
- URL 图片：首次访问时下载并缓存至本地，后续检索时从缓存读取。缓存 TTL 见 [ops/configuration.md](../ops/configuration.md) §6.7
- 图片的语义向量：由多模态 embedding 模型（如 CLIP）生成，存入 `memories.embedding` 的图片专用向量空间（与文本向量独立存储，维度可不同）

**ToolPart**——工具调用/返回片段：

```text
ToolPart {
  "type": "tool_call" | "tool_result",
  // tool_call 字段
  "tool_name": string | null,    // 工具名称
  "arguments": object | null,    // 调用参数（JSON）
  "call_id": string | null,      // 工具调用唯一 ID
  // tool_result 字段
  "result": string | null,       // 工具返回内容
  "is_error": bool,              // 是否为错误返回
  "result_truncated": bool       // 返回结果是否被截断
}
```

**示例——工具调用**：
```json
{
  "type": "tool_call",
  "index": 2,
  "tool_name": "read_file",
  "arguments": {"path": "/app/config.yaml"},
  "call_id": "call_abc123"
}
```

**示例——工具返回**：
```json
{
  "type": "tool_result",
  "index": 3,
  "call_id": "call_abc123",
  "result": "server:\n  port: 8080\n  host: 0.0.0.0",
  "is_error": false
}
```

**消息组装——Message 结构**：

```json
{
  "message_id": "uuid",
  "session_id": "string",
  "role": "user | assistant | tool",
  "parts": [
    {"type": "text", "index": 0, "text": "请分析这个架构图：", "language": "zh"},
    {"type": "image", "index": 1, "format": "data_uri", "data_uri": "data:image/png;base64,...", "mime_type": "image/png"},
    {"type": "text", "index": 2, "text": "并检查以下错误：", "language": "zh"},
    {"type": "tool_result", "index": 3, "call_id": "call_xyz", "result": "Error: connection refused", "is_error": true}
  ],
  "timestamp": 1700000000000000000
}
```

**Part 与结构化通信单元的集成**：

多模态 Part 在编译器（§7.0 结构化通信单元）处理时转换为统一的内部表示——编译器读取 Message 的 `parts` 数组，按序处理每个 Part：
- TextPart → 文本净化 + 意图理解（编译器 L1+L2），输出 `payload.type = "text"`
- ImagePart → 如启用多模态 embedding，生成图片语义向量并入 `payload`；否则将 alt_text / URL 作为文本附件嵌入
- ToolPart → 提取工具调用序列和结果，作为 `payload.type = "structured"` 的结构化上下文，参与检索排序的工具调用信号维度

> **配置参数**：多模态支持的图片尺寸、缓存和多模态 embedding 参数见 [ops/configuration.md](../ops/configuration.md) §6.7。

**v0.1.0 范围与 v1.1 规划**：

v0.1.0 交付：
- TextPart、ImagePart（data URI + URL）、ToolPart 的完整序列化/反序列化
- ImagePart 的存储（BLOB + 缓存）和基础验证（MIME 白名单、尺寸限制）
- conversation_messages 表的 parts 列（JSONB）存储 Part 数组

v1.1 规划：
- FilePart（文件附件，含 office 文档、PDF 的文本提取管线）、AudioPart（音频片段，含语音转文本管道）
- 多模态 embedding（CLIP/SigLIP）启用，图片可参与语义检索排序
- Part 级访问控制（敏感图片不进入 LLM 上下文但保留在存储层）

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 接口规格：REST API 78 端点、Agent Tool、CLI、MCP 工具与事件消息格式。 |
| 0.0.2 | 2026-08-04 | RC-19 补顶层 REST 端点与 Agent Tool 响应定义；D-13 端点计数口径（78 业务端点 + 1 探针 = 79）。 |
| 0.0.3 | 2026-08-04 | 全库深度审计修复：回滚端点安全红线 S-14（语境自指禁令）误标修正为 S-08（未授权管理访问拒绝）。 |
| 0.0.4 | 2026-08-04 | 全库深度审计修复：§7 错误码表补权威来源声明（error-reference 为准）、stats/health-detail by_state 合计修正为与 total 一致、memories_list_recent/memories_merge JSON 块对调、§6.8 冗余端点行删除。 |
| 0.0.5 | 2026-08-04 | 文档职责剥离承接（changelog 0.0.9 批次）：新增 §18 资源摄取与多模态——§18.1 资源摄取 API（add_resource 四类资源）、§18.2 多模态消息 Part 统一接口（5 种 Part schema），承接自架构 §7.3e/§7.3i。 |
| 0.0.6~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.6~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：§18.2 空表清理；§6.8 MCP 工具清单引用改指 §7.3.1。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：契约枚举唯一化、五项悬空端点补机制指针、priority 示例修正、chat_messages 表名修正、临时契约审计痕迹统一。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：DELETE 契约删除语义统一（permanent 拒删/ondemand+environmental 软删/temporary 硬删留痕）；S-07 导出脱敏「掩码+截断」口径与参数名统一（clearance=level）；HMAC 审计链公式统一为 threat-model 权威 5 项输入；memories_write 契约枚举补 intention 第五值；CLI 示例 `kairos_create_memory`→`kairos_store_memory`；MCP 工具集 15 个计数口径注记。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次（changelog 0.0.15，依 comprehensive-documentation-audit P1-01/P1-02）：资源摄取端点 contract 枚举补 intention 第五值（四值→五值，注释改指 data-model 权威）；注册竖切 M-05 归档端点 `POST /v1/memories/{id}/archive` 与配套 `POST /v1/memories/{id}/restore`（对应架构 12 规范操作集 archive/restore，含幂等性/契约约束/潜伏势能重估匹配验证）；业务端点计数 78→80、物理总数 79→81（口径注记同步）。 |
| 0.0.16 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.16，建议一/四/五/七落地）：检索响应补 meta.calibration_status 与 nudge 可选字段；新增 GET /v1/health/calibration、GET /v1/health/memory-pressure、GET /audit/compression、GET /audit/compression/summary 四端点；§8 叙事线 API 补 v0.1.0 子集声明与 create/members/memories 三端点。（0.0.25 勘误补登：业务端点计数 80→85、物理总数 81→88，口径注记同步） |
| 0.0.20 | 2026-08-05 | 第五轮全库深度审计修复批次（changelog 0.0.20）：§6.5/§8/§9/§10 补「被架构引用」反向注记（架构引用本章节时须同步回改，防章节号漂移）。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：端点计数重算 80→85、物理总数 81→88（口径注记同步 + 0.0.16 条目勘误补登）；顶层章节标题统一数字（一~十八→1~18）与中文序引用同步；前瞻记忆引用 §8→§3.2。 |
| 0.0.26~0.0.27 | 2026-08-06 | (合并占位：changelog 0.0.26/0.0.27 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景) |
| 0.0.28 | 2026-08-06 | 第十轮全库深度审计修复批次（changelog 0.0.28）：§6.8 MCP Bridge 工具表补关系管理 3 工具（kairos_link/kairos_unlink/kairos_relations，15 口径统一）；指引段 §7.3.1→§7.1a 并注明 15 构成；§1.4 archive 引用 §7.3→§7.3.1；sessions/evolution 路径占位符统一为 {id}。 |

> **端点计数口径（2026-08-03 决策 D-13；0.0.15 更新；0.0.25 勘误）**：全库声明的 **85** 指 **`/v1` 前缀的业务端点**去重后的 `(METHOD, PATH)` 组合数（0.0.15 注册 `archive`/`restore` 两个竖切端点后 78→80；0.0.16 新增 `health/calibration`、`health/memory-pressure` 与叙事线三端点后 80→85）。另有 **3 个**无 `/v1` 前缀端点：基础设施探针 `GET /health`（见 §健康检查）与压缩审计端点 `GET /audit/compression`、`GET /audit/compression/summary`（见 §9），**不计入**业务端点总数。因此本文档定义的 HTTP 端点物理总数为 **88** = 85 业务端点 + 3 无前缀端点。引用端点数时须注明口径，避免再次产生 80/81/85/88 歧义。
