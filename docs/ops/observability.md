---
title: Kairos 可观测性设计
aliases:
  - 可观测性
  - Observability
tags:
  - kairos
  - ops
  - monitoring
created: 2026-07-20
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 可观测性设计

> **⚠ 草稿完善声明**：本文定义的指标、日志格式、告警规则和健康检查端点为设计目标。当前草稿完善阶段无运行代码，可观测性基础设施将在代码启动后实现。

> **定位**：定义 Kairos 系统的指标体系、结构化日志 schema、告警规则。架构文档定义了「做什么」，本文定义「如何看见做了什么」。
>
> **暴露协议**：指标通过 `/metrics` 端点以 Prometheus 文本格式暴露（端口 8010/metrics）——**端点待定义**：在 [api-spec.md](../specification/api-spec.md) §1.8 登记前为设计目标。日志通过异步 I/O 写入 `~/.kairos/logs/`（本地模式）或 stdout（容器模式），按日轮转，保留 30 天。

---

## 一、指标体系

### 1.1 运行时指标

| 指标 | 类型 | 说明 | 标签 |
|:----|:----|:-----|:-----|
| `kairos_memory_count` | Gauge | 当前存储记忆总数 | layer, contract |
| `kairos_disk_usage_pct` | Gauge | 磁盘使用率（%）。告警阈值 75%/85%/92% 对应黄色/红色/崩溃三级，见 [reliability.md](reliability.md) §1.4 | — |
| `kairos_write_total` | Counter | 写入操作累计次数 | contract, status |
| `kairos_read_total` | Counter | 检索操作累计次数 | method(path/semantic) |
| `kairos_write_duration_ms` | Histogram | 写入延迟 | contract |
| `kairos_read_duration_ms` | Histogram | 检索延迟 | method |
| `kairos_event_bus_queue_depth` | Gauge | 事件总线队列深度 | priority |
| `kairos_sublimation_stage` | Gauge | 升华管道各阶段计数 | stage |
| `kairos_forgetting_score` | Gauge | 遗忘得分分布 | bucket |
| `kairos_budget_remaining_fen` | Gauge | LLM 日预算剩余（分） | provider |
| `kairos_calibration_last_arrival` | Gauge | 距上次校准信号到达的秒数 | source |
| `kairos_degradation_mode` | Gauge | 当前降级模式（0=正常 1=静默 2=受限交叉验证 3=安全休眠） | — |

### 1.2 健康检查

**`GET /health`** 返回：

```json
{
  "status": "ok | degraded | down",
  "components": {
    "api": {"status": "ok", "latency_ms": 2},
    "db": {"status": "ok", "pool_connections": 5, "pool_available": 3},
    "scheduler": {"status": "running", "last_tick": "2026-07-20T10:00:00Z"},
    "embedding": {"status": "ok", "model": "text-embedding-3-small"},
    "sublimation": {"status": "idle", "queue_length": 0},
    "calibration": {"status": "active", "last_arrival": "2026-07-20T09:55:00Z", "mode": "normal"}
  },
  "deployment_mode": "standard",
  "uptime_seconds": 3600
}
```

> **轻量模式**：components 不含 embedding/sublimation/calibration（见 [deployment.md](deployment.md) §四）。

## 二、日志 Schema

每个日志条目为 JSON 行（JSON Lines 格式），固定字段：

```json
{
  "timestamp": "2026-07-20T10:00:00.000Z",
  "level": "info",
  "logger": "kairos.storage.forgetting",
  "message": "forgetting score threshold reached",
  "module": "forgetting_scheduler",
  "function": "scan_and_forget",
  "line": 42,
  "memory_id": "abc-def-123",
  "forgetting_score": 0.87,
  "event_id": "uuid-456",
  "duration_ms": 15,
  "error_code": null,
  "trace_id": "trace-789"
}
```

## 三、分布式追踪

日志 schema 已包含 `trace_id` 字段（§二）。v0.1.0 使用应用层日志关联实现请求级追踪——

| 追踪边界 | 实现方式 | 覆盖范围 |
|:---------|:---------|:---------|
| **单请求追踪** | 入口生成 `trace_id`，贯穿存储/WM/策略各层日志 | 写入/检索/校准请求全链路 |
| **异步链路追踪** | 升华/遗忘等后台任务使用独立 `trace_id`，在事件日志中通过 `parent_trace_id` 关联 | 后台批量操作 |
| **跨服务追踪** | [P] 模式下通过 HTTP `X-Trace-Id` 头传递 | 对外 API（v1.1 目标） |

