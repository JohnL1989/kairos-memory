---
title: Kairos 版本与发布机制
aliases:
  - 版本机制
  - 发布机制
tags:
  - kairos
  - governance
created: 2026-08-13
updated: 2026-08-13
last_reviewed: 2026-08-13
status: design-freeze
---

# Kairos 版本与发布机制

> **确立**：2026-08-13（0.2.0 起生效）。替代此前「包版本固定 0.1.0、changelog 批次无限迭代」的无序状态。

## 1. 版本号体系

- **包版本**（`pyproject.toml` `version` 字段）为唯一发布权威，遵循**语义化版本** `MAJOR.MINOR.PATCH`。
- **changelog 批次号**（`0.1.x`）为内部开发迭代标记（过程记录），与发布版本**解耦**——迭代批次不要求逐次发布。
- 每次发布记录「发布版本 ↔ changelog 批次」映射（changelog 发布批次登记）。

## 2. 语义规则

| 段位 | 规则 | 实例 |
|:---|:---|:---|
| **MAJOR** | 破坏性变更 / 里程碑。`1.0.0` = 全量 v0.1.0（升华/图谱/WM 等 125 项扩展能力）交付 | 0.x → 1.0.0 |
| **MINOR** | 功能新增（实体提取、身份注册表、backfill、新命令、安全契约升级等新能力） | 0.1.0 → 0.2.0 |
| **PATCH** | 修复批次（审计修复、缺陷修复、安全修复，无新功能） | 0.2.0 → 0.2.1 |

## 3. 发布触发条件

**Release 不自动触发**（ci.yml 只在 push/tag 时跑质量门禁，不生成 Release）——发布由显式流程创建（GitHub Actions `release.yml` 或本地 `scripts/release.sh`）。

**触发时机**：
- **MINOR**：功能批次完成且全量门禁通过
- **PATCH**：修复批次完成且全量门禁通过（建议积累 1 个修复批次即可发，保持供应链干净）
- **MAJOR**：里程碑交付（如全量 v0.1.0）

**发布前置门禁（全部通过才可发布）**：
1. `ruff check` + `ruff format --check` + `mypy` 全绿
2. `pytest` 全量通过（PG 测试无环境时以 `KAIROS_PG_TEST_SKIP=1` 跳过并注明）
3. `doc-audit` / `deep-audit` exit 0（含 6.40 第三方来源名门禁）
4. 远端 CI（ci.yml）最近一次 main 运行全绿
5. changelog 已登记待发布批次（叙述节 + 版本记录行）

## 4. 发布流程（自动化）

### 方式 A：GitHub Actions（推荐，全自动）

`.github/workflows/release.yml`——`workflow_dispatch` 手动触发，选择 bump 类型（minor/patch/major）：

1. 自动按语义规则 bump `pyproject.toml` 版本
2. 快速门禁（ruff check + mypy）——完整门禁由 ci.yml 在 tag 推送后兜底
3. 自动 commit（`chore: bump version to vX.Y.Z`）+ annotated tag + push（触发 ci.yml 全量验证）
4. `gh release create vX.Y.Z --generate-notes`（GitHub 自动生成 commit 摘要）

### 方式 B：本地脚本

`scripts/release.sh <minor|patch|major>`——等效流程，适合需要交互确认的场景。

## 5. 发布产物

- `git tag vX.Y.Z`（annotated）+ push
- GitHub Release：标题 `vX.Y.Z`，正文为 changelog 对应批次摘要（或 `--generate-notes`）
- `pyproject.toml` version 同步
- changelog 发布批次登记（「发布 vX.Y.Z」行 + 版本记录表）

## 6. 历史映射

| 发布版本 | 对应 changelog 批次 | 内容 |
|:---|:---|:---|
| v0.1.0 | 0.1.0 | 竖切首版（16 表 / 31 端点 / 21 CLI / 15 MCP / 测试 288） |
| v0.2.0 | 0.1.1~0.1.9 | 实体信号激活（三信号 3/3）、身份注册表激活、存量实体回溯、S-01/S-09 安全契约、CI 真实化、测试并行化、第三方零标记门禁 6.40、状态声明零漂移门禁 6.41 |

## 版本记录

| 版本 | 日期 | 说明 |
|:---|:---|:---|
| 0.0.1 | 2026-08-13 | 版本与发布机制文档确立（v0.2.0 发布时创建）。 |
| 0.2.0 | 2026-08-13 | v0.2.0 发布（聚合 0.1.1~0.1.9，pyproject 0.2.0）。 |
