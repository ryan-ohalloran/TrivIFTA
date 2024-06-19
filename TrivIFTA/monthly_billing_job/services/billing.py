from monthly_billing_job.models import PricingTier, FlatMarkup, SourcewellProductPricing, SourcewellRatePlanPricing, CompanyType, Product, RatePlan, Reseller

class BillingManager:
    def __init__(self, company_type: CompanyType, reseller: Reseller):
        self.company_type = company_type
        self.reseller = reseller
    
    def get_product_price(self, product: Product) -> float:
        price = product.price

        if self.company_type.type_name == 'internal':
            flat_markup = FlatMarkup.objects.get(reseller=self.reseller, company_type=self.company_type)
            price += flat_markup.markup_amount
        elif self.company_type.type_name == 'sourcewell':
            print(f"Getting product price for sourcewell company type {self.company_type}")
            try:
                sourcewell_pricing = SourcewellProductPricing.objects.get(reseller=self.reseller, product=product)
                print(f"Sourcewell pricing found for product {product} | {sourcewell_pricing}")
                price = sourcewell_pricing.price
                print(f"Price after sourcewell pricing: {price}")
            except SourcewellProductPricing.DoesNotExist:
                print(f"Sourcewell pricing not found for product {product}")
                print(f"Price before sourcewell pricing: {price}")
                print(f"Product category {product.category}")
                print(f"MSRP Price {product.mrsp_price}")
                pass
        elif self.company_type.type_name == 'default':
            pricing_tiers = PricingTier.objects.filter(reseller=self.reseller)
            for tier in pricing_tiers:
                if tier.min_price <= price < tier.max_price:
                    price += price * (tier.markup_percentage / 100)
                    break
        else:
            raise Exception(f"Invalid company type {self.company_type.type_name}")
        
        return price
    
    def get_rate_plan_price(self, rate_plan: RatePlan) -> float:
        price = rate_plan.default_customer_fee
        
        if self.company_type.type_name == 'internal':
            # internal companies pay a rate of the monthly fee plus a flat markup
            price = rate_plan.monthly_fee
            flat_markup = FlatMarkup.objects.get(reseller=self.reseller, company_type=self.company_type)
            price += flat_markup.markup_amount
        elif self.company_type.type_name == 'sourcewell':
            try:
                sourcewell_pricing = SourcewellRatePlanPricing.objects.get(reseller=self.reseller, rate_plan=rate_plan)
                price = sourcewell_pricing.price
            except SourcewellRatePlanPricing.DoesNotExist:
                pass
                # raise Exception(f"SourcewellRatePlanPricing not found for reseller {self.reseller} and rate plan {rate_plan}")
        elif self.company_type.type_name == 'default':
            # price is same as default customer fee
            pass
        else:
            raise Exception(f"Invalid company type {self.company_type.type_name}")
        
        return price