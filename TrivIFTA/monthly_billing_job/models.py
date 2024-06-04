from django.db import models
from typing import List
from dateutil.parser import parse
from django.contrib.auth.models import AbstractUser, Group, Permission
from rest_framework.authtoken.models import Token
from django.core.exceptions import MultipleObjectsReturned
from datetime import date

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

class Pricing(models.Model):
    COMPANY_TYPE_CHOICES = [
        ('default', 'Default'),
        ('internal', 'Internal'),
        ('sourcewell', 'Sourcewell'),
    ]
    company_type = models.CharField(max_length=10, choices=COMPANY_TYPE_CHOICES)
    markup_rate = models.FloatField()
    reseller = models.ForeignKey(Reseller, on_delete=models.RESTRICT, related_name='pricings', null=True)

    class Meta:
        unique_together = (('reseller', 'company_type'),)

    def save(self, *args, **kwargs):
        if not self.reseller_id:
            default_reseller, created = Reseller.objects.get_or_create(name='Default Reseller')
            self.reseller_id = default_reseller.id
        super().save(*args, **kwargs)

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
    company_type = models.CharField(max_length=10, choices=Pricing.COMPANY_TYPE_CHOICES, default='default')

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
    
class Contract(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contracts')
    serial_no = models.CharField(max_length=100)
    vin = models.CharField(max_length=20, null=True, blank=True)
    database = models.CharField(max_length=50, null=True, blank=True)
    assigned_po = models.CharField(max_length=50, null=True, blank=True)
    bill_days = models.IntegerField()
    billing_days = models.FloatField()
    total_cost = models.FloatField()
    rate_plan_name = models.CharField(max_length=1000, null=True, blank=True, default='')
    rate_plan_fee = models.FloatField(default=-1.0)
    period_from = models.DateTimeField()
    period_to = models.DateTimeField()
    customer_cost = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = (('serial_no', 'period_from', 'period_to'),)

    def __str__(self):
        return self.serial_no
    
    @classmethod
    def get_contract_by_serial_no_and_period(cls, serial_no: str, period_from: date, period_to: date) -> 'Contract':
        try:
            return cls.objects.get(serial_no=serial_no, period_from=period_from, period_to=period_to)
        except cls.DoesNotExist:
            return None

class Order(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='orders')
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


class Bill(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bills')
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
