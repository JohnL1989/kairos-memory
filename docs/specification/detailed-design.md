---
title: Kairos 详细设计
aliases:
  - 组件设计
  - 详细设计
  - detailed-design
tags:
  - kairos
  - design
  - implementation
created: 2026-07-21
updated: 2026-08-10
last_reviewed: 2026-08-10
status: draft
---

> **说明**：本文为施工图纸（设计稿），组件状态见下方索引表。待首迭代完成核心 3 组件后晋升为 v0.1.0。当前 status=draft，非发布版本。

# Kairos 详细设计

> **定位**：[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) 是「鸟瞰图」，本文是「施工图纸」——每个核心组件的内部结构、状态机、核心算法伪代码、接口定义。代码启动后第一个迭代内完成核心 3 组件（WM 管理器 / 存储引擎 / 遗忘引擎），校准调度器与事件总线同为 P0 但归入第二迭代，其余随开发补齐。

---

## 组件索引

| 组件 | 章节 | 优先级 | 状态 |
|:-----|:----:|:-----:|:----:|
| WM 管理器 | §1 | P0 | 待实现 |
| 存储引擎 | §2 | P0 | 待实现 |
| 遗忘引擎 | §3 | P0 | 待实现 |
| 升华管道（含 Reflect 反思循环） | §4 | P1 | 待实现 |
| 校准调度器 | §5 | P0 | 待实现 |
| 元认知检测器（含代理实现） | §6 | P1 | 待实现 |
| WM调度预处理器 | §7 | P1 | 待实现 |
| 事件总线 | §8 | P0 | 待实现 |
| 检索引擎（含去重/实体提取） | §9 | P0 | 待实现 |
| 注意力调度器（Token 预算/评分） | §10 | P1 | 待实现 |
| 编译与存储基础设施 | §11 | P1 | 待实现 |
| 探索治理 | §12 | P1 | 待实现 |

---

## §1 WM 管理器

### 职责边界

- 维护当前活跃记忆槽位（7±2）
- 管理检索候选集（路径 + 语义 + 关系多路径融合，情感通过关系标签注入）
- 与注意力调度器协作（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §9，全局资源分配）
- 提供WM调度预处理器子模块上下文

### 状态机

```text
         ┌─────────────┐
         │   IDLE      │ ← 无待办任务，等待输入
         └──────┬──────┘
                │ 检索请求到达
                ▼
         ┌─────────────┐
    ┌─→  │ RETRIEVING  │ ← 多路径并行检索
    │    └──────┬──────┘
    │           │ 候选集到达
    │           ▼
    │    ┌─────────────┐
    │    │ FUSING      │ ← 多路径交叉筛选+融合
    │    └──────┬──────┘
    │           │ 融合完成
    │           ▼
    │    ┌─────────────┐
    │    │ OPERATING   │ ← WM调度预处理器操作结果
    │    └──────┬──────┘
    │           │ 操作完成 / 超时
    │           ▼
    │    ┌─────────────┐
    └────│  STABILIZING│ ← 再稳定化（检索后）
         └──────┬──────┘
                │ 稳定化完成
                ▼
              IDLE
```

### 核心接口

```python
class WMManager:
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """多路径检索→融合→返回"""
        ...

    async def operate(self, context: WMContext) -> Action:
        """WM调度预处理器操作入口"""
        ...

    async def stabilize(self, memory_id: UUID):
        """检索后再稳定化"""
        ...
```

### 多路径融合算法（伪代码）

```text
FUSE(candidates_by_path):
    # 交集 → 直接进 WM
    intersection = INTERSECT(candidates_by_path)

    # 独有 → 按信息增益筛选
    unique = UNION(candidates_by_path) - intersection
    filtered = []
    for candidate in unique:
        gain = INFORMATION_GAIN(candidate, intersection)
        if gain > GAIN_THRESHOLD:  # v0.1.0 默认 0.15，可由 KAIROS_FUSE_GAIN_THRESHOLD 配置
            filtered.append(candidate)

    # 提取抑制：高并发低互补路径衰减
    for path_a, path_b in PAIRS_WITH_HIGH_OVERLAP(candidates_by_path):
        if MUTUAL_INFORMATION_GAIN(path_a, path_b) < 0:
            DECAY_WEIGHT(path_b, SUPPRESSION_FACTOR)  # v0.1.0 默认 0.3，可由 KAIROS_FUSE_SUPPRESSION_FACTOR 配置

    return intersection + filtered
```

---

## §2 存储引擎

### 职责边界

- 统一 LTM 存储（SQLite / PostgreSQL 后端抽象）
- 双副本管理（见证锚定主副本 + 使用权重影子副本）
- 路径空间索引（`kairos://` 前缀树）
- 关系索引（边+类型）
- 情感效价空间（VAD 三维独立存储）

### 数据流：写入路径

```text
写入请求
  │
  ▼
Access Layer → 验证门禁（高信用源豁免→跳过 raw）
  │
  ▼
写入 raw（processing）层（不可检索）
  │
  ▼
摄取验证环 → 失败 → 丢弃
  │ 通过
  ▼
升格为 item——经验证区（validation）推进至正式库（canonical）后可检索
（三区流转：raw 驻 processing 区，item 经 validation→canonical 两阶段推进，见 data-model memories.hall）
  │
  ├──→ 写入见证锚定主副本（强一致）
  ├──→ 初始化使用权重影子副本（最终一致）
  ├──→ 注册路径空间（前缀树插入）
  ├──→ 建立关系索引（若有关系标注）
  └──→ 记录情感效价（若有 VAD）
```

### 后端抽象接口

> **v0.1.0 首迭代（2026-07-31 竖切决策）**：实现 SQLite + sqlite-vec 后端；PostgreSQL + pgvector 适配在竖切验收后迭代。业务代码仅依赖下方 StorageBackend 抽象，方言差异（FTS5 vs tsvector、JSONB 等）收敛于各后端实现内部。

```python
class StorageBackend(ABC):
    @abstractmethod
    async def write(self, memory: Memory) -> UUID: ...

    @abstractmethod
    async def path_retrieve(self, prefix: str) -> list[Memory]: ...

    @abstractmethod
    async def vector_search(self, query: list[float], top_k: int) -> list[ScoredMemory]: ...

    @abstractmethod
    async def update_witness(self, memory_id: UUID, witness: dict): ...

    @abstractmethod
    async def update_usage(self, memory_id: UUID, delta: UsageDelta): ...
```

### 写入管线设计（外部理念吸收）

写入路径（本节「数据流：写入路径」）的可靠性设计三项约束——承接「写入失败→积累垃圾」「巩固失败→矛盾规则」两类失败模式（troubleshooting §二a）的正面约束：

**① 稳定 Memory Key 规范化策略**：同一事实的多次观测收敛到稳定写入键——Memory Key 由（用户域 + 规范化实体/主题锚点 + 路径前缀）确定性派生，规范化规则（大小写、别名、时态归一）在摄取门禁内统一执行；同 Key 的新观测按 ADD-only 协议（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3g）追加（relation_type=supplement）而非新建独立记忆，避免同一事实的多副本漂移；内容级去重由 `content_hash` 兜底（同哈希不新建记录，仅更新 usage_weight，见 [data-model.md](data-model.md) §1 memories `content_hash` 列）。

**② 幂等 + 乐观锁事务提交（事实源/日志/Outbox 三分）**：单次写入在单事务内三分提交——事实源（`memories` 主记录）、日志（`journal_entries` 原始轮次/审计链）、Outbox（事件总线持久化 `usage_events`）要么全部成功要么全部回滚（竖切事务开关 `KAIROS_BATCH_TRANSACTION_ENABLED`）；写入请求可携带 `Idempotency-Key` 请求头（可选）——提供时服务端以该键去重：同键重复提交不产生新记录（返回首次写入结果），键冲突且载荷不一致返回 409 `ERR-CTR-005`（幂等键冲突），未提供时按常规写入（重复提交可能产生重复记录）；并发更新经 `version` 乐观锁裁决（冲突返回 409 `ERR-DB-005`），冲突走版本链追加而非覆盖（版本链模型见 [data-model.md](data-model.md) §1 memories）。**两错误码分工**：`ERR-CTR-005` 为幂等键冲突（同键重复提交且载荷不一致），`ERR-DB-005` 为版本冲突（`If-Match` 与当前版本不一致，见 [api-spec.md](api-spec.md) §1.3）。

**③ 索引为派生视图可重建**：路径前缀树、FTS5 全文索引、向量索引、kNN 近邻表（`memory_semantic_knn`，见 [data-model.md](data-model.md) §8.16）均声明为事实源（`memories` 主记录）的**派生视图**——可由主记录确定性重建（重建与校验路径见 §11.5 一致性检查 C1~C8）；主记录是唯一事实源，任何索引损坏不损失数据、仅触发重建，禁止索引侧数据反写主记录。

---

## §3 遗忘引擎

### 职责边界

- 定时扫描遗忘候选（遗忘调度器）
- 计算遗忘得分（v1.1 完整目标：二维遗忘曲面 + 使用频率调制；**v0.1.0 落地为单曲线指数衰减**，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2）
- 潜伏势能重估（盲区驱动 + 前向关联扫描）
- 复兴加速通道（遗忘后悔补偿）

### 遗忘得分算法（伪代码）

> **权威口径**：本节以架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 遗忘调度器为权威定义（v0.1.0 单曲线指数衰减）。两处不一致时以架构 §5.2 为准。下文的「v1.1 目标」段为完整愿景，不在 v0.1.0 执行路径内。

> **返回值极性声明（防倒置）**：本函数返回 **freshness（新鲜度）**——**值越高越新鲜、越不该被遗忘**，与 v1.1 二维曲面的「遗忘得分」（值越高越该被遗忘，对应 `KAIROS_FORGETTING_SCORE_THRESHOLD`，见 [configuration.md](../ops/configuration.md) §3）**极性相反**。两者不可互换代入阈值比较。函数命名与返回值统一采用 freshness 语义；豁免记忆返回哨兵值而非数值 `0.0`，避免被误读为「新鲜度最低 = 最该遗忘」。

```python
EVALUATE_FRESHNESS(memory):
    # v0.1.0 权威算法（架构 §5.2 遗忘调度器·单曲线指数衰减）
    # 返回 freshness ∈ (0,1]：越高越新鲜（越不该遗忘），或哨兵 EXEMPT（豁免）
    # freshness = 2^(-days_since_last_access / HALF_LIFE)
    # 三阈值判定：freshness ≥ ACTIVE_THRESHOLD → active / [STALE_THRESHOLD, ACTIVE_THRESHOLD) → stale / < STALE_THRESHOLD → archived

    # 身份与结构豁免（见证豁免 S-10 + 结构性记忆守护）——先于计算判定，豁免记忆不产生 freshness 得分
    if memory.is_identity or memory.is_structure:
        return EXEMPT   # 哨兵值：不进入遗忘候选池、不参与状态转换、不参与遗忘排序（≠ 数值 0）

    days_since_last_access = (NOW - memory.last_access_at).days          # 与架构 §5.2 公式口径一致（freshness = 2^(-days_since_last_access / HALF_LIFE)）
    freshness = 2 ** (-days_since_last_access / HALF_LIFE)               # HALF_LIFE 默认 69 天（KAIROS_FORGETTING_HALF_LIFE）

    # 状态转换（与架构 §5.2 记忆状态机一致：Active→Stale→Archived）
    if freshness >= ACTIVE_THRESHOLD:             # 默认 0.3（KAIROS_FRESHNESS_ACTIVE_THRESHOLD）
        TRANSITION_STATE(memory, "active")
    elif freshness >= STALE_THRESHOLD:            # 默认 0.1（KAIROS_FRESHNESS_STALE_THRESHOLD）
        TRANSITION_STATE(memory, "stale")         # 降权参与检索，可被外部校准激活
    else:
        TRANSITION_STATE(memory, "archived")      # 归档至冷存储，可经潜伏势能重估端口复兴

    # 复兴通道：Archived→Active 由潜伏势能重估端口（latent_trigger）或外部校准信号触发
    # （架构 §5.2 状态转换表）——显式检索仅更新 last_access_at，不直接触发状态复兴
    # 衰减口径注记（防「检索即复兴」）：freshness 公式锚定 last_access_at（与架构 §5.2 一致），
    # 但 archived/stale 记忆经显式检索仅更新 last_access_at（用于使用统计与 5D 排序新鲜度调制），
    # 不改变状态——状态复兴必须经潜伏势能重估端口或外部校准信号显式触发（架构 §5.2 状态转换表），
    # 避免「检索即复兴」绕过状态机判定（对齐 §11.5 一致性检查 C4）。
    return freshness

# ── v1.1 目标（二维遗忘曲面 + 使用频率调制；不在 v0.1.0 执行路径内，仅供实现参考）──
# base_score = decontextualization_level × SIGMOID(age_days / AGE_DECAY_CONSTANT)   # AGE_DECAY_CONSTANT 默认 30 天
# frequency_mod = 1.0 / (1.0 + LN(1 + recent_use_count_30d))
# score = base_rate(contract) × base_score × frequency_mod
# 状态转换（候选两阶段）：得分 > 阈值 → CANDIDATING（标记遗忘候选）→ 候选期结束且无复兴命中 → SUPPRESSED（memories.status 五值平级枚举之一，非 archived 子态；由定向遗忘操作写入，经 restore 撤销）
# 物理删除仅由 forgetAfter 对 temporary 契约执行；suppressed 仅抑制检索、保留数据，与 archived 平级
```

### 遗忘调度器状态机

```text
          ┌──────────────┐
          │   SCHEDULING  │ ← 等待调度周期
          └──────┬───────┘
                 │ 周期到达
                 ▼
          ┌──────────────┐
          │   SCANNING    │ ← 遍历记忆计算 freshness
          └──────┬───────┘
                 │ freshness 判定（三阈值，与架构 §5.2 记忆状态机一致）
                 ▼
   ┌─────────────┬──────────────┬──────────────┐
   │ ≥ ACTIVE_THRESHOLD        │ [STALE, ACTIVE) │ < STALE_THRESHOLD
   ▼             ▼              ▼
   ACTIVE       STALE          ARCHIVED
   （正常参与检索） （降权检索）（归档至冷存储）
                 │              │
                 └──────────────┘ 复兴：潜伏势能重估端口 / 外部校准信号
                     → ACTIVE（架构 §5.2 状态转换表，非「再次被检索」直接触发）

注：temporary 契约记忆不进入本状态机——由 forgetAfter 基于 expires_at 被动过期硬删除
（架构 §5.2 forgetAfter，清理前写审计日志 expiry_cascade_delete）。
```

> **状态机范围注记**：本遗忘调度器状态机仅覆盖 freshness 驱动的 ACTIVE/STALE/ARCHIVED 三态（与架构 §5.2 记忆状态机五态平级口径一致；SUPPRESSED 由用户主动定向遗忘操作 `POST /v1/memories/{id}/suppress` 写入、SUPERSEDED 由知识演化 replaces 触发，均不经由本调度器）；temporary 契约例外见本图末行。Superseded 记忆经宪法修订端口恢复。

