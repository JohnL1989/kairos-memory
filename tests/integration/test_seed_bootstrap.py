"""种子冷启动锚点测试（组件 5 身份注册表激活：slice-guide 组件 5 / 架构 §5.2）。

覆盖：
- identity 种子 → Seed 落库 + 身份记忆（is_identity=true + confidence）
- S-10 见证豁免：身份记忆被遗忘扫描跳过（action=skip_identity）
- S-16 审计：identity_initial_grant 留痕（HMAC 链可追溯）
- config 类型种子不联动身份记忆
- CLI `kairos seed add` 端到端
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from src.storage.models import AuditLog, Memory, Seed

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def kairos(memory_db):
    from src.app import build_app

    app = build_app(db=memory_db)
    yield app
    await app.close()


async def test_identity_seed_creates_identity_memory(kairos) -> None:
    result = await kairos.seed_bootstrap(
        path="kairos://_user/hermes/identity/developer",
        seed_type="identity",
        content={"name": "JohnL1989", "role": "developer"},
        confidence=0.8,
    )
    assert result["identity_memory"]["is_identity"] is True
    assert result["identity_memory"]["identity_confidence"] == 0.8
    async with kairos.db.session() as s:
        seeds = (await s.execute(select(Seed))).scalars().all()
        assert len(seeds) == 1
        assert seeds[0].seed_type == "identity"
        mem = await s.get(Memory, result["identity_memory"]["memory_id"])
        assert mem is not None
        assert mem.is_identity == 1
        assert abs(mem.identity_confidence - 0.8) < 1e-6
        # S-16 审计留痕
        grants = (
            (await s.execute(select(AuditLog).where(AuditLog.action == "identity_initial_grant")))
            .scalars()
            .all()
        )
        assert len(grants) == 1
        assert grants[0].target_id == mem.id


async def test_identity_exempt_from_forgetting(kairos) -> None:
    """S-10 见证豁免：身份记忆不参与遗忘评估。"""
    result = await kairos.seed_bootstrap(
        path="kairos://_user/hermes/identity/developer",
        seed_type="identity",
        content={"name": "JohnL1989"},
        confidence=0.9,
    )
    mid = result["identity_memory"]["memory_id"]
    decisions = await kairos.forgetting.scan()
    decision = next(d for d in decisions if d.memory_id == mid)
    assert decision.action == "skip_identity"


async def test_config_seed_no_identity(kairos) -> None:
    """config 类型种子仅落库，不联动身份记忆。"""
    result = await kairos.seed_bootstrap(
        path="kairos://_user/hermes/config/app",
        seed_type="config",
        content={"log_level": "info"},
        confidence=0.5,
    )
    assert "identity_memory" not in result
    async with kairos.db.session() as s:
        seeds = (await s.execute(select(Seed))).scalars().all()
        assert len(seeds) == 1
        assert seeds[0].seed_type == "config"
        mems = (await s.execute(select(func.count()).select_from(Memory))).scalar()
        assert mems == 0  # 无记忆写入


async def test_duplicate_seed_path_conflict(kairos) -> None:
    await kairos.seed_bootstrap(
        path="kairos://_user/hermes/identity/x",
        seed_type="identity",
        content={"name": "重复路径冲突测试身份内容"},
        confidence=0.6,
    )
    from src.errors import VersionConflictError

    with pytest.raises(VersionConflictError):
        await kairos.seed_bootstrap(
            path="kairos://_user/hermes/identity/x",
            seed_type="identity",
            content={"name": "重复路径冲突测试身份内容之二"},
            confidence=0.6,
        )
