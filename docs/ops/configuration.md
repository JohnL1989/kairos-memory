---
title: Kairos 配置参数参考
aliases:
  - 配置文档
  - Configuration
tags:
  - kairos
  - ops
  - configuration
created: 2026-07-18
updated: 2026-08-11
last_reviewed: 2026-08-11
status: draft
---

# Kairos 配置参数

> **时间单位定义**：本文中「个调度周期」为相对时间单位，1 调度周期 = `KAIROS_SCHEDULER_INTERVAL` 配置值（默认 300 秒 / 5 分钟）。所有以「调度周期」为单位的参数均以此值为基准换算。

> **参数名约定**：所有配置参数通过环境变量或配置文件设置，统一使用 `KAIROS_` 前缀。本文正文列出 227 项核心参数（v0.1.0 设计阶段的参数主索引）。可靠性参数（如 LLM 超时/熔断阈值）在正文 §7 定义；部署模式特有参数（如 [deployment.md](deployment.md) 中的 `KAIROS_DB_DSN`、`KAIROS_LITE_MODE`）在对应文档中定义，并已在**附录 A** 中建立全量索引（147 项）。**全库参数总数 = 227 + 147 = 374 项**，本文为唯一完整入口。（附录收录规则：正文已定义参数不入附录——`KAIROS_LLM_MAX_COST_PER_CALL_FEN`/`KAIROS_LLM_CIRCUIT_BREAK_FAILURES`/`KAIROS_LLM_CIRCUIT_BREAK_COOLDOWN_S` 曾两处重复登记，已按此规则在附录去重；历史计数链见版本记录。）

> **计数口径：登记总数 ≠ v0.1.0 生效子集**。374（227 + 147）为**登记总数**，用于跨文档对账；实现方按下述子集取用，勿将登记总数当作"必须实现 373 个开关"。
>
> | 口径 | 数量 | 构成 |
> |:-----|:----:|:-----|
> | 正文登记 | 227 | v0.1.0 参数主索引 |
> | 正文中 **v0.1.0 不生效** | 7 | `KAIROS_SEARCH_WEIGHT_VECTOR` / `_BM25` / `_TIME` / `_RELIABILITY` / `_HEAT`（5 项，§8.3 废弃声明——5D 权重框架已被 §6.1 三信号检索替代）、`KAIROS_VIRTUAL_CALIBRATION_TIMEOUT`（§1，非独立生效，实际由 `KAIROS_CALIBRATION_*` 三参数联动承载）、`KAIROS_FORGETTING_SCORE_THRESHOLD`（§3，v1.1 二维遗忘曲面口径，v0.1.0 用 freshness 三阈值） |
> | **正文 v0.1.0 生效子集** | **220** | 227 − 7 |
> | 附录 A 索引 | 147 | 部署模式特有参数 + 蓝图 v1.1 参数（后者「来源」列指向 [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md)，v0.1.0 不实现）——**例外注记（round31 收敛）**：`KAIROS_FTS5_*` 基础参数族（ENABLED/TOKENIZER/CHINESE_SEGMENTATION/OPTIMIZE_INTERVAL）为 v0.1.0 已交付（轻量模式 BM25 承载，见架构 §7.3a / data-model §11），「来源」列已改指 v0.1.0 权威；蓝图 §P3-21 保留 jieba 精细分词与 Playbook 全文索引的 v1.1 增强语义 |
>
> 「不生效」项**保留登记**而非删除：废弃项保留供旧部署迁移比对（§8.3 迁移说明），v1.1 项保留供版本衔接，两类均在各自条目内已标注，读者按标注取用。

> **状态声明**：以下参数为草稿完善阶段的设计值。框架实现版本锁定后可能微调。

> **新增列说明（RC-08）**：自 2026-08-03 起，正文 §1–§10 参数表表头由 `| 参数 | 默认值 | 说明 |` 扩展为 `| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |`。「取值范围」按参数语义推断（权重/阈值/概率类为 [0,1]，周期类为 ≥1 周期，布尔类为 {true,false}）；「生效时机」标注配置热加载能力（核心参数多为重启生效）。

> **章节导航**：
> | 章节 | 主题 |
> |:----|:----|
> | 一、架构层参数（按章节） | 227 项正文参数主索引（§1~§10，按架构章节组织） |
> | 二、运行时动态调整规则 | 动态调参模式、授权者与不变量 |
> | §11 特征标志默认值 | 特征标志默认值对照（含竖切例外注记） |
> | 附录 A：全库参数总索引 | 147 项正文未收录参数索引（合计 374 项）

## 一、架构层参数（按章节）

### §1 宪法主权面

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_EXPLANATION_EXHAUSTION_ALERT_THRESHOLD` | 3 次 | 见说明约束 | 重启生效 | 解释枯竭告警连续触发此次数后申请推理悬挂 |
| `KAIROS_VIRTUAL_CALIBRATION_CONFIDENCE_CAP` | 0.3 | [0,1] | 重启生效 | 虚拟校准信号的置信度上限（架构定义：预设上限 0.3 且不可用于修宪）。**动态衰减**：生效置信度 = `0.3 × exp(-λ × 静默天数)`，见 `KAIROS_CALIBRATION_DECAY_LAMBDA` |
| `KAIROS_CALIBRATION_DECAY_LAMBDA` | 0.02 | >0 浮点 | 重启生效 | 虚拟校准置信度时间衰减速率常数（建议一）——`virtual_confidence = 0.3 × exp(-λ × days)`，λ=0.02 约每 35 天减半（架构 §1.2 虚拟校准生成器） |
| `KAIROS_CALIBRATION_DECAY_FLOOR` | 0.05 | [0,0.3] | 重启生效 | 虚拟校准置信度下限（建议一），衰减不低于此值 |
| `KAIROS_CALIBRATION_AUTO_DORMANT_DAYS` | 60 | ≥1 整数 | 重启生效 | 外部校准静默达此天数时自动切换休眠态（建议一）——运营可视化 dormant 态阈值，实际休眠切换仍由 §10.9 降级状态机周期阈值驱动 |
| `KAIROS_VIRTUAL_CALIBRATION_TIMEOUT` | 900 | ≥0 整数 | 重启生效 | 外部校准端口静默超过此时长（秒）后生成虚拟校准信号。**触发口径**：实际触发由校准调度器联动逻辑承载（[detailed-design.md](../specification/detailed-design.md) §5）——`KAIROS_CALIBRATION_TIMEOUT`（默认 300s）每次超时静默计数 +1，计数 > `KAIROS_CALIBRATION_SILENT_COUNT`（默认 6 次）即 6×300=1800s 触发生成。本参数 900s 为架构 §11 术语表的简化表述（对应 3 次静默），不作为独立生效参数——实现与配置核对以校准调度器联动逻辑与 `KAIROS_CALIBRATION_*` 三参数为准 |
| `KAIROS_VIRTUAL_CALIBRATION_SIMILARITY_THRESHOLD` | 0.7 | [0,1] | 重启生效 | 虚拟校准与见证锚定比对的相似度阈值 |
| `KAIROS_VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD` | 3 次 | 见说明约束 | 重启生效 | 连续冲突次数超过此值触发拟真校准失稳告警（对应 observability 拟真校准失稳告警）。**与 `KAIROS_CALIBRATION_CONFLICT_THRESHOLD` 的区分（注记）**：本参数为**次数阈值**（连续冲突 N 次 → 告警，架构 §1.2 虚拟校准生成器）；后者为**单次冲突判定的相似度阈值**（cosine 距离 ≥0.35 判定为冲突，[detailed-design.md](../specification/detailed-design.md) §5 校准调度器）——两者是同一冲突检测链的两个环节（单次判定 + 连续计数），非同一参数 |
| `KAIROS_CALIBRATION_DEGRADE_THRESHOLD` | 6 周期 | ≥1 周期 | 重启生效 | 距上次校准超过此周期数触发降级告警（对应 observability 校准中断严重。1 周期 = KAIROS_SCHEDULER_INTERVAL 默认 300s） |
| `KAIROS_SAFETY_HIBERNATION_COOLDOWN` | 30 周期 | ≥1 周期 | 重启生效 | 安全休眠态自动恢复前的冷却周期数（对应 observability degradation_mode=3） |

### §2 元认知层

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_BLIND_SPOT_PROXIMITY_RADIUS` | 0.3（余弦距离） | 见说明约束 | 重启生效 | 盲区标注「几何邻近」的半径 |
| `KAIROS_BLIND_SPOT_SEMANTIC_DIVERGENCE_THRESHOLD` | 0.6（余弦距离） | [0,1] | 重启生效 | 盲区标注「语义迥异」的阈值 |
| `KAIROS_EMOTIONAL_VAD_DEVIATION_SIGMA` | 1.5σ | [0,1] | 重启生效 | 情感 VAD 偏移背离标准差倍数，超过此值情感提升权重衰减至零（架构 §3.2）；另一用途：情感流形监测器超 σ 触发外部校准告警（[vad-coordinate-algorithm.md](../references/vad-coordinate-algorithm.md) §三） |
| `KAIROS_EMOTIONAL_VAD_WEIGHT_BASE` | 0.15 | [0,1] | 重启生效 | VAD 情感在综合评分中的基础权重系数（0=不使用VAD，1=VAD完全主导）。实际参与权重 = base × (1 - deviation/deviation_sigma)，超出 sigma 时降为 0 |
| `KAIROS_META_AUDIT_ENTROPY_SURGE_THRESHOLD` | 3× 基线标准差 | ≥0（按语义标定） | 重启生效 | 决策熵异常飙升的判定阈值（相对于基线偏差倍数） |
| `KAIROS_META_AUDIT_ENTROPY_MEASUREMENT_WINDOW` | 10 个调度周期 | ≥1 周期 | 重启生效 | 决策熵测量的滑动窗口长度 |
| `KAIROS_HEALTH_MONITOR_PERIOD` | 5 个调度周期 | ≥1 周期 | 重启生效 | 健康计数器连续无异常的判定周期数 |
| `KAIROS_HEALTH_MONITOR_LATENCY_THRESHOLD` | 500ms | ≥0（按语义标定） | 重启生效 | 环延迟告警阈值 |
| `KAIROS_FROZEN_EMERGENCY_TIMEOUT` | 30 个调度周期 | ≥1 周期 | 重启生效 | 应急冻结自动进入安全降级持久态的超时 |
| `KAIROS_FROZEN_COOLDOWN_PERIOD` | 3 个调度周期 | ≥1 周期 | 重启生效 | 冻结解除后不接受探索投资的冷启动期 |

