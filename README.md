# Kairos Memory System

**Kairos** 是一个面向 AI Agent 的持久化记忆系统——让 Agent 像人一样「记得用过的东西，忘了不再重要的东西，知道自己是谁」。

## 项目定位

Kairos 不是简单的键值存储或向量数据库，而是一套完整的记忆认知系统：

- **记忆即使用**：以「使用权重」驱动记忆的激活与遗忘，而非仅靠时间
- **双副本架构**：见证锚定（主副本，真实性权威）与使用权重（影子副本，使用统计）物理分离，内部信号永不反向污染真实性（S-14 语境自指禁令）
- **三信号混合检索**：语义向量 + BM25 全文 + 实体加成加权融合（0.50 / 0.35 / 0.15），路径空间作为确定性硬过滤边界
- **身份注册表（构造论）**：Agent 的身份记忆经外部校准初始赋予、叙事自洽度驱动双向更新，身份记忆享受见证豁免（S-10）
- **宪法主权面**：外部校准是宪法级偏好的唯一入口（S-11），外部校准中断时按降级状态机逐级退守（保守静默 → 受限交叉验证 → 安全休眠）
- **可审计**：所有治理操作写入 HMAC 链审计日志（S-16），篡改可检测、来源可追溯

## 系统概览

```
六层功能栈 + 两个正交治理面（宪法主权面 + 监督平面）
├── 接入层     REST API（Litestar）· CLI（Typer）· Agent Tool · MCP Bridge
├── 工作记忆层  WM 核心（7±2 槽位）· 多路径融合
├── 策略层     预测器 · 调节器 · 价值上下文（六级辞典式排序）
├── 推理皮层    最小推理内核
├── 存储层     记忆 CRUD · 双副本 · 三信号检索 · 遗忘调度器 · 身份注册表 · 升华管道
├── 元认知层    检测器族 · 健康计数器 · 治理器族
├── 宪法主权面  外部校准 · 强制冻结 · 降级状态机 · 宪法修订端口
└── 监督平面    审计庭（HMAC 链）
```

完整设计见 [系统架构](docs/foundation/architecture-v0.1.0.md)（设计权威文档）与 [认知基础](docs/foundation/cognitive-foundation.md)（第一性原理）。

## 开发状态

| 阶段 | 状态 |
|:-----|:-----|
| 文档体系（52 份） | ✅ 已定稿（0.0.96） |
| 竖切 v0.1.0-slice（W1~W10） | ✅ 已交付——16 张表、REST 31 端点、CLI 21 条、MCP 15 工具全可用、288 项测试 |
| 全量 v0.1.0（升华/图谱/WM 等） | 📋 架构就绪，未启动 |

进度追踪见 [changelog](docs/governance/changelog.md) 与 [项目计划](docs/governance/project-plan.md)；能力清单见 [功能清单](docs/specification/feature-list.md)（168 项能力：43 核心 + 125 扩展）。

## 快速开始

```bash
# 环境：Python ≥ 3.11 + uv
uv sync

# 初始化（生成密钥 + 数据库迁移）
kairos init --init-key --db sqlite:///$HOME/.kairos/kairos.db

# 启动 REST 服务（默认 127.0.0.1:8010，S-04 本地回环绑定）
kairos serve

# 写入与检索
kairos write kairos://_user/default/memories/ --content "..." --source user_input
kairos search "关键词"
```

更完整的示例见 [用户指南](docs/user/user-guide.md) 与 [快速上手](docs/user/quick-start.md)。

## 技术栈

| 层 | 轻量模式（竖切当前） | 标准模式（规划） |
|:---|:-------------------|:----------------|
| 语言/框架 | Python 3.11+ · Litestar | 同左 |
| 存储 | SQLite + FTS5（向量经 numpy 扫描） | PostgreSQL + pgvector |
| 检索 | 三信号混合（语义 + BM25 + 实体） | 同左（pg_bigm + zhparser） |
| 嵌入 | HashEmbedder（开发默认）→ BGE-M3 | text-embedding-3-small（1536 维） |

技术选型全景见 [技术栈文档](docs/development/technology-stack.md)；实现偏差与待办见 [债务清单](docs/governance/debt-collection.md)（D-447/D-448/D-449）。

## 文档体系

完整的 52 份文档索引见 [docs/README.md](docs/README.md)，按 地基 / 规格 / 开发 / 治理 / 运维 / 质量 / 安全 / 用户 八类组织。

## 许可证

未定（见 [发布指南](docs/governance/release-guide.md)）。
