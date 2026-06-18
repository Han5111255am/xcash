from django.contrib import admin
from django.db.models import F
from django.db.models.functions import Greatest
from tron.client import TronHttpClient
from tron.models import TronTxTask
from tron.models import TronWatchCursor
from unfold.decorators import display

from chains.models import Chain
from common.admin import ReadOnlyModelAdmin
from common.admin_scan_cursor import SyncScanCursorToLatestActionMixin


@admin.register(TronTxTask)
class TronTxTaskAdmin(ReadOnlyModelAdmin):
    ordering = ("-created_at",)
    exclude = ("signed_payload",)
    readonly_fields = (
        "base_task",
        "sender",
        "chain",
        "to",
        "function_selector",
        "parameter",
        "fee_limit",
        "display_status",
        "tx_id",
        "display_expiration_state",
        "expiration",
        "ref_block_bytes",
        "ref_block_hash",
        "simulation_revert_count",
        "simulation_revert_first_at",
        "formatted_last_attempt_at",
        "created_at",
    )
    list_display = (
        "display_sender",
        "display_chain",
        "tx_type",
        "to",
        "function_selector",
        "display_status",
        "display_expiration_state",
        "tx_id",
        "created_at",
        "formatted_last_attempt_at",
    )
    list_filter = ("chain", "base_task__tx_type", "base_task__status")
    list_select_related = ("base_task", "sender", "chain")
    search_fields = ("base_task__tx_hash", "tx_id", "sender__address", "to")

    @admin.display(description="执行时间", ordering="last_attempt_at")
    def formatted_last_attempt_at(self, obj: TronTxTask):
        if obj.last_attempt_at:
            return obj.last_attempt_at.strftime("%-m月%-d日 %H:%M:%S")
        return None

    @display(
        description="状态",
        label={
            "待提交": "warning",
            "已提交": "warning",
            "成功": "success",
            "失败": "danger",
        },
    )
    def display_status(self, obj: TronTxTask):
        return obj.status

    @display(
        description="过期",
        label={
            "未签名": "secondary",
            "否": "success",
            "是": "warning",
        },
    )
    def display_expiration_state(self, obj: TronTxTask) -> str:
        if obj.expiration is None:
            return "未签名"
        return "是" if obj.is_expired() else "否"

    @admin.display(description="类型", ordering="base_task__tx_type")
    def tx_type(self, obj: TronTxTask):  # pragma: no cover
        return obj.base_task.get_tx_type_display() if obj.base_task_id else "—"

    @admin.display(ordering="sender__address", description="发送地址")
    def display_sender(self, obj: TronTxTask):  # pragma: no cover
        return obj.sender

    @admin.display(ordering="chain__code", description="网络")
    def display_chain(self, obj: TronTxTask):  # pragma: no cover
        return obj.chain


@admin.register(TronWatchCursor)
class TronWatchCursorAdmin(SyncScanCursorToLatestActionMixin, ReadOnlyModelAdmin):
    actions = (
        "enable_selected_scanners",
        "disable_selected_scanners",
        "sync_selected_to_latest",
    )
    ordering = ("chain__code",)
    list_display = (
        "display_chain",
        "display_enabled",
        "display_lag_state",
        "display_chain_latest_block",
        "last_scanned_block",
        "display_scan_gap",
        "display_error_state",
        "display_error_summary",
        "updated_at",
    )
    list_filter = ("enabled", "chain")
    search_fields = ("chain__code", "last_error")
    list_select_related = ("chain",)
    readonly_fields = (
        "chain",
        "display_enabled",
        "last_scanned_block",
        "display_chain_latest_block",
        "display_scan_gap",
        "display_lag_state",
        "last_error",
        "display_error_summary",
        "last_error_at",
        "updated_at",
        "created_at",
    )
    fields = readonly_fields

    def get_sync_latest_block(self, *, chain: Chain) -> int:
        latest_block = TronHttpClient(chain=chain).get_latest_solid_block_number()
        Chain.objects.filter(pk=chain.pk).update(
            latest_block_number=Greatest(F("latest_block_number"), latest_block)
        )
        chain.refresh_from_db(fields=["latest_block_number"])
        return chain.latest_block_number

    @admin.display(ordering="chain__code", description="网络")
    def display_chain(self, obj: TronWatchCursor):  # pragma: no cover
        return obj.chain

    @display(
        description="启用",
        label={
            "是": "success",
            "否": "danger",
        },
    )
    def display_enabled(self, obj: TronWatchCursor) -> str:
        return "是" if obj.enabled else "否"

    @admin.display(description="链上最新块")
    def display_chain_latest_block(self, obj: TronWatchCursor) -> int:  # pragma: no cover
        return obj.chain.latest_block_number

    @admin.display(description="落后区块")
    def display_scan_gap(self, obj: TronWatchCursor) -> int:
        return max(obj.chain.latest_block_number - obj.last_scanned_block, 0)

    @display(
        description="积压",
        label={
            "正常": "success",
            "轻微": "warning",
            "严重": "danger",
        },
    )
    def display_lag_state(self, obj: TronWatchCursor) -> str:
        gap = self.display_scan_gap(obj)
        if gap >= 128:
            return "严重"
        if gap >= 16:
            return "轻微"
        return "正常"

    @display(
        description="扫描状态",
        label={
            "正常": "success",
            "异常": "danger",
        },
    )
    def display_error_state(self, obj: TronWatchCursor) -> str:
        return "异常" if obj.last_error else "正常"

    @admin.display(description="错误摘要")
    def display_error_summary(self, obj: TronWatchCursor) -> str:
        if not obj.last_error:
            return "—"
        return obj.last_error[:60]
