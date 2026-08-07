---
title: REPO-02 仓库分析：OptMem
aliases:
  - 外部仓库分析-02
tags:
  - kairos
  - external-videos
  - repo-analysis
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# REPO-02 OptMem

## 元信息
| 项 | 值 |
|:--|:--|
| 仓库 | https://github.com/VictorTaelin/OptMem |
| Star | 1129★（任务简报口径，2026-08-07） |
| 语言/许可 | 单文件 Python 3（零依赖，约 860 行）/ **仓库无 LICENSE 文件**（存疑，见下） |
| 视频对应 | VID-33（BV1QwGT6MEKQ，素材级别 C——短剧串台，无可用字幕；仅视频标题「一行一段永久记忆」可对照） |
| 分析日期 | 2026-08-07 |
| 素材来源声明 | 直连 GitHub 失败，经 gh-proxy 镜像下载 main 分支 tarball（无 .git，无 commit SHA）；作者 VictorTaelin 为 HVM/Bend 生态创立者（视频备注语境） |

## 项目定位（README 口径 vs 源码实证）

**README 口径**：「Permanent memory for AI agents. A 426-token prompt, a script, plug and play.」——安装脚本打印一段 `## Memory` 提示块粘贴到 `AGENTS.md` 顶部即完成接入；记忆 = 一行一条、最多 280 字节；「百万条记忆（608MB）时 wake 仅 0.03s」；「OptMem outlives every session, compaction, model and vendor change」；无后台进程，一切显式驱动（`README.md`, 30-31, 50-57）。

**源码实证**：与 README **高度一致**——整个工具就是一个文件 `memo`（Python 3，零依赖），完整实现可逐行验证。这是 4 个仓库中唯一「口径=实现」的项目。

## 架构与核心机制（源码实证，全部在 `memo` 单文件）

1. **存储：追加型定宽日志 + 可重建摘要树**
   - `LOG.txt`：追加型（append-only，`log_append()`，memo:335-350），**定宽记录 LOG_REC=320 字节**（memo:72），**位置即身份**（memory i 位于 i×320 字节偏移，O(1) seek，免索引同步）；崩溃时 `repair()` 截断半条记录（memo:228-238）；fsync 落盘
   - `TREE/<size>`：逐级摘要文件（TREE_REC=288 字节），块 [lo,hi) 的摘要 = 该块两半摘要的压缩；摘要只是**可重建缓存**（README「a cache, rebuildable from the log alone」；memo:26-27 注释）——日志是唯一源
2. **检索：年龄-粒度自适应预算（cover 算法）**
   - `cover(T, budget)`（memo:104-131）：把日志 [0,T) 平铺为对齐的 2 的幂块，约束「块大小 ≤ α×块龄」，二分 α 使块数 ≤ WAKE_LINES=96（≈8k token）——**细节随龄衰减**：近期记忆逐字保留、远古记忆折叠为摘要；预算花不完时把剩余预算拆给最近的块（memo:124-130）
   - `wake`：按 cover 输出打印块（单条=原文 `#id date text`，多块=摘要 `#lo-hi 摘要`）；`recall <regex>` 流式全量扫描日志，只保留最新命中且受输出预算限制（memo:731-759）；`zoom lo-hi` 打开树节点两半下钻到原文
   - 输出**分页**（PART_CHARS=20000 字节 / PART_LINES=500 行，memo:58-63）：适配各 harness 截断（Claude Code 切中段 30k 字符、pi 切头 50KB、Codex 10k token）
3. **更新/巩固：agent 亲自压缩（in-the-loop）**
   - `nap`（memo:463-494）：压缩提示——「把 #lo-hi 压缩成一行，保留有持久影响的、丢弃没有的、不虚构」；**由 agent（LLM）执行压缩**，按序构建（`pending()` 最小块优先，memo:437-449）；note 后若欠压缩立即提示。工具零后台进程——巩固是会话内显式动作
4. **遗忘：只删摘要、永不删原文**
   - `forget lo-hi`（memo:718-728, `tree_drop()` memo:372-389）：截断 TREE 各级到该块，级联删掉其派生块，**日志分毫不动**——「nothing is ever actually lost」；坏摘要（写坏/压缩错）下次 nap 重建
5. **并发与身份纪律**
   - 文件锁（fcntl/Windows msvcrt 自旋，memo:302-332）：多会话并行安全，id 在锁内分配
   - **subagent 禁写**（README prompt）：子代理不得运行 memo——「它无法判断什么已已知，其笔记会重复且错误」；并行会话「都是你」（同一身份）
   - `store()` 拒绝非 init 命令创建目录（memo:140-149）：防 MEMORY_DIR 拼写错误静默开出第二个空身份

## 关键设计决策（与视频声称对照）

| 视频声称 | 源码验证结果 |
|:--|:--|
| 「一行一段永久记忆」 | **一致**：note 强制单行、≤280 字节（`check()` memo:421-432）；日志永久保留、只增不改 |
| 「永久」 | **部分一致**：原文永久，但摘要（树）会被覆盖重建、可被 forget 丢弃——「永久」指原始记录层，投影层非永久 |
| （其余视频声称） | **不适用**：VID-33 为 C 级短剧串台素材，无可用字幕内容（见 [笔记](../notes/VID-33-BV1QwGT6MEKQ.md)，尚未产出） |

