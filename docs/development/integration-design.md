---
title: Kairos 集成设计
aliases:
  - 集成设计
  - Integration Design
tags:
  - kairos
  - design
  - integration
created: 2026-07-20
updated: 2026-08-06
last_reviewed: 2026-08-06
status: draft
---

# Kairos 集成设计

> **⚠ 草稿完善声明**：`from kairos import KairosClient` 等 SDK 调用为目标示例。当前文档草稿阶段，无运行代码。

> **定位**：定义 Kairos 与宿主 Agent 的交互全生命周期。覆盖会话初始化、写入、检索、升华、事件回调、错误传播语义、并发约束、超时契约。

---

## 一、Agent 集成流程

```text
Agent 应用
  │
  ├── 初始化 ──→ KairosClient(config)
  │                 ├── api_key (read/write/admin)
  │                 ├── base_url (默认 localhost:8010)
  │                 └── timeout (默认 30s)
  │
  ├── 写入 ──→ client.write(path, content, contract, ...)
  │                 └── 返回 memory_id
  │
  ├── 检索 ──→ client.search(query, path, limit)
  │                 └── 返回 Memory 对象列表
  │
  ├── 浏览 ──→ client.browse(path, depth)
  │                 └── 返回路径树
  │
  └── 关闭 ──→ client.close()
```

## 二、同步与异步

| 操作 | 推荐模式 | 超时 | 说明 |
|:----|:--------|:----|:-----|
| 写入 | 同步 | 10s | 写入后即时返回 memory_id。嵌入计算在后续巩固管道异步完成，不影响写入响应时间。嵌入就绪前若被检索，降级为路径前缀匹配 |
| 检索 | 同步 | 10s | 路径索引查询 + 可选的向量搜索 |
| 批量导入 | 异步 | — | 返回 job_id，轮询进度 |
| 升华触发 | 异步 | — | 空闲调度，不阻塞 Agent |
| 校准信号 | 同步 | 5s | 见证锚定更新需确认 |
| 冻结 | 同步 | 5s | 强制操作需确认 |
| 配置修改 | 同步 | 5s | 运行时参数热更新 |

## 三、并发约束

| 场景 | 约束 | 违反后果 |
|:----|:-----|:---------|
| 同一记忆并发写入 | 最后写入者胜出（version 递增，适用于单进程本地部署） | 旧版本标记 superseded |
| 同一记忆并发检索 | 无锁，顺序执行 | — |
| 遗忘与检索并发 | 遗忘不阻塞检索（标记后清除，标记态非最终态——已被标记为遗忘的记忆在清除前仍可被检索命中，但返回时标记 `stale=true`）。标记态是遗忘调度器的中间状态，非持久状态机态——四态机（active/stale/archived/superseded），suppressed 为定向遗忘子态（被抑制路径不可检索，数据仍存在），遗忘调度器清除冷存储记忆后不产生新的持久状态机态 | 已清除的记忆不被返回 |
| 升华与写入并发 | 升华读取快照，写入不阻塞 | 升华延迟一个周期 |
| 外部校准与内部使用并发 | 校准优先（强一致） | 使用权重延迟更新 |
| 冻结期间 | 所有生成性操作拒绝 | 只读操作允许 |
| 多进程并发（PostgreSQL） | PostgreSQL SERIALIZABLE 隔离 + version 递增乐观锁（`If-Match` 头）。写入冲突时返回 409 Conflict，调用方读取最新版本后重试 | 冲突返回 409，重试后成功 |

## 四、错误传播语义

| 错误类型 | 传播方式 | Agent 可见性 |
|:--------|:---------|:------------|
| 输入验证失败 | 直接返回 4xx | 可见 |
| 存储层异常 | 返回 503（内部码 `ERR-DB-*` 仅日志记录） | 可见（重试建议，但不暴露内部错误码） |
| LLM 超时 | 返回 503（内部码 `ERR-LLM-*` 仅日志记录） | 可见（可降级为纯路径检索，但不暴露内部错误码） |
| 安全红线违反 | 返回 403 + `ERR-SEC-*` | 可见 |
| 层内异常（非传播） | 日志记录 + 降级触发 | 不可见（健康检查可查询） |
| 事件总线背压 | 事件发送方等待（阻塞） | 不可见（延迟增加） |

## 五、事件回调

Kairos 支持通过 Webhook 或事件轮询向 Agent 通知异步事件。Webhook 注册端点已在 api-spec 中定义（POST /v1/webhooks），接收与回调处理标记为 v1.1 持续完善：

| 事件 | 触发条件 | 建议 Agent 响应 |
|:----|:---------|:---------------|
| `use_event` | 记忆写入/检索完成 | 检查影子副本合并状态 |
| `calibration_signal` | 外部校准信号注入 | 检查见证锚定更新 |
| `degradation_switch` | 降级模式切换 | 检查校准源 |

## 六、配置集成

```python
# Agent 集成示例
from kairos import KairosClient

client = KairosClient(
    api_key=os.environ["KAIROS_API_KEY"],
    base_url="http://localhost:8010",
    timeout=30,
)

# 写入
memory = client.write(
    path="kairos://sessions/abc123/",
    content="用户偏好：暗色主题",
    contract="ondemand",
    memory_types="semantic",
)

# 检索
results = client.search("暗色主题", limit=5)
for r in results:
    print(f"{r.path}: {r.content}")
```

---

## 七、MCP 集成

Kairos 通过独立的 MCP Bridge 服务器进程暴露能力给 Hermes Agent：

- **通信协议**：MCP stdio 协议（Hermes Agent 启动 Kairos MCP 子进程，通过 stdin/stdout JSON-RPC 通信）
- **工具注册**：Kairos 启动时向 Hermes 注册 MCP 工具（`kairos_store_memory` / `kairos_search_memories` / `kairos_link` 等 15 个），工具清单见 [architecture-v0.1.0.md](../foundation/architecture-v0.1.0.md) §7.1a MCP Bridge 实现表与 [api-spec.md](../specification/api-spec.md) §6.8。注：`memories_write` / `memories_search` / `path_browse` 为接入层 Agent Tool 定义（[implementation-map.md](../specification/implementation-map.md) `src/access/tools.py`），与 MCP 工具为两层接口，不混用
- **进程模型**：MCP Bridge 作为独立子进程运行，与 Kairos 主进程通过 localhost HTTP 通信
- **安全边界**：MCP 请求受 S-04（本地绑定）约束，仅接受本地连接

SDK 集成示例见 `src/access/mcp/bridge.py`。MCP 工具与 REST API 的等价映射见 [api-spec.md](../specification/api-spec.md) §6.8。

---
## 版本记录

> 草稿阶段从 0.0.1 起；发生实质性内容变更时按 0.0.2 → 0.0.3 … 递增，并在本表登记变更原因；待定稿后升级版本号。

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| 0.0.1 | 2026-07-31 | 集成设计：Agent 全生命周期接入、同步/异步、并发约束、错误传播与事件回调。 |
| 0.0.2 | 2026-08-04 | 全库深度审计修复：MCP 工具映射章节引用修正（§6.9 → §6.8）。 |
| 0.0.14 | 2026-08-05 | 开发就绪度审计修复批次（changelog 0.0.14）：MCP 工具注册改列 kairos_* 系列（15 个）并注明 Agent Tool 与 MCP 工具两层接口不混用。 |
| 0.0.26 | 2026-08-06 | 第九轮全库深度审计修复批次（changelog 0.0.26）：M-05 同源联动（审计未列）——MCP Bridge 落点 §7.3→§7.1a。 |
