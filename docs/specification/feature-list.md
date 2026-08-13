---
title: Kairos 功能清单
aliases:
  - 功能清单
  - Feature List
tags:
  - kairos
  - design
  - requirements
created: 2026-07-20
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 功能清单

> **状态声明**：本文列出的能力总数为设计就绪状态下的近似值（**168 项，含 43 核心 + 125 扩展**；最终计数见文末「最终计数」表）。竖切范围内能力已实现（REST/CLI/MCP/Agent Tool 落点见 [implementation-map.md](implementation-map.md) 与 [slice-implementation-guide.md](../development/slice-implementation-guide.md)）；竖切范围外状态标记为`冻结`——表示**设计已固化、架构规划已完成，代码尚未编写（非"已实现"）**。

> **定位**：从外部视角枚举 Kairos 系统对外提供的全部能力。架构文档按「层」组织，本清单按「能力」组织——是数据模型、接口规格和测试策略的输入锚点。
>
> **读者**：实现者、测试编写者、集成方
>
> **验收标准声明**：本文列出的 168 项功能当前无逐项验收标准。验收标准在代码实现阶段逐项补充，纳入 [quality/acceptance-criteria.md](../quality/acceptance-criteria.md)。本文仅定性列功能、对应架构组件和状态标记。

> **竖切范围（v0.1.0-slice，2026-07-31 决策）**：以下功能进入首迭代最小竖切（架构 §0.8 最小系统 + 构造论身份模型 + 4 类事件总线 + SQLite 优先）。其余功能保持「冻结」状态，随迭代启用。

| 分类 | 竖切功能 |
|:-----|:--------|
| 记忆写入 | W-01, W-02, W-03, W-04, W-07 |
| 记忆检索 | R-01, R-02, R-03, R-08（**R-18 三信号混合检索为竖切组件**——语义检索 R-02 即其载体，见 [project-plan.md](../governance/project-plan.md) §一 组件行与 [implementation-map.md](implementation-map.md) 竖切组件 3；下表检索类扩展功能标注的 Phase 1 以竖切标注为准） |
| 记忆管理 | M-01, M-03, M-05 |
| 遗忘与衰减 | F-01, F-02, F-03 |
| 校准与治理 | CAL-01, CAL-03, CAL-04, CAL-05 |
| 系统管理 | A-01, A-02, A-04, A-07 |
| 横切 | 事件总线 4 类（use_event/calibration_signal/degradation_switch/latent_trigger）、身份注册表（构造论）、审计 HMAC 链、双副本分离、19 条安全红线单元测试 |

---

> **章节导航**：一 记忆写入 · 二 记忆检索 · 三 记忆管理 · 四 升华管道 · 五 遗忘与衰减 · 六 前瞻记忆 · 七 校准与治理 · 八 系统管理 · 九 扩展功能

## 一、记忆写入

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| W-01 | 按路径写入记忆 | 在指定路径下创建一条记忆，自动分配默认契约 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 摄取 |
| W-02 | 指定契约写入 | 写入时显式指定契约类型（常驻/按需/环境/临时） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 使用契约 |
| W-03 | 批量导入 | 从文件或管道批量导入记忆 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 多源摄取 |
| W-04 | VAD 情感元数据写入 | 写入时附带情感 VAD 元数据 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 情感效价空间 |
| W-05 | 关系标注 | 在记忆写入时标注关系类型（causal / independent / hierarchical / competitive / part_whole / derived_from 六种，详见 [data-model.md](data-model.md) `memory_relations` 表——`hierarchical` 对应认知基础「弱层级关系」） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 关系索引 |
| W-06 | 高信用源豁免 | 来自代码库或用户手动输入的写入可跳过验证环 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 高信用源豁免 |
| W-07 | 敏感信息脱敏 | 含敏感信息的写入自动打标并脱敏 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8（S-07） |

## 二、记忆检索

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| R-01 | 路径前缀检索 | 按 kairos:// 路径前缀查询记忆集合 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 路径空间 |
| R-02 | 语义检索 | 按内容语义相似度检索（向量搜索） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 向量空间 |
| R-03 | 多路径融合 | 同时走多条检索路径后汇聚结果 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4.2 汇聚式多路径融合 |
| R-04 | 按契约过滤 | 仅检索指定契约类型的记忆 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 契约过滤 |
| R-05 | 按时间范围过滤 | 检索指定时间窗口内的记忆 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a 时间过滤约束 |
| R-06 | 情感维度（VAD）加权检索 | VAD 条件激活的排序权重提升通道（非独立检索轴，cos≥0.5 时注入，默认忽略情感维度） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 预测器（情感基线提升通道） |
| R-07 | 按关系检索 | 检索与某记忆存在指定关系的记忆集合 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 关系索引 |
| R-08 | 路径空间浏览 | 树状浏览路径空间（ls/cd/tree） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1 CLI 接口 |

