#!/usr/bin/env python3
"""B站视频批量本地转写脚本（Kairos 外部视频分析批次配套工具）

用途：对 B站 AI 字幕串台/缺失的视频，下载音频后本地转写（faster-whisper），
作为可信内容素材。输出合并为 <bvid>/whisper.content.json（多P 合并，分段带 part）。

前置：
- yt-dlp 可用（用于下载音频）
- faster-whisper 已安装；模型经 HF_ENDPOINT=https://hf-mirror.com 与
  HF_HUB_DISABLE_XET=1 下载（国内网络必需）

用法：
  HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 \
  python scripts/transcribe_batch.py --list video-work/transcribe_list.json
"""
import argparse
import json
import os
import subprocess
import sys
import time

YTDLP = r"C:\Users\54111\AppData\Local\hermes\hermes-agent\venv\Scripts\yt-dlp.exe"


def download_audio(bvid: str, out_dir: str) -> list[str]:
    """下载全部 P 的音频，返回 mp3 文件路径列表（按 P 序号排序）。"""
    subprocess.run(
        [
            YTDLP, "-f", "bestaudio", "-x", "--audio-format", "mp3",
            "--no-warnings", "-o", os.path.join(out_dir, "p%(playlist_index)02d.%(ext)s"),
            f"https://www.bilibili.com/video/{bvid}/",
        ],
        check=False, capture_output=True, timeout=900,
    )
    files = sorted(f for f in os.listdir(out_dir) if f.endswith(".mp3"))
    return [os.path.join(out_dir, f) for f in files]


def main() -> int:
    ap = argparse.ArgumentParser(description="B站视频批量本地转写")
    ap.add_argument("--list", required=True, help="转写清单 JSON（数组，含 bvid/note）")
    ap.add_argument("--out", default="video-work", help="输出目录（默认 video-work/）")
    ap.add_argument("--model", default="small", help="whisper 模型（默认 small）")
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    print(f"加载模型 {args.model} ...", flush=True)
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    print("模型就绪", flush=True)

    videos = json.load(open(args.list, encoding="utf-8"))
    for i, v in enumerate(videos, 1):
        bvid = v["bvid"]
        bvid_dir = os.path.join(args.out, bvid)
        os.makedirs(bvid_dir, exist_ok=True)
        out_path = os.path.join(bvid_dir, "whisper.content.json")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 10:
            print(f"[{i}/{len(videos)}] {bvid} 已转写，跳过", flush=True)
            continue
        print(f"[{i}/{len(videos)}] {bvid} 下载音频...", flush=True)
        t0 = time.time()
        try:
            mp3s = download_audio(bvid, bvid_dir)
        except Exception as e:
            print(f"  {bvid} 下载失败: {type(e).__name__}", flush=True)
            continue
        if not mp3s:
            print(f"  {bvid} 无音频文件", flush=True)
            continue
        all_segs = []
        for mp3 in mp3s:
            print(f"  转写 {os.path.basename(mp3)}...", flush=True)
            segments, info = model.transcribe(mp3, language="zh", vad_filter=True)
            part = os.path.basename(mp3)
            for s in segments:
                all_segs.append({
                    "from": round(s.start, 2), "to": round(s.end, 2),
                    "content": s.text.strip(), "part": part,
                })
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_segs, f, ensure_ascii=False)
        print(f"  {bvid} 完成: {len(all_segs)} 条，用时 {time.time()-t0:.0f}s", flush=True)

    print("全部完成", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
