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
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 工程流程

> **定位**：定义 Kairos 的工程协作流程——分支策略、PR 流程、提交规范、CI 门禁与发布流程。竖切实现已交付，本流程生效；CI 流水线（`.github/workflows/ci.yml`）已落地，发布管线中尚未落地的部分见 [debt-collection.md](../governance/debt-collection.md)。`docs/` 文档库的变更（doc 批次）以 [documentation-governance.md](../governance/documentation-governance.md) 的更新联动规则为准，不强制走 PR 流程（文档批次按 [changelog.md](../governance/changelog.md) 登记）。

> **与 [release-guide.md](../governance/release-guide.md) 的关系**：本文件定义「怎么协作」的日常工程流程；[release-guide.md](../governance/release-guide.md) 定义「怎么发布」的版本规则与发布检查清单——发布步骤执行本文件 §五 的发布流程，版本号规则以 [release-guide.md](../governance/release-guide.md) 为权威。
> **代码规范**：命名/结构/错误处理/日志等编码规范见 [coding-conventions.md](./coding-conventions.md)（提交前对照自检）。

---

## 一、分支策略

| 分支 | 用途 | 生命周期 | 说明 |
|:----|:----|:--------|:-----|
| `main` | 主分支 | 常驻 | 唯一长期分支；始终处于可发布状态（门禁全绿）；历史提交即里程碑 |
| `develop` | 集成分支 | 常驻 | 功能分支合并目标；doc 批次与开发批次在 develop 上集成 |
| `feature/<编号>-<主题>` | 功能分支 | 短生命 | 从 `develop` 切出，按功能/审计批次创建；编号关联 issue/批次（如 `feature/d-415-file-graph`、`feature/round11-c01-mcp`） |
| `release/<版本>` | 发布分支 | 短生命 | 从 `develop` 切出（release-guide §3 发布步骤），仅做发布阻断级修复；合并回 `main` 与 `develop` |

**规则**：

- 禁止直接向 `main` 提交（热修复例外：生产阻断级缺陷经双人复核后可直接 hotfix 分支合并）。
- 功能分支生命周期内须保持与 `develop` 同步（合并前 rebase 或 merge 最新）。
- 分支命名使用 kebab-case；审计/文档批次分支按 changelog 批次号命名（如 `feature/0.0.30-round11`）。

## 二、PR 流程

1. **PR 创建**：功能分支完成 → 创建 PR 至 `develop`（文档批次可不走 PR，见定位）。
2. **必过门禁**（PR 合并前置条件，全部通过才可合并）：
   - CI 流水线全绿：`python scripts/doc-audit.py`（exit 0）+ `python scripts/deep-audit.py`（exit 0）——文档一致性门禁，任何失败项须先闭环；
   - 单元测试/集成测试通过（代码就绪后按 [test-plan.md](../quality/test-plan.md) 执行）；
   - 无未解决的安全红线冲突（S-01~S-19 相关改动须过 [security-specification.md](../security/security-specification.md) 复核）。
3. **人工复核清单**：结构性变更（章节迁移/更名/删除）须完成 [documentation-governance.md](../governance/documentation-governance.md) §2.2 连锁复核并登记结果；新增参数/术语/债务编号先注册（[configuration.md](../ops/configuration.md)/[glossary.md](../references/glossary.md)/[debt-collection.md](../governance/debt-collection.md) 登记优先，见 [documentation-governance.md](../governance/documentation-governance.md) §5）；计数类改动（表/端点/参数/文档数）同步 README 声明。
4. **合并方式**：`develop` 用 squash merge（单提交入集成分支，提交信息保留功能描述）；`main` 用 merge commit（保留发布历史）。

## 三、提交规范

