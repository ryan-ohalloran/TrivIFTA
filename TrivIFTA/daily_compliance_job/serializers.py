from rest_framework import serializers
from .models import IftaEntry

class IftaEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = IftaEntry
        fields = '__all__'