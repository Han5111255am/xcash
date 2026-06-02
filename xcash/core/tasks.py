import structlog
from celery import shared_task

from alerts.service import TelegramAlertService
from common.decorators import singleton_task
from core.monitoring import OperationalRiskService

logger = structlog.get_logger()


@shared_task(ignore_result=True)
@singleton_task(timeout=55)
def scan_operational_risks() -> None:
    """周期性巡检回调链路中的卡单风险，并输出结构化告警。"""
    summary = OperationalRiskService.build_summary(limit=3)
    # 项目级 Telegram 告警与后台巡检共享同一异常口径，避免“后台看得到但负责人收不到”的状态漂移。
    TelegramAlertService().sync_operational_alerts()
    if not summary["stalled_webhook_event_count"]:
        return

    logger.warning(
        "运营巡检发现异常任务",
        stalled_webhook_events=summary["stalled_webhook_event_count"],
        sample_event_ids=[
            event.pk for event in summary["recent_stalled_webhook_events"]
        ],
    )
