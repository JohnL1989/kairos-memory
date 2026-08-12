"""调度器单元测试（首迭代 2）——任务注册/空闲驱动/错误隔离/forgetAfter。

覆盖：
- 任务注册（4 项：forgetting_scan / latent_reevaluation / forget_after_scan / degradation_tick）
- 幂等 start（重复 start 不重复注册）
- 任务错误隔离（单任务失败不阻断调度循环）
- forget_after_scan：temporary 到期硬删除 + expiry_cascade_delete 审计（HMAC 链）
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.app import build_app
from src.supervision.audit_tribunal import AuditTribunal

pytestmark = pytest.mark.unit


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


class TestSchedulerLifecycle:
    async def test_jobs_registered(self, app) -> None:
        app.scheduler.start()
        try:
            jobs = app.scheduler._scheduler.get_jobs()
            ids = {j.id for j in jobs}
            assert {
                "forgetting_scan",
                "latent_reevaluation",
                "forget_after_scan",
                "degradation_tick",
            } <= ids
        finally:
            await app.scheduler.shutdown()

    async def test_start_idempotent(self, app) -> None:
        app.scheduler.start()
        first = app.scheduler._scheduler
        app.scheduler.start()  # 重复 start 不重新注册
        assert app.scheduler._scheduler is first
        await app.scheduler.shutdown()


class TestTaskErrorIsolation:
    async def test_failing_task_does_not_break_scheduler(self, app) -> None:
        """单任务异常被隔离（_run_task 捕获，不阻断调度循环）。"""
        scheduler = app.scheduler

        async def boom() -> None:
            raise RuntimeError("task bug")

        wrapper = scheduler._run_task(boom)
        await wrapper()  # 不抛异常（错误隔离）
        # 正常任务仍工作（无异常、无副作用）
        await scheduler._forget_after_scan()


class TestForgetAfterScan:
    async def test_expired_temporary_deleted(self, app) -> None:
        """temporary 到期硬删除 + 审计留痕（expiry_cascade_delete）。"""
        tribunal = AuditTribunal(app.db, hmac_key="22" * 32)
        app.forgetting.tribunal = tribunal  # 注入审计庭
        # 已到期 temporary 记忆
        past = (datetime.now(UTC) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        from sqlalchemy import text

        async with app.db.session() as session:
            await session.execute(
                text(
                    "INSERT INTO memories (id, path, version, content, content_hash, "
                    "memory_types, provenance, contract, expires_at, root_memory_id) "
                    "VALUES ('t1', 'kairos://_user/u1/memories/t1', 1, '临时记忆内容，长度足够。', "
                    "'h1', '[\"semantic\"]', 'user_input', 'temporary', :exp, 't1')"
                ),
                {"exp": past},
            )
            await session.commit()
        expired = await app.forgetting.forget_after_scan()
        assert "t1" in expired
        # 记录已删除
        from src.storage.models import Memory

        async with app.db.session() as session:
            memory = await session.get(Memory, "t1")
            assert memory is None
        # 审计留痕（HMAC 链有效）
        verify = await tribunal.verify_chain()
        assert verify["chain_valid"] is True

    async def test_unexpired_temporary_kept(self, app) -> None:
        """未到期 temporary 不清除。"""
        future = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        from sqlalchemy import text

        async with app.db.session() as session:
            await session.execute(
                text(
                    "INSERT INTO memories (id, path, version, content, content_hash, "
                    "memory_types, provenance, contract, expires_at, root_memory_id) "
                    "VALUES ('t2', 'kairos://_user/u1/memories/t2', 1, '未到期临时记忆内容。', "
                    "'h2', '[\"semantic\"]', 'user_input', 'temporary', :exp, 't2')"
                ),
                {"exp": future},
            )
            await session.commit()
        expired = await app.forgetting.forget_after_scan()
        assert "t2" not in expired
        from src.storage.models import Memory

        async with app.db.session() as session:
            assert await session.get(Memory, "t2") is not None
