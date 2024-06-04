from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from monthly_billing_job.models import Bill
from monthly_billing_job.serializers import BillSerializer
from datetime import datetime
from .utils import last_day_of_month

@api_view(['GET'])
def get_company_bills(request, year, month):
    try:
        period_from = datetime(year, month, 1).date()
        period_to = datetime(year, month, last_day_of_month(year=year, month=month)).date()

        bills = Bill.objects.filter(period_from=period_from, period_to=period_to)
        
        serializer = BillSerializer(bills, many=True)
        return Response(serializer.data, content_type='application/json')
    except Exception as e:
        return Response({'error': str(e)}, status=400, content_type='application/json')