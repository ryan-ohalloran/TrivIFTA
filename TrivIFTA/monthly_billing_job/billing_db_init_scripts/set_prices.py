#!/usr/bin/env python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrivIFTA.settings')

application = get_wsgi_application()


from monthly_billing_job.models import *
from monthly_billing_job.services.myadmin import MyAdminPublicAPI    

RATE_PLAN_PRICES = {
    "suspend": 8.0,
    "base": 12.0,
    "pro": 27.0,
    "proplus": 32.0,
    "flex asset tracker": 15.0,
    "surfsight": 18.0,
}

def set_rate_plan_prices():
    # Iterate over each rate plan and set the default customer fee
    for rate_plan in RatePlan.objects.all():
        rate_plan_name = rate_plan.name.lower()
        if "suspend" in rate_plan_name:
            print(f'{rate_plan_name} | {RATE_PLAN_PRICES["suspend"]}')
            rate_plan.default_customer_fee = RATE_PLAN_PRICES["suspend"]
        elif "base" in rate_plan_name:
            print(f'{rate_plan_name} | {RATE_PLAN_PRICES["base"]}')
            rate_plan.default_customer_fee = RATE_PLAN_PRICES["base"]
        elif "proplus" in rate_plan_name:
            print(f'{rate_plan_name} | {RATE_PLAN_PRICES["proplus"]}')
            rate_plan.default_customer_fee = RATE_PLAN_PRICES["proplus"]
        elif "flex asset tracker" in rate_plan_name:
            print(f'{rate_plan_name} | {RATE_PLAN_PRICES["flex asset tracker"]}')
            rate_plan.default_customer_fee = RATE_PLAN_PRICES["flex asset tracker"]
        elif ("pro" in rate_plan_name and "proplus" not in rate_plan_name) or "premium" in rate_plan_name:
            print(f'{rate_plan_name} | {RATE_PLAN_PRICES["pro"]}')
            rate_plan.default_customer_fee = RATE_PLAN_PRICES["pro"]
        elif "surfsight" in rate_plan_name:
            print(f'{rate_plan_name} | {RATE_PLAN_PRICES["surfsight"]}')
            rate_plan.default_customer_fee = RATE_PLAN_PRICES["surfsight"]
        else:
            # for now, default to 1.5 times the monthly fee
            print(f'{rate_plan_name} | {rate_plan.monthly_fee * 1.5}')
            rate_plan.default_customer_fee = rate_plan.monthly_fee * 1.5

        rate_plan.save()

def main():
    set_rate_plan_prices()

if __name__ == '__main__':
    main()