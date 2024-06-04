from rest_framework import serializers
from monthly_billing_job.models import Bill, ContractBillItem, OrderBillItem

class ContractBillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractBillItem
        fields = ['contract', 'item_cost']

class OrderBillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBillItem
        fields = ['order', 'item_cost']

class BillSerializer(serializers.ModelSerializer):
    contract_bill_items = ContractBillItemSerializer(many=True, read_only=True)
    order_bill_items = OrderBillItemSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = ['company', 'period_from', 'period_to', 'total_cost', 'contract_bill_items', 'order_bill_items']