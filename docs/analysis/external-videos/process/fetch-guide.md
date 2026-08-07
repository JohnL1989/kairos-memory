---
title: 字幕抓取与转写流程记录
aliases:
  - 抓取流程记录
tags:
  - kairos
  - external-videos
  - process
created: 2026-08-07
updated: 2026-08-07
last_reviewed: 2026-08-07
status: draft
---

# 字幕抓取与转写流程记录

> 本文档记录 2026-08-07 批次的字幕获取技术路径，供复现与审计。**不含任何凭据**（Cookie 仅为运行时内存使用，未落盘入库）。

## 一、B站 AI 字幕串台问题（本批次最重要技术发现）

**现象**：通过 B站 字幕接口获取的 `ai-zh` AI 字幕中，约 65% 的视频字幕内容与视频主题完全无关（串台），且多个无关视频可能返回完全相同字幕。已排除请求方因素：

| 验证 | 结论 |
|:--|:--|
| 无签名接口 `x/player/v2`（带 Cookie） | 返回串台字幕 |
| wbi 签名接口 `x/player/wbi/v2`（网页播放器同款，完整实现签名算法） | 返回**同一个**串台字幕（URL 完全一致） |
| yt-dlp extractor | 走同一字幕源，同样串台 |
| 视频 cid 唯一性 | 串台字幕与 cid 绑定，与接口形态无关 |

**结论**：串台发生在 B站 侧（AI 字幕系统音频指纹错误关联），**无法通过任何接口规避**。唯一可靠途径是本地转写（本文档第三节）。

**人工核验方法**：对每个视频的字幕取「中段（30%-60%）去重采样」与视频标题主题比对——仅凭开头几秒会误判（部分 UP 视频开头是自我介绍/引子）。

## 二、AI 字幕抓取（仅对匹配视频有效）

1. 元信息：`GET https://api.bilibili.com/x/web-interface/view?bvid=<bvid>` → `data.pages[].cid`（多P 逐 cid）
2. 字幕列表：`GET https://api.bilibili.com/x/player/v2?bvid=<bvid>&cid=<cid>`（需 Cookie 头）→ `data.subtitle.subtitles[]` 找 `lan=="ai-zh"` → `subtitle_url`
3. 字幕正文：`GET <subtitle_url>`（**不带 Cookie**——实测带 Cookie 返回异常/不完整；仅需 UA + Referer）
4. 正文格式：JSON，`body[]` 每项 `{from, to, content}`（秒）

**注意事项**：
- 字幕 URL 为**单次有效签名**：player/v2 每次返回新 URL，需获取后立即下载；重复请求同一 URL 返回 403
- 同一视频反复请求 player/v2 可能触发字幕获取次数限制（返回空字幕列表），需间隔重试
- 频率控制：串行 + 2~5s 随机抖动，412 指数退避（30s→300s），连续 3 次 412 暂停整批

## 三、本地 whisper 转写（可靠替代路径）

1. 音频下载：`yt-dlp -f bestaudio -x --audio-format mp3 -o "<out>/p%(playlist_index)02d.%(ext)s" <url>`（多P 自动分文件；单P 时 playlist_index 为 NA，不影响功能）
2. 模型：faster-whisper `small`（CPU，int8 量化，中文可用）
3. 国内网络必需：`HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1`（新版 huggingface_hub 默认 xet 协议下载，hf-mirror 不支持会 401；禁用 xet 后走普通 HTTP）
4. 转写：`model.transcribe(audio, language="zh", vad_filter=True)`，速度约 3.5× 实时（small/int8/CPU）

## 四、弹幕/评论降级链

| 接口 | 状态 |
|:--|:--|
| `x/v1/dm/list.so?oid=<cid>` | ❌ 2026-08 实测返回二进制加密数据（非 XML），公开接口已变更 |
| yt-dlp `--write-subs --sub-langs danmaku` | ✅ 可下载弹幕 XML（该版本 yt-dlp 无 `--write-danmaku` 选项，弹幕按 subtitle 语言处理） |
| `x/v2/reply/main?type=1&oid=<cid>` | 公开可用，但小 UP 视频评论常为空 |
| `x/web-interface/view/conclusion/get` | ❌ 返回 -403（AI 总结接口权限受限） |

## 五、工具脚本（可入库）

| 脚本 | 职责 |
|:--|:--|
| [scripts/fetch_bilibili_subs.py](../../../scripts/fetch_bilibili_subs.py) | AI 字幕批量抓取：stdin/文件注入 Cookie（禁 `--cookie` 参数）、幂等跳过、频率控制、manifest 记录 |
| [scripts/transcribe_batch.py](../../../scripts/transcribe_batch.py) | 批量转写：yt-dlp 下载 + faster-whisper 转写 + 合并输出，幂等跳过 |

## 版本记录

| 版本 | 日期 | 摘要 |
|:-----|:-----|:-----|
| 0.0.1 | 2026-08-07 | 批次抓取流程记录：串台问题验证（两种接口形态）、wbi 签名实现、whisper 转写管线、降级链实测 |
