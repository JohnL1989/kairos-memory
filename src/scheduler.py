"""周期性任务调度（竖切首迭代）——APScheduler 空闲驱动。

权威规格：technology-stack §一（APScheduler ≥3.10，interval trigger +
负载感知启控实现空闲驱动，ADR-006 非 cron 模式）；架构 §2.6.3
（latent_reevaluation 防抖 5 秒、forgetting_scan 10 秒）。

任务注册（竖切首迭代）：
- forgetting_scan     遗忘扫描（10s 防抖；KAIROS_FEATURE_FORGETTING_ENGINE=ON）
- latent_reevaluation 潜伏势能重估（5s 防抖）
- forget_after_scan   temporary 契约到期硬删除（KAIROS_FORGETAFTER_SCAN_INTERVAL=3600s）
- degradation_tick    降级状态机推进（KAIROS_SCHEDULER_INTERVAL=300s）

空闲驱动语义（ADR-006）：interval trigger + max_instances=1 + coalesce——
任务不重叠执行（上次未完成则跳过本次），等效「空闲时执行」。
"""

from __future__ import annotations

import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]

from src.app import KairosApp

logger = logging.getLogger("kairos.scheduler")

# 防抖间隔（架构 §2.6.3）
LATENT_REEVALUATION_INTERVAL = 5
FORGETTING_SCAN_INTERVAL = 10
# 事件队列消费间隔（use_event → 影子副本 + last_access_at 刷新；drain 确定性消费，
# 架构 §10.10 分发语义——无消费端则订阅器永不执行，闭环断裂）
BUS_DRAIN_INTERVAL = 2
# configuration 参数（KAIROS_FORGETAFTER_SCAN_INTERVAL / KAIROS_SCHEDULER_INTERVAL）
DEFAULT_FORGETAFTER_SCAN = 3600
DEFAULT_DEGRADATION_TICK = 300


class KairosScheduler:
    """竖切调度器（APScheduler AsyncIOScheduler + interval 空闲驱动）。"""

    def __init__(self, app: KairosApp) -> None:
        self.app = app
        self._scheduler: AsyncIOScheduler | None = None

    def start(self) -> None:
        """启动调度（注册任务；幂等——重复 start 不重复注册）。"""
        if self._scheduler is not None:
            return
        scheduler = AsyncIOScheduler(timezone="UTC")
        scheduler.add_job(
            self._run_task(self._forgetting_scan),
            IntervalTrigger(seconds=FORGETTING_SCAN_INTERVAL),
            id="forgetting_scan",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        scheduler.add_job(
            self._run_task(self._latent_reevaluation),
            IntervalTrigger(seconds=LATENT_REEVALUATION_INTERVAL),
            id="latent_reevaluation",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        scheduler.add_job(
            self._run_task(self._forget_after_scan),
            IntervalTrigger(seconds=DEFAULT_FORGETAFTER_SCAN),
            id="forget_after_scan",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        scheduler.add_job(
            self._run_task(self._degradation_tick),
            IntervalTrigger(seconds=DEFAULT_DEGRADATION_TICK),
            id="degradation_tick",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        scheduler.add_job(
            self._run_task(self._bus_drain),
            IntervalTrigger(seconds=BUS_DRAIN_INTERVAL),
            id="bus_drain",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        scheduler.start()
        self._scheduler = scheduler
        logger.info(
            "kairos scheduler started (forgetting_scan/latent_reevaluation/forget_after_scan/degradation_tick/bus_drain)"
        )

    async def shutdown(self) -> None:
        """停止调度。"""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    # ------------------------------------------------------------------
    # 任务实现（错误隔离：单任务失败不影响调度循环）
    # ------------------------------------------------------------------

    def _run_task(self, coro_factory: Any) -> Any:
        async def _wrapper() -> None:
            try:
                await coro_factory()
            except Exception:
                # 任务错误隔离：不阻断调度循环（健康计数器/观测留痕由后续接入）
                logger.exception("scheduled task failed")

        return _wrapper

    async def _forgetting_scan(self) -> None:
        from src.config import load_settings

        if not load_settings().get("KAIROS_FEATURE_FORGETTING_ENGINE"):
            return  # 特征标志 OFF：遗忘扫描不启动
        decisions = await self.app.forgetting.scan()
        archived = [d.memory_id for d in decisions if d.action == "archive"]
        if archived:
            logger.info("forgetting_scan: %d archived", len(archived))

    async def _latent_reevaluation(self) -> None:
        result = await self.app.forgetting.reevaluate_latent()
        if result["revival_candidates"]:
            logger.info("latent_reevaluation: %d revival candidates", result["revival_candidates"])

    async def _forget_after_scan(self) -> None:
        expired = await self.app.forgetting.forget_after_scan()
        if expired:
            logger.info("forget_after_scan: %d expired temporary memories deleted", len(expired))

    async def _degradation_tick(self) -> None:
        last_cal = await self.app.calibration.last_calibration_at()
        mode = await self.app.degradation.tick(last_calibration_at=last_cal)
        if mode != "normal":
            logger.info("degradation_tick: mode=%s", mode)

    async def _bus_drain(self) -> None:
        """消费事件队列（use_event → 影子副本增量 + memories.last_access_at 刷新）。

        架构 §10.10 分发语义：publish 持久化 + 入队，drain 确定性消费——无消费端
        则订阅器永不执行（使用不驱动新鲜度，"记忆即使用"闭环断裂）。
        """
        processed = await self.app.bus.drain()
        if processed:
            logger.debug("bus_drain: %d events dispatched", processed)
