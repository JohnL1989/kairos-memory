#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kairos 文档深度审计 —— 独立于 doc-audit.py 的补充检查。"""
from __future__ import annotations

import collections
import json
import tempfile
import pathlib
import re
import sys

# Windows 默认控制台编码（GBK）无法编码 ↔ 等字符，强制 UTF-8 输出避免 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EXCLUDE = {"reviews"}

def docs_iter():
    for p in sorted(DOCS.rglob("*")):
        if p.is_dir() or p.suffix not in (".md", ".yaml"):
            continue
        if any(part in EXCLUDE for part in p.relative_to(DOCS).parts):
            continue
        yield p

REPORT: dict = collections.defaultdict(list)

# ---------- 1. frontmatter ----------
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
fm_data = {}
for p in docs_iter():
    if p.suffix != ".md":
        continue
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        REPORT["fm_missing"].append(rel)
        continue
    body = m.group(1)
    fields = {}
    for line in body.splitlines():
        mm = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line)
        if mm:
            fields[mm.group(1)] = mm.group(2).strip()
    fm_data[rel] = fields

REQUIRED = ["title", "created", "updated", "last_reviewed", "status"]
for rel, f in fm_data.items():
    miss = [k for k in REQUIRED if k not in f]
    if miss:
        REPORT["fm_incomplete"].append(f"{rel}: 缺 {miss}")

# frontmatter 字段取值分布
for key in ["status", "created", "updated", "last_reviewed"]:
    c = collections.Counter(f.get(key, "<none>") for f in fm_data.values())
    REPORT[f"fm_dist_{key}"].append(dict(c))

# tags 分布
tag_counter = collections.Counter()
for p in docs_iter():
    if p.suffix != ".md":
        continue
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        continue
    tags = re.findall(r"^\s*-\s+(\S+)$", m.group(1), re.M)
    tag_counter[tuple(sorted(tags))] += 1

# ---------- 2. 锚点链接 ----------
def slugify_headings(text):
    slugs = set()
    for line in text.splitlines():
        mm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if mm:
            h = mm.group(2).strip()
            s = re.sub(r"[^\w\u4e00-\u9fff\- ]", "", h).strip().lower().replace(" ", "-")
            slugs.add(s)
    return slugs

all_slugs = {}
for p in docs_iter():
    if p.suffix == ".md":
        rel = str(p.relative_to(DOCS)).replace("\\", "/")
        all_slugs[rel] = slugify_headings(p.read_text(encoding="utf-8"))

for p in docs_iter():
    if p.suffix != ".md":
        continue
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r"\[[^\]]*\]\(([^)]*#[^)]+)\)", text):
        target = m.group(1)
        if target.startswith("http"):
            continue
        path_part, _, anchor = target.partition("#")
        if path_part:
            tgt = (p.parent / path_part).resolve()
            try:
                trel = str(tgt.relative_to(DOCS)).replace("\\", "/")
            except ValueError:
                continue
        else:
            trel = rel
        if trel in all_slugs and anchor.lower() not in all_slugs[trel]:
            REPORT["anchor_broken"].append(f"{rel} -> {target}")

# ---------- 3. 孤儿文档 / 索引覆盖 ----------
readme = (DOCS / "README.md").read_text(encoding="utf-8")
linked = set()
for m in re.finditer(r"\(([^)]+\.(?:md|yaml))\)", readme):
    linked.add(m.group(1).lstrip("./").replace("\\", "/"))
for m in re.finditer(r"`([^`]+\.(?:md|yaml))`", readme):
    linked.add(m.group(1).lstrip("./").replace("\\", "/"))

actual = {str(p.relative_to(DOCS)).replace("\\", "/") for p in docs_iter()}
missing_from_index = sorted(actual - linked - {"README.md"})
if missing_from_index:
    REPORT["not_in_index"] = missing_from_index

# 入度统计（被引用次数）
indeg = collections.Counter()
for p in docs_iter():
    if p.suffix != ".md":
        continue
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r"\]\(([^)]+\.(?:md|yaml))", text):
        t = m.group(1).split("#")[0]
        tgt = (p.parent / t).resolve()
        try:
            indeg[str(tgt.relative_to(DOCS)).replace("\\", "/")] += 1
        except ValueError:
            pass
REPORT["indegree"] = [dict(sorted(((k, v) for k, v in indeg.items()), key=lambda x: x[1]))]
REPORT["indegree_zero"] = sorted(actual - set(indeg) - {"README.md"})

