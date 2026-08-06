---
title: Kairos 需求基线
aliases:
  - 需求规格
  - 需求基线
  - requirements-baseline
tags:
  - kairos
  - requirements
  - baseline
created: 2026-07-21
updated: 2026-08-05
last_reviewed: 2026-08-05
status: draft
---

# Kairos 需求基线

> **定位**：将 feature-list（功能清单）、use-cases（使用场景）、nfr-specification（非功能需求）收敛为一份受管的可追踪需求基线。回答「这个系统要做什么、做到什么程度、怎么算做完」。
>
> **读者**：实现者、测试编写者、版本规划者

---

## §0 项目愿景

Kairos 是一个面向 AI Agent 的记忆系统——不是传统数据库，也不是 RAG 中间件，而是一个**携带最小推理回路的认知记忆系统**。

- **给谁用**：AI Agent 开发者（包括未来的自己）
- **解决什么问题**：Agent 的「上下文膨胀 + 检索错配 + 冷热不分 + 自指性失效」
- **成功标准**：Agent 接入 Kairos 后，能在不丢失身份连续性的前提下管理超过 100 万条记忆，检索延迟 <100ms，且系统能自知认知边界
- **v0.1.0 目标**：可运行的核心存储/检索/遗忘闭环 + 他律性降级契约 + 19 条安全红线实现

---

## §1 功能需求

按模块组织，每条含：ID / 描述 / 前置条件 / 后置条件 / 优先级 / 验收标准。

### 1.1 记忆写入

| ID | 描述 | 前置条件 | 后置条件 | 优先级 | 验收标准 |
|:---|:-----|:--------|:--------|:-----:|:--------|
| W-01 | 按路径写入记忆 | 系统运行中、认证通过 | 记忆写入 LTM，返回路径 | P0 | 写入后可被路径前缀检索到 |
| W-02 | 指定契约写入 | 同 W-01 | 记忆按契约类型存储；常驻记忆不受遗忘调度 | P0 | 常驻记忆在 100 轮遗忘周期后仍存在 |
| W-03 | 批量导入 | 系统运行中 | 批量记忆全部写入，失败项记录错误 | P1 | 1000 条导入 ≤30s |
| W-04 | 多模态写入（VAD） | 同 W-01 | 情感元数据与记忆一同存储 | P0 | 检索时可按 VAD 相似度过滤 |
| W-05 | 关系标注 | 同 W-01 | 关系索引建立 | P1 | 可按关系类型检索关联记忆 |
| W-06 | 高信用源豁免 | 来源标记为代码库或手动输入 | 跳过验证环直接写入 item | P1 | 豁免记忆立即可用 |
| W-07 | 敏感信息脱敏 | 内容匹配敏感模式 | 自动打标并脱敏存储 | P0 | 明文不写入持久存储 |

### 1.2 记忆检索

| ID | 描述 | 前置条件 | 后置条件 | 优先级 | 验收标准 |
|:---|:-----|:--------|:--------|:-----:|:--------|
| R-01 | 路径前缀检索 | 路径存在 | 返回该路径下记忆集合 | P0 | P50 ≤20ms |
| R-02 | 语义检索 | 有写入记忆 | 按相似度排序返回 Top-K | P0 | P50 ≤100ms |
| R-03 | 多路径融合 | ≥2 条检索路径同时执行 | 去重融合后返回 | P1 | 交集优先、独有按信息增益准入 |
| R-04 | 按契约过滤 | 同 R-01 | 仅返回指定契约类型的记忆 | P1 | 过滤结果不含非匹配契约 |
| R-05 | 按时间范围检索 | 同 R-01 | 返回指定时间窗口内的记忆 | P1 | 时间窗口边缘精度 ≤1s |
| R-06 | 按情感维度检索 | 有 VAD 元数据 | 按 VAD 相似度返回结果 | P1 | 情感相似度排序正确 |
| R-07 | 按关系检索 | 有关联记忆存在 | 返回与目标记忆存在指定关系的记忆集合 | P1 | 关系类型过滤精准 |
| R-08 | 路径空间浏览（ls/cd/tree） | 系统运行中 | 返回树状目录 | P0 | CLI `kairos tree` 可展开全部路径 |

