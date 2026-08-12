"""Kairos 应用组装（竖切 v0.1.0-slice 依赖容器）。

将各层组件装配为可运行应用：配置 → 数据库 → 存储层（CRUD/路径/检索/
遗忘/身份）→ 事件总线 → 监督平面（审计庭）→ 宪法主权面（校准/降级/冻结）。

竖切命名配置集（架构 §0.8 kairos-slice）：
MULTI_SIGNAL_SEARCH ON + NARRATIVE_IDENTITY ON + FORGETTING_ENGINE ON，
其余 OFF——本组装即该配置集。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.config import Settings
from src.events.bus import EventBus
from src.storage.db import Database
from src.storage.dual_copy import DualCopyManager
from src.storage.forgetting import ForgettingScheduler
from src.storage.hybrid_search import HybridSearch
from src.storage.identity_registry import IdentityRegistry, VetoAdjudicator
from src.storage.memory_store import MemoryStore
from src.storage.path_index import PathIndex
from src.supervision.audit_tribunal import AuditTribunal
from src.utils.embeddings import HashEmbedder

if TYPE_CHECKING:
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

    async def close(self) -> None:
        await self.db.close()


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

    # 存储层
    store = MemoryStore(db, embedder=embedder)
    path_index = PathIndex(db)
    dual_copy = DualCopyManager(db)
    search = HybridSearch(db, embedder=embedder)
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

    # 组装容器（主权面组件为正式字段，供 API/CLI 类型安全访问）
    return KairosApp(
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


def _load_settings() -> Settings:
    from src.config import load_settings

    return load_settings()
