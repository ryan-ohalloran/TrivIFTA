#!/usr/bin/env python
import os
import csv
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrivIFTA.settings')

application = get_wsgi_application()

from monthly_billing_job.models import Company, CompanyType

def set_company_types_from_csv():
    with open('company_types.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_name = row['Company']
            company_type_name = row['Company Type'].lower()
            companies = Company.objects.filter(name__iexact=company_name)
            if companies.exists():
                company_type, created = CompanyType.objects.get_or_create(type_name=company_type_name)
                for company in companies:
                    print(f'Setting type of {company_name} to {company_type_name}')
                    company.company_type = company_type
                    company.save()
            else:
                print(f'Company {company_name} does not exist in the database')
                
def main():
    set_company_types_from_csv()

if __name__ == '__main__':
    main()