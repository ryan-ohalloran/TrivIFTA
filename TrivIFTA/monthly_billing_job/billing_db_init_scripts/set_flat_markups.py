#!/usr/bin/env python
import os
import csv
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrivIFTA.settings')

application = get_wsgi_application()

from monthly_billing_job.models import *

def main():
    # Find first reseller
    reseller = Reseller.objects.first()
    company_types = ("internal", "sourcewell", "default")

    for company_type in company_types:
        # find the company type
        company_type = CompanyType.objects.get(type_name=company_type)
        print(f"Creating flat markup for {company_type}")
        # Set the markup amount (5.0 for all as default right now)
        flat_markup, created = FlatMarkup.objects.get_or_create(
            reseller=reseller,
            company_type=company_type,
            defaults={'markup_amount': 5.0},
        )
        print(f"Flat markup created: {flat_markup}")

if __name__ == '__main__':
    main()