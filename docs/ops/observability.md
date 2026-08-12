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
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 可观测性设计

> **⚠ 草稿完善声明**：本文定义的指标、日志格式、告警规则和健康检查端点为设计目标。当前草稿完善阶段无运行代码，可观测性基础设施将在代码启动后实现。

> **定位**：定义 Kairos 系统的指标体系、结构化日志 schema、告警规则。架构文档定义了「做什么」，本文定义「如何看见做了什么」。
>
> **暴露协议**：指标通过 `/metrics` 端点以 Prometheus 文本格式暴露（端口 8010/metrics）——**端点待定义**：在 [api-spec.md](../specification/api-spec.md) §1.8 登记前为设计目标（追缴条目：债务 D-429，见 [debt-collection.md](../governance/debt-collection.md)）。日志通过异步 I/O 写入 `~/.kairos/logs/`（本地模式）或 stdout（容器模式），按日轮转，保留 30 天。

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
| `kairos_forgetting_score` | Gauge | 遗忘评估分布——**freshness（新鲜度）分布**，值越高越新鲜（越不该遗忘），与 detailed-design §3 `EVALUATE_FRESHNESS` 返回值一致（豁免记忆不计入本指标） | bucket |
| `kairos_stale_call_ratio` | Gauge | 过时调用率——被选中进入输出的检索结果中 status=stale/expired（或 fact_freshness 过期）者占比（Deep 模式日频聚合，指标定义见 [acceptance-criteria.md](../quality/acceptance-criteria.md) §一a；**v1.1+ 设计目标**，非 v0.1.0 交付指标） | user_id |
| `kairos_task_success_rate` | Gauge | 任务成功率（集成场景）——三态对比：完整上下文 / 仅检索记忆 / 无记忆（反事实检验，见 [test-strategy.md](../quality/test-strategy.md) §2.7） | mode |
| `kairos_budget_remaining_fen` | Gauge | LLM 日预算剩余（分） | provider |
| `kairos_calibration_last_arrival` | Gauge | 距上次校准信号到达的秒数 | source |
| `kairos_degradation_mode` | Gauge | 当前降级模式（0=正常 1=静默 2=受限交叉验证 3=安全休眠） | — |
| `kairos_availability_ratio` | Gauge | 滚动窗口可用性比率——窗口内健康请求（`GET /health` 返回 ok）时间占比，滚动窗口 SLO 统计的输入指标（目标 ≥99.9%，降级可用性 ≥99%，见 [nfr-specification.md](../specification/nfr-specification.md) §三；可用性声明以生产运行数据为准，基准测试不统计，见 [benchmark-plan.md](../quality/benchmark-plan.md) §3.6） | window（如 30d/90d） |

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
| **跨服务追踪** | [P] 模式（定义见 [security-specification.md](../security/security-specification.md) 引言「适用模式声明」）下通过 HTTP `X-Trace-Id` 头传递 | 对外 API（v1.1 目标） |

**可观测性四支柱**：指标（§一）+ 日志（§二）+ 追踪（本节）+ 告警（§四）。v0.1.0 以日志关联追踪为主，v1.1 目标引入 OpenTelemetry SDK 实现自动插桩（追缴条目：债务 D-432，见 [debt-collection.md](../governance/debt-collection.md)）。

## 四、告警规则

| 告警名 | 条件 | 严重度 | 响应 |
|:-------|:-----|:-------|:-----|
| 数据库断连 | 健康检查连续 3 次失败（基线硬编码值，参数化列入后续运维批次，追缴见 [debt-collection.md](../governance/debt-collection.md) 债务 D-442） | critical | 人工介入 |
| 磁盘黄色预警 | `kairos_disk_usage_pct` > 75% | warning | 写入告警日志，通知运维（联动 [reliability.md](reliability.md) §1.4 异常状态管理） |
| 磁盘红色警戒 | `kairos_disk_usage_pct` > 85% | critical | 暂停非关键写入，仅运行归档和压缩 |
| 磁盘崩溃边缘 | `kairos_disk_usage_pct` > 92% | critical | 丢弃临时数据、截断日志、触发优雅关闭 |
| SLO 跌破 | `kairos_availability_ratio` 滚动窗口低于目标（≥99.9%；降级可用性 ≥99%，见 [nfr-specification.md](../specification/nfr-specification.md) §三） | critical | 人工介入（SLO 数据源：`kairos_availability_ratio` + `GET /health` 探针历史） |
| LLM 熔断触发 | 连续失败次数达 `KAIROS_LLM_CIRCUIT_BREAK_FAILURES`（默认 5 次，含超时） | warning | 熔断该模型冷却 `KAIROS_LLM_CIRCUIT_BREAK_COOLDOWN_S`（默认 5 分钟）；冷却期满放行探测，成功恢复/失败重置计时（见 [reliability.md](reliability.md) §1.5） |
| 写入延迟退化 | 写入 P95 延迟超 NFR 基线持续 5 分钟（基于 `kairos_write_duration_ms` 直方图 P95 分位数） | warning | 检查嵌入服务 |
| 检索延迟退化 | 检索 P95 延迟超 NFR 基线持续 5 分钟（基于 `kairos_read_duration_ms` 直方图 P95 分位数） | warning | 检查 pgvector 索引 |
| 校准中断警告 | 距上次校准 > 3 周期（=900s/15min，对应 `KAIROS_VIRTUAL_CALIBRATION_TIMEOUT` 术语表口径，configuration §1） | info | 检查校准源 |
| 校准中断严重 | 距上次校准 > 6 周期（=1800s/30min，对应 `KAIROS_CALIBRATION_DEGRADE_THRESHOLD`，configuration §1） | warning | 触发降级**告警**——实际降级模式切换仍以他律性降级契约的周期阈值 N/M 为准（`KAIROS_DEGRADATION_*`，configuration §4；N=50/M=200 周期），本告警仅提示校准静默已超常规窗口 |
| 拟真校准失稳 | 虚拟校准连续冲突次数 ≥ `KAIROS_VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD`（默认 3 次，configuration §1） | warning | 检查外部校准源（架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2 虚拟校准生成器） |
| 偏置告警 | 来源多样性收敛或校准衰减超阈 | warning | 人工审查 |
| 正反馈告警 | 偏置在加速放大 | critical | 宪法解释层介入 |
| 身份偏置告警 | 身份一致性记忆系统性压制异质记忆 | warning | 人工审查 |
| 冻结超时 | 冻结持续超过预设时长 | critical | 自动告警至外部管理员 |
| 预算耗尽 | LLM 日预算余额 < 10%（基线硬编码值，对应 `KAIROS_DAILY_BUDGET_FEN` 上限；告警比例参数化列入后续运维批次，追缴见 [debt-collection.md](../governance/debt-collection.md) 债务 D-442） | info | 等待预算重置或充值 |
| 过时调用率超阈 | `kairos_stale_call_ratio` > 20%（设计目标，首轮基准后校准；指标定义见 acceptance-criteria §一a） | warning | 检查遗忘调度器 freshness 参数与检索排序的时间惩罚；> 40% 升级 critical 触发治理面审查 |