### 1.3 记忆管理

| ID | 描述 | 优先级 |
|:---|:-----|:-----:|
| M-01 | 更新记忆内容或元数据 | P0 |
| M-02 | 契约类型变更 | P1 |
| M-03 | 显式遗忘标记 | P0 |
| M-04 | 定向遗忘（抑制路径前缀检索性，非删除） | P1 |
| M-05 | 记忆归档 | P2 |
| M-06 | 记忆导出 | P2 |

### 1.4 遗忘与衰减

| ID | 描述 | 优先级 |
|:---|:-----|:-----:|
| F-01 | 遗忘调度器按得分定时扫描 | P0 |
| F-02 | 潜伏势能重估（空闲时触发） | P0 |
| F-03 | 遗忘后悔补偿（复兴加速通道） | P1 |

### 1.5 升华管道

| ID | 描述 | 优先级 |
|:---|:-----|:-----:|
| SF-01 | 空闲自动升华（raw→item→strategy→behavior） | P1 |
| SF-02 | 手动触发升华 | P1 |
| SF-03 | behavior 阶段产物人工审批 | P1 |
| SF-04 | 升华进度查询 | P2 |

### 1.6 校准与治理

| ID | 描述 | 优先级 |
|:---|:-----|:-----:|
| CAL-01 | 外部校准入（REST/CLI 接收校准信号） | P0 |
| CAL-02 | 宪法级偏好管理 | P0 |
| CAL-03 | 强制冻结/解冻 | P0 |
| CAL-04 | 降级模式切换 | P0 |
| CAL-05 | 审计日志查询（含 HMAC 验证） | P0 |
| CAL-06 | 证伪信号查询 | P1 |

### 1.7 系统管理

| ID | 描述 | 优先级 |
|:---|:-----|:-----:|
| A-01 | 健康检查 | P0 |
| A-02 | 配置查看/修改 | P0 |
| A-03 | 调度器状态查询 | P1 |
| A-04 | 冷启动种子注入 | P0 |
| A-05 | 种子状态查看（退化/生命周期） | P1 |
| A-06 | 路径索引重建（手动触发） | P2 |
| A-07 | 数据库迁移 | P0 |

### 1.8 前瞻记忆

> **版本归属**：前瞻记忆为 **v1.1+ 交付**（P2），以 feature-list 标注为准——数据模型与 API 尚未落地（前瞻保持协议见架构 §3.2）。前瞻记忆使用**意图契约**（intention，独立于四类基础契约，不受遗忘调度器评估；意图完成/取消后降级为按需），见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.2 前瞻记忆段与 [data-model.md](data-model.md) `memories.contract`。竖切（v0.1.0-slice）范围不含前瞻记忆。

| ID | 描述 | 优先级 |
|:---|:-----|:-----:|
| PM-01 | 前瞻意图创建 | P2（v1.1+） |
| PM-02 | 前瞻意图完成/取消 | P2（v1.1+） |

---

## §2 非功能需求

从 [nfr-specification.md](nfr-specification.md) 整合，每条可测量。

| ID | 指标 | 目标值 | 测量方法 |
|:---|:-----|:------|:---------|
| N-01 | 写延迟 P50 | ≤50ms | 基准测试 |
| N-02 | 写延迟 P95 | ≤200ms | 基准测试 |
| N-03 | 路径前缀检索 P50 | ≤20ms | 基准测试 |
| N-04 | 语义检索 P50 | ≤100ms | 基准测试 |
| N-05 | 标准模式容量 | ≥100 万条记忆 | 压力测试 |
| N-06 | 轻量模式容量 | ≥10 万条记忆 | 压力测试 |
| N-07 | 单元测试覆盖率 | ≥80% | `pytest --cov`（nfr-spec 无对应条目，本表补充） |
| N-08 | 安全红线测试覆盖 | 19/19 条 | 逐条验证 |
| N-09 | RTO（自动恢复） | ≤30s | 故障注入测试 |
| N-10 | RPO（数据丢失窗口） | ≤5 分钟 | 写入→崩溃→恢复→验证（nfr-spec 可用性表已增补 RPO 条目，本表与之对齐） |
| N-11 | 系统可用性 | ≥99.9%（v0.1.0 设计目标，适用于有进程级恢复的部署；单进程无守护模式不承诺，见 [deployment.md](../ops/deployment.md) 三级部署梯度） | 运行期可用性监控（滚动窗口 SLO 统计） |
| N-12 | 降级可用性 | ≥99%（外部校准中断期间） | 运行期可用性监控（滚动窗口 SLO 统计） |

