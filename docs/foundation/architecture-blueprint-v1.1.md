---
title: Kairos 架构蓝图（v1.1+ 规划）
aliases:
  - architecture-blueprint
tags:
  - kairos
  - blueprint
  - future
created: 2026-07-29
status: draft
updated: 2026-08-08
last_reviewed: 2026-08-08
---

> 本文为 Kairos 架构的未来版本规划蓝图，描述 v1.1+ 目标的详细设计。本文内容**不属 v0.1.0 交付范围**（§5.5 见证→使用仲裁除外——决策 D-05 已迁入 v0.1.0 作为正式交付能力，主架构 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.5 为权威定义，本文 §5.5 不再单独演进），主架构文档 [architecture-v0.1.0.md](architecture-v0.1.0.md) 中的 **§0.1 交付范围**和 **§0.9 差距追踪表**是其与当前版本的映射桥梁。实现者应优先阅读主架构文档，本文仅作为未来版本的参考。

> **与 v0.1.0 的关系**：本文 §5.3–§5.8（价值独立性公理 / 见证轴内仲裁 / 见证→使用仲裁 / 冲突解决 / 多 Agent 校准 / 升华管道 vs 认知层特征空间）被 [architecture-v0.1.0.md](architecture-v0.1.0.md) 作为结论性规范引用（v0.1.0 正文不重复展开，仅在其 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5 顶部加范围说明；**§5.5 见证→使用仲裁除外**——决策 D-05 已迁入 v0.1.0 作为正式交付能力，该处为权威定义）。读者追溯这些机制细节请以本文为准。另：P3-11 Directives / P3-12 malloc_trim / P3-13 Webhook 的逐项功能规格见 [specification/feature-list.md](../specification/feature-list.md) §九（Phase 3 新增）。

## 一、P3 前瞻组件（v1.1+ 目标，非 v0.1.0 交付）

> **P3 编号导航**：本文按主题分组组织 P3 组件，**编号并非严格升序**（P3-11/12/13 位于 P3-14/15/16 之后）。P3-01~07、P3-18 不在本文定义（P3-01~07 分别见 [detailed-design.md](../specification/detailed-design.md) 与 [api-spec.md](../specification/api-spec.md)，P3-18 为未使用编号；P3-19 File Graph 承接自 [technology-stack.md](../development/technology-stack.md) §七，本文仅收录规格摘要）。完整编号→位置索引以 [feature-list.md](../specification/feature-list.md) §九（Phase 3 新增）为准。

> **经验-资产共演化候选注记（外部理念吸收 0.0.48；外部实证：PAPER-16 Mem²Evolve，+18.53% vs 标准 LLM）**：Mem²Evolve 以经验记忆引导动态创建资产（工具/专家 agent）、资产使用回流新经验——共演化优于单轨（对照纯经验 +11.80%、纯资产 +6.46%）。作为 v1.1 升华管道（经验蒸馏，[architecture-v0.1.0.md](architecture-v0.1.0.md) §5.2）与 P3 资产/技能层扩张的联动候选：升华产物（strategy/behavior）→ 引导创建新工具/技能资产 → 新经验回流升华。**门禁**：自动创建资产须过宪法边界 + 审计（与升华管道同门禁），「纯资产创建不稳定」为升华默认 OFF 立场的外部论据。

#### P3-08 GLiNER2 本地 NER（Local NER with GLiNER2 — 205M CPU 模型降本）

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**认知层依据**：纯工程增强——此组件为工程优化手段，不涉及认知层承诺。未实现时实体提取路径回退至 spaCy 规则 + LLM 两段式现有方案。

**定位**：在现有 spaCy 轻量实体提取（[detailed-design.md](../specification/detailed-design.md) §9.3）和 LLM 实体提取（§5 升华管道 L1→L2）之间引入 GLiNER2 作为中间层——以 205M 参数在 CPU 上运行的开放词汇 NER 模型，替代 LLM 调用完成实体提取任务，将实体提取成本从 LLM API 调用降为零成本本地推理。

**设计要点**：

```text
GLiNER2 本地 NER 管线：
  文本输入
    │
    ├─ 快速路径（Fast Path）
    │   实体词典精确匹配（spaCy Matcher，详见 detailed-design §9.3 实体提取）→ 命中则直接返回
    │
    ├─ GLiNER2 路径（Zero-Shot NER）
    │   开放词汇实体识别——无需预定义实体类型，按当前 Profile Schema
    │   中活跃的实体类别（人物/项目/技术栈/工具/概念）动态构建 prompt
    │   → 模型推理（CPU，~50ms/句）→ 返回 (entity_text, entity_label, confidence)
    │
    └─ LLM 兜底路径（仅异常时使用）
        当 GLiNER2 confidence 低于阈值（默认 0.3）或检测到新实体类别
        → 降级至 LLM 提取（Tier 2 轻量模型）
```

**与现有 NER 的关系**：

| NER 方式 | 阶段 | 模型 | 延迟 | 成本 | 适用场景 |
|:---------|:-----|:-----|:-----|:-----|:---------|
| spaCy 规则引擎 | 写入时实时 | 无（规则） | <1ms | 零 | 已知实体精确匹配（人名/邮箱/日期/URL） |
| **GLiNER2** | 写入时实时 | 205M 开放词汇 | ~50ms (CPU) | 零（本地） | 开放词汇实体提取——替代 Tier 2 LLM 调用 |
| LLM 提取 | 升华管道 L1→L2 | Tier 2/3 | 500ms-2s | ~¥0.001/次 | 复杂语义实体（仅 GLiNER2 低置信时兜底） |

**工程权衡**：

- **收益**：将实体的初始提取从 LLM 调用迁移至本地 CPU 推理，按日均 500 条新记忆计算，月节省 LLM 调用成本约 ¥150（对比 Tier 2 LLM 提取）。GLiNER2 的 205M 参数模型内存占用 ~400MB，适合轻量部署。
- **限制**：GLiNER2 的开放词汇识别依赖 prompt 质量——对高度领域特定的实体类别（如「江铜财务公司特定金融工具代码」）可能识别率偏低，需配合领域实体词典。
- **v0.1.0 占位**：当前实体提取路径为 spaCy 规则 + LLM 两段——spaCy 覆盖确定性实体，LLM 覆盖语义实体。v0.1.0 不引入 GLiNER2——保持现有双路径稳定后，v1.1 在 GLiNER2 模型评估通过（在 Kairos 实体提取基准上 F1 ≥ 0.75）后替换 Tier 2 LLM 调用。

#### P3-09 事实三元组直接注入（Fact Triplet Direct Injection — Bypass LLM Structured Write Endpoint `POST /v1/facts`）

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**认知层依据**：纯工程增强——此组件为工程优化手段，不涉及认知层承诺。未实现时外部事实写入路径回退至现有 LLM 提取管道。

**定位**：为外部可信数据源（DFA 确认的事实、Connector 同步的结构化数据、用户显式声明）提供一条绕过 LLM 提取管道的直接写入路径——通过结构化 API `POST /v1/facts` 将 (subject, predicate, object) 三元组直接写入实体知识图谱和关系索引，避免 LLM 提取引入的语义误差和延迟。

**设计要点**：通过 `POST /v1/facts`（见 api-spec §11）将 (subject, predicate, object) 三元组直接写入实体知识图谱和关系索引，绕过 LLM 提取管道。请求体含事实数组（含置信度/来源/证据/时间戳）和选项（跳过 LLM 提取、直接索引、关联记忆 ID）。

**写入路径对比**：

| 路径 | 当前（v0.1.0） | P3-09 目标 |
|:-----|:-----------|:----------|
| 外部事实进入 | 文本→摄取管道→LLM 提取→实体知识图谱 | 三元组→`POST /v1/facts`→直接写入知识图谱 |
| LLM 参与 | 必需（Tier 2 实体提取） | 零（结构化数据直接写入） |
| 延迟 | 500ms-2s | <10ms（纯数据库写入） |
| 语义保真度 | LLM 提取可能引入误差 | 100%（来源数据原样存储） |

**事实来源白名单**：仅以下来源的事实可通过 `POST /v1/facts` 直接注入——(a) DFA 中 `status=active` 且 `confidence ≥ 0.8` 的已确认事实；(b) Connectors 同步的结构化元数据（GitHub `package.json` 依赖、Notion 数据库字段、Gmail 结构化头信息）；(c) 用户通过 `kairos_fact_assert` MCP 工具显式声明的事实（需标注 `user_asserted=true`）。其他来源的事实仍走 LLM 提取管道。此白名单防止非可信来源绕过 LLM 的语义验证。

**与 ADD-only 协议的关系**：`POST /v1/facts` 写入的三元组遵循 ADD-only 协议（[architecture-v0.1.0.md](architecture-v0.1.0.md) §7.3g）——不覆盖已有事实，以叠加模式追加。同一 (subject, predicate, object) 三元组的重复写入不产生新记录（幂等——基于三元组哈希去重），仅更新 `last_observed_at` 时间戳。

**v0.1.0 占位**：v0.1.0 所有外部事实均经过 LLM 提取管道——不存在绕过路径。v1.1 在 DFA 稳定运行（连续 30 天无假阳性确认）后开启 `POST /v1/facts` 端点，首批支持 DFA 确认事实和 Connector 结构化元数据两类来源。

#### P3-10 自定义边类型签名验证（Custom Edge Type Signature Validation — Source/Target Label 组合约束）

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**认知层依据**：纯工程增强——此组件为工程优化手段，不涉及认知层承诺。未实现时关系索引的边创建路径不执行签名验证，所有合法边类型均接受任意 source/target 标签组合。

**定位**：在关系索引的边创建路径上增加编译时签名验证——自定义边类型不仅定义名称，还声明合法的 (source_label, target_label) 组合约束。当边创建请求的 source/target 标签组合不在该边类型声明的合法组合集合中时，写入被拒绝。此机制防止关系索引中出现语义不合法的边（如「项目 has_child 电子邮件地址」）。

**设计要点**：

```text
边类型签名声明（CustomEdgeType）：
{
  "edge_type": "manages_project",
  "description": "用户管理项目",
  "allowed_combinations": [
    {"source_label": "Person", "target_label": "Project"},
    {"source_label": "Team",   "target_label": "Project"}
  ],
  "cardinality": "many_to_many",
  "inverse_edge": "managed_by",
  "validation_mode": "strict"  // strict: 拒绝不合法组合；warn: 告警但放行
}

写入时的签名验证流程：
  边创建请求 (source_id, target_id, edge_type)
    │
    ├─ 1. 查询 source 和 target 的实体标签（从 entities 表）
    │
    ├─ 2. 查找 edge_type 的 CustomEdgeType 声明
    │      ├─ 未找到声明 → 策略：(a) 默认放行（v0.1.0 行为）；(b) 严格拒绝（需配置）
    │      └─ 找到声明 →
    │
    ├─ 3. 检查 (source_label, target_label) 是否在 allowed_combinations 中
    │      ├─ 匹配 → 写入关系索引
    │      └─ 不匹配 →
    │           ├─ validation_mode=strict → 拒绝写入，返回错误 + 合法组合列表
    │           └─ validation_mode=warn  → 写入但标记 edge_quality=unverified，
    │                                       写入审计日志标记 edge_validation_warning
    │
    └─ 4. 写入成功后，自动创建逆边（inverse_edge）
```

**预定义边类型签名表**（v0.1.0 内置草稿）：

| 边类型 | 合法 source→target 组合 | 逆边 | 用途 |
|:-------|:----------------------|:-----|:-----|
| `manages_project` | Person→Project, Team→Project | `managed_by` | 项目管理关系 |
| `uses_technology` | Project→Technology, Person→Technology | `used_by` | 技术栈关系 |
| `part_of_team` | Person→Team | `has_member` | 团队归属 |
| `depends_on` | Project→Project, Task→Task, Service→Service | `dependency_of` | 项目/任务依赖 |
| `authored_by` | Document→Person, Code→Person | `author_of` | 作者归属 |
| `references` | Memory→Memory, Document→Document | `referenced_by` | 引用关系 |

**工程权衡**：

- **收益**：防止 LLM 提取阶段产生语义不合法的关系边（当前 v0.1.0 无约束——任何 (source, target) 均可创建任意 relation_type 的边）。签名验证在写入时拦截非法边，避免后续检索和推理基于错误的关系拓扑。
- **风险**：过于严格的验证可能阻止合法但未预见的边类型组合——需要 `validation_mode=warn` 模式在初期积累数据后再收紧。边缘类型的 `allowed_combinations` 须易于扩展（配置文件驱动，非硬编码）。
│   - **管理接口**：通过边类型管理 API（见 api-spec §12）注册新边类型签名、查询已注册签名、更新合法组合（不影响已有边——仅对新写入生效）。

**v0.1.0 占位**：v0.1.0 不实施边类型签名验证——所有边创建请求直接写入关系索引，无标签组合约束。v1.1 在实体知识图谱的实体标签覆盖率 ≥ 80%（即至少 80% 的实体节点已有明确标签）后激活签名验证——先以 `warn` 模式运行一个观察期，审计日志确认无误报后切换至 `strict` 模式。

