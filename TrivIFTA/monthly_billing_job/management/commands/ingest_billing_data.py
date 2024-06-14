from typing import Any, List
from django.core.management.base import BaseCommand, CommandParser
from monthly_billing_job.services.myadmin import MyAdminPublicAPI
import datetime
from monthly_billing_job.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Run the monthly billing job'

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
    
    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> str | None:
        month = int(options['month'])
        year = int(options['year'])

        # ensure month is a digit between 1 and 12
        if month < 1 or month > 12:
            self.stdout.write(self.style.ERROR('Invalid month provided'))
            return
        
        # ensure year is a digit with 4 characters greater than 2000 and less than or equal to the current year
        if  year < 2020 or year > datetime.datetime.now().year:
            self.stdout.write(self.style.ERROR('Invalid year provided'))
            return
        print("Starting billing data ingest...")
        try:
            for user in User.objects.all():
                print(f"User: {user} | Reseller: {user.reseller}")
                api = MyAdminPublicAPI(user=user)
                api.ingest_billing_data(month, year)
                # destroy api object
                del api
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'get_company_total() raised an exception: {e}'))
            return