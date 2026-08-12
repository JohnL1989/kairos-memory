---
title: Kairos 开发环境搭建
aliases:
  - 开发环境
  - Development Setup
tags:
  - kairos
  - development
  - setup
created: 2026-07-20
updated: 2026-08-12
last_reviewed: 2026-08-12
status: design-freeze
---

# Kairos 开发环境搭建

> **状态声明**：本文描述的命令（`git clone` → `uv pip install -e ".[dev]"` → `kairos init` → `kairos serve`）为**设计目标**。CLI 尚未构建，本文待 CLI 构建后重写。

> **定位**：开发者从零开始搭建 Kairos 开发环境。
>
> **⚠ 草稿完善声明**：以下所有命令为架构设计阶段的目标示例。项目当前处于草稿完善阶段期（见 changelog），CLI 尚未构建。命令格式和参数将在代码启动后最终确认。

---

## 一、前置条件

| 依赖 | 版本 | 验证命令 |
|:----|:----|:---------|
| Python | ≥ 3.11 | `python --version` |
| uv | ≥ 0.4 | `uv --version` |
| Git | ≥ 2.40 | `git --version` |
| Docker | ≥ 24.0（标准模式需要） | `docker --version` |
| BGE-M3 嵌入模型 | 轻量模式本地运行需要 | 自动下载（首次 `kairos serve` 时） |

## 二、克隆与虚拟环境

```bash
git clone <repo-url>   # 仓库地址以全面重新设计定稿后的实际地址为准
cd kairos

# 创建虚拟环境
uv venv
source .venv/bin/activate   # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install
```

## 三、数据库初始化

> **首迭代默认（2026-07-31 竖切决策）**：轻量模式（SQLite + sqlite-vec）为开发主后端；标准模式（PostgreSQL + pgvector）在竖切验收后迭代适配，StorageBackend 抽象层保证业务代码无感切换（ADR-001）。

```bash
# 轻量模式（推荐开发使用）

# 1. 初始化密钥（自动生成全部四个密钥并写入环境文件）
kairos init --init-key

# 2. 初始化数据库（密钥已就绪，自动加载）
kairos init --db sqlite:///$HOME/.kairos/kairos.db

# 标准模式（需要 Docker PostgreSQL）
# 开发专用：密码经 ${KAIROS_DB_PASSWORD} 注入（本地开发先 export 该变量）；生产部署与环境变量注入见 [deployment.md](../ops/deployment.md) §三
docker run -d --name db -p 5432:5432 \
  -e POSTGRES_USER=kairos \
  -e POSTGRES_PASSWORD=${KAIROS_DB_PASSWORD} pgvector/pgvector:pg16
kairos init --db postgresql://kairos:${KAIROS_DB_PASSWORD}@localhost:5432/kairos
```

## 四、运行测试

```bash
# 单元测试
pytest tests/unit/ -v --cov=src

# 集成测试（需要 Docker）
pytest tests/integration/ -v

# E2E 测试（需要 Docker）
pytest tests/e2e/ -v

# 全部测试
pytest -v
```

## 五、常用命令

```bash
# 类型检查
mypy src/

# 代码格式检查
ruff check src/ tests/

# 代码格式化
ruff format src/ tests/

# 启动开发服务器（热重载）
kairos serve --port 8010 --reload
```

## 六、IDE 配置建议

### VS Code

推荐扩展：
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- GitHub Copilot

`settings.json` 建议：
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "ruff.lint.enable": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "files.exclude": {
    "**/.venv": true,
    "**/__pycache__": true
  }
}
```

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 开发环境搭建：前置条件、初始化、测试与 IDE 配置（设计目标，CLI 未构建）。 |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：frontmatter 与版本记录同步（第二轮全库深度审计修复批次）。 |
| 0.0.38 | 2026-08-06 | round16 全面深度审计修复批次（changelog 0.0.38）：Docker 密码硬编码改为 ${KAIROS_DB_PASSWORD} 注入。 |
| 0.0.42 | 2026-08-07 | 0.0.42 文档审计修复批次（changelog 0.0.42）：部署引用改指 deployment §三；frontmatter 审查日期同步。 |
| 0.0.89 | 2026-08-10 | round51 全面深度审计修复批次（changelog 0.0.89）：L68 deployment 裸文件名引用链接化。 |
| 0.1.0 | 2026-08-12 | 定稿评审通过，版本统一升级（0.0.x → 0.1.0）——首版发布（见 changelog 0.1.0 批次） |

