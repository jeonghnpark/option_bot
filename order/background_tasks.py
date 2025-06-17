from asyncio import Task
import asyncio
from django.http import StreamingHttpResponse

from datetime import datetime
import traceback
import logging
import json


logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    _instance = None
    _tasks = {}
    _strategy_params = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def start_flexswitch_task(cls, params: dict) -> dict:
        strategy_type = params.get("strategy_type")

        if strategy_type in cls._tasks:
            logger.info(f"{strategy_type} task already running")
            return {
                "status": "already_running",
                "message": f"{strategy_type} strategy is already running",
            }

        cls._strategy_params[strategy_type] = params

        async def run_single_flexswitch():
            from order.views import run_flexswitch_strategy_internal

            try:
                logger.info(
                    f"Running {strategy_type} strategy iteration \n {cls._strategy_params[strategy_type]}"
                )
                current_params = cls._strategy_params[strategy_type].copy()
                current_params["portfolio_id"] = (
                    f"{strategy_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )

                try:
                    await run_flexswitch_strategy_internal(current_params)
                except Exception as e:
                    logger.error(f"Error in {strategy_type} iteration: {e}")
                    logger.error("Traceback:", exc_info=True)

                # 다음 실행 예약
                await asyncio.sleep(int(current_params["interval"]) * 60)
                if strategy_type in cls._tasks:  # 태스크가 아직 활성 상태인 경우에만
                    asyncio.create_task(run_single_flexswitch())

            except asyncio.CancelledError:
                logger.info(f"{strategy_type} task cancelled")
            except Exception as e:
                logger.error(f"Fatal error in {strategy_type} task: {e}")
                cls.stop_flexswitch_task(strategy_type)

        task = asyncio.create_task(run_single_flexswitch())
        cls._tasks[strategy_type] = task
        logger.info(f"Started {strategy_type} task")
        logger.info(f"전체 cls._tasks {cls._tasks}")

        return {
            "status": "success",
            "message": f"{strategy_type} strategy started",
            "strategy_id": strategy_type,
        }

    @classmethod
    def stop_flexswitch_task(cls, strategy_type: str) -> dict:
        if strategy_type in cls._tasks:
            if cls._tasks[strategy_type]:
                cls._tasks[strategy_type].cancel()
            cls._tasks.pop(strategy_type)
            cls._strategy_params.pop(strategy_type, None)
            logger.info(f"Stopped {strategy_type} task")
            return {"status": "success", "message": f"{strategy_type} strategy stopped"}
        return {
            "status": "not_running",
            "message": f"{strategy_type} strategy was not running",
        }

    @classmethod
    async def start_portfolio_monitor_task(cls) -> dict:
        strategy_id = "portfolio_monitor"
        if strategy_id in cls._tasks:
            logger.info("포트폴리오 모니터링이 이미 실행중")
            return {
                "status": "already_running",
                "message": "포트폴리오 모니터링이 이미 실행중입니다",
            }

        cls._tasks[strategy_id] = True
        logger.info("포트폴리오 모니터링 시작")

        return {
            "status": "success",
            "message": "포트폴리오 모니터링이 시작되었습니다",
            "strategy_id": strategy_id,
        }

    @classmethod
    def stop_portfolio_monitor_task(cls) -> dict:
        strategy_id = "portfolio_monitor"
        task = cls._tasks.get(strategy_id)

        if task:
            task.cancel()
            del cls._tasks[strategy_id]
            logger.info("포트폴리오 모니터링 중지됨")
            return {
                "status": "success",
                "message": "포트폴리오 모니터링이 중지되었습니다",
            }

        return {
            "status": "not_running",
            "message": "포트폴리오 모니터링이 실행중이지 않습니다",
        }

    @classmethod
    def is_portfolio_monitor_running(cls) -> bool:
        return "portfolio_monitor" in cls._tasks

    @classmethod
    async def start_liquidation_task(cls) -> dict:
        strategy_id = "auto_liquidation"
        if strategy_id in cls._tasks:
            logger.info("자동청산 테스크가 이미 실행중")
            return {"status": "already_running", "message": "자동청산이 이미 실행중"}

        async def run_single_liquidation():
            from order.views import auto_liquidation_internal

            try:
                logger.info("자동청산 실행중")
                await auto_liquidation_internal()
                # 다음 실행을 예약
                await asyncio.sleep(15)
                if strategy_id in cls._tasks:  # 태스크가 아직 활성 상태인 경우에만
                    asyncio.create_task(run_single_liquidation())
            except asyncio.CancelledError:
                logger.info("자동청산 태스크가 취소되었습니다")
            except Exception as e:
                logger.error(f"자동 청산 태스크 치명적 오류 {e}")
                logger.error(f"Traceback:", exe_info=True)
                cls.stop_liquidation_task()

        task = asyncio.create_task(run_single_liquidation())
        cls._tasks[strategy_id] = task
        logger.info("자동청산 태스크 시작")
        logger.info(f"전체 cls._tasks {cls._tasks}")

        return {
            "status": "success",
            "message": "자동청산이 시작되었습니다.",
            "strategy_id": strategy_id,
        }

    @classmethod
    def stop_liquidation_task(cls) -> dict:  # 동기함수
        strategy_id = "auto_liquidation"
        task = cls._tasks.get(strategy_id)
        if task:  # 청산중이면
            task.cancel()
            del cls._tasks[strategy_id]

            logger.info("자동청산이 중지됨")
            return {"status": "success", "message": "자동청산이 중지되었습니다. "}
        return {"status": "not_running", "message": "자동청산이 실행중이 아닙니다. "}

    @classmethod
    async def start_buydip_task(cls, params: dict) -> dict:
        strategy_id = "buydip"

        if strategy_id in cls._tasks:
            logger.info("Buy-dip task already running")
            return {
                "status": "already_running",
                "message": "Buy-dip strategy is already running",
            }

        cls._strategy_params[strategy_id] = params

        async def run_single_buydip():
            from order.views import run_buydip_strategy_internal

            try:
                logger.info("Running buy-dip strategy iteration")
                current_params = cls._strategy_params[strategy_id].copy()
                current_params["portfolio_id"] = (
                    f"buydip_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )

                try:
                    await run_buydip_strategy_internal(current_params)
                except Exception as e:
                    logger.error(f"Error in buy-dip iteration: {e}")
                    logger.error("Traceback:", exc_info=True)

                # 다음 실행 예약
                await asyncio.sleep(int(current_params["interval"]) * 60)
                if strategy_id in cls._tasks:  # 태스크가 아직 활성 상태인 경우에만
                    asyncio.create_task(run_single_buydip())

            except asyncio.CancelledError:
                logger.info("Buy-dip task cancelled")
            except Exception as e:
                logger.error(f"Fatal error in buy-dip task: {e}")
                cls.stop_buydip_task()

        task = asyncio.create_task(run_single_buydip())
        cls._tasks[strategy_id] = task
        logger.info("Started buy-dip task")
        logger.info(f"전체 cls._tasks {cls._tasks}")

        return {
            "status": "success",
            "message": "Buy-dip strategy started",
            "strategy_id": strategy_id,
        }

    @classmethod
    def stop_buydip_task(cls) -> dict:
        strategy_id = "buydip"
        task = cls._tasks.get(strategy_id)

        if task:
            task.cancel()
            del cls._tasks[strategy_id]
            if strategy_id in cls._strategy_params:
                del cls._strategy_params[strategy_id]
            logger.info("Stopped buy-dip task")
            return {"status": "success", "message": "Buy-dip strategy stopped"}

        return {"status": "not_running", "message": "Buy-dip strategy was not running"}

    @classmethod
    def is_buydip_task_running(cls) -> bool:
        # print(f"cls._tasks{cls._tasks}")
        return "buydip" in cls._tasks

    @classmethod
    def is_liquidation_task_running(cls) -> bool:
        return "auto_liquidation" in cls._tasks
