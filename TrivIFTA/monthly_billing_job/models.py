from django.db import models
from typing import Any, List
from dateutil.parser import parse
from django.contrib.auth.models import AbstractUser, Group, Permission
from rest_framework.authtoken.models import Token
from django.core.exceptions import MultipleObjectsReturned
from datetime import date
import calendar

class Reseller(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=15, null=True, blank=True)

    @classmethod
    def get_reseller_by_name(cls, name: str) -> 'Reseller':
        return cls.objects.get(name=name)

    def __str__(self):
        return self.name

class User(AbstractUser):
    groups = models.ManyToManyField(Group, related_name='users', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='users', blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='users')
    my_admin_username = models.CharField(max_length=255, null=True, blank=True)
    my_admin_password = models.CharField(max_length=255, null=True, blank=True)
    database_name = models.CharField(max_length=255, null=True, blank=True, default='default')

    def __str__(self):
        return self.email

class Account(models.Model):
    account_id = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(User, related_name='accounts')
    
    def __str__(self):
        return self.account_id
    
class CompanyType(models.Model):
    type_name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.type_name

class Company(models.Model):
    company_id = models.IntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    display_name = models.CharField(max_length=1000, null=True, blank=True)
    reseller = models.ForeignKey(Reseller, on_delete=models.CASCADE, related_name='companies')
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=55, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)    
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=15, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    company_type = models.ForeignKey(CompanyType, on_delete=models.RESTRICT, related_name='companies', null=True, blank=True)

    class Meta:
        unique_together = (('company_id',),)

    @classmethod
    def get_company_by_id(cls, company_id: int) -> 'Company':
        try:
            return cls.objects.get(company_id=company_id)
        except cls.DoesNotExist:
            return None
        
    def __str__(self):
        return self.name

class RatePlan(models.Model):
    name = models.CharField(max_length=255, unique=True)
    monthly_fee = models.FloatField()
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='rate_plans')
    month_and_year = models.CharField(max_length=7, null=True, blank=True)
    default_customer_fee = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.name        
    
    @classmethod
    def get_rate_plan_by_name_and_reseller(cls, name: str, reseller: Reseller) -> 'RatePlan':
        try:
            return cls.objects.get(name=name, reseller=reseller)
        except cls.DoesNotExist:
            return None
    
    class Meta:
        unique_together = (('name', 'monthly_fee', 'reseller', 'month_and_year'),)
    
class Contract(models.Model):
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='contracts')
    serial_no = models.CharField(max_length=100)
    vin = models.CharField(max_length=20, null=True, blank=True)
    database = models.CharField(max_length=50, null=True, blank=True)
    assigned_po = models.CharField(max_length=50, null=True, blank=True)
    bill_days = models.IntegerField()
    billing_days = models.FloatField()
    total_cost = models.FloatField()
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.RESTRICT)
    customer_cost = models.FloatField(null=True, blank=True)
    total_customer_cost = models.FloatField(default=0.0)
    month = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = (('serial_no', 'company', 'month', 'year'),)

    def __str__(self):
        return self.serial_no
    
    @classmethod
    def get_contract_by_serial_no_company_month_and_year(cls, serial_no: str, company: Company, month: int, year: int) -> 'Contract':
        try:
            return cls.objects.get(serial_no=serial_no, company=company, month=month, year=year)
        except cls.DoesNotExist:
            return None

class Order(models.Model):
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='orders')
    po_number = models.CharField(max_length=50)
    current_status = models.CharField(max_length=100)
    placed_by = models.CharField(max_length=100)
    shipping_address = models.CharField(max_length=250)
    order_date = models.DateTimeField()
    item_cost = models.FloatField()
    shipping_cost = models.FloatField()
    order_total = models.FloatField()
    order_number = models.CharField(max_length=100)
    customer_cost = models.FloatField(null=True, blank=True)
    comment = models.CharField(max_length=1000, null=True, blank=True, default='')

    class Meta:
        unique_together = (('po_number', 'order_number', 'order_date'),)

    def __str__(self):
        return self.po_number
    
    @classmethod
    def get_order_by_po_order_and_date(cls, po_number: str, order_number: str, order_date: date) -> 'Order':
        try:
            return cls.objects.get(po_number=po_number, order_number=order_number, order_date=order_date)
        except cls.DoesNotExist:
            return None

class Product(models.Model):
    product_code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=1500, null=True, blank=True)
    price = models.FloatField()
    mrsp_price = models.FloatField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    last_updated = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = (('product_code',),)
    
    def __str__(self):
        return f'{self.product_code} - {self.name}'

class PricingTier(models.Model):
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='pricing_tiers')
    min_price = models.FloatField()
    max_price = models.FloatField()
    markup_percentage = models.FloatField()

    class Meta:
        unique_together = (('reseller', 'min_price', 'max_price'),)
    
    def __str__(self):
        return f'{self.reseller} - {self.min_price} to {self.max_price}'
    
class FlatMarkup(models.Model):
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='flat_markups')
    company_type = models.ForeignKey(CompanyType, on_delete=models.RESTRICT, related_name='flat_markups')
    markup_amount = models.FloatField()

    class Meta:
        unique_together = (('reseller', 'company_type'),)

class SourcewellProductPricing(models.Model):
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='sourcewell_product_pricings')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT)
    price = models.FloatField()

    class Meta:
        unique_together = (('reseller', 'product'),)
    
    def __str__(self):
        return f'{self.reseller} - {self.product}'

class SourcewellRatePlanPricing(models.Model):
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='sourcewell_rate_plan_pricings')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.RESTRICT)
    price = models.FloatField()

    class Meta:
        unique_together = (('reseller', 'rate_plan'),)
    
    def __str__(self):
        return f'{self.reseller} - {self.rate_plan}'

class ShipItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name='ship_items')
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    tracking_url = models.URLField(null=True, blank=True)
    erp_reference = models.CharField(max_length=100, null=True, blank=True)
    purchase_order_no = models.CharField(max_length=100)

    class Meta:
        unique_together = (('order', 'purchase_order_no'),)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT)
    device_id = models.IntegerField(null=True, blank=True)
    device_plan_name = models.CharField(max_length=255, null=True, blank=True)
    unit_cost = models.FloatField()
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = (('order', 'product'),)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

class Bill(models.Model):
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='bills')
    period_from = models.DateField()
    period_to = models.DateField()
    total_cost = models.FloatField()

    class Meta:
        unique_together = (('company', 'period_from', 'period_to'),)

    def __str__(self):
        return f'Bill for {self.company.name} from {self.period_from} to {self.period_to}'

class BillItemBase(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    item_cost = models.FloatField()

    class Meta:
        abstract = True

    def __str__(self):
        return f'BillItem for {self.bill}'

class ContractBillItem(BillItemBase):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='contract_bill_items')

class OrderBillItem(BillItemBase):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='order_bill_items')

class Quote(models.Model):
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='quotes')
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    quote_date = models.DateField()
    total_cost = models.FloatField()

    class Meta:
        unique_together = (('reseller', 'customer_email', 'quote_date'),)

    def __str__(self):
        return f'{self.quote_number} for {self.company.name}'
    
class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, related_name='items', on_delete=models.RESTRICT)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.RESTRICT)
    rate_plan = models.ForeignKey(RatePlan, null=True, blank=True, on_delete=models.RESTRICT)
    price = models.FloatField()

    def __str__(self):
        return f'{self.quantity} x {self.product or self.contract} for {self.quote}'