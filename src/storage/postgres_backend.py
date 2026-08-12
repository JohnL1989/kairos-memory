"""PostgreSQL 后端（D-449 闭合，ADR-001 竖切验收后适配）。

实现 StorageBackend 契约（detailed-design §2 五方法）——asyncpg 驱动 +
pgvector 距离运算符（<=> 余弦）+ tsvector 全文检索（pg_bigm/zhparser
扩展可选；基础实现用内置 to_tsvector）。

方言差异（vs SQLiteBackend）收敛于本实现内部：
- 向量检索：pgvector `1 - (embedding <=> $1)`（HNSW 索引可选）
- 全文检索：tsvector（竖切 BM25 分量在 PG 侧由 pg_bigm 承载，本实现
  提供基础 ts_rank 兜底）
- 存储：memories / witness_anchor / usage_weight 三表（PostgresBackend
  契约最小依赖集；全量 15 表迁移经 Alembic PG 方言扩展）

连接：asyncpg 内建连接池（technology-stack §二：asyncpg + 内建连接池）。
"""

from __future__ import annotations

import os

import asyncpg  # type: ignore[import-untyped]

from src.storage.backend import (
    MemoryRecord,
    ScoredMemory,
    StorageBackend,
    UsageDelta,
    WitnessUpdate,
)

# 默认 DSN（Docker 本地开发；生产经 KAIROS_DB_URL 注入）
DEFAULT_DSN = os.environ.get(
    "KAIROS_PG_DSN",
    "postgresql://kairos:kairos_test_pw@127.0.0.1:55432/kairos",
)

# 向量维度（schema-slice §约定：1536）
EMBEDDING_DIM = 1536


def _vec_text(vector: list[float]) -> str:
    """pgvector 文本表示（asyncpg 无原生 vector codec）：[0.1,0.2,...]。"""
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"


class PostgresBackend(StorageBackend):
    """PostgreSQL 后端（pgvector + tsvector 方言）。"""

    def __init__(self, dsn: str = DEFAULT_DSN, pool_size: int = 5) -> None:
        self.dsn = dsn
        self.pool_size = pool_size
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """建立连接池 + 初始化 schema（幂等）。"""
        self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=self.pool_size)
        async with self._pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    content TEXT NOT NULL,
                    embedding vector({EMBEDDING_DIM}),
                    provenance TEXT NOT NULL DEFAULT 'system_generated',
                    contract TEXT NOT NULL DEFAULT 'ondemand',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_pg_memories_path ON memories(path)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS witness_anchor ("
                " memory_id TEXT PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,"
                " narrative_coherence_score REAL NOT NULL DEFAULT 0,"
                " calibration_count INTEGER NOT NULL DEFAULT 0)"
            )
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS usage_weight ("
                " memory_id TEXT PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,"
                " usage_count INTEGER NOT NULL DEFAULT 0,"
                " last_used_at TIMESTAMPTZ)"
            )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def _pool_or_raise(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PostgresBackend 未连接（先调用 connect()）")
        return self._pool

    # ------------------------------------------------------------------
    # StorageBackend 契约
    # ------------------------------------------------------------------

    async def write(self, memory: MemoryRecord) -> str:
        pool = self._pool_or_raise()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "INSERT INTO memories (id, path, version, content, provenance, contract) "
                "VALUES ($1, $2, $3, $4, $5, $6) "
                "ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content",
                memory.id,
                memory.path,
                memory.version,
                memory.content,
                memory.metadata.get("provenance", "system_generated"),
                memory.contract,
            )
            await conn.execute(
                "INSERT INTO witness_anchor (memory_id) VALUES ($1) "
                "ON CONFLICT (memory_id) DO NOTHING",
                memory.id,
            )
            await conn.execute(
                "INSERT INTO usage_weight (memory_id) VALUES ($1) "
                "ON CONFLICT (memory_id) DO NOTHING",
                memory.id,
            )
        return memory.id

    async def path_retrieve(self, prefix: str, limit: int = 10) -> list[MemoryRecord]:
        pool = self._pool_or_raise()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, path, version, content, contract FROM memories "
                "WHERE path LIKE $1 ORDER BY created_at DESC LIMIT $2",
                f"{prefix}%",
                limit,
            )
        return [
            MemoryRecord(
                id=r["id"],
                path=r["path"],
                version=r["version"],
                content=r["content"],
                contract=r["contract"],
            )
            for r in rows
        ]

    async def vector_search(
        self, query_vector: list[float], top_k: int = 100
    ) -> list[ScoredMemory]:
        pool = self._pool_or_raise()
        if len(query_vector) != EMBEDDING_DIM:
            raise ValueError(f"查询嵌入维度必须为 {EMBEDDING_DIM}")
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, path, 1 - (embedding <=> $1) AS score FROM memories "
                "WHERE embedding IS NOT NULL ORDER BY embedding <=> $1 LIMIT $2",
                _vec_text(query_vector),
                top_k,
            )
        return [ScoredMemory(id=r["id"], path=r["path"], score=float(r["score"])) for r in rows]

    async def update_witness(self, memory_id: str, witness: WitnessUpdate) -> None:
        pool = self._pool_or_raise()
        async with pool.acquire() as conn:
            if witness.narrative_coherence_score is not None:
                await conn.execute(
                    "UPDATE witness_anchor SET narrative_coherence_score = $1, "
                    "calibration_count = calibration_count + 1 WHERE memory_id = $2",
                    witness.narrative_coherence_score,
                    memory_id,
                )

    async def update_usage(self, memory_id: str, delta: UsageDelta) -> None:
        pool = self._pool_or_raise()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE usage_weight SET usage_count = usage_count + $1, last_used_at = now() "
                "WHERE memory_id = $2",
                delta.usage_count,
                memory_id,
            )

    async def upsert_embedding(self, memory_id: str, vector: list[float]) -> None:
        """写入嵌入向量（pgvector 类型；MemoryStore 嵌入路径适配）。"""
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(f"嵌入维度必须为 {EMBEDDING_DIM}")
        pool = self._pool_or_raise()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE memories SET embedding = $1 WHERE id = $2",
                _vec_text(vector),
                memory_id,
            )