- **格式**：`<type>: <中文摘要>`（conventional commits 子集）——`feat`（新功能/新文档批次）/ `fix`（缺陷修复）/ `docs`（文档变更）/ `chore`（构建、配置、杂务）/ `refactor`（重构，不改变行为）。
- **摘要**：简明描述变更；审计修复批次标注批次号（如 `docs: 0.0.30 round11 修复批次——…`）。
- **提交粒度**：一个批次（changelog 版本号）一个提交，批次内不拆分零散提交——保持 changelog 版本记录 ↔ git 历史一一对应，便于按批次回查。
- **协作者署名**：AI 协作产物在提交信息尾部附 `Co-Authored-By: Claude <noreply@anthropic.com>`。
- **禁止项**：密钥/Token/用户数据不得进入提交信息与代码注释（S 级红线）；提交信息不夹带无关改动（最小化改动原则）。
- **文档批次与代码批次分离**：文档批次（`docs:`）与代码批次（`feat:`/`fix:`）不混交一个提交。
- **批次收尾检查清单**（防「版本记录登记缺口」再发）：批次提交前逐项核对——① 本批次实质触及的文档（以 changelog 叙述节为线索）须在各文档版本记录表登记对应批次行（「触及即登记」）；② 门禁清单与 doc-audit 实际检查类别保持一致（新增门禁类别须同步本文档与 changelog）；③ 门禁实测结果回填 changelog 批次条目（「已验证」而非「待验证」）。脚本级自动校验无法判定「批次是否实质触及某文档」，故以人工清单落地（round12 1-1 根因：版本记录缺口 0.0.18 补登后 0.0.29/0.0.30 再发）。

## 四、CI 门禁

进入开发阶段后，CI 流水线必过步骤（按序执行，任一失败即阻断合并）：

1. `python scripts/doc-audit.py` —— 18 类 + 14a + 6.8a + 6.12a + 6.13 + 6.14 + 6.15 + 6.16 + 6.17 + 6.18 + 6.19 + 6.20 + 6.21 + 6.22 + 6.23 + 6.24 + 6.25 + 6.26 + 6.27 + 6.28 + 6.29 + 6.30 + 6.31 + 6.32 + 6.33 + 6.34 + 6.35 + 6.36 + 6.37 + 6.38 + 6.39 门禁全绿（exit 0）；**级别注记**：6.36 版本归属互斥 / 6.37 表格范围词一致性 / 6.38 阈值监控自洽性 为 **FAIL 级硬门禁**（round46 以 WARN 软门禁首轮、round47 全库 0 违例观察、round48 晋升 FAIL，见 changelog 0.0.86）；6.26 档 4 为 WARN 级软提示（供人工审计）；6.39 受改批次版本记录覆盖性 为 **WARN 级软门禁**（round54 首跑，防「触及即登记」登记缺陷复发——以 changelog 最新批次受改清单核对各文档版本记录是否含该批次行，见 changelog 0.0.94）。
2. `python scripts/deep-audit.py` —— 链接/出入度/数字声明/占位盘点无阻断项（exit 0）；
3. 代码检查（代码就绪后）：lint + 类型检查 + 单元测试 + 集成测试 + **证伪测试**（`[FALSIFICATION]` 套件——架构 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §0.8 编码纪律：没有证伪测试的特征标志不应合入主分支）；测试矩阵按三种命名配置集执行（CI 默认 `kairos-slice`，发布前全量三集，见 [test-strategy.md](../quality/test-strategy.md) §六、[test-plan.md](../quality/test-plan.md) §1 配置集矩阵与 [slice-implementation-guide.md](slice-implementation-guide.md) 竖切验收标准）；
4. 安全扫描：依赖漏洞扫描 + 密钥扫描（防密钥入库）。

门禁失败处理：失败项须在本 PR/批次内闭环——禁止以「跳过门禁」方式合并（0.0.22 批次「门禁虚假绿灯」教训，处置记录见 changelog 0.0.22）。

## 五、发布流程

发布步骤执行 [release-guide.md](../governance/release-guide.md) §3；工程侧要点：

