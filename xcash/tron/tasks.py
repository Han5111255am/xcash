import structlog
from celery import shared_task
from tron.client import TronClientError
from tron.scanner import TronUsdtPaymentScanner

from chains.constants import ChainType
from chains.models import Chain
from common.decorators import singleton_task

logger = structlog.get_logger()


@shared_task(ignore_result=True)
@singleton_task(timeout=48, use_params=True)
def scan_tron_chain(chain_pk: int) -> None:
    chain = Chain.objects.get(pk=chain_pk)
    if not chain.active:
        return
    if chain.type == ChainType.TRON and not chain.tron_api_key:
        logger.warning("Tron USDT 扫描跳过，缺少 API Key", chain=chain.code)
        return

    try:
        try:
            summary = TronUsdtPaymentScanner.scan_chain(chain=chain)
        except TronClientError:
            logger.warning("Tron USDT 扫描 RPC 失败", chain=chain.code)
            return

        logger.info(
            "Tron USDT 扫描完成",
            chain=chain.code,
            filter_addresses=summary.filter_addresses,
            blocks_scanned=summary.blocks_scanned,
            events_seen=summary.events_seen,
        )
    finally:
        # 无论成功还是 RPC 失败都推进 last_scanned_at，按固定周期重试。
        chain.mark_scanned()


@shared_task(ignore_result=True)
@singleton_task(timeout=64)
def scan_active_tron_chains() -> None:
    """每 2 秒巡检活跃 Tron 链，仅调度到期（now - last_scanned_at ≥ 扫描周期）的链。"""
    chains = (
        Chain.objects.filter(active=True, type=ChainType.TRON)
        .exclude(tron_api_key="")
    )
    for chain in chains:
        if chain.is_due_for_scan:
            scan_tron_chain.delay(chain.pk)
