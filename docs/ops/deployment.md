---
title: Kairos 部署指南
aliases:
  - Kairos 部署
  - 部署配置
tags:
  - kairos
  - deployment
  - ops
created: 2026-07-18
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 部署指南

> **章节导航**——按下表定位所需章节：
>
> | 章节 | 主题 |
> |:----|:----|
> | 一、三级部署模式 | 轻量/标准/全量三级部署 |
> | 二、数据目录 | 持久化目录与文件布局 |
> | 三、环境变量 | 环境变量清单 |
> | 四、启动与健康检查 | 启动流程与健康探针 |
> | 五、Docker 部署参考 | 容器化部署参考 |
> | 六、数据库初始化 | 数据库初始化与迁移 |
> | 七、日志与监控 | 日志与指标 |
> | 八、版本升级 | 升级流程 |
> | 九、进程级隔离演进路径 | 多进程演进路径（外部建议 R-2） |
>


> **文档定位：** 本指南描述 Kairos 的部署模式、配置项、数据目录结构和运维基础。不包含系统架构设计（见 [docs/foundation/architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)）或可靠性策略（见 [docs/ops/reliability.md](reliability.md)）。
>
> **⚠ 草稿完善声明**：以下部署步骤（`pip install kairos`、`kairos/kairos:latest` 等）为目标示例。当前草稿完善阶段期无构建产物或 Docker 镜像，部署命令将在代码启动后交付。
>
> **单租户声明**：Kairos 为单租户系统（见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §10.7）。单部署实例服务于单用户——`{user_id}` 仅为内部路径组织，不表示多租户隔离。三级 API Key（read/write/admin）用于操作权限分级，非租户隔离。部署时不需配置多租户代理。部署模式中的「正式生产/全功能」指功能完整度（含 Docker/备份/告警），不改变单租户约束。

---

## 一、三级部署模式

> **命名说明**：本文「轻量模式」对应 architecture [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.5 的「内核级」。全库统一表述为：内核级（轻量）/标准级/全量级。

| 维度 | 轻量模式 | 标准模式 | 全量模式 |
|:-----|:--------|:--------|:--------|
| **安装方式** | `pip install kairos && kairos serve` | `docker compose up -d` | `docker compose -f docker-compose.full.yml up -d` |
| **数据库** | SQLite + sqlite-vec | PostgreSQL + pgvector | PostgreSQL + pgvector |
| **启动时间** | ~10 秒（扩展设计值——NFR 仅定义标准模式启动 ≤10s，见 [nfr-specification.md](../specification/nfr-specification.md) §三） | ~10 秒 | ~15 秒（扩展设计值——NFR 仅定义标准模式启动 ≤10s，见 [nfr-specification.md](../specification/nfr-specification.md) §三） |
| **记忆容量** | 10 万条 | 100 万条 | ≥100 万条 |
| **升华层** | 受限（空闲单线） | 可用 | 完整多线 |
| **策略层** | 内置（使用权重衰减） | 完整激活调度 | 完整 + 探索投资 |
| **元认知层** | — | — | 完整监测器族 |
| **宪法主权面** | 简化（仅外部校准端口 + 必选宪法约束，架构 §0.5 内核级） | 舍弃完整形态，继承简化（外部校准端口为不可裁剪最小承载，架构 §0.5 标准级） | 完整（外部校准 + 宪法修订端口 + 监督平面） |
| **推理皮层** | — | — | 完整（架构 §0.5 全量级组成） |
| **适用场景** | 个人开发、试用 | 正式生产 | 全功能部署 |

三种模式下 API 兼容，核心记忆操作（写入/检索）均可用。**遗忘能力注记**：遗忘调度器在竖切（v0.1.0-slice）内显式启用；完整系统形态下 `KAIROS_FEATURE_FORGETTING_ENGINE` 默认 OFF（仅基础 TTL 清理），需在配置中显式开启（见 [configuration.md](configuration.md) §11 特征标志与架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8）。差异在于元认知层监测深度（全量模式有完整监测器族）和跨层协调能力——轻量模式为独立进程，标准/全量模式支持 Docker 编排。切换只需要更改配置文件中的数据源指向和部署方式。

> **认知组件声明（部分正交）**：上表描述的是**基础设施与部署维度**的差异（数据库/容量/编排方式），与认知组件启用范围**部分正交**——认知组件由 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 的**命名配置集**（`kairos-minimal` / `kairos-slice` / `kairos-full`）决定，而非由部署模式独立控制。默认仅启用核心 LTM、路径空间、三信号混合检索和基础审计日志；功能标志（帕累托排序、元认知监测器、宪法治理、升华管道等）默认 OFF，须在配置中显式启用。命名配置集与部署模式的关系：轻量/标准模式可搭配 `kairos-minimal` 或 `kairos-slice`；**全量模式绑定 `kairos-full`**（其定义即「全部特征标志 ON」）为唯一例外——其余「部署模式 × 命名配置集」组合不在受支持范围。详见配置文档中对应 `KAIROS_FEATURE_*` 参数及架构文档 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 特征标志编码纪律与配置集降级阶梯。

---

## 二、数据目录

```text
~/.kairos/
├── kairos/                  路径空间根目录（内存映射 + 持久化）
├── core/                    常驻契约 · 索引+文件
├── memories/                按需契约 · 向量存储
├── sessions/                按需契约 · 对话日志
├── strategies/              升华产物
├── archive/                 过期数据
└── backups/
    └── core/                常驻契约备份
```

---

## 三、环境变量

| 变量 | 必填 | 默认值 | 说明 |
|:----|:----|:-------|:-----|
| `KAIROS_DB_DSN` | 标准模式必填；轻量模式（SQLite）自动创建 | `sqlite:///$HOME/.kairos/kairos.db`（轻量模式，与 backup/restore 路径一致） | 数据库连接串 |
| `KAIROS_LOG_LEVEL` | 否 | `info` | 日志级别：`debug` / `info` / `warn` / `error`（见 §五 日志级别说明） |
| `KAIROS_LITE_MODE` | 否 | `true` | 轻量模式开关（true=SQLite/false=PostgreSQL）。设为 false 时需配置 `KAIROS_DB_DSN` |
| `KAIROS_DB_PASSWORD` | 标准模式需 | — | PostgreSQL 密码（docker-compose 部署用，非 DSN 内部含密码时不需要） |
| `KAIROS_API_KEY` | 标准模式是；轻量模式否 | — | API 认证密钥（标准模式用；轻量模式以 `KAIROS_API_KEY_HASH` 单 Key 校验代替，见下行与 [security-specification.md](../security/security-specification.md) §2.1） |
| `KAIROS_API_KEY_HASH` | 轻量模式是；标准模式否 | — | 轻量模式单 Key 认证（密钥哈希口径，文件权限 600；竖切形态，见 [slice-implementation-guide.md](../development/slice-implementation-guide.md) §一 组件 9 与 [configuration.md](../ops/configuration.md) 附录 A） |
| `KAIROS_SALT` | 是 | — | PBKDF2 盐值（S-05） |
| `KAIROS_SECRET_KEY` | 是 | — | AES-256-GCM 敏感字段加密密钥 |
| `KAIROS_AUDIT_HMAC_KEY` | 是 | — | HMAC-SHA256 审计链签名密钥 |
| `KAIROS_LLM_API_KEY` | 标准/全量模式 ✅；轻量模式 ❌ | — | LLM 供应商 API Key（轻量模式使用本地 BGE-M3 嵌入，不需 LLM，与 [user-guide.md](../user/user-guide.md) 一致） |
| `KAIROS_LLM_ENDPOINT` | 标准/全量模式 ✅；轻量模式 ❌ | — | LLM 供应商端点（轻量模式使用本地 BGE-M3 嵌入，不需 LLM 端点，与 `KAIROS_LLM_API_KEY` 口径一致） |
| `KAIROS_ADMIN_IPS` | 生产推荐 | — | 管理端点 IP 白名单 |
| `KAIROS_SCHEDULER_INTERVAL` | 否 | 300s | 调度器检查周期 |
| `KAIROS_DAILY_BUDGET_FEN` | 否 | 20000 | LLM 日预算上限（分） |
| `KAIROS_CORE_LIMIT_BYTES` | 否 | 25KB | 常驻契约索引上限 |
| `KAIROS_CORE_LIMIT_LINES` | 否 | 200 | 常驻契约索引行数上限 |
| `KAIROS_SEARCH_DEFAULT_LIMIT` | 否（deployment 自定） | 5 | 默认召回上限（正文未收录，已在 [configuration.md](configuration.md) 附录 A 登记，默认值由部署覆盖） |
| `KAIROS_RATE_LIMIT_WRITE_PER_MIN` | 否 | 60 | 写操作限流（单客户端级别） |
| `KAIROS_RATE_LIMIT_READ_PER_MIN` | 否 | 120 | 读操作限流 |
| `KAIROS_INPUT_LIMIT_CONTENT_BYTES` | 否 | 65536 | 单条内容上限（字节） |
| `KAIROS_SSRF_ALLOWED_HOSTS` | 生产推荐 | `api.deepseek.com` | 出站 URL 白名单 |
| `KAIROS_WAL_ARCHIVE_RETENTION_DAYS` | 否 | `7` | WAL 归档保留天数（[configuration.md](configuration.md) §7 引用，默认 7 天）。设为 0 表示不保留归档文件；设为空字符串禁用归档（与 [configuration.md](configuration.md) §7 的 `KAIROS_WAL_ARCHIVE_COMMAND` 语义一致） |
| `KAIROS_SSRF_IP_CHECK` | 否 | `true` | 解析 URL 后二次校验 IP，阻断内网/元数据地址 |
| `KAIROS_SSRF_DNS_REBIND_PROTECTION` | 否 | `true` | DNS 重绑定防护（DNS 解析结果与 HTTP 请求时的 IP 不一致时拒绝） |
| `KAIROS_INPUT_LIMIT_QUERY_CHARS` | 否（默认 500；生产环境建议显式配置） | `500` | query 字段最大字符数。此参数对应 [configuration.md](configuration.md) §7 与 threat-model §三 的安全要求——漏配时以默认值 500 生效；生产环境建议显式配置以符合安全基线 |
| `KAIROS_WAL_ARCHIVE_COMMAND` | 否 | `cp %p ~/.kairos/wal_archive/%f` | WAL 归档命令 |

> **密钥生成引导**：上表四个 `KAIROS_*` 密钥（`API_KEY` / `SALT` / `SECRET_KEY` / `AUDIT_HMAC_KEY`）可通过 `kairos init --init-key` 一次性生成并写入环境文件，无需手动逐一配置。`KAIROS_LLM_API_KEY` 为外部 LLM 供应商凭证，需用户自行申请，不在 `init` 自动生成范围内。详见 [user-guide.md](../user/user-guide.md) 与 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §1.2。

---

## 四、启动与健康检查

轻量模式：
```bash
kairos serve              # 默认 SQLite 模式轻量
# PostgreSQL 模式：kairos serve --pg（等价于设置 KAIROS_LITE_MODE=false，--pg 覆盖环境变量中的 LITE_MODE 值；规划扩展命令，api-spec §3 未登记，须纳入债务 D-430 追缴清单）
kairos health             # 健康检查
```

标准模式：
```bash
docker compose up -d       # 启动全部服务
docker compose logs -f     # 查看日志
curl http://localhost:8010/health  # 健康检查端点
```

健康检查返回 JSON，包含各组件状态（整体 status 取值 `ok|degraded|down`）：

**标准模式**（API 嵌入模型 `text-embedding-3-small`）：
```json
{
  "status": "ok",
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

**轻量模式**（本地 BGE-M3，embedding 不暴露为独立组件）：
```json
{
  "status": "ok",
  "components": {
    "api": {"status": "ok", "latency_ms": 1},
    "db": {"status": "ok", "db_size_mb": 42},
    "scheduler": {"status": "running", "last_tick": "2026-07-20T10:00:00Z"}
  },
  "deployment_mode": "lightweight",
  "uptime_seconds": 7200
}
```

> **轻量模式说明**：components 中不含 `sublimation`、`calibration`、`embedding`（BGE-M3 本地推理不暴露为独立组件），`db` 使用 SQLite（无连接池指标）。**校准能力注记**：轻量模式不含 calibration **组件**（不暴露为 health 独立组件），但保留外部校准端口能力（架构内核级梯度「外部校准端口不可裁剪」——校准信号接收与处理仍可用，仅不单独呈现为健康检查组件）。

---

## 五、Docker 部署参考

> **全量模式（docker-compose.full.yml）说明**：全量模式 = 标准模式 + **全部特征标志 ON**（对应架构 §0.8 命名配置集 `kairos-full`——全部标志 ON 为唯一受支持的全量形态，见架构 §0.8「命名配置集与组合约束」）。与标准模式的 compose 差异仅在**环境变量与特征标志**（启用完整监测器族 `KAIROS_FEATURE_META_COGNITION=true` 与探索投资等，见 §一 部署模式表与架构 §0.8 特征标志），服务拓扑相同（kairos + db 双服务）。`docker-compose.full.yml` 参考骨架：复制下方 compose 文件，在 `environment` 追加 `kairos-full` 配置集所需特征标志（共 12 个标志全部置 ON，见 [configuration.md](configuration.md) §11 与架构 §0.8），并在启动命令中校验全量模式启动时间 ~15 秒（扩展设计值——NFR 仅定义标准模式启动 ≤10s，见 [nfr-specification.md](../specification/nfr-specification.md) §三；标准模式 ~10 秒）。

```yaml
# docker-compose.yml
services:
  kairos:
    image: kairos/kairos:v0.1.0-dev    # 草稿阶段无发布镜像，tag 仅供本地构建参考，不可用于 docker pull
    ports:
      - "127.0.0.1:8010:8010"
    environment:
      - KAIROS_DB_DSN=postgresql://kairos:${KAIROS_DB_PASSWORD}@db:5432/kairos
      - KAIROS_API_KEY=${KAIROS_API_KEY}
      - KAIROS_SALT=${KAIROS_SALT}
      - KAIROS_SECRET_KEY=${KAIROS_SECRET_KEY}
      - KAIROS_AUDIT_HMAC_KEY=${KAIROS_AUDIT_HMAC_KEY}
      - KAIROS_LLM_API_KEY=${KAIROS_LLM_API_KEY}
      - KAIROS_LITE_MODE=false
      - KAIROS_LLM_ENDPOINT=${KAIROS_LLM_ENDPOINT}
    volumes:
      - ~/.kairos:/root/.kairos
    depends_on:
      - db
  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=kairos
      - POSTGRES_USER=kairos
      - POSTGRES_PASSWORD=${KAIROS_DB_PASSWORD}
    volumes:
      - kairos_db:/var/lib/postgresql/data

volumes:
  kairos_db:
```

---

## 六、数据库初始化

轻量模式（SQLite）首次启动时自动创建数据库和表结构。升级/降级等 schema 变更需手动执行迁移命令（见下文）。

标准模式（PostgreSQL）：
```bash
kairos init --db                # 无参=使用配置文件 DSN
kairos init --db <dsn>          # 显式指定 DSN，详见 development-setup.md
kairos db migrate     # 执行迁移
kairos db verify      # 验证数据完整性
kairos db backup      # 手动备份
```

迁移文件位于 `~/.kairos/migrations/`，按时间戳命名。支持回滚。

---

## 七、日志与监控

Kairos 输出结构化 JSON 日志到 stdout（容器部署模式）；本地运行时同时写入 `~/.kairos/logs/`（按日轮转，保留 30 天）。日志格式见 [observability.md](observability.md) §二。

```json
{"level":"info","timestamp":"2026-07-18T10:00:00Z","logger":"kairos.scheduler","message":"sublimation stage 2 completed","events_processed":42}
```

日志级别：`debug` / `info` / `warn` / `error`。通过 `KAIROS_LOG_LEVEL` 环境变量配置（取值范围 `debug|info|warn|error`）。

---

## 八、版本升级

> 版本升级/降级完整步骤（轻量/标准模式命令、`kairos db migrate` / `kairos db migrate rollback`、升级前备份要求）以 [runbook.md](runbook.md) §3 升级与降级为权威——本文仅保留指针，不重复步骤。

---
## 九、进程级隔离演进路径（外部建议 R-2）

> **背景**：架构 §2.2 已声明单进程部署下 ME-1/ME-2/ME-3（监测/治理/自观察）为逻辑隔离而非故障隔离——"治理不影响监测"的承诺在单进程下有漏洞。本节定义从单进程到进程级隔离的演进路径与各阶段部署形态。

| 阶段 | 隔离项 | 部署形态 | 交付版本 |
|:----|:-------|:---------|:--------|
| **已隔离** | 宪法解释层独立故障域（架构 §0.4——不驻留被治理系统进程空间）；监督平面独立加载（架构 §1.7——独立于宪法主权面生命周期，独立快照校验通道） | 标准/全量模式独立进程/容器 | v0.1.0 设计承诺 |
| **v0.1.0.x 候选** | 元认知层 ME-1/ME-2/ME-3 分离——监测子域独立进程（治理操作挂起时监测不阻塞，消除"监测被治理拖累"的二级失效）；审计庭独立感知通道保持 | 标准/全量模式：`kairos-meta-monitor` 独立进程；轻量模式维持单进程 | v0.1.0.x |
| **v1.1 目标** | 全组件容器化——接入/WM/策略层/存储层/元认知层/宪法主权面/监督平面各独立容器，事件总线为唯一跨进程通信 | Docker Compose 多服务编排 | v1.1 |

**生产部署建议**：v0.1.0 生产部署至少启用「已隔离」阶段（宪法解释层 + 监督平面独立进程）；对长期无人值守运行场景，建议在 v0.1.0.x 升级 ME-1/ME-2/ME-3 分离——监测盲区是元认知层自我修复能力的前提，逻辑隔离不足以覆盖治理异常场景。

**降级兼容**：各阶段隔离均不影响单进程模式运行——隔离是部署形态选项，非强制要求；轻量模式始终维持单进程（架构 §2.2 声明不变量）。

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 部署指南：轻量/标准/全量三级部署模式、环境变量与 Docker 参考。 |
| 0.0.2~0.0.11 | 2026-08-04 | （合并占位：changelog 0.0.2~0.0.11 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：KAIROS_SEARCH_DEFAULT_LIMIT 附录登记勘误；轻量模式校准能力注记（保留外部校准端口，不暴露 health 组件）。 |
| 0.0.17 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.17，外部建议 R-2 落地）：新增 §九 进程级隔离演进路径——已隔离项（宪法解释层/监督平面）+ v0.1.0.x 候选（ME-1/2/3 分离）+ v1.1 目标（全组件容器化）+ 生产部署建议 + 降级兼容。 |
| 0.0.37 | 2026-08-06 | round15 深度审计修复批次：全量模式启动时间 ~15 秒补「扩展设计值」注记（NFR 仅定义标准模式启动 ≤10s，§一 部署模式表与 §五 compose 说明两处）；`KAIROS_LLM_ENDPOINT` 必填口径与 `KAIROS_LLM_API_KEY` 对齐（标准/全量 ✅，轻量 ❌）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：全量模式与架构 kairos-full 配置集对齐（补宪法主权面/推理皮层维度）；日志字段统一 logger；轻量模式启动时间补扩展设计值注记。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：§八 版本升级压缩为指针（runbook §3 权威）；--pg 规划扩展注记；「试用」笔误。 |
| 0.0.51 | 2026-08-08 | round22 审计修复批次（changelog 0.0.51）：§一 认知组件声明改写为部分正交语义（部署模式决定基础设施维度、命名配置集决定认知组件；全量模式绑定 kairos-full 为唯一例外）。 |
| 0.0.55 | 2026-08-08 | round24 全面深度审计修复批次（changelog 0.0.55）：认知基础去版本化 30 处改写；引用错位修正（api-spec §6.5 等）；S-19 行为层验收承载；CLI 追缴对齐；blueprint 无编号承诺追缴 D-433~D-438 补登；摘要表 D-422~D-428 补行。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：补章节导航表（一~九）。 |
| 0.0.94 | 2026-08-11 | round54 全面深度审计修复批次（changelog 0.0.94）：标准级宪法主权面措辞对齐（「舍弃」→「舍弃完整形态，继承简化」——与架构 §0.5「继承内核级简化形态」表述一致，消除「完全移除」误读可能）。 |
| 0.0.96 | 2026-08-11 | 定稿审查处置批次（changelog 0.0.96）：§三 环境变量表补 `KAIROS_API_KEY_HASH`（轻量模式单 Key 认证，密钥哈希口径，竖切形态——原表仅 KAIROS_API_KEY 覆盖不全），KAIROS_API_KEY 行补模式区分。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |


