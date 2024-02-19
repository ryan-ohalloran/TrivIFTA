from rest_framework import serializers
from .models import ContractBillEntry, OrderBillEntry

class ContractBillEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractBillEntry
        fields = '__all__'

class OrderBillEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBillEntry
        fields = '__all__'