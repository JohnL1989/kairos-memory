#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kairos 竖切性能基准（W9 交付物）。

判据（project-plan W9）：
- 写 P50 ≤ 50ms
- 路径检索 P50 ≤ 20ms
- 语义检索 P50 ≤ 100ms（1 万条 SQLite 基准）

用法：
    PYTHONIOENCODING=utf-8 uv run python scripts/benchmark.py --count 10000
报告写入 reports/benchmark-baseline-0.1.0.json。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import tempfile
import time
from pathlib import Path

from src.app import build_app
from src.config import load_settings
from src.storage.hybrid_search import SearchFilter
from src.storage.memory_store import MemoryWriteInput
from src.utils.embeddings import HashEmbedder, vector_to_bytes


async def _seed_memories(app, count: int, embedder: HashEmbedder) -> None:
    """批量写入记忆（嵌入批量预计算后事务写入，仅测量写入耗时）。"""
    from sqlalchemy import text

    vectors: dict[str, bytes] = {}
    # 预计算嵌入（HashEmbedder 确定性，可离线）
    for i in range(count):
        content = f"基准测试记忆第{i}条，主题关键词 topic{i % 100} 的内容描述。"
        vectors[content] = vector_to_bytes(await embedder.embed(content))

    async with app.db.session() as session:
        for i in range(count):
            content = f"基准测试记忆第{i}条，主题关键词 topic{i % 100} 的内容描述。"
            mid = f"bench-{i:06d}"
            await session.execute(
                text(
                    "INSERT INTO memories (id, path, version, content, content_hash, embedding, "
                    "memory_types, provenance, root_memory_id) "
                    "VALUES (:id, :path, 1, :content, :hash, :emb, '[\"semantic\"]', "
                    "'system_generated', :id)"
                ),
                {
                    "id": mid,
                    "path": f"kairos://_bench/topic{i % 100}/memories/{mid}",
                    "content": content,
                    "hash": f"h{i}",
                    "emb": vectors[content],
                },
            )
            await session.execute(
                text(
                    "INSERT INTO witness_anchor (memory_id) VALUES (:id)"
                ),
                {"id": mid},
            )
            await session.execute(
                text(
                    "INSERT INTO usage_weight (memory_id) VALUES (:id)"
                ),
                {"id": mid},
            )
        await session.commit()


async def _bench_write(app, count: int = 200) -> dict[str, float]:
    """写路径 P50（经 store.create 全链路：门禁+事务+双副本）。"""
    latencies: list[float] = []
    for i in range(count):
        start = time.perf_counter()
        await app.store.create(
            MemoryWriteInput(
                path="kairos://_user/bench/memories/",
                content=f"写入基准记忆第{i}条，内容长度足够用于测试。",
                provenance="system_generated",
            )
        )
        latencies.append((time.perf_counter() - start) * 1000)
    return {
        "p50_ms": statistics.median(latencies),
        "p95_ms": sorted(latencies)[int(len(latencies) * 0.95) - 1],
        "samples": count,
    }


async def _bench_path(app) -> dict[str, float]:
    """路径检索 P50（GET /v1/path 语义）。"""
    latencies: list[float] = []
    for i in range(100):
        start = time.perf_counter()
        await app.path_index.list_path(f"kairos://_bench/topic{i % 100}/")
        latencies.append((time.perf_counter() - start) * 1000)
    return {"p50_ms": statistics.median(latencies), "samples": 100}


async def _bench_semantic(app) -> dict[str, float]:
    """语义检索 P50（1 万条向量扫描，numpy 批量余弦）。"""
    latencies: list[float] = []
    for i in range(20):
        start = time.perf_counter()
        await app.search._semantic_recall(f"topic{i % 100}", prefix=None)
        latencies.append((time.perf_counter() - start) * 1000)
    return {"p50_ms": statistics.median(latencies), "samples": 20}


async def main(count: int = 10000) -> None:
    # 基准环境审计密钥（临时测试值，非真实密钥）
    import os

    os.environ.setdefault("KAIROS_AUDIT_HMAC_KEY", "0" * 64)
    tmpdir = Path(tempfile.mkdtemp(prefix="kairos-bench-"))
    settings = load_settings()
    from src.storage.db import Database

    db = Database(f"sqlite:///{tmpdir / 'bench.db'}")
    await db.run_migrations()
    app = build_app(settings, db=db)
    try:
        print(f"[bench] 写入 {count} 条种子记忆（含嵌入预计算）...")
        embedder = HashEmbedder()
        t0 = time.perf_counter()
        await _seed_memories(app, count, embedder)
        print(f"[bench] 种子写入完成 {time.perf_counter() - t0:.1f}s")

        write = await _bench_write(app)
        path = await _bench_path(app)
        semantic = await _bench_semantic(app)

        report = {
            "benchmark": "kairos-slice",
            "date": "2026-08-11",
            "seed_count": count,
            "results": {
                "write": write,
                "path_retrieval": path,
                "semantic_search": semantic,
            },
            "criteria": {
                "write_p50_le_ms": 50,
                "path_p50_le_ms": 20,
                "semantic_p50_le_ms": 100,
            },
        }
        out = Path("reports") / "benchmark-baseline-0.1.0.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["results"], ensure_ascii=False, indent=2))
        print(f"[bench] 报告已写入 {out}")

        # 判据核对
        ok = (
            write["p50_ms"] <= 50
            and path["p50_ms"] <= 20
            and semantic["p50_ms"] <= 100
        )
        print(f"[bench] 判据核对: {'PASS' if ok else 'FAIL'}")
    finally:
        await app.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000, help="种子记忆数")
    args = parser.parse_args()
    asyncio.run(main(count=args.count))
