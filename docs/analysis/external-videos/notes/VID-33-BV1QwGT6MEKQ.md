---
title: VID-33 视频笔记：OptMem 一行一段永久记忆
aliases:
  - 外部视频笔记-33
tags:
  - kairos
  - external-videos
  - video-notes
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# VID-33 OptMem 一行一段永久记忆

## 元信息
| 项 | 值 |
|:--|:--|
| 链接 | https://www.bilibili.com/video/BV1QwGT6MEKQ |
| UP主 | jeffzhengye |
| 时长 | 7min（1P） |
| 字幕来源 | 本地 whisper 转写（B站 AI 字幕串台不可用，2026-08-07），内容与主题匹配 |
| 素材边界声明 | 完整覆盖视频全程；whisper 谐音错字严重（OptemVM/Optimium/OptinVM=OptMem、二插合并数=二叉合并树、Light.txt=log.txt、入境在=路径在、吃一缓存=摘要缓存、跨绘画=跨会话、Wrong Research=疑为 Roam Research、零一赖=零依赖、拍放=安装、Tlock Code=Claude Code、给仓库=Git 仓库），已按语境转述；与仓库 REPO-02（OptMem 源码实证）同主题，个别参数与源码实证存在出入（见「存疑与未验证」） |

## 内容提炼
### 核心论点
1. OptMem 核心组成极小：**426 token 的 prompt 块 + 31KB 零依赖安装脚本**，一行 curl 五分钟装完，同时支持 Claude Code / Codex / Pieshell 及任何 harness 框架（00:17-00:47）
2. 走**反向量库路线**：纯文本 + 定宽日志，零 embedding、零外部服务、零依赖、零供应商锁定；普通文本直接放进 git 就能做版本控制——零运行成本、可移植、可审计（00:59-01:29）
3. **无后台进程、无定时任务**：所有压缩与合并动作由 Agent 自己在 Note 之后收到 Merge 提示、主动触发完成——「小而美的工具应该有的克制」（01:45-02:00）
4. **位置即身份**：每条记录固定 280 字节，第 N 条就在 log 文件 N×280 字节偏移处，读取只需一次磁盘 seek、O(1) 复杂度；实测 100 万条记忆（608MB）时 Wake 仍在 0.03 秒内完成（02:25-02:50）

### 关键机制
- 核心 = 一颗二叉合并树 + 两个数据结构：①log.txt——唯一真相源，append-only 永不修改，位于 ~/.OpenMemory/log.txt；②Tree 目录——总结缓存，丢了可从 log 重算（02:04-02:25）
- 六条命令：Note（追加一行记忆）/ Wake（唤醒读取上下文）/ Recall（正则检索）/ Nap（合并总结导出缓存）/ Forget（软删除）/ Config（查看设置参数）（01:29-01:44）
- 完整生命周期：Wake 读最近 96 行（默认约 8K tokens，含近四条原文与上层合并摘要）→ Note 写一条 280 字节固定长度记忆（记录约定/踩坑/决定/偏好）→ Nap 合并总结到缓存（丢弃可重建，Agent 同意后执行，目的是节省下次 Wake 时间）→ Forget 软删除（标记 + 后续 Nap 清理）；log 永不删除条目，靠位置偏移维持整本日志的不变性（02:55-03:32）
- 跨机同步：MEMORY_DIR 环境变量指向 git 仓库 / Dropbox / iCloud 目录即可（04:20-04:27）
- 检索取舍：Recall 是正则搜索、不做语义相似——「找上次聊过的 Triple X 非常准，但没法做意思差不多的回查」，这个取舍值得记住（05:45-06:00）

