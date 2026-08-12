---
title: Kairos 发布指引
aliases:
  - 发布管理
  - release-process
tags:
  - kairos
  - governance
  - release
created: 2026-07-21
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 发布流程

> **状态声明**：本文为意图声明文档，非可执行发布流程。当前 Kairos 处于文档草稿阶段（无运行代码），以下流程以代码就绪为前置条件。待 v0.1.0-draft 定稿、代码启动后，本文须重写为可执行的 CI/CD 流程。
> **定位**：第一次发布前定义版本号规则、发布检查清单、发布步骤、发布说明模板。防止每次发布都是临时起意。
>
> **单人简化**：发布流程可一人走完。CI 辅助，但核心步骤人工检查不省略。

---

## §1 版本号规则

遵循 SemVer 2.0：`MAJOR.MINOR.PATCH`

| 版本 | 何时递增 | 示例 |
|:----|:---------|:-----|
| **MAJOR** | 破坏性架构变更 / API 不兼容 / 数据库 schema 不兼容 | v0.1.0 → v1.0.0 |
| **MINOR** | 新功能（向后兼容）/ 降级 / 废弃 | v0.1.0 → v0.2.0 |
| **PATCH** | Bug 修复 / 性能优化 / 文档更新（无功能变化） | v0.1.0 → v0.1.1 |

**0.0.1 特殊规则**：0.0.1 = 草稿起始版本（全库统一起点）。草稿期间发生实质性内容变更时，各文档版本记录按 0.0.2 → 0.0.3 … 递增（见 [documentation-governance.md](documentation-governance.md)）；待设计定稿后统一升级版本号；代码首版（首次可运行）从 **v0.1.0** 起——草稿版本与代码发布在版本号上明确分离。

> **版本号口径（2026-08-03 决策 D-07）**：全库以 **v0.1.0** 为代码首版口径，与 [README.md](../README.md)、[architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md)、[feature-list.md](../specification/feature-list.md) 及差距表一致。`v0.1.0` 语义为「首个不完整交付」，对应当前六层架构部分降维的实际状态。此前本节所写「v1.1.0」为历史笔误——v1.1.0 会暗示已存在 v1.0.0，与事实不符。

---

## §2 发布检查清单

每次发布前逐项检查（单人可在一小时内走完）：

- [ ] 所有 P0 bug 已修复
- [ ] 单元测试覆盖率 ≥80%
- [ ] 9 条 E2E（E2E-01~09，见 test-plan §3.7）全部通过
- [ ] 19 条安全红线（S-01~S-19）逐条验证通过
- [ ] [CHANGELOG.md](changelog.md) 已更新（新功能/修复/破坏性变更/已知问题）
- [ ] 版本号已在 `__init__.py` 中更新
- [ ] 文档交叉引用一致性检查通过
- [ ] 数据库迁移脚本可回滚（`kairos db migrate` + `kairos db migrate rollback` 均正常）
- [ ] 备份已创建
- [ ] 构建产物正常（`uv build` 无错误）

---

## §3 发布步骤

> **⚠ 代码启动前不可执行**：以下步骤假定 Kairos 已有可运行的代码包。当前项目处于设计冻结阶段，代码尚未启动。此文档保留发布流程框架供参考，实际执行须在代码启动后重新校准确认。

```bash
# 1. 检查清单 → 全过
# 2. 构建
uv build

# 3. 测试安装
uv pip install dist/kairos-*.whl
kairos --version     # 确认版本号正确
kairos health        # 确认服务正常

# 4. 提交 + Tag
git add .
git commit -m "release: v0.1.0"
git tag v0.1.0
git push origin main --tags

# 5. GitHub Release
gh release create v0.1.0 \
  --title "v0.1.0" \
  --notes "见 CHANGELOG.md" \
  dist/kairos-*.whl dist/kairos-*.tar.gz

# 6. 发布后验证
pip install kairos==0.1.0
kairos init --seed-path ~/.kairos/seeds/
kairos health --full
```

