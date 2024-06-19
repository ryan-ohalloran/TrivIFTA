from django.core.management.base import BaseCommand, CommandParser
from monthly_billing_job.models import Quote, QuoteItem, Product, RatePlan, Reseller, User
from monthly_billing_job.services.quoting import QuoteManager
from datetime import date
from pprint import pprint

def test_generate_quotes():
    rate_plans = RatePlan.objects.all()
    # get first 3 products
    products = Product.objects.all()[:3]
    user = User.objects.first()

    quote_manager = QuoteManager(products, rate_plans, user)
    quote = quote_manager.generate_quote(
        customer_name='John Doe',
        customer_email="johndoe123@live.com",
        quote_date=date.today(),
    )

    pprint(quote.__dict__)
    for item in quote.items.all():
        pprint(item)

class Command(BaseCommand):
    help = 'test generation of quotes'

    def handle(self, *args, **options):
        test_generate_quotes()
