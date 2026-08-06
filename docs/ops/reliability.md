---
title: Kairos 可靠性策略
aliases:
  - Kairos 备份与恢复
  - RTO RPO
tags:
  - kairos
  - ops
  - reliability
created: 2026-07-18
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 可靠性策略

> **⚠ 草稿完善声明**：本文定义的 RTO/RPO、备份策略和自动恢复机制为设计目标。当前草稿完善阶段无运行代码。轻量模式（bare Python 进程）不含 sidecar 自动恢复能力——RTO ≤30s 自动恢复适用于标准/全量部署（Docker/sidecar），轻量模式需手动重启。

---

## 一、回滚策略

### 1.1 常驻契约回滚

升华层每次运行前自动创建数据库快照：

```text
# SQLite
cp ~/.kairos/kairos.db ~/.kairos/backups/kairos-$(date +%Y%m%d-%H%M%S).db

# PostgreSQL
pg_dump -d kairos -f ~/.kairos/backups/kairos-$(date +%Y%m%d-%H%M%S).sql
```

最多保留最近 30 天备份。恢复方式：手动复制备份覆盖或 `psql -f <dump>`。

### 1.2 数据库回滚

| 场景 | 方式 |
|:----|:-----|
| 数据损坏 | 从 migrations 按序回滚 + 备份恢复 |
| 版本回退 | 使用旧镜像 + 旧数据库快照 |
| 调度器误操作 | 重启容器，调度器从头循环 |
| 数据库意外丢失 | 从每日全量备份 + WAL 归档恢复 |

### 1.3 数据可靠性设计

写入路径设计见架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §4「存储层（缓冲写入）」。核心原则：写入确认基于内存缓冲收讫而非落盘确认，缓冲层有持久化兜底。

### 1.4 异常状态管理

系统通过分级响应机制保障数据在容量异常时的完整性：

| 状态 | 触发条件 | 响应动作 |
|:----|:---------|:--------|
| **黄色预警** | 磁盘使用率 >75% | 写入告警日志，通知运维 |
| **红色警戒** | 磁盘使用率 >85% | 暂停非关键写入，仅运行归档和压缩 |
| **崩溃边缘** | 磁盘使用率 >92% | 丢弃临时数据，截断日志，触发优雅关闭 |

退出红色警戒后强制冷却期，防止频繁切换。

### 1.5 LLM 调用超时与熔断

架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.3 定义了跨层三环不变量。以下为超时重试与熔断的具体策略：

| 控制项 | 默认值 | 说明 |
|:------|:-------|:-----|
| 单次调用超时 | 30s（轻量）/ 60s（全量）（`KAIROS_LLM_TIMEOUT_S`，见 [configuration.md](configuration.md) §7） | 超时计入重试次数。轻量档 30s 取值适用于轻量模式启用 LLM 功能（如实体提取）的场景；纯本地 BGE-M3 推理不涉及 LLM 超时 |
| 最大重试次数 | 3 次（`KAIROS_RETRY_MAX_ATTEMPTS=3`，见 [configuration.md](configuration.md) §8.7） | 超限后切换降级模型 |
| 连续失败熔断 | 5 次 | 连续 5 次调用失败（含超时），熔断该模型 5 分钟 |
| 熔断冷却 | 5 分钟 | 冷却期满后放行一次探测调用，成功则恢复，失败则重置冷却计时器 |
| 全链路失败行为 | 跳过本轮推理，写入审计日志（使用事件总线） | 所有模型均不可用时，不阻塞写入和检索 |

重试计入同一 `run_id` 的成本统计，不额外叠加日预算消费。

---

## 二、RTO/RPO

| 组件 | 自动恢复 RTO | 总恢复 RTO | RPO | 恢复方式 |
|:----|:-----------:|:----------:|:----:|:--------|
| Kairos API | ≤ 30s | ≤ 5 分钟 | N/A（无状态） | 容器重启（自动拉起）；总 RTO 含手动干预 |
| 数据库 | ≤ 30s | ≤ 30 分钟 | ≤ 5 分钟（WAL） | 全量 + WAL 回放；自动恢复仅用于 WAL 回档；**RPO ≤ 5 分钟**，与 [requirements-baseline.md](../specification/requirements-baseline.md) §2 N-10 一致性基线对齐 |
| 升华层 | ≤ 30s | ≤ 5 分钟 | ≤ 1 天 | 重启后从 sublimation_queue 表恢复未完成阶段（status=pending/processing，见 [data-model.md](../specification/data-model.md) §sublimation_queue） |