### §3 策略层

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_PREDICTOR_ATTRIBUTION_TTL` | 3 个调度周期 | ≥1 周期 | 重启生效 | 任务归档后使用权重冻结前的窗口 |
| `KAIROS_COMPOSITION_RETRIEVAL_WEIGHT` | 1.2 | ≥0（相对负载倍数，无量纲，按语义标定） | 重启生效 | 检索级负载系数 |
| `KAIROS_COMPOSITION_SIMULATION_WEIGHT` | 1.8 | ≥0（相对负载倍数，无量纲，按语义标定） | 重启生效 | 模拟级负载系数 |
| `KAIROS_COMPOSITION_VERIFICATION_WEIGHT` | 1.4 | ≥0（相对负载倍数，无量纲，按语义标定） | 重启生效 | 验证级负载系数 |
| `KAIROS_COMPOSITION_CONTRIBUTION_WEIGHT` | 1.6 | ≥0（相对负载倍数，无量纲，按语义标定） | 重启生效 | 贡献级负载系数 |
| `KAIROS_COMPOSITION_IMPLICIT_WEIGHT` | 2.0 | ≥0（相对负载倍数，无量纲，按语义标定） | 重启生效 | 内隐级负载系数 |
| `KAIROS_CONSTITUTIONAL_LOCK_PERIOD` | 1000 个外部校准周期 | ≥1 周期 | 重启生效 | 辞典式排序优先级链的最小锁定周期 |
| `KAIROS_EDGE_SLOT_TIMEOUT_MULTIPLIER` | 3× | 见说明约束 | 重启生效 | 边缘槽超时倍数 |
### §4 存储层

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_LATENT_REVIVAL_MATCH_THRESHOLD` | 0.65（余弦相似度） | [0,1] | 重启生效 | 潜伏记忆二级匹配的相似度阈值 |
| `KAIROS_LATENT_REVIVAL_INITIAL_CONFIDENCE` | 80% | [0,1] | 重启生效 | 复兴加速通道的影子副本置信度初始值（占积累阈值比例） |
| `KAIROS_FORGETTING_SCORE_THRESHOLD` | 0.75 | ≥0（按语义标定） | 重启生效 | 遗忘调度器触发压缩/归档的遗忘得分阈值。**归属勘误**：v0.1.0 遗忘判定为 freshness 三阈值（`KAIROS_FRESHNESS_ACTIVE_THRESHOLD`/`KAIROS_FRESHNESS_STALE_THRESHOLD`），本参数属于 v1.1 二维遗忘曲面得分口径（[detailed-design.md](../specification/detailed-design.md) §3 v1.1 目标段），v0.1.0 不使用 |
| `KAIROS_WITNESS_UPDATE_BARRIER_N_DEFAULT` | 3 | ≥0 整数 | 重启生效 | 更新势垒 N 的默认值（外部校准可上调） |
| `KAIROS_NARRATIVE_COHERENCE_FALLBACK_SCORE` | 0.5 | 见说明约束 | 重启生效 | 叙事自洽度评估器不可用时的默认分 |
| `KAIROS_INTEGRATION_CONSISTENCY_PERIOD` | 5 个调度周期 | ≥1 周期 | 重启生效 | 反向调整方向一致判定周期数 |
| `KAIROS_INTEGRATION_COOLDOWN_PERIOD` | 10 个调度周期 | ≥1 周期 | 重启生效 | 反向调整冷却期 |
| `KAIROS_EMOTIONAL_DE_AMPLIFICATION_RATIO` | 50% | [0,1] | 重启生效 | 情感去强化时 arousal→更新势垒增益的衰减比例 |
| `KAIROS_EMOTIONAL_DE_AMPLIFICATION_WINDOW` | 20 个调度周期 | ≥1 周期 | 重启生效 | 情感去强化默认窗口长度 |
| `KAIROS_ENCODING_BUDGET_RATIO` | 3:3:2:2 | [0,1] | 重启生效 | 情景:叙事:语义:程序的编码预算分配比例 |
| `KAIROS_CONFLICT_RESOLUTION_SIMILARITY_HIGH` | 0.9 | [0,1] | 重启生效 | 补充/修正/重构判定的高相似度阈值 |
| `KAIROS_CONFLICT_RESOLUTION_SIMILARITY_MEDIUM` | 0.5 | [0,1] | 重启生效 | 补充/修正/重构判定的中相似度阈值下限 |
| `KAIROS_COMPLEXITY_BUDGET_THRESHOLD` | 15 | ≥0（按语义标定） | 重启生效 | 跨层协调协议复杂度阈值（层数 × 接口数） |
| `KAIROS_DEGRADATION_PERIOD_N` | 50 个调度周期 | ≥0（按语义标定） | 重启生效 | 他律性降级契约——保守静默模式的阈值 |
| `KAIROS_DEGRADATION_PERIOD_M` | 200 个调度周期 | ≥0（按语义标定） | 重启生效 | 他律性降级契约——受限内部验证模式的阈值 |
| `KAIROS_COGNITIVE_JOINT_BACKUP_PATH` | `~/.kairos/backups/cognitive-joints/` | 见说明约束 | 重启生效 | 认知关节可逆执行的备份目录 |
| `KAIROS_OBSERVATION_WINDOW_PERIODS` | 5 个调度周期 | ≥1 周期 | 重启生效 | 认知关节调整后的双轨观察窗口长度 |
| `KAIROS_SANDBOX_TIMEOUT_PERIODS` | 90 | ≥1 周期 | 重启生效 | 沙箱验证环超时待定状态自动拒绝的周期数 |
| `KAIROS_INVARIANT_OBSERVATION_WINDOW_PERIODS` | 3 | ≥0 整数 | 重启生效 | 不变量修订门禁的观察窗口期长度 |
| `KAIROS_REVERSE_CHAIN_FEEDBACK_PERIODS` | 3 | ≥1 周期 | 重启生效 | 逆向链反馈升级观察周期数 |
| `KAIROS_SEED_ANCHOR_PATH_PREFIX` | `kairos://_system/seeds/` | 见说明约束 | 重启生效 | 冷启动种子价值源的路径前缀 |
| `KAIROS_SEED_ANCHOR_MAX_ITEMS` | 10 | ≥0 整数 | 重启生效 | 种子锚点的最大条目数 |
| `KAIROS_HEALTH_MONITOR_RECOVERY_PERIODS` | 5 | ≥1 周期 | 重启生效 | 健康计数器自动撤销降级信号所需连续无异常周期数 |
| `KAIROS_HEALTH_MONITOR_TIMEOUT_PERIODS` | 30 | ≥1 周期 | 重启生效 | 健康计数器超时后升级为紧急冻结请求的周期数 |

### §5 工作记忆层（WM）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_WM_SLOT_CAPACITY` | 7 | ≥0 整数 | 重启生效 | WM 维护缓冲槽位上限（与注意力调度器资源池关联） |
| `KAIROS_WM_OPERATION_BUDGET` | 5 次/周期 | ≥1 周期 | 重启生效 | 每个调度周期内 WM 操作空间的最大推理/比较/组合操作次数 |
| `KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` | 0.7 | ≥0（按语义标定） | 重启生效 | 沙箱验证环允许合并的置信度积分阈值 |
| `KAIROS_SIMULATION_ISOLATION_TTL` | 3 个调度周期 | ≥1 周期 | 重启生效 | 模拟隔离区缓存项的超时时间 |
| `KAIROS_EXTRACTION_SUPPRESSION_INHIBITION_RATIO` | 0.7 | [0,1] | 重启生效 | 提取抑制的多路径衰减加权系数 |
| `KAIROS_EPSILON_LAG_INJECTION_RATE` | 0.3 | [0,1] | 重启生效 | ε滞后注入的默认滞后系数 |
| `KAIROS_CORTEX_DEGRADATION_TRIGGER_LATENCY` | 2000ms | ≥0（按语义标定） | 重启生效 | WM调度预处理器退化的外部推理引擎延迟阈值（超过此值皮层不可退化） |

### §6 接入层

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_PROVIDER_DEFAULT_ACCURACY` | 0.5 | 见说明约束 | 重启生效 | 新 Provider 参与加权前的默认历史准确率（v0.1.0 默认关闭，v1.1+ 启用加权） |
| `KAIROS_PROVIDER_MIN_CALIBRATION_EVENTS` | 5 | ≥0 整数 | 重启生效 | 新 Provider 参与加权所需的最小校准事件数（v0.1.0 默认关闭，v1.1+ 启用加权） |
| `KAIROS_DAILY_BUDGET_FEN` | 20000 | ≥0 整数 | 重启生效 | LLM 日预算上限（分，约 ¥200/天） |
| `KAIROS_INGEST_NOISE_FILTER_ENABLED` | true | {true,false} | 重启生效 | 摄取噪音规则库层开关（实证参考基线，债务 D-338）：§7.3 捕获门控后的四类纯正则噪音规则（单字/短确认、语气词、元命令、分隔符与纯标点行），命中不计轮数、不触发使用权重升温 |
| `KAIROS_EMOTIONAL_BURST_KEYWORDS` | 见说明约束 | 见说明约束 | 重启生效 | 摄入侧情绪爆发关键词表（债务 D-337）：命中整轮进入保护通道；由外部校准维护、不自动学习扩展（保守倾向 E.5），初始表随实现批次核定 |
| `KAIROS_EMOTIONAL_BURST_PROTECTION_ENABLED` | true | {true,false} | 重启生效 | 摄入侧情绪保护总开关（债务 D-337）：§5.2 摄入侧情绪保护组件的启用开关 |

#### §6.1 三信号混合检索参数（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_HYBRID_SEMANTIC_WEIGHT` | 0.50 | [0,1] | 重启生效 | 语义信号权重（α_s） |
| `KAIROS_HYBRID_BM25_WEIGHT` | 0.35 | [0,1] | 重启生效 | BM25 信号权重（α_b） |
| `KAIROS_HYBRID_ENTITY_WEIGHT` | 0.15 | [0,1] | 重启生效 | 实体加成权重（α_e） |
| `KAIROS_LITE_PROJECTION_CALIBRATION` | true | {true,false} | 重启生效 | 轻量模式 BGE-M3 投影至 1536 维后是否沿用标准模式语义权重 α_s=0.50；false 时回退至 BM25 主导路径（见 [adr.md](../governance/adr.md) ADR-012） |
| `KAIROS_BM25_ADAPTIVE_ENABLED` | true | {true,false} | 重启生效 | 自适应 BM25 参数调整开关 |
| `KAIROS_BM25_K1_BASE` | 1.2 | 见说明约束 | 重启生效 | BM25 k1 基值（中等长度查询） |
| `KAIROS_BM25_B_BASE` | 0.75 | 见说明约束 | 重启生效 | BM25 b 基值（中性长度归一化） |
| `KAIROS_HYBRID_CANDIDATE_POOL_SIZE` | 100 | ≥0 整数 | 重启生效 | 语义检索召回候选池大小（ANN top-K） |
| `KAIROS_TIME_FILTER_ENABLED` | true | {true,false} | 重启生效 | 时间过滤约束开关（实证参考基线）：§7.3a 检索管线中 as_of/事件时间窗口/纪元边界的候选域裁剪。false 时检索行为与无时间过滤完全一致（退化兼容） |

#### §6.2 GSPO 聚类去重参数（[detailed-design.md](../specification/detailed-design.md) §9.1）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_GSPO_ENABLED` | true | {true,false} | 重启生效 | GSPO 聚类去重开关 |
| `KAIROS_GSPO_SIMILARITY_THRESHOLD` | 0.85 | [0,1] | 重启生效 | 聚类语义相似度阈值（余弦相似度） |
| `KAIROS_GSPO_CV_THRESHOLD` | 0.15 | ≥0（按语义标定） | 重启生效 | 组内变异系数激活阈值 |
| `KAIROS_GSPO_DOMAIN_DIVERSIFY` | true | {true,false} | 重启生效 | 域均衡开关 |
| `KAIROS_GSPO_MIN_PER_DOMAIN` | 1 | ≥0 整数 | 重启生效 | 每个域的最小代表记忆数 |
| `KAIROS_GSPO_MIN_CLUSTER_SIZE` | 2 | ≥2 整数 | 重启生效 | 最小聚类规模——成员数低于此值的聚类不执行压缩（对应 [data-model.md](../specification/data-model.md) `kairos.retrieval.gspo.min_cluster_size`） |

#### §6.3 MMR 去重参数（[detailed-design.md](../specification/detailed-design.md) §9.2）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_MMR_ENABLED` | true | {true,false} | 重启生效 | MMR 去重开关 |
| `KAIROS_MMR_LAMBDA` | 0.50 | [0,1] | 重启生效 | λ 权衡系数——查询相关性与多样性的权重 |
| `KAIROS_MMR_TOP_K` | 10 | ≥0 整数 | 重启生效 | MMR 选择的目标返回数（通常等于检索请求的 top_k） |

#### §6.4 spaCy 实体提取参数（[detailed-design.md](../specification/detailed-design.md) §9.3）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_SPACY_ENABLED` | true | {true,false} | 重启生效 | spaCy 实体提取开关 |
| `KAIROS_SPACY_MODEL_ZH` | `zh_core_web_sm` | 见说明约束 | 重启生效 | 中文模型 |
| `KAIROS_SPACY_MODEL_EN` | `en_core_web_sm` | 见说明约束 | 重启生效 | 英文模型 |
| `KAIROS_SPACY_CONFIDENCE_THRESHOLD` | 0.7 | ≥0（按语义标定） | 重启生效 | 高置信度阈值——高于此值跳过 LLM 审核 |
| `KAIROS_SPACY_ENTITY_FILTER_PATH` | `config/entity_filter.json` | 合法 JSON | 重启生效 | 过滤词表路径 |
| `KAIROS_SPACY_ENTITY_RULER_PATH` | `config/entity_ruler_patterns.jsonl` | 合法 JSON | 重启生效 | 自定义 EntityRuler 模式路径 |
| `KAIROS_SPACY_ONLY_MODE` | false | {true,false} | 重启生效 | 纯 spaCy 模式（跳过 LLM 实体提取） |