---

## §3 约束与假设

- **运行环境**：Python ≥3.11，支持 SQLite（轻量模式）/ PostgreSQL+pgvector（标准/全量模式）
- **部署模型**：单进程常驻后台服务，非分布式
- **外部依赖**：Embedding 模型（标准模式 text-embedding-3-small 1536 维，轻量模式 BGE-M3 1024 维线性投影至 1536——DDL 以 1536 为准）、LLM（可选，用于校准）
- **非目标**：不提供多 Agent 通信、不提供分布式一致性、不提供用户管理（0.0.14 边界注记：不含对外用户管理（注册/登录/权限控制）；内部用户维度承载——跨平台身份映射（identity_mapper，implementation-map §七）与用户画像（user_profiles 表，rl-weight-spec §持久化）属系统内部结构，不构成用户管理能力）
- **安全假设**：本地部署以文件系统权限为第一道防线；API Key 为第二道

---

## §4 需求追踪矩阵（RTM）

需求 ID → 设计章节 → API 端点 → 测试用例。以下为竖切（v0.1.0-slice）需求追踪矩阵；竖切外功能待相应迭代补全。

| 需求 ID | 设计章节 | API 端点 | 测试用例（[test-plan.md](../quality/test-plan.md)） |
|:--------|:--------|:---------|:------------------------|
| W-01 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3 | `POST /v1/memories` | TC-W01-001~003 |
| W-02 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.1 | `POST /v1/memories`（contract 参数） | TC-W02-001 |
| R-01 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 路径空间 | `GET /v1/path` | TC-R01-001~003 |
| R-02 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 向量空间 | `POST /v1/memories/search`（语义检索） | TC-R02-001~002 |
| R-03 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4.2 | `POST /v1/memories/search`（多路径融合，含语义+全文检索） | TC-R03-001~002 |
| R-08 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1 | `GET /v1/path/tree`、CLI `kairos tree` | TC-R01-003 |
| R-18 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a | 三信号混合检索（竖切组件 3，由 R-02 语义检索承载——0.0.14 补充 RTM 行，对齐 feature-list 竖切注记与 implementation-map 竖切组件 3） | TC-R02-001~002、TC-R03-001~002 |
| W-03 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 多源摄取 | `POST /v1/memories/batch` | 代码启动后补充 |
| W-04 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 情感效价空间 | VAD 元数据字段 | TC-W04-001 |
| W-07 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8（S-07） | 写入自动打标 + 加密存储 | TC-W07-001 |
| M-01 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 更新 | `PATCH /v1/memories/{id}` | 代码启动后补充 |
| M-03 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 遗忘调度器 | `DELETE /v1/memories/{id}`（软删除） | 代码启动后补充 |
| M-05 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 归档 | `POST /v1/memories/{id}/archive` / `POST /v1/memories/{id}/restore`（api-spec §1.5，0.0.15 注册） | 代码启动后补充 |
| F-01 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 遗忘调度器 | 自动调度 | TC-F01-001 |
| F-02 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 潜伏势能重估 | `latent_trigger` 事件 + 手动触发 | TC-F02-001 |
| F-03 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §5 复兴加速 | 自动（潜伏势能重估/外部校准触发，0.0.14 勘误：非检索触发） | TC-F03-001 |
| CAL-01 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 | `POST /v1/calibrate` | TC-CAL01-001 |
| CAL-03 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 | `POST /v1/freeze` | TC-CAL03-001 |
| CAL-04 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.9 | `POST /v1/degradation/switch` | TC-CAL04-001 |
| CAL-05 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.7 | `GET /v1/audit-log` | E2E-06 |
| A-01 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7 | `GET /health`（存活探针）、`GET /v1/health/detail`（聚合健康报告） | 代码启动后补充 |
| A-02 | [configuration.md](../ops/configuration.md) | `GET/PATCH /v1/config` | 代码启动后补充 |
| A-04 | 架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §2.2 种子 | `POST /v1/seeds` | 代码启动后补充 |
| A-07 | [deployment.md](../ops/deployment.md) | CLI `kairos db migrate` | 代码启动后补充 |