---

## §4 升华管道

### 触发条件

- 系统空闲（无待办任务、无检索请求）→ 自动触发
- 用户手动触发特定路径 `kairos sublimation trigger --path kairos://...`

### 四阶段流程

```text
raw（原始表征，不可检索）
  │
  │  验证通过（摄取门禁）
  ▼
item（标准表征，可检索）
  │
  │  空闲周期离线重组
  │  └─ 回放：稳定化不稳定记忆
  │  └─ 抽象萃取：从多条 item 提取模式 → strategy
  ▼
strategy（抽象模式，跨场景适用）
  │
  │  行为固化
  │  └─ 人工确认门控（必须确认，默认开——模拟产物未经实证不得转正，违反 S-13，见 [security/security-specification.md](../security/security-specification.md) §1 红线定义）
  ▼
behavior（自动化行为规则，不检索直接输出）
```

### 升华产物质量护栏（R-02）

**verbatim 拒绝**：strategy 阶段产物（抽象萃取/Reflect `done` 结论）与源 item 内容 verbatim 相同（或仅格式包装）时判定为**无效升华**——LLM 偷懒直接复制输入不产生抽象，收敛判据（§4.1，针对反思结论稳定性）无法拦截此失效模式。处理：拒绝该产物，标记 `sublimation_invalid` 审计事件（§10.10 事件总线），重试一次（重试输入附加「产物不得与源文本相同」指令）；重试仍 verbatim 相同则放弃本次升华，留待下个空闲周期（不进入 behavior 阶段，不触发人工确认门控）。

> 设计来源：会话压缩器的 verbatim 检查（摘要与最后一条消息完全相同则拒绝）——同一「模型复制输入冒充产出」失效模式的护栏结构。Kairos 的 Reflect 收敛判据（§4.1）与 verbatim 检查为两个独立维度：前者防「结论不稳定」，后者防「产物无抽象」。

### Compaction 成本-保真三 regime（外部理念吸收）

> 权威定义：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2「双模式 Compaction」（sliding_window / all），存储承载见 [data-model.md](data-model.md) §12 `compaction_snapshots`。双模式回答「何时压缩」，本 regime 框架回答「压缩成什么样、付出什么代价」。

| Regime | 成本形态 | 保真形态 | 定位 |
|:--|:--|:--|:--|
| **朴素累积**（naive accumulation） | 不压缩、逐条累积——检索/回放成本随条目数**二次方**增长（O(n²)） | 全保真（原始事实无损） | 数据量小、访问频率低时兜底；不可规模化 |
| **粗摘要**（coarse summary） | 摘要压缩成本**线性**（O(n)） | **准确性悬崖**——压缩比越过临界后关键细节（数值/决策/适用条件）批量丢失，准确性断崖式下降且无校验 | 仅作中间产物，不作为正式 regime |
| **验证压缩**（verified compression） | 压缩成本**线性** + 保真验证开销 | 压缩后经保真校验（关键事实/决策/适用条件保持率 ≥ 阈值）通过才提交，保真可量化 | **v0.1.0 目标 regime**——压缩产物落 `compaction_snapshots` 且保留源记忆（30 天回滚窗口，见 [data-model.md](data-model.md) §1 `compacted` 列） |

**选择规则**：默认验证压缩。压缩批量执行后进入观察窗口（`KAIROS_OBSERVATION_WINDOW_PERIODS`，见 [ops/configuration.md](../ops/configuration.md) §4）比对压缩前后检索质量指标（过时调用率/任务成功率改善，见 [quality/acceptance-criteria.md](../quality/acceptance-criteria.md) 记忆质量评估指标）——观察窗口内效用下降即回滚（`POST /v1/admin/compaction/rollback/{snapshot_id}`），并登记整合失败批次（见 [ops/troubleshooting.md](../ops/troubleshooting.md) 记忆整合失效排查）。

### 4.1 Reflect 反思循环

> 本节内容复制自架构 §5.19（文档职责剥离——实现细节落位于施工图纸，架构保留定位与机制描述）。

**定位**：Reflect 是升华管道中的自反思机制——将传统线性 Reflect（单次 LLM 调用输出反思文本）升级为 tool-calling 驱动的多轮 agentic 循环。Reflect agentic loop 赋予系统「检索自身记忆→观察模式→更新认知模型→判定收敛」的结构化反思能力，替代「让 LLM 写一段反思」的朴素实现。

**设计动机**：线性 Reflect 存在三项结构性缺陷——(a) **反思浅表化**：单次 LLM 调用无法区分「检索了什么证据」与「得出了什么结论」，反思沦为对对话片段的摘要而非对认知过程的审查；(b) **证据不可追溯**：反思结论无法回溯到具体的记忆观察，后续审计无法验证反思质量；(c) **收敛不可判定**：单轮反思无法判定「还需要更多证据」还是「已可得出结论」。

Reflect agentic loop 通过 tool-calling 循环解决上述问题：每次反思循环是一个独立的工具调用回合，Agent 自主决定调用哪些工具、何时终止，每步的工具输出作为下一步的观测输入。

#### 工具集

Reflect loop 暴露四类只读工具（仅查询，不修改记忆内容）：

| 工具 | 功能 | 输入 | 输出 |
|:-----|:-----|:-----|:-----|
| **`recall`** | 从存储层检索相关记忆 | `query: string`, `max_results: int`, `domain_filter?: string` | 排序后的记忆列表（含 `path`、`content_summary`、`narrative_coherence_score`、`timestamp`） |
| **`search_observations`** | 在自观察记忆（meta-LTM）中搜索历史治理动作后效 | `governance_type?: string`, `time_window?: [start, end]`, `outcome_filter?: "success"\|"failure"` | 匹配的治理后效记录（含治理策略 ID、产出影响摘要、后效评估） |
| **`search_mental_models`** | 在关系索引中检索因果链与认知结构 | `anchor_memory_id?: string`, `relation_type?: "causal"\|"competitive"\|"dependency"`, `max_hops: int` | 多跳关系图（节点=记忆 ID，边=关系类型 + 方向），最大深度 3 |
| **`done`** | 提交候选反思结论，交由收敛判据裁决是否终止 | `conclusion: string`, `confidence: float`, `updated_mental_models?: string[]`, `evidence_ids: string[]` | 候选结论入收敛评估缓冲：**首次调用记录基线并继续下一轮**；与上一次 `done` 结论余弦相似度 ≥ 0.90 时判定收敛、终止循环并将结论写入升华管道的 item→strategy 阶段 |

> **只读约束**：四类工具均为只读——Reflect loop 不修改记忆内容。反思结论（`done` 输出）作为升华管道的输入进入 strategy 阶段，由后续的 strategy→behavior 管线决定是否触发记忆权重的调整或 playbook 生成。此约束防止反思循环直接修改见证锚定或使用权重，确保反思是「观察-理解-建议」路径而非「观察-篡改」路径。

#### 循环控制

Reflect agentic loop 的循环控制遵循 tool-calling 模式——Agent 在每轮自主选择调用 recall/search_observations/search_mental_models/done 工具，最大 10 轮硬上限。收敛判据：连续两次 `done` 调用输出的结论余弦相似度 ≥ 0.90 时判定收敛。具体循环伪代码见 [implementation-map.md](implementation-map.md) 存储层 `src/storage/reflect.py` 实现。

**收敛判据**：Reflect loop 的终止条件不是固定轮数而是收敛度——`done` 是**结论提交动作而非终止动作**，终止权归收敛判据：

| `done` 调用序次 | 处置 |
|:---------------|:-----|
| 第 1 次 | 记录为收敛基线，**不终止**，循环继续（Agent 可继续调用只读工具后再次 `done`） |
| 第 n 次（n ≥ 2） | 与第 n-1 次结论计算余弦相似度：≥ 0.90 判定收敛并终止；< 0.90 更新基线后继续 |
| 达到 MAX_ROUNDS=10 仍未收敛 | 强制终止，取所有 `done` 调用中置信度最高的作为最终输出 |
| 全程未调用 `done`（达轮数上限） | 判定 `reflection_unconverged`，结论缺失，仅写入审计日志（见下表末行处置） |

因此**收敛终止的最小 `done` 调用次数为 2**——单次 `done` 不构成收敛，只建立基线。

**收敛度阈值分级**：

| 收敛度区间 | 结论质量标记 | 后续动作 |
|:----------|:-----------|:---------|
| [0.90, 1.00] | `reflection_converged` | 正常进入 strategy 阶段 |
| [0.70, 0.90) | `reflection_partial` | 进入 strategy 但标记「需后续验证」，降低自动执行的置信度阈值 |
| [0, 0.70) 或 强制终止 | `reflection_unconverged` | 结论仅写入审计日志，不进入升华管道的自动执行路径——须经宪法解释层审查 |

#### 与升华管道的集成

Reflect agentic loop 在升华管道的 **item→strategy** 阶段触发（非每次检索都运行）：

```text
raw → item → [Reflect agentic loop] → strategy → behavior
```

触发条件（AND 逻辑）：
1. item 阶段产出的记忆簇中，存在 ≥ 3 条不同来源的记忆（来源多样性条件）
2. 当前调度周期的注意力预算中，`reflection_budget` 配额 > 0
3. 自上次 Reflect loop 完成已超过冷却周期（默认 3 个调度周期，防止过度反思）

Reflect loop 的 `done` 输出直接作为 strategy 阶段的输入——strategy 阶段根据反思结论决定：(a) 更新使用权重的衰减参数；(b) 调整契约类型建议；(c) 生成 playbook candidate；(d) 触发潜伏势能重估。

#### 审计与可观测性

Reflect loop 的完整执行轨迹写入使用事件总线，标记 `reflect_agentic_loop`。**事件类型复用 `sublimation_tick`**（事件类型枚举见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10——Reflect 是升华管道 item→strategy 阶段的内部循环，不新增独立事件类型；全库事件类型枚举保持 10 类不变），payload 携带 `marker: "reflect_round"` 与下述字段：

```json
{
  "event_type": "sublimation_tick",
  "marker": "reflect_round",
  "trigger": "item→strategy",
  "rounds_executed": 5,
  "convergence_score": 0.93,
  "termination": "converged",
  "tools_called": {"recall": 2, "search_observations": 1, "search_mental_models": 1, "done": 2},
  "evidence_ids": ["mem_001", "mem_042", "mem_107"],
  "conclusion_summary": "...",
  "confidence": 0.85
}
```

审计庭可查询：(a) 收敛率（`reflection_converged` 占比）——收敛率持续下降时触发「反思漂移告警」；(b) 工具使用分布——`done` 调用次数 < 2 的循环占比（`done` 从未调用指示 Agent 在循环中「迷失」；仅调用 1 次指示 Agent 在建立基线后即耗尽轮数）；(c) 反思触发频率——频率异常升高时触发「过度反思告警」（可能指示升华管道产出质量下降）。

> **反思债务（Reflection Debt）风险声明**：Reflect agentic loop 的工具调用消耗 LLM token——每次 tool-choice 决策 + 工具执行（`recall` 触发检索、`search_mental_models` 触发图遍历）—的总 token 成本是线性 Reflect 的 3-10 倍。系统在注意力预算紧张（§9 Token 预算分解中 reserved 配额不足）时自动跳过 Reflect loop，降级为线性 Reflect。此风险已登记于成本护栏（§7）的监控范围内。

---

## §5 校准调度器

### 职责

- 接收外部校准信号（REST 端点 / CLI）
- 与见证锚定主副本比对（差异检验）
- 更新见证锚定或触发降级

### 核心循环（伪代码）

```text
CALIBRATION_LOOP:
    while True:
        signal = AWAIT_CALIBRATION_SIGNAL(timeout=DEFAULT_TIMEOUT)  # v0.1.0 默认 300s（见 KAIROS_CALIBRATION_TIMEOUT）

        if signal is None:  # 超时静默
            IDLE_COUNTER++
            if IDLE_COUNTER > CALIBRATION_SILENT_THRESHOLD:  # v0.1.0 默认 6 次超时（见 KAIROS_CALIBRATION_SILENT_COUNT）
                GENERATE_VIRTUAL_CALIBRATION()
            continue

        IDLE_COUNTER = 0

        # 差异检验
        diff = COMPUTE_DIFF(signal, witness_anchor)

        if diff < MERGE_THRESHOLD:  # v0.1.0 默认 0.15（cosine 距离），见 KAIROS_CALIBRATION_MERGE_THRESHOLD
            # 一致：合并
            MERGE_INTO_WITNESS(signal)
        elif diff < CONFLICT_THRESHOLD:  # v0.1.0 默认 0.35（cosine 距离），见 KAIROS_CALIBRATION_CONFLICT_THRESHOLD
            # 轻微偏差：加权融合
            WEIGHTED_MERGE(signal, CONFIDENCE(signal))
        else:
            # 冲突：进入冲突消解协议
            # RESOLVE_CONFLICT 协议：当外部校准信号与见证锚定主副本存在实质性冲突（cosine 距离 ≥ 0.35）时——
            # 1. 将冲突校准信号注入模拟隔离区做反事实推演
            # 2. 推演结果与主副本对比，确认冲突范围（局部属性冲突 vs 核心主张冲突）
            # 3. 局部属性冲突：标记冲突属性，保留主副本其余部分不变
            # 4. 核心主张冲突：悬挂主副本更新，等待下一次校准信号确认（连续两次冲突则触发宪法解释层仲裁）
            RESOLVE_CONFLICT(signal)

        # 审计记录
        AUDIT_LOG("calibration", signal_id=signal.id, diff=diff)
```

---

## §6 元认知检测器（概要）

| 检测器 | 监测指标 | 输出 |
|:-------|:---------|:-----|
| 情感流形监测器 | VAD 空间中记忆簇的激活预算占比 | 情感去强化触发信号 |
| 盲区覆盖率监测器 | 向量空间低密度区域占比 | 探索预算调整信号 |
| 叙事连贯性检测器 | 叙事自洽度时间序列趋势 | 身份漂移告警 |
| VAD 独立性测试器 | VAD 值是否可由其他轴完全预测 | 证伪信号 |
| 耦合计监测器 | 四轴之间的相关性趋势 | 轴正交假设证伪信号 |
| 偏置监测器 | 心境一致性/确认偏误积累 | 偏置告警 |

### 6.1 认知完整性轴三维检测器

认知完整性轴的三个度量维度（反例覆盖度 / 路径禁区标注密度 / 组合约束网络连通性）的认知定义见认知基础 §1.1。以下为其可操作代理定义（决策 D-15，方案 A）——原始表述含不可知分母（「总推理边界范围」）与无架构承载项（组合约束连通性），v0.1.0 采用**闭集代理**实现：

