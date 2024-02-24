from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from monthly_billing_job.models import ContractBillEntry, OrderBillEntry
from monthly_billing_job.services.myadmin import MyAdminPublicAPI
import datetime
import dataclasses
import json
import pprint

class Command(BaseCommand):
    help = 'Run the monthly billing job'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--month',
            nargs='?',
            default=None,
            type=str,
            help='Month for which the report should be run (format MM)',)
        parser.add_argument('--year',
            nargs='?',
            default=None,
            type=str,
            help='Year for which the report should be run (format YYYY)',)
    
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

        # Get the data from the API
        api = MyAdminPublicAPI()
        api.get_company_total(month, year)

        # Save the data to the database
        for _, company_contract in api.company_contracts.items():
            ContractBillEntry.save_all_entries(company_contract.contracts)
            OrderBillEntry.save_all_entries(company_contract.orders)

        self.stdout.write(self.style.SUCCESS('Monthly billing job ran successfully'))

        return export_company_contracts_as_json(api.company_contracts)
        
def export_company_contracts_as_json(company_contracts: dict) -> str:
    """
    Replaces all dataclasses in the company_contracts dictionary with dictionaries and exports the result as a JSON string
    """
    json_contracts = {}

    for company, contract in company_contracts.items():
        json_contract = contract
        json_contracts[company] = json_contract
        json_contract.contracts = [dataclasses.asdict(c) for c in json_contract.contracts]
        json_contract.orders = [dataclasses.asdict(o) for o in json_contract.orders]
        json_contracts[company] = dataclasses.asdict(json_contract)
    
    pprint.pprint(json_contracts)
    return json.dumps(json_contracts)