> 预留用例编号：W-05/W-06、R-04~R-07、M-04、SF-01~04、CAL-02/06 等核心功能对应测试用例编号（TC-W05-001~ 等）待代码启动后补充，编号规则见 [test-plan.md](../quality/test-plan.md)，补充时须与 RTM 一一对应，避免编号冲突（TC-C01 前缀已废弃）。

> 竖切范围外的功能（升华/前瞻/定向遗忘/导出/Connectors 等）待相应迭代补全 RTM。

---

## §5 版本边界

### v0.1.0 设计覆盖

- 六层 + 监督平面骨架
- 双副本分离（见证锚定 + 使用权重）
- 四契约（常驻/按需/环境/临时）
- 路径空间优先检索（`kairos://`）
- 升华管道骨架（raw→item→strategy→behavior，空闲驱动）
- 他律性降级契约（三模式状态机）
- 19 条安全红线 + HMAC 审计链
- CLI 完整命令集
- 轻量 / 标准 / 全量三级梯度

### v0.1.0 暂不覆盖（推迟至 v1.1+）

- 逻辑-因果轴完整落地（D-301）
- 动态身份增强（D-302）——身份构造论基础（初始赋予 + 叙事驱动双向更新）已入竖切；核心/外围差异化降级门槛仍为 v1.1
- 能力转化状态机（D-303）
- ~~定向遗忘机制（D-304）~~（已闭环，见 debt-collection DC-027；v0.1.0 范围以 feature-list M-04 为准）
- 四轴完整度量函数（D-306）
- 元记忆偏置正反馈闭合（D-307）
- 外部校准源充分性建模（D-305）
- 社会性校准认知框架（D-308，v2.0）
- 多 Agent 协议（D-309，v1.2）

### v0.1.0-slice（竖切，2026-07-31 决策）

竖切范围见 feature-list「竖切范围」标注：核心存储/检索/遗忘（含潜伏势能重估）/身份（构造论）/校准/审计闭环。存储后端 SQLite 优先（ADR-001 实施顺序）；事件总线首迭代 4 类（架构 §10.10）。竖切外能力保持「冻结」状态，随迭代启用。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 需求基线：功能需求/NFR/约束/部署规模/RTM 与版本边界。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：PM-01/02 版本归属修正为 P2（v1.1+，对齐 feature-list，竖切不含前瞻记忆）；RTM CAL-01 测试用例编号 TC-C01-001 → TC-CAL01-001（对齐 test-plan 新命名）。 |
| 0.0.3 | 2026-08-04 | 全库深度审计修复：N-07/N-10 补 nfr-spec 无对应条目注记、RTM 补预留用例编号说明块、W-02 端点列修正。 |
| 0.0.4~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.4~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：N-10 注记同步 nfr-spec；补 N-11/N-12 可用性指标；PM 意图契约说明。 |
| 0.0.11~0.0.13 | 2026-08-04 | （合并占位：changelog 0.0.11~0.0.13 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：RTM 补 R-18 行（竖切组件 3）；F-03 复兴触发勘误；非目标「用户管理」边界注记。 |
| 0.0.15 | 2026-08-05 | 全面深度审计修复批次（changelog 0.0.15，补登）：api-spec 定稿注册 archive/restore 端点（§1.5，竖切功能 M-05）——RTM M-05 行标注原应同步而未同步，正文修正见 0.0.24 条目。 |
| 0.0.16~0.0.23 | 2026-08-05 | （合并占位：changelog 0.0.16~0.0.23 批次无涉及本文的变更，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次（changelog 0.0.24）：RTM R-01/R-02 设计章节列引用 §4.2→§5 路径空间/向量空间（1-03，对齐 feature-list）；M-05 端点标注改 api-spec §1.5 注册端点（2-01）；§1.8 前瞻记忆段引用改指 §3.2（1-08 联动）；RTM「arch」缩写统一为「架构」（22 行，4-04）。 |