> **可操作代理定义（决策 D-15，方案 A）**：上述三维的原始表述含不可知分母（「总推理边界范围」）与无架构承载项（组合约束连通性），不可直接实现。v0.1.0 采用**闭集代理**——把分母从「客观全集」改为「系统已登记全集」，使三维成为可计算量：
>
> | 维度 | 代理定义（分子 / 分母均取自系统内已登记数据） | 数据源 |
> |:--|:--|:--|
> | 反例覆盖度 `coverage` | 已登记反例所覆盖的推理边界数 / **已登记推理边界总数**（非「客观总边界」） | 关系索引中 `boundary` 类关系条目 |
> | 路径禁区标注密度 `dead_end` | 标记为死胡同的路径数 / **已探索路径总数**（路径注册表中有访问记录的路径） | 路径注册表 + `is_structure` 标记 |
> | 组合约束网络连通性 `connectivity` | 约束关系图中实际连通边数 / 同节点数下的最大可能边数 `n(n-1)/2` | 关系索引中约束类关系边 |
>
> 三维合成沿用 [debt-collection.md](../governance/debt-collection.md) 债务 D-016 既定公式：`S = 0.4×coverage + 0.3×dead_end + 0.3×connectivity`，值域 [0,1]。

> **认知局限**：代理的闭集分母局限声明（`coverage` 度量的是「系统自认为」的边界覆盖率、`S` 仅用于趋势监测与结构保护判定、不得跨系统横向比较）保留在认知基础 §1.1，本检测器按该局限执行，此处不重复。

### 6.2 可及性轴代理

可及性轴的认知定义（度量「给定检索线索，找到这条信息的预期成本」）见认知基础 §1.1。以下为其可操作代理定义（决策 D-15，方案 A）：

> **可操作代理定义（决策 D-15，方案 A）**：本轴原定义的三项输入中，「前摄/倒摄抑制深度」与「提取诱发遗忘的抑制强度」在 v0.1.0 **无数据源**——D.9 已声明当前认知模型不将干扰预设为独立机制，故不存在对应的追踪字段。若坚持原定义，本轴不可取值。v0.1.0 改以三项**可观测量**合成代理值：
>
> `Accessibility = 1 − clamp₀₁(0.5·R̂ + 0.3·Ĉ + 0.2·D̂)`
>
> | 项 | 代理定义 | 数据源 |
> |:--|:--|:--|
> | `R̂` 检索命中位次 | 最近 N 次命中该记忆时的结果位次均值 ÷ 候选集规模；从未命中记为 1.0（最不可及） | 检索日志 |
> | `Ĉ` 路径竞争降权幅度 | 该记忆因同路径邻近竞争而被扣减的权重 ÷ 其原始权重 | 检索排序器 |
> | `D̂` 路径密度 | 该记忆所在路径前缀下的条目数 ÷ 密度告警阈值，上限截断为 1 | 路径密度监测（元认知层） |
>
> **代理与原定义的偏离（须显式承认）**：三项可观测量度量的是**干扰的结果**（检索时排不上、被降权、路径拥挤），而原定义的三项抑制深度度量的是**干扰的机制**。以结果代理机制的代价是：无法区分「因干扰不可达」与「因本身低价值不可达」——`R̂` 对二者给出相同的低分。因此本轴代理值在 v0.1.0 **不参与遗忘裁决**，仅用于① 触发路径密度告警、② 为「高使用价值 + 低可及性」的异常组合生成人工审查提示。机制级度量待 [debt-collection.md](../governance/debt-collection.md) **债务 D-313** 协议槽位落地后补全。此代理性质与 §1.1「3+2 代理人模型」的诚实声明一致。

### 6.3 CRI 代理实现

上下文腐烂指数（Context Rot Index, CRI）的认知定义（综合注意力分布熵、有效信息利用率、任务成功率三指标，值域 [0,1]，0=无腐烂、1=完全腐烂）见认知基础 §1.9。以下为其可操作代理定义（决策 D-15，方案 A）：

> **可操作代理定义（决策 D-15，方案 A）**：上述三指标的「综合」原表述无权重、无归一化、无采样窗口，不可实现。v0.1.0 给出如下可计算定义：
>
> `CRI = w₁·(1 − Ĥ) + w₂·(1 − U) + w₃·(1 − Ŝ)`
>
> | 项 | 归一化定义 | 默认权重 | 权重理由 |
> |:--|:--|:--|:--|
> | `Ĥ` 注意力分布熵 | 窗口内注意力权重分布的 Shannon 熵 ÷ `log(N)`（N=窗口内条目数），值域 [0,1]，熵越低越腐烂故取 `1−Ĥ` | `w₁ = 0.3` | 可直接从检索日志计算，客观但间接 |
> | `U` 有效信息利用率 | 窗口内被实际引用于输出的历史条目数 ÷ 窗口内注入上下文的历史条目总数 | `w₂ = 0.5` | **最直接的腐烂证据**，权重最高 |
> | `Ŝ` 任务成功率 | 由 `KAIROS_CRI_TASK_SUCCESS_PROXY` 指定的代理测得（见 [ops/configuration.md](../ops/configuration.md) §0.10） | `w₃ = 0.2` | 代理最弱（见 债务 D-024），权重压低以限制其失真影响 |
>
> **采样窗口**：滑动窗口取最近 `KAIROS_CRI_WINDOW_TURNS`（默认 20）轮交互，每调度周期重算一次（离线轻量任务，不入实时推理路径）。
>
> **冷启动与置信度**：窗口内交互轮次 < 5 时，CRI 强制取 `0` 且不触发任何降级——样本不足时的高 CRI 无统计意义，宁可漏报不可误降级。轮次介于 5 与窗口长度之间时正常计算但标记 `cri_confidence=low`，此时 L3（人工确认）不由 CRI 单独触发。
>
> **`Ŝ` 失效时的降权保护**：`KAIROS_CRI_TASK_SUCCESS_PROXY=explicit_feedback` 在多数普通对话中恒为 0（债务 D-024 已登记此风险），会使 CRI 虚高 `w₃=0.2`。故规定：窗口内**无任何成功/失败信号**时，`w₃` 置 0 并将 `w₁ w₂` 按比例重规范化为 `0.375 / 0.625`——即缺失项不参与，而非以 0 值污染。此规则使 CRI 在无反馈场景下仍然可用。

### 6.4 自激回路诊断指标

注意力-价值自激回路的机制与认知含义（已知无解局限、缓解措施、设计约束）见认知基础 §1.3。以下为诊断指标定义与默认动作：

**注意力-价值自激回路的诊断指标**：自激回路是否正在失控的判定不能仅依赖「理论上的风险承认」——需要可观测的指标。以下指标作为回路的诊断基准：(a) **使用价值分布熵的收敛速率**——若熵值在连续 N 个周期（默认 N=10）的下降速率持续加速（本周期的下降量 > 上一周期的下降量），指示回路正在自我强化：高使用价值的记忆越来越集中，低使用价值记忆的可见度加速降低；(b) **注意力分配的自相关性**——每周期的注意力分配结果与上一周期自身结果的皮尔逊相关系数连续超过 0.8 且无下降趋势，指示注意力倾向已失去对外部输入（当前任务上下文）的敏感性，转为由历史分配惯性驱动；(c) **被压制的候审队列清空率**——候审队列中的候选在 N 个周期内被重新推入候选集后再次被压制（二次压制）的比例持续超过 60%，指示回路对「非主流候选」存在系统性排斥。三项指标中任意一项连续超阈 3 个周期，触发「自激回路失控」告警至宪法解释层——解释层裁定是否需要暂停回路的正反馈环节（临时冻结使用权重更新，仅依赖见证价值和时间轴运行）。

**自激回路诊断指标的默认行为**：三项诊断指标（熵收敛速率、注意力自相关、候审二次压制率）中任意一项连续超阈 3 个周期时的默认动作——(a) 熵收敛超阈：临时冻结使用权重更新，暂停影子副本累积，持续 2 个审计周期后自动恢复（除非在此期间收到外部校准信号确认偏置确实存在）；(b) 注意力自相关超阈：强制注入身份记忆候选和低使用价值候选的配额翻倍（从正常制衡幅度的 1× 提升至 2×），持续至自相关降至阈值以下；(c) 候审二次压制率超阈：候审队列的存活周期数翻倍（从默认 N=10 翻倍至 N=20），给被压制候选更多机会被重新激活。默认动作不等待宪法解释层裁定（解释层介入为非必要动作，仅在默认动作无效时触发升级流程）。

---

## §7 WM调度预处理器（概要）

架构详见 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4（WM调度预处理器）。核心循环：

### 层级蒸馏管道

五层时间记忆树的蒸馏循环：

```text
LAYER_DISTILL(session_id):
    # L0: 写入原始轮次
    journal_entries ← (session_id, role, content, source, platform)

    # L1: 会话摘要（session 结束时触发）
    rows ← SELECT * FROM journal_entries WHERE session_id = $1
    summary ← LLM("将以下对话提炼为会话摘要", rows)  # 或启发式摘要
    key_decisions ← LLM("提取关键决策", rows)
    entities ← extract_entities(rows)  # 实体提取
    INSERT INTO session_summaries (session_id, summary, key_decisions, entities)

    # L2: 日报告（日终触发）
    sessions ← SELECT * FROM session_summaries WHERE date = today
    daily_summary ← LLM("聚合以下会话摘要为日报告", sessions)
    INSERT INTO daily_reports (report_date, summary, insights, session_count)

    # L3: 周知识包（周终触发）
    dailies ← SELECT * FROM daily_reports WHERE week = current_week
    patterns ← LLM("分析以下日报告的重复模式", dailies)
    INSERT INTO weekly_packs (week_start, patterns, trends, key_decisions)

    # L4: 画像更新（持续触发，增量）
    profile ← SELECT * FROM user_profiles WHERE user_id = $1
    new_prefs ← extract_preferences(sessions, dailies)
    profile.preferences ← merge(profile.preferences, new_prefs)
    UPDATE user_profiles SET preferences = $1, version = version + 1
```

蒸馏置信度低于 KAIROS_CAPTURE_CONFIDENCE_FLOOR（默认 0.6）的产物标记为待审，
不自动进入上层。关系检测在 L1 阶段执行。

> **时间粒度层级蒸馏形态对照（实证参考基线；债务 D-336）**：本管道与实战型开源记忆系统（外部实证参考：时间粒度层级蒸馏）的 L1 碎片→L2 会话→L3 每日→L4 每周→L5 画像五级蒸馏形态同构（蒸馏算子 Φᵢ:(Cᵢ,Hᵢ,Iᵢ)→{m⁽ⁱ⁾}，10 分钟/日/周/月节奏逐级压缩，见认知基础 §1.1 时间粒度层级实证对照声明）。对照价值：该蒸馏的节奏参数（10 分钟/日/周/月）与触发时点（日终/周终/月末）可作为本管道调度参数的参考基线，不改变 v0.1.0 既有口径。

```text
REASONING_LOOP(context):
    # 1. 向预测器查询预激活集
    pre_activated = PREDICTOR.QUERY(context)

    # 2. 候选集上下文裁剪
    candidates = CORTEX.FILTER(pre_activated, context)

    # 3. 推理输出行动决策
    action = CORTEX.REASON(candidates, context)

    # 4. 执行后更新使用事件
    EVENT_BUS.EMIT("use_event", candidates)

    return action
```

---

## §8 事件总线

### 事件格式

```json
{
  "event_id": "uuid",
  "event_type": "calibration_signal | degradation_switch | use_event | intention_activate | intention_resolve | affective_boost | exploration_budget | latent_trigger | attention_allocation | sublimation_tick",
  "source": "storage_layer | strategy_layer | wm_layer | metacognition_layer | sovereignty_plane",
  "target": "broadcast | specific_layer | specific_component",
  "trace_id": "uuid",
  "priority": 5,
  "payload": {},
  "timestamp": 1700000000000000000
}
// 注：TTL 由 event_type 按架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 事件类型枚举表确定，不在事件中携带
```

### 事件类型表

> 事件定义以 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 为唯一权威来源。本文仅引用，不新增事件类型。

| event_type | 发送者 | 接收者 | 说明 |
|:----------|:-------|:-------|:-----|
| `use_event` | WM | 策略+存储+元认知 | 使用事件提交 |
| `calibration_signal` | 宪法主权面 | 全层广播 | 外部校准信号注入 |
| `degradation_switch` | 宪法主权面 | 元认知+策略 | 降级模式切换 |
| `intention_activate` | 策略层 | WM | 前瞻意图激活 |
| `intention_resolve` | WM | 策略→存储 | 前瞻意图完成/取消 |
| `affective_boost` | 策略层 | WM | 情感基线提升注入 |
| `exploration_budget` | 元认知层 | 策略层 | 探索预算分配 |
| `latent_trigger` | 元认知层 | 存储层 | 潜伏势能重估触发 |
| `attention_allocation` | 注意力调度器 | 元认知层 | 注意力分配日志 |
| `sublimation_tick` | 存储层 | 自身 | 升华管道轮次推进 |

---
## §9 检索引擎

> **补充章节**：架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a 定义了三信号混合检索的公式与权重，本节点明其**管线执行顺序、状态机与 StorageBackend 接口**——此前检索算法细节仅存在于架构文档，无施工图纸。

### 职责边界

- 执行 §7.3a 三信号混合检索管线（路径过滤 → 时间过滤 → 三信号融合 → GSPO → MMR）
- 提供时间感知检索的 `as_of` 查询能力（双时态，认知基础 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1 双时态声明）
- 与 WM 管理器（§1 RETRIEVING 状态）协作，输出融合后的候选集

### 检索管线状态机

```text
解析 → 路径过滤 → 时间过滤 → 三信号融合 → GSPO 去重 → MMR 多样性 → 输出
 │        │            │            │             │            │
 │        │            │            └─ 语义 + BM25 + 实体       │
 │        │            │               权重 α_s=0.50/α_b=0.35/α_e=0.15  │
 │        │            └─ as_of / 事件时间窗口 / 纪元边界（可选约束）        │
 │        └─ kairos:// 路径前缀圈定候选域（硬过滤边界，RC-06）                 │
 └─ 解析查询意图（含按会话上下文构造的检索意图，策略层预测器输入）
```

### StorageBackend `as_of` 接口

```python
def as_of(ts: datetime) -> list[MemoryRecord]:
    """返回事件时间 ts 之前发生（occurred_at ≤ ts）且当时已写入（created_at ≤ ts）的记忆。
    被 superseded 的记忆按事务时间视角仍可查询（版本链保留旧版本）。
    双时态语义见架构 §5.2 半开区间时间语义。
    检索口径与常规查询一致（见 [data-model.md](data-model.md) §1 检索默认过滤）：
      (a) 软删除过滤——追加 is_deleted = FALSE，与 [data-model.md](data-model.md) 全库检索默认口径一致；
      (b) 版本选择——按版本链取 ts 时刻的生效版本（created_at ≤ ts 的最新版本），
          而非默认的 is_latest=TRUE（is_latest 为当前时刻视角，双时态查询须以 ts 为视角）。"""
    return self._query(
        "WHERE occurred_at IS NOT NULL AND occurred_at <= :ts AND created_at <= :ts "
        "AND is_deleted = FALSE "
        "AND version = (SELECT MAX(v.version) FROM memories v "
        "                 WHERE v.root_memory_id = memories.root_memory_id "
        "                   AND v.created_at <= :ts)",
        {"ts": ts},
    )
```