## 三、记忆管理

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| M-01 | 记忆更新 | 更新现有记忆的内容或元数据 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 更新（补充/修正/重构） |
| M-02 | 契约变更 | 更改记忆的契约类型 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 契约层 |
| M-03 | 显式遗忘 | 主动标记一条记忆为遗忘候选 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 遗忘调度器 |
| M-04 | 定向遗忘 | 抑制特定路径前缀的记忆可检索性（非删除） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 检索路径抑制器 |
| M-05 | 记忆归档 | 将低价值记忆移至归档存储 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 归档 |
| M-06 | 记忆导出 | 导出记忆为可移植格式 | [api-spec.md](api-spec.md) §1.5 GET /v1/memories/{id}/export |

## 四、升华管道

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| SF-01 | 空闲触发升华 | 系统空闲时自动执行升华（raw→item→strategy→behavior） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 升华管道 |
| SF-02 | 手动触发升华 | 用户手动触发指定路径下的升华 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 升华管道 |
| SF-03 | 升华产物审批 | strategy→behavior 阶段的产出需人工确认 | [cognitive-foundation.md](../foundation/cognitive-foundation.md) §D.8 升华门控 |
| SF-04 | 升华进度查询 | 查看当前升华阶段和进度 | [api-spec.md](api-spec.md) §1.8 GET /v1/sublimation/status |

## 五、遗忘与衰减

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| F-01 | 自动遗忘调度 | 按遗忘得分定时扫描并处理候选遗忘对象 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 遗忘调度器 |
| F-02 | 潜伏势能重估 | 空闲时重估零使用价值记忆的保留价值 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 潜伏势能重估 |
| F-03 | 遗忘后悔补偿 | 被遗忘记忆经潜伏势能重估端口（盲区/前向关联命中）或外部校准触发复兴（复兴加速通道）——显式检索仅更新 last_access_at，不直接触发复兴（勘误，对齐架构 §5.2 状态转换表） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 潜伏复兴加速 |

