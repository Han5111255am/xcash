from aml.service import AmlScreeningService
from celery import shared_task


@shared_task(ignore_result=True)
def screen_invoice_aml(invoice_id: int) -> None:
    AmlScreeningService.screen_invoice(invoice_id)


@shared_task(ignore_result=True)
def screen_deposit_aml(deposit_id: int) -> None:
    AmlScreeningService.screen_deposit(deposit_id)