### 时间过滤约束（可选）

```python
def apply_time_filter(candidates: list[MemoryRecord], query: TimeConstraint) -> list[MemoryRecord]:
    """时间过滤约束阶段——候选域裁剪，非排序信号。
    未提供时间条件时返回原候选集（退化兼容，检索行为与无时间过滤时一致）。"""
    if query is None:
        return candidates
    return [
        c for c in candidates
        if c.occurred_at is not None
        and c.occurred_at >= query.window_start
        and (query.window_end is None or c.occurred_at <= query.window_end)
    ]
```

### 9.1 GSPO 聚类去重（三信号排序后几何均值压缩阶段）

GSPO（Geometric SPherical clustering of cO-occurring memories）是三信号混合检索完成后的聚类去重阶段——对排序结果中同源、同会话、高相似度的记忆进行几何均值压缩，以抑制检索结果中的信息冗余，确保返回给调用方的候选集在保持覆盖度的前提下最小化重复。

**聚类判定条件**

两条记忆 m1、m2 被归入同一 GSPO 聚类当且仅当同时满足：

1. **同源会话**：m1 和 m2 的 `session_id`（从 `encoding_context.session_id` 提取）相同
2. **高语义相似**：余弦相似度 `sim(embedding(m1), embedding(m2)) >` 配置阈值
3. **同域**：m1 和 m2 的 `domain` 字段相同（或均为 `general` 视为同域）

满足上述三条件的记忆对形成一张无向相似图，通过连通分量分析（Union-Find 或 BFS）将图划分为若干聚类簇。

**几何均值压缩**

对每个聚类簇 C，计算簇内各记忆的重要性值（importance，定义为当前排序阶段该记忆的归一化总分 `score_total ∈ [0,1]`），以几何均值作为聚类代表值：

$$\text{cluster\_importance}(C) = \exp\left(\frac{1}{|C|} \sum_{m \in C} \ln(\text{importance}(m))\right)$$

使用几何均值（而非算术均值）的理由：几何均值对低分记忆敏感——一个聚类中若混入低重要性的记忆（可能是冗余片段），几何均值会将其拉低；若所有记忆均为高分，几何均值接近算术均值。这使聚类代表值更诚实地反映簇内最低质量。

**激活条件：组内变异系数**

GSPO 压缩仅在聚类簇内存在足够差异时激活——计算簇内重要性值的变异系数（Coefficient of Variation）：

$$\text{CV}(C) = \frac{\sigma_C}{\mu_C} \quad \text{其中 } \mu_C \text{ 为算术均值，} \sigma_C \text{ 为标准差}$$

当 `CV(C) >` 配置阈值时，GSPO 压缩激活，以 `cluster_importance(C)` 替代簇内所有记忆的独立分数。CV ≤ 阈值时簇内记忆保持独立分数不变（簇内质量均匀，无冗余压缩必要）。

**候选集缩减语义（防「重打分不缩减」误解）**：GSPO 压缩**同时缩减候选集规模**——簇内仅保留重要性最高的成员作为「簇代表」进入下游（Cross-encoder / MMR），其余成员由检索管线剔除（标记 `gspo_collapsed` 写入审计事件，可按 `?clearance=debug` 回溯复核，不代表删除）。因此：(a) 「替代簇内所有记忆的独立分数」指代表成员的排序分以 `cluster_importance` 计，而非对每个成员分别打分；(b) 下游 Cross-encoder 的输入规模 = 簇数 + 未成簇记忆数，小于原始候选数，达成「降低 Cross-encoder 计算开销」的目标。

**域均衡（Domain Diversification）**

GSPO 压缩完成后，对压缩后的候选集执行 `_diversify_top_k()` 域均衡处理——确保最终返回的 top-K 结果中每个 domain 至少有一个代表：

1. 将候选记忆按 domain 分组
2. 从每个 domain 组中取分数最高的记忆作为「域代表」，合计得到 D 个代表
3. 剩余 `K - D` 个槽位从全局排序中取最高分（不区分 domain）填充
4. 若 `D > K`（域数超过返回槽位数），按 domain 出现频次降序取前 K 个域

域均衡的参数（开关、每域最小代表数等）见 [ops/configuration.md](../ops/configuration.md) §6.2。

**执行位置**：GSPO 聚类去重位于 5D 混合排序（历史沿用名，见架构 §7.3a 术语口径）输出端、Cross-encoder 重排序输入端——即先聚类去重缩减候选集规模，再对缩减后的候选集执行 Cross-encoder 精排（如启用），以降低 Cross-encoder 的计算开销。

> **配置参数**：GSPO 聚类去重的阈值、变异系数和域均衡参数见 [ops/configuration.md](../ops/configuration.md) §6.2。

### 9.2 MMR 去重阶段（最终多样性保障）

MMR（Maximal Marginal Relevance）去重是检索管线的最终阶段——在所有排序、增强和聚类压缩完成后，对最终候选集执行贪心多样性选择，确保返回结果的语义多样性。

**MMR 公式**

给定查询 q、已选择记忆集合 S、候选记忆 d，MMR 得分定义为：

$$\text{mmr}(d) = \lambda \cdot \text{sim}(q, d) - (1 - \lambda) \cdot \max_{j \in S} \text{sim}(d, j)$$

其中：
- `sim(q, d)`：查询 q 与候选记忆 d 的语义相似度（余弦相似度，复用三信号融合阶段的语义得分）
- `max_{j ∈ S} sim(d, j)`：候选记忆 d 与已选择集合 S 中任一记忆的最大相似度——衡量 d 的冗余度
- `λ ∈ [0,1]`：查询相关性（第一项）与多样性（第二项）的权衡系数。默认 `λ = 0.5`，意味着相关性与多样性等权重

**贪心选择算法**

1. 初始化空选择集 S = ∅
2. 从候选池 D 中选出当前 MMR 得分最高的记忆：`d* = argmax_{d ∈ D} mmr(d; S)`
3. 将 d* 从 D 移入 S
4. 重复步骤 2-3 直到 |S| = K（目标返回数）或 D 为空
5. S 作为最终输出，保持原 MMR 选择顺序（非原始排序顺序）

**与 GSPO 的分工**

| 维度 | GSPO 聚类去重 | MMR 去重 |
|:-----|:------------|:--------|
| **目标** | 消除同源冗余（同一会话的重复片段） | 消除语义冗余（不同来源但语义高度重叠的记忆） |
| **作用对象** | 同会话+同域+高相似记忆 | 跨会话/跨域但语义重叠的记忆 |
| **机制** | 聚类→几何均值压缩（簇内聚合） | 贪心 MMR 选择（跨簇多样性） |
| **执行阶段** | 5D 排序（历史沿用名，见架构 §7.3a 术语口径）后 → Cross-encoder 前 | 全管线最后（Cross-encoder 后，如启用） |
| **输出** | 每个聚类一个代表值，减少 Cross-encoder 输入规模 | 最终 top-K 多样性结果集 |

两个阶段互补：GSPO 解决「同一会话说了三遍同一件事」的冗余，MMR 解决「三个不同会话讨论了同一主题的相似结论」的冗余。两者串联执行，不互相替代。

**λ 自适应策略（v1.1 规划）**：v0.1.0 使用固定 λ=0.5；v1.1 规划根据查询类型动态调整 λ——事实型查询（"什么是 X"）提升 λ 至 0.7（更偏相关性），探索型查询（"还有哪些相关"）降低 λ 至 0.3（更偏多样性）。v1.1 的查询类型分类器由编译器子模块（§7）的意图理解字段输出。

> **配置参数**：MMR 去重的 λ 参数、开关和目标返回数见 [ops/configuration.md](../ops/configuration.md) §6.3。

**检索增强管线总览**

三信号混合检索 →（v1.1+ RL 二次排序——同优先级内加权，见 [rl-weight-spec.md](rl-weight-spec.md)；v0.1.0 不启用，5D 混合排序框架已废弃，见 [ops/configuration.md](../ops/configuration.md) §8.3） → GSPO 聚类去重（同源冗余压缩） → Cross-encoder 精排（可选） → MMR 去重（语义多样性保障） → 返回最终结果。图谱距离可选信号（如启用）在三信号融合后加入总分计算。

### 9.3 实体提取（spaCy 轻量路径）

为降低 LLM 实体提取的成本和延迟，Kairos v0.1.0 引入基于 spaCy 的轻量级实体提取管线——在 LLM 实体提取（Deep 模式维护任务）之前执行规则化预提取，减少不必要的 LLM 调用。

**设计原则**：spaCy 管线是 LLM 实体提取的**前置过滤器**而非替代品——识别高置信度的结构化实体（人名、组织、日期、数字等），将剩余文本中不确定的实体候选留给 LLM 处理。

**四级规则引擎**：

| 规则层 | 规则 | 匹配对象 | 示例 |
|:------|:-----|:--------|:-----|
| **L1: spaCy 内置 NER** | spaCy 预训练模型（`zh_core_web_sm` / `en_core_web_sm`） | PERSON, ORG, GPE, DATE, MONEY, PERCENT, PRODUCT, LOC, FAC | "张三"→PERSON, "2024-07-27"→DATE |
| **L2: 正则模式匹配** | 基于 `spaCy Matcher` 的领域规则库 | 邮箱、URL、版本号、IP 地址、手机号、身份证号、项目代号（`PROJ-\\d{4}`）、Git SHA | "v0.1.0"→VERSION, "commit a1b2c3d"→GIT_SHA |
| **L3: 字典匹配** | `spaCy PhraseMatcher` 预加载领域词典 | 技术栈名称、内部项目名、行业术语、配置键名 | "PostgreSQL"→TECH_STACK, "kairos://"→KAIROS_PATH |
| **L4: EntityRuler 管道** | 用户自定义 `patterns.jsonl` 文件 | 组织特定实体模式（客户名、产品名、内部缩写） | 通过配置指定路径 |

> **存储映射**：L1~L4 输出与 LLM 提取共享同一实体表，`entities.type` 存储层统一为四值枚举（project/people/concept/tool，权威口径见 [data-model.md](data-model.md) §8.2）；各类别映射规则见 §9.4「存储枚举映射」注记。

**150+ 过滤词表（Stop-Entity List）**：

L1 提取结果经过滤词表二次筛选——移除高频率但低信息价值的泛化实体（如 "今天"、"明天"、"这里"、"那个"、"stuff"、"thing"、"someone" 等）。过滤词表分中英双语维护：

- **中文过滤词**（~70 条）："这个"、"那个"、"大家"、"现在"、"之前"、"之后"、"一次"、"一种"、"一般"、"以上"、"以下"、"其中"、"其他"...
- **英文过滤词**（~80 条）："stuff", "thing", "things", "someone", "anyone", "everyone", "today", "tomorrow", "yesterday", "now", "later", "here", "there", "way", "lot", "kind", "sort"...

过滤词表通过配置 JSON 文件加载，支持运行时热更新。配置路径见 [ops/configuration.md](../ops/configuration.md) §6.4。

**执行位置与成本**：

- spaCy 管线在 L1 提取阶段（背景/新消息分段提取）中执行——位于四层递进式防御之后、LLM 提取之前
- 延迟目标：< 50ms（P95），不增加 L1 提取的总延迟预算
- 提取的实体直接写入实体知识图谱，与 LLM 提取的实体共享同一实体表和 memory_entities 关联表
- 实体来源标记为 `provenance: "spacy"`（区别于 LLM 提取的 `provenance: "llm"`），供检索时的实体加成（信号三）按来源类型加权

**与 LLM 实体提取的协作**：

- spaCy 高置信度实体（L1+L3+L4 命中且不在过滤词表中）→ 直接写入，不触发 LLM 调用
- spaCy 不确定实体（仅 L2 正则命中、或 L1 置信度 < 0.7）→ 标记为 `entity_pending_review`，在 Deep 模式维护任务中由 LLM 统一审核
- 用户可配置仅 spaCy 模式——启用后完全跳过 LLM 实体提取，仅依赖 spaCy 管线（适用于预算敏感场景）。配置参数见 [ops/configuration.md](../ops/configuration.md) §6.4。

> **配置参数**：spaCy 实体提取的模型、阈值和过滤词表路径见 [ops/configuration.md](../ops/configuration.md) §6.4。

### 9.4 实体提取（LLM+关键字双策略）

Kairos v0.1.0 的实体抽取采用**主-备双策略**架构——以 LLM 结构化 JSON 提取为主路径，以关键字/规则匹配为降级路径，确保在任何条件下实体提取功能均可用。

**设计原则**：LLM 实体提取是主策略（精度高、支持复杂语义），关键字降级是安全网（零 token 成本、始终可用）。两者共享同一实体知识图谱写入接口，上游调用方不感知当前使用的策略。

**双策略架构**：

```text
实体提取请求
    │
    ├─ 策略一：LLM 优先 JSON 提取（主路径）
    │     ┌─────────────────────────────┐
    │     │ Prompt: 严格 JSON Schema   │
    │     │ 输出: {entities: [{name,   │
    │     │   type, confidence,        │
    │     │   attributes}]}            │
    │     └─────────────────────────────┘
    │     成功 → 写入实体知识图谱
    │     失败/超时/预算不足 → 降级至策略二
    │
    └─ 策略二：关键字降级提取（安全网）
          基于前缀词典 + 正则模式 + spaCy 管线
          零 LLM token 消耗，始终可用
```

**策略一：LLM 优先 JSON 提取**

LLM 实体提取是 Kairos 实体知识图谱的核心数据源——每次 Deep 模式维护任务执行时，对新增记忆批量调用 LLM，以严格 JSON Schema 约束输出结构化实体：

```json
{
  "entities": [
    {
      "name": "PostgreSQL",
      "type": "TECH_STACK",
      "confidence": 0.95,
      "attributes": {
        "version": "16",
        "category": "database"
      }
    },
    {
      "name": "张三",
      "type": "PERSON",
      "confidence": 0.87,
      "attributes": {
        "role": "后端工程师",
        "team": "基础架构组"
      }
    }
  ]
}
```

**JSON Schema 约束**：
- `name`（必填）：实体名称，去重键
- `type`（必填）：实体类型，枚举值 `PERSON / ORG / GPE / DATE / TECH_STACK / CONCEPT / PROJECT / TOOL / EVENT / PRODUCT`
- `confidence`（必填）：浮点数 0-1，LLM 自评置信度
- `attributes`（可选）：键值对形式的实体属性（如版本号、角色、分类）

> **存储枚举映射**：`type` 为外部提取输出（LLM/spaCy）的 10 类枚举；持久化至 `entities.type` 时映射为存储层四值枚举（[data-model.md](data-model.md) §8.2 entities 表，存储层权威口径）：PERSON/ORG/GPE → `people`；PROJECT/TOOL/TECH_STACK → `project`；CONCEPT/EVENT/PRODUCT → `concept`；DATE → 时间字段（如 `occurred_at` 事件时间，不落 entities.type）。其余类（如 spaCy L1 的 MONEY/PERCENT/LOC/FAC、L2/L3 规则类 VERSION/GIT_SHA 等）归 `concept`——四值闭合。

