from typing import List
from dateutil.parser import parse
from .dataclasses import ContractEntry, OrderEntry
from .models import Contract, Order, Company
import datetime

def save_all_contracts(entries: List[ContractEntry]) -> None:
    for entry in entries:
        Contract.objects.update_or_create(
            company=entry.company,
            serial_no=entry.serial_no,
            vin=entry.vin,
            database=entry.database,
            assigned_po=entry.assigned_po,
            bill_days=entry.bill_days,
            billing_days=entry.billing_days,
            total_cost=entry.total_cost,
            rate_plan_name=entry.rate_plan_name,
            rate_plan_fee=entry.rate_plan_fee,
            period_from=parse(entry.period_from).date() if isinstance(entry.period_from, str) else entry.period_from,
            period_to=parse(entry.period_to).date() if isinstance(entry.period_to, str) else entry.period_to,
        )

def save_all_orders(entries: List[OrderEntry]) -> None:
    for entry in entries:
        Order.objects.update_or_create(
            company=entry.company,
            po_number=entry.po_number,
            current_status=entry.current_status,
            placed_by=entry.placed_by,
            shipping_address=entry.shipping_address,
            order_date=parse(entry.order_date).date() if isinstance(entry.order_date, str) else entry.order_date,
            item_cost=entry.item_cost,
            shipping_cost=entry.shipping_cost,
            order_total=entry.order_total,
            order_number=entry.order_number,
        )

def last_day_of_month(year: int, month: int) -> int:
    next_month = month % 12 + 1
    next_month_year = year + month // 12
    first_day_next_month = datetime.date(next_month_year, next_month, 1)
    return (first_day_next_month - datetime.timedelta(days=1)).day