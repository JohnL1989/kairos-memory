"""存储后端抽象层（StorageBackend）——detailed-design §2 后端抽象接口。

权威规格：detailed-design §2（write / path_retrieve / vector_search /
update_witness / update_usage 五方法抽象——业务代码仅依赖抽象，方言差异
收敛于各后端实现内部）；ADR-001 实施顺序（SQLite 首迭代，PostgreSQL 竖切
验收后适配）。

实现说明（D-449 前置落实）：
- StorageBackend 协议定义五方法契约（含类型）
- SQLiteBackend：竖切组件的存储门面（薄适配——委托现有 MemoryStore /
  DualCopyManager / VectorIndex，不重构业务组件；PG 适配时新增
  PostgresBackend 切换）
- MockPGBackend：接口可替换性验证（acceptance-criteria「StorageBackend
  接口可替换（mock PG 后端单测通过）」判据——mock 后端实现同契约，
  业务层无感）
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.storage.db import Database


@dataclass(frozen=True)
class MemoryRecord:
    """存储后端写入/检索的记忆记录（后端无关形态）。"""

    id: str
    path: str
    version: int = 1
    content: str = ""
    contract: str = "ondemand"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredMemory:
    """向量检索结果（后端无关形态）。"""

    id: str
    path: str
    score: float


@dataclass(frozen=True)
class WitnessUpdate:
    """见证锚定更新（S-11 外部校准端口写路径）。"""

    narrative_coherence_score: float | None = None
    overridden_by_external: bool | None = None


@dataclass(frozen=True)
class UsageDelta:
    """使用事件增量（影子副本更新）。"""

    usage_count: int = 1
    activation_weight: float = 0.0


class StorageBackend(ABC):
    """存储后端抽象（detailed-design §2 五方法契约）。

    业务代码仅依赖本抽象——方言差异（FTS5 vs tsvector、JSONB、
    sqlite-vec vs pgvector）收敛于各实现内部；切换后端业务无感。
    """

    @abstractmethod
    async def write(self, memory: MemoryRecord) -> str:
        """写入记忆，返回记忆 id（含双副本初始化）。"""

    @abstractmethod
    async def path_retrieve(self, prefix: str, limit: int = 10) -> list[MemoryRecord]:
        """路径前缀检索（B-tree 前缀索引）。"""

    @abstractmethod
    async def vector_search(
        self, query_vector: list[float], top_k: int = 100
    ) -> list[ScoredMemory]:
        """向量相似度检索（语义信号候选池）。"""

    @abstractmethod
    async def update_witness(self, memory_id: str, witness: WitnessUpdate) -> None:
        """更新见证锚定主副本（S-14：仅外部校准可写）。"""

    @abstractmethod
    async def update_usage(self, memory_id: str, delta: UsageDelta) -> None:
        """更新使用权重影子副本（S-14：永不写回主副本）。"""


class SQLiteBackend(StorageBackend):
    """SQLite 后端（竖切当前形态）——委托现有存储组件实现五方法契约。

    薄适配：不重构业务组件（MemoryStore/DualCopyManager/VectorIndex 保持
    现有实现），本类作为存储门面满足抽象契约；PG 适配时新增 PostgresBackend。
    """

    def __init__(
        self, db: Database, store: Any = None, copies: Any = None, vectors: Any = None
    ) -> None:
        self.db = db
        self._store = store  # MemoryStore（write/path_retrieve 委托）
        self._copies = copies  # DualCopyManager（witness/usage 委托）
        self._vectors = vectors  # VectorIndex（vector_search 委托）

    async def write(self, memory: MemoryRecord) -> str:
        from src.storage.memory_store import MemoryWriteInput

        result = await self._store.create(
            MemoryWriteInput(
                path=memory.path,
                content=memory.content,
                provenance=memory.metadata.get("provenance", "system_generated"),
                contract=memory.contract,
            )
        )
        return str(result.id)

    async def path_retrieve(self, prefix: str, limit: int = 10) -> list[MemoryRecord]:
        items, _total = await self._store.list(path_prefix=prefix, limit=limit)
        return [
            MemoryRecord(
                id=i["id"],
                path=i["path"],
                version=i["version"],
                content=i["content"],
                contract=i["contract"],
            )
            for i in items
        ]

    async def vector_search(
        self, query_vector: list[float], top_k: int = 100
    ) -> list[ScoredMemory]:
        hits = await self._vectors.cosine_search(query_vector, top_k=top_k)
        return [
            ScoredMemory(id=str(h["id"]), path=str(h["path"]), score=float(h["score"]))
            for h in hits
        ]

    async def update_witness(self, memory_id: str, witness: WitnessUpdate) -> None:
        await self._copies.update_witness(
            memory_id,
            narrative_coherence_score=witness.narrative_coherence_score,
            overridden_by_external=witness.overridden_by_external,
        )

    async def update_usage(self, memory_id: str, delta: UsageDelta) -> None:
        from src.storage.dual_copy import UsageDelta as DualUsageDelta

        await self._copies.update_usage(
            memory_id,
            DualUsageDelta(
                usage_count=delta.usage_count, activation_weight=delta.activation_weight
            ),
        )


class MockPGBackend(StorageBackend):
    """Mock PostgreSQL 后端（接口可替换性验证，acceptance-criteria 判据）。

    内存实现——模拟 PG 方言（pgvector/tsvector 语义），验证业务层对
    抽象契约的依赖不绑定 SQLite 方言；仅用于接口可替换性单测，非真实 PG。
    """

    def __init__(self) -> None:
        self._memories: dict[str, MemoryRecord] = {}
        self._witness: dict[str, float] = {}
        self._usage: dict[str, int] = {}

    async def write(self, memory: MemoryRecord) -> str:
        self._memories[memory.id] = memory
        return memory.id

    async def path_retrieve(self, prefix: str, limit: int = 10) -> list[MemoryRecord]:
        hits = [m for m in self._memories.values() if m.path.startswith(prefix)]
        return hits[:limit]

    async def vector_search(
        self, query_vector: list[float], top_k: int = 100
    ) -> list[ScoredMemory]:
        # Mock 语义：按路径包含 query 首维符号近似（仅契约验证，非真实检索）
        return [
            ScoredMemory(id=m.id, path=m.path, score=0.5)
            for m in list(self._memories.values())[:top_k]
        ]

    async def update_witness(self, memory_id: str, witness: WitnessUpdate) -> None:
        if witness.narrative_coherence_score is not None:
            self._witness[memory_id] = witness.narrative_coherence_score

    async def update_usage(self, memory_id: str, delta: UsageDelta) -> None:
        self._usage[memory_id] = self._usage.get(memory_id, 0) + delta.usage_count