**写入策略**（阈值均取**开区间**判定，互斥无重叠；配置参数见 [ops/configuration.md](../ops/configuration.md) §6.6）：
- LLM 置信度 ≥ `KAIROS_ENTITY_LLM_CONFIDENCE_THRESHOLD`（默认 0.8）→ 直接写入实体表，source=`llm`
- LLM 置信度 ∈ [`KAIROS_ENTITY_LLM_DISCARD_THRESHOLD`, `KAIROS_ENTITY_LLM_CONFIDENCE_THRESHOLD`)（默认 [0.5, 0.8)）→ 写入但标记 `entity_pending_review`，供后续人工或高置信度校准信号确认
- LLM 置信度 < `KAIROS_ENTITY_LLM_DISCARD_THRESHOLD`（默认 0.5）→ 丢弃该实体（不写入）

> **来源字段口径**：`source` 为实体提取来源标记（`llm` / `keyword_fallback` / 降级标记），持久化于 `entities.metadata` JSON 的 `source` 键——`entities` 表无独立 `source`/`provenance` 列（见 [schema-slice.sql](schema-slice.sql) §12）；与记忆级 `memories.provenance`（S-15 来源标识，记忆写入必填）为两个不同层级字段，勿混用。

**输出校验**：
- JSON 解析失败 → 重试一次（指数退避 1s），仍失败则降级至策略二
- JSON schema 不匹配 → 丢弃不匹配字段，保留合法字段。若合法字段为空则降级
- 同批次内实体名称重复 → 去重（保留 confidence 更高者）

**策略二：关键字降级提取**

当 LLM 提取不可用时（API 超时、token 预算耗尽、模型不可用），系统自动降级至关键字提取策略。降级策略由三层规则引擎组成，无需任何 LLM 调用：

| 规则层 | 机制 | 匹配对象 | 置信度 | 示例 |
|:------|:-----|:--------|:------|:-----|
| **L1: 前缀词典** | 预加载领域词典（技术栈、项目名、术语）→ Trie 树最长前缀匹配 | 已知实体名 | 0.90 | "PostgreSQL" → TECH_STACK |
| **L2: 正则模式** | 预编译正则库（版本号、邮箱、URL、IP、Git SHA）→ 单次扫描 | 结构化模式 | 0.85 | "v0.1.0" → VERSION |
| **L3: spaCy NER** | 复用 §9.3 四级规则引擎输出 | 通用实体类型 | 0.70 | "张三" → PERSON |

降级模式下的实体写入 source 标记为 `keyword_fallback`，与 LLM 提取的实体区分。降级事件写入系统事件总线标记 `entity_extraction_degraded`，附降级原因（超时/预算不足/模型不可用）。

**降级触发条件**：

| 条件 | 检测方式 | 动作 |
|:-----|:--------|:-----|
| LLM API 超时 | 请求超时 ≥ 配置超时值（见 [ops/configuration.md](../ops/configuration.md) §6.6） | 立即降级至策略二 |
| Token 预算不足 | 当前周期 `entity_extraction_budget` 配额耗尽 | 新请求直接走策略二，不尝试 LLM |
| 模型不可用 | 连续 3 次请求返回 5xx | 标记 LLM 通道为 `degraded`，冷却期内全部走策略二 |
| JSON 解析失败 | 重试后仍失败 | 降级，写入日志标记 `llm_output_parse_failed` |

**恢复机制**：LLM 通道在降级后持续探测（每 5 分钟一次健康检查请求）——健康检查通过且 token 预算恢复后，自动切回策略一。

**双策略执行位置**：
- 主路径（策略一）：后台维护引擎 Deep 模式，每日凌晨批量执行
- 降级路径（策略二）：当 Deep 模式检测到 LLM 不可用时自动切换；同时作为 L1 提取阶段的实时实体补充（与 spaCy §9.3 在同一管线位置执行）

**参数配置**：

> **配置参数**：实体抽取双策略的 LLM 开关、置信度阈值和降级冷却期见 [ops/configuration.md](../ops/configuration.md) §6.6。

**与 spaCy 实体提取（§9.3）的关系**：

spaCy 管线是 L1 实时提取阶段的低延迟前置过滤器（< 50ms），双策略实体提取是 Deep 模式下的高精度批量提取。两者互补：
- spaCy → 毫秒级在线预提取，服务于实时检索的实体加成信号
- 双策略 → 分钟/小时级离线批量提取，服务于实体知识图谱的长期建设

spaCy 提取的实体 source 标记为 `spacy`，双策略 LLM 提取标记为 `llm`，关键字降级提取标记为 `keyword_fallback`。三者写入同一实体表和 memory_entities 关联表，检索时按 source 类型加权（LLM > spaCy > keyword_fallback）。

---

## §10 注意力调度器

> 注意力调度器是全局横切资源管理器（架构 §9）——每轮对话前执行 token 预算计算与分配。本节为施工图纸级实现细节（Token 预算分解、任务感知评分协议、元记忆/提示词优化、断点续训与性能基准）。

### 10.1 Token 预算分解

每轮上下文注入前的 token 预算计算管线（在编译管线组装前执行）：

```python
# 预算分解逻辑（伪代码）
total_budget = CONTEXT_WINDOW_LIMIT        # 模型上下文窗口上限
fixed_overhead = SYSTEM_PROMPT + TOOL_DEFS  # 固定开销（系统提示词+工具定义）
remaining_budget = total_budget - fixed_overhead

# Step 1: 分解到记忆来源
# 口径：本分配表为「上下文注入侧」账本——决定各来源的结果最终占用多少注入 token，
#       合计恒为 1.00。与 §7.3d 的「检索执行侧」预算（Fast 0.15 + Deep 0.25 = 0.40，
#       计的是 embedding/LLM 调用开销）互不重叠，不可相加。
budget_allocation = {
    "blocks":     remaining_budget * 0.35,   # 上下文块（SOUL/skills/playbook）
    "semantic":   remaining_budget * 0.25,   # 语义检索结果
    "path":       remaining_budget * 0.15,   # 路径检索结果
    "entity":     remaining_budget * 0.10,   # 实体图谱检索结果
    "recent":     remaining_budget * 0.10,   # 最近对话历史
    "reserved":   remaining_budget * 0.05,   # 预留（动态调整）
}

# Step 2: 每个来源按 token_limit 裁剪
for block in memory_blocks:
    block.effective_limit = min(block.token_limit, budget_allocation["blocks"] / num_blocks)
# 语义检索候选按 similarity_score 降序排列，超出限额的截断

# Step 3: 注意力预算超限时执行降级策略
# 降级顺序（从低优先级开始）：
# 1. entity 检索配额 → 0（先关实体）
# 2. path 检索配额 → 减半
# 3. recent 历史 → 只保留最后 1 轮
# 4. semantic 检索 → 按 similarity 截断更严格
# blocks 和 reserved 始终保留（不可降级）
```

**设计原则**：
- 固定开销（system prompt + tool defs）必须在预算计算前已知，不由注意力调度器分配——这是代码实现的责任
- 各来源的预算比是建议性基线，可在运行时通过校准信号调整
- 降级策略的「不可降级」列表（blocks + reserved）确保核心上下文（身份/技能等）不受预算波动影响
- 降级后的实际分配与原始预算间的差距写回注意力分配日志，供元认知层评估预算充足度

### 10.2 任务感知评分

任务感知评分协议定义了 Kairos 记忆检索质量的评估框架——将检索评分从「通用相关性」扩展为「任务感知的时序容错评估」，解决传统评分指标（如 Precision@K、Recall@K、MRR）在时序记忆场景中的系统性误判问题。

**设计动机**：

传统检索评分假设「正确答案」是静态事实——检索到「正确答案」计 1 分，未检索到计 0 分。但在 Kairos 的记忆场景中，同一查询在不同时间点的「正确答案」可能不同：

- 查询「项目用的什么数据库？」——正确答案在 2024-01 是 PostgreSQL 14，在 2024-07 是 PostgreSQL 16
- 检索到 PostgreSQL 14（旧正确事实）比检索到 MySQL（完全错误）更有价值——但传统评分将两者等同为「错误」

任务感知评分协议通过时序容错和部分匹配，还原检索质量在「事实随时间演化」场景中的真实评估。

**评分维度**：

| 维度 | 定义 | 权重 | 说明 |
|:-----|:-----|:-----|:-----|
| **时序精度**（Temporal Precision） | 检索结果与查询时间点的匹配程度 | 40% | 核心维度——最新观测优先，但容忍 off-by-one |
| **事实置信度**（Factual Confidence） | 检索结果的事实可靠性（基于来源和校准历史） | 30% | 高置信度记忆即使时序略旧也优于低置信度新记忆 |
| **关系完整性**（Relation Completeness） | 检索结果是否附带完整的因果/引用/补充关系链 | 20% | 孤立事实的价值低于关系完备的事实网络 |
| **任务适配度**（Task Fit） | 检索结果与当前任务类型的语义匹配程度 | 10% | 通过 Profile Schema 的 `retrieval_hints` 映射 |

**Temporal Off-by-One 容忍规则**：

时序精度评分的核心创新是容忍「off-by-one」——检索到比查询时间点早一个 observation 周期内的记忆，不按完全错误扣分：

```text
时序精度得分 =
  if 检索结果的 observation_date 与查询预期时间点完全匹配: 1.0
  elif 检索结果的 observation_date 在查询预期时间点的 ±1 observation 窗口内: 0.8  (off-by-one 容忍)
  elif 检索结果的 observation_date 在 ±2 observation 窗口内: 0.5  (弱匹配)
  elif 检索结果与预期位于同一 observation 链（通过 linked_memory_ids 追溯）: 0.3  (同链但偏差较大)
  else: 0.0  (无关)
```

`observation 窗口` 的定义由任务域决定——编码协作场景为「天」粒度（off-by-one = 前后一天），研究辅助场景为「周」粒度（off-by-one = 前后一周）。默认粒度为「天」。

**综合评分公式**：

$$\text{task\_score} = 0.40 \cdot \text{temporal\_precision} + 0.30 \cdot \text{factual\_confidence} + 0.20 \cdot \text{relation\_completeness} + 0.10 \cdot \text{task\_fit}$$

其中 `factual_confidence` 直接取自记忆的 `calibration_confidence` 字段，`relation_completeness` 定义为该记忆的关系边数量 / 该主题域的平均关系边数量（归一化至 [0,1]），`task_fit` 为当前任务类型关键词与记忆所在路径前缀的余弦相似度。

**基准测试集成**：任务感知评分的基准评估流程（查询执行 → task_score 计算 → Task-Aware Precision@K/MRR 聚合 → 传统 Precision@K/MRR 对照组）见 [quality/benchmark-plan.md](../quality/benchmark-plan.md) 任务感知评分评估流程——本文仅承载评分协议定义。

**off-by-one 容忍的边界条件**：

- **不超过 1 个 observation 周期**：容忍 off-by-one 超时（如容忍 2 个周期）会使评分失去区分度
- **同链追溯作为安全网**：即使偏离超过 2 个周期，若能通过 `linked_memory_ids` 追溯到与期望答案在同一 observation 链上，仍给予 0.3 分——承认「旧但相关」的检索价值
- **不适用于非时序事实**：对于不随时间变化的事实（如「地球是圆的」），`temporal_precision` 恒为 1.0（无时间依赖性）

> **配置参数**：Benchmark 时序参数见 [quality/acceptance-criteria.md](../quality/acceptance-criteria.md) §三。

### 10.3 元记忆优化

为 LLM 生成**如何使用记忆**的指导原则——与 RL 优化器（「用什么权重排序」）互补但不重叠。

**机制**：在后台维护 Deep 模式中执行自反思循环，对检索→回答→反馈过程做轨迹分析，提炼可迁移的元记忆原则：

1. **轨迹分析**：对每次检索→回答→反馈的完整轨迹做结构化分析（Light 模式每 50 条反馈执行一次）
   - 分析内容：哪些记忆被使用/忽略？是否正确解读？哪些推理步骤正确/错误？
   - 输出：单条轨迹摘要（记忆利用分析 + 关键决策点 + 教训）
2. **跨轨迹对比**：聚合 ≥3 条同任务类别的轨迹，对比成功与失败案例，识别模式与反模式（Deep 模式日终执行）
3. **原则提炼**：基于模式分析对元记忆知识库执行 add/update/delete 三种符号操作
   - **add**：发现当前知识库未覆盖的新原则
   - **update**：可改进的现有原则
   - **delete**：错误或冗余的原则
4. **消费**：元记忆原则在每轮检索前注入上下文，作为「如何阅读和使用记忆」的策略指导

**约束**：
- 元记忆原则必须是关于**检索到记忆后怎么用**的策略，不是关于检索什么或存储什么
- 每条原则 ≤30 字，可操作、可泛化（不绑定特定任务类型）
- 知识库上限 50 条，超限时淘汰使用频率最低的原则
- 原则质量由宪法主权面的外部校准端口验证——连续 3 次校准确认无效的原则自动标记为候选淘汰

所有参数见 [ops/configuration.md](../ops/configuration.md) §8。配置参数包括批处理大小、原则数量上限、以及校准后淘汰阈值。

### 10.4 提示词优化

为系统提示词提供自动优化能力——与 §10.3 元记忆优化互补但不重叠：元记忆关注「怎么用记忆」，提示词优化关注「怎么组织提示词」。

**三种优化策略**：

| 策略 | 方法 | LLM 调用/轮 | 适用场景 |
|:-----|:-----|:-----------|:---------|
| Gradient（梯度） | 分离"评估"与"更新"→反思+生成 | 2 | 需要大幅度改进的复杂提示词 |
| Meta-Prompt（元提示） | 元提示分析轨迹→直接生成改进 | 1 | 中等幅度改进 |
| Prompt Memory（提示记忆） | 从成功模式中提取有效策略 | 1 | 快速小幅度优化 |

**执行流程**：
1. 收集最近 N 条对话轨迹（含用户反馈信号）
2. 根据配置策略选择优化策略
3. 对当前系统提示词执行配置轮数的优化循环
4. 输出优化后的提示词版本

**多提示词信用分配**（Multi-Prompt Credit Assignment）：
当系统使用多条提示词（SOUL.md + skill + playbook context）时，优化器先通过 Agent 推理分析判定哪条提示词导致性能下降，仅对问题提示词执行优化，其余保持原样。输出为 `{name: 原提示词名, optimized: 优化后文本, updated: true/false}[]`。

**安全约束**：
- 优化后的提示词须经宪法主权面外部校准端口验证方可上线
- 校准反馈连续 2 次 negative 自动回滚至上一版本（开关见 [ops/configuration.md](../ops/configuration.md) §8）
- 优化记录写入版本历史（`prompt_versions` 表）

所有参数见 [ops/configuration.md](../ops/configuration.md) §8。配置参数包括优化策略、反射轮次和自动回滚开关。

### 10.5 断点续训与重试（P3-05）

