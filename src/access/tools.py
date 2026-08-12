"""Agent Tool 层（api-spec §2 五个工具）——implementation-map 落点。

工具清单（api-spec §2）：
- memories_write         记忆写入（S-15 provenance 必填；contract 五值枚举）
- memories_search        三信号混合检索（query/path/limit）
- path_browse            路径空间浏览（path/depth）
- memories_list_recent   最近使用记忆列表（limit）
- memories_merge         语义合并（source_ids/strategy，S-14 约束）

工具语义对齐 api-spec §2 参数定义；错误码经 KairosError 体系映射
（422 缺 provenance / 413 超长 / 429 限流等由存储层校验承载）。
"""

from __future__ import annotations

from typing import Any

from src.app import KairosApp
from src.storage.memory_store import MemoryWriteInput


class AgentTools:
    """Agent Tool 层（经 KairosApp 组装调用存储/检索组件）。"""

    def __init__(self, app: KairosApp) -> None:
        self.app = app

    # ------------------------------------------------------------------
    # memories_write（api-spec §2 Tool: memories_write）
    # ------------------------------------------------------------------

    async def memories_write(
        self,
        path: str,
        content: str,
        provenance: str,
        *,
        contract: str = "ondemand",
        memory_types: list[str] | None = None,
        vad: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """记忆写入（S-15 provenance 必填，缺失 422）。"""
        result = await self.app.store.create(
            MemoryWriteInput(
                path=path,
                content=content,
                provenance=provenance,
                contract=contract,
                memory_types=memory_types or ["semantic"],
                vad=vad,
            )
        )
        return {"id": result.id, "path": result.path, "version": result.version}

    # ------------------------------------------------------------------
    # memories_search（api-spec §2 Tool: memories_search）
    # ------------------------------------------------------------------

    async def memories_search(
        self,
        query: str,
        *,
        path: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """三信号混合检索（默认 limit 5，api-spec §2）。"""
        from src.storage.hybrid_search import SearchFilter

        result = await self.app.search.search(
            query,
            limit=limit,
            filters=SearchFilter(path_prefix=path) if path else None,
        )
        return {
            "results": [
                {"id": d["id"], "path": d["path"], "score": d["score"]} for d in result["data"]
            ],
            "total": result["total"],
        }

    # ------------------------------------------------------------------
    # path_browse（api-spec §2 Tool: path_browse）
    # ------------------------------------------------------------------

    async def path_browse(self, path: str = "kairos://", depth: int = 2) -> dict[str, Any]:
        """路径空间浏览（默认根，depth 2；截断标记）。"""
        root = await self.app.path_index.tree(path, depth=depth)
        nodes: list[dict[str, Any]] = []

        def _flatten(node: Any, level: int) -> None:
            nodes.append(
                {
                    "path": node.path,
                    "children": len(node.children),
                    "memory_count": node.memory_count,
                }
            )
            if level < depth:
                for child in node.children:
                    _flatten(child, level + 1)

        _flatten(root, 0)
        return {"nodes": nodes, "truncated": len(nodes) > 50}

    # ------------------------------------------------------------------
    # memories_list_recent（api-spec §2 Tool: memories_list_recent）
    # ------------------------------------------------------------------

    async def memories_list_recent(self, limit: int = 10) -> dict[str, Any]:
        """最近使用记忆（影子副本 last_used_at 降序；无使用记录按创建时间）。"""
        async with self.app.db.session() as session:
            from sqlalchemy import text

            rows = (
                await session.execute(
                    text(
                        "SELECT m.id, m.content, m.created_at FROM memories m "
                        "LEFT JOIN usage_weight u ON u.memory_id = m.id "
                        "WHERE m.is_deleted = 0 AND m.is_latest = 1 "
                        "ORDER BY COALESCE(u.last_used_at, m.created_at) DESC LIMIT :lim"
                    ),
                    {"lim": max(1, min(limit, 100))},
                )
            ).fetchall()
        return {
            "items": [
                {"id": r[0], "content": (r[1] or "")[:200], "created_at": r[2]} for r in rows
            ],
            "total": len(rows),
        }

    # ------------------------------------------------------------------
    # memories_merge（api-spec §2 Tool: memories_merge）
    # ------------------------------------------------------------------

    async def memories_merge(
        self, source_ids: list[str], strategy: str = "semantic_overlay"
    ) -> dict[str, Any]:
        """语义合并（保留见证锚定，受 S-14 约束）。

        竖切内实现：合并 = 新建记忆（内容拼接 + 来源标记）+ 源记忆软删除
        （保留审计痕迹）。完整语义合并（见证锚定保留）随升华/再巩固组件接入。
        """
        from src.errors import MissingFieldError

        if not source_ids:
            raise MissingFieldError("source_ids 不能为空（api-spec §2 memories_merge）")
        if strategy not in ("semantic_overlay", "chronological_append"):
            raise MissingFieldError(f"非法合并策略: {strategy}")

        contents: list[str] = []
        paths: list[str] = []
        for source_id in source_ids:
            detail = await self.app.store.get(source_id)
            contents.append(detail["content"])
            paths.append(detail["path"])

        separator = "\n\n" if strategy == "semantic_overlay" else "\n"
        merged_content = separator.join(contents)
        created = await self.app.store.create(
            MemoryWriteInput(
                path=paths[0].rsplit("/", 1)[0] + "/",
                content=f"[merged:{strategy}] {merged_content}",
                provenance="system_generated",
            )
        )
        # 源记忆软删除（S-16 审计由 store.delete 契约分支承载）
        for source_id in source_ids:
            await self.app.store.delete(source_id)
        return {
            "merged_id": created.id,
            "sources": source_ids,
            "status": "merged",
        }