# ---------- 4. 标题编号体系 ----------
for p in docs_iter():
    if p.suffix != ".md":
        continue
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    styles = collections.Counter()
    for line in text.splitlines():
        mm = re.match(r"^(#{2,6})\s+(.*)$", line)
        if not mm:
            continue
        h = mm.group(2).strip()
        if re.match(r"^§?[一二三四五六七八九十]+[、.．]?\s", h) or re.match(r"^§?[一二三四五六七八九十]+\s", h):
            styles["cn"] += 1
        elif re.match(r"^§?\d+(\.\d+)*\.?\s", h):
            styles["num"] += 1
        elif re.match(r"^§?[A-Z](\.\d+)*\s", h):
            styles["alpha"] += 1
        else:
            styles["none"] += 1
    REPORT["heading_style"].append(f"{rel}: {dict(styles)}")

# ---------- 5. 未决标记 ----------
PENDING = ["TODO", "TBD", "FIXME", "待定", "待补", "待核定", "待确认", "待补充", "占位", "XXX", "???"]
for p in docs_iter():
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        for kw in PENDING:
            if kw in line:
                REPORT["pending"].append(f"{rel}:{i} [{kw}] {line.strip()[:140]}")
                break

# ---------- 6. 数量声明抽取 ----------
NUM_RE = re.compile(r"(\d+)\s*(项|个|张|类|条|层|维|轴|端点|表|阶段|步|级)")
num_claims = collections.defaultdict(list)
for p in docs_iter():
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        for m in NUM_RE.finditer(line):
            ctx = line.strip()[:120]
            num_claims[f"{m.group(1)}{m.group(2)}"].append(f"{rel}:{i}")
REPORT["num_claims"] = [{k: v for k, v in sorted(num_claims.items(), key=lambda x: -len(x[1]))}]

# ---------- 7. 版本号 / 日期 出现分布 ----------
ver = collections.Counter()
for p in docs_iter():
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r"v?\d+\.\d+\.\d+", text):
        ver[m.group(0)] += 1
REPORT["versions"] = [dict(sorted(ver.items(), key=lambda x: -x[1]))]

dates = collections.Counter()
for p in docs_iter():
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r"20\d\d-\d\d-\d\d", text):
        dates[m.group(0)] += 1
REPORT["dates"] = [dict(sorted(dates.items(), key=lambda x: -x[1]))]

# ---------- 8. 表格格式 ----------
for p in docs_iter():
    if p.suffix != ".md":
        continue
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    lines = p.read_text(encoding="utf-8").splitlines()
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        if re.match(r"^\s*\|[\s:|-]+\|\s*$", line) and i >= 2:
            header = lines[i - 2]
            if header.count("|") != line.count("|"):
                REPORT["table_mismatch"].append(f"{rel}:{i} 表头{header.count('|')}列/分隔{line.count('|')}列")

# ---------- 9. 行尾空白 / 制表符 / 超长行 ----------
for p in docs_iter():
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    raw = p.read_bytes()
    if b"\r\n" in raw:
        REPORT["crlf"].append(rel)
    if b"\t" in raw:
        REPORT["tab"].append(rel)
    text = raw.decode("utf-8")
    if not text.endswith("\n"):
        REPORT["no_final_newline"].append(rel)
    trailing = sum(1 for l in text.splitlines() if l != l.rstrip())
    if trailing:
        REPORT["trailing_ws"].append(f"{rel}: {trailing} 行")

# ---------- 10. 代码块语言标注 ----------
for p in docs_iter():
    if p.suffix != ".md":
        continue
    rel = str(p.relative_to(DOCS)).replace("\\", "/")
    text = p.read_text(encoding="utf-8")
    fences = re.findall(r"^ {0,3}```(\S*)", text, re.M)
    bare = sum(1 for f in fences[::2] if not f)
    if bare:
        REPORT["code_no_lang"].append(f"{rel}: {bare} 处")

out = pathlib.Path(tempfile.gettempdir()) / "kairos_deep_audit_out.json"  # 0.0.31：输出移入系统临时目录，仓库不残留（round11 审计 2.3-02）
out.write_text(json.dumps(REPORT, ensure_ascii=False, indent=1), encoding="utf-8")

for k in sorted(REPORT):
    v = REPORT[k]
    print(f"### {k} ({len(v)})")
    if k in ("num_claims", "indegree", "versions", "dates") or k.startswith("fm_dist"):
        print(json.dumps(v, ensure_ascii=False)[:2000])
    else:
        for item in v[:40]:
            print("  ", item)
        if len(v) > 40:
            print(f"   ...还有 {len(v)-40} 条")
    print()