在 RL 权重优化器和升华管道等长时间运行的计算任务中，系统故障（进程崩溃、断电、OOM）或外部校准中断可能导致已部分完成的工作丢失。断点续训机制确保修复后可恢复进度，而非从零重启。

**设计原则**：

- **最小检查点粒度**：每个独立可验证的计算步骤完成后自动写入检查点，粒度控制在单步骤级别（如单条记忆的蒸馏完成、单次 RL 权重更新后的 snapshot）
- **检查点内容**：计算进度游标（已完成步骤序号/已处理记忆 ID 列表）、中间状态快照（当前权重向量、当前蒸馏阶段）、任务元数据（任务类型、启动时间、已消耗预算）
- **幂等续训**：从检查点恢复后，已完成的步骤不重复执行——通过对比检查点中的已完成步骤列表与待处理队列，跳过已完成项
- **检查点持久化**：写入 `training_checkpoints` 表（见 [data-model.md](data-model.md)），每个任务类型 + 任务 ID 保留最近 3 个检查点（循环覆盖旧检查点）

**重试策略**：

| 失败类型 | 重试策略 | 最大重试次数 | 退避算法 |
|:--------|:--------|:-----------|:--------|
| 瞬时错误（网络超时、API 限流） | 立即重试 | 3 | 指数退避：1s → 4s → 16s |
| 资源不足（OOM、磁盘满） | 延迟重试 | 2 | 固定延迟 60s，重试前检查资源可用性 |
| 数据损坏（检查点校验失败） | 回退至上一检查点 | 1（回退后续训） | 无退避——直接加载上一有效检查点 |
| 外部校准中断 | 等待校准恢复后续训 | 无上限（阻塞等待） | 每 30s 轮询校准端口状态 |

**恢复契约六属性（验收标准）**：持久化/防抖相关设计（断点续训检查点、防抖任务链 `debounced_tasks`、`journal_buffer` 回放）的恢复行为以六属性（前缀延续 / 效果恰好一次 / 分叉确定性 / 检查点有效性 / 消费一次 / 恢复确定性）为验收标准——任一属性不满足即视为恢复契约违约。验收判据表见 [quality/acceptance-criteria.md](../quality/acceptance-criteria.md) 恢复契约验收（自本文剥离）。配置参数：断点续训与重试参数见 [ops/configuration.md](../ops/configuration.md) §8.7。

### 10.6 用户画像性能基准（P3-06）

用户画像（`user_profiles` 表，见 [data-model.md](data-model.md) §7）是检索管线中的高频读取路径——每次检索请求须查询用户画像以获取 RL 权重配置、偏好、技能摘要等上下文信息。若画像读取延迟过高，将直接拖慢检索全链路。

**性能基准**：用户画像（`user_profiles` 表）是检索管线中的高频读取路径。P50/P99 读取/写入延迟和缓存命中率等性能基准见 [quality/acceptance-criteria.md](../quality/acceptance-criteria.md) §二。

**实现策略**：

- **应用层 LRU 缓存**：`user_profiles` 读取结果缓存于画像专用的应用层 LRU 缓存（容量独立于数据库访问层，不依赖语句缓存组件），TTL 30 秒。缓存键为 `user_profile:{user_id}:{trait_type}`。PreparedStatementCache 为 v1.1 组件（见 [debt-collection.md](../governance/debt-collection.md) 债务 D-418），其落地后两者可共享 LRU 空间但保持独立计数
- **写入穿透**：画像更新时同步写入数据库 + 主动失效缓存对应条目，确保检索始终拿到最新权重配置
- **预热策略**：系统启动时预加载高频用户画像至缓存（基于最近 7 天活跃用户 Top-N）
- **降级路径**：缓存未命中且数据库查询超时时，返回默认画像配置（所有 RL 权重使用默认值），记录降级事件至使用事件总线标记 `profile_read_degraded`

**监测指标**：元认知层定期采集延迟和缓存命中率，写入 `profile_perf_metrics` 日志。告警阈值见 [quality/acceptance-criteria.md](../quality/acceptance-criteria.md) §二。

---

## §11 编译与存储基础设施

> 编译与存储基础设施——编译管线渲染与缓存、Connectors 同步、Profile Schema、可移植备份格式与一致性检查。

### 11.1 编译管线渲染与缓存

**定位**：编译管线是上下文块系统的运行时执行引擎——将静态的上下文块描述转化为实际的、注入 LLM 的系统提示词，在每轮对话前执行。本节仅落位渲染策略表与缓存/参数细节，四阶段机制（采集→分类渲染→注入元数据→组装哈希缓存）保留在架构 §4.3。

**渲染策略表**：渲染器（Renderer）接收采集清单，按 `source` 类型分配独立的渲染策略：

```python
# 渲染策略表
RENDERING_STRATEGIES = {
    "system_file": {
        "mode": "tree",           # 目录树骨架 + 按需展开内容
        "max_depth": 3,           # 目录树最大深度
        "expand_threshold": 0.6,  # 相关性分数 > 阈值时展开完整内容
        "fallback": "summary",    # 超 token 预算时降级为摘要
    },
    "memory_retrieved": {
        "mode": "ranked_list",    # 按相关性降序排列
        "per_item_template": "[{timestamp}] [{path}] (score={score})\n{content_summary}",
        "max_items": 15,          # 最多注入条数
        "truncate_content": 500,  # 单条内容最大字符数
    },
    "runtime_context": {
        "mode": "inline",         # 键值对直排
        "template": "{key}: {value}",
        "omit_empty": True,
    },
    "playbook": {
        "mode": "structured",     # 结构化步骤模板
        "template": "## {title}\n触发: {trigger}\n前置: {preconditions}\n步骤:\n{steps}",
    },
}
```

每种渲染策略的输出为 `rendered_block`：`{name, content, token_count, rendering_mode}`。渲染器在渲染时实时追踪累计 token 消耗——当累计 token 超出预算上限时，后续块自动触发降级渲染（见渲染元数据中的 `render_overflow` 标记）。

**缓存策略（第四阶段：组装哈希缓存）**——两级哈希缓存策略：

**(a) 块级缓存**：每个 `rendered_block` 以其 `{source + version_hash + rendering_mode + block_name}` 的 SHA-256 作为缓存键。当下一轮编译管线的采集器检测到该源的 `content_hash` 未变化且渲染策略未变更时，直接从缓存取回已渲染的块，跳过第二阶段渲染。

**(b) 全局组装缓存**：对最终组装的完整提示词文本做 SHA-256 哈希。若连续两轮对话的提示词全局哈希一致（意味着所有源均未变化且渲染策略未变更），编译管线整体短路——直接复用上轮的完整组装结果，不执行采集→渲染→组装的全流程。

```text
缓存生命周期：
  块级缓存 TTL = 会话生命周期（session 结束时清除）
  全局组装缓存 TTL = 1 轮（仅在相邻轮次间复用，防止上下文漂移）
```

缓存的驱逐策略：(i) 文件源 `mtime`/`SHA-256` 变化的对应块立即失效；(ii) 任一渲染策略参数变更（如 token 预算重新分配）时全局组装缓存全部失效；(iii) 降级模式切换时全局缓存失效——不同降级模式下的提示词不应复用。

> **缓存命中率统计**：缓存器每轮记录 `cache_hit_ratio = cache_hits / total_blocks`，作为注意力调度器（§9）评估编译管线效率的输入指标。命中率持续低于预设阈值时，注意力调度器可决定降低编译管线频率或关闭全局组装缓存。

**编译管线的降级行为**：

| 故障场景 | 降级行为 |
|:--------|:--------|
| 文件源不可读（权限/IO 错误） | 跳过该源，标记 `block_missing`，其余块正常组装 |
| 渲染器 token 预算耗尽 | 后续块全部降级为 `rendering_mode=summary`（仅注入标题+一行摘要） |
| 缓存存储后端不可用 | 关闭缓存，每轮全量执行四阶段（功能降级不中断） |
| 全局管道超时（默认 500ms） | 中断当前组装，使用上一轮缓存的提示词（若无缓存则使用最小骨架提示词） |

### 11.2 Connectors 同步模式（Webhook 式自动同步）

Connectors 是 Kairos 与外部 SaaS 平台之间的**事件驱动同步桥接层**——通过 Webhook 回调或轮询机制，将 Gmail、Google Drive、Notion、GitHub 等外部平台的内容变更自动同步至 Kairos 记忆库，无需用户手动触发 `add_resource`。

**设计原则**：Connectors 遵循「外部事件 → Kairos 记忆」的单向同步模型——Kairos 不从记忆库反向写入外部平台（防止记忆系统成为数据污染源），仅作为知识消费端。

**支持的 Connector 类型**：

| Connector | 同步触发方式 | 摄取内容 | 默认契约 | 路径前缀 |
|:----------|:-----------|:--------|:--------|:--------|
| **Gmail** | Webhook（Google Pub/Sub）+ 轮询兜底（默认 300s） | 新邮件摘要（主题+发件人+正文前 2000 字符）、附件文本提取 | 按需 | `kairos://_user/{id}/gmail/` |
| **Google Drive** | Webhook（Drive API Changes）+ 轮询兜底（默认 600s） | 新增/修改文件文本提取（GDoc/GSheet/GSlides/PDF） | 环境 | `kairos://_project/{id}/drive/` |
| **Notion** | 轮询（Notion API search，默认 300s） | 新增/修改页面 Markdown 内容、数据库条目变更 | 环境 | `kairos://_project/{id}/notion/` |
| **GitHub** | Webhook（Repository events）+ 轮询兜底（默认 600s） | Issues/PRs 正文+评论、Release Notes、README/Wiki 变更、Commits diff 摘要 | 环境 | `kairos://_project/{id}/github/` |

> **注**：Notion 官方 Webhook 支持有限（v0.1.0 仅提供页面级 `updated_time` 查询），因此 v0.1.0 以轮询为主要触发方式。v1.1 目标迁移至 Notion Webhook GA 版本。

**Connector 注册接口**：通过 `POST /v1/connectors/register`（见 api-spec §14）注册外部平台 Connector，支持 OAuth2 认证、Webhook 验证、摄取过滤器（标签/文件夹/仓库过滤）和同步选项（全量同步、轮询间隔、实体提取开关、批次上限）。

**事件驱动同步流程**：

1. **Webhook 接收**：外部平台推送变更事件至 Kairos 的 `/webhooks/{connector_type}` 端点
2. **事件验证**：验证 Webhook 签名/来源（防止伪造）+ 去重（基于事件 ID 幂等检查）
3. **变更提取**：根据事件类型（创建/更新/删除）调用对应平台 API 提取变更内容 → 文本化
4. **摄取管道**：文本进入标准摄取验证门禁 → L0 日志 + 四层递进式防御 + L1 提取 → 写入统一 LTM
5. **审计记录**：每次同步写入使用事件总线，标记 `connector_sync`，附带 connector_type、变更条目数、成功/失败计数

**轮询兜底**：当 Webhook 通道不可用（如防火墙限制、平台不提供 Webhook）时，Connector 自动降级为定时轮询模式——按 `poll_interval_sec` 间隔调用平台 API 查询变更。轮询期间不丢失事件——Connector 维护 `last_sync_cursor`（如 Gmail `historyId`、GitHub `etag`），确保增量同步的连续性。

**失败处理**：
- 单次同步失败（API 超时/限流）→ 指数退避重试（1s → 2s → 4s → 8s），最多 3 次
- 认证失效（OAuth Token 过期）→ 标记 Connector 为 `auth_expired`，通知管理员
- 连续 N 次失败（默认 5 次）→ Connector 自动暂停，标记 `paused`，等待手动恢复
- 同步冲突（外部平台数据与已有记忆存在语义冲突）→ 触发差异检验，不自动覆盖

**安全约束**：
- 所有 Connector OAuth Token 使用 AES-256-GCM 加密存储（S-07 适用）
- Webhook 端点仅接受 HTTPS（TLS 1.2+），且验证 HMAC 签名
- Connector 同步的数据受 S-15 来源可鉴别约束——provenance 标记为 `connector:{connector_type}`

**配置参数**：
| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_CONNECTORS_ENABLED` | true | Connectors 总开关 |
| `KAIROS_CONNECTORS_WEBHOOK_PORT` | 8443 | Webhook 监听端口 |
| `KAIROS_CONNECTORS_MAX_RETRIES` | 3 | 单次同步最大重试次数 |
| `KAIROS_CONNECTORS_MAX_FAILURES` | 5 | 连续失败上限——超限自动暂停 |
| `KAIROS_CONNECTORS_POLL_MIN_INTERVAL` | 60 | 最小轮询间隔（秒）——防止 API 限流 |

### 11.3 可配置 Profile Schema（Configurable Profile Schema）

Kairos v0.1.0 支持用户自定义 Profile Schema——将用户画像（User Profile）的字段结构和主题分类从硬编码迁移至可配置的声明式模板，使不同场景（个人助手、开发协作、研究辅助）使用不同粒度和维度的用户建模框架。

**核心理念**：Profile Schema 定义「系统应关注用户哪些方面的信息」——而非「用户在这些方面的当前值」。当前值由升华管道 L4（Profile 蒸馏层）持续刷新。

**Schema 结构**：

```text
ProfileSchema {
  "schema_id": "developer-profile-v1",
  "name": "开发者画像模板",
  "description": "适用于编码协作场景的用户画像模板",
  "domains": [
    {
      "domain": "core",                       // 主题域
      "label": "核心身份",
      "fields": [
        { "name": "technical_role", "type": "enum", "values": ["frontend","backend","fullstack","devops","data","mobile"], "description": "技术角色" },
        { "name": "experience_level", "type": "enum", "values": ["junior","mid","senior","lead","principal"], "description": "经验级别" },
        { "name": "primary_language", "type": "string", "description": "主要编程语言" }
      ]
    },
    {
      "domain": "preferences",                // 子主题
      "label": "偏好与习惯",
      "fields": [
        { "name": "preferred_tech_stack", "type": "string_list", "description": "偏好技术栈" },
        { "name": "code_style", "type": "text", "description": "代码风格偏好（自然语言描述）" },
        { "name": "communication_style", "type": "enum", "values": ["verbose","concise","code-first","explain-first"], "description": "沟通风格" }
      ]
    },
    {
      "domain": "context",
      "label": "当前上下文",
      "fields": [
        { "name": "active_projects", "type": "string_list", "description": "活跃项目名称" },
        { "name": "current_focus", "type": "text", "description": "当前关注点（自然语言描述）" },
        { "name": "recent_achievements", "type": "text_list", "description": "最近成就" }
      ],
      "ttl_hours": 168                        // 该域字段的有效期（168h = 7天）
    }
  ],
  "retrieval_hints": {                        // 检索提示——指导系统何时注入此 Profile 的哪些域
    "on_coding_task": ["core", "preferences"],
    "on_code_review": ["core", "preferences"],
    "on_general_query": ["core"]
  }
}
```

**预设模板（v0.1.0 内置）**：

| 模板 ID | 适用场景 | 主题域 | 说明 |
|:--------|:--------|:------|:-----|
| `general-v1` | 通用个人助手 | core, preferences, knowledge | 最简模板——基础身份+偏好+已知事实 |
| `developer-v1` | 编码协作 | core, preferences, context, codebase_knowledge | 含技术栈、代码风格、活跃项目 |
| `researcher-v1` | 研究辅助 | core, expertise, current_research, methodology | 含专业领域、研究方法、当前课题 |
| `team-v1` | 团队协作 | core, role, team_context, meeting_notes | 含团队角色、协作偏好、会议记录 |
| `minimal-v1` | 零配置降级 | core | 仅 `technical_role` 和 `communication_style` 两个字段——零配置模式的默认模板 |

用户可通过 Profile Schema 管理 API（见 api-spec §15 PUT /v1/profile/schema）注册自定义 Schema 或覆盖预设模板的字段定义。Schema 版本化——修改后的 Schema 自动递增 `schema_id` 后缀（如 `developer-v2`），旧 Schema 保留供历史 Profile 数据回溯。

**字段提取与刷新**：

- Profile 字段值由升华管道 L4（Profile 蒸馏层）从 L3 周度报告中提取并持续刷新
- 每个字段维护 `last_updated` 时间戳和 `confidence`（0-1）置信度——长期未观察到的字段（超过 `ttl_hours`）置信度指数衰减
- 字段值冲突（如 L4 蒸馏得出的 `primary_language` 与历史值不同）——遵循 ADD-only 协议：追加新观察而非覆盖，通过 relation_type=supplement 链接历史值
- Profile 字段的 `confidence` 低于阈值（默认 0.3）时，标记为 `low_confidence`——检索时不作为硬过滤条件，仅作为弱信号参与排序调制

**检索集成**：

- Profile 在每轮对话开始时通过 Fast Context 路径注入 WM——仅注入 `retrieval_hints` 中与当前任务类型匹配的域
- Profile 字段作为检索的附加上下文——不参与主排序公式（三信号融合），但影响领域路由的路径前缀选择和实体加成的实体权重

**配置参数**：
| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_PROFILE_SCHEMA_ID` | `general-v1` | 当前激活的 Profile Schema |
| `KAIROS_PROFILE_CONFIDENCE_THRESHOLD` | 0.3 | 低置信度阈值 |
| `KAIROS_PROFILE_REFRESH_INTERVAL_HOURS` | 24 | Profile 字段刷新间隔 |
| `KAIROS_PROFILE_MAX_FIELDS` | 30 | 单个 Schema 最大字段数——防止过度膨胀 |

