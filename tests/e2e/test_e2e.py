"""竖切 E2E 测试（7/9 条：E2E-01/02/04/05/06/07/08）。

口径（test-plan §2 注记）：E2E-03 升华、E2E-09 S-14 不在竖切范围——
S-14 由单测覆盖（test_dual_copy.py）。

覆盖：
- E2E-01：写入→检索全链路
- E2E-02：写入→遗忘→复兴
- E2E-04：校准→降级→恢复
- E2E-05：降级模式切换
- E2E-06：写入→修改→删除→审计链验证
- E2E-07：冷启动（迁移→健康检查）
- E2E-08：审计 HMAC 链篡改检测
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from litestar.testing import AsyncTestClient

from src.access.server import create_app
from src.app import build_app
from src.storage.forgetting import ForgettingScheduler
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.models import Memory, utc_now

pytestmark = pytest.mark.e2e

HMAC_KEY = "22" * 32


def _settings():
    return type(
        "S",
        (),
        {
            "get": lambda self, k, d=None: {
                "KAIROS_AUDIT_HMAC_KEY": HMAC_KEY,
                "KAIROS_FORGETTING_HALF_LIFE": 69,
                "KAIROS_FRESHNESS_ACTIVE_THRESHOLD": 0.3,
                "KAIROS_FRESHNESS_STALE_THRESHOLD": 0.1,
                "KAIROS_DEGRADATION_PERIOD_N": 50,
                "KAIROS_DEGRADATION_PERIOD_M": 200,
                "KAIROS_HOST": "127.0.0.1",
                "KAIROS_PORT": 8010,
            }.get(k, d),
        },
    )()


@pytest.fixture
async def app_client(memory_db):
    kairos = build_app(_settings(), db=memory_db)
    app = create_app(kairos)
    async with AsyncTestClient(app) as c:
        yield c, kairos
    await kairos.close()


async def _write(store: MemoryStore, content: str, **kw) -> str:
    result = await store.create(
        MemoryWriteInput(
            path="kairos://_user/e2e/memories/",
            content=content,
            provenance="user_input",
            **kw,
        )
    )
    return result.id


async def _age(store: MemoryStore, memory_id: str, days: float) -> None:
    past = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    async with store.db.session() as session:
        memory = await session.get(Memory, memory_id)
        assert memory is not None
        memory.last_access_at = past
        await session.commit()


class TestE2E01WriteRetrieve:
    async def test_write_search_flow(self, app_client) -> None:
        """E2E-01：写入→检索。"""
        client, kairos = app_client
        resp = await client.post(
            "/v1/memories",
            json={
                "path": "kairos://_user/e2e/memories/",
                "content": "E2E 写入检索全链路测试内容，长度足够。",
                "provenance": "user_input",
            },
        )
        assert resp.status_code in (200, 201)
        memory_id = resp.json()["id"]
        # 读取
        got = await client.get(f"/v1/memories/{memory_id}")
        assert got.status_code == 200
        # 检索
        searched = await client.post(
            "/v1/memories/search", json={"query": "E2E 写入检索", "limit": 5}
        )
        assert searched.status_code == 200
        assert any(d["id"] == memory_id for d in searched.json()["data"])


class TestE2E02ForgetRevive:
    async def test_write_forget_revive_flow(self, app_client) -> None:
        """E2E-02：写入→遗忘→复兴。"""
        _client, kairos = app_client
        store = kairos.store
        scheduler = ForgettingScheduler(kairos.db)
        mid = await _write(store, "E2E 遗忘复兴测试记忆内容，长度足够用于测试。")
        await _age(store, mid, 400)
        await scheduler.scan()  # 遗忘：archived
        async with kairos.db.session() as session:
            memory = await session.get(Memory, mid)
            assert memory is not None and memory.status == "archived"
        await scheduler.revive(mid)  # 复兴：active
        async with kairos.db.session() as session:
            memory = await session.get(Memory, mid)
            assert memory is not None and memory.status == "active"


class TestE2E04CalibrateDegrade:
    async def test_calibrate_degrade_recover(self, app_client) -> None:
        """E2E-04：校准→降级→恢复。"""
        _client, kairos = app_client
        store = kairos.store
        mid = await _write(store, "E2E 校准降级测试记忆内容，长度足够用于测试。")
        # 校准（S-11 外部校准端口）
        cal = await kairos.calibration.calibrate(
            memory_id=mid, narrative_coherence_score=0.85, source="e2e"
        )
        assert cal["status"] == "accepted"
        # 降级（校准时延驱动：长中断 → 安全休眠）
        past = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        mode = await kairos.degradation.tick(last_calibration_at=past)
        assert mode in ("conservative_silent", "safe_hibernation")
        # 恢复（最近校准 → 正常态）
        mode2 = await kairos.degradation.tick(last_calibration_at=utc_now())
        assert mode2 == "normal"


class TestE2E05DegradationSwitch:
    async def test_degradation_switch_via_api(self, app_client) -> None:
        """E2E-05：降级模式切换（API）。"""
        client, _kairos = app_client
        resp = await client.post("/v1/degradation/switch", json={"mode": "conservative_silent"})
        assert resp.status_code == 200
        assert resp.json()["mode"] == "conservative_silent"
        resp2 = await client.post("/v1/degradation/switch", json={"mode": "normal"})
        assert resp2.status_code == 200


class TestE2E06AuditChain:
    async def test_write_update_delete_audit(self, app_client) -> None:
        """E2E-06：写入→修改→删除→审计链验证。"""
        client, kairos = app_client
        created = (
            await client.post(
                "/v1/memories",
                json={
                    "path": "kairos://_user/e2e/memories/",
                    "content": "E2E 审计链测试记忆内容，长度足够用于测试。",
                    "provenance": "user_input",
                },
            )
        ).json()
        # 修改（If-Match 乐观锁）
        updated = await client.patch(
            f"/v1/memories/{created['id']}",
            json={"content": "E2E 审计链更新后内容，长度足够用于测试。"},
            headers={"If-Match": "1"},
        )
        assert updated.status_code == 200
        # 校准（产生审计记录）
        await client.post(
            "/v1/calibrate",
            json={"memory_id": created["id"], "narrative_coherence_score": 0.7, "source": "e2e"},
        )
        # 删除（软删除）
        deleted = await client.delete(f"/v1/memories/{created['id']}")
        assert deleted.status_code == 200
        # 审计链验证（HMAC 完整性）
        audit = await client.get("/v1/audit-log")
        assert audit.status_code == 200
        body = audit.json()
        assert body["chain_valid"] is True
        assert body["total"] >= 1
        assert any(e["action"] == "external_calibration" for e in body["logs"])


class TestE2E07ColdStart:
    async def test_cold_start_migrate_health(self, tmp_path) -> None:
        """E2E-07：冷启动（迁移→健康检查）。"""
        from src.storage.db import Database

        db = Database(f"sqlite:///{tmp_path / 'cold.db'}")
        await db.run_migrations()
        await db.verify_schema()
        kairos = build_app(_settings(), db=db)
        app = create_app(kairos)
        async with AsyncTestClient(app) as c:
            health = await c.get("/health")
            assert health.status_code == 200
            assert health.json()["status"] == "ok"
        await kairos.close()


class TestE2E08TamperDetection:
    async def test_audit_tamper_via_api(self, app_client) -> None:
        """E2E-08：审计 HMAC 链篡改检测（API 层）。"""
        client, kairos = app_client
        created = (
            await client.post(
                "/v1/memories",
                json={
                    "path": "kairos://_user/e2e/memories/",
                    "content": "E2E 篡改检测测试记忆内容，长度足够用于测试。",
                    "provenance": "user_input",
                },
            )
        ).json()
        await client.post(
            "/v1/calibrate",
            json={"memory_id": created["id"], "narrative_coherence_score": 0.9, "source": "e2e"},
        )
        # 篡改审计记录（直接改库）
        from sqlalchemy import text

        async with kairos.db.session() as session:
            await session.execute(
                text(
                    "UPDATE audit_log SET action = 'tampered' WHERE action = 'external_calibration'"
                )
            )
            await session.commit()
        audit = await client.get("/v1/audit-log")
        assert audit.json()["chain_valid"] is False  # 篡改被检测
