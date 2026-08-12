"""Mnemosyne 备份 → Kairos 批量导入脚本（2026-08-12）。

解析 D:\\amber-db-backup-final-20260812.sql 的 COPY public.memories 块，
过滤无效数据（is_deleted / peer_profile 元数据 / 空内容），映射到
Kairos MemoryWriteInput 语义，经 POST /v1/memories/batch 批量导入（100/批）。
"""
import json
import re
import sys
import urllib.request

BACKUP = r"D:\amber-db-backup-final-20260812.sql"
BASE = "http://127.0.0.1:8010"
API_KEY = "Dyu2Oe5epnj2-GKkdtsWgsQaTCYGIdDsnqb1Tn2GRdg"
BATCH = 100
PROVENANCE = "external_calibration"


def unescape_copy_field(field: str):
    """COPY 格式反转义：\\N → None；\\t → tab；\\n → newline；\\\\ → \\。"""
    if field == r"\N":
        return None
    out = []
    i = 0
    while i < len(field):
        ch = field[i]
        if ch == "\\" and i + 1 < len(field):
            nxt = field[i + 1]
            if nxt == "N":
                out.append("")
                i += 2
                continue
            out.append({"t": "\t", "n": "\n", "r": "\r", "\\": "\\"}.get(nxt, nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def main():
    raw = open(BACKUP, encoding="utf-8").read()
    m = re.search(
        r"COPY public\.memories \((.*?)\) FROM stdin;\n(.*?)\n\\\.\n", raw, re.S
    )
    if not m:
        print("FAIL: COPY 块未找到")
        sys.exit(1)
    cols = [c.strip() for c in m.group(1).split(",")]
    idx = {name: i for i, name in enumerate(cols)}
    body = m.group(2)

    valid, skipped = [], {"deleted": 0, "peer_profile": 0, "empty": 0}
    for line in body.split("\n"):
        if not line.strip() or line.strip() == r"\.":
            continue
        fields = [unescape_copy_field(f) for f in line.split("\t")]
        if len(fields) != len(cols):
            continue
        is_deleted = fields[idx["is_deleted"]]
        category = fields[idx["category"]] or ""
        content = fields[idx["content"]] or ""
        if is_deleted == "t":
            skipped["deleted"] += 1
            continue
        if category == "peer_profile":
            skipped["peer_profile"] += 1
            continue
        if not content.strip():
            skipped["empty"] += 1
            continue
        created_at = fields[idx["created_at"]]
        valid.append(
            {
                "path": "kairos://_user/hermes/memories/",
                "content": content,
                "provenance": PROVENANCE,
                "contract": "ondemand",
                "memory_types": ["semantic"],
                "occurred_at": created_at,
            }
        )

    print(f"有效待导入: {len(valid)}  跳过: {skipped}")

    # 批量导入
    total_ok, total_fail = 0, 0
    fail_codes: dict[str, int] = {}
    fail_samples: list[dict] = []
    with open(r"D:\projects\kairos-memory\scripts\import_valid.json", "w", encoding="utf-8") as fv:
        json.dump(valid, fv, ensure_ascii=False)
    for start in range(0, len(valid), BATCH):
        chunk = valid[start : start + BATCH]
        req = urllib.request.Request(
            f"{BASE}/v1/memories/batch",
            data=json.dumps({"items": chunk}).encode(),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
            total_ok += result.get("success_count", 0)
            total_fail += result.get("failed_count", 0)
            for item in result.get("results", []):
                if item.get("status") == "error":
                    code = item.get("code", "?")
                    fail_codes[code] = fail_codes.get(code, 0) + 1
                    if len(fail_samples) < 8:
                        fail_samples.append(
                            {"index": item.get("index"), "code": code, "message": item.get("message", "")}
                        )
        except Exception as exc:
            print(f"批 {start//BATCH} 请求失败: {exc}")
            total_fail += len(chunk)
    print(f"导入完成: 成功 {total_ok} / 失败 {total_fail}")
    print("失败码分布:", fail_codes)
    for s in fail_samples:
        print("  样例:", s)


if __name__ == "__main__":
    main()
