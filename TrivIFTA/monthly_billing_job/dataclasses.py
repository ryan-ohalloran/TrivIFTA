from .models import Contract, Order, Company, Bill, OrderBillItem, ContractBillItem
from datetime import date
from dataclasses import dataclass, field
from typing import List
from dateutil.parser import parse

@dataclass
class OrderEntry:
    po_number: str
    current_status: str
    placed_by: str
    shipping_address: str
    order_date: date
    item_cost: float
    shipping_cost: float
    order_total: float
    order_number: str
    company: Company 
    customer_cost: float

    def save_to_db(self):
        Order.objects.update_or_create(
            po_number=self.po_number,
            order_number=self.order_number,
            defaults={
                'company': self.company,
                'current_status': self.current_status,
                'placed_by': self.placed_by,
                'shipping_address': self.shipping_address,
                'order_date': self.order_date,
                'item_cost': self.item_cost,
                'shipping_cost': self.shipping_cost,
                'order_total': self.order_total,
                'customer_cost': self.order_total
            }
        )

@dataclass
class ContractEntry:
    serial_no: str
    vin: str
    database: str
    assigned_po: str
    bill_days: int
    billing_days: float
    total_cost: float
    rate_plan_name: str
    rate_plan_fee: float
    company: Company
    period_from: date
    period_to: date
    customer_cost: float
    
    def save_to_db(self):
        Contract.objects.update_or_create(
            serial_no=self.serial_no,
            vin=self.vin,
            database=self.database,
            assigned_po=self.assigned_po,
            period_from=self.period_from,
            defaults={
                'company': self.company,
                'bill_days': self.bill_days,
                'billing_days': self.billing_days,
                'total_cost': self.total_cost,
                'rate_plan_name': self.rate_plan_name,
                'rate_plan_fee': self.rate_plan_fee,
                'period_to': self.period_to,
                'customer_cost': self.total_cost
            }
        )

@dataclass
class CompanyBill:
    company: Company
    display_name: str
    contracts: List[ContractEntry] = field(default_factory=list)
    orders: List[OrderEntry] = field(default_factory=list)
    total_cost: float = 0

    def calculate_total_cost(self):
        self.total_cost = sum(contract.customer_cost for contract in self.contracts) + sum(order.customer_cost for order in self.orders)

    def save_to_db(self, period_from, period_to):
        self.calculate_total_cost()
        
        bill, created = Bill.objects.get_or_create(
            company=self.company,
            period_from=period_from,
            period_to=period_to,
            defaults={'total_cost': self.total_cost}
        )
        
        if not created:
            # If the bill already exists, update the total_cost
            bill.total_cost = self.total_cost
            bill.save()
        
        # Clear existing bill items to avoid duplicates
        bill.contract_bill_items.all().delete()
        bill.order_bill_items.all().delete()

        for contract in self.contracts:
            contract_instance = Contract.get_contract_by_serial_no_and_period(contract.serial_no, contract.period_from, contract.period_to)
            ContractBillItem.objects.create(
                bill=bill,
                contract=contract_instance,
                item_cost=contract.customer_cost
            )
        for order in self.orders:
            order_instance = Order.get_order_by_po_order_and_date(order.po_number, order.order_number, order.order_date)
            OrderBillItem.objects.create(
                bill=bill,
                order=order_instance,
                item_cost=order.customer_cost
            )
        return bill

    def get_itemized_bill(self):
        itemized_details = []
        for contract in self.contracts:
            itemized_details.append({
                'type': 'contract',
                'serial_no': contract.serial_no,
                'customer_cost': contract.customer_cost
            })
        for order in self.orders:
            itemized_details.append({
                'type': 'order',
                'order_number': order.order_number,
                'customer_cost': order.customer_cost
            })
        return {
            'company': self.company.name,
            'display_name': self.display_name,
            'period_from': self.period_from,
            'period_to': self.period_to,
            'total_cost': self.total_cost,
            'itemized_details': itemized_details
        }

    def get_summary_bill(self):
        return {
            'company': self.company.name,
            'display_name': self.display_name,
            'period_from': self.period_from,
            'period_to': self.period_to,
            'total_cost': self.total_cost
        }