### 11.4 可移植备份格式（.kairos 协议）

Kairos v0.1.0 定义一套自包含的**可移植备份格式**——`.kairos` 协议包——用于记忆库的完整导出/导入、跨实例迁移和灾难恢复。`.kairos` 包是一个自描述的压缩归档，包含记忆数据、向量索引、关系图谱和元数据，不依赖原始数据库引擎即可完整还原。

**设计原则**：
- **自包含**：解包后的 `.kairos` 归档不需要原始数据库、外部向量服务或 LLM API 即可独立验证数据完整性
- **可移植**：跨操作系统、跨存储后端（SQLite ↔ PostgreSQL）无缝迁移
- **版本化**：协议版本号内嵌，导入时自动检测版本兼容性
- **可审计**：归档内含 SHA-256 清单文件，可独立验证数据未被篡改

**`.kairos` 包结构**：

```text
archive.kairos（ZIP 压缩包，无压缩或 deflate）
│
├── manifest.json           # 清单文件——版本、校验和、元数据
├── schema.sql              # DDL 建表语句（目标数据库方言）
├── data/                   # 数据文件目录
│   ├── memories.jsonl      # 主记忆表（NDJSON，每行一条记忆）
│   ├── memory_relations.jsonl   # 关系索引
│   ├── knowledge_evolution.jsonl # 知识演化追踪
│   ├── memory_versions.jsonl    # 版本快照
│   ├── entities.jsonl      # 实体知识图谱
│   ├── memory_entities.jsonl    # 实体-记忆关联（含时序字段）
│   ├── witness_anchor.jsonl     # 见证锚定主副本
│   ├── usage_weight.jsonl       # 使用权重影子副本
│   ├── journal_buffer.jsonl     # 写入暂存区
│   ├── memory_flags.jsonl       # Flag 标记
│   ├── memory_tags.jsonl        # 记忆标签
│   ├── conversation_messages.jsonl  # 对话历史
│   ├── session_summaries.jsonl      # L1 会话摘要
│   ├── daily_reports.jsonl          # L2 日报告
│   ├── weekly_packs.jsonl           # L3 周知识包
│   ├── user_profiles.jsonl          # L4 用户画像
│   └── config.jsonl             # 配置表
│
├── vectors/                # 向量数据目录
│   ├── embeddings.npy      # NumPy 格式的 embedding 矩阵（float32）
│   ├── embedding_index.jsonl   # embedding_id → memory_id 映射
│   └── index_config.json   # 向量索引配置（维度、距离度量、索引类型）
│
└── checksums.sha256        # 所有文件的 SHA-256 校验和
```

**`manifest.json` 结构**：

```json
{
  "kairos_version": "1.0.0",
  "protocol_version": 1,
  "created_at": "2026-07-27T10:00:00Z",
  "source": {
    "storage_backend": "postgresql",
    "hostname": "kairos-prod-01",
    "instance_id": "uuid"
  },
  "stats": {
    "total_memories": 15420,
    "total_entities": 3200,
    "total_relations": 8700,
    "embedding_dim": 1536,
    "total_size_bytes": 245000000
  },
  "options": {
    "include_vectors": true,
    "include_journal": false,
    "include_audit_log": false,
    "compression": "deflate",
    "encryption": null
  },
  "checksums": {
    "data/memories.jsonl": "sha256:abc123...",
    "vectors/embeddings.npy": "sha256:def456..."
  }
}
```

**导出选项**：

| 选项 | 默认值 | 说明 |
|:-----|:------|:-----|
| `include_vectors` | true | 是否导出向量数据（.npy + 映射表）。false 时仅导出文本数据，导入后需重新计算 embedding |
| `include_journal` | false | 是否导出 journal_buffer（原始对话暂存区）。默认不导出以减少包体积 |
| `include_audit_log` | false | 是否导出审计日志。默认不导出——审计日志体积大且通常为只读历史数据 |
| `compression` | `deflate` | 压缩算法：`none` / `deflate` / `zstd` |
| `encryption` | null | 加密方式：null（不加密）/ `aes256`（AES-256-GCM，需提供密钥） |

**导出 API**：通过 `POST /v1/admin/export`（见 api-spec §16）导出 .kairos 备份包，支持向量数据、压缩算法和加密选项。

**导入 API**：通过 `POST /v1/admin/import`（见 api-spec §16）导入 .kairos 备份包，支持三级冲突解决策略（fail/overwrite/skip）。

**三级冲突解决策略**：

导入时，若 `.kairos` 包中的记忆与目标数据库中已存在的记忆发生冲突（同 `path` + 同 `version` 或同 UUID），系统提供三级冲突解决策略：

| 策略 | 标识 | 行为 | 适用场景 |
|:-----|:-----|:-----|:---------|
| **fail**（遇冲突即中止） | `conflict_resolution=fail` | 检测到第一条冲突时立即中止导入，整个事务回滚，不写入任何数据。返回冲突详情列表供用户手动处理。 | 首次迁移、空库导入——不应有冲突 |
| **overwrite**（覆盖冲突条目） | `conflict_resolution=overwrite` | 以 `.kairos` 包中的版本覆盖目标数据库中冲突的记忆。覆盖前自动创建 version snapshot（写入 `memory_versions` 表），保留被覆盖版本的审计痕迹。覆盖操作写入审计日志标记 `import_overwrite`。 | 从备份恢复——备份数据优先于当前数据 |
| **skip**（跳过冲突条目） | `conflict_resolution=skip` | 跳过所有冲突的记忆及其关联数据（关系、实体关联、Flag），仅导入新记忆。被跳过的条目汇总在导入响应中。关联数据（如实体关联到被跳过记忆的关系边）也一并跳过，不产生孤儿引用。 | 增量合并——已有数据优先于导入数据 |

**冲突判定规则**：
- 同 UUID（`memories.id` 碰撞）→ 冲突
- 同路径 + 同版本（`UNIQUE(path, version)` 约束）→ 冲突
- 不同 UUID 但内容哈希相同（`content_hash` 碰撞）→ 不视为冲突（去重写入，仅更新 usage_weight）

**冲突详情响应格式**（`conflict_resolution=fail` 时返回）：

```json
{
  "conflicts": [
    {
      "type": "uuid_collision",
      "memory_id": "uuid-123",
      "existing_path": "kairos://_user/abc/core/mem_001",
      "incoming_path": "kairos://_user/abc/core/mem_001",
      "existing_created_at": "2026-07-20T10:00:00Z",
      "incoming_created_at": "2026-07-25T10:00:00Z"
    }
  ],
  "suggestion": "使用 conflict_resolution=overwrite 以导入版本覆盖，或 conflict_resolution=skip 跳过冲突条目"
}
```

**导入验证流程**：

导入操作分三个阶段，每阶段独立验证，失败时可精确回滚至阶段起点：

1. **阶段一：完整性校验**
   - 验证 `checksums.sha256` 中的所有文件哈希
   - 验证 `manifest.json` 的 JSON schema
   - 验证 `.kairos` 协议版本与当前 Kairos 版本兼容性
   - 失败 → 拒绝导入，不清除任何数据

2. **阶段二：数据验证**
   - 逐条验证 NDJSON 格式的合法性（每行可解析为合法 JSON）
   - 验证外键引用完整性（`memory_relations.source_id` 是否存在于 `memories.jsonl`）
   - 验证向量维度与 `manifest.stats.embedding_dim` 一致
   - 失败 → 拒绝导入，返回验证错误详情

3. **阶段三：写入提交**
   - 按依赖顺序写入（memories → relations → entities → ...）
   - 在单事务内执行（PostgreSQL）或批量写入（SQLite，关闭外键约束后逐表写入再恢复）
   - 冲突按 `conflict_resolution` 策略处理
   - 导入完成后触发一次性索引重建（REINDEX）

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_EXPORT_MAX_MEMORIES` | 100000 | 单次导出最大记忆数（超限分批导出） |
| `KAIROS_IMPORT_MAX_SIZE_BYTES` | 1073741824 | 导入包最大体积（1GB） |
| `KAIROS_IMPORT_TRANSACTION_TIMEOUT` | 600 | 导入事务超时（秒） |
| `KAIROS_EXPORT_TEMP_DIR` | `/tmp/kairos-export` | 导出临时目录 |

### 11.5 文件系统-向量索引一致性检查

Kairos 的存储层维护两套数据视图——**文件系统视图**（`memories` 表中的结构化记录）与**向量索引视图**（pgvector/sqlite-vec 中的 embedding 索引）——两者理论上是同一数据的两种索引，但在长期运行中可能因以下原因出现不一致：

- **异步写入中断**：记忆写入成功但 embedding 写入在事务提交前崩溃
- **向量索引碎片**：大量删除/更新后向量索引未及时重建（如 IVFFlat 索引的 dead tuples）
- **并行导入**：批量导入时外键约束临时关闭导致的孤儿向量
- **手动操作**：数据库直接操作绕过了应用层的双写事务

**一致性检查器（Consistency Checker）**是存储层的定期校验组件——不需要也不应该依赖 LLM，所有检查通过确定性 SQL 查询和数据指纹比对完成。

**检查维度**：

| 检查项 | 查询方式 | 不一致信号 | 严重级别 |
|:-------|:--------|:----------|:--------|
| **C1: 有记忆无向量** | `SELECT id FROM memories WHERE embedding IS NULL AND is_deleted = FALSE` | 记忆存在但缺少向量 | WARNING |
| **C2: 有向量无记忆** | 向量索引中存在的 ID 在 `memories` 表中无对应记录（孤儿向量） | 向量存在但源记忆已删除 | ERROR |
| **C3: 记忆-副本不一致** | `memories` 的 `id` ↔ `witness_anchor.memory_id` + `usage_weight.memory_id` 双向检查 | 记忆有主副本但无影子副本、影子副本指向不存在的记忆 | WARNING |
| **C4: 关系孤边** | `SELECT * FROM memory_relations WHERE source_id NOT IN (SELECT id FROM memories) OR target_id NOT IN (SELECT id FROM memories)` | 关系索引的源/目标记忆不存在 | ERROR |
| **C5: 实体孤边** | `SELECT * FROM memory_entities WHERE memory_id NOT IN (SELECT id FROM memories) OR entity_id NOT IN (SELECT id FROM entities)` | 实体-记忆关联指向不存在的实体或记忆 | WARNING |
| **C6: 向量维度不一致** | 检查所有 embedding 向量的实际维度是否与 `manifest.stats.embedding_dim` 一致 | 向量维度不匹配——可能混入了不同模型的 embedding | CRITICAL |
| **C7: 索引效率** | 检查 pgvector 索引的 `n_dead_tup` / `n_live_tup` 比值（PostgreSQL）或 sqlite-vec 的碎片率（SQLite） | 索引碎片率超过阈值（默认 > 0.3） | INFO |
| **C8: 内容哈希一致性** | `SELECT id, content_hash FROM memories` 与 `SHA-256(content)` 逐一比对 | 存储的 `content_hash` 与实际内容哈希不一致 | CRITICAL |

**执行模式**：

| 模式 | 触发方式 | 检查范围 | 延迟预算 |
|:-----|:--------|:--------|:--------|
| **Light（轻量）** | 后台维护引擎 Light 模式，每小时 | C1 + C2 + C4 + C7（仅统计计数，不逐条比对） | < 1s |
| **Deep（深度）** | 后台维护引擎 Deep 模式，每日凌晨 | C1-C8 全量检查——C1~C7 为确定性 SQL 全量查询（无抽样）；C8 内容哈希校验按 `KAIROS_CONSISTENCY_HASH_VERIFY_SAMPLE_RATE`（默认 0.05）抽检（全量哈希比对成本过高，参数见 [configuration.md](../ops/configuration.md) §11.5；抽检发现不一致后对该记忆全链复核） | < 60s（100K 记忆规模，含 5% 哈希抽检） |
| **On-demand（按需）** | 手动触发一致性检查端点（见 api-spec §16 POST /v1/admin/consistency-check） | 可指定检查项子集和路径范围 | 取决于数据量和检查项 |

**自动修复策略**：

检查发现不一致后，系统根据严重级别自动执行修复或触发人工介入：

| 检查项 | 严重级别 | 自动修复 | 修复方式 |
|:-------|:--------|:--------|:---------|
| C1（有记忆无向量） | WARNING | ✅ 是 | 将缺失向量的记忆加入 embedding 补算队列——后台异步调用 embedding 模型重新生成向量。补算完成前该记忆降级为仅路径检索（不参与语义检索） |
| C2（孤儿向量） | ERROR | ✅ 是 | 自动删除孤儿向量——该向量对应的记忆已被删除，保留向量无意义。删除操作写入审计日志 `consistency_orphan_vector_cleanup` |
| C3（副本不一致） | WARNING | ⚠️ 半自动 | 缺失的影子副本自动创建（初始 `activation_weight=0`）。缺失的主副本（见证锚定）无法自动恢复——标记为 `consistency_needs_manual_fix`，写入告警事件 |
| C4（关系孤边） | ERROR | ✅ 是 | 自动删除孤边——源或目标不存在的关系索引无意义。删除操作写入审计日志 |
| C5（实体孤边） | WARNING | ✅ 是 | 自动删除孤边。但在删除前检查孤边是否关联到 `valid_to IS NULL` 的时序关系——如果是（表示关系仍在生效中），标记为 `consistency_deferred`，延迟 24h 后再次检查（可能记忆正在写入中） |
| C6（向量维度不一致） | CRITICAL | ❌ 否 | 无法自动修复——维度不一致可能意味着混入了不同 embedding 模型产生的向量。系统触发 `consistency_vector_dimension_mismatch` 紧急告警，暂停该路径前缀下的语义检索直至人工介入 |
| C7（索引碎片率高） | INFO | ✅ 是 | 自动触发 REINDEX（PostgreSQL）或 VACUUM（SQLite-vec）。REINDEX 在低负载窗口执行（默认凌晨 2-4 点） |
| C8（内容哈希不一致） | CRITICAL | ❌ 否 | 无法自动修复——内容哈希不一致意味着 `content` 字段可能被篡改或损坏。标记该记忆为 `content_hash_mismatch`，暂停检索该记忆，触发安全告警至宪法解释层 |

**修复后的验证闭环**：

自动修复执行完成后，系统在同一调度周期内重新运行该检查项——验证修复是否成功：
- 修复成功 → 写入审计日志 `consistency_fix_applied`，记录修复方式、修复前后的不一致计数
- 修复失败（同检查项仍检测到不一致）→ 升级严重级别（WARNING→ERROR, ERROR→CRITICAL），标记为 `consistency_fix_failed`，触发人工介入告警

**一致性检查的元监控**：

元认知层的健康检测器接收一致性检查的输出指标：
- **不一致检出率**（`consistency_issues_detected / total_records`）：趋势上升 → 指示存储层可能正在缓慢漂移
- **自动修复成功率**（`consistency_fix_applied / consistency_issues_detected`）：持续下降 → 指示自动修复策略可能需要调整
- **C6/C8 检出频率**：任何 C6 或 C8 检出（即使成功修复）立即触发宪法解释层审查——这两类问题指向数据完整性风险

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_CONSISTENCY_LIGHT_ENABLED` | true | Light 模式开关 |
| `KAIROS_CONSISTENCY_DEEP_ENABLED` | true | Deep 模式开关 |
| `KAIROS_CONSISTENCY_AUTO_FIX_ENABLED` | true | 自动修复总开关（关闭后仅报告不修复） |
| `KAIROS_CONSISTENCY_INDEX_FRAG_THRESHOLD` | 0.3 | 索引碎片率告警阈值 |
| `KAIROS_CONSISTENCY_HASH_VERIFY_SAMPLE_RATE` | 0.05 | Deep 模式内容哈希校验的抽样率（0.05=抽检 5% 的记忆，全量比对成本过高） |
| `KAIROS_CONSISTENCY_MAX_FIX_PER_CYCLE` | 1000 | 单周期最大自动修复条目数（防止批量修复冲击正常检索） |

