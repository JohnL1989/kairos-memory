#!/usr/bin/env python3
"""B站 AI 字幕批量抓取脚本（Kairos 外部视频分析批次配套工具）

用途：输入 BVID 清单（JSON 数组），逐个抓取视频（含多P）的 AI 字幕（ai-zh），
落盘到输出目录，并生成 manifest.json 记录每个分P的抓取状态。

安全约定（S 级红线）：
- 凭据绝不进入命令行参数；Cookie 从 --cookie-file 指向的文件读取（须放在仓库外）
- 不打印 Cookie、不打印请求头、异常输出不含请求细节
- 输出目录默认 gitignored（video-work/），原始字幕不入库

用法：
  python scripts/fetch_bilibili_subs.py --list video-work/videos.json \
      --cookie-file /c/Users/<user>/bili-sessdata.txt --out video-work/
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
REFERER = "https://www.bilibili.com/"
SUBTITLE_REFERER = "https://www.bilibili.com/"

# 风控退避参数
BASE_DELAY = (2.0, 5.0)      # 请求间随机抖动（秒）
BACKOFF_START = 30           # 412 首次退避（秒）
BACKOFF_MAX = 300            # 412 退避上限（秒）
MAX_CONSECUTIVE_412 = 3      # 连续 412 达到此数暂停整批


def http_get_json(url: str, cookie: str, referer: str = REFERER) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Referer": referer, "Cookie": cookie},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_bytes(url: str, cookie: str, referer: str = REFERER) -> bytes:
    # 注意：字幕 CDN（aisubtitle.hdslb.com）不应携带 Cookie——
    # 实测带 Cookie 会返回不完整/异常响应，无 Cookie 可正常下载。
    headers = {"User-Agent": UA, "Referer": referer}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read()


def get_pages(bvid: str, cookie: str):
    """返回 (pages, error)。pages: [{cid, part, duration}]"""
    try:
        d = http_get_json(
            f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", cookie
        )
    except urllib.error.HTTPError as e:
        return None, f"view-HTTP:{e.code}"
    except Exception as e:
        return None, f"view-NET:{type(e).__name__}"
    if d.get("code") != 0:
        return None, f"view-ERR:{d.get('code')}"
    return [
        {"cid": p["cid"], "part": p["part"], "duration": p["duration"]}
        for p in d["data"]["pages"]
    ], None


def find_ai_subtitle(bvid: str, cid: int, cookie: str):
    """返回 (subtitle_url, error)。无字幕时 error == 'no-subtitle'"""
    try:
        d = http_get_json(
            f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}", cookie
        )
    except urllib.error.HTTPError as e:
        return None, f"player-HTTP:{e.code}"
    except Exception as e:
        return None, f"player-NET:{type(e).__name__}"
    if d.get("code") != 0:
        return None, f"player-ERR:{d.get('code')}"
    for s in d.get("data", {}).get("subtitle", {}).get("subtitles", []):
        if s.get("lan") == "ai-zh":
            url = s["subtitle_url"]
            if url.startswith("//"):
                url = "https:" + url
            return url, None
    return None, "no-subtitle"


def main() -> int:
    ap = argparse.ArgumentParser(description="B站 AI 字幕批量抓取")
    ap.add_argument("--list", required=True, help="BVID 清单 JSON（数组，含 bvid 字段）")
    ap.add_argument("--cookie-file", required=True, help="Cookie 文件路径（仓库外，含完整 Cookie 头）")
    ap.add_argument("--out", default="video-work", help="输出目录（默认 video-work/）")
    ap.add_argument("--limit", type=int, default=0, help="仅抓前 N 个视频（0=全部，调试用）")
    args = ap.parse_args()

    with open(args.cookie_file, encoding="utf-8") as f:
        cookie = f.read().strip()
    with open(args.list, encoding="utf-8") as f:
        videos = json.load(f)

    os.makedirs(args.out, exist_ok=True)
    manifest = []
    consecutive_412 = 0
    backoff = BACKOFF_START
    total = len(videos[:args.limit] if args.limit else videos)

    for i, v in enumerate(videos[:args.limit] if args.limit else videos, 1):
        bvid = v["bvid"]
        bvid_dir = os.path.join(args.out, bvid)
        os.makedirs(bvid_dir, exist_ok=True)
        entry = {"bvid": bvid, "title": v.get("title", ""), "pages": []}

        pages, err = get_pages(bvid, cookie)
        if err:
            entry["status"] = "failed"
            entry["error"] = err
            manifest.append(entry)
            print(f"[{i}/{total}] {bvid} FAILED {err}")
            time.sleep(random.uniform(*BASE_DELAY))
            continue

        for p in pages:
            cid = p["cid"]
            pentry = {"cid": cid, "part": p["part"], "status": "pending"}
            content_path = os.path.join(bvid_dir, f"{cid}.content.json")
            if os.path.exists(content_path) and os.path.getsize(content_path) > 10:
                pentry["status"] = "ok-skip"
                pentry["segments"] = "已存在"
                entry["pages"].append(pentry)
                continue
            sub_url, err = find_ai_subtitle(bvid, cid, cookie)
            if err and err.startswith("player-HTTP:412"):
                consecutive_412 += 1
                if consecutive_412 >= MAX_CONSECUTIVE_412:
                    pentry["status"] = "risk-paused"
                    pentry["error"] = "连续 412，整批暂停"
                    entry["status"] = "risk-paused"
                    entry["pages"].append(pentry)
                    manifest.append(entry)
                    print(f"[{i}/{total}] {bvid} 风控触发，整批暂停")
                    write_manifest(args.out, manifest)
                    return 2
                print(f"  412 风控，退避 {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
                sub_url, err = find_ai_subtitle(bvid, cid, cookie)
            else:
                backoff = BACKOFF_START
                consecutive_412 = 0

            if err == "no-subtitle":
                pentry["status"] = "no-subtitle"
                entry["pages"].append(pentry)
                continue
            if err:
                pentry["status"] = "failed"
                pentry["error"] = err
                entry["pages"].append(pentry)
                continue

            try:
                raw = http_get_bytes(sub_url, cookie, SUBTITLE_REFERER)
                body = json.loads(raw.decode("utf-8"))
                with open(os.path.join(bvid_dir, f"{cid}.subtitle.json"), "wb") as f:
                    f.write(raw)
                content = [
                    {"from": seg.get("from"), "to": seg.get("to"), "content": seg.get("content", "")}
                    for seg in body.get("body", [])
                ]
                with open(os.path.join(bvid_dir, f"{cid}.content.json"), "w", encoding="utf-8") as f:
                    json.dump(content, f, ensure_ascii=False)
                pentry["status"] = "ok"
                pentry["segments"] = len(content)
            except Exception as e:
                pentry["status"] = "failed"
                pentry["error"] = f"sub-DL:{type(e).__name__}"
            entry["pages"].append(pentry)
            time.sleep(random.uniform(*BASE_DELAY))

        ok = sum(1 for p in entry["pages"] if p["status"] in ("ok", "ok-skip"))
        ns = sum(1 for p in entry["pages"] if p["status"] == "no-subtitle")
        entry["status"] = "ok" if ok else ("no-subtitle" if ns else "failed")
        manifest.append(entry)
        print(f"[{i}/{total}] {bvid} 完成（ok={ok} no-subtitle={ns}）")
        time.sleep(random.uniform(*BASE_DELAY))

    write_manifest(args.out, manifest)
    return 0


def write_manifest(out_dir: str, manifest: list) -> None:
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"manifest.json 已写入 {out_dir}/manifest.json")


if __name__ == "__main__":
    sys.exit(main())