## 六、前瞻记忆

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| PM-01 | 前瞻意图创建 ⏳ v1.1+ | 写入未来意图记忆至 `kairos://_system/intentions/`，使用**意图契约**（intention——独立契约类型，激活优先级低于常驻但高于按需，不受遗忘调度器评估；完成/取消后降级为按需，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 前瞻记忆段与 [data-model.md](data-model.md) `memories.contract`）。**版本归属按能力粒度切分**：v0.1.0 落地契约层承载——`contract` 枚举值 `intention` 及其保护语义（不受遗忘调度器评估）见 [data-model.md](data-model.md) `memories.contract`，删除守卫（409 `ERR-CTR-004` 意图契约未关闭）见 [api-spec.md](api-spec.md) §1.5；v1.1+ 承载意图创建专用端点与 WM 触发条件匹配（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 前瞻保持协议当前为架构就绪状态） | §4 WM调度预处理器 + [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 前瞻保持跨层协调协议 |
| PM-02 | 前瞻意图完成/取消 ⏳ v1.1+ | 意图完成或取消时标记为 `resolved`，降级为普通按需记忆。v0.1.0 首迭代（竖切）实现 4 类事件（use_event/calibration_signal/degradation_switch/latent_trigger），并已落地删除守卫（未关闭意图直接删除返回 409 `ERR-CTR-004`，见 [api-spec.md](api-spec.md) §1.5）；intention_activate/intention_resolve 事件待对应组件启用时按架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.6 事件类型注册门禁实现，完整生命周期管理归 v1.1 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4 WM调度预处理器生命周期管理 |

## 七、校准与治理

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| CAL-01 | 外部校准入 | 接收外部校准信号并更新见证锚定 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 外部校准端口 |
| CAL-02 | 宪法级偏好管理 | 查看和修订宪法级偏好声明 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 宪法修订端口 |
| CAL-03 | 强制冻结/解冻 | 冻结/解冻所有内部环 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 强制冻结机制 |
| CAL-04 | 降级模式切换 | 手动切换外部校准降级模式（保守静默/受限交叉验证/安全休眠） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.9 降级状态机 |
| CAL-05 | 审计日志查询 | 查询审计日志（含 HMAC 验证） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.7 监督平面（审计庭） |
| CAL-06 | 证伪信号查询 | 查询耦合计监测器/VAD 测试器/体系聚合审计器的输出 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 证伪响应 |

## 八、系统管理

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| A-01 | 健康检查 | 返回系统各组件的健康状态 JSON | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 安全红线（健康检查） |
| A-02 | 配置查看/修改 | 查看和动态修改可配置参数 | [ops/configuration.md](../ops/configuration.md)（参数参考） |
| A-03 | 调度器状态查询 | 查看调度器运行状态（升华/遗忘/重估） | [api-spec.md](api-spec.md) §1.8 GET /v1/scheduler/status |
| A-04 | 冷启动种子注入 | 首次运行时注入种子锚点 | [cognitive-foundation.md](../foundation/cognitive-foundation.md) §B.2 种子价值源 |
| A-05 | 种子状态查看 | 查看种子锚点的退化状态 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.2 种子生命周期 |
| A-06 | 路径索引重建 | 手动触发路径索引重建 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 路径重建 |
| A-07 | 数据库迁移 | 执行数据库 schema 迁移 | [ops/deployment.md](../ops/deployment.md) |

### 功能分类统计（核心 43 项）

| 分类 | 数量 | 关键功能 |
|:----|:----:|:---------|
| 记忆写入 | 7 | 按路径/契约/批量/多模态/关系标注 |
| 记忆检索 | 8 | 路径/语义/多路径/过滤/情感/关系 |
| 记忆管理 | 6 | 更新/契约变更/显式遗忘/定向遗忘/归档/导出 |
| 升华管道 | 4 | 空闲触发/手动触发/产物审批/进度查询 |
| 遗忘与衰减 | 3 | 自动调度/潜伏重估/复兴补偿 |
| 前瞻记忆 | 2 | 意图创建/意图完成取消 |
| 校准与治理 | 6 | 外部校准/宪法管理/冻结/降级/审计/证伪 |
| 系统管理 | 7 | 健康检查/配置/调度/种子/重建/迁移 |
| **总计（核心）** | **43** | — |


## 九、扩展功能

> **范围说明**：以下 125 项扩展能力中，仅 43 项核心能力在 [references/traceability-map.md](../references/traceability-map.md) 有认知声明映射；扩展能力的声明映射待 v1.1 补充（与 traceability-map 一致）。

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| M-07 | 冗余合并 | 余弦相似度 > 0.92 的记忆自动合并，保留高热，软删低热 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 后台维护引擎·Light |
| M-08 | 热度衰减 | 记忆 heat_score 按日衰减 α=0.95，访问增量 Δ=0.05 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 后台维护引擎·Light |
| M-09 | 噪声清理 | 临时契约中超 TTL 且未被查询的记忆自动清除 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 后台维护引擎·Light |
| R-10 | 时间序检索 | 纯时间轴排序，与热度解耦（sort=created_at） | [api-spec.md](api-spec.md) §1.2 记忆检索（sort 参数） |
| R-11 | 实体图谱检索 | 按实体查询关联记忆，支持多跳图遍历 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 实体知识图谱 |
| R-12 | 分块检索 | 长文本分块后逐块检索，结果去重 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 长文本分块引擎 |
| W-08 | 实体自动提取 | 写入时 LLM 自动提取实体并写入知识图谱 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 实体知识图谱 |
| W-09 | 冲突检测写入 | 写入时检测语义冲突/重复，返回合并/覆盖/新建建议 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §5.6 新信息冲突解决 |
| W-10 | 三区写入 | 记忆按 hall 字段写入加工区，自动触发蒸馏→验证→归档 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.10 知识加工区 |
| W-11 | 纠正自动检测 | 检测用户否定/改写/隐式纠正，自动触发差异检验 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.4 用户纠正自动检测 |
| SF-05 | 会话历史保留 | 完整对话消息持久化，跨会话可查询 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 对话历史持久化 |
| SF-06 | 加工区→验证区推进 | 蒸馏完成后自动推进记忆至验证区 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.10 加工→验证闸机 |
| SF-07 | 验证区退回加工区 | 差异检验不通过时退回加工区重新蒸馏 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.10 退回回流 |
| SF-08 | 自适应蒸馏调度 | 基于周活跃度动态调整蒸馏批次和触发阈值 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 升华管道·自适应调度 |
| H-01 | MCP Bridge 接入 | 15 个 MCP 工具供 Hermes Agent 直接调用（基础工具集 12 + 关系管理 3，见 [api-spec.md](api-spec.md) §6.8） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a MCP Bridge |
| H-02 | Memory Provider | 6 个生命周期钩子自动监听代理事件 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a Hermes Memory Provider |
| H-03 | 热度预取 | on_turn_start 预取高热度记忆注入 WM | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a Memory Provider hook |
| A-08 | 后台维护触发 | 手动触发 Light/Deep 维护模式 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 后台维护引擎 |
| A-09 | 维护状态查看 | 查询维护引擎运行历史和指标 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 后台维护引擎 |
| A-10 | 端云同步推送 | 本地增量修改推送到服务端 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.11 端云同步协议 |
| A-11 | 端云同步拉取 | 从服务端拉取增量变更 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.11 端云同步协议 |
| A-12 | 数据快照导出 | 导出 .kairos 格式便携快照 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.11 快照导入导出 |
| A-13 | 数据快照导入 | 导入 .kairos 格式数据 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.11 快照导入导出 |
| T-01 | 模型路由梯队 | 按成本/能力分层调用 LLM，自动升降级 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.9 模型路由梯队 |
| T-02 | 双层语义缓存 | LLM 结果 + Embedding 双重缓存 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.9 双层语义缓存 |
| T-03 | RL ε-greedy 探索 | 随机扰动权重防止局部最优 | [rl-weight-spec.md](rl-weight-spec.md) §权重优化器实现 |
| T-04 | RCW 多源加权 | 按来源类型分配奖励贡献权重 | [rl-weight-spec.md](rl-weight-spec.md) §权重优化器实现 |
| T-05 | KPop 稳定性监测 | KL 散度超阈值触发额外衰减 | [rl-weight-spec.md](rl-weight-spec.md) §权重优化器实现 |
| T-06 | Cosine LR 调度 | 余弦退火学习率，后期防震荡 | [rl-weight-spec.md](rl-weight-spec.md) §权重优化器实现 |
| M-10 | 状态机五态 | Active→Stale→Archived→Suppressed→Superseded 五态平级全生命周期（无子态） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 记忆状态机 |
| M-11 | 状态变更跟踪 | 每次状态转换写入 memory_states 表 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 记忆状态机 |
| M-12 | 社区检测 | 对实体关系图自动聚类为社区，支持社区级检索和摘要 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（社区检测） |
| M-13 | 临时事实智能过期 | 自动检测记忆中的时间指示，到期自动清理 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（事实新鲜度元数据） |
| M-14 | 记忆版本管理 | Update 自动保留内容快照，支持版本历史查询和回滚 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 记忆版本管理 |
| R-13 | 知识演化链查询 | 按记忆 ID 查询 replaces/enriches/confirms/challenges | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 知识演化追踪 |
| R-14 | 分块差分索引 | Update 操作只 embedding 新行，不变行保留向量 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 长文本分块引擎·差分同步 |
| R-15 | 时序知识图谱 | 实体关系带 valid_from/valid_to，支持 as_of 时间点查询 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 实体知识图谱·时序查询 |
| R-16 | 关系失效与替代 | invalidate/supersede 操作，版本化实体关系 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 实体知识图谱·时序查询 |
| R-17 | 实体检索加成 | 查询实体匹配候选关联实体→第 6 维加权（v1.1+ 激活完整加权时参与排序） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a 实体加成 |
| PL-01 | Playbook 创建 | 升华 strategy 阶段自动产出结构化 playbook candidate | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（过程知识 Playbook 系统） |
| PL-02 | Playbook 搜索 | 按 task_class/title/steps 全文检索 + 语义混合搜索 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（过程知识 Playbook 系统） |
| PL-03 | Playbook 反馈 | 使用后记录 outcome，自动更新 confidence 和状态 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（过程知识 Playbook 系统） |
| PL-04 | Playbook 状态机 | candidate→needs_review→reviewed→promoted→superseded | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（过程知识 Playbook 系统） |
| PL-05 | 三级技能进化 | L1 Traces→L2 Policies→L3 World Model→Skills | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（三级技能进化） |
| PL-06 | World Model 规则 | 跨 task_class 稳定模式自动沉淀为 world_model_rules | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（三级技能进化） |
| W-12 | 捕获门控增强 | 12 种 skip pattern + secret regex + trivial + hard_max | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 摄取验证门禁·捕获门控 |
| A-15 | Recall Funnel | 检索 trace 结构化（stage counts + timings + scoring） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 检索轨迹可视化 / [api-spec.md](api-spec.md) §6.7 |
| A-16 | Freshness 报告 | fact_freshness 覆盖度/过期/需验证统计 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（事实新鲜度元数据）/ [data-model.md](data-model.md) §8.6 |
| A-17 | 主动话题 | Deep 模式生成四种 proactive topics，on_turn_start 注入 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 主动话题生成器 |
| A-18 | 检索轨迹可视化 | 意图分析→定位→钻取→聚合全程记录，事件总线标记 retrieval_trajectory | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 检索轨迹可视化 |
| A-19 | Cross-encoder 重排序 | 5D 排序后 cross-encoder 逐对精确重排 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 Cross-encoder 重排序 |
| A-20 | 图谱距离重排序 | 按候选在图谱中与查询实体的距离加权排序 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 图谱距离重排序 |
| SF-09 | 自反思元记忆优化 | 自反思循环提炼 add/update/delete 元记忆原则 | [detailed-design.md](detailed-design.md) §10.3 |
| SF-10 | 提示词优化 | Gradient/Meta-Prompt/Prompt Memory 三种策略优化系统提示词 | [detailed-design.md](detailed-design.md) §10.4 |
| SF-11 | 多提示词信用分配 | 识别问题提示词，仅优化导致性能下降的提示词 | [detailed-design.md](detailed-design.md) §10.4 |
| SF-12 | Reflect 按需深度分析 | 用户触发、LLM 分析现有记忆形成新洞察并写入加工区 | [api-spec.md](api-spec.md) §6.4 POST /v1/reflect |
| SF-13 | 符号化压缩 | LLM 中间输出（搜索结果/代码/错误追踪）自动生成结构化摘要 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 符号化压缩 |
| SYS-01 | Journal 暂存写入 | 原始对话先入 journal_buffer（立即返回），后台异步 digest 后写入 memories | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 journal 双重隔离写入 |
| SYS-02 | 上下文块管理 | memory_blocks 表管理结构化上下文块，支持独立 token_limit/read_only | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4 上下文块系统 |
| SYS-03 | 上下文块版本历史 | memory_block_versions 表支持块编辑历史查询和 diff/revert | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4 上下文块系统 |
| SYS-04 | Token 预算分解 | 编译前按来源（blocks/semantic/path/entity/recent/reserved）分解 token 预算 | [detailed-design.md](detailed-design.md) §10.1 |

### Phase 1 新增

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| R-18 | 三信号混合检索 | 语义 + 自适应 BM25 + 实体加成三路加权融合（0.50/0.35/0.15） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a |
| R-19 | GSPO 聚类去重 | 同源同域高相似记忆几何均值压缩，CV>0.15 激活 | [detailed-design.md](detailed-design.md) §9.1 |
| R-20 | MMR 去重 | GSPO 后 MMR λ=0.5 贪心去重（跨源语义冗余） | [detailed-design.md](detailed-design.md) §9.2 |
| R-21 | 四链路图谱扩展 | 语义 + Entity 共现 + Semantic kNN + Causal 四链并行扩展，融合权重 0.50/0.20/0.10/0.20（语义/共现/kNN/因果，架构 §5.2 检索扩展链路） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| R-22 | 编译管线敏捷检索 | 编译时注入双模检索（Fast <10ms + Deep 按需） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3d |
| M-15 | 技能管理系统 | skills 表 + find_skills 语义搜索 + 六态生命周期 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（技能管理系统） |
| M-16 | MemCube 四层分化 | textual/activation/parametric/preference 四层记忆 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（MemCube 四层记忆分化） |
| M-17 | 四层记忆质量层次 | mental_models>observation>experience>world 检索优先级 1.00/0.75/0.50/0.25 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（四层记忆质量层次） |
| M-18 | 组件注册表 | 运行时类型化组件注册 + 优先级回退 + 五态生命周期 | 横切组件 |
| SF-14 | 编译管线上下文组装 | 四阶段（采集→分类渲染→注入元数据→哈希缓存）多源上下文组装 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4.3 |
| SF-15 | 编译管线降级模式 | 4 级降级（full→structured→attributes→empty） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4.3 |
| SF-16 | Reflect agentic 循环 | tool-calling 循环（recall/search_observations/search_mental_models/done，max 10 轮）替代线性 Reflect | [detailed-design.md](detailed-design.md) §4.1 |
| SF-17 | 双模检索 | Fast Context（embedding+路径 <10ms）+ Deep Reasoning（LLM 按需唤醒） | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3d |
| A-21 | L0/L1 写入分层 | append-only L0 日志 + 异步 L1 提取，L0 写入不等待 L1 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.4c |
| A-22 | 背景/新消息分段 LLM | 单次 LLM 调用完成背景摘要 + 新消息联合提取 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.4d |
| T-07 | 自适应 BM25 | k1/b 参数根据查询长度和实体密度动态调整 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a |

### Phase 2 新增

| 编号 | 功能 | 说明 | 对应架构组件 |
|:----|:-----|:-----|:------------|
| M-19 | Flag 系统 | needs_verify（30天无演化链）+ contradiction（Jaccard>0.7+极性相反）主动告警 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| M-20 | 版本链模型 | parentMemoryId/rootMemoryId/nextVersionId/isLatest 四字段 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| M-21 | Saga 叙事线 | narrative_threads 表。**v0.1.0 子集：创建/添加记忆/按叙事线检索/手动完结四操作（纯 DB 无 LLM），端点见 [api-spec.md](api-spec.md) §8；summarize_thread() 与自动聚合/自动完结为 v1.1 目标** | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| M-22 | Mental Model 可刷新 | DERIVED_FROM 关系追踪 + 源变化触发 re-generation | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §一（四层记忆质量层次） |
| M-23 | 可配置 Profile Schema | 声明式 Schema + 5 预设模板 + L4 蒸馏刷新 | [detailed-design.md](detailed-design.md) §11.3 |
| R-23 | QueryAnalyzer | 三阶段（意图5类→实体5类型→时间6种）理解层 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.6.1 |
| R-24 | 时间覆盖采样 | 8 对数桶→10 入口点均匀覆盖算法 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.6.2 |
| R-25 | 时间戳后处理 | 小模型独立后处理（<100M），主流程解耦 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| R-26 | Episode 归因索引 | 批量摄取 episode_indices → node_episode_index_map | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| R-27 | 时间覆盖检索 | 8桶→10入口点，QueryAnalyzer 联动 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.6.2 |
| R-28 | ADD-only 提取 | linked_memory_ids + Observation Date 锚定，叠加非替代 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3g |
| SF-18 | 防抖反射执行器 | 同 thread_id 新提交自动取消旧任务 + after_seconds 延迟 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.6.3 |
| SF-19 | 双模式 Compaction | sliding_window 增量 + all 全量 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| SF-20 | 变量愈合 | 变量注册表 + 三策略回填 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4.4 |
| W-13 | 资源摄取 | add_resource file/URL/sitemap/RSS + watch_interval（**v0.1.0 交付**，与 api-spec §18.2 多模态 Part 的 v0.1.0 档位一致，见 §18.1） | [api-spec.md](api-spec.md) §18.1 |
| W-14 | spaCy 实体提取 | 非 LLM NER 4 规则 + 150+ 过滤词 | [detailed-design.md](detailed-design.md) §9.3 |
| W-15 | ADD-only 提取协议 | 叠加非替代，linked_memory_ids 溯源 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3g |
| A-23 | Connectors 同步 | Gmail/Drive/Notion/GitHub webhook + 轮询兜底 | [detailed-design.md](detailed-design.md) §11.2 |
| A-24 | 关系管理 API | link/unlink/relations 三工具 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a MCP Bridge |
| A-25 | forgetAfter 过期 | temporary 契约到期硬删除，级联清理 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| A-26 | 12 规范操作集 | CRUD + merge/fork/archive/restore/purge/link/unlink | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 |
| A-27 | 半开区间时间 | [valid_from, valid_to) 严格上界 + supersede() | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5.2 |
| A-28 | freshness 自动过期 | last_access_at 三级判定：30d/90d/180d | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| A-29 | 任务感知评分 | 四维综合（时序40%+置信30%+关系20%+适配10%），off-by-one 容忍 | [detailed-design.md](detailed-design.md) §10.2 |

### 功能分类更新

| 分类 | 原数量 | 新增 | 新数量 |
|:----|:-----:|:----:|:-----:|
| 记忆写入 | 7 | +8 (W-08~W-15) | 15 |
| 记忆检索 | 8 | +19 (R-10~R-28) | 27 |
| 记忆管理 | 6 | +17 (M-07~M-23) | 23 |
| 升华管道 | 4 | +16 (SF-05~SF-20) | 20 |
| 遗忘与衰减 | 3 | +1 (A-25 forgetAfter) | 4 |
| 前瞻记忆 | 2 | 0 | 2 |
| 校准与治理 | 6 | 0 | 6 |
| 系统管理 | 7 | +20 (A-08~A-29，其中 A-14 为未使用编号、A-25 计入「遗忘与衰减」) | 27 |
| Hermes 集成 | — | +3 (H-01~H-03) | 3 |
| 模型能力 | — | +3 (T-01/T-02/T-07) | 3 |
| RL 优化 | — | +4 (T-03~T-06) | 4 |
| Playbook | — | +4 (PL-01~PL-04) | 4 |
| 技能进化 | — | +2 (PL-05/PL-06) | 2 |
| 系统基建 | — | +4 (SYS-01~SYS-04) | 4 |
| **小计（不含 Phase 3 长期储备）** | **43** | **+101** | **144** |

> **计数口径**：上表为**小计**，仅统计 Phase 0~2 的 144 项；叠加下方 Phase 3 长期储备 24 项后，全量为 **168 项**（见 §最终计数）。引用本文件功能总数时请以 168 为准，勿取本表的 144。
>
> **未使用编号**（已登记，不得回收复用）：`A-14`、`R-09`、`P3-18`。
>
> **分类口径注记**：功能分类共 **14 类** = 核心 8 类（上表）+ 扩展 6 类（Hermes 集成 / 模型能力 / RL 优化 / Playbook / 技能进化 / 系统基建）——README 与版本记录「14 类 168 项」即此口径。

### Phase 3 新增（长期技术储备）

| 编号 | 名称 | 说明 | 来源 |
|:----|:----|:----|:----|
| P3-01 | 实体抽取双策略 | LLM 优先 JSON + 关键字降级（前缀词典 Trie + spaCy） | [detailed-design.md](detailed-design.md) §9.4 |
| P3-02 | .kairos 备份协议 | 自包含 ZIP（manifest + NDJSON + .npy 向量 + SHA-256）三级冲突 | [detailed-design.md](detailed-design.md) §11.4 |
| P3-03 | 一致性检查 | 8 维检查（C1-C8），Light/Deep/On-demand 三模式 | [detailed-design.md](detailed-design.md) §11.5 |
| P3-04 | 多模态 Part 接口 | TextPart/ImagePart/ToolPart 统一 Schema（**v0.1.0 子集交付**：文本/图片 data URI/URL/工具 Part，见 api-spec §18.2；音频/文件等扩展 Part 为 P3 长期储备） | [api-spec.md](api-spec.md) §18.2 |
| P3-05 | 断点续训 | 检查点持久化 + 指数退避重试 + 7 参数 | [detailed-design.md](detailed-design.md) §10.5 |
| P3-06 | 用户画像性能基准 | P50≤50ms/P99≤200ms，LRU 缓存+预热降级 | [detailed-design.md](detailed-design.md) §10.6 |
| P3-07 | 三 SDK 战略 | MCP + Python/TS/Go 三语言 | [technology-stack.md](../development/technology-stack.md) §七 |
| P3-08 | GLiNER2 本地 NER | 205M CPU 模型，三段管线 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| P3-09 | 事实三元组注入 | POST /v1/facts bypass LLM | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| P3-10 | 边类型签名验证 | source/target label 约束，strict/warn 模式 | [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 |
| P3-11 | Directives 系统 | Reflect 前注入 + compliance YAML 追踪 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-11 |
| P3-12 | malloc_trim 管理 | glibc heap 释放 + RSS 防泄漏 | 规格待 v1.1 细化（当前无具体设计文本） |
| P3-13 | Webhook 框架 | 订阅/投递/重试三表 + HMAC-SHA256 | [api-spec.md](api-spec.md) §1.8 POST /v1/webhooks |
| P3-14 | 远程/本地升华 | 远程执行 API（L2→L4） | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-14 |
| P3-15 | Prompt 依赖图 | SOUL.md 修改→通知关联 Skill | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-15 |
| P3-16 | GraphRAG + Rust Core | petgraph/PyO3 + Louvain 检测 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-16 |
| P3-17 | TeamScope 多租户 | team_id + user_id 双层跨 host | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-17 |
| P3-19 | File Graph 深层能力 | 反向链接/多跳/孤立检测/中心性 | [technology-stack.md](../development/technology-stack.md) §七 |
| P3-20 | SQLCipher 加密 | AES-256-CBC page 全库加密 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-20 |
| P3-21 | FTS5 全文搜索 | contentless-external 模式（基础 FTS5 + unicode61 为 v0.1.0 轻量模式 BM25 承载，见架构 §5.20.2；jieba 为需编译扩展的可选精细中文分词，由 `KAIROS_FTS5_CHINESE_SEGMENTATION` 控制） | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-21 |
| P3-22 | PreparedCache 96 条 | LRU 逐出 + SHA256 键 + 读写锁 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-22 |
| P3-23 | Schema 版本保护 | 硬拒绝高版本 DB（exit 75） | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-23 |
| P3-24 | Symbolic Memory | Mermaid Canvas 节点图，200 节点上限，交互展开/过滤/样式映射 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-24 |
| P3-25 | Permission ACL | read/write/admin 三权 + whitelist/blacklist 继承链 | [architecture-blueprint-v1.1.md](../foundation/architecture-blueprint-v1.1.md) §P3-25 |

### 最终计数

| 合计 | 核心 | 扩展 | 总计 |
|:----|:----:|:----:|:----:|
| P0（当前修补） | 0 | +61 | 61 |
| P1（v1.1 迭代） | 0 | +16 | 16 |
| P2（v1.1+ 增强） | 0 | +24 | 24 |
| P3（长期储备） | 0 | +24 | 24 |
| **总计** | **43** | **+125** | **168** |

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 功能清单：14 类 168 项对外能力（43 核心 + 125 扩展）。 |
| 0.0.2~0.0.42 | 2026-08-07 | （合并占位：changelog 0.0.2~0.0.42 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.61 | 2026-08-08 | 版本记录补登（changelog 0.0.61）：M-10 记忆状态机口径由「含子态 Suppressed」修正为五态平级全生命周期（active/stale/archived/suppressed/superseded，无子态），与架构 §5.2 一致（前序批次实施、漏登记于本文档版本记录，本批补登）。 |
| 0.0.72 | 2026-08-09 | round36 全面深度审计修复批次（changelog 0.0.72）：H-02/H-03 引用落点 §7.3→§7.1a（Hermes Memory Provider 权威定义在 §7.1a，0.0.26 批次仅修 H-01 同源遗漏 H-02/H-03）；P3-21 FTS5 口径补注（基础 unicode61 为 v0.1.0 轻量模式承载，jieba 为可选扩展，对齐 0.0.62 批次）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.73 | 2026-08-09 | round37 全面深度审计修复批次（changelog 0.0.73）：引用落点批量修正 9 行——R-05 时间索引→§7.3a 时间过滤约束（架构无「时间索引」节点）、R-10 时间序检索→api-spec §1.2（架构无「向量空间·时间序」，接口承载补全）、W-09 冲突检测→blueprint §5.6（§5.5 差异检验语义错配）、M-12 社区检测→blueprint §一（架构 §5.2 无此节点）、M-13/A-16 事实新鲜度→blueprint §一（架构 §5.2 无此节点）、A-15 Recall Funnel→架构 §7.3（架构 §5.2 无此节点）、M-16 MemCube→blueprint §一（架构无 MemCube）、M-22 Mental Model→blueprint §一（架构无 mental_model 承载）、A-24 MCP Bridge→§7.1a（权威定义处）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.79 | 2026-08-09 | round41 全面深度审计修复批次（changelog 0.0.79）：新增分节导航（一~九）。 |
| 0.0.80 | 2026-08-09 | round42 全面深度审计修复批次（changelog 0.0.80）：引用/口径收口 + 格式收尾 + 术语登记（glossary 70→76）——详见 changelog 0.0.80 叙述节。 |
| 0.0.81 | 2026-08-10 | round43 审计修复（见 changelog 0.0.81）|
| 0.0.83 | 2026-08-10 | round45 全面深度审计修复批次（changelog 0.0.83）：PM-01/PM-02 意图契约版本归属改能力粒度切分——v0.1.0 落地契约枚举值 + 保护语义 + DELETE 守卫（409 ERR-CTR-004），意图生命周期端点与 intention_activate/resolve 事件归 v1.1+；与 requirements-baseline §1.8 / data-model / api-spec 契约层已落地事实对齐；详见 changelog 0.0.83 叙述节。 |
| 0.0.88 | 2026-08-10 | round50 全面深度审计修复批次（changelog 0.0.88）：Phase 2 引用落点修正 4 处——R-23 QueryAnalyzer §2.1→§2.6.1、R-24 时间覆盖采样 §2.1→§2.6.2、R-27 时间覆盖检索 §2.1→§2.6.2、SF-18 防抖反射执行器 §2.1→§2.6.3（架构关联组件实际章节；§2.1 为元认知层定位）。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：版本记录节归位文末并升为 ## 层级（原嵌于八/九之间）。 |
| 0.0.93 | 2026-08-11 | round53 全面深度审计修复批次（changelog 0.0.93）：文末补结尾换行符（deep-audit 捕获，格式类）；frontmatter updated/last_reviewed 同步 2026-08-11。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |



---
