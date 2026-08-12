---
title: Kairos 故障排查指南
aliases:
  - 故障排查
  - Troubleshooting
tags:
  - kairos
  - ops
  - troubleshooting
created: 2026-07-18
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 故障排查指南

> **文档定位：** 常见问题的排查步骤和恢复命令。不包含系统设计或配置细节——部署配置见 [docs/ops/deployment.md](deployment.md)，可靠性策略见 [docs/ops/reliability.md](reliability.md)，设计约束见 [docs/foundation/architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §8「安全红线」。值班速查子集（启动失败/运行时异常/错误码）见 [runbook.md](runbook.md) §5。

> **⚠ 草稿完善声明**：本文所有 CLI 命令（`kairos db restore`、`kairos db repair`、`kairos admin key rotate` 等）与 SQL 语句均为**设计示例**，当前无构建产物、无可执行命令。项目处于设计冻结阶段，代码尚未启动。**请勿将本文当作可执行的灾难恢复手册使用**——在代码实现前，本文的价值在于定义"应当具备哪些恢复能力"，而非"如何执行恢复"。具体命令语法在实现后可能变化，读者应关注排查思路与恢复语义而非命令文本。

---

## 一、CLI 命令定义状态

下表标注本文引用的运维命令在规格文档中的定义来源。**「无」表示该命令未在 [api-spec.md](../specification/api-spec.md) §3 登记契约**（可能仅在本文或 runbook/security-spec 中使用）——实现前须先补齐定义，否则将成为实现盲区。

| 命令 | 定义来源 | 状态 |
|:-----|:---------|:-----|
| `kairos db verify` | [api-spec.md](../specification/api-spec.md) §3 | 已定义 |
| `kairos admin key rotate` | [api-spec.md](../specification/api-spec.md) §3 | 已定义 |
| `kairos db repair` | 无 | ⚠ 待定义（灾难恢复主命令） |
| `kairos db restore <backup_path>` | 无 | ⚠ 待定义（灾难恢复主命令） |
| `kairos db migrate rollback` | 无 | ⚠ 待定义（灾难恢复主命令） |
| `kairos admin key revoke <key-id>` | 无（runbook §4.2、security-spec §2.1 使用中） | ⚠ 待定义 |
| `kairos admin key rotate --hmac` | 无（runbook §4.3 使用中） | ⚠ 待定义 |
| `kairos audit log` | 无（runbook §6.2 使用中） | ⚠ 待定义 |
| `kairos audit approve-forgetting <id>` | 无（runbook §6.2 使用中） | ⚠ 待定义 |
| `kairos health --full` | 无（runbook §1.2/§2.3 使用中） | ⚠ 待定义 |
| `kairos logs --level / --module / --since / --follow` | 无（runbook §1.3 使用中；api-spec §3 仅定义 `kairos logs --tail`） | ⚠ 待定义 |
| `kairos config show` | [api-spec.md](../specification/api-spec.md) §3 | 已定义（0.0.96 登记，竖切 CLI 15 交付项，组件 9） |
| `kairos config reset <param>` | 无（runbook §4.1 使用中；api-spec §3 仅定义 `kairos config set` / `config show`） | ⚠ 待定义（v0.1.0 全量阶段登记，D-430） |

> 上述 3 条灾难恢复主命令（db repair / db restore / db migrate rollback）在 [api-spec.md](../specification/api-spec.md) §3 中无定义，此缺口已在 [governance/cognitive-architecture-gap.md](../governance/cognitive-architecture-gap.md) 之外单列。**待定义命令处置（0.0.96 分类处置，债务 D-430）**：竖切相关命令 `kairos config show` 已于 0.0.96 在 api-spec §3 登记契约（竖切 CLI 15 交付项）——竖切启动无待定义命令；其余 10 条（含 3 条灾难恢复主命令）为灾难恢复/运维/发布验证链路命令，均不在竖切端点集内，归 v0.1.0 全量阶段（Phase 2 后、发布前）在 api-spec §3 登记契约或从使用方文档（runbook/security-spec）移除，否则将成为实现盲区。该门禁已登记债务 **D-430**（见 [governance/debt-collection.md](../governance/debt-collection.md)）。

---

## 二、症状排查表

| 症状 | 排查步骤 | 恢复命令 |
|:----|:--------|:--------|
| **Kairos 无法启动** | ① 检查 `KAIROS_API_KEY` 是否设置（S-01：无 Key 拒绝启动）② 检查 `KAIROS_SALT` 是否设置 ③ 检查 `KAIROS_DB_DSN` 是否正确 ④ 检查数据库是否可连接 ⑤ 检查特征标志组合是否匹配某一命名配置集（`invalid_flag_composition` 审计事件拒绝启动，见 [error-reference.md](../references/error-reference.md) `ERR-SYS-006`）⑥ 检查宪法核组件装配后是否可用（`constitutional_core_unavailable` 审计事件拒绝启动，见 `ERR-SYS-007`） | 设置环境变量后重启容器；⑤⑥ 须使组合落入 `kairos-minimal`/`kairos-slice`/`kairos-full` 之一且宪法核可用 |
| **按需召回返回空** | ① 检查嵌入模型是否在线 ② 检查 memories 表是否有数据 ③ 检查是否为短查询被门禁拦截 | 嵌入恢复后自动重试 |
| **常驻契约不更新** | ① 检查冻结快照机制——写入已落盘但当前 session 不刷新 ② 新 session 是否加载了新内容 | 新 session 自动生效 |
| **升华层不运行** | ① 检查调度器状态 ② 检查系统是否持续处于「推理活跃」状态 ③ 检查 `sublimation_queue` 表中升华阶段的状态 | 推理空闲后自动触发 |
| **磁盘使用率超 85%** | ① 检查 archive 目录大小 ② 检查备份目录大小 | 手动清理过期备份或触发升华层激进归档 |
| **契约分配错误** | ① 检查写入时是否指定了 contract 参数 ② 一键模式默认分配按需契约 | 显式指定 contract 参数重试 |
| **路径搜索结果跨路径** | ① 检查 SQL 中 path 前缀过滤是否正确 ② 检查索引状态 | 重建索引或修复查询条件 |
| **升华阶段停滞** | ① 检查 `sublimation_queue` 表中对应阶段的状态 ② 检查调度器是否处于空闲状态 | 重启调度器或手动插入下一阶段事件：`INSERT INTO sublimation_queue (id, memory_id, stage, status, created_at) VALUES (gen_random_uuid(), '<uuid>', 'item', 'pending', now());`（`stage` 合法取值：`raw` / `item` / `strategy` / `behavior`；Schema 见 [specification/data-model.md](../specification/data-model.md) §sublimation_queue） |

---

## 二a、记忆循环四动作失败模式（写入/巩固/检索/遗忘）

> **外部理念吸收注记**：记忆循环（验证→写入→去重抽象→按条件检索→用后评估→更新或遗忘）的每一步都可能失败：写入失败积累垃圾、巩固失败产生互相矛盾的规则、检索失败在错误场景调用经验、遗忘失败让系统固守过时世界。下表将四类失败模式映射到 Kairos 已有监控信号，供排障时按「症状 → 失败环节 → 检查点」定位。

| 失败模式 | 症状 | 对应监控信号（observability §一） | 检查点 |
|:--------|:-----|:------------------------------|:------|
| **写入失败→积累垃圾** | 记忆库膨胀但检索质量下降；检索结果大量低相关 | `kairos_memory_count` 异常增长、GSPO 聚类命中率上升（冗余压力） | ① 摄取管道的验证环节（ADD-only 协议、四层递进式摄取防御）是否被绕过 ② 探索产物是否未经验证即进入常规存储（置信度带 30%→70%→95% 是否执行）③ `kairos_write_total` 中 status 分布 |
| **巩固失败→矛盾规则** | 同一主题存在互相矛盾的记忆条目；contradiction Flag 密度上升 | 事件总线 `contradiction_detected` 事件频率、knowledge_evolution 的 challenges 记录密度 | ① 升华管道蒸馏产物是否通过冲突检验（ERR-SUB-002）② 新信息冲突解决（补充/修正/重构）是否按语义内核相似度正确分流 ③ memory_flags 中 contradiction 的解析率（长期未解析=矛盾悬而未决） |
| **检索失败→错误场景调用** | 过时经验被高频选中；任务成功率下降但检索延迟正常 | `kairos_stale_call_ratio`（过时调用率，见 acceptance-criteria §一a）、`kairos_task_success_rate` 三态对比 | ① 排序调制的「高相似 × 过时联合惩罚」是否生效（架构 §7.3a）② conditions/encoding_context 的环境匹配是否执行 ③ 检索路径是否越过了路径空间硬过滤边界 |
| **遗忘失败→固守过时世界** | 陈旧记忆长期占活跃存储；freshness 分布异常 | `kairos_forgetting_score` 分布、遗忘队列积压比（`KAIROS_PRESSURE_BACKLOG_RATIO`） | ① 遗忘调度器是否运行（Light 模式心跳）② freshness.py 推断是否被 false_positive 调优抑制（假阳性率阈值 15%）③ 结构性守护/身份豁免是否误用了范围（`is_structure=true` 记忆过多=守护过度） |

---

## 二b、记忆整合失效排查（整合后效用下降）

> **外部理念吸收注记**：**整合步骤本身可能成为错误来源**（外部实证：PAPER-01 持续更新衰退）——持续把新信息整合进既有记忆（升华蒸馏 / Compaction 压缩 / 知识演化合并），长期运行后记忆效用反而下降。Kairos 的整合动作启用或升级后，出现下述症状时按本小节排查。

**症状**：整合/升华/压缩批量运行后，检索命中率或任务成功率下降（而非上升）；整合后的记忆与用户实际情况偏离（「记住了错的东西」）。

| 排查点 | 症状特征 | 检查方法 | 处置 |
|:--|:--|:--|:--|
| **错误分组** | 不同主题/不同主体的内容被并入同一条记忆 | 检查 Compaction/升华的聚类合并是否跨域误并（GSPO/蒸馏分组结果）；检查 `knowledge_evolution` 的 replaces 记录是否误取代 | 30 天窗口内回滚压缩（`POST /v1/admin/compaction/rollback/{snapshot_id}`，见 [data-model.md](../specification/data-model.md) §12 `compaction_snapshots`） |
| **过度泛化** | 经验被提炼成无条件通用的规则，错误套用于不适用场景 | 检查升华产物（strategy 级）是否携带适用条件——`encoding_context.conditions`（外部理念吸收约定）；无条件约束的经验不得在升华管道中去语境化为通用规律 | 补录适用条件或降级回 item 级；conditions 不匹配的候选在检索排序中降权 |
| **过拟合** | 整合偏向近期少数样本，长期稳定事实被短期高频话题覆盖 | 检查 L4 画像/RL 权重是否被短期话题主导（`user_profiles` 刷新、`rl_weights` 分布）；检查 `knowledge_evolution` confirms 密度异常 | 恢复基线权重；画像更新触发人工审查 |

**预防闭环**：整合动作与效果评估解耦——整合批量执行后进入观察窗口（`KAIROS_OBSERVATION_WINDOW_PERIODS`，见 [configuration.md](../ops/configuration.md) §4），窗口内比对整合前后检索质量指标（过时调用率 / 任务成功率改善，见 acceptance-criteria 记忆质量评估指标，[acceptance-criteria.md](../quality/acceptance-criteria.md)）；窗口内效用下降即回滚该批次整合，并在 changelog 批次条目登记整合失败批次。

---

## 三、错误码速查（全量 43 项）

> **口径**：本表为 [references/error-reference.md](../references/error-reference.md) 的运维视角镜像，**已覆盖全部 43 个已定义错误码**。错误码的权威定义（含 HTTP 状态码语义与响应体结构）以 error-reference 为准；本表额外提供「排查动作」列，供值班时直接使用。
>
> **返回方式**：`ERR-AUTH-*`、`ERR-RATE-*`、`ERR-INPUT-*`、`ERR-CTR-*`、`ERR-CNF-*`、`ERR-SEC-001` 由 HTTP API 直接返回；`ERR-DB-001~003`、`ERR-LLM-*`、`ERR-SUB-*`、`ERR-CAL-*`、`ERR-SYS-*` 为内部运维与日志使用码，API 层不直接返回——对外映射为 503/500（映射规则见 [api-spec.md](../specification/api-spec.md) §7），主要用于排查。**例外**：`ERR-DB-004`（404）与 `ERR-DB-005`（409）为资源状态码，随 HTTP 响应直接返回给调用方。

| 错误码 | HTTP | 含义 | 排查动作 |
|:------|:----:|:-----|:--------|
| `ERR-AUTH-001` | 401 | API Key 无效或未设置 | 检查 `KAIROS_API_KEY` 环境变量 |
| `ERR-AUTH-002` | 401 | API Key 已过期/被吊销 | 生成新 Key |
| `ERR-AUTH-003` | 403 | API Key 权限不足（read 权限尝试写入） | 升级 Key 权限级别 |
| `ERR-AUTH-004` | 403 | 管理操作需要 admin Key | 使用 admin Key 重试 |
| `ERR-RATE-001` | 429 | 写入操作超出限流阈值 | 等待 `Retry-After` 秒后重试 |
| `ERR-RATE-002` | 429 | 检索操作超出限流阈值 | 等待后重试 |
| `ERR-RATE-003` | 429 | LLM 日预算耗尽 | 等待预算重置（每日 0 点）或充值 |
| `ERR-RATE-004` | 429 | 外部校准信号频次过高 | 降低校准频次 |
| `ERR-INPUT-001` | 413 | 内容超过 64 KB 上限 | 分段写入并关联 |
| `ERR-INPUT-002` | 400 | 路径格式无效（非 `kairos://` 开头） | 确认路径以 `kairos://` 开头 |
| `ERR-INPUT-003` | 422 | 路径深度超限（超过 10 层） | 减少路径层级 |
| `ERR-INPUT-004` | 422 | 缺少必填字段（content / path） | 检查请求参数 |
| `ERR-INPUT-005` | 400 | 记忆类型无效（memory_types 数组内容须为 episodic/semantic/procedural 白名单内的值） | 检查 memory_types 值 |
| `ERR-INPUT-006` | 400 | 契约类型无效 | 检查 contract 值 |
| `ERR-INPUT-007` | 400 | JSON 解析失败 | 检查请求体格式 |
| `ERR-DB-001` | 503 | 数据库连接失败 | 检查数据库是否运行、连接 URL 是否正确 |
| `ERR-DB-002` | 500 | 数据库迁移失败 | 检查迁移文件，手动修复后重试 `kairos db migrate` |
| `ERR-DB-003` | 500 | 记忆写入失败（存储层异常） | 检查数据库状态，重试 |
| `ERR-DB-004` | 404 | 资源不存在（记忆 / 版本 / 叙事线 / 边类型等定位失败）——API 直接返回 | 确认 memory_id 或路径正确 |
| `ERR-DB-005` | 409 | 版本冲突（并发更新，`If-Match` 不一致）——API 直接返回 | 读取最新版本后重试 |
| `ERR-LLM-001` | 503 | LLM 调用超时 | 检查 LLM Provider 状态 |
| `ERR-LLM-002` | — | **DEPRECATED** — 已合并至 ERR-RATE-003。此码仅用于后向兼容引用，新实现请使用 ERR-RATE-003（429）定位 LLM 日预算耗尽场景 | 使用 ERR-RATE-003 |
| `ERR-LLM-003` | 503 | 嵌入服务不可用 | 切换至本地 BGE-M3 或检查 API Key |
| `ERR-LLM-004` | 500 | LLM 返回异常响应 | 检查 LLM 响应格式 |
| `ERR-SEC-001` | 403 | 安全红线违反（详情见审计日志）。S-01 三层响应：启动缺 Key→连接拒绝（非 HTTP），运行时缺 Token→401（ERR-AUTH-001），红线违反→403（ERR-SEC-001） | 检查操作是否符合红线约束 |
| `ERR-SYS-001` | 503 | 系统正被冻结 | 等待解冻或外部干预 |
| `ERR-CAL-001` | 400 | 外部校准信号无效或格式错误 | 检查校准信号格式 |
| `ERR-CAL-002` | 400 | 校准置信度过低，拒绝注入 | 提高校准信号置信度或重试 |
| `ERR-SUB-001` | 500 | 升华管道阶段转换失败 | 检查升华日志，手动推进或回退 |
| `ERR-SUB-002` | 500 | 蒸馏结果冲突检验不通过 | 检查蒸馏输入质量 |
| `ERR-CTR-001` | 400 | 无效的契约类型 | 检查 contract 参数值 |
| `ERR-CTR-002` | 403 | 临时契约不可写入审计历史（设计约束——捕获阶段拒绝输入未入库，不产生审计事件；**已入库临时记忆过期清除必留痕**（`expiry_cascade_delete`，见 [api-spec.md](../specification/api-spec.md) §4） | 检查审计写操作的目标记忆契约类型 |
| `ERR-CTR-003` | 403 | 记忆已锁定（`locked_until` 未到期），禁止修改/删除/归档/抑制/合并 | 等待锁定到期，或用 admin Key 将 `locked_until` 置空 |
| `ERR-CTR-004` | 409 | 意图契约未关闭，禁止直接删除 | 先经 `intention_resolve` 关闭意图降级为 ondemand 后重试 |
| `ERR-CTR-005` | 409 | 幂等键冲突（`Idempotency-Key` 已存在且载荷不一致） | 更换幂等键重试，或查询首次提交结果 |
| `ERR-CNF-001` | 409 | 记忆合并冲突 | 手动裁决或等待外部校准信号 |
| `ERR-CNF-002` | 409 | 差异检验阻断合并 | 检查使用权重与见证锚定的一致性 |
| `ERR-SYS-002` | 503 | 系统处于降级模式 | 检查校准状态 |
| `ERR-SYS-003` | 500 | 内部组件异常 | 检查健康检查端点和日志 |
| `ERR-SYS-004` | 503 | 调度器不可用 | 重启调度器 |
| `ERR-SYS-005` | 500 | 未预期的内部错误 | 查看日志并报告 |
| `ERR-SYS-006` | — | 特征标志组合不匹配任一命名配置集（`invalid_flag_composition`），拒绝启动 | 检查 `KAIROS_FEATURE_*` 配置，使组合落入 `kairos-minimal`/`kairos-slice`/`kairos-full` 之一 |
| `ERR-SYS-007` | — | 宪法核组件装配后不可用（`constitutional_core_unavailable`），拒绝启动 | 检查宪法核组件装配与依赖，必要时降级或重建装配 |

---

## 四、安全事件排查

| 事件 | 排查步骤 | 恢复命令 |
|:----|:--------|:--------|
| **API Key 疑似泄露** | (1) 立即吊销泄露 Key (2) 生成新 Key 并更新 `KAIROS_API_KEY` (3) 检查审计日志中该 Key 在泄露时间窗口内的所有操作 | `kairos admin key rotate`（已定义，见 api-spec §3） |
| **数据库文件损坏** | (1) 停止服务 (2) 从最近备份恢复 (3) 运行 `kairos db verify` (4) 如备份不可用，尝试 `kairos db repair` | `kairos db restore <backup_path>`（⚠ 待定义，见 §一） |
| **升级失败回滚** | (1) 停止服务 (2) 恢复旧版本二进制/镜像 (3) 执行 `kairos db migrate rollback` 回滚数据库迁移 | 旧镜像版本 + `docker compose up -d`（⚠ 命令待定义，见 §一） |

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 故障排查：常见症状、排查步骤与恢复命令、错误码索引。 |
| 0.0.2~0.0.38 | 2026-08-06 | （合并占位：changelog 0.0.2~0.0.38 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.39 | 2026-08-06 | 外部理念吸收批次（changelog 0.0.39）：新增 §二a 记忆循环四动作失败模式表（写入/巩固/检索/遗忘 → 症状 → 监控信号 → 检查点）。 |
| 0.0.41 | 2026-08-07 | 外部理念吸收落地批次（changelog 0.0.41）：新增 §二b 记忆整合失效排查（整合后效用下降——错误分组 / 过度泛化 / 过拟合三排查点 + 预防闭环，外部实证：PAPER-01 持续更新衰退 2026）。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：ERR-CAL-001/002 状态码 503→400（对齐 error-reference 权威）；ERR-CTR-002 审计痕迹口径修正（已入库清除必留痕）；探索产物置信度带补 50% 档；§三 映射注记删除。 |
| 0.0.51 | 2026-08-08 | round22 审计修复批次（changelog 0.0.51）：§二 启动排查补⑤⑥（标志组合 / 宪法核可用性，对应 ERR-SYS-006/007）；§三 错误码 38→40 全量同步；§一 补 D-430 债务指针。 |
| 0.0.55 | 2026-08-08 | round24 全面深度审计修复批次（changelog 0.0.55）：认知基础去版本化 30 处改写；引用错位修正（api-spec §6.5 等）；S-19 行为层验收承载；CLI 追缴对齐；blueprint 无编号承诺追缴 D-433~D-438 补登；摘要表 D-422~D-428 补行。 |
| 0.0.57 | 2026-08-08 | round25 全面深度审计修复批次（changelog 0.0.57）：架构元认知层第五层编号/完结叙事线 409/deleted_at 承载补列/技能管理定位改指 blueprint/S-17 法定擦除例外同步/README 版本链补登/KAIROS_ 参数前缀等 21 项闭环。 |
| 0.0.59 | 2026-08-08 | round26 全面深度审计修复批次（changelog 0.0.59）：§三 错误码 40→42（补 `ERR-CTR-003` 记忆已锁定 / `ERR-CTR-004` 意图契约未关闭）；`ERR-DB-004/005` 返回方式标为例外（API 直接返回）。 |
| 0.0.80 | 2026-08-09 | round42 全面深度审计修复批次（changelog 0.0.80）：引用/口径收口 + 格式收尾 + 术语登记（glossary 70→76）——详见 changelog 0.0.80 叙述节。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85）：§三 错误码 42→43（补 `ERR-CTR-005` 幂等键冲突）；错误码速查标题与口径声明计数同步。详见 changelog 0.0.85 叙述节。 |
| 0.0.96 | 2026-08-11 | 定稿审查处置批次（changelog 0.0.96）：CLI 定义状态表 `config show` 状态改「已定义」（api-spec §3 登记，竖切交付项）+ 门禁段落改分类处置声明（D-430：竖切无待定义命令，其余 10 条归 v0.1.0 全量阶段）。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |


