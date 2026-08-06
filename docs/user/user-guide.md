---
title: Kairos 用户指南
aliases:
  - 用户指南
  - User Guide
tags:
  - kairos
  - user
  - guide
created: 2026-07-20
updated: 2026-08-05
last_reviewed: 2026-08-05
status: draft
---

# Kairos 用户指南

> **状态声明**：本文描述的 CLI 命令（`kairos init`、`kairos serve` 等）为**设计目标**。CLI 工具尚未构建。本文档作为完整的操作规格，待 CLI 就绪后逐条可执行化。

> **定位**：面向 Agent 开发者的操作文档。deployment 解决「怎么装」，本文解决「怎么用」。`kairos suppress` 为 v0.1.0 功能。定向遗忘（suppress，M-04）属 v0.1.0 全量功能，**不在竖切（v0.1.0-slice）首迭代内**（竖切范围见 [slice-implementation-guide](../development/slice-implementation-guide.md)）；竖切交付后随全量功能启用。
>
> **⚠ 草稿完善声明**：以下所有命令与 SDK 调用（`pip install kairos`、`from kairos import KairosClient` 等）为设计示例，当前无构建产物、无可执行命令、无 Python SDK。全部 CLI 命令（`kairos write`、`kairos search` 等）为虚构——当前文档处于设计冻结阶段，代码尚未启动。具体命令语法在代码实现后可能变化。读者应关注接口语义而非命令文本。

---

## 一、快速上手

### 1.1 安装

```bash
# 标准模式（需要 PostgreSQL）
pip install kairos
kairos init --db postgresql://localhost:5432/kairos

# 轻量模式（SQLite，开箱即用）
pip install kairos
kairos init --db sqlite:///$HOME/.kairos/kairos.db
```

### 1.2 首次部署（Key 引导流程）

S-01 要求无有效 Key 拒绝启动。首次部署时需先生成密钥，打破「先有 Key 才能启动」的循环：

```bash
# 1. 初始化密钥（生成全部四个密钥并写入环境文件）
kairos init --init-key

# 2. 初始化数据库
kairos init --db sqlite:///$HOME/.kairos/kairos.db

# 3. 启动服务
kairos serve --port 8010
```

> **注（0.0.11 澄清）**：第 1、2 步为同一 `kairos init` 命令的两个子项——首次执行一次即可完成密钥与数据库初始化；重复执行幂等（不覆盖既有密钥，仅补缺失项）。

`--init-key` 生成以下密钥并写入 `~/.kairos/.env`（与 quick-start 一致）：
- `KAIROS_API_KEY` — API 鉴权
- `KAIROS_SECRET_KEY` — 数据加密
- `KAIROS_AUDIT_HMAC_KEY` — 审计链 HMAC
- `KAIROS_SALT` — Salt 密钥（S-05 要求）

> **注意**：`--init-key` 生成全部四个密钥（含 `KAIROS_SALT`）。这四个密钥是首次启动的必要条件——缺少任意一个均拒绝启动。

### 1.3 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|:----|:----|:-------|:-----|
| `KAIROS_SALT` | ✅ | — | Salt 密钥（S-05 要求无 Salt 拒绝启动） |
| `KAIROS_API_KEY` | ✅ | — | API Key（read/write/admin 三级） |
| `KAIROS_SECRET_KEY` | ✅ | — | 数据加密密钥 |
| `KAIROS_AUDIT_HMAC_KEY` | ✅ | — | 审计链 HMAC 密钥 |
| `KAIROS_DB_DSN` | 标准模式 ✅ / 轻量模式 ❌ | — | 数据库连接串（轻量模式 SQLite 自动创建，不需配置） |
| `KAIROS_LLM_API_KEY` | 标准/全量模式 ✅ / 轻量模式 ❌ | — | LLM Provider API Key（轻量模式使用本地 BGE-M3 嵌入，不需 LLM。详见 [system-context.md](../specification/system-context.md) 可选声明） |
| `KAIROS_LLM_ENDPOINT` | 标准/全量模式 ✅ / 轻量模式 ❌ | — | LLM Provider 端点（升华/嵌入调用地址）。轻量模式使用本地模型（BGE-M3 嵌入 + 本地小模型），不需 LLM 端点（同 `KAIROS_LLM_API_KEY` 模式限定） |
| `KAIROS_DAILY_BUDGET_FEN` | ❌ | 20000 | LLM 日预算（分，20000分=200元） |

### 1.4 启动

```bash
kairos serve --port 8010
# 输出：Kairos started on http://localhost:8010
```

---

## 二、核心操作

### 2.1 写入记忆

```python
# 使用 KairosClient（目标 SDK，当前草稿完善阶段期无构建产物）
from kairos import KairosClient

client = KairosClient(api_key="sk-...")

# 写入一条按需记忆
memory = client.write(
    path="kairos://sessions/abc123/",
    content="用户偏好：暗色主题",
    source="user_input",         # SDK 参数名 source 对应 API 字段 provenance（S-15 来源标识，必填；合法枚举值见 api-spec provenance 字段）
    contract="ondemand",         # 可选：permanent / ondemand / environmental / temporary
)

print(f"写入成功：{memory.id}")
```

```bash
# 使用 CLI
kairos write kairos://sessions/abc123/ --content "用户偏好：暗色主题" --contract ondemand
```

### 2.2 检索记忆

```python
# 按路径前缀检索
results = client.search(path="kairos://sessions/abc123/")
for r in results:
    print(f"[{r.path}] {r.content}")

# 按语义检索
results = client.search("暗色主题", limit=5)
```

```bash
kairos search "暗色主题" --limit 5
kairos ls kairos://sessions/abc123/
kairos tree kairos://sessions/ --depth 2
```

### 2.3 管理记忆

```bash
# 查看记忆详情（参数接受记忆 ID 或路径，见 api-spec §3 CLI 表）
kairos read <memory_id>

# 更新记忆
kairos update <memory_id> --content "更新后内容"

# 显式遗忘
kairos forget <memory_id>

# 定向遗忘（抑制检索但保留数据）
kairos suppress <memory_id> --reason "合规擦除"
```

### 2.4 外部校准

当系统内的记忆见证锚定不准确时，发送校准信号：

```bash
kairos calibrate --memory-id <uuid> --score 0.85
```

查看当前校准状态：
```bash
kairos status
# 输出：校准状态: active | 距上次校准: 120s | 模式: 正常
```

---

## 三、最佳实践

### 3.1 路径规划

- 使用 `kairos://projects/{project_name}/sessions/` 组织项目级记忆
- 使用 `kairos://sessions/{session_id}/` 组织会话级临时记忆
- 使用 `kairos://users/{user_id}/preferences/` 存储用户偏好
- 使用 `kairos://knowledge/` 存储全局知识库

### 3.2 契约选择

| 契约 | 适用场景 | 遗忘行为 |
|:----|:---------|:---------|
| `permanent` | 核心规则、宪法级偏好 | 不遗忘（仅 S-10 见证豁免保护） |
| `ondemand` | 日常写入，默认选项 | 低使用权重时被遗忘 |
| `environmental` | 高相关信息（如当天上下文） | 环境变化时自然过期 |
| `temporary` | 中间状态、临时缓存 | 空闲时优先清理 |

### 3.3 升华利用

系统在空闲时将原始经验（raw）逐步提纯为行为规则（behavior）。建议：
- 定期 `kairos status` 查看升华进度
- behavior 阶段需人工确认（`kairos approve <id>` 或拒绝）
- 升华产物会去语境化，重复经验归约为通用策略

### 3.4 种子锚点

首次启动时系统需要种子锚点作为冷启动参考。建议：
# 种子路径设置
KAIROS_SEED_PATH=~/.kairos/seeds/   # 可选。未设置则使用内置默认种子
- 种子应尽量少而精确（最小化原则）
- 系统会在运行中逐步退化为自产数据驱动

---

## 四、限制与约束

| 项 | 限制 | 绕过 |
|:----|:-----|:-----|
| 单条内容上限 | 64 KB | 分割为多条关联记忆 |
| 路径深度 | ≤ 10 层 | 超深层路径拒绝（返回 422），缩短路径后重试 |
| 单次检索返回条数 | ≤ 100 | 分页（offset/limit） |
| 并发写入 | ≤ 60/min（≈1 ops/s，单客户端令牌桶限流） | 队列缓冲。写入容量目标 ≥100 ops/s（多客户端并行），检索吞吐验收目标 ≥180 ops/s（含 10% 余量；200 ops/s 为 100 并发的理论峰值容量口径——见 [nfr-specification.md](../specification/nfr-specification.md)）。详见 [ops/configuration.md](../ops/configuration.md) §7 |
| 单 API Key 分级 | 三级权限预置 | 多 Key 轮换 |
| 外部校准中断持续 | 超过配置阈值（DEGRADATION_PERIOD）周期进入安全休眠 | 恢复校准信号自动退出 |

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 用户指南：上手/核心操作/最佳实践/限制（设计目标，CLI 未构建）。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：suppress 定向遗忘竖切范围注记（M-04 不在 v0.1.0-slice 首迭代）。 |
| 0.0.4~0.0.9 | 2026-08-04 | （合并占位：changelog 0.0.4~0.0.9 批次的变更未逐条登记于本文档，见 [changelog.md](../governance/changelog.md) 全景） |
| 0.0.10 | 2026-08-04 | 第二轮全库深度审计修复（changelog 0.0.10）：SQLite DSN 统一为 sqlite:///$HOME/ 形式。 |
| 0.0.11 | 2026-08-04 | 开发就绪度修复批次：init 幂等澄清。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：检索吞吐 200→180 ops/s 口径；LLM_ENDPOINT 模式限定；kairos read 参数语义注记；SDK source 参数映射注记。 |
| 0.0.25 | 2026-08-05 | 第八轮全库深度审计修复批次（changelog 0.0.25）：api-spec §三→§3 引用联动。 |