> **命令定义状态注记**：`kairos health --full` 与 `kairos init --seed-path` 均在 api-spec §3 CLI 表无契约登记（`kairos init --seed-path` 为种子目录参数，未列入 CLI 表；`kairos health --full` 属 11 条待定义命令之一）——已纳入债务 D-430 追缴清单（round25 审计 R25-10 补登），编码启动前须在 api-spec §3 完成契约登记或从本文移除使用引用。

---

## §4 发布说明模板

```markdown
### vX.Y.Z - YYYY-MM-DD（版本条目模板，发布时复制并替换版本号/日期）

### 新功能
- （列出新增功能及对应 Issue/PR）

### Bug 修复
- （列出修复的 bug 及对应 Issue）

### 破坏性变更
- （如有，列出变更内容 + 迁移指南链接）

### 已知问题
- （如有，列出未修复已知问题）

### 升级注意事项
- （如有，列出需要手动操作的步骤）
```

---

## §5 回滚方案

> **回滚三原则**：(1) 数据库回滚优先于代码回滚——数据无损最高优先级；(2) 不删除已打 tag 的 Release——回滚通过发布新 PATCH 而非删除旧 Release 实现；(3) 回滚完成后 24 小时内完成根因分析。

### 发布后验证失败时的回滚步骤

```text
1. 终止：停止新流量（如适用），防止更多错误数据写入
2. 标记：在 CHANGELOG 中标记当前 Release 为 FAILED（附失败原因）
3. 恢复数据库：kairos db migrate rollback（回滚最近一次迁移）
4. 恢复代码：git revert HEAD && git push
5. 重建部署：docker compose up -d --build（或等效部署命令）
6. 验证：运行回滚后健康检查，确认旧版本正常
7. 审计：记录回滚原因、影响范围、修复时间线至 CHANGELOG
```

### 数据库回滚失败时的升级路径

若 `kairos db migrate rollback` 失败（如数据不兼容），升级为数据恢复流程：从最近一次全量备份恢复 → 重放 WAL 至回滚目标时间点 → 验证数据完整性 → 重建部署。

---

## §6 API 版本化与弃用

| 策略 | 规则 |
|:----|:-----|
| **版本化** | API 前缀 `/v1/`、`/v2/`，支持跨版本共存 |
| **弃用通知** | 废弃端点在 Header 返回 `Deprecation: true` + `Sunset: <date>` |
| **最低支持周期** | 弃用后至少支持 2 个 MINOR 版本 |
| **迁移指南** | 每次破坏性变更发布时附带迁移说明 |

---

## §7 许可证

| 项 | 内容 |
|:---|:-----|
| 项目许可证 | MIT（代码）+ CC-BY-4.0（文档） |
| 第三方依赖 | 所有依赖不引入 GPL/AGPL（兼容 MIT） |
| 依赖合规 | 每次 `uv sync` 后运行 `uv licenses` 检查许可兼容性 |

---

## §8 隐私声明（简要）

Kairos 存储的记忆数据默认仅存储在本地。收集的数据类型、保留策略、删除方法详见 [security/security-specification.md](../security/security-specification.md) §4 隐私评估。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 发布指南：版本号规则/发布检查清单/发布步骤/回滚/API 弃用/许可证。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：E2E 计数口径更新（6→9 条，见 test-plan §3.7）、回滚命令名统一为 `kairos db migrate rollback`（ADR-011）。 |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：§1 版本号规则 0.0.1 语义修订（草稿起始版本+递增规则）。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（changelog 0.0.26）：M-11 种子路径统一目录语义（--seed-path ~/.kairos/seeds/）。 |
| 0.0.57 | 2026-08-08 | round25 全面深度审计修复批次（changelog 0.0.57）：架构元认知层第五层编号/完结叙事线 409/deleted_at 承载补列/技能管理定位改指 blueprint/S-17 法定擦除例外同步/README 版本链补登/KAIROS_ 参数前缀等 21 项闭环。 |
| 0.0.87 | 2026-08-10 | round49 全面深度审计修复批次（changelog 0.0.87）：`## vX.Y.Z` 模板标题降级 `###`（版本条目模板，不打断 §N 序列）。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |

