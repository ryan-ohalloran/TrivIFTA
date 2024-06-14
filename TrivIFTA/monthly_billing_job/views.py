# views.py
import csv
from django.http import HttpResponse
from django.db.models import F, Value, CharField, FloatField, Sum, Min, Max
from django.db.models.functions import Concat
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, Contract, Company, Bill, OrderItem
from .serializers import CompanyBillSerializer, ItemizedReceiptSerializer
from datetime import datetime, timedelta
from django.utils import timezone
import calendar

class GetAllCompaniesView(APIView):
    def get(self, request, format=None):
        companies = Company.objects.all()
        company_names = companies.values_list('name', flat=True)
        return Response({'companies': list(company_names)})

class CompanyBillView(APIView):
    def get(self, request, company_name, month, year, format=None):
        period_from = timezone.make_aware(datetime(year, month, 1))
        period_to = timezone.make_aware(datetime(year, month, 1) + timedelta(days=calendar.monthrange(year, month)[1] - 1))

        # Fetch all companies with the given name
        companies = Company.objects.filter(name=company_name)
        if not companies.exists():
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        company_ids = companies.values_list('company_id', flat=True)
        
        # Sum up the total_cost fields for each company entry with that id in the companybill table
        period_from=f'{year}-{month:02d}-01'
        period_to=f'{year}-{month:02d}-{calendar.monthrange(year, month)[1]}'

        total_cost = Bill.objects.filter(
            company_id__in=company_ids,
            period_from=period_from,
            period_to=period_to
        ).aggregate(total_cost=Sum('total_cost'))

        # Serialize the data
        serializer = CompanyBillSerializer({
            'company_name': company_name,
            'period_from': period_from,
            'period_to': period_to,
            'total_cost': round(total_cost['total_cost'] or 0, 2)
        })

        # Create the CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{company_name}_{month}_{year}_bill.csv"'

        writer = csv.writer(response)
        writer.writerow(['Company Name', 'Period From', 'Period To', 'Total Cost'])
        writer.writerow([serializer.data['company_name'], serializer.data['period_from'], serializer.data['period_to'], serializer.data['total_cost']])

        return response
    
class ItemizedReceiptView(APIView):
    def get(self, request, company_name, month, year, format=None):
        period_from = timezone.make_aware(datetime(year, month, 1))
        period_to = timezone.make_aware(datetime(year, month, 1) + timedelta(days=calendar.monthrange(year, month)[1] - 1))

        # Fetch all companies with the given name
        companies = Company.objects.filter(name=company_name)
        if not companies.exists():
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        company_ids = companies.values_list('company_id', flat=True)

        # Fetch order items for all orders in the given period
        order_items = OrderItem.objects.filter(
            order__company_id__in=company_ids,
            order__order_date__range=[period_from, period_to]
        ).annotate(
            company_name=F('order__company__name'),
            item_type=Value('Order', output_field=CharField()),
            item_identifier=F('order__order_number'),
            item_date=F('order__order_date'),
            name=F('product__name'),
            annotated_quantity=F('quantity'),
            annotated_item_cost=F('unit_cost'),
            annotated_total_cost=(F('unit_cost') * F('quantity')),
            annotated_shipping_cost=F('order__shipping_cost'),
        ).values('company_name', 'item_type', 'item_identifier', 'item_date', 'name', 'annotated_quantity', 'annotated_item_cost', 'annotated_total_cost', 'annotated_shipping_cost')

        # Fetch contracts for all companies with the given name
        contracts = Contract.objects.filter(
            company_id__in=company_ids,
            month=month,
            year=year
        ).annotate(
            company_name=Value(company_name, output_field=CharField()),
            item_type=Value('Recurring', output_field=CharField()),
            item_identifier=F('serial_no'),
            item_date=Concat(Value(f'{year}-'), Value(month, output_field=CharField()), Value('-01'), output_field=CharField()),
            name=F('rate_plan__name'),
            annotated_billing_days=F('billing_days'),
            annotated_item_cost=F('customer_cost'),
            annotated_total_cost=F('total_customer_cost'),
            annotated_shipping_cost=Value(0, output_field=FloatField()),
        ).values('company_name', 'item_type', 'item_identifier', 'item_date', 'name', 'annotated_billing_days', 'annotated_item_cost', 'annotated_total_cost', 'annotated_shipping_cost')

        # Combine the results
        itemized_receipt = list(order_items) + list(contracts)

        # Serialize the data
        serializer = ItemizedReceiptSerializer(itemized_receipt, many=True)

        # Create the CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{company_name}_{month}_{year}_itemized_receipt.csv"'

        writer = csv.writer(response)
        writer.writerow(['Company Name', 'Item Type', 'Item Identifier', 'Item Date', 'Name', 'Quantity', 'Billing Days', 'Item Cost', 'Total Cost', 'Shipping Cost', 'Total Cost with Shipping'])
        # Track orders for which the shipping cost has already been included
        processed_orders = set()
        for item in serializer.data:
            order_number = item['item_identifier']
            if order_number in processed_orders:
                shipping_cost = 0
            else:
                shipping_cost = item.get('annotated_shipping_cost', 0)
                processed_orders.add(order_number)
            order_total = item['annotated_total_cost'] + shipping_cost
            writer.writerow([
                item['company_name'],
                item['item_type'],
                item['item_identifier'],
                item['item_date'],
                item.get('name', ''),
                item.get('annotated_quantity', ''),
                item.get('annotated_billing_days', ''),
                f"{item.get('annotated_item_cost', 0):.2f}",
                f"{item['annotated_total_cost']:.2f}",
                f"{shipping_cost:.2f}",
                f"{order_total:.2f}"
            ])

        return response

class CompanyBillsForMonthView(APIView):
    def get(self, request, month, year, format=None):
        try:
            period_from = timezone.make_aware(datetime(year, month, 1))
            period_to = timezone.make_aware(datetime(year, month, 1) + timedelta(days=calendar.monthrange(year, month)[1] - 1))
        except ValueError:
            return Response({'error': 'Invalid month or year'}, status=status.HTTP_400_BAD_REQUEST)

        bills = Bill.objects.filter(period_from=period_from, period_to=period_to)
        if not bills.exists():
            return Response({'error': 'No bills found for the given period'}, status=status.HTTP_404_NOT_FOUND)

        company_bills = bills.values('company__name').annotate(
            company_name=F('company__name'),
            period_from=Min('period_from'),
            period_to=Max('period_to'),
            total_cost=Sum('total_cost')
        ).order_by('company__name')

        # Ensure total_cost is rounded to 2 decimal places
        for bill in company_bills:
            bill['total_cost'] = round(bill['total_cost'], 2)

        serializer = CompanyBillSerializer(company_bills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)