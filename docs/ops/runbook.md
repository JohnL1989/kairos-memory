---
title: Kairos 运维手册
aliases:
  - Runbook
  - 运维操作手册
tags:
  - kairos
  - ops
  - runbook
created: 2026-07-21
updated: 2026-08-10
last_reviewed: 2026-08-10
status: draft
---

# Kairos 运维手册

> **定位**：[deployment.md](deployment.md) 首次部署后的日常操作手册。三个月后不记得怎么备份、升级、恢复时翻这里。
>
> **⚠ 草稿完善声明**：以下 `kairos` 子命令为目标示例。当前文档草稿阶段，无运行代码，命令格式和可用性将在代码启动后最终确认。所有操作以当时版本 CLI 帮助为准。
>
> **CLI 命令状态**：本手册使用的 `kairos *` 子命令为设计目标命令；与 [troubleshooting.md](troubleshooting.md) 的命令定义状态表共用——标注"待定义"的命令在代码启动前以 `--help` 为准，启动后以 CLI 实现为准。
>
> **待定义命令追缴**：本手册直接使用的待定义命令包括 `kairos health --full`（§1.2 启动检查、§2.3 灾难恢复验证）、`kairos logs --level/--module/--since/--follow`（§1.3 日常操作、§5.2 故障排查）、`kairos config show`（§4.1 配置查看）、`kairos config reset`（§4.1 配置重置）、`kairos admin key revoke`（§4.2 密钥吊销）、`kairos admin key rotate --hmac`（§4.3 密钥轮换）、`kairos audit log`（§6.2/§6.4 审计查询）、`kairos audit approve-forgetting`（§6.2 遗忘审批）——全部纳入**债务 D-430** 追缴（api-spec §3 登记契约或从本手册移除），条目见 [debt-collection.md](../governance/debt-collection.md)。灾难恢复主链路命令（`db repair` / `db restore` / `db migrate rollback`）同属 D-430 范围。

---

## §1 日常操作

### 1.1 启动与停止

| 模式 | 启动 | 停止 |
|:----|:-----|:-----|
| 轻量模式 | `kairos serve --port 8010` | `Ctrl+C` 或 `kairos stop` |
| 标准模式 | `docker compose up -d` | `docker compose down` |

### 1.2 状态检查

| 命令 | 用途 |
|:----|:-----|
| `kairos status` | 各层运行状态（宪法主权面/元认知/策略/WM/存储/接入） |
| `kairos health` | 健康检查（含数据库连接/LLM 端点/调度器状态） |
| `kairos health --full` | 全量健康检查（含 P6 余量/审计链完整性/偏置监测状态） |

### 1.3 日志查看

```bash
kairos logs --level info           # 查看 info 及以上级别日志
kairos logs --module forgetting     # 仅查看遗忘模块日志
kairos logs --since "2 hours ago"  # 近 2 小时日志
kairos logs --follow                # 实时追踪（轻量模式）
```

标准模式下通过 `docker compose logs` 查看。

---

## §2 备份与恢复

### 2.1 数据库备份

| 模式 | 备份命令 | 恢复命令 |
|:----|:---------|:---------|
| 轻量模式 | `kairos db backup`（默认路径 `~/.kairos/backups/`） | 复制备份文件至 `~/.kairos/kairos.db` |
| 标准模式（Docker） | `docker exec db pg_dump -U kairos kairos > ~/.kairos/backups/kairos-<时间戳>.sql` | ① 全量导入：`cat backup.sql \| docker exec -i db psql -U kairos kairos`；② WAL 回档（RPO ≤5 分钟关键步骤）：按 WAL 归档回放到崩溃点（`pg_restore`/replay 连续归档，恢复方式见 [reliability.md](reliability.md) §1.2「数据库意外丢失：每日全量备份 + WAL 归档恢复」） |
| 标准模式（本地） | `pg_dump -h localhost -U kairos kairos > backup.sql` | ① 全量导入：`psql -h localhost -U kairos kairos < backup.sql`；② WAL 回档：回放 `~/.kairos/wal_archive/` 连续归档至崩溃点 |

> **恢复 RPO 口径**：RPO ≤5 分钟（N-10）依赖 **WAL 归档持续启用**（`KAIROS_WAL_ARCHIVE_COMMAND`）与回档步骤；仅全量导入时实际 RPO 只能到最近全量备份点（每日 05:00 UTC），不满足 N-10。WAL 保留期见 [reliability.md](reliability.md) §三（`KAIROS_WAL_ARCHIVE_RETENTION_DAYS` 默认 7 天）。恢复后按 §2.3 执行验证。

> **保留策略**：备份保留期 30 天（`KAIROS_BACKUP_RETENTION_DAYS`），见 [reliability.md](reliability.md) §三；常驻契约快照与升华快照的 30 天为基线硬编码值（参数化列入后续运维批次，追缴见 [debt-collection.md](../governance/debt-collection.md) 债务 D-442），见 [reliability.md](reliability.md) §1.1 参数化注记。

