from monthly_billing_job.models import Quote, QuoteItem, Product, RatePlan, Reseller, User, CompanyType
from monthly_billing_job.services.billing import BillingManager
from typing import List
from datetime import date

class QuoteManager:
    def __init__(self, products: List[Product], rate_plans: List[RatePlan], user: User):
        self.products = products
        self.rate_plans = rate_plans
        self.company_type = CompanyType.objects.get(type_name='default')
        self.billing_manager = BillingManager(company_type=self.company_type, reseller=user.reseller)
        self.reseller = user.reseller
    
    def generate_quote(self, customer_name: str, customer_email: str, quote_date: date) -> Quote:
        quote = Quote.objects.create(
            reseller=self.reseller,
            customer_name=customer_name,
            customer_email=customer_email,
            quote_date=quote_date,
            total_cost=0.0
        )
        total_cost = 0.0
        # set quote items for products and rate plans 
        for product in self.products:
            price = self.billing_manager.get_product_price(product)
            total_cost += price
            quote_item = QuoteItem.objects.create(
                quote=quote,
                product=product,
                price=price
            )
        for rate_plan in self.rate_plans:
            price = self.billing_manager.get_rate_plan_price(rate_plan)
            total_cost += price
            quote_item = QuoteItem.objects.create(
                quote=quote,
                rate_plan=rate_plan,
                price=price
            )
        quote.total_cost = total_cost
        quote.save()
        return quote

    