## 与 Kairos 的映射点
| 外部理念 | 分诊（初步） | Kairos 证据 | 第一性原理评估 | 备注 |
|:--|:--|:--|:--|:--|
| 追加型定宽日志 + 位置即身份（O(1) seek、免索引同步） | 已覆盖（工程增量可吸收） | ADD-only 写入协议（[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §7.3g）；见证锚定主副本不可变（§5.5） | 支撑：「定宽记录使位置=身份」是 ADD-only 的工程化——Kairos 语义上同构，但未规定存储布局 | 工程参数（LOG_REC=320B/TREE_REC=288B/fsync/repair）可作实现参照 |
| 摘要树=可重建缓存（日志可全量重建，缓存损坏可丢弃重建） | **已覆盖/强共鸣** | 使用权重影子副本「可重建缓存」声明（R-03，[architecture-v0.1.0.md](../../../foundation/architecture-v0.1.0.md) §5.5）；激活-存储解耦（认知基础 §2.2） | 支撑：OptMem 把「缓存可重建、源不可删」落成逐级树结构，与 Kairos 影子副本可重建性声明同构 | 可入 R-03 的实现参照 |
| cover()：块粒度≤α×块龄、二分求最细粒度满足预算（细节随龄衰减） | 可吸收 | 时间轴物理衰减+逻辑因果双轴（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1）；检索深度分级 R0/R1/R2（架构 §3.9） | 支撑：年龄→粒度自适应是「物理衰减」的检索侧投影；预算驱动而非评分驱动，天然无标量聚合 | 可作 Kairos 检索预算分配算法参照（二分 α + 剩余预算投给近期） |
| agent 亲自压缩（nap 提示+人/agent in-the-loop 巩固） | 张力 | 升华管道 raw→item→strategy→behavior（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.3.1）为体系内自动管道 | 挑战：OptMem 巩固依赖 agent 纪律（提示文本而非强制），压缩质量不可审计；Kairos 要求可审计压缩（§2.2） | 「压缩提示的认知诚实措辞」（保留持久影响/不虚构/显式丢弃）可吸收进管道提示 |
| forget=删摘要不删原文（遗忘的是投影） | 已覆盖 | 遗忘调度器「受控优化」（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.2）；遗忘后重建循环 | 支撑：遗忘作用于可重建投影、源保留——与 Kairos「遗忘不摧毁见证」同向 | 「坏摘要显式遗忘→下次重建」是受控遗忘的实现形态 |
| subagent 禁写规则（子代理不能判断已知性） | 可吸收 | 身份面否决权（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §2.1）；监督平面 | 未触及：Kairos 未声明「子代理不得写记忆」的权限纪律 | 可直接吸收为写入面权限规则 |
| WAKE_LINES 是阅读预算而非存储预算（改它不重算） | 可吸收 | 检索深度分级 R0/R1/R2（架构 §3.9）是检索侧预算 | 支撑：阅读预算与存储解耦，调整零成本 | 「预算只选打印内容、不动存储」的决策与 Kairos 激活-存储解耦（§2.2）同向 |
| 无使用价值度量、无 TTL、无嵌入检索（纯时间+正则+agent 判断） | 未触及 | 使用价值轴（[cognitive-foundation.md](../../../foundation/cognitive-foundation.md) §1.1） | 未触及：OptMem 检索是穷举流式+正则，无语义/使用度信号——是 Kairos 五轴的退化子集，不构成挑战 | 其「recall 全量扫描」在百万级仍可行得益于定宽布局 |

## 可吸收增量（具体到机制/参数/接口）
1. **cover() 年龄-粒度预算算法**（`memo` 的 `_cover`/`cover`，memo:82-131）：对齐 2 的幂块 + 二分 α + 剩余预算投给近期；可直接作为 Kairos 检索预算分配（R0/R1/R2 内层）的算法参照
2. **定宽记录布局**（LOG_REC=320/TREE_REC=288，memo:66-73）：位置即身份、单 seek 取数、崩溃 repair 截断半记录、逐级文件长度即进度（`pending()` 免扫描，memo:437-449）——ADD-only 存储工程参数集
3. **摘要层「显式 forget→nap 重建」循环**（memo:372-389, 718-728）：坏摘要不修补而是丢弃重建——可入 Kairos 遗忘调度器「投影可重建」注记
4. **输出分页协议**（PART_CHARS/PART_LINES，memo:569-581）：按 harness 截断特性（中段/头/预算）分包输出 + 页脚续读指令——Kairos 若做 agent 侧输出需同款适配
5. **subagent 禁写纪律**：记忆写入要求「能判断已知性」的主体身份——写入面权限规则
6. **压缩提示的认知诚实措辞**（memo:481-486）：「保留持久影响、丢弃无关、不虚构、一行≤280 字节」——可吸收进升华管道提示模板

## 存疑与未验证
- 「百万记忆 608MB、wake 0.03s」为 README 自述（`README.md`:55）；`test.py` 仅以 2000 条合成记忆做不变量测试（test.py:20-29），未实测百万级（未验证）
- **无 LICENSE 文件**（tarball 中不存在）——许可状态以 GitHub 页面为准（未验证）
- 「426-token prompt」为 README 自述，未实测 token 数（未验证）
- Windows 锁为 msvcrt 自旋+退避（memo:311-331），代码注释自述「30 秒超时抛错」，多进程高竞争下行为未实测（未验证）
- 压缩质量完全依赖 agent（LLM）遵循提示——无任何自动校验（`forget` 是唯一纠错路径），此弱点为设计取舍而非缺陷

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 外部视频分析批次初始化（素材抓取/转写/精读） |