> **说明：** 自动恢复 RTO 目标对齐 NFR（[specification/nfr-specification.md](../specification/nfr-specification.md) §三 故障恢复 ≤30s），适用于自动容器重启/sidecar 恢复场景。总恢复 RTO 涵盖需要备份回放的人工介入场景。

---

## 三、备份策略

| 备份对象 | 频率 | 保留期 | 存储位置 |
|:--------|:----|:-------|:--------|
| 常驻契约文件 | 升华前 | 30 天 | `~/.kairos/backups/core/` |
| **数据库全量** | 每日 05:00 UTC | 30 天 | 备份目录 + 可选远程 |
| **数据库 WAL** | 持续（由 `KAIROS_WAL_ARCHIVE_COMMAND` 触发） | `KAIROS_WAL_ARCHIVE_RETENTION_DAYS`（默认 7 天） | `~/.kairos/wal_archive/` |

> **容量预算**：单次全量备份体积 ≈ 数据库文件体积（10 万条 ≈ 2GB 级，标准模式 NFR 口径；轻量模式 ≤500MB，见 [nfr-specification.md](../specification/nfr-specification.md) §四）；30 天保留总量预算 ≤ 单次体积 × 30 + WAL 7 天 × 日增量 + 升华快照 30 天 × 单次体积。备份目录占用 ≥ 磁盘 75% 时触发清理最旧备份（保留期最短的 WAL 先行），≥ 92% 时停止升华快照并告警（与 §1.4 磁盘告警联动）。
>
> **核算注记**：以 NFR 口径换算（10 万条 ≈ 2GB 级标准模式，[nfr-specification.md](../specification/nfr-specification.md) §四），数据库全量 30 天保留 ≈ 60GB，超出 NFR 标准模式 50GB 磁盘预算（§二）——备份目录须独立磁盘或远程存储承载，或按实际数据量下调保留天数（`KAIROS_BACKUP_RETENTION_DAYS` 已参数化）；WAL 7 天与升华快照保留另计。原「100 万条 ≈ 2GB 级」表述与 NFR 冲突，已按 NFR 口径修正。
>
> **参数化注记**：常驻契约快照与升华快照的「30 天」保留期为基线硬编码值（数据库全量 30 天与 WAL 7 天已由 `KAIROS_BACKUP_RETENTION_DAYS`/`KAIROS_WAL_ARCHIVE_RETENTION_DAYS` 参数化）；快照保留期的参数化列入后续运维批次（届时在 configuration 附录 A 登记），当前按基线值执行。

---

## 四、恢复演练

每月自动运行一次干恢复演练，由健康检查触发。演练内容包括：
1. 从最近一次全量备份恢复至测试数据库
2. 验证数据完整性（行数 + content_hash 校验）
3. 报告恢复时间和通过/失败状态

演练结果写入 `~/.kairos/backups/recovery-drill.log`。
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 可靠性策略：回滚/备份/RTO/RPO/恢复演练与 LLM 熔断。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复——三环不变量引用修正、备份容量预算补全。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：requirements-baseline 链接修正、LLM 超时参数化（KAIROS_LLM_TIMEOUT_S）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：快照保留期参数化注记（基线硬编码 30 天，参数化列入后续批次）。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（changelog 0.0.26）：M-01 三环不变量引用 §6/§10.3→§10.3。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：`error_log`/`events` 表改指真实承载（写入审计日志（使用事件总线）；升华恢复改 sublimation_queue 表 status=pending/processing，见 data-model）；备份容量换算口径修正（100 万条≈2GB 级 → 10 万条≈2GB 级 NFR 口径，原表述与 NFR 冲突）；30 天保留 vs NFR 50GB 磁盘预算核算注记。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：轻量档 LLM 超时取值适用前提注记；版本标记收敛。 |
