import structlog
from celery import shared_task

from common.decorators import singleton_task
from core.monitoring import OperationalRiskService

logger = structlog.get_logger()


@shared_task(ignore_result=True)
@singleton_task(timeout=55)
def scan_operational_risks() -> None:
    """周期性巡检回调链路中的卡单风险，并输出结构化告警。"""
    summary = OperationalRiskService.build_summary(limit=3)
    if not summary["stalled_webhook_event_count"]:
        return

    logger.warning(
        "运营巡检发现异常任务",
        stalled_webhook_events=summary["stalled_webhook_event_count"],
        sample_event_ids=[
            event.pk for event in summary["recent_stalled_webhook_events"]
        ],
    )
