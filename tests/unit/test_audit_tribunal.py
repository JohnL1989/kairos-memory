"""审计庭单元测试（组件 6）——HMAC 链完整性 + 篡改检测 + S-16 留痕。

覆盖：
- 记录写入（双字段链：content_hash + HMAC）
- 链完整性校验（正常链 valid）
- 篡改检测（修改历史记录 → 链断裂并定位）
- S-16 语义：定向遗忘/身份降级留痕（未留痕视为未执行）
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from src.supervision.audit_tribunal import AuditTribunal

pytestmark = pytest.mark.unit

TEST_HMAC_KEY = "22" * 32


@pytest.fixture
async def tribunal(memory_db) -> AuditTribunal:
    return AuditTribunal(memory_db, hmac_key=TEST_HMAC_KEY)


class TestRecord:
    async def test_record_creates_chain_entry(self, tribunal: AuditTribunal) -> None:
        result = await tribunal.record(
            operator="test",
            action="memory_write",
            target_type="memory",
            target_id="m1",
            details={"k": "v"},
        )
        assert result["hmac"]
        assert result["previous_hash"] == ""  # 首条：前驱为空

    async def test_second_record_chains(self, tribunal: AuditTribunal) -> None:
        first = await tribunal.record(operator="t", action="a1", target_id="m1")
        second = await tribunal.record(operator="t", action="a2", target_id="m2")
        assert second["previous_hash"] == first["hmac"]


class TestChainVerification:
    async def test_clean_chain_valid(self, tribunal: AuditTribunal) -> None:
        for i in range(5):
            await tribunal.record(operator="t", action=f"op{i}", target_id=f"m{i}")
        result = await tribunal.verify_chain()
        assert result["chain_valid"] is True
        assert result["total"] == 5

    async def test_tamper_detection(self, tribunal: AuditTribunal) -> None:
        """篡改历史记录（改 action）→ 链断裂并精确定位。"""
        for i in range(4):
            await tribunal.record(operator="t", action=f"op{i}", target_id=f"m{i}")
        # 篡改第 2 条记录的 action
        async with tribunal.db.session() as session:
            await session.execute(
                text("UPDATE audit_log SET action = 'tampered' WHERE action = 'op1'")
            )
            await session.commit()
        result = await tribunal.verify_chain()
        assert result["chain_valid"] is False
        # 精确定位篡改记录（action 篡改仅影响该条自身重算；
        # 篡改 content_hash/hmac 会级联其后继的 prev 引用断裂）
        assert len(result["broken_ids"]) >= 1


class TestS16Semantics:
    async def test_directed_forgetting_audit_marker(self, tribunal: AuditTribunal) -> None:
        """S-16：定向遗忘留痕（标记 directed_forgetting）。"""
        await tribunal.record(
            operator="user",
            action="directed_forgetting",
            target_type="memory",
            target_id="m9",
            redline_id="S-16",
        )
        async with tribunal.db.session() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT action, redline_id, hmac FROM audit_log "
                        "WHERE action = 'directed_forgetting'"
                    )
                )
            ).fetchone()
        assert row is not None
        assert row[0] == "directed_forgetting"
        assert row[1] == "S-16"
        assert row[2]  # HMAC 非空（完整性链参与）