**与差异检验的关系**：

一致性检查与差异检验是两种互补的校验机制：
- **差异检验**——校验主副本（见证锚定）与影子副本（使用权重）之间的**语义一致性**（使用频率是否偏离了事实锚定）。关注的是记忆的「价值」一致性。
- **一致性检查**（本节）——校验文件系统视图与向量索引之间的**结构一致性**（每行记录对应的向量/索引是否完整且匹配）。关注的是存储层的「结构」完整性。

两者在后台维护引擎 Deep 模式中串行执行——先执行一致性检查（确保数据结构完整），再执行差异检验（在完整数据上检验语义一致性）。

---

## §12 探索治理

> 探索治理——冷启动种子探索预算与批量探索清理协议（源自认知基础 §2.1 附录 B.2 / 附录 E.4）。

### 12.1 冷启动种子探索预算

冷启动种子价值源的完整声明（种子价值源打破「价值源于使用」循环、三条偏置约束、主动消解路径）见认知基础 §2.1 附录 B.2。以下为其探索预算规则：

**冷启动种子平衡理念**：种子锚点生效阶段（前 K 个校准周期，K 默认值见配置文档），探索预算强制上浮至预设基线值 1.5 倍以上，调度器应主动采样与种子价值判断相悖的语义域。此强制上浮不经过常规探索预算分配逻辑（不受盲区覆盖率衰减的影响），确保系统在冷启动阶段不因种子偏置而错过与其价值判断相悖的关键认知域。K 窗口期满或累计探索采样量达预设阈值后，探索预算回归常规盲区驱动逻辑。

### 12.2 批量探索清理协议

> **批量探索违规清理协议**（补充，解决「探索 > 宪法」时序优先下批量探索产物污染问题）：探索产物的「时序优先」允许探索先于宪法审查发生，但当单批探索量超过预设阈值（默认值见配置文档）时，触发批量清理前置条件——（a）大批量探索（单批 ≥ 阈值）在产出时不做逐条审查，而是整体打包为 exploration_batch 标记簇；（b）宪法事后否决时，否决结果是一个整批回滚而非逐条裁决——同一批探索产出的所有记忆附带 batch_revert 标记，在下一个离线巩固周期批量清除；（c）回滚不影响探索前已存在的记忆——仅清除该批次探索产生的影子副本和见证副本，不触及探索前的见证锚定。此协议确保探索的时序自由不被批量污染所利用：宪法否决权可从「逐条审查」升级为「整批否决」，否决成本与探索规模无关。仅大批量（超阈值）触发整批回滚；小批量探索仍执行逐条审查——逐条审查粒度不因此协议改变。

---
## 吸收承接注记

> 本节承接外部项目理念吸收的工程细节，权威定义在认知基础与架构文档，本节为施工参考。

**噪音规则库参考清单（实证参考清单，债务 D-338，架构 §7.3 噪音规则库层的工程承接）**：

四类纯正则规则（零 LLM 成本，命中不计轮数、不升温）：

| 规则类 | 示例 |
|:-------|:-----|
| 单字/短确认 | 好/嗯/ok/可以/继续/收到/了解/对/是的/知道等 |
| 语气词 | 哈哈/呵呵/我去/牛逼等 |
| 元命令 | /compress、/status 等系统命令 |
| 分隔符与纯标点行 | `^[-=*]{3,}$`、`^[。.，,]{1,10}$` |

重要性加分表（内容类型 → 参考分，摄入侧附加）：未完成任务 5 / 纠正 4 / 决策 3 / 情绪 3 / 路径变更 2 / 工具结果 1 / 寒喧 0 / 保护 ∞。加分仅作编码深度分配与影子副本置信度累积速率参考，不聚合为单标量参与价值裁决（P6）。规则与加分表在 v0.1.0.x 实现阶段按架构 §7.3 权威口径细化。

**热度体系参考参数表（实证参考参数表，债务 D-335，usage-load-algorithm 三.5 与认知基础 §1.1 的工程承接）**：

| 参数 | 参考值 | 用途 |
|:-----|:-------|:-----|
| 热度组合公式 | 热度 = 1.0 + 频次×2 + 新近×10 + 重要性加分（范围 0.5~50，新近度半衰期 20 轮） | 时间衰减函数未闭合（K-063）期间的实证参考 |
| 层级衰减系数 | ×0.985/0.975/0.965/0.95 | 物理时间轴衰减形态参考 |
| 父节点传播 | 父热度 = 子节点 max×0.6 + mean×0.3 + 一致性×0.1 | 路径空间父子热度传播形态参考 |

参考基线非默认值：来源系统以单标量热度近似多维价值，与五维负载向量不同构；v0.1.0.x 校准时以 Kairos 实测为准。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 详细设计：核心组件状态机与算法伪代码（WM/存储/遗忘/升华/校准/事件总线）。 |
| 0.0.2 | 2026-08-04 | 新增 §9 检索引擎：检索管线状态机（解析→路径过滤→时间过滤→三信号融合→5D 调制→GSPO→MMR）、StorageBackend as_of 接口、时间过滤约束。 |
| 0.0.3 | 2026-08-04 | 文档职责剥离承接（changelog 0.0.9 批次）：承接自架构/认知基础的工程实现——§4.1 Reflect 反思循环、§6.1-6.4 元认知代理（认知完整性三维/可及性/CRI/自激回路诊断）、§9.1-9.4 检索去重与实体提取（GSPO/MMR/spaCy/双策略）、§10 注意力调度器（Token 预算/任务感知评分/元记忆/提示词/断点续训/画像基准）、§11 编译与存储基础设施（编译渲染/Connectors/Profile/.kairos/一致性）、§12 探索治理（冷启动种子/批量清理）。组件索引表同步扩充。 |
| 0.0.4~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.4~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：§3 遗忘算法标注 v1.1 完整目标（v0.1.0 单曲线落地）。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：api-spec 章节引用 5 处修正、5D 排序表述清理、reflect 事件复用 sublimation_tick、遗忘伪代码两阶段对齐。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：§3 遗忘伪代码改为架构 freshness 单曲线权威口径（v1.1 二维曲面移出 v0.1.0 执行路径并标注目标段）；状态机图对齐架构四态（active/stale/archived + forgetAfter 分工）；SUPPRESSION_THRESHOLD 从 v0.1.0 路径移除。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次（changelog 0.0.15，依 comprehensive-documentation-audit P4-01）：正文括号间双空格清理 1 处（「（降权检索）  （归档至冷存储）」→「（降权检索）（归档至冷存储）」）。 |
| 0.0.22 | 2026-08-05 | 外部项目理念吸收批次（changelog 0.0.22）：新增「吸收承接注记」节（噪音规则库参考清单与重要性加分表 D-338、热度体系参考参数表 D-335）；§7 层级蒸馏管道补时间粒度层级蒸馏形态对照（D-336）。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：api-spec 中文序引用联动（§十四→§14 等 5 处）。 |
| 0.0.36 | 2026-08-06 | 第三方分析分诊（changelog 0.0.36）：§4 升华管道新增「升华产物质量护栏（R-02）」——strategy 阶段产物与源 item verbatim 相同（或仅格式包装）判定无效升华，标记 `sublimation_invalid` 审计事件并重试一次，重试仍相同则放弃本次升华。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：外部理念吸收表述收敛（R-02 护栏/verbatim 设计来源/时间粒度层级对照去产品名，保留技术信息）；「吸收承接注记」标题去版本号前缀；5D 混合排序两处补历史沿用名注记（架构 §7.3a 术语口径）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：遗忘伪代码删悬空 base_weight；实体提取输出→存储枚举映射注记；§2 写入路径三区流转改写；遗忘状态机补 Superseded 态注记；升华产物质量护栏来源收敛；路径空间统一下划线命名。 |
| 0.0.41 | 2026-08-07 | 外部理念吸收落地批次（changelog 0.0.41）：§2 补写入管线设计（稳定 Memory Key 规范化 / 幂等+乐观锁三分提交 / 索引为派生视图可重建）；§4 补 Compaction 成本-保真三 regime（朴素累积二次方 → 粗摘要线性+准确性悬崖 → 验证压缩线性+保真）；§10.5 补恢复契约六属性（前缀延续/效果恰好一次/分叉确定性/检查点有效性/消费一次/恢复确定性）作为验收标准。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：§10.5 恢复契约六属性验收判据剥离至 acceptance-criteria §三a；§10.2 基准测试集成流程剥离至 benchmark-plan §3.14；§4.1/§6.x 引用修正与决策/债务前缀补标。 |
| 0.0.53 | 2026-08-08 | round23 深度审计修复批次（changelog 0.0.53）：R23-04 `### StorageBackend \`as_of\` 接口（新增）`→去除版本标记。 |
| 0.0.61 | 2026-08-08 | round27 深度审计修复批次（changelog 0.0.61）：§3 遗忘调度器状态机范围注记修正——明确本图仅覆盖 freshness 驱动的 ACTIVE/STALE/ARCHIVED 三态，SUPPRESSED（定向遗忘操作写入）/SUPERSEDED（知识演化 replaces 触发）均不经由本调度器，与架构 §5.2 五态平级口径一致。 |
| 0.0.63 | 2026-08-08 | round29 全面深度审计修复批次（changelog 0.0.63）：§10.6 用户画像缓存解除对 v1.1 组件的依赖——画像读取结果改缓存于画像专用应用层 LRU 缓存（容量独立于数据库访问层），PreparedStatementCache 作为 v1.1 组件（债务 D-418）落地后可共享 LRU 空间但保持独立计数。 |
| 0.0.74 | 2026-08-09 | round38 门禁建议落实批次（changelog 0.0.74）：§事件总线 TTL 注记引用「架构 §10.10 事件类型原语表」→「事件类型枚举表」（架构实际标题为「事件类型枚举」，round37 门禁补盲区 6.26 档 4 捕获的三处同源悬空引用之一）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.75 | 2026-08-09 | round39 全面深度审计修复批次（changelog 0.0.75）：写入管线① 内容级去重引用「data-model §8.3 冲突判定规则」→「data-model §1 memories `content_hash` 列」（data-model §8.3 为 memory_entities 表，全文无「冲突判定规则」章节，悬空引用；content_hash 去重语义承载于 §1 memories 表）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.79 | 2026-08-09 | round41 全面深度审计修复批次（changelog 0.0.79）：恢复契约六属性去除单轨批次号注记「（外部理念吸收 0.0.41）」（豁免 2 条款：仅批次号无外部实证代号不豁免）；事件表分隔行首格补冒号。 |
| 0.0.80 | 2026-08-09 | round42 全面深度审计修复批次（changelog 0.0.80）：引用/口径收口 + 格式收尾 + 术语登记（glossary 70→76）——详见 changelog 0.0.80 叙述节。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85）：状态机死角收口——Reflect done 收敛语义（首次调用建基线、≥2 次比对收敛）、遗忘函数更名 EVALUATE_FRESHNESS + 极性声明 + EXEMPT 哨兵、宪法修订端口补单条记忆出口（contract_downgrade / state_restore，is_identity 须附判例）；幂等键统一（Idempotency-Key + ERR-CTR-005）、乐观锁强制 If-Match；as_of 补软删过滤 + ts 时刻版本选择；Deep C1-C8 全量/哈希 5% 抽检口径澄清；GSPO 补候选集缩减语义；实体置信度阈值改互斥开区间（KAIROS_ENTITY_LLM_DISCARD_THRESHOLD）；陈旧检索不触发复兴口径注记。详见 changelog 0.0.85 叙述节。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87）：写入管线设计② 幂等模型改写（Idempotency-Key 可选头 + 同键返回首次结果 + ERR-CTR-005/ERR-DB-005 两码分工）+ 正文裸引用链接化 4 处。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：H1 标题改为「# Kairos 详细设计」。 |
