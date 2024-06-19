#!/usr/bin/env python
import os
import csv
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrivIFTA.settings')

application = get_wsgi_application()

from monthly_billing_job.models import Reseller, Contract, Product, SourcewellProductPricing, SourcewellRatePlanPricing, RatePlan

def set_sourcewell_prices_from_csv():
    reseller = Reseller.objects.first()

    with open('sourcewell_product_prices.csv', 'r') as f:
        i = 0
        reader = csv.DictReader(f)
        for row in reader:
            product_code = row['SKU']
            sourcewell_price = row['Sourcewell Member Price (USD)']
            
            product = Product.objects.filter(product_code=product_code).first()
            if not product:
                continue
            if sourcewell_price == "Included in bundle":
                continue
            print(f'SKU: {product_code} | Price: {sourcewell_price} | Product: {product}')
            sourcewell_pricing, created = SourcewellProductPricing.objects.get_or_create(
                reseller=reseller,
                product=product,
                defaults={'price': sourcewell_price},
            )
            if not created:
                sourcewell_pricing.price = sourcewell_price
                sourcewell_pricing.save()
            i += 1
    print(f'{i} SourcewellProductPricing objects created')

def set_sourcewell_rate_plan_prices():
    SOURCEWELL_RATE_PLAN_PRICES = {
        "base": (10.20, "Base Plan [0700]"),
        "pro": (16.33, "Pro Plan [1540]"),
        "proplus": (19.25, "ProPlus Public Works Plan [2285]"),
        "suspend": (15.40, "Suspend Plan [1540]"),
    }
    reseller = Reseller.objects.first()
    for rate_plan, (price, plan_name) in SOURCEWELL_RATE_PLAN_PRICES.items():
        rate_plan = RatePlan.objects.get(name=plan_name)
        if not rate_plan:
            print(f'Rate plan {plan_name} not found')
        SourcewellRatePlanPricing.objects.get_or_create(
            reseller = reseller,
            rate_plan = rate_plan,
            price=price
        )

def main():
    set_sourcewell_prices_from_csv()
    set_sourcewell_rate_plan_prices()

if __name__ == '__main__':
    main()