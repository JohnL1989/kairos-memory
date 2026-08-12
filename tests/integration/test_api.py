"""REST API 集成测试（竖切 21 端点）——E2E-01 语义（写入→检索）。

覆盖：写入/读取/更新（乐观锁）/删除契约分支/搜索/路径/校准/审计/健康/
配置/种子端点；错误码映射（404/409/403）。
"""

from __future__ import annotations

import pytest
from litestar.testing import AsyncTestClient

from src.access.server import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
async def client(memory_db):
    """无密钥测试客户端（本地开发放行路径）。"""
    from src.app import build_app

    settings = type(
        "S",
        (),
        {
            "get": lambda self, k, d=None: {
                "KAIROS_AUDIT_HMAC_KEY": "22" * 32,
                "KAIROS_FORGETTING_HALF_LIFE": 69,
                "KAIROS_FRESHNESS_ACTIVE_THRESHOLD": 0.3,
                "KAIROS_FRESHNESS_STALE_THRESHOLD": 0.1,
                "KAIROS_DEGRADATION_PERIOD_N": 50,
                "KAIROS_DEGRADATION_PERIOD_M": 200,
                "KAIROS_HOST": "127.0.0.1",
                "KAIROS_PORT": 8010,
            }.get(k, d)
        },
    )()
    kairos = build_app(settings, db=memory_db)
    app = create_app(kairos)
    async with AsyncTestClient(app) as c:
        yield c
    await kairos.close()


def _write_payload(
    path: str = "kairos://_user/u1/memories/",
    content: str = "API 集成测试记忆内容，长度足够用于测试。",
    **kw,
) -> dict:
    return {"path": path, "content": content, "provenance": "user_input", **kw}


class TestMemoryEndpoints:
    async def test_create_and_get(self, client) -> None:
        resp = await client.post("/v1/memories", json=_write_payload())
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["id"] and body["version"] == 1
        # 读取
        resp2 = await client.get(f"/v1/memories/{body['id']}")
        assert resp2.status_code == 200
        assert resp2.json()["content"] == "API 集成测试记忆内容，长度足够用于测试。"

    async def test_create_missing_provenance_422(self, client) -> None:
        resp = await client.post("/v1/memories", json={"path": "kairos://x/", "content": "内容"})
        assert resp.status_code == 422  # S-15 来源缺失

    async def test_update_with_if_match(self, client) -> None:
        created = (await client.post("/v1/memories", json=_write_payload())).json()
        resp = await client.patch(
            f"/v1/memories/{created['id']}",
            json={"content": "更新后的内容，测试版本链，长度足够用于测试。"},
            headers={"If-Match": "1"},
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == 2

    async def test_update_version_conflict_409(self, client) -> None:
        created = (await client.post("/v1/memories", json=_write_payload())).json()
        resp = await client.patch(
            f"/v1/memories/{created['id']}", json={"content": "x" * 30}, headers={"If-Match": "99"}
        )
        assert resp.status_code == 409  # ERR-DB-005

    async def test_delete_permanent_403(self, client) -> None:
        created = (
            await client.post(
                "/v1/memories",
                json=_write_payload(
                    content="永久记忆内容，长度足够用于测试。", contract="permanent"
                ),
            )
        ).json()
        resp = await client.delete(f"/v1/memories/{created['id']}")
        assert resp.status_code == 403

    async def test_archive_and_restore(self, client) -> None:
        created = (await client.post("/v1/memories", json=_write_payload())).json()
        resp = await client.post(
            f"/v1/memories/{created['id']}/archive", json={"reason": "low_usage"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"
        # 恢复
        resp2 = await client.post(
            f"/v1/memories/{created['id']}/restore", json={"reason": "context_reemerged"}
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "active"

    async def test_archive_identity_rejected(self, client) -> None:
        """S-10：身份记忆不可归档（ERR-SEC-001）。"""
        created = (await client.post("/v1/memories", json=_write_payload())).json()
        from src.storage.models import Memory

        async with client.app.state["kairos"].db.session() as session:
            memory = await session.get(Memory, created["id"])
            assert memory is not None
            memory.is_identity = 1
            await session.commit()
        resp = await client.post(f"/v1/memories/{created['id']}/archive", json={})
        assert resp.status_code == 403


class TestSearchEndpoints:
    async def test_search_hybrid(self, client) -> None:
        await client.post(
            "/v1/memories", json=_write_payload(content="Python asyncio programming guide")
        )
        resp = await client.post(
            "/v1/memories/search", json={"query": "Python asyncio", "limit": 5}
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_search_requires_query(self, client) -> None:
        resp = await client.post("/v1/memories/search", json={})
        assert resp.status_code in (400, 422)


class TestGovernanceEndpoints:
    async def test_calibrate(self, client) -> None:
        created = (await client.post("/v1/memories", json=_write_payload())).json()
        resp = await client.post(
            "/v1/calibrate",
            json={"memory_id": created["id"], "narrative_coherence_score": 0.85, "source": "test"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    async def test_freeze_and_unfreeze(self, client) -> None:
        resp = await client.post("/v1/freeze", json={"duration_seconds": 60})
        assert resp.status_code == 200
        # 冻结期间写入拒绝
        resp2 = await client.post("/v1/memories", json=_write_payload())
        assert resp2.status_code == 403
        resp3 = await client.post("/v1/unfreeze", json={})
        assert resp3.status_code == 200

    async def test_degradation_switch(self, client) -> None:
        resp = await client.post("/v1/degradation/switch", json={"mode": "safe_hibernation"})
        assert resp.status_code == 200
        assert resp.json()["mode"] == "safe_hibernation"


class TestSystemEndpoints:
    async def test_health(self, client) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_audit_log(self, client) -> None:
        created = (await client.post("/v1/memories", json=_write_payload())).json()
        # 校准触发审计记录（S-11 external_calibration）
        await client.post(
            "/v1/calibrate",
            json={"memory_id": created["id"], "narrative_coherence_score": 0.8, "source": "test"},
        )
        resp = await client.get("/v1/audit-log")
        assert resp.status_code == 200
        body = resp.json()
        assert body["chain_valid"] is True
        assert body["total"] >= 1

    async def test_config_get(self, client) -> None:
        resp = await client.get("/v1/config")
        assert resp.status_code == 200
        assert len(resp.json()["config"]) > 0

    async def test_config_patch_unknown_key_400(self, client) -> None:
        resp = await client.patch(
            "/v1/config", json={"updates": [{"key": "KAIROS_NOPE", "value": "1"}]}
        )
        assert resp.status_code == 400

    async def test_seeds(self, client) -> None:
        resp = await client.post(
            "/v1/seeds",
            json={
                "seed_type": "identity",
                "path": "kairos://_system/seeds/identity-core",
                "initial_confidence": 0.9,
                "current_confidence": 0.9,
            },
        )
        assert resp.status_code == 200
        resp2 = await client.get("/v1/seeds")
        assert resp2.status_code == 200
        assert len(resp2.json()["seeds"]) >= 1

    async def test_404_memory(self, client) -> None:
        resp = await client.get("/v1/memories/nonexistent")
        assert resp.status_code == 404  # ERR-DB-004