### §4a 告警投递

> **告警投递渠道**：告警投递渠道（webhook URL / 邮件 / 监督平面信道）与重试策略已参数化——`KAIROS_ALERT_WEBHOOK_URL`（空=不启用）、`KAIROS_ALERT_EMAIL_ENABLED`、`KAIROS_ALERT_RETRY_MAX`、`KAIROS_ALERT_RETRY_BACKOFF_S` 四项登记于 [configuration.md](../ops/configuration.md) §8.9。默认仅日志 + 审计事件，配置后启用对应渠道。

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
| 耦合计 | 轴耦合告警 + 核心命题证伪信号（判据与响应路径见架构 §10.10；证伪信号不持有系统控制权，仅为信息） | 监督平面专用信道 |
| VAD 独立性 | 独立性证伪信号 | 监督平面专用信道 |

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 可观测性设计：指标/日志/追踪/告警与检测器可见性。 |
| 0.0.2~0.0.14 | 2026-08-05 | （合并占位：changelog 0.0.2~0.0.14 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：/metrics 端点断言式陈述弱化为设计目标（标注「端点待定义，api-spec §1.8 登记前为设计目标」）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：configuration 章节引用修正（§2→§4）。 |
| 0.0.39 | 2026-08-06 | 外部理念吸收批次（changelog 0.0.39）：运行时指标补 `kairos_stale_call_ratio` / `kairos_task_success_rate`（记忆质量评估，指标定义见 acceptance-criteria §一a）；告警规则补「过时调用率超阈」。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：过时调用率指标补 v1.1+ 设计目标注记；[P] 模式补定义指针。 |
| 0.0.53 | 2026-08-08 | round23 深度审计修复批次（changelog 0.0.53）：R23-03 §三 OTel 行补「（追缴条目：债务 D-432）」、暴露协议 /metrics 行补「（追缴条目：债务 D-429）」指针。 |
| 0.0.55 | 2026-08-08 | round24 全面深度审计修复批次（changelog 0.0.55）：认知基础去版本化 30 处改写；引用错位修正（api-spec §6.5 等）；S-19 行为层验收承载；CLI 追缴对齐；blueprint 无编号承诺追缴 D-433~D-438 补登；摘要表 D-422~D-428 补行。 |
| 0.0.65 | 2026-08-08 | round31 深度审计修复批次（changelog 0.0.65）：§1.1 补 `kairos_availability_ratio` 指标（滚动窗口 SLO 统计输入，对齐 NFR §三）；§四 告警表补磁盘三级告警（75/85/92%，联动 reliability §1.4）+ SLO 跌破 + LLM 熔断告警（联动 reliability §1.5）；§五 耦合计检测器补核心命题证伪信号可见性（架构 §10.10）。 |
| 0.0.67 | 2026-08-09 | round33 全面深度审计修复批次（changelog 0.0.67）：§4a「告警投递渠道（勘误）」去除过程标记后缀（零版本标记纪律收敛，正文仅描述当前状态）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.85 | 2026-08-10 | round47 全面深度审计修复批次（changelog 0.0.85）：§1.1 `kairos_forgetting_score` 指标说明改 freshness 口径（值越高越新鲜，与 detailed-design §3 EVALUATE_FRESHNESS 返回值一致，豁免记忆不计入）。详见 changelog 0.0.85 叙述节。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87）：健康检查/告警比例基线硬编码补债务 D-442 指针（2 处）。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |


