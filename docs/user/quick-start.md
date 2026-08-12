---
title: Kairos 快速入门
aliases:
  - 快速入门
  - Quick Start
tags:
  - kairos
  - user
  - quickstart
created: 2026-07-20
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 快速入门

> **状态声明**：本文描述的 CLI 命令（`kairos init`、`kairos serve` 等）以竖切交付的 CLI 实现为准（18 命令，`kairos --help`）；Python wheel 已构建（`dist/kairos-0.1.0*`）。

> **定位**：约 2 分钟跑通 Kairos 最小闭环（**不含首次模型权重下载耗时**，见第四步）。无需 PostgreSQL，轻量模式（SQLite）开箱即用。
>
> **⚠ 说明**：以下命令（`pip install kairos`、`kairos serve` 等）以 CLI 实现为准；wheel 已构建（`dist/kairos-0.1.0*`），Docker 镜像待发布（见 [deployment.md](../ops/deployment.md)）。

---

## 前置条件

- Python ≥ 3.11
- pip 或 uv
- 设置 `KAIROS_SALT` 环境变量（S-05 要求无 Salt 拒绝启动）。由 `kairos init --init-key` 自动生成，前置条件阶段无需手动设置
- `KAIROS_API_KEY`、`KAIROS_SECRET_KEY`、`KAIROS_AUDIT_HMAC_KEY` 同样由 `init --init-key` 自动生成——前置条件阶段无需手动设置任何密钥

## 第一步：安装

```bash
pip install kairos
```

## 第二步：初始化并生成密钥

```bash
# 初始化数据库并自动生成全部密钥
kairos init --init-key

# init --init-key 自动生成 KAIROS_API_KEY / KAIROS_SALT / KAIROS_SECRET_KEY / KAIROS_AUDIT_HMAC_KEY
# 并写入环境文件（默认 ~/.kairos/.env——密钥文件路径，非 secrets.yaml）
# 启动时自动读取，无需手动 export
```

> S-01 要求无有效 API Key 时系统拒绝所有请求。Key 生成后请妥善保管。

## 第三步：初始化

```bash
# 轻量模式——使用 SQLite，零配置
kairos init --db sqlite:///$HOME/.kairos/kairos.db
```

> **注（澄清）**：第二步的 `kairos init --init-key` 与第三步的 `kairos init --db ...` 是**同一初始化命令的两种用途**（密钥生成 vs 数据库初始化），实际使用执行一次 `kairos init` 即可完成——首次执行时两个子项一并处理；重复执行 `kairos init` 不会覆盖已生成的密钥（幂等），仅对缺失项补初始化。

## 第四步：启动

```bash
kairos serve --port 8010
```

看到输出 `Kairos started on http://localhost:8010` 即启动成功。

> **首次启动注记**：轻量模式使用本地 BGE-M3 嵌入，权重在首次 `kairos serve` 时自动下载（见 [development-setup.md](../development/development-setup.md) §环境依赖）——该次下载耗时取决于网络带宽，不计入本文「约 2 分钟」口径；后续启动直接读取本地缓存。下载失败或中断的处置见 [troubleshooting.md](../ops/troubleshooting.md)。

## 第五步：写入一条记忆

```bash
kairos write kairos://_user/default/playground/ \
  --content "Kairos 快速入门测试记忆" \
  --contract ondemand \
  --source user_input
```

> `--source` 为 CLI 参数名，对应 API 字段 `provenance`（来源标识，S-15 必填，缺失返回 422）——CLI 与 API 的命名映射见 [api-spec.md](../specification/api-spec.md) §3 CLI 表。路径使用用户持久域 `_user/default/`（域路由表见架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §3.4；`default` 为零配置模式默认用户路径）。

输出应类似：
```text
写入成功：abc-def-123-456
```

## 第六步：检索

```bash
kairos search "快速入门" --limit 5
```

输出应返回刚写入的记忆。

## 第七步：浏览路径空间

```bash
kairos tree kairos://_user/default/playground/ --depth 3
kairos ls kairos://_user/default/playground/
```

## 第八步：查看系统状态

```bash
kairos status
```

输出应显示各组件的健康状态。

---

## 完成

你已完成 Kairos 的最小闭环：写入 → 检索 → 路径浏览。全部操作约 2 分钟（首次启动的 BGE-M3 权重下载时间另计）。

> 下一步：阅读 [user-guide.md](user-guide.md) 了解核心操作。
> 部署生产环境：使用标准模式（PostgreSQL + pgvector），见 [ops/deployment.md](../ops/deployment.md)。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 快速入门：轻量模式约 2 分钟最小闭环教程（设计目标）。 |
| 0.0.4~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.4~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：frontmatter 与版本记录同步（第二轮全库深度审计修复批次）。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：init 幂等澄清（两次 init 的关系）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：--source 参数映射 provenance 注记。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：api-spec §三→§3 引用联动（4-1）。 |
| 0.0.59 | 2026-08-08 | round26 全面深度审计修复批次（changelog 0.0.59）：U-04「约 2 分钟」口径澄清为不含首次模型权重下载；第四步补首次启动 BGE-M3 权重下载注记与 development-setup / troubleshooting 指针。 |
| 0.0.68 | 2026-08-09 | round34 全面深度审计修复批次（changelog 0.0.68）：第五/七步演示路径 `kairos://playground/` 改指 `kairos://_user/default/playground/`（用户持久域，对齐架构 §3.4 域路由表与 api-spec CLI 示例路径惯例）。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |

