# monthly_billing_job/urls.py
from django.urls import path
from monthly_billing_job.views import ItemizedReceiptView

urlpatterns = [
    path('api/itemized-receipt/<str:company_name>/<int:month>/<int:year>/', ItemizedReceiptView.as_view(), name='itemized-receipt'),
]
