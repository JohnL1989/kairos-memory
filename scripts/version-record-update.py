#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本记录回填生成式脚本 —— round23 结构性建议 S23-2 落地。

对指定文档的「版本记录」表（`| 版本 | 日期 | 说明 |`）追加一行版本记录，
并同步校正 frontmatter 的 updated / last_reviewed 日期（不得早于新版本日期）。

用法:
    python scripts/version-record-update.py \
        --version 0.0.54 --date 2026-08-08 \
        --desc "round23 结构性建议落地批次（changelog 0.0.54）：S23-1 ..." \
        docs/governance/changelog.md docs/foundation/architecture-v0.1.0.md ...

特性:
  - 幂等：目标版本号已存在时跳过（不重复插入）。
  - 全库扫描模式：--all 时自动扫描 docs/ 下所有含该版本号（changelog 批次）
    的文档，其余文档跳过（用于「某批次只改部分文档」的回填）。
  - 保持 LF 行尾（统一 newline='' 二进制安全读写），不引入 CRLF。
  - frontmatter 日期倒挂校正：updated/last_reviewed 若早于 --date 则更新。
  - 报告每份文档的处置结果（插入/跳过/无版本记录表/无 frontmatter）。

仅依赖标准库。注意：changelog 的版本记录是「批次叙述节」（## 0.0.X），
不是版本记录表，本脚本只处理表格形态的版本记录。
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

SECTION_MARK = "\u00a7"  # §
ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
VERSION_HEADER = "| 版本 | 日期 | 说明 |"


def md_files() -> list[pathlib.Path]:
    """受治理 Markdown 文档（跳过审计产物目录）。"""
    out = []
    for p in DOCS.rglob("*.md"):
        if "reviews" in p.parts:
            continue
        out.append(p)
    return out


def read_text(p: pathlib.Path) -> str:
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write_text(p: pathlib.Path, text: str) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def find_version_table(lines: list[str]) -> int | None:
    """定位版本记录表头行（`| 版本 | 日期 | 说明 |`）索引。"""
    for i, ln in enumerate(lines):
        if ln.strip() == VERSION_HEADER:
            return i
    return None


def has_version_row(lines: list[str], version: str) -> bool:
    """版本记录表中是否已有该版本行。"""
    return any(
        re.match(r"^\|\s*" + re.escape(version) + r"\s*\|", ln) for ln in lines
    )


def bump_frontmatter(text: str, date: str) -> str:
    """把 frontmatter 中早于 date 的 updated/last_reviewed 校正为 date。"""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm = text[3:end]
    body = text[end:]
    changed = False
    lines = fm.split("\n")
    for i, ln in enumerate(lines):
        m = re.match(r"^(updated|last_reviewed):\s*(\S+)\s*$", ln)
        if m and m.group(2) < date:
            lines[i] = f"{m.group(1)}: {date}"
            changed = True
    if not changed:
        return text
    return "---" + "\n".join(lines) + body


def insert_row(lines: list[str], hdr: int, version: str, date: str, desc: str) -> list[str]:
    """在版本记录表最后一行后插入新版本行。"""
    row = f"| {version} | {date} | {desc} |"
    # 表头之后找最后一行表格行（`| ... |`）
    last = hdr
    for j in range(hdr + 1, len(lines)):
        if lines[j].lstrip().startswith("|"):
            last = j
        else:
            break
    return lines[: last + 1] + [row] + lines[last + 1 :]


def process(p: pathlib.Path, version: str, date: str, desc: str, stats: dict) -> None:
    try:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(p)
    text = read_text(p)
    lines = text.split("\n")
    hdr = find_version_table(lines)
    if hdr is None:
        stats["no_table"] += 1
        print(f"[跳过] {rel}: 无版本记录表")
        return
    if has_version_row(lines, version):
        stats["skip"] += 1
        print(f"[跳过] {rel}: 版本 {version} 已存在")
        return
    new_lines = insert_row(lines, hdr, version, date, desc)
    new_text = bump_frontmatter("\n".join(new_lines), date)
    write_text(p, new_text)
    stats["inserted"] += 1
    print(f"[插入] {rel}: 版本 {version} 行 + frontmatter 校正")


def main() -> int:
    ap = argparse.ArgumentParser(description="版本记录回填生成式脚本（S23-2）")
    ap.add_argument("--version", required=True, help="版本号，如 0.0.54")
    ap.add_argument("--date", required=True, help="日期，如 2026-08-08")
    ap.add_argument("--desc", required=True, help="版本记录说明（一行）")
    ap.add_argument("files", nargs="*", help="目标文档路径（相对仓库根）；--all 时忽略")
    ap.add_argument("--all", action="store_true",
                    help="全库扫描：对 changelog 中含该版本号的文档回填")
    args = ap.parse_args()

    if args.all:
        changelog = DOCS / "governance" / "changelog.md"
        cl = read_text(changelog)
        if f"## {args.version}（" not in cl:
            print(f"错误：changelog 中无批次节 ## {args.version}（，无法全库扫描")
            return 1
        # 该批次涉及的文件 = changelog 批次叙述节内出现的 .md 文件名 + 全库
        # 已含该版本号的文档。这里采用保守策略：扫描所有含该版本的文档。
        targets = []
        for p in md_files():
            t = read_text(p)
            if re.search(r"^\|\s*" + re.escape(args.version) + r"\s*\|", t, re.M):
                targets.append(p)
        if not targets:
            print(f"全库扫描：无文档含版本 {args.version}，需显式指定文件")
            return 1
    else:
        if not args.files:
            ap.error("必须指定目标文件或使用 --all")
        targets = []
        for f in args.files:
            p = (ROOT / f) if not pathlib.Path(f).is_absolute() else pathlib.Path(f)
            if not p.is_file():
                print(f"错误：文件不存在 {f}")
                return 1
            targets.append(p)

    stats = {"inserted": 0, "skip": 0, "no_table": 0}
    for p in targets:
        process(p, args.version, args.date, args.desc, stats)
    print(
        f"\n完成：插入 {stats['inserted']} / 跳过 {stats['skip']} / 无表 {stats['no_table']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
