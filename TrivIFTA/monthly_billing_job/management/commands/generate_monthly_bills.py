# generate_monthly_bills.py
from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from monthly_billing_job.services.myadmin import MyAdminPublicAPI
import datetime
from monthly_billing_job.models import User

class Command(BaseCommand):
    help = 'Run the monthly bill generation job'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--month',
            nargs='?',
            required=True,
            default=None,
            type=str,
            help='Month for which the report should be run (format MM)',)
        parser.add_argument('--year',
            nargs='?',
            required=True,
            default=None,
            type=str,
            help='Year for which the report should be run (format YYYY)',)
        
    def handle(self, *args: Any, **options: Any) -> str | None:
        month = int(options['month'])
        year = int(options['year'])

        if month < 1 or month > 12:
            self.stdout.write(self.style.ERROR('Invalid month provided'))
            return
        
        if year < 2020 or year > datetime.datetime.now().year:
            self.stdout.write(self.style.ERROR('Invalid year provided'))
            return

        print("Starting monthly bill generation...")
        try:
            for user in User.objects.all():
                print(f"User: {user} | Reseller: {user.reseller}")
                api = MyAdminPublicAPI(user=user)
                api.generate_monthly_bills(month, year)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'generate_monthly_bills() raised an exception: {e}'))
            return
