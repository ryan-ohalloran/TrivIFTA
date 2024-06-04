# monthly_billing_job/urls.py
from django.urls import path
from monthly_billing_job.views import get_company_bills

urlpatterns = [
    path('bills/<int:year>/<int:month>/', get_company_bills, name='get_company_bills')
]
