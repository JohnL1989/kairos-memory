---
title: Kairos 操作目录
aliases:
  - 操作目录
  - Operation Catalog
tags:
  - kairos
  - design
  - api
created: 2026-07-22
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 操作目录

> **定位**：将架构文档各处的 API 端点、Agent Tool、MCP Bridge 工具、CLI 命令汇聚为统一的显式操作清单。按三阶段（编码/检索/存储治理）组织，每操作标注安全红线、契约约束和 P6 合规状态。
>
> **与 [api-spec.md](api-spec.md) 的关系**：操作目录是"系统能做什么"的外部视角——按意图而非按协议组织。[api-spec.md](api-spec.md) 是"怎么调用"的协议层细节。两份文档互补不冲突。

---

## 一、编码阶段（ENC）

记忆的创建和摄入。

| 操作ID | 操作 | 映射端点 | 工具（AgentTool/MCP 来源见 api-spec §6） | 安全红线 | 契约支持 | P6 合规 |
| --- | --- | --- | --- | --- | --- | --- |
| OP-001 | 按路径写入 | POST /v1/memories | memories_write | S-03（长度）/S-09（注入）/S-15（来源） | permanent/ondemand/environmental/temporary | 条件激活（P6 受控例外） |
| OP-002 | 批量写入 | POST /v1/memories/batch | — | S-03/S-09 | 逐条独立 | ✅ |
| OP-003 | 三区写入 | POST /v1/memories + hall | — | S-03/S-09/S-17（结构反例） | 默认 ondemand | ✅ |
| OP-004 | 实体自动提取 | 写入时自动触发 | kairos_extract_entities | S-15 | — | ✅ |
| OP-005 | 冲突检测写入 | 写入时自动触发 | — | S-14（语境自指禁令） | — | ⚠️ 压缩~33–43%（v0.1.0 已知超限、非受控偏离——归属注记：此超限为**维度降维**（认知完整性/可及性轴降维）的系统级性质，非冲突检测操作自身所致，见 [system-context.md](system-context.md) §二 假设表与架构 §0.6/§10.11） |
| OP-006 | 会话消息同步 | POST /v1/sessions/{id}/messages | — | S-15 | — | ✅ |
| OP-007 | 校准信号注入 | POST /v1/calibrate | kairos_calibrate | S-11（唯一入口） | — | ✅ |

## 二、检索阶段（RET）

记忆的查询和召回。

