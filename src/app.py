"""Kairos 应用组装（竖切 v0.1.0-slice 依赖容器）。

将各层组件装配为可运行应用：配置 → 数据库 → 存储层（CRUD/路径/检索/
遗忘/身份）→ 事件总线 → 监督平面（审计庭）→ 宪法主权面（校准/降级/冻结）。

竖切命名配置集（架构 §0.8 kairos-slice）：
MULTI_SIGNAL_SEARCH ON + NARRATIVE_IDENTITY ON + FORGETTING_ENGINE ON，
其余 OFF——本组装即该配置集。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from src.config import Settings
from src.events.bus import EventBus
from src.storage.db import Database
from src.storage.dual_copy import DualCopyManager
from src.storage.forgetting import ForgettingScheduler
from src.storage.hybrid_search import HybridSearch
from src.storage.identity_registry import IdentityRegistry, VetoAdjudicator
from src.storage.memory_store import MemoryStore, MemoryWriteInput
from src.storage.path_index import PathIndex
from src.supervision.audit_tribunal import AuditTribunal
from src.utils.embeddings import HashEmbedder

if TYPE_CHECKING:
    from src.scheduler import KairosScheduler
    from src.sovereignty.calibration import CalibrationPort
    from src.sovereignty.degradation import DegradationStateMachine
    from src.sovereignty.freeze import FreezePort


@dataclass
class KairosApp:
    """竖切应用容器（各组件共享 db 与事件总线）。"""

    settings: Settings
    db: Database
    bus: EventBus
    tribunal: AuditTribunal
    store: MemoryStore
    path_index: PathIndex
    dual_copy: DualCopyManager
    search: HybridSearch
    forgetting: ForgettingScheduler
    identity: IdentityRegistry
    veto: VetoAdjudicator
    calibration: CalibrationPort
    degradation: DegradationStateMachine
    freeze: FreezePort
    scheduler: KairosScheduler | None = None

    async def close(self) -> None:
        if self.scheduler is not None:
            await self.scheduler.shutdown()
        await self.db.close()

    async def seed_bootstrap(
        self, *, path: str, seed_type: str, content: dict[str, Any], confidence: float
    ) -> dict[str, Any]:
        """种子冷启动锚点（组件 5 激活：slice-guide 组件 5 / 架构 §5.2）。

        Seed 落库（seeds 表，seed_type 枚举 config/identity/calibration）；
        seed_type=identity 时联动创建身份记忆（见证锚定写入 + 初始赋予
        grant_initial_identity + S-16 审计 identity_initial_grant）——
        此前 seeds 端点仅落库不建身份记忆，身份注册表（S-10 见证豁免）
        处于在位未启用状态。

        routes (POST /v1/seeds) 与 CLI (kairos seed add) 统一复用。
        """
        from uuid import uuid4

        from src.storage.models import Seed

        async with self.db.session() as session:
            exists = (
                await session.execute(select(Seed).where(Seed.path == path))
            ).scalar_one_or_none()
            if exists is not None:
                from src.errors import VersionConflictError

                raise VersionConflictError(f"种子路径已存在: {path}")

        # 冷启动锚点：content dict → 可读文本 → 见证锚定写入 → 初始赋予
        # （identity 类型先建记忆后落库 Seed——记忆门禁失败不留孤儿种子）
        identity_memory: dict[str, Any] | None = None
        if seed_type == "identity":
            text = (
                "；".join(f"{k}: {v}" for k, v in content.items())
                if isinstance(content, dict)
                else str(content)
            )
            created = await self.store.create(
                MemoryWriteInput(
                    path=path,
                    content=text,
                    provenance="system_generated",  # S-15：种子为系统冷启动锚点
                )
            )
            grant = await self.identity.grant_initial_identity(created.id, confidence=confidence)
            identity_memory = {
                "memory_id": created.id,
                "is_identity": grant["is_identity"],
                "identity_confidence": grant["identity_confidence"],
            }

        async with self.db.session() as session:
            seed = Seed(
                id=str(uuid4()),
                path=path,
                seed_type=seed_type,
                initial_confidence=confidence,
                current_confidence=confidence,
                content_snapshot=json.dumps(content, ensure_ascii=False),
            )
            session.add(seed)
            await session.commit()

        result: dict[str, Any] = {
            "seed": {
                "path": seed.path,
                "seed_type": seed.seed_type,
                "status": seed.status,
                "degradation_level": seed.degradation_level,
                "initial_confidence": seed.initial_confidence,
                "current_confidence": seed.current_confidence,
                "review_count": seed.review_count,
            }
        }
        if identity_memory is not None:
            result["identity_memory"] = identity_memory
        return result


def build_app(settings: Settings | None = None, *, db: Database | None = None) -> KairosApp:
    """组装竖切应用（默认装配 kairos-slice 配置集）。

    db 可注入（测试用临时库）；未注入时按 settings 创建。
    """
    from src.sovereignty.calibration import CalibrationPort
    from src.sovereignty.degradation import DegradationStateMachine
    from src.sovereignty.freeze import FreezePort

    settings = settings or _load_settings()
    db = db or Database(settings.get("KAIROS_DB_URL"))

    # 监督平面（S-01 必填密钥由配置校验保证）
    tribunal = AuditTribunal(db, hmac_key=settings.get("KAIROS_AUDIT_HMAC_KEY"))

    # 横切基础设施
    bus = EventBus(db)

    # 嵌入（竖切开发默认 HashEmbedder；BGE-M3 接入点见 utils.embeddings）
    embedder = HashEmbedder()

    # 存储层（bus 注入：use_event 发布）
    store = MemoryStore(db, embedder=embedder, bus=bus)
    path_index = PathIndex(db)
    dual_copy = DualCopyManager(db)
    # QueryAnalyzer（首迭代增强：意图分类 + 时间锚定，注入检索管线）
    from src.storage.query_analyzer import QueryAnalyzer

    search = HybridSearch(db, embedder=embedder, bus=bus, analyzer=QueryAnalyzer(db))
    # 事件订阅者注册（use_event → 影子副本更新，首迭代接线）
    from src.events.subscribers import UsageEventSubscriber

    bus.subscribe("use_event", UsageEventSubscriber(db).handle)
    forgetting = ForgettingScheduler(
        db,
        half_life=settings.get("KAIROS_FORGETTING_HALF_LIFE"),
        active_threshold=settings.get("KAIROS_FRESHNESS_ACTIVE_THRESHOLD"),
        stale_threshold=settings.get("KAIROS_FRESHNESS_STALE_THRESHOLD"),
    )
    identity = IdentityRegistry(db, tribunal=tribunal)
    veto = VetoAdjudicator()

    # 宪法主权面（bus 注入：校准/降级事件发布）
    calibration = CalibrationPort(db, tribunal, bus=bus)
    degradation = DegradationStateMachine(
        db,
        period_n=settings.get("KAIROS_DEGRADATION_PERIOD_N"),
        period_m=settings.get("KAIROS_DEGRADATION_PERIOD_M"),
        bus=bus,
    )
    freeze = FreezePort(db, tribunal)
    # CAL-03 冻结守卫接入存储层写路径（冻结期间所有写操作拒绝）
    store.freeze_guard = freeze.guard

    # 调度器（APScheduler 空闲驱动；kairos serve 启动时 start）
    from src.scheduler import KairosScheduler

    app = KairosApp(
        settings=settings,
        db=db,
        bus=bus,
        tribunal=tribunal,
        store=store,
        path_index=path_index,
        dual_copy=dual_copy,
        search=search,
        forgetting=forgetting,
        identity=identity,
        veto=veto,
        calibration=calibration,
        degradation=degradation,
        freeze=freeze,
    )
    app.scheduler = KairosScheduler(app)
    return app


def _load_settings() -> Settings:
    from src.config import load_settings

    return load_settings()
