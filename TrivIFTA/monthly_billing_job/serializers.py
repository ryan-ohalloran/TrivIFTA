from rest_framework import serializers
from monthly_billing_job.models import Bill, ContractBillItem, OrderBillItem

class CompanyBillSerializer(serializers.Serializer):
    company_name = serializers.CharField()
    period_from = serializers.CharField()
    period_to = serializers.CharField()
    total_cost = serializers.FloatField()

class ItemizedReceiptSerializer(serializers.Serializer):
    company_name = serializers.CharField()
    item_type = serializers.CharField()
    item_identifier = serializers.CharField()
    item_date = serializers.CharField()
    name = serializers.CharField(required=False, allow_blank=True)
    annotated_quantity = serializers.IntegerField(required=False, allow_null=True)
    annotated_billing_days = serializers.IntegerField(required=False)
    annotated_item_cost = serializers.FloatField(required=False)
    annotated_total_cost = serializers.FloatField()
    annotated_shipping_cost = serializers.FloatField(required=False)
