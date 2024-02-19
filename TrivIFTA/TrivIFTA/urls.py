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
from monthly_billing_job.views import get_company_bills


urlpatterns = [
    path('api/config/', get_config),
    path("admin/", admin.site.urls),
    path('api/run-job/', run_job),
    path('api/bills/', get_company_bills),
    path('api/entries/<str:date>/', get_entries_by_date),
    re_path('.*', TemplateView.as_view(template_name='index.html')),
]
