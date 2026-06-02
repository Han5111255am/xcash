from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import timedelta
from django.utils import timezone

from core.runtime_settings import get_webhook_event_timeout
from webhooks.models import WebhookEvent


class OperationalRiskService:
    """统一收口后台巡检阈值，避免仪表盘与异步巡检出现两套口径。"""

    @classmethod
    def webhook_event_timeout(cls) -> timedelta:
        return get_webhook_event_timeout()

    @classmethod
    def stalled_webhook_events(cls):
        now = timezone.now()
        return WebhookEvent.objects.filter(
            status=WebhookEvent.Status.PENDING,
            created_at__lte=now - cls.webhook_event_timeout(),
        ).select_related("project")

    @classmethod
    def build_summary(cls, *, limit: int = 4) -> dict:
        """返回后台展示与异步巡检共享的异常概览。"""
        stalled_webhook_events = cls.stalled_webhook_events()

        return {
            "stalled_webhook_event_count": stalled_webhook_events.count(),
            "recent_stalled_webhook_events": list(
                stalled_webhook_events.order_by("created_at")[:limit]
            ),
        }
