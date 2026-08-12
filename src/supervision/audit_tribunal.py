"""审计庭（竖切组件 6 前置）——审计日志记录 + HMAC 链维护。

权威规格：
- 架构 §1.7 监督平面（审计庭：独立感知通道，不依赖检测器族预聚合）
- 架构 §10.10 审计与可追溯性（trace_id 全链路）
- threat-model HMAC 审计链：hmac = HMAC-SHA256(hmac_key, timestamp + operator +
  action + content_hash + prev_hmac)，5 项输入；details 等可变信息以 SHA256
  摘要并入 content_hash 参与链计算
- S-16：定向遗忘/身份降级等留痕标记（未留痕视为未执行）
- audit_log 表：双字段链（明文 content_hash 链 + HMAC-SHA256 完整性链）

HMAC 密钥：KAIROS_AUDIT_HMAC_KEY（必填，S-01 启动校验已保证）。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text

from src.storage.db import Database
from src.storage.models import utc_now
from src.utils.keys import hmac_sha256_hex


class AuditTribunal:
    """审计庭：审计记录（HMAC 链）+ 链完整性校验。"""

    def __init__(self, db: Database, hmac_key: str) -> None:
        self.db = db
        self.hmac_key = hmac_key

    # ------------------------------------------------------------------
    # 记录（双字段链：content_hash 明文链 + HMAC 完整性链）
    # ------------------------------------------------------------------

    async def record(
        self,
        *,
        operator: str,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict[str, Any] | None = None,
        redline_id: str | None = None,
    ) -> dict[str, Any]:
        """写入审计记录（HMAC 链追加）。

        hmac = HMAC-SHA256(hmac_key, timestamp + operator + action + content_hash + prev_hmac)
        details 的 SHA256 摘要并入 content_hash 参与链计算（threat-model 口径）。
        """
        async with self.db.session() as session:
            prev_row = (
                await session.execute(text("SELECT hmac FROM audit_log ORDER BY id DESC LIMIT 1"))
            ).fetchone()
            prev_hmac = prev_row[0] if prev_row else ""

            details_json = json.dumps(details or {}, ensure_ascii=False, sort_keys=True)
            content_hash = hashlib.sha256(
                f"{action}|{target_id or ''}|{details_json}".encode()
            ).hexdigest()
            timestamp = utc_now()
            chain_input = f"{timestamp}{operator}{action}{content_hash}{prev_hmac}".encode()
            hmac = hmac_sha256_hex(self.hmac_key, chain_input)

            row = await session.execute(
                text(
                    "INSERT INTO audit_log (timestamp, operator, action, target_type, "
                    "target_id, content_hash, previous_hash, hmac, details, redline_id) "
                    "VALUES (:ts, :op, :action, :ttype, :tid, :ch, :prev, :hmac, :details, :rid)"
                ),
                {
                    "ts": timestamp,
                    "op": operator,
                    "action": action,
                    "ttype": target_type,
                    "tid": target_id,
                    "ch": content_hash,
                    "prev": prev_hmac,
                    "hmac": hmac,
                    "details": details_json if details else None,
                    "rid": redline_id,
                },
            )
            await session.commit()
            conn = await session.connection()
            last_id = await conn.scalar(text("SELECT last_insert_rowid()"))
            return {"id": int(last_id or 0), "hmac": hmac, "previous_hash": prev_hmac}

    # ------------------------------------------------------------------
    # 链完整性校验（GET /v1/audit-log 校验 + kairos audit verify-chain）
    # ------------------------------------------------------------------

    async def verify_chain(self, limit: int | None = None) -> dict[str, Any]:
        """校验 HMAC 链完整性（逐条重算比对；支持定位篡改记录）。"""
        async with self.db.session() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT id, timestamp, operator, action, content_hash, previous_hash, hmac "
                        "FROM audit_log ORDER BY id ASC" + (f" LIMIT {int(limit)}" if limit else "")
                    )
                )
            ).fetchall()

        prev_hmac = ""
        broken: list[int] = []
        for row in rows:
            rec_id, ts, operator, action, content_hash, prev_ref, hmac = row
            if prev_ref != prev_hmac:
                broken.append(rec_id)
            chain_input = f"{ts}{operator}{action}{content_hash}{prev_hmac}".encode()
            if hmac_sha256_hex(self.hmac_key, chain_input) != hmac:
                broken.append(rec_id)
            prev_hmac = hmac

        return {
            "total": len(rows),
            "chain_valid": not broken,
            "broken_ids": broken,
        }
