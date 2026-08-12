"""事件总线全链路接线集成测试（首迭代 1）。

覆盖：
- 记忆写入 → use_event 发布 → 订阅者 → 影子副本更新（全链路）
- 检索 → use_event（retrieval 升温）
- 校准 → calibration_signal（已有）+ 降级 → degradation_switch（已有）
- trace_id 跨层可审计（4 类事件持久化可查）
"""

from __future__ import annotations

import pytest

from src.app import build_app
from src.storage.memory_store import MemoryWriteInput

pytestmark = pytest.mark.integration


def _settings():
    return type(
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
            }.get(k, d),
        },
    )()


@pytest.fixture
async def app(memory_db):
    kairos = build_app(_settings(), db=memory_db)
    yield kairos
    await kairos.close()


class TestUseEventFullChain:
    async def test_write_triggers_shadow_update(self, app) -> None:
        """写入 → use_event → 订阅者 → usage_weight 升温（全链路）。"""
        created = await app.store.create(
            MemoryWriteInput(
                path="kairos://_user/u1/memories/",
                content="事件全链路测试记忆内容，长度足够用于测试。",
                provenance="user_input",
            )
        )
        # 总线消费（写入 use_event → 影子副本）
        processed = await app.bus.drain()
        assert processed >= 1
        snap = await app.dual_copy.read_usage(created.id)
        assert snap["usage_count"] == 1  # 写入升温
        assert snap["activation_weight"] > 0

    async def test_retrieval_triggers_usage(self, app) -> None:
        """检索 → use_event（retrieval 升温）。"""
        created = await app.store.create(
            MemoryWriteInput(
                path="kairos://_user/u1/memories/",
                content="检索升温测试记忆内容，长度足够用于测试。",
                provenance="user_input",
            )
        )
        await app.bus.drain()
        await app.search.search("检索升温")
        await app.bus.drain()
        snap = await app.dual_copy.read_usage(created.id)
        assert snap["usage_count"] >= 2  # 写入 1 + 检索 1

    async def test_events_persisted_with_trace(self, app) -> None:
        """4 类事件持久化 + trace_id 可审计。"""
        created = await app.store.create(
            MemoryWriteInput(
                path="kairos://_user/u1/memories/",
                content="事件持久化测试记忆内容，长度足够用于测试。",
                provenance="user_input",
            )
        )
        # 校准（calibration_signal）
        await app.calibration.calibrate(
            memory_id=created.id, narrative_coherence_score=0.8, source="test"
        )
        # 降级切换（degradation_switch）
        await app.degradation.explicit_switch("conservative_silent")
        recent = await app.bus.recent(limit=10)
        types = {e["event_type"] for e in recent}
        assert "use_event" in types
        assert "calibration_signal" in types
        assert "degradation_switch" in types
        # trace_id 审计（校准事件链路；context 直接查表取 JSON）
        import json as _json

        from sqlalchemy import text

        async with app.db.session() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT context FROM usage_events "
                        "WHERE event_type = 'calibration_signal' ORDER BY id DESC LIMIT 1"
                    )
                )
            ).fetchone()
        assert row is not None and row[0]
        context = _json.loads(row[0])
        trace_id = context.get("trace_id", "")
        assert trace_id  # trace_id 随事件持久化
        trace = await app.bus.query_by_trace(trace_id)
        assert len(trace) >= 1  # 校准事件经 trace_id 可审计

    async def test_latent_trigger_publishable(self, app) -> None:
        """latent_trigger 可发布/订阅（4 类事件全链路验收）。"""
        received = []

        async def handler(event) -> None:
            received.append(event)

        app.bus.subscribe("latent_trigger", handler)
        await app.bus.publish(
            "latent_trigger", "metacognition", payload={"reason": "blind_spot_scan"}, priority=6
        )
        await app.bus.drain()
        assert len(received) == 1
        assert received[0].event_type == "latent_trigger"
