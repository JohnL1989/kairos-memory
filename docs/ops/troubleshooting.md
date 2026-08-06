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
updated: 2026-08-05
last_reviewed: 2026-08-04
status: draft
---

# Kairos 故障排查指南

> **文档定位：** 常见问题的排查步骤和恢复命令。不包含系统设计或配置细节——部署配置见 [docs/ops/deployment.md](deployment.md)，可靠性策略见 [docs/ops/reliability.md](reliability.md)，设计约束见 [docs/foundation/architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7「安全红线」。

> **⚠ 草稿完善声明**：本文所有 CLI 命令（`kairos db restore`、`kairos db repair`、`kairos admin key rotate` 等）与 SQL 语句均为**设计示例**，当前无构建产物、无可执行命令。项目处于设计冻结阶段，代码尚未启动。**请勿将本文当作可执行的灾难恢复手册使用**——在代码实现前，本文的价值在于定义"应当具备哪些恢复能力"，而非"如何执行恢复"。具体命令语法在实现后可能变化，读者应关注排查思路与恢复语义而非命令文本。

---

## 一、CLI 命令定义状态

下表标注本文引用的运维命令在规格文档中的定义来源。**「无」表示该命令目前仅在本文出现，尚未在任何规格文档中定义契约**——实现前须先补齐定义，否则将成为实现盲区。

| 命令 | 定义来源 | 状态 |
|:-----|:---------|:-----|
| `kairos db verify` | 无 | ⚠ 待定义 |
| `kairos db repair` | 无 | ⚠ 待定义（灾难恢复主命令） |
| `kairos db restore <backup_path>` | 无 | ⚠ 待定义（灾难恢复主命令） |
| `kairos db migrate rollback` | 无 | ⚠ 待定义（灾难恢复主命令） |
| `kairos admin key rotate` | 无 | ⚠ 待定义 |

> 上述 5 条命令在 [slice-implementation-guide.md](../development/slice-implementation-guide.md)、[api-spec.md](../specification/api-spec.md)、[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) 三处检索均为 0 命中。此缺口已在 [governance/cognitive-architecture-gap.md](../governance/cognitive-architecture-gap.md) 之外单列，须在 v0.1.0 编码启动前补齐 CLI 契约规格。

---

## 二、症状排查表

| 症状 | 排查步骤 | 恢复命令 |
|:----|:--------|:--------|
| **Kairos 无法启动** | ① 检查 `KAIROS_SALT` 是否设置 ② 检查 `KAIROS_DB_DSN` 是否正确 ③ 检查数据库是否可连接 | 设置环境变量后重启容器 |
| **按需召回返回空** | ① 检查嵌入模型是否在线 ② 检查 memories 表是否有数据 ③ 检查是否为短查询被门禁拦截 | 嵌入恢复后自动重试 |
| **常驻契约不更新** | ① 检查冻结快照机制——写入已落盘但当前 session 不刷新 ② 新 session 是否加载了新内容 | 新 session 自动生效 |
| **升华层不运行** | ① 检查调度器状态 ② 检查系统是否持续处于「推理活跃」状态 ③ 检查 `sublimation_queue` 表中升华阶段的状态 | 推理空闲后自动触发 |
| **磁盘使用率超 85%** | ① 检查 archive 目录大小 ② 检查备份目录大小 | 手动清理过期备份或触发升华层激进归档 |
| **契约分配错误** | ① 检查写入时是否指定了 contract 参数 ② 一键模式默认分配按需契约 | 显式指定 contract 参数重试 |
| **路径搜索结果跨路径** | ① 检查 SQL 中 path 前缀过滤是否正确 ② 检查索引状态 | 重建索引或修复查询条件 |
| **升华阶段停滞** | ① 检查 `sublimation_queue` 表中对应阶段的状态 ② 检查调度器是否处于空闲状态 | 重启调度器或手动插入下一阶段事件：`INSERT INTO sublimation_queue (id, memory_id, stage, status, created_at) VALUES (gen_random_uuid(), '<uuid>', 'item', 'pending', now());`（`stage` 合法取值：`raw` / `item` / `strategy` / `behavior`；Schema 见 [specification/data-model.md](../specification/data-model.md) §sublimation_queue） |

---

## 三、错误码速查（全量 38 项）

> **口径**：本表为 [references/error-reference.md](../references/error-reference.md) 的运维视角镜像，**已覆盖全部 38 个已定义错误码**（此前仅收录 17 项，覆盖率 44.7%）。错误码的权威定义（含 HTTP 状态码语义与响应体结构）以 error-reference 为准；本表额外提供「排查动作」列，供值班时直接使用。
>
> **返回方式**：`ERR-AUTH-*`、`ERR-RATE-*`、`ERR-INPUT-*`、`ERR-DB-004/005`、`ERR-CTR-*`、`ERR-CNF-*`、`ERR-SYS-001/002` 由 HTTP API 直接返回；`ERR-DB-001/002/003`、`ERR-LLM-*`、`ERR-SUB-*`、`ERR-CAL-*`、`ERR-SEC-001`、`ERR-SYS-003/004/005` 主要出现在内部日志中，用于排查。

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
| `ERR-DB-004` | 404 | 记忆未找到 | 确认 memory_id 或路径正确 |
| `ERR-DB-005` | 409 | 版本冲突（并发更新） | 读取最新版本后重试 |
| `ERR-LLM-001` | 503 | LLM 调用超时 | 检查 LLM Provider 状态 |
| `ERR-LLM-002` | — | **DEPRECATED** — 已合并至 ERR-RATE-003。此码仅用于后向兼容引用，新实现请使用 ERR-RATE-003（429）定位 LLM 日预算耗尽场景 | 使用 ERR-RATE-003 |
| `ERR-LLM-003` | 503 | 嵌入服务不可用 | 切换至本地 BGE-M3 或检查 API Key |
| `ERR-LLM-004` | 500 | LLM 返回异常响应 | 检查 LLM 响应格式 |
| `ERR-SEC-001` | 403 | 安全红线违反（详情见审计日志）。S-01 三层响应：启动缺 Key→连接拒绝（非 HTTP），运行时缺 Token→401（ERR-AUTH-001），红线违反→403（ERR-SEC-001） | 检查操作是否符合红线约束 |
| `ERR-SYS-001` | 503 | 系统正被冻结 | 等待解冻或外部干预 |
| `ERR-CAL-001` | 503 | 外部校准信号无效或格式错误 | 检查校准信号格式 |
| `ERR-CAL-002` | 503 | 校准置信度过低，拒绝注入 | 提高校准信号置信度或重试 |
| `ERR-SUB-001` | 500 | 升华管道阶段转换失败 | 检查升华日志，手动推进或回退 |
| `ERR-SUB-002` | 500 | 蒸馏结果冲突检验不通过 | 检查蒸馏输入质量 |
| `ERR-CTR-001` | 400 | 无效的契约类型 | 检查 contract 参数值 |
| `ERR-CTR-002` | 403 | 临时契约不可写入审计历史（此为设计约束——临时契约过期清除刻意不产生审计事件，api-spec §4） | 检查审计写操作的目标记忆契约类型 |
| `ERR-CNF-001` | 409 | 记忆合并冲突 | 手动裁决或等待外部校准信号 |
| `ERR-CNF-002` | 409 | 差异检验阻断合并 | 检查使用权重与见证锚定的一致性 |
| `ERR-SYS-002` | 503 | 系统处于降级模式 | 检查校准状态 |
| `ERR-SYS-003` | 500 | 内部组件异常 | 检查健康检查端点和日志 |
| `ERR-SYS-004` | 503 | 调度器不可用 | 重启调度器 |
| `ERR-SYS-005` | 500 | 未预期的内部错误 | 查看日志并报告 |

---

## 四、安全事件排查

| 事件 | 排查步骤 | 恢复命令 |
|:----|:--------|:--------|
| **API Key 疑似泄露** | (1) 立即吊销泄露 Key (2) 生成新 Key 并更新 `KAIROS_API_KEY` (3) 检查审计日志中该 Key 在泄露时间窗口内的所有操作 | `kairos admin key rotate`（⚠ 待定义，见 §一） |
| **数据库文件损坏** | (1) 停止服务 (2) 从最近备份恢复 (3) 运行 `kairos db verify` (4) 如备份不可用，尝试 `kairos db repair` | `kairos db restore <backup_path>`（⚠ 待定义，见 §一） |
| **升级失败回滚** | (1) 停止服务 (2) 恢复旧版本二进制/镜像 (3) 执行 `kairos db migrate rollback` 回滚数据库迁移 | 旧镜像版本 + `docker compose up -d`（⚠ 命令待定义，见 §一） |

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 故障排查：常见症状、排查步骤与恢复命令、错误码索引。 |
| 0.0.2 | 2026-08-03 | 补加草稿完善声明；新增 CLI 命令定义状态表；修正 `sublimation_events` -> `sublimation_queue`；错误码速查由 17 项补全至 38 项。 |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：frontmatter 与版本记录同步（第二轮全库深度审计修复批次）。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：api-spec §四→§4 引用联动。 |
