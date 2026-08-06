---
title: Kairos 工程流程
aliases:
  - 工程流程
  - Engineering Workflow
tags:
  - kairos
  - development
  - engineering
created: 2026-08-06
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 工程流程

> **定位**：定义代码启动后的工程协作流程——分支策略、PR 流程、提交规范、CI 门禁与发布流程。当前处于文档草稿阶段（无运行代码），本流程以代码就绪为前置条件；`docs/` 文档库的变更（doc 批次）以 [documentation-governance.md](../governance/documentation-governance.md) 的更新联动规则为准，不强制走 PR 流程（文档批次按 [changelog.md](../governance/changelog.md) 登记）。

> **与 [release-guide.md](../governance/release-guide.md) 的关系**：本文件定义「怎么协作」的日常工程流程；release-guide 定义「怎么发布」的版本规则与发布检查清单——发布步骤执行本文件 §五 的发布流程，版本号规则以 release-guide 为权威。

---

## 一、分支策略

| 分支 | 用途 | 生命周期 | 说明 |
|:----|:----|:--------|:-----|
| `main` | 主分支 | 常驻 | 唯一长期分支；始终处于可发布状态（门禁全绿）；历史提交即里程碑 |
| `develop` | 集成分支 | 常驻 | 功能分支合并目标；doc 批次与开发批次在 develop 上集成 |
| `feature/<编号>-<主题>` | 功能分支 | 短生命 | 从 `develop` 切出，按功能/审计批次创建；编号关联 issue/批次（如 `feature/d-403-compaction`、`feature/round11-c01-mcp`） |
| `release/<版本>` | 发布分支 | 短生命 | 从 `develop` 切出（release-guide §3 发布步骤），仅做发布阻断级修复；合并回 `main` 与 `develop` |

**规则**：

- 禁止直接向 `main` 提交（热修复例外：生产阻断级缺陷经双人复核后可直接 hotfix 分支合并）。
- 功能分支生命周期内须保持与 `develop` 同步（合并前 rebase 或 merge 最新）。
- 分支命名使用 kebab-case；审计/文档批次分支按 changelog 批次号命名（如 `feature/0.0.30-round11`）。

## 二、PR 流程

1. **PR 创建**：功能分支完成 → 创建 PR 至 `develop`（文档批次可不走 PR，见定位）。
2. **必过门禁**（PR 合并前置条件，全部通过才可合并）：
   - CI 流水线全绿：`python scripts/doc-audit.py`（exit 0）+ `python scripts/deep-audit.py`（exit 0）——文档一致性门禁，任何失败项须先闭环；
   - 单元测试/集成测试通过（代码就绪后按 test-plan 执行）；
   - 无未解决的安全红线冲突（S-01~S-19 相关改动须过 [security-specification.md](../security/security-specification.md) 复核）。
3. **人工复核清单**：结构性变更（章节迁移/更名/删除）须完成 documentation-governance §2.2 连锁复核并登记结果；新增参数/术语/债务编号先注册（configuration/glossary/debt-collection 登记优先，见 documentation-governance §5）；计数类改动（表/端点/参数/文档数）同步 README 声明。
4. **合并方式**：`develop` 用 squash merge（单提交入集成分支，提交信息保留功能描述）；`main` 用 merge commit（保留发布历史）。

## 三、提交规范

- **格式**：`<type>: <中文摘要>`（conventional commits 子集）——`feat`（新功能/新文档批次）/ `fix`（缺陷修复）/ `docs`（文档变更）/ `chore`（构建、配置、杂务）/ `refactor`（重构，不改变行为）。
- **摘要**：简明描述变更；审计修复批次标注批次号（如 `docs: 0.0.30 round11 修复批次——…`）。
- **提交粒度**：一个批次（changelog 版本号）一个提交，批次内不拆分零散提交——保持 changelog 版本记录 ↔ git 历史一一对应，便于按批次回查。
- **协作者署名**：AI 协作产物在提交信息尾部附 `Co-Authored-By: Claude <noreply@anthropic.com>`。
- **禁止项**：密钥/Token/用户数据不得进入提交信息与代码注释（S 级红线）；提交信息不夹带无关改动（最小化改动原则）。
- **文档批次与代码批次分离**：文档批次（`docs:`）与代码批次（`feat:`/`fix:`）不混交一个提交。

## 四、CI 门禁

进入开发阶段后，CI 流水线必过步骤（按序执行，任一失败即阻断合并）：

1. `python scripts/doc-audit.py` —— 18 类 + 14a + 6.13 + 6.14 + 6.15 + 6.12a 门禁全绿（exit 0）；
2. `python scripts/deep-audit.py` —— 链接/出入度/数字声明/占位盘点无阻断项（exit 0）；
3. 代码检查（代码就绪后）：lint + 类型检查 + 单元测试 + 集成测试（测试矩阵见 [test-plan.md](../quality/test-plan.md) 与 [slice-implementation-guide.md](slice-implementation-guide.md) 竖切验收标准）；
4. 安全扫描：依赖漏洞扫描 + 密钥扫描（防密钥入库）。

门禁失败处理：失败项须在本 PR/批次内闭环——禁止以「跳过门禁」方式合并（0.0.22 批次「门禁虚假绿灯」教训，处置记录见 changelog 0.0.22）。

## 五、发布流程

发布步骤执行 [release-guide.md](../governance/release-guide.md) §3；工程侧要点：

1. `develop` 门禁全绿 → 切 `release/<版本>` 分支；
2. release 分支仅接受发布阻断级修复（修复后回归门禁）；
3. 发布检查清单（release-guide §2）逐项执行，含文档同步（changelog 版本记录与批次登记）；
4. 打 tag → 合并 `main` → 合并回 `develop`；
5. 发布说明模板见 release-guide §4。

---

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-08-06 | 工程流程文档（第十轮深度审计 D-01/M-12 闭环）：分支策略、PR 流程、提交规范、CI 门禁、发布流程。 |