#### §6.5 ADD-only 提取协议参数（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3g）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_ADD_ONLY_ENABLED` | true | {true,false} | 重启生效 | ADD-only 协议开关 |
| `KAIROS_ADD_ONLY_SUPPLEMENT_THRESHOLD` | 0.85 | [0,1] | 重启生效 | 语义重叠触发叠加判定的余弦相似度阈值 |
| `KAIROS_ADD_ONLY_OBSERVATION_CHAIN_MAX` | 50 | ≥0 整数 | 重启生效 | 单一主题的最大 observation 链长度——超限触发压缩合并 |

#### §6.6 实体抽取双策略参数（[detailed-design.md](../specification/detailed-design.md) §9.4）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_ENTITY_LLM_ENABLED` | true | {true,false} | 重启生效 | LLM 实体提取开关 |
| `KAIROS_ENTITY_LLM_CONFIDENCE_THRESHOLD` | 0.8 | ≥0（按语义标定） | 重启生效 | LLM 提取直接写入的置信度阈值（上阈值，区间判定的高界） |
| `KAIROS_ENTITY_LLM_DISCARD_THRESHOLD` | 0.5 | ≥0（按语义标定） | 重启生效 | LLM 提取丢弃实体的置信度阈值（下阈值——置信度低于本值丢弃；[下阈值, 上阈值) 区间写入并标记 `entity_pending_review`，区间判定互斥无重叠，见 detailed-design §9.4 写入策略） |
| `KAIROS_ENTITY_LLM_TIMEOUT` | 5 | ≥0 整数 | 重启生效 | LLM 提取超时（秒） |
| `KAIROS_ENTITY_KEYWORD_FALLBACK_ENABLED` | true | {true,false} | 重启生效 | 关键字降级策略开关 |
| `KAIROS_ENTITY_LLM_HEALTH_CHECK_INTERVAL` | 300 | ≥0 整数 | 重启生效 | LLM 通道健康检查间隔（秒） |
| `KAIROS_ENTITY_LLM_COOLDOWN_PERIOD` | 600 | ≥0 整数 | 重启生效 | LLM 通道降级冷却期（秒） |

#### §6.7 多模态图片参数（[api-spec.md](../specification/api-spec.md) §18.2）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_IMAGE_MAX_SIZE_BYTES` | 20971520 | ≥0 整数 | 重启生效 | 图片最大体积（20MB） |
| `KAIROS_IMAGE_THUMBNAIL_MAX_PX` | 512 | ≥0 整数 | 重启生效 | 缩略图最大边长（像素） |
| `KAIROS_IMAGE_ALLOWED_DOMAINS` | `[]` | 见说明约束 | 重启生效 | URL 图片允许的域名白名单（空=全允许） |
| `KAIROS_IMAGE_CACHE_TTL` | 604800 | ≥0 整数 | 重启生效 | 缓存 TTL（秒，默认 7 天） |
| `KAIROS_MULTIMODAL_EMBEDDING_ENABLED` | false | {true,false} | 重启生效 | 多模态 embedding 开关（v0.1.0 默认关闭，需 CLIP 模型部署） |
| `KAIROS_MESSAGE_PART_MAX_COUNT` | 50 | ≥0 整数 | 重启生效 | 单条消息最大 Part 数量 |

#### §6.8 Permission ACL 参数（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.4c）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_ACL_ENABLED` | `true` | 见说明约束 | 重启生效 | Permission ACL 总开关 |
| `KAIROS_ACL_DEFAULT_POLICY` | `deny` | 见说明约束 | 重启生效 | 无匹配规则时的默认策略（`deny` / `allow`） |
| `KAIROS_ACL_BOOTSTRAP_PATH` | `config/acl_bootstrap.yaml` | 见说明约束 | 重启生效 | 初始 ACL 规则集文件路径 |
| `KAIROS_ACL_MAX_RULES` | `500` | 见说明约束 | 重启生效 | ACL 规则数量上限（防止规则膨胀影响检查性能） |

#### §6.9 检索递归与 Cross-encoder 参数（[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_RECURSIVE_DEPTH_MAX` | 3 | ≥0 整数 | 重启生效 | 递归路径检索最大深度 |
| `KAIROS_RECURSIVE_SCORE_DIFF_THRESHOLD` | 0.3 | ≥0（按语义标定） | 重启生效 | 递归钻取层间最佳分差阈值 |
| `KAIROS_CROSS_ENCODER_ENABLED` | false | {true,false} | 重启生效 | Cross-encoder 重排序总开关——默认关闭，启用须同时配置 `KAIROS_CROSS_ENCODER_MODEL`（对应 [data-model.md](../specification/data-model.md) `kairos.retrieval.cross_encoder.enabled`） |
| `KAIROS_CROSS_ENCODER_MODEL` | 空（不启用） | 见说明约束 | 重启生效 | Cross-encoder 模型名 |
| `KAIROS_CROSS_ENCODER_TOP_K` | 20 | ≥0 整数 | 重启生效 | Cross-encoder 输入候选数 |
| `KAIROS_CROSS_ENCODER_BATCH_SIZE` | 8 | ≥0 整数 | 重启生效 | Cross-encoder 批处理大小 |
| `KAIROS_BM25_LEMMATIZE` | true | {true,false} | 重启生效 | BM25 词形归并开关 |
| `KAIROS_GRAPH_DISTANCE_ENABLED` | true | {true,false} | 重启生效 | 图谱距离重排序开关 |
| `KAIROS_GRAPH_DISTANCE_MAX_HOPS` | 3 | ≥0 整数 | 重启生效 | 图谱距离最大跳数 |
| `KAIROS_GRAPH_DISTANCE_WEIGHT` | 0.15 | [0,1] | 重启生效 | 图谱距离权重 |
| `KAIROS_CANONICAL_OPS_ENABLED` | true | {true,false} | 重启生效 | 12 规范操作集开关 |
| `KAIROS_CANONICAL_OPS_STRICT_MODE` | false | {true,false} | 重启生效 | 规范操作严格模式 |
| `KAIROS_CLARIFY_ENABLED` | true | {true,false} | 重启生效 | MCP Bridge Clarify 消歧开关 |
| `KAIROS_DEEP_REASONING_MAX_RECURSIVE` | 2 | ≥0 整数 | 重启生效 | Deep Reasoning 递归检索最大轮次 |

### §7 限流与安全配置

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_RATE_LIMIT_WRITE_PER_MIN` | 60 | ≥0 整数 | 重启生效 | 写操作限流（每分钟请求数，单客户端级别）。系统容量 ≥100 ops/s（多客户端并行） |
| `KAIROS_RATE_LIMIT_READ_PER_MIN` | 120 | ≥0 整数 | 重启生效 | 读操作限流（每分钟请求数） |
| `KAIROS_INPUT_LIMIT_CONTENT_BYTES` | 65536 | ≥0 整数 | 重启生效 | content 字段最大长度（字节，64KB 硬上限） |
| `KAIROS_INPUT_LIMIT_QUERY_CHARS` | 500 | ≥0 整数 | 重启生效 | query 字段最大字符数 |
| `KAIROS_SSRF_ALLOWED_HOSTS` | `api.deepseek.com`（示例） | 见说明约束 | 重启生效 | 出站 URL 白名单（逗号分隔）。部署时设为实际使用的 API 域名；`*`=无限制（不推荐生产） |
| `KAIROS_SSRF_IP_CHECK` | `true` | 见说明约束 | 重启生效 | 解析 URL 后二次校验 IP，阻断内网/元数据地址 |
| `KAIROS_SSRF_DNS_REBIND_PROTECTION` | `true` | 见说明约束 | 重启生效 | DNS 重绑定防护（DNS 解析结果与 HTTP 请求时的 IP 不一致时拒绝） |
| `KAIROS_WAL_ARCHIVE_COMMAND` | `cp %p ~/.kairos/wal_archive/%f` | 见说明约束 | 重启生效 | PostgreSQL WAL 归档命令（`%p`=WAL 段路径，`%f`=文件名）。设为空字符串禁用归档 |
| `KAIROS_WAL_ARCHIVE_RETENTION_DAYS` | 7 | ≥0 整数 | 重启生效 | WAL 归档保留天数 |
| `KAIROS_LLM_MAX_COST_PER_CALL_FEN` | 100 | 0~1000 | 运行时生效 | 单次 LLM 调用成本上限（分），超限拒绝该调用 |
| `KAIROS_LLM_CIRCUIT_BREAK_FAILURES` | 5 | ≥1 整数 | 运行时生效 | 连续失败次数阈值，超限熔断该模型（含超时） |
| `KAIROS_LLM_CIRCUIT_BREAK_COOLDOWN_S` | 300 | ≥0 整数 | 运行时生效 | 熔断冷却时长（秒） |
| `KAIROS_LLM_TIMEOUT_S` | 60 | ≥0 整数 | 运行时生效 | LLM 单次调用超时（秒）；轻量模式取 30（见 [reliability.md](reliability.md) §1.5）。超时计入重试次数与熔断统计 |
| `KAIROS_RATE_LIMIT_CIRCUIT_BREAK_OPS` | 500 | ≥0 整数 | 重启生效 | 系统级吞吐熔断阈值（ops/s）——超过后拒绝新请求（S-02 系统容量上限，见 [security-specification.md](../security/security-specification.md) §2.1） |
| `KAIROS_RATE_LIMIT_READ_CAPACITY_OPS` | 200 | ≥0 整数 | 重启生效 | 读操作系统容量（ops/s）——检索吞吐 ≥180 ops/s（200 的 90% 余量，见 [acceptance-criteria.md](../quality/acceptance-criteria.md)） |

### §8 质量属性

（本节参数见 §8.1 表）

### §8.1 见证→使用仲裁参数

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_WITNESS_SURGE_WINDOW` | 10 个调度周期 | ≥1 周期 | 重启生效 | 陡升检测的单位时间窗口 |
| `KAIROS_WITNESS_SURGE_THRESHOLD` | 40% | 见说明约束 | 重启生效 | 窗口内升幅超过此值触发差异检验 |
| `KAIROS_WITNESS_GRADUAL_PERIOD` | 30 个调度周期 | ≥1 周期 | 重启生效 | 渐进式上升连续周期数 |
| `KAIROS_WITNESS_DIFFERENCE_SIMILARITY_THRESHOLD` | 0.6（余弦相似度） | [0,1] | 重启生效 | 语义内核相似度比对阈值，低于此值标记存疑 |
| `KAIROS_WITNESS_ALERT_PERIOD` | 3 个调度周期 | ≥1 周期 | 重启生效 | 检测器持续背离外部校准后发出告警 |

### §8.2 [预留]

### §8.3 检索与蒸馏参数（v0.1.0 交付）

> ⚠️ **废弃声明**：以下 `KAIROS_SEARCH_WEIGHT_*` 变量组出自 v0.1.0 之前的 5D 混合排序**权重框架**（语义+BM25+时序+信任+热度），已被 v0.1.0 的三信号混合检索（§6.1 `KAIROS_HYBRID_*`）替代。时序/信任/热度作为排序调制因子而非独立基础维度，权重由 RL 重排序层（[rl-weight-spec.md](../specification/rl-weight-spec.md)）管理。**新部署请勿引用本节变量，迁移说明见 §6.1。**（口径注记：此处废弃的是 5D **权重参数框架**；「5D 混合排序」作为检索管线排序调制层的沿用名仍保留，见架构 §7.3a 检索管线术语口径——两者不矛盾）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_RETRIEVAL_MIN_QUERY_LENGTH` | 3 | ≥0 整数 | 重启生效 | 检索触发最小 query 长度 |
| `KAIROS_RETRIEVAL_GREETING_PATTERNS` | "hi,hello,thanks,ok" | 见说明约束 | 重启生效 | 问候/噪音模式列表 |
| `KAIROS_CAPTURE_MIN_LENGTH` | 10 | ≥0 整数 | 重启生效 | 捕获最小内容长度 |
| `KAIROS_CAPTURE_CONFIDENCE_FLOOR` | 0.6 | [0,1] | 重启生效 | 蒸馏产物置信度下限 |
| `KAIROS_HEAT_DECAY_ALPHA` | 0.95 | [0,1] | 重启生效 | 热度每日衰减系数 |
| `KAIROS_HEAT_ACCESS_BOOST` | 0.05 | 见说明约束 | 重启生效 | 每次访问热度增量 |
| `KAIROS_SEARCH_WEIGHT_VECTOR` | 0.40 | [0,1] | 重启生效 | 混合排序向量权重 |
| `KAIROS_SEARCH_WEIGHT_BM25` | 0.20 | [0,1] | 重启生效 | 混合排序 BM25 权重 |
| `KAIROS_SEARCH_WEIGHT_TIME` | 0.15 | [0,1] | 重启生效 | 混合排序时间权重 |
| `KAIROS_SEARCH_WEIGHT_RELIABILITY` | 0.10 | [0,1] | 重启生效 | 混合排序可信度权重 |
| `KAIROS_SEARCH_WEIGHT_HEAT` | 0.15 | [0,1] | 重启生效 | 混合排序热度权重 |

### §8.4 身份映射参数（v0.1.0 交付）

`KAIROS_USER_ALIASES` 为 JSON 格式，配置多平台用户 ID 到规范用户 ID 的映射（参数名统一口径见架构 §5.2 跨平台身份映射）：

```json
{
  "cross_platform_shared_scope": true,
  "user_aliases": {
    "telegram:user_123": "canonical_user_123",
    "cli:local": "canonical_user_123"
  }
}
```

仅在 `kairos://_user/` 域下生效。

### §8.5 质量指标

> **表格式说明**：本表为质量指标表（非 `KAIROS_` 参数，不计入参数计数）。

| 指标 | 值 | 属性 |
|:-----|:---|:-----|
| 保守倾向平局率 | ≤ 5% | 上限（超过触发宪法解释层审视） |

### §8.6 P6 维度保护参数（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.11）

P6 禁止不可审计的维度信息丢失。以下参数定义 P6 压缩的硬上限和审计阈值：

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_P6_COMPRESSION_RATIO_HARD_LIMIT` | 0.30 | 见说明约束 | 重启生效 | P6 全局闸门压缩比硬上限（标量综合度量压缩率 ≤30%）。v0.1.0 因从五维规范目标降维至四轴空间运行，累计压缩比（~33–43%）必然超限。超限不改变硬上限的规范效力——受限例外须逐条登记、审计、跟踪。详见 architecture [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.6 及 §10.11 |
| `KAIROS_P6_COMPRESSION_RATIO_WARNING` | 0.20 | ≥0（按语义标定） | 重启生效 | P6 压缩比告警阈值（超过此值记录审计警告，不阻断操作） |
| `KAIROS_P6_ACTIVE_EXCEPTION_RATIO_LIMIT` | 0.50 | [0,1] | 重启生效 | 活跃受控例外占全部操作的比例上限（超过此值自动触发宪法解释层合规审查） |
| `KAIROS_P6_AUDIT_CYCLE_PERIODS` | 10 | ≥1 周期 | 重启生效 | P6 合规审计周期（调度周期数，超限持续超 2 周期触发审查） |
| `KAIROS_PARETO_FRONT_MAX` | 16 | ≥1 整数 | 重启生效 | 帕累托不可支配集的输出规模上限（决策 D-01 方案 B）。前沿规模**未超**此值时全集随裁决结果输出，辞典式排序仅标记默认推荐项；**超过**此值时禁止用优先级链截断前沿求单解——须转 L3 人工确认（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.10）或保守 NO-OP。截断行为触发 `p6_violation` 告警并阻断该次裁决 |
| `KAIROS_PARETO_FRONT_OVERFLOW_ACTION` | `escalate_l3` | 见说明约束 | 重启生效 | 前沿溢出时的处理动作：`escalate_l3`=转人工确认；`conservative_noop`=维持现状不裁决。**不提供** `truncate` 选项——截断即 P6 违规，故不作为可配置行为暴露 |

### §8.7 断点续训与重试参数（架构 [detailed-design.md](../specification/detailed-design.md) §10.5 断点续训）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_CHECKPOINT_ENABLED` | `true` | 见说明约束 | 重启生效 | 断点续训总开关 |
| `KAIROS_CHECKPOINT_MAX_PER_TASK` | `3` | 见说明约束 | 重启生效 | 每任务保留的最大检查点数 |
| `KAIROS_CHECKPOINT_INTERVAL_STEPS` | `1` | 见说明约束 | 重启生效 | 每 N 个步骤写入一次检查点 |
| `KAIROS_RETRY_MAX_ATTEMPTS` | `3` | 见说明约束 | 重启生效 | 瞬时错误最大重试次数 |
| `KAIROS_RETRY_BACKOFF_BASE_MS` | `1000` | 见说明约束 | 重启生效 | 退避基础间隔（毫秒） |
| `KAIROS_RETRY_BACKOFF_MULTIPLIER` | `4` | 见说明约束 | 重启生效 | 退避乘数 |

### §8.8 MCP 与 SDK 参数（架构 [technology-stack.md](../development/technology-stack.md) §七 MCP 与 SDK）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_MCP_ENABLED` | `true` | 见说明约束 | 重启生效 | MCP Server 总开关 |
| `KAIROS_SDK_PYTHON_MIN_VERSION` | `3.10` | 见说明约束 | 重启生效 | Python SDK 最低版本（SDK 为独立交付物，版本要求与后端运行时（3.11–3.13）互不约束，见 [technology-stack.md](../development/technology-stack.md) §七） |
| `KAIROS_SDK_TYPESCRIPT_MIN_VERSION` | `5.0` | 见说明约束 | 重启生效 | TypeScript SDK 最低版本 |
| `KAIROS_SDK_GO_MIN_VERSION` | `1.21` | 见说明约束 | 重启生效 | Go SDK 最低版本 |
| `KAIROS_FILE_GRAPH_MAX_TRAVERSAL_DEPTH` | `3` | 见说明约束 | 重启生效 | 多跳图遍历最大深度 |
| `KAIROS_FILE_GRAPH_CENTRALITY_REFRESH_INTERVAL` | `86400` | 见说明约束 | 重启生效 | 中心性重算间隔（秒，默认 24h） |

### §8.9 告警投递参数（[observability.md](observability.md) §4a）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_ALERT_WEBHOOK_URL` | 空（不启用） | 合法 URL | 重启生效 | 告警投递 Webhook URL（为空则仅日志输出 + 审计事件，见 [observability.md](observability.md) §4a） |
| `KAIROS_ALERT_EMAIL_ENABLED` | false | {true,false} | 重启生效 | 邮件告警投递开关 |
| `KAIROS_ALERT_RETRY_MAX` | 3 | ≥0 整数 | 重启生效 | 告警投递失败最大重试次数 |
| `KAIROS_ALERT_RETRY_BACKOFF_S` | 60 | ≥0 整数 | 重启生效 | 告警投递重试退避间隔（秒） |

### §8.10 磁盘与运维参数（[observability.md](observability.md) §1.1 / [reliability.md](reliability.md) §1.4/§三/§四 / [security-specification.md](../security/security-specification.md) §2.1）

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_DISK_WARN_PCT` | 75 | (0,100] | 重启生效 | 磁盘使用率黄色预警阈值（对应 `kairos_disk_usage_pct` 告警） |
| `KAIROS_DISK_CRIT_PCT` | 85 | (0,100] | 重启生效 | 磁盘使用率红色警戒阈值（暂停非关键写入） |
| `KAIROS_DISK_HARD_PCT` | 92 | (0,100] | 重启生效 | 磁盘使用率崩溃边缘阈值（丢弃临时数据、优雅关闭） |
| `KAIROS_BACKUP_RETENTION_DAYS` | 30 | ≥0 整数 | 重启生效 | 数据库全量备份保留天数（备份目录 ≥75% 时先清理保留期最短的 WAL，见 [reliability.md](reliability.md) §三 容量预算） |
| `KAIROS_LOG_RETENTION_DAYS` | 30 | ≥0 整数 | 重启生效 | 日志文件保留天数（按日轮转，见 [observability.md](observability.md) 暴露协议） |
| `KAIROS_RECOVERY_DRILL_INTERVAL_DAYS` | 30 | ≥0 整数 | 重启生效 | 恢复演练周期（天，默认每月一次，见 [reliability.md](reliability.md) §四） |
| `KAIROS_KEY_GRACE_PERIOD_HOURS` | 1 | ≥0 整数 | 重启生效 | API Key 轮换宽限期（小时）——旧 Key 在宽限期内仍可用（见 [security-specification.md](../security/security-specification.md) §2.1） |

---

### §9 RL 权重优化器参数

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_RL_LEARNING_RATE` | 0.07 | 见说明约束 | 重启生效 | RL 学习率 |
| `KAIROS_RL_DECAY_FACTOR` | 0.97 | [0,1] | 重启生效 | EMA 衰减因子 |
| `KAIROS_RL_MAX_BUFFER_SIZE` | 50 | ≥0 整数 | 重启生效 | 反馈缓冲上限 |
| `KAIROS_RL_WEIGHT_RELEVANCE` | 0.4 | [0,1] | 重启生效 | RL 相关性权重初始值 |
| `KAIROS_RL_WEIGHT_RECENCY` | 0.2 | [0,1] | 重启生效 | RL 新鲜度权重初始值 |
| `KAIROS_RL_WEIGHT_FREQUENCY` | 0.15 | [0,1] | 重启生效 | RL 频率权重初始值 |
| `KAIROS_RL_WEIGHT_USER_FEEDBACK` | 0.15 | [0,1] | 重启生效 | RL 显式反馈权重初始值（用户 👍/👎） |
| `KAIROS_RL_WEIGHT_ENTITY_BOOST` | 0.05 | [0,1] | 重启生效 | RL 实体提升权重初始值（v0.1.0 默认 0.05，v1.1+ 激活完整加权） |
| `KAIROS_RL_WEIGHT_TRUST_SCORE` | 0.10 | [0,1] | 重启生效 | RL 可信度权重初始值 |

### §10 遗忘与检索参数

| 参数 | 默认值 | 取值范围 | 生效时机 | 说明 |
| --- | --- | --- | --- | --- |
| `KAIROS_FORGETTING_HALF_LIFE` | 69 | ≥0 整数 | 重启生效 | 遗忘半衰期（天） |
| `KAIROS_HIGH_FORK_THRESHOLD` | 5 | ≥1 整数 | 重启生效 | structural_value L1 判定——路径高分叉节点子节点数阈值（建议二，架构 §5.2 结构性记忆守护） |
| `KAIROS_STRUCTURAL_CONFIRMED_THRESHOLD` | 5 | ≥1 整数 | 重启生效 | structural_value L1→L2 升级的 causal 引用计数阈值（建议二） |
| `KAIROS_STRUCTURAL_REVIEW_INTERVAL` | 86400 | ≥3600 整数 | 重启生效 | L1→L2 周期审查间隔（秒，后台维护引擎 Deep 模式执行）（建议二） |
| `KAIROS_PRESSURE_WM_OCCUPANCY_THRESHOLD` | 0.8 | [0,1] | 重启生效 | 记忆压力·上下文预算压力——WM 槽位占用率阈值（建议四，架构 §5.2 压力信号族） |
| `KAIROS_PRESSURE_LOW_HIT_RATIO` | 0.3 | [0,1] | 重启生效 | 记忆压力·检索失败压力——24h 窗口低命中率阈值（建议四） |
| `KAIROS_PRESSURE_REDUNDANCY_RATIO` | 0.4 | [0,1] | 重启生效 | 记忆压力·冗余压力——GSPO 聚类命中率阈值（建议四） |
| `KAIROS_PRESSURE_BACKLOG_RATIO` | 2.0 | ≥0 浮点 | 重启生效 | 记忆压力·遗忘积压压力——遗忘队列待评估/24h 已评估比阈值（建议四） |
| `KAIROS_FRESHNESS_ACTIVE_THRESHOLD` | 0.3 | 见说明约束 | 重启生效 | 活跃记忆 freshness 下限 |
| `KAIROS_FRESHNESS_STALE_THRESHOLD` | 0.1 | 见说明约束 | 重启生效 | 归档记忆 freshness 下限 |
| `KAIROS_DOMAIN_KEYWORDS_PATH` | `~/.kairos/domain_keywords.yaml` | 见说明约束 | 重启生效 | 领域知识库路径 |

## 二、运行时动态调整规则

架构中所有可配置参数支持两类调整模式：

| 模式 | 授权者 | 约束 |
|:-----|:-------|:-----|
| **运维静态配置** | 运维/部署者 | 通过环境变量或配置文件设定，重启生效 |
| **元认知层动态调参** | 元认知层治理器族 | 仅在宪法级约束范围内调整，且受元审计子层监测。每秒调参不超过 1 次 |
| **外部校准驱动调整** | 宪法主权面外部校准端口 | 可临时覆盖任意参数值，覆盖有效期随校准信号生命周期 |

**动态调参不变量（任何时候均不得违反）：**
1. 安全红线（S-01~S-19）阈值不可调低
2. 跨层三环不变量（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.3）不可被调参破坏
3. 辞典式排序优先级链不受动态调参影响（受 CONSTITUTIONAL_LOCK_PERIOD 保护）

> **设计约束注记**：「每秒调参不超过 1 次」为设计约束（无外部需求来源）——避免热调参与检索路径竞争。

---

## §11 特征标志默认值

特征标志是编译/注入级的模块隔离机制（参见架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8）。以下为 v0.1.0 定义的默认状态及 Noop 降级行为。

| 标志 | 默认 | 最小系统依赖 | OFF 时行为 |
|:-----|:----:|:-----------|:-----------|
| `KAIROS_FEATURE_MULTI_SIGNAL_SEARCH` | ON | ✅ 核心 | OFF 时退化为纯语义向量检索 |
| `KAIROS_FEATURE_FULL_VALUE_METRICS` | OFF | — | 使用负载追踪返回标量计数（简化为频率统计）；帕累托排序和辞典式裁决器替换为 Noop |
| `KAIROS_FEATURE_FORGETTING_ENGINE` | OFF | — | 遗忘调度器不启动；仅依赖基础 TTL 清理（**竖切内 ON**——单曲线指数衰减遗忘与潜伏势能重估为竖切组件，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 竖切与特征标志） |
| `KAIROS_FEATURE_NARRATIVE_IDENTITY` | ON | ✅ 宪法核 | **此标志为宪法核**——身份面否决权在认知层被定位为不可关闭的宪法级治理面。OFF 仅在最小系统原型阶段合法，正式部署中须为 ON（见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8）。OFF 时身份注册表降级为普通表（写入即固定，永不重评）；身份总线监听器和叙事连贯性检测器不启动 |
| `KAIROS_FEATURE_META_COGNITION` | OFF | — | 元认知检测器族、治理器族不启动。**例外**：叙事连贯性检测器虽物理位于元认知层组件树，其启停由 `NARRATIVE_IDENTITY` 单独控制，本标志 OFF 时仍随宪法核加载（见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 组件归属与门控优先级） |
| `KAIROS_FEATURE_CONSTITUTIONAL_GOVERNANCE` | OFF | ✅ 常驻核部分 | 宪法主权面仅保留外部校准端口；监督平面**扩展能力面**不启动（体系聚合证伪审计器、耦合计监测器、全量决策熵扫描、周期性全量快照比对）。**监督平面常驻核不受本标志门控**——审计庭最小职能与证伪信号路由随系统启动独立加载，存在性不可禁用（见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.7 与 §0.8 组件归属与门控优先级）。**竖切口径**：竖切内额外启用审计庭快照校验/审计日志比对，见 [slice-implementation-guide.md](../development/slice-implementation-guide.md) 组件 6 |
| `KAIROS_FEATURE_WM_PREPROCESSOR` | OFF | — | 候选排序退化为直接权重排列；触发条件匹配和上下文裁剪由 WM 域内联处理 |
| `KAIROS_FEATURE_ATTENTION_SCHEDULER` | OFF | — | 全局注意力调度器不启动；存储域内建固定槽位轮询（每域每周期 N 槽，FIFO，无制衡注入）仍运行 |
| `KAIROS_FEATURE_SUBLIMATION_PIPELINE` | OFF | — | 升华管道不启动；所有记忆保持 raw 状态 |
| `KAIROS_FEATURE_GSPO_DEDUP` | OFF | — | GSPO 去重和 MMR 去重不执行 |
| `KAIROS_FEATURE_ENTITY_GRAPH` | OFF | — | 实体知识图谱和社区检测不加载。三信号检索中的实体加成信号权重（α_e）重新分配给语义和 BM25（**编译期标志级降级**，与运行时退化不同处置，见下方降级细节） |
| `KAIROS_FEATURE_CONNECTORS` | OFF | — | Gmail/Drive/Notion/GitHub 外部连接器同步不加载 |

**实体加成 Noop 降级细节**（`ENTITY_GRAPH=OFF` 时）：`score_entity` 始终返回 0，`norm()` 对单值集返回 [0,1] 线性映射，不报错、不丢精度。三信号公式自动退化为双信号并重新归一化：α_s 从 0.50 升至 0.60，α_b 从 0.35 升至 0.40（权重和恒为 1，分数值域保持 `[0,1]`）。

> **与运行时退化的区分**：本条是**编译期标志级降级**（实体信号不进入融合公式，权重重新归一化）。标志为 ON 但某次查询的候选池实体信号无区分度（`max == min`）时属**运行时退化**——`norm()` 返回 0 且权重**不**重分配，总分整体缩小。两者处置不同，判定顺序为「先看标志、标志 ON 再按查询判退化」，权威定义见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a 退化情形定义。

**注意力调度器降级细节**（`ATTENTION_SCHEDULER=OFF` 时）：固定槽位轮询是存储域内建的最小调度能力，不依赖该标志。每域每调度周期分配固定 N 个处理槽位，FIFO 顺序推进，不做制衡注入、不做优先级重排。调度器标志仅控制独立服务模式下的全局注意力调度器是否启动。

**启动输出预期：** 系统启动时输出 `flags: ON/OFF, count: N/M`。证伪测试（标记 `[FALSIFICATION]`）与功能测试同套件管理，失败时核心假设标志强制关闭。

### §0.10 未闭合风险缓解参数（编号为历史遗留：本节位于 §11 之后）

以下参数对应架构审计确认的 4 项未闭合工程风险，必须在 v0.1.0 首次实现中设定基线值并纳入启动校验。

| 参数 | 默认值 | 风险域 | 说明 |
|:-----|:-------|:-------|:-----|
| `KAIROS_CRI_TASK_SUCCESS_PROXY` | `explicit_feedback` | CRI 任务成功率 | v0.1.0 任务成功率的操作代理：`explicit_feedback`=用户显式肯定（"好""对的""成了"关键词匹配 + 任务完成标记），`implicit_signal`=任务上下文中的正反馈模式识别（对话延续/确认性点头/下一步指令） |
| `KAIROS_CRI_SUCCESS_KEYWORDS` | `["好","对的","没错","可以","完成了","done"]` | CRI 任务成功率 | 显式肯定关键词列表，匹配到任一词即计为一次任务成功信号 |
| `KAIROS_NARRATIVE_AUDIT_CYCLE_MAX` | `5` | 身份否决休眠 | 叙事连贯性审计周期的最大值（调度周期数，单位 5 分钟）。超过此值身份否决权在两次审计之间的空白期超过 25 分钟，削弱其预防性价值。**风险警告**：将此值设为 >12（即 >1 小时）将导致身份否决权在两次审计之间实质失效 |
| `KAIROS_META_EVENT_DROP_MONITOR` | `true` | ME-1/ME-2 故障传播 | 是否启用元认知事件丢弃计数器——由审计庭直接监控（不经 ME-1 路径），记录 `monitor_event_dropped` 事件数的单调度周期变化量。`true`=启用独立计数器，输出至监督平面专用信道 |
| `KAIROS_EXPLORATION_QUALITY_BASELINE` | `0.15` | 探索固定窗口盲区 | 固定窗口（默认 100ms）内探索候选被采纳的比例基线。低于此值说明固定窗口不足以为 P5 提供有效探索——触发告警并建议 v0.1.0.x 缩小窗口或切换至认知状态触发模式 |

**关联风险登记**：以上参数对应的完整风险分析见 [governance/debt-collection.md](../governance/debt-collection.md) 债务 D-024~债务 D-027。首次实现时须将 `KAIROS_NARRATIVE_AUDIT_CYCLE_MAX` 和 `KAIROS_META_EVENT_DROP_MONITOR` 纳入启动校验——未通过则阻断启动。

### §0.11 核心度量代理参数（编号为历史遗留：本节位于 §11 之后）

以下参数承载 [cognitive-foundation.md](../foundation/cognitive-foundation.md) 中三项核心度量的**可操作代理定义**（决策 D-15 方案 A）。三项度量原定义均含不可计算成分（CRI 无权重/窗口、认知完整性含不可知分母、可及性轴无数据源），此处的参数化是使其可实现的最小充分集。

| 参数 | 默认值 | 度量域 | 说明 |
|:-----|:-------|:-------|:-----|
| `KAIROS_CRI_WEIGHTS` | `[0.3, 0.5, 0.2]` | CRI | 依次为注意力熵、有效信息利用率、任务成功率的权重，三者之和须为 1.0（启动校验）。有效信息利用率权重最高（最直接的腐烂证据），任务成功率最低（代理最弱，见 债务 D-024） |
| `KAIROS_CRI_WINDOW_TURNS` | `20` | CRI | 滑动采样窗口的交互轮次数。每调度周期重算一次 CRI |
| `KAIROS_CRI_COLD_START_MIN_TURNS` | `5` | CRI | 冷启动下限——窗口内轮次低于此值时 CRI 强制取 0 且不触发任何降级，避免小样本误降级 |
| `KAIROS_CRI_RENORM_ON_MISSING_SIGNAL` | `true` | CRI | 窗口内无任何任务成功/失败信号时，是否将任务成功率权重置 0 并把其余两项重规范化为 `0.375 / 0.625`。`false`=以 0 值参与计算（会使 CRI 系统性虚高 0.2） |
| `KAIROS_INTEGRITY_WEIGHTS` | `[0.4, 0.3, 0.3]` | 认知完整性 | 依次为反例覆盖度、路径禁区标注密度、组合约束连通性的权重，对应 债务 D-016 公式 `S = 0.4×coverage + 0.3×dead_end + 0.3×connectivity` |
| `KAIROS_ACCESSIBILITY_PROXY_WEIGHTS` | `[0.5, 0.3, 0.2]` | 可及性轴 | 依次为检索命中位次、路径竞争降权幅度、路径密度的权重。合成值仅用于告警与人工审查提示，**不参与遗忘裁决** |

> **代理性质警告**：本节六项参数调节的是**代理指标**而非原度量本身。三项代理各自的认知局限已在 [cognitive-foundation.md](../foundation/cognitive-foundation.md) §1.1（认知完整性闭集分母系统性偏高、可及性轴以结果代理机制）与 §1.9（CRI 弱信号项）中显式声明。调参可改变灵敏度，**不能**消除代理与原定义之间的语义偏离。

> **CRI 触发压缩外部参考值（外部理念吸收 0.0.41；外部实证：Hermes VID-45）**：上下文腐烂驱动的压缩行为参数可参考以下外部实证值——**压缩触发阈值 0.5**（CRI ≥ 0.5 时触发压缩）、**压缩目标 0.2**（压缩至 CRI ≈ 0.2）、**保护最近 20 条**（最近 20 条记忆/轮次豁免压缩，与 `KAIROS_CRI_WINDOW_TURNS` 默认 20 同量级）。v0.1.0 无独立参数承载——CRI 度量参数见本表（§0.11）与 §0.10，压缩执行参数见附录 A `KAIROS_COMPACTION_*` 组；上述三值作为实现期标定参考基线，不改变既有默认值口径（与 detailed-design §4 Compaction 成本-保真三 regime 的验证压缩策略联动）。

---




---

## 附录 A：全库参数总索引（正文未收录部分）

> **用途**：本文正文各节收录 227 项核心参数；全库另有 **147 项** `KAIROS_*` 参数散落在架构、规格、部署、质量等文档中定义，此前无任何集中索引。本附录建立完整映射，使「配置参数入口」名副其实。（附录仅收录正文未定义的参数；计数口径：正文 227 项 + 附录 147 项 = 374 项。）
>
> **权威性**：默认值一栏自各参数的**定义出处**抄录，语义以出处文档为准；出处未给出默认值的标注 `—（待定义）`（共 10 项）。**分类处置（0.0.92 批次，追缴见 [债务 D-431](../governance/debt-collection.md)）**：8 项源头在 architecture-blueprint-v1.1 的 v1.1 域参数（`KAIROS_DERIVED_FROM_MIN_STRENGTH` / `KAIROS_PLAYBOOK_NEGATIVE_THRESHOLD` / `KAIROS_PLAYBOOK_PROMOTION_THRESHOLD` / `KAIROS_PROMPT_DEPENDENCY_STRATEGY` / `KAIROS_SKILL_EXPERIMENTAL_MAX_AGE` / `KAIROS_SUBLIMATION_ENCRYPTION_KEY` / `KAIROS_TEMPORAL_EXTRA_BUFFER_DAYS` / `KAIROS_PATH`（随 detailed-design 实体标签 schema 落地补齐））随对应功能迭代定义，不构成编码启动阻塞；2 项为部署环境变量（`KAIROS_ADMIN_IPS` / `KAIROS_DB_PASSWORD`）部署时点确定，非设计缺口。**竖切（v0.1.0-slice）相关参数无待定义项**。
>
> **维护约定**：新增 `KAIROS_*` 参数须同时登记至本文正文对应章节或本附录，二者取其一，不得只在架构文档中出现。

| 参数 | 默认值 | 定义出处 |
|:-----|:-------|:---------|
| `KAIROS_ADMIN_IPS` | —（待定义） | `ops/deployment.md §三 环境变量` |
| `KAIROS_AGE_DECAY_CONSTANT` | `30 天` | `specification/detailed-design.md` §3 遗忘得分（AGE_DECAY_CONSTANT 默认 30 天） |
| `KAIROS_API_KEY` | —（必填，无默认值） | `ops/deployment.md §三 环境变量` |
| `KAIROS_API_KEY_HASH` | —（必填，轻量模式单 Key 校验场景；文件权限 600） | `security-specification.md §2.1 API Key 生命周期` |
| `KAIROS_AUDIT_HMAC_KEY` | —（必填，无默认值） | `ops/deployment.md §三 环境变量` |
| `KAIROS_BATCH_TRANSACTION_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_BENCHMARK_OFF_BY_ONE_SCORE` | `0.80` | `acceptance-criteria.md §三 时序基准参数` |
| `KAIROS_BENCHMARK_OFF_BY_TWO_SCORE` | `0.50` | `acceptance-criteria.md §三 时序基准参数` |
| `KAIROS_BENCHMARK_SAME_CHAIN_SCORE` | `0.30` | `acceptance-criteria.md §三 时序基准参数` |
| `KAIROS_BENCHMARK_TASK_SCORE_WEIGHTS` | `[0.40, 0.30, 0.20, 0.10]` | `acceptance-criteria.md §三 时序基准参数` |
| `KAIROS_BENCHMARK_TEMPORAL_GRANULARITY` | `day` | `acceptance-criteria.md §三 时序基准参数` |
| `KAIROS_CALIBRATION_CONFLICT_THRESHOLD` | `0.35`（cosine） | `specification/detailed-design.md` §5 校准；单次冲突判定阈值，与正文 `KAIROS_VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD`（连续次数阈值）为同一冲突检测链的两个环节 |
| `KAIROS_CALIBRATION_MERGE_THRESHOLD` | `0.15`（cosine） | `specification/detailed-design.md` §5 校准 |
| `KAIROS_CALIBRATION_SILENT_COUNT` | `6 次` | `specification/detailed-design.md` §5 校准 |
| `KAIROS_CALIBRATION_TIMEOUT` | `300 秒` | `specification/detailed-design.md` §5 校准 |
| `KAIROS_CHUNK_DIFF_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_CHUNK_DIFF_MIN_SAVINGS` | `0.3` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_COMMUNITY_DETECTION_ALGORITHM` | `label_propagation` | `architecture-blueprint-v1.1.md §社区检测（Community Detection）` |
| `KAIROS_COMMUNITY_DETECTION_ENABLED` | `true` | `architecture-blueprint-v1.1.md §社区检测（Community Detection）` |
| `KAIROS_COMMUNITY_MIN_SIZE` | `3` | `architecture-blueprint-v1.1.md §社区检测（Community Detection）` |
| `KAIROS_COMPACTION_ALL_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_COMPACTION_BATCH_SIZE` | `100` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_COMPACTION_FULL_THRESHOLD` | `100,000` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_COMPACTION_KEEP_RECENT` | `5` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_COMPACTION_SLIDING_WINDOW_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_COMPACTION_SUPERSEDED_RATIO` | `0.3` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_CONNECTORS_ENABLED` | `true` | `specification/detailed-design.md §11.2 Connectors 同步模式（Webhook 式自动同步）` |
| `KAIROS_CONNECTORS_MAX_FAILURES` | `5` | `specification/detailed-design.md §11.2 Connectors 同步模式（Webhook 式自动同步）` |
| `KAIROS_CONNECTORS_MAX_RETRIES` | `3` | `specification/detailed-design.md §11.2 Connectors 同步模式（Webhook 式自动同步）` |
| `KAIROS_CONNECTORS_POLL_MIN_INTERVAL` | `60` | `specification/detailed-design.md §11.2 Connectors 同步模式（Webhook 式自动同步）` |
| `KAIROS_CONNECTORS_WEBHOOK_PORT` | `8443` | `specification/detailed-design.md §11.2 Connectors 同步模式（Webhook 式自动同步）` |
| `KAIROS_CONSISTENCY_AUTO_FIX_ENABLED` | `true` | `specification/detailed-design.md §11.5 文件系统-向量索引一致性检查` |
| `KAIROS_CONSISTENCY_DEEP_ENABLED` | `true` | `specification/detailed-design.md §11.5 文件系统-向量索引一致性检查` |
| `KAIROS_CONSISTENCY_HASH_VERIFY_SAMPLE_RATE` | `0.05` | `specification/detailed-design.md §11.5 文件系统-向量索引一致性检查` |
| `KAIROS_CONSISTENCY_INDEX_FRAG_THRESHOLD` | `0.3` | `specification/detailed-design.md §11.5 文件系统-向量索引一致性检查` |
| `KAIROS_CONSISTENCY_LIGHT_ENABLED` | `true` | `specification/detailed-design.md §11.5 文件系统-向量索引一致性检查` |
| `KAIROS_CONSISTENCY_MAX_FIX_PER_CYCLE` | `1000` | `specification/detailed-design.md §11.5 文件系统-向量索引一致性检查` |
| `KAIROS_CORE_LIMIT_BYTES` | `25KB` | `ops/deployment.md §三 环境变量` |
| `KAIROS_CORE_LIMIT_LINES` | `200` | `ops/deployment.md §三 环境变量` |
| `KAIROS_DB_DSN` | `sqlite:///$HOME/.kairos/kairos.db`（轻量模式，与 backup/restore 路径一致） | `ops/deployment.md §三 环境变量` |
| `KAIROS_DB_PASSWORD` | —（待定义） | `ops/deployment.md §三 环境变量` |
| `KAIROS_DEBOUNCE_DEFAULT_AFTER_SECONDS` | `3 秒` | `architecture-v0.1.0.md §2.6.3 防抖反射执行器（Debounced Reflex Executor）` |
| `KAIROS_DEBOUNCE_ENABLED` | `true` | `architecture-v0.1.0.md §2.6.3 防抖反射执行器（Debounced Reflex Executor）` |
| `KAIROS_DEBOUNCE_MAX_CHAIN_CANCELS` | `5，触发告警阈值` | `architecture-v0.1.0.md §2.6.3 防抖反射执行器（Debounced Reflex Executor）` |
| `KAIROS_DERIVED_FROM_MIN_STRENGTH` | —（待定义） | `architecture-blueprint-v1.1.md §四层记忆质量层次（Four-Tier Memory Quality Hierarchy）` |
| `KAIROS_DERIVED_FROM_MIN_VALID_SOURCES_RATIO` | `0.5，有效源低于此比例触发降级` | `architecture-blueprint-v1.1.md §四层记忆质量层次（Four-Tier Memory Quality Hierarchy）` |
| `KAIROS_DERIVED_FROM_REGENERATION_INTERVAL` | `Deep 模式日频` | `architecture-blueprint-v1.1.md §四层记忆质量层次（Four-Tier Memory Quality Hierarchy）` |
| `KAIROS_DISTILLED_MAX_IDLE_DAYS` | `180 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_ENV_MAX_IDLE_DAYS` | `30 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_EVENT_QUEUE_CAPACITY` | `128 条` | `foundation/architecture-v0.1.0.md` §10.10 流控与背压（容量验收下限见 `specification/nfr-specification.md` §二 容量） |
| `KAIROS_EXPLORATION_BUDGET_RATIO` | `0.30`（30%） | `foundation/architecture-v0.1.0.md` §0.9 探索窗口 |
| `KAIROS_EXPLORATION_CLOSURE_MODE` | `fixed_window` | `foundation/architecture-v0.1.0.md` §0.9（v0.1.0 默认固定窗口，v1.1 认知状态触发） |
| `KAIROS_EXPLORATION_GAIN_THRESHOLD` | `0.15` | `architecture-v0.1.0.md §探索窗口关闭判据` |
| `KAIROS_EXPORT_MAX_MEMORIES` | `100000` | `specification/detailed-design.md §11.4 可移植备份格式（.kairos 协议）` |
| `KAIROS_EXPORT_TEMP_DIR` | `/tmp/kairos-export` | `specification/detailed-design.md §11.4 可移植备份格式（.kairos 协议）` |
| `KAIROS_FLAG_CONTRADICTION_JACCARD_THRESHOLD` | `0.7` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FLAG_CONTRADICTION_POLARITY_MODEL` | `使用 LLM 分类` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FLAG_NEEDS_VERIFY_COOLDOWN_DAYS` | `7 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FLAG_NEEDS_VERIFY_DAYS` | `30 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FLAG_NEEDS_VERIFY_WEIGHT_PENALTY` | `0.7` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FORGETAFTER_CASCADE_DELETE` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FORGETAFTER_SCAN_INTERVAL` | `3600 秒，即 Light 模式周期` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FRESHNESS_INFERENCE_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_FTS5_CHINESE_SEGMENTATION` | `true` | `specification/data-model.md §11 全文检索（memories_fts）`——基础 FTS5 contentless-external + unicode61 为 v0.1.0 已交付；jieba 精细分词与 Playbook 全文索引增强归属 v1.1 蓝图 §P3-21。**扩展缺失时的行为（本表为行为权威）**：本参数为 `true` 但 jieba tokenizer 扩展未编译时，启动阶段输出降级告警（日志标记 `fts5_segmentation_fallback`）并回落 `unicode61` 分词，**不阻断启动**；此为可用性降级的 fail-open 且留痕，不属安全校验，不适用 S-01/S-05 的失败关闭纪律。运行时实际生效的分词器须在启动日志与 `GET /health` 响应中可见，避免「配置显示 jieba、实际为 unicode61」的观测失真 |
| `KAIROS_FTS5_ENABLED` | `true` | `specification/data-model.md §11 全文检索（memories_fts）`——基础 FTS5 contentless-external 为 v0.1.0 已交付（轻量模式 BM25 承载，见架构 §7.3a）；jieba 精细分词与 Playbook 全文索引增强归属 v1.1 蓝图 §P3-21 |
| `KAIROS_FTS5_OPTIMIZE_INTERVAL` | `3600` | `specification/data-model.md §11 全文检索（memories_fts）`——基础 FTS5 contentless-external 为 v0.1.0 已交付；jieba 精细分词与 Playbook 全文索引增强归属 v1.1 蓝图 §P3-21 |
| `KAIROS_FTS5_TOKENIZER` | `unicode61` | `specification/data-model.md §11 全文检索（memories_fts）`——基础 FTS5 contentless-external + unicode61 为 v0.1.0 已交付；jieba 精细分词与 Playbook 全文索引增强归属 v1.1 蓝图 §P3-21 |
| `KAIROS_FUSE_GAIN_THRESHOLD` | `0.15` | `specification/detailed-design.md` §1 融合 |
| `KAIROS_FUSE_SUPPRESSION_FACTOR` | `0.3` | `specification/detailed-design.md` §1 融合 |
| `KAIROS_USER_ALIASES` | 见正文 §8.4（JSON 示例） | 本文 §8.4（与正文 §8.4 同一参数；附录收录例外：正文定义但附录保留索引以便检索，注记） |
| `KAIROS_IMPORT_MAX_SIZE_BYTES` | `1073741824` | `specification/detailed-design.md §11.4 可移植备份格式（.kairos 协议）` |
| `KAIROS_IMPORT_TRANSACTION_TIMEOUT` | `600` | `specification/detailed-design.md §11.4 可移植备份格式（.kairos 协议）` |
| `KAIROS_INFERENCE_FALSE_POSITIVE_THRESHOLD` | `0.15` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_INFERENCE_MULTIPLIER` | `1.5` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_INTENT_CLASSIFIER_MODEL` | `./models/intent-t5-small` | `architecture-v0.1.0.md §2.6.1 QueryAnalyzer 查询理解层` |
| `KAIROS_INTENT_CONFIDENCE_THRESHOLD` | `0.6` | `architecture-v0.1.0.md §2.6.1 QueryAnalyzer 查询理解层` |
| `KAIROS_KNN_INCREMENTAL_THRESHOLD` | `100` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_KNN_K` | `10` | `foundation/architecture-v0.1.0.md` §5.2 三链路（k 可配置，默认 10） |
| `KAIROS_LITE_MODE` | `true` | `ops/deployment.md §三 环境变量` |
| `KAIROS_LLM_API_KEY` | —（必填，无默认值） | `ops/deployment.md §三 环境变量` |
| `KAIROS_LLM_ENDPOINT` | —（必填，无默认值） | `ops/deployment.md §三 环境变量` |
| `KAIROS_LOG_LEVEL` | `info` | `ops/deployment.md §三 环境变量` |
| `KAIROS_MEMORY_VERSIONING_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_MEMORY_VERSION_LIMIT` | `50` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_NARRATIVE_COHERENCE_ALERT_THRESHOLD` | `0.4` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_NARRATIVE_COMPLETION_IDLE_DAYS` | `90 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_NARRATIVE_MAX_MEMORIES_PER_THREAD` | `100` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_NARRATIVE_THREADS_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_ONDEMAND_MAX_IDLE_DAYS` | `90 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_PATH` | —（待定义） | `specification/detailed-design.md §9.3 四级规则引擎（L3 字典匹配：NER 实体标签命名空间 kairos://，非 OS 环境变量；默认值待 detailed-design 实体标签 schema 落地后补齐）` |
| `KAIROS_PLAYBOOK_NEGATIVE_THRESHOLD` | —（待定义） | `architecture-blueprint-v1.1.md §过程知识 Playbook 系统（Procedural Playbook System）` |
| `KAIROS_PLAYBOOK_PROMOTION_THRESHOLD` | —（待定义） | `architecture-blueprint-v1.1.md §过程知识 Playbook 系统（Procedural Playbook System）` |
| `KAIROS_PROFILE_CONFIDENCE_THRESHOLD` | `0.3` | `specification/detailed-design.md §11.3 可配置 Profile Schema（Configurable Profile Schema）` |
| `KAIROS_PROFILE_MAX_FIELDS` | `30` | `specification/detailed-design.md §11.3 可配置 Profile Schema（Configurable Profile Schema）` |
| `KAIROS_PROFILE_REFRESH_INTERVAL_HOURS` | `24` | `specification/detailed-design.md §11.3 可配置 Profile Schema（Configurable Profile Schema）` |
| `KAIROS_PROFILE_SCHEMA_ID` | `general-v1` | `specification/detailed-design.md §11.3 可配置 Profile Schema（Configurable Profile Schema）` |
| `KAIROS_PROMPT_DEPENDENCY_STRATEGY` | —（待定义） | `architecture-blueprint-v1.1.md §P3-15 Prompt 依赖关系图` |
| `KAIROS_QUERY_ANALYSIS_CACHE_TTL` | `300 秒` | `architecture-v0.1.0.md §2.6.1 QueryAnalyzer 查询理解层` |
| `KAIROS_QUERY_ANALYZER_ENABLED` | `true` | `architecture-v0.1.0.md §2.6.1 QueryAnalyzer 查询理解层` |
| `KAIROS_RETRIEVAL_LINK_WEIGHTS` | `{"semantic": 0.50, "cooc": 0.20, "knn": 0.10, "causal": 0.20}` | `architecture-v0.1.0.md §5.2 链路融合与检索扩展（唯一权威）` |
| `KAIROS_SALT` | —（必填，无默认值） | `ops/deployment.md §三 环境变量` |
| `KAIROS_SCHEDULER_INTERVAL` | `300s` | `ops/deployment.md §三 环境变量` |
| `KAIROS_SCHEMA_STRICT_MODE` | `true` | `foundation/architecture-blueprint-v1.1.md §P3-23 Schema 前向版本保护` |
| `KAIROS_SCHEMA_VERSION` | `编译时常量` | `foundation/architecture-blueprint-v1.1.md §P3-23 Schema 前向版本保护` |
| `KAIROS_SEARCH_DEFAULT_LIMIT` | `5` | `ops/deployment.md §三 环境变量` |
| `KAIROS_SECRET_KEY` | —（必填，无默认值） | `ops/deployment.md §三 环境变量` |
| `KAIROS_SEED_PATH` | `~/.kairos/seeds/` | `user-guide.md §3.4 种子锚点` |
| `KAIROS_SKILL_ARCHIVE_DAYS` | `180 天` | `architecture-blueprint-v1.1.md §技能管理系统（Skill Management System）` |
| `KAIROS_SKILL_DEPRECATION_INACTIVE_DAYS` | `90 天` | `architecture-blueprint-v1.1.md §技能管理系统（Skill Management System）` |
| `KAIROS_SKILL_EXPERIMENTAL_MAX_AGE` | —（待定义） | `architecture-blueprint-v1.1.md §技能管理系统（Skill Management System）` |
| `KAIROS_SKILL_PROMOTION_MIN_CONTEXTS` | `2` | `architecture-blueprint-v1.1.md §三级技能进化（Skill Evolution）` |
| `KAIROS_SKILL_PROMOTION_MIN_RATE` | `0.7` | `architecture-blueprint-v1.1.md §技能管理系统（Skill Management System）` |
| `KAIROS_SKILL_PROMOTION_MIN_SUCCESS` | `10` | `architecture-blueprint-v1.1.md §三级技能进化（Skill Evolution）` |
| `KAIROS_SKILL_PROMOTION_MIN_USAGE` | `5` | `architecture-blueprint-v1.1.md §技能管理系统（Skill Management System）` |
| `KAIROS_SQLCIPHER_ENABLED` | `false` | `foundation/architecture-blueprint-v1.1.md §P3-20 SQLCipher 静态加密` |
| `KAIROS_SQLCIPHER_KDF_ITER` | `256000` | `foundation/architecture-blueprint-v1.1.md §P3-20 SQLCipher 静态加密` |
| `KAIROS_SQLCIPHER_KEY` | `—（必填，启用时）` | `foundation/architecture-blueprint-v1.1.md §P3-20 SQLCipher 静态加密` |
| `KAIROS_SQLCIPHER_PAGE_SIZE` | `4096` | `foundation/architecture-blueprint-v1.1.md §P3-20 SQLCipher 静态加密` |
| `KAIROS_STMT_CACHE_ENABLED` | `true` | `foundation/architecture-blueprint-v1.1.md §P3-22 PreparedStatementCache——96 条 LRU 缓存管理` |
| `KAIROS_STMT_CACHE_HIT_RATE_ALERT` | `0.80` | `foundation/architecture-blueprint-v1.1.md §P3-22 PreparedStatementCache——96 条 LRU 缓存管理` |
| `KAIROS_STMT_CACHE_SIZE` | `96` | `foundation/architecture-blueprint-v1.1.md §P3-22 PreparedStatementCache——96 条 LRU 缓存管理` |
| `KAIROS_SUBLIMATION_ENCRYPTION_KEY` | —（待定义） | `architecture-blueprint-v1.1.md §P3-14 远程/本地双模式升华` |
| `KAIROS_SUBLIMATION_MODE` | `remote` | `architecture-blueprint-v1.1.md §P3-14 远程/本地双模式升华` |
| `KAIROS_SYMBOLIC_COMPRESSION` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_SYMBOLIC_DEFAULT_LAYOUT` | `TD` | `foundation/architecture-blueprint-v1.1.md §P3-24 Symbolic Memory——Mermaid Canvas 节点图可视化` |
| `KAIROS_SYMBOLIC_ENABLED` | `true` | `foundation/architecture-blueprint-v1.1.md §P3-24 Symbolic Memory——Mermaid Canvas 节点图可视化` |
| `KAIROS_SYMBOLIC_MAX_NODES` | `200` | `foundation/architecture-blueprint-v1.1.md §P3-24 Symbolic Memory——Mermaid Canvas 节点图可视化` |
| `KAIROS_SYMBOLIC_RENDER_FORMAT` | `svg` | `foundation/architecture-blueprint-v1.1.md §P3-24 Symbolic Memory——Mermaid Canvas 节点图可视化` |
| `KAIROS_TEAMSCOPE_ENABLED` | `true` | `foundation/architecture-blueprint-v1.1.md §P3-17 TeamScope 多租户隔离` |
| `KAIROS_TEMPORAL_APPLY_THRESHOLD` | `0.7` | `architecture-blueprint-v1.1.md §事实新鲜度元数据（Fact Freshness Metadata）` |
| `KAIROS_TEMPORAL_BUCKET_COUNT` | `8` | `architecture-v0.1.0.md §2.6.2 时间覆盖均匀采样（Temporal Coverage Uniform Sampling）` |
| `KAIROS_TEMPORAL_CANDIDATE_POOL_SIZE` | `50` | `architecture-v0.1.0.md §2.6.2 时间覆盖均匀采样（Temporal Coverage Uniform Sampling）` |
| `KAIROS_TEMPORAL_ENTRY_POINTS` | `10` | `architecture-v0.1.0.md §2.6.2 时间覆盖均匀采样（Temporal Coverage Uniform Sampling）` |
| `KAIROS_TEMPORAL_EXPIRY_ENABLED` | `true` | `architecture-blueprint-v1.1.md §事实新鲜度元数据（Fact Freshness Metadata）` |
| `KAIROS_TEMPORAL_EXTRA_BUFFER_DAYS` | —（待定义） | `architecture-blueprint-v1.1.md §事实新鲜度元数据（Fact Freshness Metadata）` |
| `KAIROS_TEMPORAL_SAMPLING_ENABLED` | `true` | `architecture-v0.1.0.md §2.6.2 时间覆盖均匀采样（Temporal Coverage Uniform Sampling）` |
| `KAIROS_TEMPORARY_MAX_TTL` | `7 天` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_TIMESTAMP_BATCH_SIZE` | `32` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_TIMESTAMP_MODEL_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_TIMESTAMP_MODEL_PATH` | `./models/timestamp-t5-small` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_VARIABLE_HEALING_ENABLED` | `true` | `architecture-v0.1.0.md §4.4 变量愈合（Variable Healing）` |
| `KAIROS_VARIABLE_HEALING_HARD_FAIL` | `true——愈合失败时阻止注入` | `architecture-v0.1.0.md §4.4 变量愈合（Variable Healing）` |
| `KAIROS_VARIABLE_HEALING_MAX_BACKFILL_CHARS` | `100` | `architecture-v0.1.0.md §4.4 变量愈合（Variable Healing）` |
| `KAIROS_VERSION_CHAIN_ENABLED` | `true` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_VERSION_CHAIN_MAX_LENGTH` | `50` | `architecture-v0.1.0.md §5.2 组件` |
| `KAIROS_WORLD_MODEL_MIN_CLASSES` | `3` | `architecture-blueprint-v1.1.md §三级技能进化（Skill Evolution）` |
| `KAIROS_WORLD_MODEL_MIN_SUCCESS` | `5` | `architecture-blueprint-v1.1.md §三级技能进化（Skill Evolution）` |

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 配置参数参考：约 176 项参数与运行时动态调整规则。 |
| 0.0.2 | 2026-08-03 | 核定正文参数为 186 项；新增附录 A 全库参数总索引（148 项，含定义出处与默认值），全库参数总数 334 项；修正「本文非完整枚举」的口径声明。 |
| 0.0.3 | 2026-08-03 | 新增 §0.11 核心度量代理参数（6 项，承载 D-15 方案 A 的 CRI / 认知完整性 / 可及性轴可操作代理定义）；正文参数 186→194 项，全库总数 334→342 项，同步 README 与 implementation-map 计数。 |
| 0.0.4 | 2026-08-03 | 废止 `KAIROS_ENTITY_BOOST_*` 三项（RC-03，原 PER_MATCH / MAX / WEIGHT 具名参数）——实体信号已由乘性加成因子统一为加性交集比例，前两项失去语义，第三项与 `KAIROS_HYBRID_ENTITY_WEIGHT` 重复且默认值冲突（0.10 vs 0.15）。实体权重统一由 `KAIROS_HYBRID_ENTITY_WEIGHT`=0.15 单一承载。正文参数 194→191 项，全库总数 342→339 项。 |
| 0.0.5 | 2026-08-04 | 市场理念吸收（2026-08-04 决策）：§6.1 新增 `KAIROS_TIME_FILTER_ENABLED`（时间过滤约束开关，默认 true，false 时检索行为与无时间过滤完全一致）。正文参数 191→193 项，全库总数 339→341 项。 |
| 0.0.6 | 2026-08-04 | 全库深度审计修复——取值范围列修正（PARETO_FRONT_MAX/COMPOSITION_*_WEIGHT/PREDICTOR_ATTRIBUTION_TTL）、三环不变量引用、新增 LLM 成本上限与熔断参数（正文参数 193→196 项，附录 A 148→151 项，全库总数 341→347 项）。 |
| 0.0.7 | 2026-08-04 | 文档职责剥离引用更新（changelog 0.0.9 批次）：§6.2/§6.3/§6.4/§6.6/§8.7/§8.8 的参数来源引用改指承接文档（GSPO/MMR/spaCy/双策略 → detailed-design §9.1-9.4、断点续训 → detailed-design §10.5、MCP/SDK → technology-stack §七）。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：附录去重（正文 210+附录 148=358）、新增 14 项参数（LLM 超时/限流容量/磁盘阈值/运维/告警投递）、待定义回填 12 项、特征标志 NARRATIVE_IDENTITY 默认 ON（宪法核）、历史计数链勘误注记。 |
| 0.0.12 | 2026-08-04 | 门禁盲区闭环批次：勘误注记去历史计数字样（归版本记录），消除陈旧值检查误报。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：虚拟校准触发链换算注记（900s=3 次静默术语口径 vs 联动逻辑 6×300s）；校准冲突阈值双参数（次数 vs cosine）区分注记；5D 权重框架废弃声明加口径注记；KAIROS_FORGETTING_SCORE_THRESHOLD 归属勘误（v1.1 口径，v0.1.0 用 freshness 三阈值）。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次（changelog 0.0.15）：**当前核定值锚定行**——正文 210 项 + 附录 A 148 项 = 全库总数 358 项（历史计数链见上方 0.0.2~0.0.11 各条目，现值以本行为准）。 |
| 0.0.16 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.16，建议一/二/四落地）：新增 10 项参数——校准衰减 3 项（DECAY_LAMBDA/DECAY_FLOOR/AUTO_DORMANT_DAYS）、structural_value 3 项（HIGH_FORK/CONFIRMED_THRESHOLD/REVIEW_INTERVAL）、记忆压力 4 项（WM_OCCUPANCY/LOW_HIT_RATIO/REDUNDANCY_RATIO/BACKLOG_RATIO）。 |
| 0.0.22 | 2026-08-05 | 外部项目理念吸收批次（changelog 0.0.22）：§6 新增 3 项参数——噪音规则库层开关（INGEST_NOISE_FILTER_ENABLED）、摄入侧情绪爆发关键词表（EMOTIONAL_BURST_KEYWORDS）、摄入侧情绪保护总开关（EMOTIONAL_BURST_PROTECTION_ENABLED）。正文参数 220→223 项，附录 A 148 项不变，全库总数 368→371 项。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次（changelog 0.0.24）：附录 A 引言正文参数计数 210→223（2-02，口径补注 0.0.16/0.0.22 增长链）；「12 项待定义」核验仍准确。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（changelog 0.0.26）：M-01 三环不变量引用 §6/§10.3→§10.3；M-11 附录 A KAIROS_SEED_PATH 来源行号 189→192。 |
| 0.0.28 | 2026-08-06 | 第十轮全库深度审计修复批次（changelog 0.0.28）：附录 A「来源」列 136 处硬行号引用整体废除（C-03/F-01）——改为「文档 §章节」语义引用（含权威落点核查：38 处原引用文档无定义、落点修正至 detailed-design/blueprint 等权威段；KAIROS_PATH 标注待定义）。 |
| 0.0.34 | 2026-08-06 | 第十四轮全库深度审计修复批次（changelog 0.0.34）：`KAIROS_RETRIEVAL_LINK_WEIGHTS` 由「—（待定义）」补填默认值 `{"semantic": 0.50, "cooc": 0.20, "knn": 0.10, "causal": 0.20}`，来源列指向架构 §5.2 链路融合与检索扩展（唯一权威）。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：附录 A「待定义」计数 12→11（0.0.34 已回填 `KAIROS_RETRIEVAL_LINK_WEIGHTS`）；`KAIROS_FEATURE_CONSTITUTIONAL_GOVERNANCE` OFF 行为补竖切例外注记（竖切内监督平面部分启用——审计庭快照校验/审计日志比对，见 slice-implementation-guide 组件 6）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：§11 特征标志补 KAIROS_FEATURE_CONNECTORS（11→12）；KAIROS_SDK_PYTHON_MIN_VERSION 统一 3.10；身份映射参数名统一为 KAIROS_USER_ALIASES；正文 224 + 附录 A 146 = 370 计数核定；附录/§0.10 格式注记；动态调参约束注记。 |
| 0.0.41 | 2026-08-07 | 外部理念吸收落地批次（changelog 0.0.41）：§0.11 补 CRI 触发压缩外部参考值注记（压缩触发阈值 0.5 / 压缩目标 0.2 / 保护最近 20 条，外部实证：Hermes VID-45）——注记形式落地，未新增参数，参数计数不变（正文 224 + 附录 A 146 = 370）。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：KAIROS_BENCHMARK_* 来源列指正（§三）；σ 双用途互注（VAD 告警+权重衰减）；dormant 笔误；附录 USER_ALIASES 收录例外注记。 |
| 0.0.46 | 2026-08-08 | 文档审计修复批次（changelog 0.0.46）：`KAIROS_RETRIEVAL_LINK_WEIGHTS` 来源列与版本记录中小节名「三链路融合与检索扩展」→「链路融合与检索扩展」（唯一权威口径同步）。 |
| 0.0.52 | 2026-08-08 | round22 结构性建议落地批次（changelog 0.0.52）：附录 A 引言「编码启动前须补齐（共 10 项）」自设硬门禁补 D-431 追缴指针（configuration → debt-collection D-431）。 |
| 0.0.64 | 2026-08-08 | round30 全面深度审计修复批次（changelog 0.0.64，补登）：§6.2 补登 `KAIROS_GSPO_MIN_CLUSTER_SIZE`（默认 2，≥2 整数）、§6.9 补登 `KAIROS_CROSS_ENCODER_ENABLED`（默认 false，{true,false}）；附录 A 补登 `KAIROS_EVENT_QUEUE_CAPACITY`（默认 128，来源架构 §10.10）；参数计数 370→373（正文 224→226、附录 A 146→147）。 |
| 0.0.65 | 2026-08-08 | round31 深度审计修复批次（changelog 0.0.65）：附录 A `KAIROS_FTS5_*` 四参数来源改指 v0.1.0 权威（data-model §11 全文检索——基础 FTS5 contentless-external 为 v0.1.0 已交付，jieba 精细分词与 Playbook 索引增强归属 v1.1 蓝图 §P3-21）；附录 A 引言「蓝图 v1.1 参数 v0.1.0 不实现」补 FTS5 基础参数族例外注记。 |
| 0.0.66 | 2026-08-09 | round32 全面深度审计修复批次（changelog 0.0.66）：版本记录补登批次——0.0.64 行（三参数补登 + 计数 373）为前序批次实质变更漏登记，本批补登（governance §4「触及即登记」）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.67 | 2026-08-09 | round33 全面深度审计修复批次（changelog 0.0.67）：§0.2 `KAIROS_VIRTUAL_CALIBRATION_TIMEOUT` 行「触发口径（勘误）」去除过程标记后缀（零版本标记纪律收敛，正文仅描述当前状态）。 |
| 0.0.68 | 2026-08-09 | round34 全面深度审计修复批次（changelog 0.0.68）：附录 A `KAIROS_PATH` 来源列章节引用修正——「§L3」→「§9.3 四级规则引擎（L3 字典匹配）」（L3 为四级规则引擎规则层名，非章节号；detailed-design §9.3 为 spaCy 实体提取章节）。 |
| 0.0.79 | 2026-08-09 | round41 全面深度审计修复批次（changelog 0.0.79）：新增章节导航（一/二/§11/附录 A）；小节标题前多空行收敛。 |
| 0.0.81 | 2026-08-10 | round43 审计修复（见 changelog 0.0.81）|
| 0.0.83 | 2026-08-10 | round45 全面深度审计修复批次（changelog 0.0.83）：KAIROS_FTS5_CHINESE_SEGMENTATION 扩展缺失行为补定义（本表为行为权威）——降级告警 + 回落 unicode61 不阻断启动，属可用性 fail-open 留痕、不适用安全失败关闭纪律，分词器状态须启动日志与 GET /health 可见；详见 changelog 0.0.83 叙述节。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85）：§6.6 新增 `KAIROS_ENTITY_LLM_DISCARD_THRESHOLD`（默认 0.5，实体提取丢弃阈值下界，与 CONFIDENCE_THRESHOLD 构成互斥开区间判定），参数 373→374；详见 changelog 0.0.85 叙述节。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：§0.11 决策 D-15 与附录 A 债务 D-431 补前缀。 |
| 0.0.92 | 2026-08-11 | 定稿收尾批次（changelog 0.0.92）：附录 A 引言 10 项待定义参数分类处置声明（8 项 v1.1 域随功能迭代定义 + 2 项部署时点确定，竖切无待定义项；追缴 D-431 同步分类处置）。 |
