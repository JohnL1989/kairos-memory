---
title: RL 权重优化器规格
aliases:
  - RL 权重
  - rl-weight-spec
tags:
  - kairos
  - rl
  - specification
created: 2026-07-22
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# RL 权重优化器规格

> **定位**：定义六级辞典式排序链+身份面否决权之上可学习的二次排序维度、更新算法与 P6 合规框架。
> 详见 [foundation/architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.14。
>
> **P6 合规声明**：本规格采用**多维独立排序**（各维度不聚合为单标量参与裁决），符合 P6 「价值裁决禁止单标量聚合」的绝对禁令。各维度在辞典式排序链内独立产出排序信号，交叉约束由维度间的全局闸门管理。

## 排序维度

| 维度 | 目标权重范围 | 默认值 | 受来源影响 | 说明 |
|:----|:-----------:|:------:|:----------|:-----|
| `relevance` | 0.30–0.50 | 0.40 | user, knowledge, research | 查询与记忆的语义相关性 |
| `recency` | 0.15–0.25 | 0.20 | context, task_history | 记忆新鲜度 |
| `frequency` | 0.10–0.20 | 0.15 | experience | 访问频率 |
| `user_feedback` | 0.10–0.20 | 0.15 | user | 用户显式反馈（👍/👎） |
| `trust_score` | 0.05–0.15 | 0.10 | knowledge, experience, research | 来源可信度 |

## 多维排序算法

辞典式排序链是主排序（第一优先），RL 权重是**二级多维排序**（在各辞典链层级内部使用）。排序过程：

```text
1. 辞典式排序链裁决：按 探索>宪法>校准>认知完整性>时间>间接度 分层，身份面以正交否决权介入（不在链内）
2. 每层内的二级排序由五维信号独立参与：
   a. 各维度独立产出排序分（不加权求和）
   b. 维度间的关系由 P6 全局闸门约束（见§P6合规段）
   c. 检索排序器接收五维独立信号，按字典序逐维裁决
3. 跨维冲突（如相关性和新鲜度指向不同结果）由辞典式优先级解决：
   relevance < recency < frequency < user_feedback < trust_score
```

### 初始化

各维度独立初始化到目标范围中位数。不做 simplex 归一化（尽管默认值和恰为 1.00——这是中位数初始化的自然结果，各维度独立运作）。**勘误**：更新管线每次迭代执行 `projected / sum(projected)` 强制 Σ=1（见 §权重更新管线），EMA 为线性组合（两序列和均为 1 时 EMA 和恒为 1）——「和会偏离 ≠1」与管线机制相抵，删除该表述；权重和的精确保持由投影步骤保证。entity_boost 默认 0.05，仅在 v1.1+ 激活完整加权时参与排序。

### 维度权重更新

```text
1. 累积 N 条反馈后进入更新（N = KAIROS_RL_MAX_BUFFER_SIZE）
2. 每条反馈携带各维度的独立评分（不合并为总分）
3. 按来源类型聚合 rel×trust 得分 → 各维度独立 delta
4. Cosine 学习率衰减：lr = lr_min + 0.5×(1+cos(π×step/max_steps))×(base_lr - lr_min)
5. Epsilon-greedy 探索：eps 从 0.1 线性衰减至 0.01
6. 各维度独立 clamp 到目标范围
7. EMA 平滑：each_dim_ema = decay × each_dim_ema + (1-decay) × each_dim_weight
```

### KL 散度策略追踪（附 softmax 归一化）

监测各维度权重分布变化，防止策略震荡：
- 各维度权重先经 softmax 归一化为概率分布（使 Σp=1），再计算当前 EMA 权重归一化分布与快照间的 KL 散度（各维度独立计算，取最大值为总体散度）
- 总体散度 > 0.5 时，衰减因子额外降低（max_extra=0.3）

> **衰减实现防坑注记（第三方实证）**：任何「降衰减因子」实现必须作用于**维度差异**（偏离快照越远的维度拉回越强），不得对所有维度同因子缩放后 softmax 归一化——softmax 对正缩放不变（softmax(λw)=softmax(w)，λ>0），同因子衰减再归一化是**数学恒等式，不产生任何效果**。此坑由第三方实现实测踩中后修正（其代码注释自曝：原「所有维度乘以同因子再 softmax」为无效实现，改为按维度差异衰减 + clamp 到规格范围）。Kairos 的 Bounded Simplex Projection（softmax 用于投影与监测、不用于衰减）不受此影响；「衰减因子额外降低」的落地实现须按维度差异执行。
- **注意**：softmax 归一化用于 KL 散度监测与权重更新投影（Bounded Simplex Projection，见 §权重更新管线）——均不参与排序裁决。排序始终按五维独立信号 + 辞典序执行（见 §排序模型），不受 softmax 影响。softmax 在监测与投影中的使用属速率调制类工程实现，不构成价值裁决——已登记为 P6 受控例外（0.0.11 勘误：原「仅用于 KL 散度监测」表述与权重更新管线中 softmax 参与投影自相矛盾，已修正）

## P6 合规框架

| 检查项 | 状态 | 证据 |
|:-------|:----|:-----|
| 禁止单标量聚合参与价值裁决 | ✅ 合规 | 五维独立排序，不加权求和。softmax 仅用于 KL 散度监测与权重投影（速率调制类工程实现，非价值裁决——已登记为 P6 受控例外） |
| 维度间交叉约束有全局闸门 | ✅ 合规 | 辞典式优先级 + 独立 clamp 范围 |
| 信息损失显式标注 | ✅ 合规 | 各维度独立输出，不聚合 |
| 可回溯的多维表征 | ✅ 合规 | 每次排序记录五维独立得分 |

## 持久化

五维权重以 JSONB 存储于 `user_profiles` 表的 `rl_weights` 字段中（按 user_id/profile 隔离，重启后自动恢复）。权重维度：`{"relevance": 0.40, "recency": 0.20, "frequency": 0.15, "user_feedback": 0.15, "trust_score": 0.10}`。`entity_boost` 为配置参数（默认 0.05），不参与五维排序，v1.1+ 激活完整加权时并入排序维度。

## 权重优化器实现（架构 §10.14 剥离）

> **来源与去重说明**：本节为 [foundation/architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.14 的实现细节剥离，仅收录本规格上文尚未覆盖的管线环节——多源奖励贡献加权（RCW）、历史基线（advantage）与 Bounded Simplex Projection 迭代投影。Cosine 学习率衰减、ε-greedy 探索与 KPop KL 散度稳定性监测的机制与公式见上文「多维排序算法」与「KL 散度策略追踪」，此处不重复。

**优化管线——RCW 奖励加权、历史基线与权重更新**：

```text
用户反馈（positive/negative）
  │
  ├─ 多源奖励贡献加权（RCW）
  │   每条检索结果的 source 类型（由 provenance 字段定义），
  │   计算 relevance × trust_score 的加权均值作为该源的奖励贡献
  │   映射规则：user→relevance, context→recency, experience→frequency
  │   （维度表「受来源影响」为输入集口径，RCW 映射为奖励信号子集——
  │    knowledge/research 经 relevance 加权、task_history 经 recency 加权）
  │   归一化至和为 1，确保各源贡献非负
  │
  ├─ 历史基线
  │   最近 M 条反馈的平均奖励作为 baseline
  │   advantages = reward - baseline
  │   （M 由配置参数控制，见 [ops/configuration.md](../ops/configuration.md) §9）
  │
  └─ 权重更新
      delta = learning_rate × advantage × rcw_multiplier
      # Bounded Simplex Projection：先 softmax 归一化，再投影到各维度的独立范围约束
      raw = softmax(weight + delta)
      # 迭代投影：clamp 到 [min, max] → 重归一化 → 重复直至收敛（通常 2-3 次）
      for _ in range(5):
          projected = clamp(raw, weight_bounds[:,0], weight_bounds[:,1])
          raw = projected / sum(projected)
      weight = raw
      EMA: ema = decay_factor × ema + (1 - decay_factor) × weight
```

> **配置参数**：RL 权重优化器的所有参数（维度范围、学习率调度、探索策略、KPop 稳定性监测等）见 [ops/configuration.md](../ops/configuration.md) §9。

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | RL 权重优化器规格：五维权重、多维排序算法与 P6 合规框架。 |
| 0.0.2 | 2026-08-04 | 文档职责剥离承接（changelog 0.0.9 批次）：新增「权重优化器实现」节——RCW 多源奖励贡献加权、历史基线 advantage、Bounded Simplex Projection 权重更新伪代码，承接自架构 §10.14（Cosine LR/ε-greedy/KPop 已覆盖处去重）。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：softmax 用途两说统一（KL 监测+权重投影）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：「和≠1」表述勘误（投影管线强制 Σ=1）。 |
| 0.0.32 | 2026-08-06 | 第三方分析分诊批次（changelog 0.0.32）：KL 散度段补衰减实现防坑注记（softmax 对正缩放不变——同因子衰减再归一化为数学恒等式，第三方 EchoMind 实测踩中后修正；Kairos 投影管线不受影响）；检索反馈权重快照机制随 D-414 登记（规格级，实现随 RL 权重优化器 v1.1+）。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：版本注记纪律收敛（正文删除 0.0.14/0.0.32 前缀与产品名，保留技术信息）；RCW 映射规则补口径注记（维度表来源为输入集，RCW 为奖励信号子集——knowledge/research 经 relevance、task_history 经 recency 加权）。 |