### 可操作细节
- 安装三步：curl install.sh → 把打印出的 426 token prompt 块粘贴到 ~`/claude/CLAUDE.md`` 或 ~/.codex/AGENTS.md` 顶部（重跑 install 自动更新）→ 唯一值得调的参数 Wake_lines（默认 96 行 ≈ 8K tokens，可用 Config 改成 300）（03:42-04:27，from 221-258）
- 推荐场景一：跨会话延续编码上下文（多日同项目、多 Agent 维护同一仓库）；场景二：当私人笔记/日记/读书笔记用（纯文本版知识管理工具），可留审计记录（04:42-06:19）
- 使用建议：「不要试图优化 OptMem——它的摘要缓存就是设计成可以丢的，先跑起来用一周再决定要不要 Fork」（07:33-07:43，from 452-463）

## 与 Kairos 的映射点
| 外部理念 | 时间戳 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|:--|
| log.txt append-only 唯一真相源 + Tree 可重建总结缓存 | 02:04 | 已覆盖 | 见证锚定主副本 + 使用权重影子副本（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.2 组件/§5.5）；可审计压缩（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：OptMem 的「不可变真相源 + 可重建派生层」与 Kairos 双副本结构同构——是「见证锚定」的极简工程实证 | 与 REPO-02「唯一源 + 可重建缓存」实证一致 |
| 软删除 + 日志永删条目（Forget 标记，Nap 清理） | 03:22 | 已覆盖 | 遗忘调度器：资源再分配而非数据删除（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2） | 支撑：OptMem 的软删除是「遗忘非删除」的落地方案 | — |
| 压缩由 Agent 主动触发（无后台进程无定时任务） | 01:45 | 张力 | 遗忘调度器独立运行、受控优化（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；探索预算独立（S-12） | 挑战：OptMem 把压缩触发完全交给 Agent 自律（收到 Merge 提示后自行执行）；Kairos 的遗忘/巩固是系统级调度职责而非 Agent 自律——「谁有权触发压缩」的归属差异 | 契约是运行时投影（§2.2）下，Agent 触发可作轻量场景；Kairos 调度器职责不可外包 |
| 位置即身份（定宽记录 O(1) 读取） | 02:25 | 未触及 | — | 未触及：纯工程实现技巧，与认知语义无关 | 可作实现注记（若 Kairos 落地文件型存储） |
| 纯文本可版本控制（git/Dropbox 同步） | 00:59 | 未触及 | 端云同步协议（可选拓扑）（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.11） | 支撑：文件级可移植同步是 Kairos 可移植备份格式（§5.15）的可选形态 | 实现级参照 |
| Recall 正则检索、明确放弃语义相似 | 05:45 | 张力 | 三信号混合检索（语义+BM25+实体，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3a） | 挑战：OptMem 以「检索能力下限（精确匹配）」换取「零依赖」，Kairos 三信号是语义优先——不同定位，取舍不冲突但不可互推 | 工程取舍注记 |
| 「摘要缓存设计成可以丢的」 | 07:33 | 已覆盖 | 使用权重影子副本可重建、见证锚定主副本不可丢（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5） | 支撑：明确「哪个副本可丢、哪个不可丢」正是 Kairos 双副本的职责边界 | — |

## 存疑与未验证
- 视频称每条记录固定 **280 字节**；REPO-02 源码实证为 **LOG_REC=320 字节**（memo:72）——数字不一致，疑为版本差异或 UP 主口误（未验证）
- 视频称「426 token prompt + 31KB 脚本」与 REPO-02 README「426-token prompt, a script」一致，脚本行数与 KB 未逐一核对（未验证）
- 「100 万条记忆 608MB、Wake 0.03 秒」为视频声称，REPO-02 README 同口径（`README.md`），未实测（未验证）
- 「Wrong Research」应为「Roam Research」（音译串词），OptMem 定位为「纯文本版 Roam Research」更合理（推断，未验证）
- 「Windows 原生支持、1600 笔并发写入全部入库」为 UP 主实测演示，数字未复核（未验证）
- 安装命令中的 raw.githubusercontent URL 为视频演示，未实际执行（未执行）

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