#### 过程知识 Playbook 系统（Procedural Playbook System）

  ┌─ 过程知识 Playbook 系统（Procedural Playbook System）
  │   升华管道 strategy→behavior 阶段的显式产物管理子系统——将可复用的过程知识从记忆体中独立为结构化 playbook。
  │   **程序记忆文档化声明（决策 D-16 批次）**：Playbook/Skills 的可全文检索文档化表征
  │   **不改变程序记忆的认知激活规则**——认知基础 §1.3.1 定义程序记忆「不输出到工作记忆的检索列表，
  │   直接输出为系统行为倾向」；Playbook 的可检索文档化是**外部交付形态**（供外部 Agent/用户审查、
  │   供 find_skills 意图匹配检索），不是程序记忆的认知激活路径（激活仍由情境触发+路径前缀匹配
  │   独立决定，见架构 §5.2 内容类型编码层）。「过程知识的文档化副本」与「程序记忆表征」是
  │   同一经验的两类形态：前者面向陈述性检索（「怎么做」的知识化表述），后者面向内隐激活
  │   （行为输出的能力性沉积）。此声明防止「程序记忆被重构为语义记忆」的认知偏离。
  │   Playbook 结构：id, scope_id, task_class, title, trigger, goal, preconditions[], steps[][含 capability_class/action/evidence_required/why/previous_mistakes],
  │   pitfalls[], verification[], cleanup[], reuse_policy, status, confidence, success/failure/stale_count, related_skills[], evidence_anchors[]
  │   状态机：candidate(蒸馏产出)→needs_review(自动标记)→reviewed(审查通过)→promoted(正式可用)→superseded(被替代)
  │   - candidate→needs_review：升华管道 strategy 阶段产出 playbook 时，自动标记 needs_review（默认）
  │   - needs_review→reviewed：经宪法解释层或用户审查确认后转换
  │   - reviewed→promoted：连续 N 次成功反馈后自动提升（N 由 `KAIROS_PLAYBOOK_PROMOTION_THRESHOLD` 配置，默认 3）
  │   - promoted→superseded：被新 playbook 标记 replaces 或连续 negative 反馈阈值（`KAIROS_PLAYBOOK_NEGATIVE_THRESHOLD` 默认 3）触发
  │   反馈循环：每次 playbook 使用后记录 outcome（success/partial/failed/stale/misleading），更新 success/failure/stale_count 和 confidence
  │   confidence 递推：新 playbook 默认 0.5；每次 success +0.05，每次 failed -0.10（下限 0.05，上限 0.99）
  │   全文索引：对 title/trigger/goal/steps 建 FTS5 索引，支持按 task_class 过滤和语义+词法混合检索
  │   与升华管道的关系：raw→item→strategy→behavior 中的 strategy 阶段产出 playbook candidate，
  │   behavior 阶段的成功执行驱动 candidate→promoted
  │   存储层：procedural_playbooks 表 + procedural_playbooks_fts FTS5 表 + playbook_versions 表（每次状态变更记录版本快照）
  │
#### 三级技能进化（Skill Evolution）

  ├─ 三级技能进化（Skill Evolution）
  │   在升华管道 + Playbook 系统之上定义技能的渐进成熟路径——从原始痕迹到可交付技能库。
  │   L1 Traces（痕迹层）：原始对话片段中可复现的操作模式。由升华管道 L0→L1 阶段自动标记，不独立存储，由 L2 蒸馏消费。
  │   L2 Policies（策略层）：可复用的操作策略——对应升华管道的 strategy 阶段输出，存储为 Playbook candidate。
  │      Candidate confidence < 0.7 时保持 needs_review 状态；经 Playbook 反馈循环提升 confidence 后进入 reviewed/promoted。
  │   L3 World Model（世界模型层）：跨任务、跨 session 的稳定认知模式。
  │      Playbook 中被连续多次 success 的模式推广为 world model 规则，存入 `world_model_rules` 表。
  │      规则触发条件：同一操作模式在 ≥3 个不同 task_class 下均获 success ≥5 次。
  │      world_model_rules 表：rule_id, task_class, trigger_condition, action_template, preconditions, confidence, evidence_count, created_at
  │   Skills（结晶技能）：经过严格验证的可交付技能。
  │      Playbook status=promoted + 满足技能生命周期状态机的晋升门禁（usage_count ≥
  │      KAIROS_SKILL_PROMOTION_MIN_USAGE（默认 5）且 success_rate ≥ KAIROS_SKILL_PROMOTION_MIN_RATE（默认 0.7），
  │      见技能生命周期状态机）+ 被 ≥ KAIROS_SKILL_PROMOTION_MIN_CONTEXTS（默认 2）个独立上下文引用。
  │      达到条件后自动注册到 Hermes skill 目录（MCP 工具接口）供跨会话调用。
  │   进化门禁：低级→高级的跃迁必须满足对应的置信度下限和证据数量，不可跳过层级。
  │   - L1→L2：同一操作模式在 session 中出现 ≥3 次（由升华管道统计）
  │   - L2→L3：Playbook 在 ≥KAIROS_WORLD_MODEL_MIN_CLASSES（默认 3）个不同 task_class 下 success ≥KAIROS_WORLD_MODEL_MIN_SUCCESS（默认 5）
  │   - L3→Skills：World model 规则被 ≥2 个独立上下文引用且总 evidence_count ≥10
  │
#### 技能管理系统（Skill Management System）

  ├─ 技能管理系统（Skill Management System）
  │   在三级技能进化的提炼管道之上，提供显式的技能注册、检索、版本化与生命周期管理——将技能从
  │   「隐式记忆产物」提升为「一等可治理实体」。本系统是三级技能进化中 L3 Skills 层的工程落地。
  │
  │   **skills 表**（详见 [data-model.md](../specification/data-model.md)）：
  │   `(id, name, description, category, embedding, status: experimental/active/deprecated/archived/superseded/retired,
  │     version, source_playbook_id → procedural_playbooks, source_memory_ids[], usage_count,
  │     success_rate, last_used_at, created_at, updated_at, superseded_by, confidence, metadata)`
  │   状态枚举以技能生命周期状态机的六态为权威（experimental/active/deprecated/archived/superseded/retired，见下）
  │   每条 skill 记录关联其来源——可追溯到产出该技能的 playbook（三级进化 L2→L3 的门禁记录）
  │   和原始记忆条目（完整的溯源链），确保技能的可审计性。
  │
  │   **find_skills 语义搜索**：
  │   技能检索的核心接口——`find_skills(query: str, context: dict, top_k: int) → list[SkillMatch]`。
  │   不同于通用记忆检索（路径空间优先 + 语义 + 情境 + 三链路加权），技能检索使用专门的两阶段管道：
  │   - **Stage 1 语义粗筛**：对 query 生成 embedding，在 skills 表的向量索引中执行 ANN 检索（k=20），
  │     按余弦相似度降序排列。
  │   - **Stage 2 上下文精排**：LLM 对粗筛结果做语义重排序——考虑当前任务上下文（task_class、活跃实体、
  │     最近使用的技能历史），为每个候选技能输出 relevance(0-1) + rationale。重排序使用轻量模型
  │     （成本护栏，同 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.9 模型路由梯队的 Tier 2/3 梯队）。
  │   - **反馈闭环**：技能被选中执行后，执行结果（success/failure）回写 skills 表更新 success_rate，
  │     影响后续排序中的置信度加权（success_rate 加权系数默认 0.15）。
  │   find_skills 与通用记忆检索（[architecture-v0.1.0.md](architecture-v0.1.0.md) §4 检索路径）的区别：技能检索是**意图匹配**（「我需要做什么」），
  │   而非内容检索（「我记得什么」）——因此不经过路径空间的确定性索引，直接走语义+LLM 重排。
  │
  │   **技能生命周期状态机**：
  │   技能从诞生到退役经历五个阶段，完整状态转移如下：
  │   ```
  │   experimental ──(验证通过)──→ active ──(长期未用)──→ deprecated ──(TTL到期)──→ archived
  │        │                          │                        │
  │        └──(验证失败)──→ retired   │                        └──(被替代)──→ superseded
  │                                   └──(被替代)──→ superseded
  │   ```
  │   状态转换条件：
  │   - `experimental → active`：usage_count ≥ `KAIROS_SKILL_PROMOTION_MIN_USAGE`（默认 5）且
  │     success_rate ≥ `KAIROS_SKILL_PROMOTION_MIN_RATE`（默认 0.7）。激活由后台维护引擎
  │     Deep 模式检查。
  │   - `experimental → retired`：experimental 状态持续 > `KAIROS_SKILL_EXPERIMENTAL_MAX_AGE`
  │     （默认 30 天）且 usage_count < 3（实验阶段未获得足够验证）。
  │   - `active → deprecated`：连续 `KAIROS_SKILL_DEPRECATION_INACTIVE_DAYS`（默认 90 天）
  │     未使用，自动标记 deprecated——降低检索权重但保留在索引中。
  │   - `deprecated → archived`：deprecated 状态持续 > `KAIROS_SKILL_ARCHIVE_DAYS`（默认 180 天）
  │     archived 技能不参与 find_skills 检索，仅通过技能列表 API 历史查询可见（见 api-spec §13 GET /v1/skills）。
  │   - `active/deprecated → superseded`：新技能通过技能管理 API 标记替代关系（见 api-spec §13 POST /v1/skills/{id}/supersede），旧技能写入 `superseded_by` 字段。
  │   - 复活路径：archived 技能可通过技能管理 API 重新激活（见 api-spec §13 POST /v1/skills/{id}/reactivate）为 experimental（置信度重置为 0.5），重新进入验证周期。
  │   所有状态变更写入 `skill_versions` 表（同 playbook_versions 的快照模式），
  │   操作日志写入审计日志标记 `skill_lifecycle`。
  │
  │   **技能与 Playbook 的关系**：
  │   Playbook 是过程知识的内部表示（L2 Policies），Skills 是 Playbook 经过充分验证后的
  │   外部可交付形态（L3 Skills）。一个 Skill 可由一个或多个 Playbook 的成功执行模式聚合而成——
  │   这是三级进化中 L2→L3 的架构承载。Playbook 记录「怎么做到」的过程知识，Skill 记录「能做什么」
  │   的对外能力声明。两者互补：Playbook 被替代时，依赖它的 Skill 自动触发重新验证（标记
  │   `needs_revalidation`），确保技能库不包含已过时的过程知识。
  │
#### 四层记忆质量层次（Four-Tier Memory Quality Hierarchy）

  ├─ 四层记忆质量层次（Four-Tier Memory Quality Hierarchy）
  │   在现有记忆分类（episodic/semantic/procedural）和蒸馏层级（distill_level 0-4）
  │   之上，定义记忆的认知质量层级——决定检索时的优先级和上下文预算分配。四层从高到低为：
  │
  │   ```
  │   mental_models（心智模型层）── 最高优先级，不可被遗忘调度器归档
  │        ↑ 抽象聚合
  │   observation（观察层）── 经多次验证的经验性知识
  │        ↑ 模式识别
  │   experience（经验层）── 单次或少量验证的任务经验
  │        ↑ 蒸馏
  │   world（世界层）── 原始外部事实，最低优先级
  │   ```
  │
  │   **层级定义与准入条件**：
  │
  │   | 层级 | 定义 | 准入条件 | 检索优先级权重 | 遗忘豁免 | 典型内容 |
  │   |:----|:-----|:---------|:-------------|:---------|:---------|
  │   | **mental_models** | 跨任务、跨领域的稳定认知框架——用户的世界观、核心价值观、长期决策偏好。最抽象层 | 蒸馏层级 ≥ 3（L3 weekly/L4 profile），且（身份记忆优先——is_identity=true 直接满足；非身份记忆经宪法解释层出具判例后可入），且 calibration_confidence ≥ 0.8 | 1.00（基准） | 完全豁免（同 is_identity 保护） | 「用户偏好 Rust 胜过 Python」「用户认为先设计后编码」 |
  │   | **observation** | 经多次验证且去语境化的知识——不再是单次经验的产物 | 蒸馏层级 ≥ 2，且去语境化程度 ≥ 0.5，且被 ≥2 条独立记忆引用 | 0.75 | 部分豁免（遗忘阈值是常规的 2 倍） | 「该项目的 CI 管道在 PR 合并后自动触发」「用户过去 5 次代码审查都要求增加测试」 |
  │   | **experience** | 单次或少量重复的任务经验——仍携带时空情境 | 蒸馏层级 ≥ 1，有明确的 encoding_context | 0.50 | 无豁免（标准遗忘曲线） | 「上周在 feature/auth 分支遇到的连接超时」「本次会话中用户说喜欢简洁的 UI」 |
  │   | **world** | 原始外部事实、一次性查询结果、未经验证的信息片段 | 默认层级——所有新记忆的初始质量层级 | 0.25 | 无豁免，且临时契约默认绑定 | 「StackOverflow 上某帖子的答案」「API 文档中某接口的参数说明」 |
  │
  │   **检索时的层级优先与回退机制**：
  │   - **优先填充**：检索时，首先在 mental_models 层中匹配（语义相似度），置信度 ≥ 0.7 的结果
  │     作为高优先级候选直接进入 WM 上下文。mental_models 层的匹配结果数量不足时，按层级顺序
  │     逐步向下回退（mental_models → observation → experience → world），直至候选集满足
  │     context_budget 的最小填充量。
  │   - **回退信号**：当高层级候选不足时，回退操作写入使用事件总线标记 `quality_fallback`，
  │     附加回退层级差（如 mental_models→experience 差为 2）供元认知层监测——高频回退是
  │     mental_models 覆盖不足或知识结构退化的预警信号。
  │   - **层级间无硬截止**：回退不是硬性阻断——低层级候选即使高层级充足时也保留在候选集中
  │     （加权系数 0.1），防止「高层级盲区」导致完全丢失相关信息。这确保跨层级的信息不被
  │     层级边界割裂。
  │   - **蒸馏升级路径**：experience 层的记忆经多次检索验证和升华管道处理后，可提升至
  │     observation 层（去语境化程度达标 + 多次验证）。observation 层的记忆经 L3 weekly
  │     聚合后，可晋升至 mental_models 层（满足 is_identity 和置信度条件）。升级不是自动的——
  │     由 Deep 模式维护任务检测升级条件，经宪法解释层审查后执行。
  │
  │   **质量层级与现有分类轴的关系**：
  │   - 质量层级 ≠ 记忆类型（episodic/semantic/procedural）：同是 semantic 类型的记忆，
  │     「API 文档原文」属于 world，「API 使用最佳实践」属于 observation。质量分层是认知深度轴，
  │     记忆类型是内容形式轴——两轴正交。
  │   - 质量层级 ≠ 蒸馏层级：蒸馏层级描述处理的阶段（L0→L4 管道位置），质量层级描述认知价值。
  │     一条 distill_level=3 的记忆可能仍是 observation（未被提升至 mental_models），
  │     一条 distill_level=1 的记忆可能已被标记为 mental_models（如核心身份记忆）。
  │   - 质量层级与身份标志保持**正交性**（决策 D-16 批次）：is_identity=true 不是 mental_models 的
  │     充要条件——身份记忆在准入中获得优先（直接满足），但非身份记忆经宪法解释层判例也可晋升
  │     mental_models（如经长期多源验证的领域世界观）。此修正消除「非身份记忆永远到不了最高质量层」
  │     的结构性封顶，与认知基础 §1.2 记忆质量层次（mental_model 层级不绑定身份标志）对齐。
  │   - 质量层级存储在 `memories` 表的 `quality_tier` 字段（ENUM: mental_models/observation/
  │     experience/world，DEFAULT 'world'）。
  │
  │   **Mental Model 基于源头的可刷新性（Source-Refreshable Mental Models）**
  │     mental_models 层级的记忆不是孤立的知识节点——它们通过 DERIVED_FROM 关系与底层源记忆
  │     （observation/experience/world 层级的记忆）保持可追溯的派生链路。当源记忆发生变化时，
  │     依赖它的 mental_models 自动触发重新生成评估，确保高层认知框架不会基于过时的底层事实。
  │
  │     **DERIVED_FROM 关系**：
  │     - 定义：DERIVED_FROM 是 memory_relations 表的新增关系类型（relation_type='derived_from'），
  │       方向为 mental_model → source。一条 mental_model 可有多条 DERIVED_FROM 边指向其
  │       派生来源（由升华管道 L3 weekly 聚合时自动创建）。
  │     - 创建时机：当 Deep 维护任务检测 memory 晋升至 mental_models 层时，自动扫描该 memory 的
  │       source_memory_ids（来自升华管道的聚合溯源），为每条源记忆创建 DERIVED_FROM 边。
  │     - 关系强度：DERIVED_FROM 边的 strength 字段表示源记忆对该 mental_model 的贡献权重——
  │       由升华管道在聚合时根据各源记忆的使用频率和置信度综合计算。
  │
  │     **源变化触发重新生成（Re-generation on Source Change）**：
  │     - 触发条件：当一条被 DERIVED_FROM 边引用的源记忆发生以下任一变化时——
  │       (a) 状态变为 `superseded`（被新知识取代）；(b) `calibration_confidence` 下降超过 0.3
  │       （外部校准降低了可信度）；(c) `contradiction` Flag 被挂载（检测到矛盾）。
  │     - 触发动作：对受影响的 mental_model 挂载 `needs_regeneration` Flag → 降低该 mental_model
  │       在检索中的优先级加权（默认降权系数 0.5，因为其派生基础可能已失效）→ 在下一 Deep 维护周期中，
  │       系统对该 mental_model 执行重新生成评估——聚合当前有效的源记忆（排除 superseded/contradiction
  │       源），通过 LLM 重新生成 mental_model 内容并与当前版本对比：
  │       · 内容无实质变化 → 摘除 Flag，恢复权重。
  │       · 内容有实质变化 → 写入新版本（version 递增），旧版本标记 superseded，新版本继承
  │         DERIVED_FROM 边（更新为当前有效的源记忆集合）。
  │       · 有效源不足（DERIVED_FROM 边中 ≥50% 的源记忆失效）→ mental_model 降级至 observation
  │         层级（`quality_tier` 降级），转为常规经验知识等待重新积累。
  │
  │     **离线优先设计**：DERIVED_FROM 追踪和重新生成评估均为周期性离线任务（Deep 模式日频执行），
  │     不参与实时检索路径——mental_model 的降权是即时生效的（Flag 挂载时检索立即感知），但重新生成
  │     本身在后台异步完成。此设计与认知完整性轴的「离线可计算」声明（[architecture-v0.1.0.md](architecture-v0.1.0.md) §0.1）一致：结构变化不需实时反映。
  │
  │     **配置参数**：`KAIROS_DERIVED_FROM_MIN_STRENGTH`（默认 0.3，低于此强度的 DERIVED_FROM 边
  │     在重新生成时忽略），`KAIROS_DERIVED_FROM_REGENERATION_INTERVAL`（默认 Deep 模式日频），
  │     `KAIROS_DERIVED_FROM_MIN_VALID_SOURCES_RATIO`（默认 0.5，有效源低于此比例触发降级）。
  │