**可观测性四支柱**：指标（§一）+ 日志（§二）+ 追踪（本节）+ 告警（§四）。v0.1.0 以日志关联追踪为主，v1.1 目标引入 OpenTelemetry SDK 实现自动插桩。

## 四、告警规则

| 告警名 | 条件 | 严重度 | 响应 |
|:-------|:-----|:-------|:-----|
| 数据库断连 | 健康检查连续 3 次失败（基线硬编码值，参数化列入后续运维批次） | critical | 人工介入 |
| 写入延迟退化 | 写入 P95 延迟超 NFR 基线持续 5 分钟（基于 `kairos_write_duration_ms` 直方图 P95 分位数） | warning | 检查嵌入服务 |
| 检索延迟退化 | 检索 P95 延迟超 NFR 基线持续 5 分钟（基于 `kairos_read_duration_ms` 直方图 P95 分位数） | warning | 检查 pgvector 索引 |
| 校准中断警告 | 距上次校准 > 3 周期（=900s/15min，对应 `KAIROS_VIRTUAL_CALIBRATION_TIMEOUT` 术语表口径，configuration §1） | info | 检查校准源 |
| 校准中断严重 | 距上次校准 > 6 周期（=1800s/30min，对应 `KAIROS_CALIBRATION_DEGRADE_THRESHOLD`，configuration §1） | warning | 触发降级**告警**——实际降级模式切换仍以他律性降级契约的周期阈值 N/M 为准（`KAIROS_DEGRADATION_*`，configuration §2；N=50/M=200 周期），本告警仅提示校准静默已超常规窗口 |
| 拟真校准失稳 | 虚拟校准连续冲突次数 ≥ `KAIROS_VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD`（默认 3 次，configuration §1） | warning | 检查外部校准源（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 虚拟校准生成器） |
| 偏置告警 | 来源多样性收敛或校准衰减超阈 | warning | 人工审查 |
| 正反馈告警 | 偏置在加速放大 | critical | 宪法解释层介入 |
| 身份偏置告警 | 身份一致性记忆系统性压制异质记忆 | warning | 人工审查 |
| 冻结超时 | 冻结持续超过预设时长 | critical | 自动告警至外部管理员 |
| 预算耗尽 | LLM 日预算余额 < 10%（基线硬编码值，对应 `KAIROS_DAILY_BUDGET_FEN` 上限；告警比例参数化列入后续运维批次） | info | 等待预算重置或充值 |

### §4a 告警投递

> **告警投递渠道（勘误）**：告警投递渠道（webhook URL / 邮件 / 监督平面信道）与重试策略已参数化——`KAIROS_ALERT_WEBHOOK_URL`（空=不启用）、`KAIROS_ALERT_EMAIL_ENABLED`、`KAIROS_ALERT_RETRY_MAX`、`KAIROS_ALERT_RETRY_BACKOFF_S` 四项登记于 [configuration.md](../ops/configuration.md) §8.9。默认仅日志 + 审计事件，配置后启用对应渠道。

## 五、元认知层检测器输出可见性

| 检测器 | 输出 | 外部可见性 |
|:-------|:-----|:----------|
| 流形曲率/密度 | 几何拓扑报告 | 通过审计日志 |
| 分布偏移 | 偏移量 + 方向 | 通过事件总线告警 |
| 盲区标注 | 盲区地图 | 只读 API |
| 叙事连贯性 | 趋势报告 | 通过校准端口 |
| 来源混淆/图式同化 | 告警（预留） | v1.1 启用 |
| 偏置放大率 | 正反馈告警 | 监督平面专用信道 |
| 自我参照效应 | 身份偏置告警 | 监督平面专用信道 |
| 耦合计 | 轴耦合告警 | 监督平面专用信道 |
| VAD 独立性 | 独立性证伪信号 | 监督平面专用信道 |

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 可观测性设计：指标/日志/追踪/告警与检测器可见性。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：/health 示例对齐 deployment 契约（deployment_mode 字段、标准模式 embedding）、告警投递渠道声明（§4a）、校准中断告警关联 TIMEOUT 参数。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：可观测性四支柱、补拟真校准失稳告警行。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：校准中断严重告警改「触发降级告警」并注明 N/M 契约为准；§4a 告警投递渠道勘误（KAIROS_ALERT_* 已参数化）；硬编码阈值加基线注记（健康检查 3 次/预算 10%）。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：/metrics 端点断言式陈述弱化为设计目标（标注「端点待定义，api-spec §1.8 登记前为设计目标」）。 |
