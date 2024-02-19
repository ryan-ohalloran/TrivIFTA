from django.db import models
from monthly_billing_job.services.myadmin import DeviceContract
from typing import List
from dateutil.parser import parse

class ContractBillEntry(models.Model):
    serial_no = models.CharField(max_length=50)
    vin = models.CharField(max_length=20, null=True, blank=True)
    database = models.CharField(max_length=50, null=True, blank=True)
    assigned_po = models.CharField(max_length=50, null=True, blank=True)
    bill_days = models.IntegerField()
    billing_days = models.FloatField()
    total_cost = models.FloatField()
    company_name = models.CharField(max_length=150)
    display_name = models.CharField(max_length=1000, null=True, blank=True)
    period_from = models.DateField()
    period_to = models.DateField()

    class Meta:
        unique_together = (('serial_no', 'vin', 'database', 'assigned_po', 'period_from', 'period_to'),)

    @staticmethod
    def save_all_entries(entries: List[DeviceContract]):
        """
        Save all entries in the dataframe to the database
        """
        for entry in entries:
            ContractBillEntry.objects.update_or_create(
                serial_no=entry.serial_no,
                vin=entry.vin,
                database=entry.database,
                assigned_po=entry.assigned_po,
                bill_days=entry.bill_days,
                billing_days=entry.billing_days,
                total_cost=entry.total_cost,
                company_name=entry.company_name,
                display_name=entry.display_name,
                period_from=parse(entry.period_from).date(),
                period_to=parse(entry.period_to).date(),
            )
    def __str__(self):
        return self.serial_no

class OrderBillEntry(models.Model):
    po_number = models.CharField(max_length=50)
    current_status = models.CharField(max_length=100)
    placed_by = models.CharField(max_length=100)
    shipping_address = models.CharField(max_length=250)
    order_date = models.DateField()
    item_cost = models.FloatField()
    shipping_cost = models.FloatField()
    order_total = models.FloatField()
    order_number = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150)

    class Meta:
        unique_together = (('po_number', 'order_number', 'order_date'),)

    @staticmethod
    def save_all_entries(entries: List[DeviceContract]):
        """
        Save all entries in the dataframe to the database
        """
        for entry in entries:
            OrderBillEntry.objects.update_or_create(
                po_number=entry.po_number,
                current_status=entry.current_status,
                placed_by=entry.placed_by,
                shipping_address=entry.shipping_address,
                order_date=parse(entry.order_date).date(),
                item_cost=entry.item_cost,
                shipping_cost=entry.shipping_cost,
                order_total=entry.order_total,
                order_number=entry.order_number,
                company_name=entry.company_name
            )
    def __str__(self):
        return self.po_number