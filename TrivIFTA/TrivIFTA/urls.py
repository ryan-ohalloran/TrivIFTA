"""
URL configuration for TrivIFTA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from daily_compliance_job.views import run_job, get_entries_by_date, get_config
from django.views.generic import TemplateView
from django.urls import include 
from monthly_billing_job.views import ItemizedReceiptView, CompanyBillView, GetAllCompaniesView, CompanyBillsForMonthView

urlpatterns = [
    path('api/config/', get_config),
    path("admin/", admin.site.urls),
    path('api/run-job/', run_job),
    #TODO: fix this to route to the app-specific billing views
    path('billing/companies/', GetAllCompaniesView.as_view(), name='companies'),
    path('billing/itemized-receipt/<str:company_name>/<int:month>/<int:year>/', ItemizedReceiptView.as_view(), name='itemized-receipt'),
    path('billing/company-bill/<str:company_name>/<int:month>/<int:year>/', CompanyBillView.as_view(), name='company-bill'),
    path('billing/company-bills/<int:month>/<int:year>/', CompanyBillsForMonthView.as_view(), name='company-bills-for-month'),
    # Include other app URL patterns here if necessary
    # path('billing/', include('monthly_billing_job.urls')),

    # Catch-all route for the React app
    re_path('.*', TemplateView.as_view(template_name='index.html')),
]