| 操作ID | 操作 | 映射端点 | 工具 | 安全红线 | 说明 |
| --- | --- | --- | --- | --- | --- |
| OP-008 | 语义检索 | POST /v1/memories/search | memories_search | S-02（限流） | 三信号混合排序（语义+自适应BM25+实体加成，[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.3a） |
| OP-009 | 文本检索 | GET /v1/memories?q={query} | — | S-02 | 关键词全文检索（多路径融合的子能力，对应 requirements-baseline R-03） |
| OP-010 | 路径检索 | GET /v1/path | kairos_tree | S-02 | 确定性前缀匹配 |
| OP-011 | 路径空间浏览 | GET /v1/path/tree | kairos_tree | S-02 | 树状浏览 |
| OP-012 | 实体图谱检索 | POST /v1/graph/search | kairos_search_graph | S-02 | 递归 CTE 多跳 |
| OP-013 | 时间序检索 | GET /v1/memories?sort=created_at | — | S-02 | 纯时间轴，与热度解耦 |
| OP-014 | 分块检索 | 写入自动分块，检索时关联 | — | — | 200-600 字重叠窗口 |
| OP-015 | 会话列表 | GET /v1/sessions | kairos_search_sessions | S-02 | |
| OP-016 | 会话消息 | GET /v1/sessions/{id}/messages | — | S-02 | 游标分页 |
| OP-017 | 知识演化链 | GET /v1/evolution/{id} | — | — | replaces/enriches/confirms/challenges |
| OP-018 | 聚合健康报告 | GET /v1/health/detail | — | — | 按 type/state 聚合 + flags |
| OP-019 | 检索 Explain | GET /v1/search/explain | — | — | 附带 Recall Funnel trace |
| OP-020 | Playbook 搜索 | GET /v1/playbooks/search | — | — | FTS + 语义混合 |
| OP-021 | 热度最高记忆 | GET /v1/memories/heat-top | kairos_get_hot_memories | S-02 | |
| OP-022 | 记忆统计 | GET /v1/memories/stats | kairos_get_stats | — | 按 type/state 聚合 |

## 三、存储治理阶段（STR）

记忆的更新、管理、运维。

| 操作ID | 操作 | 映射端点 | 工具 | 安全红线 | 说明 |
| --- | --- | --- | --- | --- | --- |
| OP-023 | 记忆更新 | PATCH /v1/memories/{id} | — | S-15 | 版本插入，修改历史可审计 |
| OP-024 | 软删除 | DELETE /v1/memories/{id} | kairos_delete_memory | S-16（定向遗忘留痕）/S-17（结构反例豁免） | 依契约分级：permanent 拒绝（403）/ ondemand+environmental 软删（标记 is_deleted，保留审计痕迹）/ temporary 硬删（写审计 expiry_cascade_delete） |
| OP-025 | 定向遗忘 | POST /v1/memories/{id}/suppress | — | S-16 | 抑制检索，保留数据 |
| OP-026 | 标记过期 | POST /v1/memories/{id}/expire | — | — | 设 TTL，到期按契约处理：temporary 硬删除（级联清理，清理前写审计日志 expiry_cascade_delete，见架构 §5.2 forgetAfter）/ 其余契约由遗忘调度器归档至冷存储 |
| OP-027 | 锁定 | POST /v1/memories/{id}/lock | — | — | 保护不被修改 |
| OP-028 | 合并 | POST /v1/memories/merge | — | S-14 | 语义合并，保留见证锚定（v0.1.0 无 MCP 合并工具，MCP 工具注册以 [api-spec.md](api-spec.md) §6.8 为准） |
| OP-029 | 路径抑制 | POST /v1/path/suppress | — | S-16/S-17 | 路径级检索抑制 |
| OP-030 | 区推进 | POST /v1/halls/promote | — | — | 加工区→验证区→正式库 |
| OP-031 | 区退回 | POST /v1/halls/demote | — | — | 验证区→加工区 |
| OP-032 | 反馈记录 | POST /v1/playbooks/{id}/feedback | — | — | Playbook outcome 记录（v0.1.0 无 MCP 反馈工具，MCP 工具注册以 [api-spec.md](api-spec.md) §6.8 为准） |
| OP-033 | Playbook 创建 | POST /v1/playbooks | — | — | 升华 strategy 产出 |
| OP-034 | 外部校准 | POST /v1/calibrate | kairos_calibrate | S-11 | 见证锚定更新 |
| OP-035 | 宪法管理 | POST /v1/constitution | — | S-11（唯一入口） | 宪法级偏好查看/修订 |
| OP-036 | 强制冻结 | POST /v1/freeze | — | 最高级 | 冻结所有内部环 |
| OP-037 | 降级切换 | POST /v1/degradation/switch | — | — | 保守静默/受限交叉验证/安全休眠 |
| OP-038 | 审计查询 | GET /v1/audit-log | — | — | HMAC 链完整性验证 |
| OP-039 | 证伪查询 | GET /v1/falsification | — | — | 耦合/VAD/聚合审计 |
| OP-040 | 后台维护 | POST /v1/maintenance/run | — | — | Light/Deep 模式 |
| OP-041 | 维护状态 | GET /v1/maintenance/status | — | — | |
| OP-042 | 端云同步推送 | POST /v1/sync/push | — | — | 本地→服务端增量 |
| OP-043 | 端云同步拉取 | POST /v1/sync/pull | — | — | 服务端→本地增量 |
| OP-044 | 快照导出 | POST /v1/sync/export | — | S-07（脱敏） | .kairos 格式 |
| OP-045 | 快照导入 | POST /v1/sync/import | — | — | 差异化合并 |
| OP-046 | 宪法解释层复审 | — | — | — | P6 合规/判例过期检查 |
| OP-047 | 后台 Diff 扫描 | — | — | — | 差异检验批量执行 |
| OP-048 | 热度衰减 | 自动（Light 模式） | — | — | α=0.95 |
| OP-049 | 冗余合并 | 自动（Light 模式） | — | S-14 | cos > 0.92 合并 |
| OP-050 | 实体提取 | 自动（Deep 模式） | — | — | LLM 批量提取 |
| OP-051 | 蒸馏补扫 | 自动（Deep 模式） | — | — | L2→L3→L4 逐级 |
| OP-052 | P6 合规扫描 | 自动（Deep 模式） | — | — | 压缩比余量监控 |
| OP-053 | 事实新鲜度过期扫描 | 自动（Deep 模式） | — | — | valid_until→expired→stale |
| OP-054 | 记忆归档 | POST /v1/memories/{id}/archive | — | — | 竖切功能 M-05（已注册）；须满足遗忘调度器（架构 §5）freshness 阈值条件或经宪法解释层批准；is_identity=true 记忆不可归档（见证豁免） |
| OP-055 | 归档恢复 | POST /v1/memories/{id}/restore | — | — | 竖切功能 M-05 配套；须经潜伏势能重估端口（架构 §5）匹配验证——语义向量与当前活跃上下文盲区方向余弦 ≥ 阈值（默认 0.6） |
| OP-056 | 版本回滚 | POST /v1/memories/{id}/rollback | — | S-08（admin） | 回滚到指定版本 |
| OP-057 | 版本历史 | GET /v1/memories/{id}/versions | — | — | 获取记忆版本历史 |
| OP-058 | 记忆导出 | GET /v1/memories/{id}/export?clearance=export | — | S-07（脱敏） | 掩码+截断语义（与 OP-044 一致） |
| OP-059 | 记忆反馈 | POST /v1/memories/{id}/feedback | kairos_feedback_memory | — | 可信度反馈（升温/降温），线上反馈闭环端口 |
| OP-060 | 显式实体提取 | POST /v1/entities/extract | kairos_extract_entities | S-15 | 区别于 OP-004（写入时自动触发）——独立显式调用 |
| OP-061 | 反思触发 | POST /v1/reflect | — | — | 对现有记忆执行按需深度分析 |
| OP-062 | 主动主题查询 | GET /v1/proactive/topics | — | — | 待处理主动话题（A-17） |
| OP-063 | 升华状态查询 | GET /v1/sublimation/status | — | — | 升华进度查询（SF-04） |
| OP-064 | 升华触发 | POST /v1/sublimation/trigger | — | — | 手动触发升华（SF-02） |
| OP-065 | 解冻 | POST /v1/unfreeze | — | — | OP-036 强制冻结的逆操作 |
| OP-066 | 大厅详情 | GET /v1/halls/{hall} | — | — | 指定区域内记忆列表（对应 OP-030/031 区推进/退回） |

## 四、按阶段统计

| 阶段 | 操作数 | 说明 |
|:-----|:------:|:------|
| ENC | 7 | 创建/摄入 |
| RET | 15 | 检索/查询/报告 |
| STR | 44 | 更新/治理/运维/自动 |
| **总计** | **66** | |

> **对应关系**：本目录的 66 项操作与 [feature-list.md](feature-list.md) 的 **168 项能力（43 核心 + 125 扩展）** 之间存在多对多映射（勘误：原表述仅含 125 项扩展功能，遗漏 43 项核心功能——如 OP-001 按路径写入对应核心 W-01；补正：操作总数 53→66 同步 §四 统计表）——一项功能可对应多种调用方式，一项操作也可服务于多项功能。操作目录回答"系统能执行什么指令"，功能清单回答"系统对外提供什么能力"。
>
> **调用方式注记**：操作支持 API + Tool + CLI 三种调用方式，但 CLI 映射为 api-spec §3 CLI 命令集的**子集**（本目录未逐项登记 CLI 列——CLI 覆盖的高频运维操作见 api-spec §3，其余经 REST/MCP 调用）；工具列混排 MCP Bridge 工具（`kairos_*`，15 个——本列仅列示高频操作对应项，完整注册清单以 [api-spec.md](api-spec.md) §6.8 为准）与 Agent Tool（`memories_*`，5 个），来源区分见 api-spec §6.8/§2。OP-046/047 为内部操作（无对外端点），不视为缺口。 工具列「—」有两种语义：**无映射端点**（自动触发类，如 OP-004 实体自动提取——随写入/维护自动执行，无独立公开端点）与**无独立工具**（仅 REST/CLI 类，如 OP-002 批量写入——经 REST API 调用，无对应 AgentTool/MCP 工具）。

## 五、与 api-spec 的覆盖边界声明

> **覆盖边界**：本目录 66 项操作覆盖 api-spec §1~§7 的 **52/64 项 `/v1` 端点**（功能类端点全覆盖——补登记记忆生命周期 6 + 主动功能 7 共 13 个 OP-054~066；复核：§1~§7 实点 64 项端点，豁免按端点计 12 个）；**10 个端点不建 OP（按端点计 12 个）**：`/v1/config`（GET/PATCH）、`/v1/health/calibration`、`/v1/health/memory-pressure`、`/v1/scheduler/status`、`/v1/seeds`（POST/GET）、`/v1/webhooks`（v1.1 预留）、`/v1/path/rebuild-index`——无操作语义或仅内部维护触发；`GET /v1/memories/{id}`（单条读取——已知 ID 定向读取为检索退化情形，读取语义由检索类 OP（OP-008/OP-009）覆盖）、`POST /v1/sublimation/prompt` 与 `POST /v1/sublimation/process`（升华两阶段蒸馏实现端点——prompt 构建与结果处理由升华触发链路 OP-064 承接）——不建独立 OP，端点定义以 api-spec §1~§7 为权威；§8~§18 的扩展端点（叙事线 summarize/complete、压缩 run/rollback、POST /v1/causal、技能 GET/POST /v1/skills、Connector register、Profile schema、/v1/admin/export|import、GET /v1/graph/render、§18 资源摄取与多模态等）属 v0.1.0 全量或 v1.1+ 扩展，端点定义以 [api-spec.md](api-spec.md) §8~§18 为权威（api-spec 已定稿，共 88 端点 = 85 个 `/v1` 业务端点 + 3 个无前缀端点），本目录不逐项登记 OP-067+ 条目。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 操作目录：ENC/RET/STR 三阶段 53 项标准操作与安全红线映射。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：OP-005 P6 合规定性「受控偏离」→「已知超限（非受控偏离）」并修正指向 system-context 的失效引用。 |
| 0.0.3 | 2026-08-04 | 全库深度审计修复：补「五、与 api-spec 的覆盖边界声明」、工具列表头加注 AgentTool/MCP 来源（api-spec §6）。 |
| 0.0.4~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.4~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：OP-026 链接错位修正；覆盖边界声明补 §十八。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：映射口径补 43 核心功能、CLI 子集与工具来源注记。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：OP-024/OP-026 契约到期语义统一（temporary 硬删除留痕/其余归档）；OP-005 超限注记归属说明（维度降维系统级性质）。 |
| 0.0.24 | 2026-08-05 | 第六/七轮全库深度审计修复批次（changelog 0.0.24）：§五 覆盖边界声明 OP-054+ 悬空承诺收口（2-03）——扩展端点定义以 api-spec §8~§18 为权威，不再逐项登记。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：覆盖边界端点计数 81→88（85 业务 + 3 无前缀）；api-spec 中文序引用联动。 |
| 0.0.26~0.0.27 | 2026-08-06 | (合并占位：changelog 0.0.26/0.0.27 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景) |
| 0.0.28 | 2026-08-06 | 第十轮全库深度审计修复批次（changelog 0.0.28）：覆盖声明失真修复（C-02）——补 OP-054~066 共 13 项（记忆生命周期 6 + 主动功能 7），工具列注记 12→15 与枚举说明，覆盖声明改写为 49/56 + 7 个运维探针豁免清单；统计表 STR 31→44、总计 53→66。 |
| 0.0.31 | 2026-08-06 | 第十一轮全库深度审计修复批次（changelog 0.0.31）：工具列注记补「—」双语义说明（无映射端点/无独立工具）。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：§四 对应关系操作总数 53→66 补正；覆盖边界声明重算（api-spec §1~§7 实点 64 端点，豁免 10 项按端点计 12 个，覆盖 52/64——单条读取与升华两阶段蒸馏三端点补豁免说明，不新增 OP，总数维持 66）。 |