### 2.2 配置备份

```bash
# 备份完整配置和密钥
cp ~/.kairos/.env ~/.kairos/.env.bak    # 备份环境配置（见 deployment.md §三）
```

### 2.3 恢复验证

恢复后执行 `kairos health --full` 确认以下项正常：
- 数据库连接
- 审计链 HMAC 完整性
- 安全红线检查（S-01~S-19）

---

## §3 升级与降级

### 3.1 轻量模式

```bash
# 升级
pip install --upgrade kairos
kairos db migrate       # 执行数据库迁移

# 降级（需保留旧版本 wheel）
pip install kairos==<旧版本>
kairos db migrate rollback      # 回滚迁移
```

### 3.2 标准模式

```bash
# 升级
docker compose pull
docker compose up -d
kairos db migrate

# 降级
docker compose down
# 加载旧镜像版本（替换 Image tag 为目标版本后执行）
docker compose pull
docker compose up -d
kairos db migrate rollback
```

升级前建议先备份数据库。

---

## §4 配置与密钥管理

### 4.1 配置查看修改

| 操作 | 命令 |
|:----|:-----|
| 查看当前配置 | `kairos config show` |
| 修改单个参数 | `kairos config set KAIROS_DAILY_BUDGET_FEN 20000` |
| 重置为默认值 | `kairos config reset KAIROS_WM_SLOT_CAPACITY` |
| 配置生效 | 重启服务生效（配置文档 [configuration.md](configuration.md) §二 详述生效规则） |

### 4.2 API Key 管理

| 操作 | 命令 |
|:----|:-----|
| 生成 | `kairos init --init-key` |
| 轮换 | `kairos admin key rotate` |
| 吊销 | `kairos admin key revoke <key-id>` |

### 4.3 审计密钥轮换

```bash
kairos admin key rotate --hmac    # 轮换审计 HMAC 密钥
# 轮换时保留旧密钥校验历史记录，新记录使用新密钥签名
```

---

## §5 故障排查

> **口径**：本节为值班速查子集；完整排查步骤见 [troubleshooting.md](troubleshooting.md)（§二 症状排查表、§三 错误码速查 43 项全量），错误码权威定义见 [error-reference.md](../references/error-reference.md)。

### 5.1 启动失败（速查）

| 现象 | 检查项 |
|:-----|:-------|
| 拒绝启动 | ① `KAIROS_API_KEY` 是否设置 ② `KAIROS_SALT` 是否设置 |
| 数据库连接失败 | ① `KAIROS_DB_DSN` 是否正确 ② 数据库服务是否运行 |
| 端口冲突 | `--port` 参数指定可用端口 |
| 标志组合非法 | ① 检查 `KAIROS_FEATURE_*` 组合是否落入 `kairos-minimal`/`kairos-slice`/`kairos-full` 之一（否则 `ERR-SYS-006` 拒绝启动，见 [error-reference.md](../references/error-reference.md)） |
| 宪法核不可用 | ① 检查宪法核组件装配与依赖（否则 `ERR-SYS-007` 拒绝启动，见 [error-reference.md](../references/error-reference.md)） |

完整排查步骤见 [troubleshooting.md](troubleshooting.md) §二。

### 5.2 运行时异常（速查）

| 现象 | 排查步骤 |
|:-----|:---------|
| 写入过慢 | ① `kairos status` 检查注意力预算 ② 检查是否触发限流（S-02） |
| 检索无结果 | ① 确认路径前缀正确 ② 检查遗忘调度器是否过频 ③ 检查升华状态 |
| 校准信号无响应 | ① 检查外部校准端点可达性 ② `kairos health` 检查宪法主权面状态 |
| 告警持续 | ① `kairos logs --level warn` 定位源 ② 检查对应监测器阈值 ③ 按需调整参数 |

完整排查步骤见 [troubleshooting.md](troubleshooting.md) §二。

### 5.3 错误码索引（速查）

> 本表为最常用子集；全量 43 项错误码及权威定义（含 HTTP 语义与响应体结构）见 [error-reference.md](../references/error-reference.md)。

| 错误码 | 说明 | 处理 |
|:-------|:-----|:-----|
| `ERR-AUTH-001` | API Key 无效 | 检查 `KAIROS_API_KEY` 和 `KAIROS_SALT` |
| `ERR-AUTH-002` | API Key 过期/吊销 | 生成新 Key |
| `ERR-DB-001` | 数据库连接失败 | 检查 `KAIROS_DB_DSN` 和数据库服务 |
| `ERR-LLM-001` | LLM 调用超时 | 检查 LLM 端点可达性 |
| `ERR-SEC-001` | 安全红线违反 | 检查操作是否符合红线约束 |

---

## §6 维护与审计

### 6.1 定期维护

| 周期 | 操作 | 命令 |
|:----|:-----|:-----|
| 日 | 健康检查 | `kairos health` |
| 周 | 审计链完整性检查 | `kairos audit verify-chain` |
| 月 | 恢复演练 | 系统调度器月度触发（从最近全量备份恢复至测试库 + 数据完整性校验，见 [reliability.md](reliability.md) §四） |
| 月 | 数据库 VACUUM | `kairos db vacuum`（SQLite 模式）；PG 自动 VACUUM |
| 月 | 重构建索引 | `kairos db reindex` |
| 季度 | 安全红线复验 | 逐条执行 test-strategy §2.2 验收方法 |
| 季度 | 密钥轮换 | `kairos admin key rotate` |
| 季度 | HMAC 密钥轮换 | `kairos admin key rotate --hmac` |

### 6.2 审计操作

| 操作 | 命令 |
|:----|:-----|
| 查看审计日志 | `kairos audit log` |
| 验证审计链完整性 | `kairos audit verify-chain` |
| 定向遗忘审批 | `kairos audit approve-forgetting <id>` |

### 6.3 升华管道管理

| 操作 | 命令 |
|:----|:-----|
| 查看升华状态 | `kairos status --sublimation`（规划扩展命令，CLI 权威表见 api-spec §3） |
| 触发升华轮次 | `kairos sublimation trigger` |
| 查看升华进度 | `kairos sublimation progress` |

### 6.4 证伪响应

当系统触发核心命题证伪或轴耦合证伪时：
1. `kairos status` 确认证伪信号类型
2. **确认遗忘调度器已暂停**（核心命题证伪响应路径首步，见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 证伪信号类型表）——未暂停时手动执行 `kairos forget pause`（待定义命令，追缴同 D-430）或按当时 CLI 帮助处理
3. `kairos audit log` 查看证伪信号负载
4. 按架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.10 证伪响应路径处理
5. 输出审查报告

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 运维手册：日常操作/备份恢复/升级降级/配置与密钥管理/故障排查。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：错误码速查表补充子集声明与 ERR-LLM-002 废弃标注、备份命令统一目录与时间戳命名、CLI 命令状态声明（批次归因：错误码三清单对齐与 ERR-LLM-002 废弃标注实际落于 changelog 0.0.8，本行 0.0.2 为历史登记，见 [changelog.md](../governance/changelog.md) 0.0.8「引用修正」）。 |
| 0.0.8 | 2026-08-04 | 补登（changelog 0.0.8 批次）：错误码三清单对齐（error-reference/api-spec/runbook，ERR-LLM-002 废弃标注、ERR-CAL-001/002 状态码 503→400）——原误归 0.0.2，按 changelog 叙述节为准。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：备份保留期引用修正（§1.1/§三 + 参数化）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：§5 故障排查精简为值班速查子集+指针（与 troubleshooting 双向互链）。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：kairos status --sublimation 补规划扩展注记；frontmatter 审查日期同步。 |
| 0.0.51 | 2026-08-08 | round22 审计修复批次（changelog 0.0.51）：§5.1 启动失败速查补「标志组合非法 / 宪法核不可用」两项（对应 ERR-SYS-006/007）；§5 口径 38→40。 |
| 0.0.53 | 2026-08-08 | round23 深度审计修复批次（changelog 0.0.53）：R23-06 补待定义 CLI 命令清单块，指针「债务 D-430」。 |
| 0.0.55 | 2026-08-08 | round24 全面深度审计修复批次（changelog 0.0.55）：认知基础去版本化 30 处改写；引用错位修正（api-spec §6.5 等）；S-19 行为层验收承载；CLI 追缴对齐；blueprint 无编号承诺追缴 D-433~D-438 补登；摘要表 D-422~D-428 补行。 |
| 0.0.59 | 2026-08-08 | round26 全面深度审计修复批次（changelog 0.0.59，补登）：错误码口径 40→42（两处，`ERR-CTR-003` 记忆已锁定 / `ERR-CTR-004` 意图契约未关闭）。 |
| 0.0.65 | 2026-08-08 | round31 深度审计修复批次（changelog 0.0.65）：§2.1 补 WAL 回档恢复步骤与 RPO 口径注记（RPO ≤5 分钟依赖 WAL 归档持续启用）；§6.1 定期维护补「月：恢复演练」行；§6.4 证伪响应补「确认遗忘调度器已暂停」步骤。 |
| 0.0.66 | 2026-08-09 | round32 全面深度审计修复批次（changelog 0.0.66）：版本记录补登批次——0.0.59 行（错误码 40→42）为前序批次实质变更漏登记，本批补登（governance §4「触及即登记」）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85）：错误码计数 42→43（新增 ERR-CTR-005 幂等键冲突）两处口径同步。详见 changelog 0.0.85 叙述节。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87）：快照保留期 30 天硬编码补债务 D-442 指针。 |