#### MemCube 四层记忆分化（Four-Layer Memory Differentiation）

  └─ MemCube：四层记忆分化（MemCube Four-Layer Memory Differentiation）
      认知基础中「激活-存储解耦」（推论三）的架构分化落地——记忆不是单一存储实体，而是在四个
      维度上以不同形态同时存在，每层回答不同的问题且有不同的访问速度和持久性特征。四层分工：

      **工程层声明（决策 D-16 批次）**：MemCube 的 L3（Parametric 参数层）与 L4（Preference 偏好层）
      **是工程层，不映射认知层记忆分类**——认知基础的三层记忆结构（内容层/签名层/关系层）与
      记忆类型学（情景/语义/程序）是认知层定义；L3 模型权重与 L4 配置/种子是工程存储形态。
      「四层记忆分化」中的「记忆」是工程隐喻而非认知断言：(a) L3 参数层承载的是「内化到模型
      权重的行为知识」（对应 D-17 B1 决策的参数级学习声明），不是认知层的记忆表征；(b) L4 偏好层
      承载注册表内容（config/seeds/宪法规则）——注册表在认知基础 §1.7 被明确定位为确定性状态存储，
      与记忆互补而非记忆本身。此声明防止实现者将「四层」误读为认知层的记忆分类扩展。

      ```text
      ┌─────────────────────────────────────────────────────┐
      │  L4 Preference（偏好层）── 最稳定，决定系统行为倾向   │
      │   存储：user_profiles 表 + seeds 表 + config 表       │
      │   访问：每次决策时加载（成本几乎为零）                │
      │   更新：L4 profile 聚合 + 外部校准 + 宪法修订          │
      │   内容：用户偏好、系统配置、种子锚点、宪法规则          │
      │   问答：「我应该怎么做」                               │
      ├─────────────────────────────────────────────────────┤
      │  L3 Parametric（参数层）── 模型权重中的隐性知识       │
      │   存储：微调适配器权重 / LoRA / RL 权重参数             │
      │   访问：模型推理时内隐激活（不经检索）                  │
      │   更新：RL 权重优化器（实现见 rl-weight-spec.md）周期性更新               │
      │   内容：内化的任务模式、语言习惯、隐式偏好              │
      │   问答：「我（模型）已经知道什么」                      │
      ├─────────────────────────────────────────────────────┤
      │  L2 Activation（激活层）── 当前上下文的活跃记忆       │
      │   存储：WM 层活跃槽位 + 近期检索缓存                    │
      │   访问：毫秒级——直接上下文注入                          │
      │   更新：每次 turn 开始时检索 + 上下文窗口滚动            │
      │   内容：当前任务相关的记忆、最近编码的事实               │
      │   问答：「我现在在想什么」                              │
      ├─────────────────────────────────────────────────────┤
      │  L1 Textual（文本层）── 持久化的完整记忆体             │
      │   存储：memories 表 + memory_chunks 表 + cold storage  │
      │   访问：百毫秒级——向量检索 + 路径空间 + 三链路加权      │
      │   更新：retain 写入 + 升华管道 + 遗忘调度器              │
      │   内容：所有编码的记忆条目，完整内容 + 向量 + 元数据     │
      │   问答：「我经历了什么 / 我知道什么」                   │
      └─────────────────────────────────────────────────────┘
      ```

      **四层分化 vs 现有存储架构**：
      MemCube 不是新增的存储子系统，而是对现有存储架构的概念整合——现有组件已覆盖全部四层，
      本声明将它们组织为一致的认知分化框架：

      | MemCube 层 | 现有承载 | 分化价值 |
      |:----------|:---------|:---------|
      | Textual | memories + memory_chunks + 冷存储 | 所有编码记忆的持久基础——回答「世界是什么」 |
      | Activation | WM 活跃槽位 + 检索缓存 | 当前上下文的瞬态工作集——回答「现在关注什么」 |
      | Parametric | RL 权重优化器 + 微调适配器 | 内化到模型参数的知识——回答「我已经学会什么」 |
      | Preference | user_profiles + seeds + config | 稳定的行为倾向基线——回答「应该怎么做」 |

      **层间信息流动**：
      - **Textual → Activation**：检索（路径空间 + 语义 + 三链路加权）将 Textual 层记忆
        提升至 Activation 层——这是系统主要的「记忆→上下文」通道。
      - **Activation → Textual**：retain 写入将 Activation 层的活跃信息持久化至 Textual 层——
        编码特异性原则在此生效（encoding_context 记录 Activation 时刻的情境）。
      - **Textual → Parametric**：RL 权重优化器周期性消费 Textual 层的使用反馈数据
        （usage_events 表中的检索-选择-结果三元组），更新 Parametric 层的权重参数。
      - **Textual → Preference**：L4 profile 聚合从 Textual 层的长期模式中提取稳定偏好，
        写入 Preference 层。
      - **Preference → Activation**：每次 turn 开始时，Preference 层的配置/偏好注入
        Activation 层作为硬约束上下文（如 rl_weights 的排序权重配置）。
      - **Parametric → Activation**：模型推理时，Parametric 层的隐式知识通过内隐激活
        影响 Activation 层的候选排序——不经显式检索通道。

      **MemCube v0.1.0 交付范围**：
      - Textual 层：核心功能——memories 表的完整 CRUD + 检索（路径空间 + 向量 + 三链路）。
      - Activation 层：WM 层活跃槽位管理 + 上下文窗口编译（[architecture-v0.1.0.md](architecture-v0.1.0.md) §6, §7）。
      - Preference 层：user_profiles 表的静态/动态画像 + seeds 表 + config 表（已有）。
      - Parametric 层：RL 权重优化器（[rl-weight-spec.md](../specification/rl-weight-spec.md) §权重优化器实现）的基础框架——v0.1.0 实现权重更新协议和反馈
        数据收集，v1.1 实现完整的微调适配器集成（LoRA 热插拔）。
      **v1.1 目标**：Parametric 层的完整闭环——从使用反馈到权重更新到模型行为改变的可观测链路。

#### 事实新鲜度元数据（Fact Freshness Metadata）

  └─ 事实新鲜度元数据（Fact Freshness Metadata）
      为确定性事实记忆提供独立的新鲜度追踪——与遗忘调度器的 freshness 计算互补但不重叠。
      fact_freshness 表：id, subject_type, subject_id, fact_key, truth_type, validator_kind(none/file_exists/command/http/manual),
      validator_spec(JSONB), ttl_days, last_checked_at, valid_until, status(current/expired/stale/superseded/needs_live_check),
      stale_reason, superseded_by
      新鲜度衰减系数（freshness_penalty）作为检索排序的衰减输入：
      - stale 记忆：penalty = 0.28（排序时适度降权——内容可能仍有效）
      - expired 记忆：penalty = 0.35（排序时更大降权——已确定过期）
      - needs_live_check 记忆：penalty = 0.18
      - current/fresh/verified：penalty = 0
      写入时机：记忆写入时检测 metadata 中的 memory_type，当类型为 factual/project_fact/environment_fact 时自动创建/更新 freshness 行
      后台维护：Deep 模式执行过期扫描——valid_until 已过期的标记为 expired，连续 expired 超过 N 周期的标记为 stale

      支持临时事实智能过期——在写入时对记忆内容检测时间指示模式：
      - 明确的未来时间点（"明天""下周""下个月""June 15"）、临时状态（"在找""正在申请"）
      - 匹配临时模式时自动设置合理的 valid_until（基于检测到的日期 + KAIROS_TEMPORAL_EXTRA_BUFFER_DAYS 默认 7 天）
      - 未匹配临时模式时保持 valid_until = NULL（永久有效，等待其他失效机制）
      配置：KAIROS_TEMPORAL_EXPIRY_ENABLED（默认 true），KAIROS_TEMPORAL_APPLY_THRESHOLD（默认 0.7）

#### 社区检测（Community Detection）

  ┌─ 社区检测（Community Detection）
  │   在后台维护 Deep 模式中执行，对 entities 表 + memory_entities 表的实体关系图做自动社区聚类。
  │   算法：Label Propagation（默认），可扩展至 Leiden/Louvain。
  │   输出：entity_communities 表——id, community_label, member_entity_ids[], summary, detection_algorithm, confidence
  │   社区摘要由 LLM 生成，聚合社区内实体的名称、类型分布、关键关系。
  │   消费方式：
  │   - 检索时附带 community_id 参数限定范围
  │   - 社区摘要作为高层上下文注入，避免检索分散在多个不相关实体群中
  │   - Deep 模式每次执行重新检测，增量更新已有社区
  │   配置：KAIROS_COMMUNITY_DETECTION_ENABLED（默认 true），KAIROS_COMMUNITY_DETECTION_ALGORITHM（默认 label_propagation），KAIROS_COMMUNITY_MIN_SIZE（默认 3）

## 二、核心机制规格（§5.3~§5.8，被 v0.1.0 结论性引用）

### 5.3 价值独立性公理

**价值独立性公理：** 使用权重（「好用」）与见证锚定（「真实/自洽」）之间存在结构性冲突，非默认和谐。系统不假设高使用频率的记忆为真实记忆——「好用 ≠ 真实」。

**架构承载：**
- 使用权重陡升 → [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.5 差异检验（语义内核相似度比对）
- 高负载+低见证 → 合并阻断（[architecture-v0.1.0.md](architecture-v0.1.0.md) §5.5 step 8）
- 语境自指禁令（S-14）：内部信号不得作为见证锚定真实性的证据来源

此公理与辞典式裁决排序中「探索 > 宪法 > 校准 > 认知完整性 > 时间 > 间接度」一致——身份（见证锚定）高于使用排序（时间/间接度），以正交否决权介入。

> **决策效用张力注记（外部理念吸收 0.0.48；外部实证：PAPER-19 DeMem / PAPER-20 Mem-W 结果感知过滤）**：外部将记忆价值定义为「压缩导致的决策质量损失」（DeMem 率失真框架）或「过滤向任务成功证据」（Mem-W 结果感知监督）——纯粹实用主义记忆观。与本文价值独立性公理（「好用 ≠ 真实」）形成张力：记忆价值 = 当下决策效用 vs 见证锚定真实性。Kairos 双标准分域立场：使用侧热度承载效用面（决策相关保留优先），见证锚定承载真实性面（过滤决策不得介入真实性裁决）；DeMem 的率失真遗忘边界作为遗忘调度器代价函数的参考（评估注记，不入裁决链，见 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5 遗忘调度器）。

### 5.4 见证轴内仲裁

见证价值轴由外部校准和内部叙事自洽度双层构成。两信号冲突时的仲裁规则：

1. **外部校准为一等约束：** 当外部校准（不含 virtual 标记的拟真校准信号）与内部叙事自洽度计算值冲突时，外部校准覆盖内部计算值。标记为 `virtual` 的校准信号（[architecture-v0.1.0.md](architecture-v0.1.0.md) §1.2 虚拟校准生成器）走独立校验路径——仅比对不触发 override，不适用本规则。原内部叙事自洽度标记为 `overridden_by_external`，存档于主副本元数据供审计。

  **is_identity 不可侵犯：** 外部校准覆盖操作不得影响 is_identity 标志位的存续状态。is_identity 的变更（含降级为普通记忆）仅可经宪法修订端口（[architecture-v0.1.0.md](architecture-v0.1.0.md) §1.2）且经宪法解释层出具语境适用性判例后执行，见证仲裁无权单方面更改。
  **错误见证锚定的半衰期与自愈机制**：若一条记忆被错误地见证锚定且外部校准长期静默，其修正依赖可能永不到达的外部校准信号。补偿机制——(a) 每条见证锚定记忆的 `calibration_confidence`（[architecture-v0.1.0.md](architecture-v0.1.0.md) §5.2）按配置的衰减率随时间降权，即使无校准事件也会渐进降权；(b) 当 `calibration_confidence` 衰减至阈值以下时，记忆自动从「见证锚定优先」降为「使用权重优先」——降为使用权重优先，合并仍受主架构 §5.5 第 8 步约束（高负载+低见证的影子副本不得合并回主副本），差异检验持续生效；(c) 若降权后使用权重与记忆内容出现持续矛盾，触发「见证锚定存疑」告警至宪法解释层。衰减率和阈值见 [ops/configuration.md](../ops/configuration.md)
2. **重算触发：** 覆盖触发后，叙事连贯性检测器（[architecture-v0.1.0.md](architecture-v0.1.0.md) §2.2）自动重启该记忆所在时间窗口的连贯性重算。重算基线切换为外部校准覆盖后的新分数——检测器以新基线做偏移检测，避免持续发出已处理告警。若检测器输出持续背离外部校准超过预设周期数（可配置），通过宪法主权面发出「解释枯竭告警」——提示外部校准与内部叙事存在结构性张力，需外部审慎复核。
3. **无冲突基线：** 内部叙事自洽度在无外部校准冲突时，独立作为见证价值轴的运作基础。

### 5.5 见证→使用仲裁

> **v0.1.0 已采用（决策 D-05）**：本节机制的 v0.1.0 采用版以 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.5 为**唯一权威定义**——步骤 1–11、CQRS 回滚四态协议、探索产物置信度带等全部规则与配置参数以主架构为准（含 0.0.40 后新增的处理完降温/范围性回滚/查询期重建产物治理）。本文不再承载副本定义，仅保留摘要与指针。

**摘要**：见证锚定（主副本）与使用权重（影子副本）的合并仲裁——使用更新仅修改影子副本，累积至置信度阈值异步合并；使用权重陡升/单调上升/绝对偏移三类触发差异检验（分级触发：低风险场景快速校验 <50ms，高风险场景完整比对+沙箱隔离验证）；合并阻断后按 `blocked → degraded → pruned → rollback` 四态降级链处理（CQRS 回滚协议，阻断原因标记 `merge_blocked`）；高负载+低见证的影子副本不得合并（防高使用频率篡改真实性，S-14 语境自指禁令）；探索产物降权累积（初始 30%，每成功验证提升一档至 50%→70%→95% 后转为常规记忆）。**全部细节与参数见 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.5**。

### 5.6 新信息冲突解决（补充/修正/重构）

当新记忆写入与旧有记忆冲突时，按三类场景分别处理：

- **补充**：新信息在旧信息之外增加细节，不否定旧信息。直接合并入 LTM，旧信息的见证锚定不受影响。补充后的记忆在检索时获得多来源加权（新旧来源各自独立投票）。
- **修正**：新信息直接否定旧记忆的核心主张。旧记忆标记为 `superseded_by_{new_id}`，保留原始内容但不参与激活权重计算。新记忆以独立条目写入 LTM，获得单独的使用价值起点。修正场景由 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.5 差异检验的兜底机制覆盖（累积偏差检测自动触发）。
- **重构**：新信息改变系统理解旧信息的方式，而非否定旧信息的内容。旧信息本身不变，但其在认知结构中的位置和关联权重重新计算——整合窗（[architecture-v0.1.0.md](architecture-v0.1.0.md) §5.2）的前向关联权重微调承担此职能。重构不产生新条目，只更新关联图拓扑。

三类场景由接入层摄取管道（[architecture-v0.1.0.md](architecture-v0.1.0.md) §7.3）在写入时根据语义内核相似度判定：高相似度（cosine ≥ 0.85）→ 补充；中等相似度（0.60 ≤ cosine < 0.85）且核心主张冲突 → 修正；低相似度（cosine < 0.60）或语义位移但无核心冲突 → 重构。

> **P6 受控例外声明**：系统定义记忆的三种模态（确定性/可能性/假设性）为连续置信度谱上的锚点区间，模态转换应基于置信度梯度做渐进修正。当前架构实现采用离散模态标记（如 `virtual` / `external` / `provisional_during_calibration_gap`），此为 v0.1.0 的受控简化。离散化造成的信息损失（过渡区间的中间状态未建模）标注如下——(1) 丢失的维度信息：模态间的连续置信度梯度；(2) 压缩比：N 个连续值映射为 3–4 个离散态；(3) 方向性：信息损失单指向（离散保留高置信端，低置信端合并）。P6 合规条件满足因离散标记仍保留多维表征可回溯性——原始置信度存储于记忆元数据，离散标记仅为索引。当架构层实现置信度→模态渐变转换时，撤销此例外标注。

> **VAD 一阶维度的 v0.1.0 受控简化声明**：认知基础（[cognitive-foundation.md](cognitive-foundation.md) §1.4 其他认知要素）将情感纹理 VAD 定位为度量空间一阶维度（应进入帕累托前沿计算）。当前架构实现中，VAD 通过情感提升通道（[architecture-v0.1.0.md](architecture-v0.1.0.md) §3.2）作为「可选注入」参与检索排序——仅在 VAD 匹配度超过阈值时生效，默认路径空间/向量检索忽略情感维度。此为 v0.1.0 的受控简化。**补偿措施**：为符合「独立维度而非可选插件」的定位，在检索排序中为 VAD 设置一个情感中性权重作为默认基线（权重系数可配置，建议 v0.1.0 默认 0.1），确保 VAD 始终作为帕累托前沿计算的一维输入（即使系数极低），而非在低匹配度时完全忽略。**能力缺口**：此降维使认知基础声明的「VAD 作为度量空间一阶维度全程参与帕累托前沿计算」在 v0.1.0 仅实现于高唤醒事件场景，低唤醒/低匹配度检索中 VAD 的排序影响被静默。影响范围限于检索排序阶段，不影响编码和巩固环节的 VAD 强制录入。当架构层评估 VAD 全时参与的效率可接受时，撤销此简化。

路径空间（kairos://）定位为使用价值轴的**检索级**和**验证级**的架构落点。它不承载见证价值轴——见证锚定独立于路径空间。

路径的层级结构映射到使用价值轴的间接度：
- `kairos://_user/{id}/core/` → 高激活权重路径（常驻投影）
- `kairos://_user/{id}/memories/` → 中等激活权重路径（按需投影）
- `kairos://_project/{id}/rules/` → 条件激活路径（环境投影）
- `kairos://_system/tmp/` → 低激活权重路径（临时投影）

### 5.7 预留——多 Agent 校准参数

> **占位声明**（v0.1.0 范围外）：本节定义多 Agent 校准参数的接口契约。当前版本仅声明三个必含维度（来源独立性、历史准确率、交叉印证度）和否决权归属（[architecture-v0.1.0.md](architecture-v0.1.0.md) §0.4 社会性校准占位段），具体实现推迟至 v1.1+。相关路径空间 `kairos://_social/` 已预留（见 [architecture-v0.1.0.md](architecture-v0.1.0.md) §0.4 接入层预留路径）。

| 维度 | 类型 | 说明 |
|:----|:----|:-----|
| 来源独立性 | 整数 [1,N] | 校准信号来自多少个独立 Agent（≥2 才激活加权） |
| 历史准确率 | FLOAT [0,1] | 各 Agent 的历史校准质量跟踪 |
| 交叉印证度 | FLOAT [0,1] | 多 Agent 对同一记忆的校准方向一致性 |

**否决权**：多 Agent 校准的激活开关归属宪法主权面（[architecture-v0.1.0.md](architecture-v0.1.0.md) §1 章宪法主权面），系统在激活前仅使用单 Agent 校准模型。激活前提条件（见 [architecture-v0.1.0.md](architecture-v0.1.0.md) §0.4 社会性校准占位段）全部满足后方可开启。此占位不约束具体存储结构或算法，仅声明上述接口契约。

> **参考注记（外部理念吸收 0.0.44；外部实证：PAPER-10 G-Memory，NeurIPS 2025）**：G-Memory 三层图记忆（交互/查询/洞察）+ Agent 特定记忆投影 + 洞察支撑集溯源，是多 Agent 团队记忆的候选形态样本——作为 v1.1 多 Agent 校准参数立项时的参考材料：① 洞察支撑集引用与本文「交叉印证度」维度的关系待立项时评估（支撑集溯源可作交叉印证的证据基座）；② 其任务后自动演化不吸收（Kairos 升华默认 OFF 立场不变，单 Agent 定位下无对应机制）。

### 5.8 升华管道 vs 认知层多维特征空间

| 认知层类型 | 升华阶段 | 产出 | 调度条件 |
|:----------|:---------|:-----|:---------|
| 检索级 | — | 原始路径索引 | — |
| 验证级 | Stage 1: raw→item | 结构化条目（gist+entities） | 推理间歇 |
| 贡献级 | Stage 2: item→strategy | 可复用策略 | 空闲（非交互） |

> **当前注册的事件处理**：使用事件提交、前瞻保持请求、模拟结果返回。

## 三、P3 前瞻组件（续，v1.1+ 目标）

#### P3-14 远程/本地双模式升华

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**认知层依据**：纯工程增强——此组件为工程优化手段，不涉及认知层承诺。未实现时升华管道全部本地执行（见下方 v0.1.0 占位）。

**定位**：将升华管道（§5.8）的执行从单一的本地执行模式扩展为远程/本地双模式——允许将计算密集的升华阶段（L2→L3 周度蒸馏、L3→L4 Profile 蒸馏）卸载到 LangGraph Cloud 远程执行，本地仅保留轻量的 L0→L1 和 L1→L2 阶段。此设计解决本地资源受限场景（如树莓派、低配 VPS）下升华管道与实时检索争抢 CPU/内存的问题。

**设计要点**：

```text
双模式升华架构：

  本地模式（v0.1.0 现有）         远程模式（P3-14 目标）
  ┌──────────────────┐         ┌──────────────────────────┐
  │  Kairos 本地进程  │         │  Kairos 本地进程          │
  │                  │         │  ┌──────────────────────┐│
  │  L0→L1 (本地)    │         │  │ L0→L1 (本地)         ││
  │  L1→L2 (本地)    │         │  │ L1→L2 (本地)         ││
  │  L2→L3 (本地)    │         │  │                      ││
  │  L3→L4 (本地)    │         │  │ LangGraph Client     ││
  │                  │         │  │  POST /runs          ││
  └──────────────────┘         │  └──────────┬───────────┘│
                               │             │            │
                               │  LangGraph Cloud        │
                               │  ┌──────────────────────┐│
                               │  │ L2→L3 周度蒸馏       ││
                               │  │ L3→L4 Profile 蒸馏   ││
                               │  │ 结果回传 → 本地合并  ││
                               │  └──────────────────────┘│
                               └──────────────────────────┘

模式切换：
  ┌──────────────┬────────────────────┬─────────────────────┐
  │ 条件          │ 本地模式            │ 远程模式             │
  ├──────────────┼────────────────────┼─────────────────────┤
  │ CPU 核心数    │ 任意               │ ≥ 1（仅需 L0-L2）   │
  │ 内存          │ ≥ 512MB            │ ≥ 256MB             │
  │ 网络          │ 不需要              │ 需要（上传记忆批次） │
  │ LangGraph Key │ 不需要              │ 需要                │
  │ 适用场景      │ 开发/单机部署       │ 边缘设备/低配 VPS    │
  └──────────────┴────────────────────┴─────────────────────┘
```

**远程升华协议**：

```text
1. 本地触发条件：升华调度器检测到 L2→L3 队列积压 > 阈值（默认 50 条待升华记忆）
2. 本地打包：将 L2 已完成的 item 记忆批量打包（JSONL 格式，含 embedding + entities）
3. 上传执行：通过 LangGraph Cloud API POST /runs 提交升华任务——
   payload = { graph_id: "kairos-sublimation", input: { batch: [...], stage: "L2_to_L3" } }
4. 远程执行：LangGraph Cloud 运行蒸馏 graph（LLM 摘要→聚合→模式识别）
5. 结果回传：LangGraph Cloud 完成后回调本地 webhook，携带升华结果包
6. 本地合并：结果包经 ADD-only 协议（[architecture-v0.1.0.md](architecture-v0.1.0.md) §7.3g）写入本地 LTM 和关系索引
7. 超时处理：远程执行超过配置超时（默认 30 分钟）→ 自动降级为本地执行
```

**数据安全**：远程传输的升华批次数据使用 AES-256-GCM 加密（密钥从本地 `KAIROS_SUBLIMATION_ENCRYPTION_KEY` 环境变量读取），LangGraph Cloud 侧不解密——仅在 LangGraph 运行时内存中解密处理，结果回传同样加密。确保远程执行不暴露原始记忆内容。

**工程权衡**：

- **收益**：边缘设备（2 核/1GB RAM）可将 L2→L4 的计算卸载到云端——本地仅运行检索和实时摄取，CPU 负载降低 60%+。远程升华在云端执行不受本地资源限制，可使用更强的 LLM 模型（Tier 4）做深度蒸馏。
- **风险**：网络中断时升华管道回退至本地模式（L2→L4 停止，仅 L0→L2 继续），中断期间记忆只能累积在加工区（[architecture-v0.1.0.md](architecture-v0.1.0.md) §5.10），待网络恢复后批量上传。数据加密密钥泄露会导致记忆暴露。
- **与 [architecture-v0.1.0.md](architecture-v0.1.0.md) §5.11 端云同步的区别**：端云同步是数据同步（SQLite↔PostgreSQL 双向同步），远程升华是计算卸载（本地数据→远程计算→结果回传）。两者互补——端云同步确保数据冗余，远程升华确保计算可伸缩。跨模式（轻量↔标准）数据同步与迁移须遵循 ADR-012 矩阵版本对齐约束（矩阵版本不一致时先对齐再比对余弦距离，见主架构 §5.11）。

**v0.1.0 占位**：v0.1.0 升华管道全部本地执行（[architecture-v0.1.0.md](architecture-v0.1.0.md) §10.7 设计约束：「升华仅本地执行」）。v1.1 引入远程/本地双模式——以 LangGraph Cloud 为首选远程后端，通过 `KAIROS_SUBLIMATION_MODE=remote` 配置项切换。首批支持 L2→L3 阶段远程执行，L3→L4 在远程 L2→L3 稳定后追加。

#### P3-15 Prompt 依赖关系图

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**认知层依据**：纯工程增强——此组件为工程优化手段，不涉及认知层承诺。未实现时 SOUL 变更后的 Skills 一致性通过手动审查解决（见下方 v0.1.0 占位）。

**定位**：在编译管线（[architecture-v0.1.0.md](architecture-v0.1.0.md) §4.3）中增加 Prompt 依赖关系图——记录 SOUL.md、Skills、Directives、Playbooks 之间的引用和依赖关系。当 SOUL.md 发生修改（如用户身份声明变更）时，自动检测依赖该 SOUL 条款的所有 Skills 和 Playbooks，触发「关联项需重新验证」通知——防止 SOUL 变更后的技能与新身份声明不一致。

**设计要点**：

```text
Prompt 依赖关系图结构：

  SOUL.md §2 "技术偏好"
  ├── 依赖项：无
  ├── 被依赖项：
  │   ├── Skill: "code-review-python"   (引用了「偏好 Rust 胜过 Python」)
  │   ├── Skill: "api-design-rest"      (引用了「先设计后编码」)
  │   ├── Playbook: "new-project-init"  (引用了「默认技术栈」)
  │   └── Directive: "DIR-007"          (引用了「沟通风格简洁」)
  │
  变更传播：
  SOUL.md §2 修改
    → 查询依赖图：哪些 Skills/Playbooks/Directives 引用了该条款？
    → 对每个依赖项：
        ├─ 标记 `needs_revalidation`（本文 §5.2 技能管理系统，v1.1 新增组件）
        ├─ 写入审计日志：`soul_dependency_changed`
        └─ 通过 Webhook（§P3-13）通知外部系统（如 Slack）
```

**依赖关系检测**：

依赖关系由编译管线在每次编译时自动检测——当 Skill 的 SOUL.md 引用语句（如 `根据 SOUL.md §2 的「偏好 Rust 胜过 Python」...`）被识别时，在 `prompt_dependencies` 表中创建一条引用边：

```text
prompt_dependencies 表：
  (id, source_type, source_id, source_section,
   target_type, target_id, target_section,
   detected_at, last_verified_at, is_active)

示例记录：
  source_type="skill", source_id="code-review-python", source_section="trigger",
  target_type="soul", target_id="v2.1", target_section="[architecture-v0.1.0.md](architecture-v0.1.0.md) §2",
  detected_at="2026-07-20", is_active=true
```

**变更触发动作**：

| SOUL 变更类型 | 触发动作 | 严重度 |
|:------------|:--------|:------|
| 技术偏好变更（如「偏好 Python」→「偏好 Rust」） | 所有引用该条款的 Skills 标记 `needs_revalidation`；Playbooks 降至 `needs_review` | 高 |
| 沟通风格变更（如「简洁」→「详细解释」） | 引用 Skills 降权（confidence × 0.8）；不阻塞使用 | 中 |
| 身份声明新增（如新角色添加） | 无自动动作——仅记录审计日志（新声明无历史依赖） | 低 |
| 身份声明删除 | 引用的 Skills 标记 `deprecated`（依据消失） | 高 |

**与编译管线的集成**：

编译管线（[architecture-v0.1.0.md](architecture-v0.1.0.md) §4.3）在第二阶段「分类渲染」时查询 `prompt_dependencies` 表——对每个即将注入的 Skill，检查其依赖的 SOUL 条款是否有未解决的 `needs_revalidation` 标记。如果有，编译管线可选择：(a) 降权注入（标注 `[待重新验证]` 前缀）；(b) 跳过注入（仅当置信度 < 0.5 时）。选择策略由 `KAIROS_PROMPT_DEPENDENCY_STRATEGY` 配置项控制。

**工程权衡**：

- **收益**：解决当前「改了 SOUL 但技能仍按旧偏好执行」的一致性问题——SOUL 是 Agent 的「人格声明」，Skills 是人格驱动的「行为模式」，两者必须保持一致。依赖关系图提供可审计的变更影响范围。
- **限制**：依赖检测依赖 LLM 在编译时识别引用语句——存在漏检风险（Skill 中隐式依赖了 SOUL 条款但未显式引用）。v0.1.0 以编译时的显式引用为唯一检测依据，隐式依赖不在检测范围内。
- **循环依赖防护**：依赖图为有向图——禁止 SOUL→Skill→SOUL 的循环引用。检测到循环时拒绝创建依赖边，写入告警日志。

**v0.1.0 占位**：v0.1.0 无依赖关系图——SOUL 变更后 Skills 仍按旧声明运作，一致性问题通过手动审查解决。v1.1 在编译管线稳定后引入——以编译时自动检测为基础，首批覆盖 Skills↔SOUL 的依赖关系，Playbooks↔SOUL 次之。

#### P3-16 GraphRAG 内建

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**认知层依据**：纯工程增强——此组件为工程优化手段，不涉及认知层承诺。未实现时检索仅依赖向量相似度 + 路径前缀匹配 + 三链路加权（见下方 v0.1.0 占位）。

**定位**：将 GraphRAG（Graph Retrieval-Augmented Generation）作为内建检索模式嵌入 Kairos——在现有向量检索（语义相似度）和路径检索（确定性前缀匹配）之外，增加基于知识图谱的图遍历检索。核心计算（图遍历、社区检测、实体解析）用 Rust 实现并通过 PyO3 绑定为 Python stub，确保图计算不影响主检索路径的延迟。

**设计要点**：

```text
GraphRAG 检索模式：

  查询: "项目 Alpha 用了哪些技术？谁在维护？"
    │
    ├─ 向量检索（现有）    → 语义相似的记忆（可能不精确）
    ├─ 路径检索（现有）    → kairos://_project/alpha/**（确定性子集）
    │
    └─ GraphRAG 检索（新增）→ 从实体知识图谱出发的图遍历：
         │
         1. 实体解析（Rust Core）
            查询 → GLiNER2 NER（§P3-08）→ 实体: ["Project:alpha"]
            │
         2. 子图提取（Rust Core）
            从实体节点出发，提取 k-hop 邻域子图（k 可配置，默认 2）
            节点类型：Entity, Memory, Playbook, Skill
            边类型：uses_technology, managed_by, authored_by, references
            │
         3. 社区检测（Rust Core — Louvain 算法）
            在子图上运行社区检测，识别紧密关联的实体群
            社区摘要（LLM 生成）作为检索结果的补充上下文
            │
         4. 路径排序（Python）
            子图中的多条路径按以下加权排序：
            - 路径长度（短优先）
            - 边置信度（高优先）
            - 实体中心性（PageRank 高分优先）
            │
         5. 结果融合
            GraphRAG 结果与向量/路径结果在三链路融合框架（[architecture-v0.1.0.md](architecture-v0.1.0.md) §5 三链路融合）
            中按权重合并：语义 0.40 + 路径 0.25 + 实体共现 0.15 + GraphRAG 子图 0.20
            **权重口径注记**：此为 GraphRAG 场景的 v1.1 独立配比（语义 0.40/路径 0.25/实体共现 0.15/GraphRAG 子图 0.20），
            与主架构四链路唯一默认（语义/共现/kNN/因果 0.50/0.20/0.10/0.20）不同——GraphRAG 场景下 kNN/因果链路由子图权重替代。
```

**Rust Core 架构**：

```text
kairos-graph-core (Rust crate)
  ├─ Cargo.toml          (依赖: petgraph, pyo3, serde)
  ├─ src/
  │   ├─ lib.rs           (PyO3 模块入口)
  │   ├─ graph.rs          (图数据结构——基于 petgraph::StableGraph)
  │   ├─ traversal.rs      (BFS/DFS k-hop 子图提取)
  │   ├─ community.rs      (Louvain 社区检测)
  │   ├─ ranking.rs        (PageRank + 路径排序)
  │   └─ ffi.rs            (Python 绑定——通过 PyO3 导出)
  │
  └─ python/
      ├─ __init__.py       (Python stub: from kairos_graph_core import ...)
      └─ _core.pyi         (类型存根)

Python 调用示例：
  from kairos_graph_core import EntityGraph, extract_subgraph, detect_communities

  graph = EntityGraph.load_from_db(entity_edges)
  subgraph = extract_subgraph(graph, start_node="entity:project-alpha", hops=2)
  communities = detect_communities(subgraph)
  ranked_paths = rank_paths(subgraph, start_node, target_nodes)
```

**为什么用 Rust**：

| 考虑 | Rust | Python（纯） |
|:-----|:-----|:-----------|
| 图遍历性能 | O(V+E) 原生——100K 节点 BFS < 5ms | NetworkX 同等规模 ~50ms |
| 社区检测 | Louvain 迭代——50K 边 <50ms | python-louvain ~200ms |
| 内存占用 | 图结构紧凑——无 GC 开销 | NetworkX 图对象内存 2-3× |
| GIL 释放 | PyO3 自动释放 GIL——图计算不阻塞检索 | 图计算占用 GIL |
| 部署 | 编译为 .so/.dll，pip install 自动安装 | 仅需 Python 依赖 |

**离线 ETL + 在线查询分离**：图结构拓扑的离线 ETL + 在线查询分离

```text
离线 ETL（Deep 模式维护任务，日频）：
  ┌──────────────────────────────────────┐
  │ 实体知识图谱（PostgreSQL/SQLite）     │
  │   ↓ 导出边列表                       │
  │ Rust Core ETL                         │
  │   ├─ 全量图构建（所有 node/edge）     │
  │   ├─ 社区检测（Louvain）              │
  │   ├─ PageRank 计算（每节点）          │
  │   └─ 社区摘要生成（LLM Tier 3）       │
  │   ↓ 写回                             │
  │ graph_communities 表                  │
  │ graph_pagerank 表                     │
  │ community_summaries 表                │
  └──────────────────────────────────────┘

在线查询（实时检索路径）：
  查询 → 实体解析 → 读 graph_communities/pagerank（预计算）→ 子图遍历 → 排序 → 返回
  （无 LLM 调用——全部基于预计算数据 + Rust 图遍历）
```

**工程权衡**：

- **收益**：GraphRAG 解决了纯向量检索的「语义相关但实体无关」的误匹配问题——如查询「项目 Alpha 使用的数据库」时，向量检索可能返回「数据库设计最佳实践」类的通用文章，而 GraphRAG 精确返回 `Project:alpha --[uses_technology]--> PostgreSQL` 的关联记忆和社区上下文。
- **风险**：Rust Core 引入额外的编译依赖（cargo + PyO3 构建工具链）——v0.1.0 的纯 Python 部署转变为 Python + Rust 混合部署。提供预编译 wheel（manylinux/win/arm64）解决此问题。
- **离线 ETL 的延迟**：社区检测和 PageRank 是离线计算（日频），新实体写入后需等到下一 ETL 周期才能在 GraphRAG 检索中生效——对实时性要求高的场景不适用。缓解措施：新实体立即在向量检索和路径检索中可用——GraphRAG 仅作为第三检索模式补充，非替代。

**v0.1.0 占位**：v0.1.0 无 GraphRAG 检索模式——检索仅依赖向量相似度 + 路径前缀匹配 + 三链路加权（实体共现/kNN/因果）。v1.1 引入 Rust Core + GraphRAG 检索——以离线 ETL 模式运行（不侵入实时检索路径），GraphRAG 结果作为第三检索通道参与结果融合。Rust Core 编译为独立 Python 包（`kairos-graph-core`），通过 `pip install` 分发预编译 wheel。

#### P3-11 Directives 轻量级规则注入系统

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**定位**：在 Reflect Agentic Loop（§6 WM 层）执行前注入一组轻量级、声明式行为指令（Directives），替代在 SOUL.md 中混入操作约束的粗粒度方式。Directives 是独立于 SOUL.md 的可版本化规则集合，每条 Directive 携带 compliance 追踪标记——系统在执行 Reflect 后检查每条 Directive 是否被遵守，输出合规报告。

**设计要点**：

```text
Directives 注入管线：
  SOUL.md（身份/偏好）──┐
  Skills（能力声明）    ├─→ 编译管线（§4.3）→ 系统提示词
  Directives（行为约束）─┘

  与 SOUL.md 的区别：
  ┌──────────────┬─────────────────────┬─────────────────────┐
  │ 维度          │ SOUL.md             │ Directives           │
  ├──────────────┼─────────────────────┼─────────────────────┤
  │ 内容          │ 身份/偏好/世界观    │ 操作约束/禁止行为    │
  │ 更新频率      │ 低（周级蒸馏）      │ 中（事件驱动）       │
  │ 注入时机      │ 每轮对话前          │ Reflect loop 执行前  │
  │ 合规检查      │ 无                  │ 有（compliance 追踪） │
  │ 格式          │ 自然语言 Markdown   │ 结构化 YAML          │
  └──────────────┴─────────────────────┴─────────────────────┘
```

**Directive 结构**：

```yaml
# directives/safety.yaml
directives:
  - id: "DIR-001"
    category: "safety"
    severity: "hard"                    # hard: 违反则阻断；soft: 违反则告警
    rule: "禁止修改或删除任何 is_identity=true 的记忆"
    scope: "reflect_write_operations"
    compliance_check: "post_reflect"    # 在 Reflect 执行后检查
    created_from: "宪法级约束 §1.5 S-10"

  - id: "DIR-002"
    category: "privacy"
    severity: "hard"
    rule: "禁止在检索结果中返回 PII（邮箱/电话/身份证号），即使命中"
    scope: "retrieval_output"
    compliance_check: "pre_response"

  - id: "DIR-003"
    category: "quality"
    severity: "soft"
    rule: "每次 Reflect 循环不得超过 5 轮工具调用"
    scope: "reflect_loop_budget"
    compliance_check: "mid_reflect"
```

**Compliance 追踪机制**：

每条 Directive 携带以下追踪元数据：
- `compliance_status`：`compliant` / `violated` / `not_applicable` / `unchecked`——每次 Reflect 后更新
- `violation_count`：累计违规次数——用于触发升级动作
- `last_checked_at`：最近一次合规检查时间戳
- `violation_response`：违规时的响应策略——(a) `block`：阻断本次 Reflect 产出（hard severity 默认）；(b) `warn`：写入审计日志但放行（soft severity 默认）；(c) `escalate`：违规次数超阈值后升级至宪法解释层

合规检查在 Reflect agentic loop 的 `done` 工具调用前执行——对 Reflect loop 的所有工具调用记录（search_memories/search_mental_models/search_sessions/search_temporal_patterns）做后置审计，检测是否有任何操作违反了 Directives 声明的禁止行为。违规时根据 severity 执行对应响应策略。

**动态加载**：Directives 支持热加载——通过 `POST /v1/directives/reload` 重新扫描 directives/ 目录，新 Directive 在下一轮 Reflect 前生效。无需重启系统。Directives 目录结构与 Hermes skills 目录类似——每个 `directives/{category}.yaml` 文件包含一个类别的所有指令。

**工程权衡**：

- **收益**：将操作约束从 SOUL.md 中解耦——SOUL.md 回归「我是谁/我偏好什么」的身份声明，Directives 独立承载「我不能做什么」的操作边界。两者独立维护、独立版本化——SOUL.md 修改不影响 Directives，Directives 更新不触发 SOUL 重编译。
- **限制**：合规检查是 post-hoc（事后）而非 preventive（预防性）——Directives 在 Reflect 执行后检查，不阻止违规操作的发生（仅阻止违规产出的提交）。完全的预防性检查需要侵入 Reflect loop 的工具调用中间层（v1.2 目标）。
- **与宪法主权面的关系**：Directives 是宪法级约束（§1.5）的操作层面具体化——不替代宪法解释层，而是在日常操作中提供低延迟的规则执行。当 Directive 的合规检查与宪法解释层判例冲突时，宪法解释层裁定为准。

**v0.1.0 占位**：v0.1.0 无 Directives 系统——操作约束通过 SOUL.md 的自然语言段落承载，无结构化合规检查。v1.1 在 Reflect agentic loop 稳定运行后引入 Directives——首批加载 3 个核心 Directive（身份保护/隐私过滤/循环预算），逐步扩展至完整规则集。

#### P3-12 malloc_trim 内存管理

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**定位**：在 Python 进程中通过周期性调用 `ctypes.CDLL("libc.so.6").malloc_trim(0)` 主动释放 glibc 堆中已 free 但未归还操作系统的内存页——解决 Python 内存分配器（pymalloc）与 glibc 之间的内存碎片化导致的 RSS（Resident Set Size）持续增长问题（即「内存不归还操作系统」）。

**设计要点**：

```text
malloc_trim 调度策略：

  触发条件（满足任一）：
    ├─ 条件 A：RSS 超过基线 1.5× 且持续 > 5 分钟
    │   （基线 = 进程启动后前 10 分钟的平均 RSS）
    ├─ 条件 B：空闲周期——系统进入空闲状态（无活跃请求 > 30s）
    │   + 上次 trim 距今 > 10 分钟
    └─ 条件 C：RSS 增长速率 > 50MB/小时（快速泄漏检测）

  执行流程：
    1. 触发条件满足 → 暂停新内存分配请求（短暂锁，<1ms）
    2. 调用 gc.collect() 强制 Python GC（释放 pymalloc arena）
    3. 调用 malloc_trim(0) 释放 glibc heap 给操作系统
    4. 记录 trim 前后 RSS（通过 /proc/self/status 读取 VmRSS）
    5. 写入审计日志：trim 时间、释放字节数、触发条件

  安全边界：
    ├─ 最小 trim 间隔：60 秒（防止高频 trim 影响性能）
    ├─ 不在活跃请求处理期间 trim（条件 B 的空闲判断）
    └─ trim 超时：5 秒（超时则放弃本次 trim，记录超时告警）
```

**关键指标监测**：

| 指标 | 采集方式 | 告警阈值 | 说明 |
|:-----|:--------|:--------|:-----|
| RSS 基线 | 启动后 10min 均值 | — | 作为比较基准 |
| RSS 增长率 | 每 60s 采样 | > 50MB/h | 触发条件 C |
| trim 有效率 | trim 后 RSS 变化 / trim 前 RSS | < 5% 连续 3 次 | trim 无效告警——可能存在真正的内存泄漏 |
| glibc arena 数量 | `mallinfo2().hblkhd` | > 8 个 arena | 表示严重碎片化 |

**为什么需要 malloc_trim**：

- Python 的 pymalloc 在释放内存时仅归还给 pymalloc arena（不会归还给 glibc），glibc 的 `free()` 也仅标记页为可复用但不一定 `munmap` 归还操作系统。
- 在长期运行的服务中（Kairos 设计目标为 7×24），碎片化累积导致 RSS 远超实际使用量——典型场景：处理大文件摄取后 RSS 从 200MB 跳到 800MB，处理完成后停留在 600MB（实际只需 250MB）。
- `malloc_trim` 是 glibc 提供的非标准但广泛支持的接口——触发 glibc 扫描堆并释放可归还的连续空闲页给 OS kernel。

**与 §10.9 降级模式的集成**：当系统进入受限交叉验证模式或安全休眠模式时，自动触发一次 malloc_trim（无论条件是否满足），作为内存清理的防御措施。trim 结果写入降级模式切换日志中。

**v0.1.0 占位**：v0.1.0 不做 RSS 主动管理——依赖 Python GC 和操作系统 OOM Killer。v1.1 引入以条件 A（RSS 超基线）为主的定期 trim 调度——以 RSS 增长曲线作为验证手段（连续运行 7 天后 RSS 应稳定在基线 1.2× 以内）。

#### P3-13 Webhook 事件通知框架

**优先级**：P3（前瞻探索，v1.1+ 目标，v0.1.0 不交付）

**定位**：在现有 Connectors 同步模式（详细设计 §11.2——外部平台事件→Kairos 记忆的单向同步）之外，增加 Kairos→外部系统的反向事件通知能力。通过订阅/投递/重试三表架构，让外部系统可以订阅 Kairos 内部事件（如记忆写入、升华完成、矛盾检测），在事件发生时通过 Webhook 主动推送通知。

**与详细设计 §11.2 Connectors 的关系**：Connectors 解决「外部→Kairos」的同步（外部内容变更同步进 Kairos），本框架解决「Kairos→外部」的通知（Kairos 内部事件推送到外部系统）。两者互补——构成完整的双向事件集成。

**三表架构**：

```text
┌─────────────────────────────────────────────────────────┐
│                  Webhook 事件通知框架                      │
│                                                          │
│  subscriptions 表          deliveries 表                 │
│  ┌──────────────────┐     ┌──────────────────────┐      │
│  │ id               │     │ id                   │      │
│  │ subscriber_name  │     │ subscription_id ───┐  │      │
│  │ callback_url     │     │ event_id           │  │      │
│  │ event_types[]    │     │ delivery_status    │  │      │
│  │ filter_rules     │     │ attempt_count      │  │      │
│  │ secret (HMAC)    │     │ last_attempt_at    │  │      │
│  │ status           │     │ next_attempt_at    │  │      │
│  │ created_at       │     │ response_code      │  │      │
│  └──────────────────┘     │ response_body      │  │      │
│           │               │ created_at          │  │      │
│           │ 1:N           └──────────────────────┘      │
│           │                                              │
│  retry_policies 表                                       │
│  ┌──────────────────────┐                               │
│  │ subscription_id      │                               │
│  │ max_attempts         │  (默认 5)                      │
│  │ backoff_strategy     │  (fixed/exponential/linear)    │
│  │ initial_delay_ms     │  (默认 1000)                   │
│  │ max_delay_ms         │  (默认 60000)                  │
│  │ timeout_ms           │  (默认 10000)                  │
│  └──────────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

**订阅管理 API**：

```text
POST /v1/webhooks/subscriptions
{
  "subscriber_name": "slack-notifier",
  "callback_url": "https://hooks.slack.com/services/T.../B.../xxx",
  "event_types": ["contradiction_detected", "sublimation_completed", "memory_created"],
  "filter_rules": {
    "memory_created": { "min_confidence": 0.7 },
    "contradiction_detected": { "min_severity": "high" }
  },
  "secret": "whsec_xxx",  // HMAC-SHA256 签名密钥
  "retry_policy": {
    "max_attempts": 5,
    "backoff_strategy": "exponential"
  }
}
```

**支持的事件类型**（首批）**：

| 事件类型 | 触发时机 | 载荷 | 优先级 |
|:--------|:--------|:-----|:------|
| `memory_created` | 新记忆写入 LTM | memory_id, path, summary, entities | 低 |
| `contradiction_detected` | 矛盾检测 Flag 挂载（§5 三链路知识图谱 Flag-2） | memory_ids[], claim_pair, polarity | 高 |
| `sublimation_completed` | 升华管道某一阶段完成 | stage, memory_count, new_playbooks[] | 中 |
| `degradation_mode_changed` | 降级模式状态切换（§10.9） | from_mode, to_mode, trigger_reason | 最高 |
| `identity_demotion` | is_identity 降级（§5.2 身份注册表） | memory_id, reason, narrative_coherence_trend | 高 |
| `calibration_gap_detected` | 外部校准中断检测 | gap_duration, last_calibration_at | 最高 |

**投递保证**：

- **至少一次（at-least-once）**：投递失败时按 retry_policy 重试——指数退避（1s→2s→4s→8s→16s），最多 max_attempts 次
- **幂等保护**：每次投递携带 `X-Kairos-Delivery-Id` 头——订阅方据此去重
- **签名验证**：投递方使用 HMAC-SHA256 对载荷签名，写入 `X-Kairos-Signature` 头——订阅方可用 secret 验证投递真实性
- **失败处理**：连续 max_attempts 次投递失败后，subscription 标记为 `degraded`——写入审计日志并通知管理员。degraded 订阅保留 7 天后如仍未恢复则自动暂停（`paused`）

**与系统事件总线的集成**：

Webhook 框架通过监听系统事件总线（§10.10）的特定事件类型来触发投递——不是独立的事件源，而是事件总线的消费者+转发器。事件总线发出 `contradiction_detected` 事件后，Webhook 框架查询 subscriptions 表中订阅了该事件类型的所有活跃订阅方，逐条创建 delivery 记录并执行 HTTP POST 投递。

**v0.1.0 占位**：v0.1.0 无事件通知框架——Kairos 内部事件仅写入系统事件总线和审计日志，外部系统无法订阅。v1.1 在系统事件总线稳定运行（事件丢失率 < 0.1%）后引入——首批支持 3 个事件类型（contradiction_detected / degradation_mode_changed / calibration_gap_detected）和单订阅方（如 Slack 通知通道）。

#### P3-17 TeamScope 多租户隔离

**优先级**：P3（前瞻探索，v1.2+ 目标，v0.1.0 不交付）

**定位**：将 Kairos 从当前的单租户部署模型（§10.7 设计约束：「单部署=单用户」）扩展为支持多租户的 TeamScope 隔离架构——通过 `team_id + user_id` 双层命名空间实现团队内共享与用户间隔离，支持跨 host 的团队记忆共享（多个 Kairos 实例共享同一团队的实体知识图谱和关系索引）。

**设计要点**：

```text
TeamScope 双层命名空间：

  kairos://{team_id}/{user_id}/{path}
  ─────────┬─────────┬─────────────
           │         └─ 用户私有空间（与 v0.1.0 路径空间兼容）
           └─ 团队共享空间

  路径空间隔离：
  ┌──────────────────────────────────────────────┐
  │ team: "acme-corp"                            │
  │  ├─ user: "alice"                            │
  │  │   ├─ core/          (私有——仅 alice 可见) │
  │  │   ├─ projects/      (私有)                │
  │  │   └─ shared/team    (团队——所有人可见)    │
  │  │                                            │
  │  ├─ user: "bob"                              │
  │  │   ├─ core/          (私有——仅 bob 可见)   │
  │  │   ├─ projects/      (私有)                │
  │  │   └─ shared/team    (团队——所有人可见)    │
  │  │                                            │
  │  └─ team: (虚拟用户)                         │
  │      └─ knowledge/     (团队知识库——只读)    │
  │      └─ playbooks/     (共享 Playbooks)       │
  └──────────────────────────────────────────────┘

数据隔离层级：

  团队级（team_id 隔离）：
    ├─ 实体知识图谱（entities 表增加 team_id 列）
    ├─ 关系索引（memory_relations 表增加 team_id 列）
    ├─ Playbooks（procedural_playbooks——team 级共享）
    └─ Skills（skills——team 级共享）

  用户级（user_id 隔离）：
    ├─ 原始记忆（memories——user_id 隔离，默认）
    ├─ 使用权重（影子副本——user_id 隔离）
    ├─ Profile Schema（每个用户独立的 Profile）
    └─ 会话记录（每个用户独立的 session 历史）

  全局级（跨 team）：
    └─ 注意力调度器（全局资源——非按租户分配）
    └─ 系统事件总线（全局——但事件 payload 标记 team_id/user_id）
```

**跨 host 共享架构**：

当多个 Kairos 实例（如 Alice 的笔记本、Bob 的台式机）需要共享同一团队的记忆时，TeamScope 通过以下协议实现跨 host 共享：

```text
跨 host 共享协议：

  实例 A（Alice 的笔记本）             实例 B（Bob 的台式机）
  ┌─────────────────────┐            ┌─────────────────────┐
  │ team_id: "acme"     │            │ team_id: "acme"     │
  │ user_id: "alice"    │            │ user_id: "bob"      │
  │                     │            │                     │
  │ 私有记忆 (alice/*)  │            │ 私有记忆 (bob/*)    │
  │ 团队知识图谱 (同步) │◄══════════►│ 团队知识图谱 (同步) │
  │ 团队 Playbooks (同步)│            │ 团队 Playbooks (同步)│
  │                     │            │                     │
  └─────────────────────┘            └─────────────────────┘
            │                                  │
            └────────────┬─────────────────────┘
                         │
               TeamScope Hub（PostgreSQL）
               ┌─────────────────────┐
               │ team_entities        │  ← 团队级实体知识图谱
               │ team_relations       │  ← 团队级关系索引
               │ team_playbooks       │  ← 共享 Playbooks
               │ team_skills          │  ← 共享 Skills
               │ sync_log             │  ← 同步日志（CRDT 冲突解决）
               └─────────────────────┘

  同步协议：
    ├─ 用户私有记忆：不跨 host 同步（留在本地 SQLite）
    ├─ 团队实体/关系：通过端云同步协议（§5.11）增量同步
    └─ 冲突解决：以 TeamScope Hub 为最终一致性仲裁方
                 （同 §5.11 的同步冲突策略——以服务端为准）
```

**权限模型**：

| 操作 | 团队管理员 | 团队成员 | 外部用户 |
|:-----|:---------|:--------|:--------|
| 读取团队知识图谱 | ✅ | ✅ | ❌ |
| 写入团队知识图谱 | ✅ | ✅（需 `can_contribute` 权限） | ❌ |
| 读取团队 Playbooks | ✅ | ✅ | ❌ |
| 修改团队 Playbooks | ✅ | ❌（需审批） | ❌ |
| 邀请成员 | ✅ | ❌ | — |
| 查看成员列表 | ✅ | ✅（仅名称/角色） | ❌ |
| 删除团队数据 | ✅（需二次确认） | ❌ | ❌ |
| 导出团队数据 | ✅ | ✅（仅自己可见的数据） | ❌ |

**与 §10.7 单租户约束的关系**：v0.1.0 的「单租户部署」约束在 TeamScope 中被解除——`team_id` 和 `user_id` 不是通过部署实例隔离，而是通过路径前缀和数据库行级安全策略（Row-Level Security）实现逻辑隔离。同一部署实例可服务多个团队和用户——查询时由 `WHERE team_id = $current_team AND (user_id = $current_user OR visibility = 'team')` 自动过滤。

**数据迁移路径**（单租户 → 多租户）：

```text
v0.1.0 单租户数据 → v1.2 TeamScope 迁移：

  1. 现有单租户数据默认分配 team_id = "default"、user_id = "default"
     （保持向后兼容——v0.1.0 路径 kairos://_user/default/... 不变）

  2. 用户创建首个 team 时：
     ├─ 创建 team_id = "my-team"
     ├─ 将现有 team 级数据（实体知识图谱、关系索引中标记为 shared 的边）
     │   迁移至 TeamScope Hub
     └─ 私有记忆保留在本地 user_id 空间下

  3. 新成员加入 team 时：
     ├─ 分配 user_id
     ├─ 从 TeamScope Hub 拉取团队知识图谱（全量同步）
     └─ 开始本地积累私有记忆
```

**工程权衡**：

- **收益**：解除单租户限制使 Kairos 可用于团队协作场景——团队共享知识图谱（如项目实体关系、技术决策因果链），个人保留私有记忆（如个人偏好、未共享的笔记）。跨 host 共享支持多设备/多成员场景。
- **风险**：多租户引入行级安全复杂度——SQL 注入或 RLS 配置错误可能导致跨租户数据泄露。需要独立的安全审计（§8 安全红线扩展多租户隔离检查）。团队管理员拥有删除数据的能力——误操作可造成团队知识丢失。
- **性能影响**：查询时增加 `team_id` 和 `user_id` 的 WHERE 条件——需在相关表上建立复合索引 `(team_id, user_id, created_at)` 以避免全表扫描。团队知识图谱的跨 host 同步增加网络开销（增量同步的传输量取决于团队实体变更频率）。

**v0.1.0 占位**：v0.1.0 严格单租户——一个 Kairos 实例服务一个用户，路径中的 `{id}` 仅为该用户内部组织（§10.7 设计约束）。v1.2 在端云同步协议（§5.11）和 DFA（§5.12）稳定运行后引入 TeamScope——以向后兼容的迁移路径启动（默认 team_id="default"），通过 `KAIROS_TEAMSCOPE_ENABLED=true` 激活多租户模式。

#### P3-19 File Graph 深层能力

**优先级**：P3（前瞻探索，v1.1 目标，v0.1.0 不交付）

**定位**：File Graph 是 Kairos 路径空间的图论增强层——将 `kairos://` 路径树从纯层级索引升级为带权有向图，支持深层图分析能力。P3-18 为预留编号（见 [feature-list.md](../specification/feature-list.md) 未使用编号登记，不得回收复用）。

**机制规格**（承接自 [technology-stack.md](../development/technology-stack.md) §七，与三语言 SDK 战略协同；v0.1.0 以邻接表单跳查询 + 递归查询实现受限版本，见主架构 §0.4 多跳遍历声明）：

- **反向链接追踪**（Reverse Link Tracking）：给定一条记忆 M，查询所有引用 M 的记忆（`WHERE target_id = M` 沿 `memory_relations` 表）。支持深度限制（默认 3 跳），用于追溯「哪些决策依赖此记忆」
- **多跳图遍历**（Multi-Hop Graph Traversal）：从给定记忆出发，沿关系边（causal/derived_from/hierarchical/part_whole）做 BFS 遍历。使用 PostgreSQL 递归 CTE（`WITH RECURSIVE`），最大深度可配置。检索时自动扩展候选集——被遍历到的记忆以加权系数 0.10 参与排序
- **孤立检测**（Orphan Detection）：后台维护引擎 Deep 模式扫描 `memories` 表中无任何关系边（既非 source 也非 target）的记忆，标记为 `orphan_suspect`。孤立记忆在检索排序中降权（×0.5），并写入使用事件总线供元认知层评估——高频孤立率是记忆结构退化的预警信号
- **中心性计算**（Centrality Computation）：对实体知识图谱（主架构 §5.2 实体知识图谱）中的实体节点计算度中心性（Degree Centrality）和介数中心性（Betweenness Centrality）。高中心性实体（度 > 阈值或介数 > 阈值）在检索时获得实体加成倍率提升（`entity_boost × centrality_factor`，上限 2.0）。中心性由 Deep 模式维护任务周期性重算（日频），不参与实时检索热路径

**对外暴露**：以上能力通过三语言 SDK 的统一 `kairos_graph_*` 系列方法对外暴露（`kairos_graph_reverse_links` / `kairos_graph_traverse` / `kairos_graph_find_orphans` / `kairos_graph_centrality`），各语言 SDK 提供等价的类型安全接口。

**与 v0.1.0 的关系**：v0.1.0 路径空间保持纯层级索引；多跳遍历（BFS 深度 ≤3）以递归查询实现但性能不受保证（主架构 §0.4 多跳遍历声明）。File Graph 在 v1.1 将多跳升级为独立一等检索模式（图遍历引擎）。

#### P3-20 SQLCipher 静态加密

在轻量模式（SQLite 后端）下，数据库文件以明文存储于磁盘——任何有文件系统访问权限的攻击者可读取全部记忆内容。SQLCipher 提供透明的全数据库 AES-256-CBC 加密，确保 at-rest 数据安全。

**设计决策**：

- **加密粒度**：全数据库加密（page-level encryption），而非列级加密——原因：(a) 全文索引（FTS5）和向量索引的页级数据无法做列级加密；(b) page-level 加密对应用层透明，无需修改 SQL 语句
- **密钥管理**：加密密钥通过 `KAIROS_SQLCIPHER_KEY` 环境变量注入，不存储在代码或配置文件中。系统启动时从环境变量读取，内存中驻留，不写入磁盘
- **密钥派生**：使用 PBKDF2-HMAC-SHA512（迭代次数 256,000）从原始密钥派生 page-level 加密密钥，防止彩虹表攻击
- **性能影响**：SQLCipher 的 page-level AES-256 开销约为 5-10% 的读写性能损失（基于 SQLCipher 官方基准），在可接受范围内。通过 `PRAGMA cipher_page_size = 4096` 和 `PRAGMA kdf_iter = 256000` 调整安全/性能平衡
- **与 S-07 的关系**：S-07（敏感信息 AES-256-GCM 加密存储）是应用层的列级加密——SQLCipher 的 page-level 加密是 S-07 的底层补充，两者不互斥：(a) SQLCipher 加密所有数据页（防止文件系统级泄露）；(b) S-07 加密 `is_sensitive=true` 记忆的 `content` 字段（防止应用层 SQL 注入或权限提升攻击读取明文内容）
- **标准模式（PostgreSQL）等效**：PostgreSQL 通过文件系统级加密（LUKS/dm-crypt）或云提供商托管密钥实现等效的 at-rest 加密，不在此组件范围内

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_SQLCIPHER_ENABLED` | `false` | SQLCipher 加密总开关（轻量模式建议开启） |
| `KAIROS_SQLCIPHER_KEY` | —（必填，启用时） | 加密密钥（通过环境变量注入） |
| `KAIROS_SQLCIPHER_PAGE_SIZE` | `4096` | 加密页大小（字节） |
| `KAIROS_SQLCIPHER_KDF_ITER` | `256000` | PBKDF2 迭代次数 |

#### P3-21 FTS5 全文搜索——contentless-external 模式

Kairos 的 BM25 全文检索（§7.3a 自适应 BM25）和 Playbook 全文索引（§5.2 procedural_playbooks_fts）基于 SQLite FTS5 引擎。使用 contentless-external 模式优化存储和索引效率。

**contentless-external 模式设计**：

- **contentless 表**：FTS5 索引表仅存储 tokenized 词项和位置信息（倒排索引），不存储原始文本。原始文本存储在外部内容表（`memories.content`、`procedural_playbooks` 等），通过 `rowid` 关联
- **优势**：(a) 避免内容重复存储（FTS5 索引体积约为 content 模式的 30-40%）；(b) 原始内容加密（S-07 + SQLCipher）不受 FTS5 索引明文影响——攻击者即使读取 FTS5 索引页也只能看到 token 位置而无法还原原文；(c) 内容更新时仅更新外部表，FTS5 索引无需重建
- **分词器**：使用 `unicode61` tokenizer（内置）+ 自定义中文分词插件（jieba 集成）。中文分词通过 `jieba.cut()` 输出 token 流，插入 FTS5 索引
- **查询语法**：支持 FTS5 标准查询语法——布尔操作符（`AND`/`OR`/`NOT`）、前缀查询（`term*`）、短语查询（`"exact phrase"`）、列过滤（`title:keyword`）
- **索引维护**：内容写入时同步更新 FTS5 索引（同一事务内）。后台维护引擎 Light 模式定期执行 `INSERT INTO fts_table(fts_table) VALUES('optimize')` 优化索引碎片

**FTS5 索引表结构**（见 [data-model.md](../specification/data-model.md) 对应表定义）：

- `memories_fts`：记忆内容全文索引（contentless-external，关联 `memories.rowid`）
- `procedural_playbooks_fts`：Playbook 全文索引（已有，§5.2）
- `skills_fts`：技能名称/描述全文索引

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_FTS5_ENABLED` | `true` | FTS5 全文搜索总开关 |
| `KAIROS_FTS5_TOKENIZER` | `unicode61` | 分词器（`unicode61` / `porter` / `trigram`） |
| `KAIROS_FTS5_CHINESE_SEGMENTATION` | `true` | 中文分词增强（jieba 集成） |
| `KAIROS_FTS5_OPTIMIZE_INTERVAL` | `3600` | 索引优化间隔（秒） |

#### P3-22 PreparedStatementCache——96 条 LRU 缓存管理

数据库连接的 prepared statement 编译有固定开销（SQL 解析、查询规划）。对于 Kairos 的高频查询模式（检索、权重更新、状态查询），重复编译相同 SQL 显著增加延迟。

**设计**：

- **缓存容量**：96 条 prepared statement，使用 LRU 逐出策略。96 条是基于 Kairos 核心 SQL 查询数（~80 条不同查询模式）+ 20% 余量的估算
- **缓存键**：`SHA256(normalized_sql)` ——对 SQL 文本做空白归一化后哈希，确保语义相同但格式不同的 SQL 共享同一条目
- **线程安全**：读写锁保护缓存访问——读（查找已缓存的 statement）使用共享锁，写（插入新 statement 或 LRU 逐出）使用排他锁。对于 SQLite（单写者），写锁竞争不影响并发读取
- **逐出策略**：LRU（Least Recently Used）——当缓存满 96 条时，逐出最久未使用的 statement。逐出前调用 `sqlite3_finalize()` 释放 SQLite 资源
- **生命周期**：PreparedStatementCache 与数据库连接生命周期绑定——连接关闭时清空缓存。连接池中的每个连接维护独立的 statement 缓存
- **命中率监测**：元认知层每 5 分钟采集缓存命中率（`hits / (hits + misses)`），写入 `stmt_cache_metrics` 日志。命中率低于 80% 时触发告警——可能指示 SQL 查询模式发生了结构性变化或缓存容量不足

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_STMT_CACHE_SIZE` | `96` | 缓存容量（条） |
| `KAIROS_STMT_CACHE_ENABLED` | `true` | 缓存总开关 |
| `KAIROS_STMT_CACHE_HIT_RATE_ALERT` | `0.80` | 命中率告警阈值 |

#### P3-23 Schema 前向版本保护

当 Kairos 版本升级引入新的 Schema 迁移后，数据库文件被更新到新的 schema 版本。如果用户尝试用旧版 Kairos 二进制打开新版数据库，可能导致数据损坏（旧代码不理解新列/新表）或静默错误（新字段被忽略但不报错）。

**保护机制**：

- **Schema 版本号**：`memories` 数据库的 `schema_version` 表中记录当前 schema 版本号（整数，单调递增）。每次迁移脚本执行后递增
- **启动时校验**：Kairos 启动时读取数据库的 `schema_version`，与编译进二进制的 `KAIROS_SCHEMA_VERSION` 比较：
  - `db_version == binary_version`：正常启动
  - `db_version < binary_version`：触发自动迁移（运行迁移脚本）
  - `db_version > binary_version`：**硬拒绝启动**——记录告警日志 `schema_version_mismatch: db=X binary=Y`，进程退出码 `EXIT_SCHEMA_VERSION`（退出码 75）
- **拒绝原因**：高版本数据库可能包含当前二进制不理解的列/表/索引——允许启动会导致：(a) 写入时丢失新字段；(b) 查询时语法错误（引用不存在的列）；(c) 迁移脚本不可逆（无法通过旧迁移脚本回退 schema）
- **用户恢复路径**：(a) 升级 Kairos 二进制至匹配数据库 schema 版本；(b) 使用 `kairos db export` 从高版本数据库导出数据（JSON 格式），再用 `kairos db import` 导入低版本数据库（需低版本 schema 兼容的导出格式）
- **前向兼容策略**（v1.1 目标）：支持 schema 版本间的受控前向兼容——在 schema 变更时定义「安全退化映射」（如新列有合理默认值时允许旧版本忽略该列），通过 `schema_compatibility` 表注册兼容范围。v0.1.0 不实现此项——采用保守的硬拒绝策略

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_SCHEMA_VERSION` | 编译时常量 | 当前二进制支持的 schema 版本 |
| `KAIROS_SCHEMA_STRICT_MODE` | `true` | true=硬拒绝高版本 DB，false=允许启动但记录告警（不推荐） |

#### P3-24 Symbolic Memory——Mermaid Canvas 节点图可视化

Kairos 的知识图谱（实体知识图谱、关系索引、因果链路）以结构化数据存储，但缺乏直观的可视化呈现。Symbolic Memory 通过 Mermaid Canvas 将记忆节点和关系边渲染为交互式图形，使开发者能「看到」记忆空间的拓扑结构。

**设计**：

- **可视化对象**：记忆节点（`memories` 表中的条目）、实体节点（`entities` 表）、关系边（`memory_relations` / `causal_links` / `memory_entities`）
- **渲染引擎**：Mermaid.js 的 `graph` 类型（支持 LR/TD 布局方向）+ Canvas 渲染后端。生成的 Mermaid 图通过 Kairos 内嵌的 Web 仪表盘展示，或通过图谱可视化 API（见 api-spec §17 GET /v1/graph/render）导出为 SVG/PNG
- **节点样式映射**：
  - `is_structure=true` → 菱形节点（表示结构性记忆）
  - `is_identity=true` → 双线边框（表示身份记忆）
  - `quality_tier` → 颜色：mental_models=金、observation=蓝、experience=绿、world=灰
  - `contract` → 虚线边框（temporary）、实线边框（其他）
- **边样式映射**：`causes`=实线箭头、`caused_by`=虚线箭头、`derived_from`=点线箭头、`enriches`=粗实线、`challenges`=红色虚线
- **交互能力**：节点可点击展开（显示记忆摘要和元数据）、边可 hover 显示关系置信度和证据片段、支持按路径前缀过滤子图、支持缩放和平移
- **性能约束**：单次渲染节点数上限 `KAIROS_SYMBOLIC_MAX_NODES`（默认 200），超过上限时按中心性排序截断至 Top-N。大规模图谱（> 1000 节点）使用离线预渲染快照，不实时生成

**配置参数**：

| 参数 | 默认值 | 说明 |
|:-----|:------|:-----|
| `KAIROS_SYMBOLIC_ENABLED` | `true` | Symbolic Memory 可视化总开关 |
| `KAIROS_SYMBOLIC_MAX_NODES` | `200` | 单次渲染节点数上限 |
| `KAIROS_SYMBOLIC_DEFAULT_LAYOUT` | `TD` | 默认布局方向（TD=上到下 / LR=左到右） |
| `KAIROS_SYMBOLIC_RENDER_FORMAT` | `svg` | 默认导出格式（svg / png） |

#### P3-25 基于 Permission ACL 的写入权限控制

§7.3 的权限检查内嵌声明定义了写入时的路径前缀权限校验，但权限模型仅含简单的「允许/拒绝」二元判定，缺乏细粒度的读写分离、黑白名单和继承机制。Permission ACL 将权限控制从硬编码路径检查升级为可配置的访问控制列表。

**ACL 条目结构**：

每条 ACL 规则定义为一个四元组：`(路径前缀, 主体, 权限集, 策略类型)`

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `path_prefix` | TEXT | `kairos://` 路径前缀，支持通配符 `*`（匹配单层）和 `**`（匹配任意深度） |
| `principal` | TEXT | 主体标识——Agent ID（如 `hermes-agent`）、用户 ID、或 `*`（通配任意主体） |
| `permissions` | JSONB | `{read_perm: bool, write_perm: bool, admin_perm: bool}` ——读写分权，admin_perm 控制 ACL 规则本身的修改权限 |
| `policy` | TEXT | `whitelist`（默认拒绝，显式允许）或 `blacklist`（默认允许，显式禁止） |
| `priority` | INTEGER | 规则优先级（0=最高），用于解决冲突——高优先级规则覆盖低优先级 |
| `inheritance` | TEXT | `none`（不继承）/ `children`（子路径继承）/ `full`（子路径和孙路径递归继承） |
| `description` | TEXT | 规则用途说明（审计用） |
| `created_at` | TIMESTAMPTZ | 规则创建时间 |
| `updated_at` | TIMESTAMPTZ | 规则最后修改时间 |

**权限检查算法**：

```text
function check_permission(path, principal, requested_perm):
    # 1. 收集所有匹配 path 的 ACL 规则（前缀匹配 + 通配符展开）
    candidates = SELECT * FROM permission_acl
                 WHERE path_prefix MATCHES path
                 AND (principal = $principal OR principal = '*')
                 ORDER BY priority ASC, path_prefix DESC

    # 2. 继承链展开：若某规则标记 inheritance=children/full 且 path 是 path_prefix 的子路径，则该规则也适用于此 path
    inherited = expand_inheritance(candidates, path)

    # 3. 按优先级仲裁——最高优先级的显式规则生效
    for rule in [candidates + inherited]:
        if rule.policy == 'whitelist':
            return rule.permissions[requested_perm]  # true=允许，false=拒绝
        elif rule.policy == 'blacklist':
            return not rule.permissions[requested_perm]  # 翻转——true=禁止访问，false=允许

    # 4. 无匹配规则时的默认策略：拒绝（fail-closed）
    return false
```

**权限分权**：

- **read_perm**：控制检索（search/read）和浏览（ls/tree）操作。read_perm 级别 ≤ write_perm 级别——能读不意味能写
- **write_perm**：控制写入（create/update/delete/merge/fork/archive）操作。write_perm 包含 read_perm（能写必能读）——若 write_perm=true 但 read_perm=false，系统自动将 read_perm 提升为 true
- **admin_perm**：控制 ACL 规则本身的修改（添加/修改/删除 ACL 条目）。仅 admin_perm=true 的主体可操作 `permission_acl` 表。admin_perm 自动包含 read_perm 和 write_perm

**黑白名单语义**：

| 策略 | 默认行为 | 权限字段语义 |
|:-----|:--------|:-----------|
| **whitelist** | 默认拒绝一切访问 | `read_perm=true` → 显式允许读；`read_perm=false` → 无意义（默认已拒绝） |
| **blacklist** | 默认允许一切访问 | `write_perm=true` → 显式禁止写；`write_perm=false` → 无意义（默认已允许） |

**继承链**：

- `inheritance=none`：规则仅适用于精确匹配的路径前缀（含通配符匹配的直接路径）
- `inheritance=children`：规则适用于路径前缀的直接子路径（一层深度），如 `/users/` → 适用于 `/users/alice/`，不适用于 `/users/alice/projects/`
- `inheritance=full`：规则递归适用于路径前缀的所有后代路径（任意深度），如 `/system/` → 适用于 `/system/config/`、`/system/config/keys/` 等
- 继承展开在权限检查时实时计算——展开结果不持久化，防止规则修改后遗留过期继承记录
- 继承冲突：当父路径的继承规则与子路径的显式规则冲突时，显式规则优先（无论优先级字段值）——最近匹配原则

**与现有权限检查的关系**：

- §7.3 的权限检查内嵌声明为硬编码的路径前缀校验——Permission ACL 将其替代为可配置的规则引擎
- v0.1.0 迁移策略：系统启动时从配置文件 `acl_bootstrap.yaml` 加载初始 ACL 规则集（等价于现有硬编码权限），之后通过 API `POST /v1/acl/rules` 管理
- 宪法级路径保护：`kairos://_system/` 和 `kairos://_audit/` 路径前缀的 ACL 规则不可修改（硬编码为 `admin_perm` 主体的 whitelist），防止 ACL 规则被篡改后锁定管理员

**配置参数**：

> **配置参数**：Permission ACL 的开关、默认策略和规则数量上限见 [ops/configuration.md](../ops/configuration.md) §6.8。

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 架构蓝图：v1.1+ 未来版本详细规划（P3 前瞻设计等），非 v0.1.0 交付范围。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：§5.5 声明扣除（D-05 已迁入 v0.1.0，本文不再单独演进）；补 P3 组件与技能体系章节标题层级；修正认知基础/VAD §1.4 错引、技能重排 Tier 2/3 引用（架构 §5.9）、技能管理系统引用（本文 §5.2）。 |
| 0.0.3 | 2026-08-04 | 文档职责剥离承接（changelog 0.0.9 批次）：承接主架构剥离的 P3 系组件详细规格——P3-11 Directives、P3-12 malloc_trim、P3-13 Webhook、P3-17 TeamScope、P3-20~24 存储基础设施（SQLCipher/FTS5/PreparedStatementCache/Schema 保护/Mermaid）、P3-25 Permission ACL。 |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：P3 编号导航索引；P3-25 配置参数空表清理。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次：决策 D-05 引用标注「决策」前缀（3 处）。 |
| 0.0.13 | 2026-08-04 | 认知×架构交叉审计修复批次（决策 D-16~D-27）：MemCube L3/L4 工程层声明（不映射认知层记忆分类）；Playbook/Skills 程序记忆文档化声明（不改变程序记忆认知激活规则）；mental_models 准入条件正交性修正（身份标志非充要条件，宪法解释层判例可入）。 |
| 0.0.19 | 2026-08-05 | 第四轮全库深度审计修复批次（changelog 0.0.19）：新增 P3-19 File Graph 章节（规格承接自 technology-stack §七，标注 v1.1 目标）；P3-18 预留编号墓碑说明；文件名 `v1.1+` → `v1.1`（全库链接同步，登记为命名规范约定）。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次（changelog 0.0.24）：§5.7 多 Agent 校准参数占位声明过时引用修正（1-04）——否决权归属/激活开关/预留路径改指架构现存章节（§0.4 社会性校准占位段/§1 章宪法主权面/§0.4 接入层），同段激活前提条件引用同源修正。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：api-spec 中文序引用联动（§十~§十六 5 处）。 |
| 0.0.29 | 2026-08-06 | 第十轮全库深度审计 P1 修复批次（changelog 0.0.29）：S-01 大章标题归位中文序（一、P3 前瞻组件 / 二、核心机制规格 / 三、P3 前瞻组件续）。 |
| 0.0.30 | 2026-08-06 | 仓库整洁化批次（changelog 0.0.30）：audit-history-summary 引用清理，引用同步。 |
| 0.0.33 | 2026-08-06 | round12/round13 深度审计修复批次（changelog 0.0.33）：版本记录补登 0.0.30 行（原漏登记）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：技能体系统一（状态机六态权威+晋升门禁参数化）；引用落点修正（§5.5 step 8/§5.2/§3.2）；P3 导航矛盾消除；GraphRAG 独立配比注记；见证自愈与架构 §5.5 第 8 步双向收敛；路径空间统一下划线命名。 |
| 0.0.44 | 2026-08-08 | 外部理念吸收落地批次（changelog 0.0.44）：§5.7 多 Agent 校准参数补参考注记（AP-29，PAPER-10 G-Memory 三层图记忆 + Agent 特定投影 + 洞察支撑集溯源为 v1.1 参考材料；任务后自动演化不吸收）。 |
| 0.0.48 | 2026-08-08 | 外部理念吸收落地批次（changelog 0.0.48）：§5.3 价值独立性公理补决策效用张力注记（AP-50，PAPER-19 DeMem / PAPER-20 Mem-W，双标准分域立场 + 率失真遗忘边界作遗忘调度器代价参考）；P3 区补经验-资产共演化候选注记（AP-46，PAPER-16 Mem²Evolve，升华管道与资产层扩张联动候选 + 宪法边界门禁）。 |
