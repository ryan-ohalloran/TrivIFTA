from typing import Any, List
from django.core.management.base import BaseCommand, CommandParser
from monthly_billing_job.models import ContractBillEntry, OrderBillEntry
from monthly_billing_job.services.myadmin import MyAdminPublicAPI, CompanyContracts, CompanyOrders, DeviceContract
import datetime
import dataclasses
import json
import csv
from io import StringIO
from pprint import pprint

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
        
def export_company_contracts_as_json(company_contracts: dict[str, CompanyContracts]) -> str:
    """
    Replaces all dataclasses in the company_contracts dictionary with dictionaries and exports the result as a JSON string
    """
    json_contracts = {}

    for company, contract in company_contracts.items():
        json_contracts[company] = transform_company_contracts(contract)
    
    pprint(json_contracts)
    return json.dumps(json_contracts)

def orders_to_csv(orders: List[CompanyOrders]) -> str:
    header = CompanyOrders.__annotations__.keys()
    data = [dataclasses.asdict(order) for order in orders]

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=header)
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()

def contracts_to_csv(contracts: List[DeviceContract]) -> str:
    header = DeviceContract.__annotations__.keys()
    data = [dataclasses.asdict(contract) for contract in contracts]

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=header)
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()

def transform_company_contracts(company_contracts: CompanyContracts) -> dict:
    return {
        'company_name': company_contracts.company_name,
        'total_cost': round(company_contracts.total_cost, 2),
        'orders_csv': orders_to_csv(company_contracts.orders),
        'contracts_csv': contracts_to_csv(company_contracts.contracts),
    }