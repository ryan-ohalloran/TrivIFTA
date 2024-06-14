from .models import Reseller, Contract, Order, Company, Bill, OrderBillItem, ContractBillItem, ShipItem, OrderItem, Product, RatePlan
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Set
from dateutil.parser import parse
from django.utils import timezone

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
    comment: str
    company: Company 
    customer_cost: float = 0

    def save_to_db(self):
        order, created = Order.objects.update_or_create(
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
                'customer_cost': self.customer_cost,
                'comment': self.comment
            }
        )
        return order
    
@dataclass
class RatePlanEntry:
    name: str
    monthly_fee: float
    reseller: Reseller
    month_and_year: Optional[date] = None  

    def save_to_db(self):
        RatePlan.objects.update_or_create(
            name=self.name,
            defaults={
                'monthly_fee': self.monthly_fee,
                'reseller': self.reseller,
                'month_and_year': self.month_and_year,
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
    rate_plan: RatePlan
    company: Company
    month: int
    year: int
    customer_cost: float
    total_customer_cost: float
    
    def save_to_db(self):
        # Check if the contract already exists to avoid duplicate entries
        existing_contract = Contract.get_contract_by_serial_no_company_month_and_year(self.serial_no, self.company, self.month, self.year)
        
        if existing_contract:
            # Update the existing contract
            existing_contract.vin = self.vin
            existing_contract.database = self.database
            existing_contract.assigned_po = self.assigned_po
            existing_contract.bill_days = self.bill_days
            existing_contract.billing_days = self.billing_days
            existing_contract.total_cost = self.total_cost
            existing_contract.rate_plan = self.rate_plan
            existing_contract.customer_cost = self.customer_cost
            existing_contract.total_customer_cost = self.total_customer_cost
            existing_contract.month = self.month
            existing_contract.year = self.year
            existing_contract.company = self.company
            existing_contract.save()
        else:
            # Create a new contract
            Contract.objects.create(
                serial_no=self.serial_no,
                vin=self.vin,
                database=self.database,
                assigned_po=self.assigned_po,
                bill_days=self.bill_days,
                billing_days=self.billing_days,
                total_cost=self.total_cost,
                rate_plan=self.rate_plan,
                month=self.month,
                year=self.year,
                customer_cost=self.customer_cost,
                company=self.company,
                total_customer_cost=self.total_customer_cost
            )

@dataclass
class ProductEntry:
    product_code: str
    name: str
    price: float
    mrsp_price: float
    category: Optional[str] = None
    last_updated: Optional[datetime] = None
    active: bool = True  # Default to True if not provided

    def save_to_db(self):
        # Ensure last_updated is timezone-aware
        last_updated = self.last_updated or timezone.now()
        if timezone.is_naive(last_updated):
            last_updated = timezone.make_aware(last_updated)

        # Save or update the product
        product, created = Product.objects.update_or_create(
            product_code=self.product_code,
            defaults={
                'name': self.name,
                'price': self.price,
                'mrsp_price': self.mrsp_price,
                'category': self.category,
                'last_updated': last_updated,
                'active': self.active
            }
        )
        
        return product
    
    @staticmethod
    def get_product_by_code(product_code: str) -> Optional[Product]:
        try:
            return Product.objects.get(product_code=product_code)
        except Product.DoesNotExist:
            return None

    @staticmethod
    def deactivate_old_products(threshold_days: int = 14, updated_product_codes: Set[str] = set()):
        # Deactivate products that have not been updated for more than threshold_days
        threshold_date = timezone.now() - timedelta(days=threshold_days)
        Product.objects.filter(last_updated__lt=threshold_date).update(active=False)
        Product.objects.exclude(product_code__in=updated_product_codes).update(active=False)

@dataclass
class ShipItemEntry:
    order: Order
    tracking_number: str
    tracking_url: Optional[str]
    erp_reference: str
    purchase_order_no: str

    def save_to_db(self):
        ShipItem.objects.update_or_create(
            order=self.order,
            purchase_order_no=self.purchase_order_no,
            defaults={
                'tracking_number': self.tracking_number,
                'tracking_url': self.tracking_url,
                'erp_reference': self.erp_reference
            }
        )

@dataclass
class OrderItemEntry:
    order: Order
    product: Product
    device_id: int
    device_plan_name: str
    unit_cost: float
    quantity: int

    def save_to_db(self):
        OrderItem.objects.update_or_create(
            order=self.order,
            product=self.product,
            defaults={
                'device_id': self.device_id,
                'device_plan_name': self.device_plan_name,
                'unit_cost': self.unit_cost,
                'quantity': self.quantity,
            }
        )

@dataclass
class CompanyBill:
    company: Company
    display_name: str
    contracts: List[ContractEntry] = field(default_factory=list)
    orders: List[OrderEntry] = field(default_factory=list)
    total_cost: float = 0.0

    def calculate_total_cost(self):
        unique_contracts = {contract.serial_no: contract for contract in self.contracts}.values()
        unique_orders = {order.po_number: order for order in self.orders}.values()
        
        self.total_cost = sum(contract.total_customer_cost for contract in unique_contracts) + sum(order.customer_cost for order in unique_orders)
        
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
            contract_instance = Contract.get_contract_by_serial_no_company_month_and_year(contract.serial_no, self.company, contract.month, contract.year)
            ContractBillItem.objects.update_or_create(
                bill=bill,
                contract=contract_instance,
                defaults={'item_cost': contract.customer_cost}
            )
        for order in self.orders:
            order_instance = Order.get_order_by_po_order_and_date(order.po_number, order.order_number, order.order_date)
            OrderBillItem.objects.update_or_create(
                bill=bill,
                order=order_instance,
                defaults={'item_cost': order.customer_cost}
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