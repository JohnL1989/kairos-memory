"""路径空间索引（竖切组件 2）——kairos:// 前缀索引与树状浏览。

权威规格：架构 §5.2 路径空间（B-tree 前缀索引，确定性第一检索手段）、
§3.4 域路由（竖切仅实现通用路径 + _user/_project/_session/_scratch/_system 前缀约束）。

路径隔离声明（架构 §8）：路径边界是不可逾越的逻辑隔离——跨路径污染率 0%。
路径隔离 ≠ S-04（S-04 为本地回环绑定红线，两者勿混用）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select

from src.storage.db import Database
from src.storage.models import Memory

# 域前缀约束（架构 §3.4 竖切范围：通用路径 + 五个保留前缀）
RESERVED_PREFIXES = ("_user", "_project", "_session", "_scratch", "_system")


@dataclass(frozen=True)
class PathNode:
    """路径树节点。"""

    path: str
    memory_count: int
    children: tuple[PathNode, ...] = ()


class PathIndex:
    """路径空间索引（基于 memories.path B-tree 前缀索引 idx_memories_path）。"""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 路径下记忆列表（GET /v1/path）
    # ------------------------------------------------------------------

    async def list_path(
        self,
        path: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """路径下记忆列表（排除软删除与失效版本）。"""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        prefix = path if path.endswith("/") else path + "/"
        async with self.db.session() as session:
            where = [Memory.is_deleted == 0, Memory.is_latest == 1]
            # 路径前缀匹配：GLOB 前缀（大小写敏感，可走 B-tree 索引
            # idx_memories_path——SQLite 的 LIKE 大小写不敏感不可用索引）
            where.append(Memory.path.op("GLOB")(f"{prefix}*"))
            total = (
                await session.execute(select(func.count(Memory.id)).where(*where))
            ).scalar_one()
            rows = (
                await session.execute(
                    select(Memory)
                    .where(*where)
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).scalars()
            items = [
                {
                    "id": m.id,
                    "path": m.path,
                    "content": m.content,
                    "contract": m.contract,
                    "created_at": m.created_at,
                    "status": m.status,
                }
                for m in rows
            ]
            return items, total

    # ------------------------------------------------------------------
    # 树状浏览（GET /v1/path/tree）
    # ------------------------------------------------------------------

    async def tree(self, path: str, *, depth: int = 2) -> PathNode:
        """路径空间树状浏览（递归聚合子路径记忆数）。

        depth：递归深度上限（api-spec §1.6 path_browse Tool depth 默认 2）。
        """
        depth = max(1, min(depth, 10))
        prefix = path if path.endswith("/") else path + "/"
        root = await self._build_node(prefix, 0, depth)
        return root

    async def _build_node(self, prefix: str, level: int, max_depth: int) -> PathNode:
        async with self.db.session() as session:
            # 直接子路径（下一层路径段）
            child_prefixes = (
                (
                    await session.execute(
                        select(Memory.path)
                        .where(
                            Memory.is_deleted == 0,
                            Memory.is_latest == 1,
                            Memory.path.op("GLOB")(f"{prefix}*"),
                        )
                        .distinct()
                    )
                )
                .scalars()
                .all()
            )
            # 自身路径下的记忆数（当前层直接挂载，非子层）
            count_rows = (
                await session.execute(
                    select(func.count(Memory.id)).where(
                        Memory.is_deleted == 0,
                        Memory.is_latest == 1,
                        Memory.path.op("GLOB")(f"{prefix}*"),
                    )
                )
            ).scalar_one()

        # 聚合下一层段
        next_segments: set[str] = set()
        for p in child_prefixes:
            rest = p[len(prefix) :]
            if "/" in rest:
                next_segments.add(rest.split("/", 1)[0] + "/")
        children: list[PathNode] = []
        if level < max_depth:
            for seg in sorted(next_segments):
                child_prefix = prefix + seg
                children.append(await self._build_node(child_prefix, level + 1, max_depth))
        return PathNode(path=prefix, memory_count=int(count_rows), children=tuple(children))

    # ------------------------------------------------------------------
    # 路径隔离校验（跨路径污染率 0%，架构 §8 路径隔离声明）
    # ------------------------------------------------------------------

    async def verify_isolation(self, boundary_a: str, boundary_b: str) -> dict[str, Any]:
        """验证两个路径边界互不可见（跨路径污染率 0%）。

        判据：boundary_a 前缀下的记忆集合与 boundary_b 前缀下的集合交集为空。
        """
        async with self.db.session() as session:
            a_rows = (
                (
                    await session.execute(
                        select(Memory.id).where(
                            Memory.is_deleted == 0,
                            Memory.is_latest == 1,
                            Memory.path.like(f"{boundary_a}%"),
                        )
                    )
                )
                .scalars()
                .all()
            )
            b_rows = (
                (
                    await session.execute(
                        select(Memory.id).where(
                            Memory.is_deleted == 0,
                            Memory.is_latest == 1,
                            Memory.path.like(f"{boundary_b}%"),
                        )
                    )
                )
                .scalars()
                .all()
            )
        overlap = set(a_rows) & set(b_rows)
        return {
            "boundary_a": boundary_a,
            "boundary_b": boundary_b,
            "count_a": len(a_rows),
            "count_b": len(b_rows),
            "overlap": len(overlap),
            "pollution_rate": len(overlap) / max(1, len(a_rows) + len(b_rows)),
        }

    # ------------------------------------------------------------------
    # 域前缀约束（架构 §3.4）
    # ------------------------------------------------------------------

    @staticmethod
    def validate_domain(path: str) -> None:
        """路径域段必须是五个保留前缀之一（竖切域路由约束，架构 §3.4）。

        路径形如 kairos://_user/{id}/...——split('/') 后首段为协议 kairos:，
        域段为第二段。
        """
        from src.errors import InvalidPathError

        segments = [s for s in path.split("/") if s]
        if (
            len(segments) >= 2
            and segments[1].startswith("_")
            and segments[1] not in RESERVED_PREFIXES
        ):
            raise InvalidPathError(f"未知保留前缀: {segments[1]!r}")