1. `develop` 门禁全绿 → 切 `release/<版本>` 分支；
2. release 分支仅接受发布阻断级修复（修复后回归门禁）；
3. 发布检查清单（[release-guide.md](../governance/release-guide.md) §2）逐项执行，含文档同步（changelog 版本记录与批次登记）；
4. 打 tag → 合并 `main` → 合并回 `develop`；
5. 发布说明模板见 [release-guide.md](../governance/release-guide.md) §4。

---

## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-08-06 | 工程流程文档（第十轮深度审计 D-01/M-12 闭环）：分支策略、PR 流程、提交规范、CI 门禁、发布流程。 |
| 0.0.2~0.0.54 | 2026-08-08 | （合并占位：changelog 0.0.2~0.0.54 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.56 | 2026-08-08 | round24 结构性建议落地批次（changelog 0.0.56）：S24-1 门禁 6.24 端点→章节锚点一致性（首跑捕获架构 L771 calibration 端点引用 §1.7→§6.5）；S24-2 门禁 6.25 认知基础去版本化（首跑捕获 4 处版本字样残留并修复）；门禁清单口径 6.13~6.25。 |
| 0.0.58 | 2026-08-08 | round25 结构性建议落地批次（changelog 0.0.58）：S25-1 门禁 6.26 通用章节引用存在性与标题语义入检；S25-2 门禁 6.27 api-spec 章节版本标注完备性入检；门禁口径 6.13~6.25→6.13~6.27。 |
| 0.0.64 | 2026-08-08 | round30 全面深度审计修复批次（changelog 0.0.64，补登）：§四 CI 门禁清单口径同步 6.13~6.31（含本轮新增 6.31 中文正文半角标点纪律，展开式列示）。 |
| 0.0.66 | 2026-08-09 | round32 全面深度审计修复批次（changelog 0.0.66）：版本记录补登批次——0.0.64 行（门禁清单 6.13~6.31）为前序批次实质变更漏登记，本批补登（governance §4「触及即登记」）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.71 | 2026-08-09 | round35 门禁建议落实批次（changelog 0.0.71）：§四 CI 门禁清单补 6.32（治理执行记录覆盖性——自引用快照须含最新 changelog 批次，R35-01 防复发）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.74 | 2026-08-09 | round38 门禁建议落实批次（changelog 0.0.74）：§四 CI 门禁清单补 6.33（feature-list「对应架构组件」列引用落点全量校验——round37 建议落地，首跑验证 0 漂移）+ 6.26 扩展「引用文本所指机制名存在性」档 4（WARN 级软提示，防 R37-04~09 类悬空引用复发）；frontmatter updated/last_reviewed 同步 2026-08-09。 |
| 0.0.84 | 2026-08-10 | round46 门禁建议落实批次（changelog 0.0.84）：§四 CI 门禁清单补 6.34/6.35/6.36/6.37/6.38（门禁口径同步 6.13~6.38，补齐 round44 漏登的 6.34/6.35）；frontmatter updated/last_reviewed 同步 2026-08-10。 |
| 0.0.86 | 2026-08-10 | round48 遗留问题处理批次（changelog 0.0.86）：§四 CI 门禁清单补级别注记——6.36/6.37/6.38 为 FAIL 级硬门禁（round46 WARN 首轮 → round47 全库 0 违例观察 → round48 晋升），6.26 档 4 为 WARN 级软提示；frontmatter updated/last_reviewed 同步 2026-08-10。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：正文裸文档名引用链接化 7 处（release-guide/test-plan/documentation-governance 等）+ 补 coding-conventions 正文入口。 |
| 0.0.94 | 2026-08-11 | round54 全面深度审计修复批次（changelog 0.0.94）：§四 CI 门禁清单补 6.39（受改批次版本记录覆盖性，WARN 级软门禁，round54 首跑 0 漏登记——R54-01 防复发）；frontmatter updated/last_reviewed 同步 2026-08-11。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |


