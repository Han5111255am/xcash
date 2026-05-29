from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q

if TYPE_CHECKING:
    from datetime import timedelta
from django.utils import timezone

from chains.models import TxTaskStatus
from core.runtime_settings import get_confirming_withdrawal_timeout
from core.runtime_settings import get_pending_withdrawal_timeout
from core.runtime_settings import get_reviewing_withdrawal_timeout
from core.runtime_settings import get_webhook_event_timeout
from webhooks.models import WebhookEvent
from withdrawals.models import Withdrawal
from withdrawals.models import WithdrawalReviewStatus


class OperationalRiskService:
    """统一收口后台巡检阈值，避免仪表盘与异步巡检出现两套口径。"""

    @classmethod
    def reviewing_withdrawal_timeout(cls) -> timedelta:
        return get_reviewing_withdrawal_timeout()

    @classmethod
    def pending_withdrawal_timeout(cls) -> timedelta:
        return get_pending_withdrawal_timeout()

    @classmethod
    def confirming_withdrawal_timeout(cls) -> timedelta:
        return get_confirming_withdrawal_timeout()

    @classmethod
    def webhook_event_timeout(cls) -> timedelta:
        return get_webhook_event_timeout()

    @classmethod
    def stalled_withdrawals(cls):
        now = timezone.now()
        return Withdrawal.objects.filter(
            Q(
                review_status=WithdrawalReviewStatus.REVIEWING,
                updated_at__lte=now - cls.reviewing_withdrawal_timeout(),
            )
            | Q(
                review_status=WithdrawalReviewStatus.APPROVED,
                tx_task__status__in=(
                    TxTaskStatus.QUEUED,
                    TxTaskStatus.PENDING_CHAIN,
                ),
                updated_at__lte=now - cls.pending_withdrawal_timeout(),
            )
            | Q(
                review_status=WithdrawalReviewStatus.APPROVED,
                tx_task__status=TxTaskStatus.PENDING_CONFIRM,
                updated_at__lte=now - cls.confirming_withdrawal_timeout(),
            )
        ).select_related("project", "crypto", "chain", "tx_task")

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
        stalled_withdrawals = cls.stalled_withdrawals()
        stalled_webhook_events = cls.stalled_webhook_events()

        return {
            "reviewing_withdrawal_count": stalled_withdrawals.filter(
                review_status=WithdrawalReviewStatus.REVIEWING
            ).count(),
            "pending_withdrawal_count": stalled_withdrawals.filter(
                tx_task__status__in=(
                    TxTaskStatus.QUEUED,
                    TxTaskStatus.PENDING_CHAIN,
                )
            ).count(),
            "confirming_withdrawal_count": stalled_withdrawals.filter(
                tx_task__status=TxTaskStatus.PENDING_CONFIRM
            ).count(),
            "stalled_withdrawal_count": stalled_withdrawals.count(),
            "stalled_webhook_event_count": stalled_webhook_events.count(),
            "recent_stalled_withdrawals": list(
                stalled_withdrawals.order_by("updated_at")[:limit]
            ),
            "recent_stalled_webhook_events": list(
                stalled_webhook_events.order_by("created_at")[:limit]
            ),
        }
