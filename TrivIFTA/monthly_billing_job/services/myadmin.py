import requests
import json
from pprint import pprint
from typing import List, Dict
import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd
from django.conf import settings
from monthly_billing_job.models import Company, User
from monthly_billing_job.dataclasses import OrderEntry, ContractEntry, CompanyBill
from monthly_billing_job.utils import last_day_of_month


class MyAdminBaseAPI:
    def __init__(self, user: User):
        # if a Reseller does not exist, raise an exception and stop everything
        try:
            self._reseller = user.reseller
        except User.DoesNotExist:
            raise Exception("Reseller does not exist in the database. Please create a Reseller object in the database.")
        self._account_id = user.accounts.first().account_id
        self.base_url = settings.MYADMIN_ENDPOINT
        self._authenticate(user.my_admin_username, user.my_admin_password)
        self._orders_by_company: Dict[Company, List[OrderEntry]] = {}
        self._device_contract_list: List[ContractEntry] = []
        self._serial_nos: List[str] = [] # serial numbers of all devices that had transactions in the given month
        self.company_contracts: Dict[Company, CompanyBill] = {}

    def _send_request(self, method, params):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            "id": -1,  # JSON-RPC ID, can be ignored/set to any negative value
            "method": method,
            "params": params
        }
        response = requests.post(self.base_url, headers=headers, data={"JSON-RPC": json.dumps(payload)})
        if response.status_code != 200:
            raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
        return response.json()


    def _authenticate(self, username: str, password: str) -> None:
        params = {
            "username": username,
            "password": password
        }

        result = self._send_request("Authenticate", params)
        if result["result"] is None:
            raise Exception("Authentication failed")
        
        self._session_id = result["result"]["sessionId"]
        self._api_key = result["result"]["userId"] # API key is the same as the user ID

        print(f"Authenticated as {username} with:\n\tsession ID {self._session_id}\n\tAPI key {self._api_key}\n\tAccount ID {self._account_id}")
    
    def _get_device_contract_transactions(self, month: int, year: int):
        params = {
            "apiKey": self._api_key,
            "forAccount": self._account_id,
            "monthFilter": month,
            "sessionId": self._session_id,
            "yearFilter": year
        }
        self._raw_contract_transactions =  self._send_request("GetDeviceContractTransactions", params)["result"]

    def _set_device_contract_transactions(self, month: int, year: int):  
        self._get_device_contract_transactions(month, year)  
        self._serial_nos = [contract["serialNo"] for contract in self._raw_contract_transactions]
        self._contract_transactions = self._raw_contract_transactions
    
    def _get_device_contracts(self, month: int, year: int):
        params = {
            "apiKey": self._api_key,
            "forAccount": self._account_id,
            "sessionId": self._session_id,
            "serialNos": self._serial_nos,
            "fromDate": datetime.datetime(year, month, 1, 0, 0, 0).isoformat(),
            "toDate": (datetime.datetime(year, month, 1, 0, 0, 0) + relativedelta(months=1)).isoformat(),
        }
        self._raw_device_contracts = self._send_request("GetDeviceContracts", params)["result"]
        
    def _set_device_contracts(self, month: int, year: int):    
        self._get_device_contracts(month, year)
        # Map serial number to contract object
        self._device_contracts = {
            contract["device"]["serialNumber"]: {
                "database":     contract["latestDeviceDatabase"]["databaseName"] if "latestDeviceDatabase" in contract and "databaseName" in contract["latestDeviceDatabase"] else None,
                "vin":          contract["latestDeviceDatabase"]["vin"] if "latestDeviceDatabase" in contract and "vin" in contract["latestDeviceDatabase"] else None,        
                "company_name": contract["userContact"]["userCompany"]["name"] if "userContact" in contract and "userCompany" in contract["userContact"] and "name" in contract["userContact"]["userCompany"] else None,
                "display_name": contract["userContact"]["displayName"] if "userContact" in contract and "displayName" in contract["userContact"] else None,
                "ratePlanName": contract["activeRatePlans"][0]["ratePlan"]["ratePlanName"] if "activeRatePlans" in contract and contract["activeRatePlans"] else "No rate plan found",
                "ratePlanFee":  contract["activeRatePlans"][0]["ratePlan"]["monthlyFee"] if "activeRatePlans" in contract and contract["activeRatePlans"] else None,
                "company_id": contract["userContact"]["id"] if "userContact" in contract and "id" in contract["userContact"] else None,
                "company_street": contract["userContact"]["street1"] if "userContact" in contract and "street1" in contract["userContact"] else None,
                "company_city": contract["userContact"]["city"] if "userContact" in contract and "city" in contract["userContact"] else None,
                "company_state": contract["userContact"]["state"] if "userContact" in contract and "state" in contract["userContact"] else None,
                "company_zip": contract["userContact"]["zipCode"] if "userContact" in contract and "zipCode" in contract["userContact"] else None,
                "company_country": contract["userContact"]["country"] if "userContact" in contract and "country" in contract["userContact"] else None,
                "company_email": contract["userContact"]["contactEmail"] if "userContact" in contract and "contactEmail" in contract["userContact"] else None,
                "company_phone": contract["userContact"]["telephone1"] if "userContact" in contract and "telephone1" in contract["userContact"] else None,
                "company_contact": contract["userContact"]["contactName"] if "userContact" in contract and "contactName" in contract["userContact"] else None,
                "company_info": contract["userContact"] if "userContact" in contract else None,
                "isTerminated": contract["isTerminated"] if "isTerminated" in contract else None,
                "isUnactivated": contract["isUnactivated"] if "isUnactivated" in contract else None,
            }
            for contract in self._raw_device_contracts if contract and contract['isTerminated'] == False and contract['isUnactivated'] == False and "userContact" in contract
        }
    
    def _set_online_device_order_entries(self, month: int, year: int):
        params = {
            "apiKey": self._api_key,
            "forAccount": self._account_id,
            "sessionId": self._session_id,
            "orderDateFrom": datetime.datetime(year, month, 1, 0, 0, 0).isoformat(),
            "orderDateTo": (datetime.datetime(year, month, 1, 0, 0, 0) + relativedelta(months=1)).isoformat(),
        }
        self._device_online_order_entries = self._send_request("GetOnlineOrderStatus", params)["result"]

    def _ensure_companies_exist(self):
        if not self._reseller:
            raise Exception("Reseller does not exist. Cannot create companies without a reseller.")

        # Collect company data from contracts
        contract_company_data = {
            contract["company_id"]: {
                "name": contract["company_name"],
                "active": not contract.get("isTerminated", False),
                "display_name": contract["display_name"],
                "street_address": contract["company_street"],
                "city": contract["company_city"],
                "state": contract["company_state"],
                "zip_code": contract["company_zip"],
                "country": contract["company_country"],
                "contact_email": contract["company_email"],
                "contact_phone": contract["company_phone"],
                "contact_name": contract["company_contact"]
            }
            for contract in self._device_contracts.values() if contract["company_id"]
        }

        # Collect company data from orders
        order_company_data = {
            order["shippingContact"]["userCompany"]["id"]: {
                "name": order["shippingContact"]["userCompany"]["name"],
                "active": True,  # Assuming orders are from active companies
                "display_name": order["shippingContact"]["userCompany"]["name"],
                "street_address": order["shippingContact"].get("street1"),
                "city": order["shippingContact"].get("city"),
                "state": order["shippingContact"].get("state"),
                "zip_code": order["shippingContact"].get("zipCode"),
                "country": order["shippingContact"].get("country"),
                "contact_email": order["shippingContact"].get("contactEmail"),
                "contact_phone": order["shippingContact"].get("telephone1"),
                "contact_name": order["shippingContact"].get("contactName")
            }
            for order in self._device_online_order_entries if order["shippingContact"]["userCompany"]["id"]
        }

        # Combine both contract and order company data
        company_data = {**contract_company_data, **order_company_data}

        for company_id, data in company_data.items():
            Company.objects.update_or_create(
                company_id=company_id,
                defaults={
                    "name": data["name"],
                    "active": data["active"],
                    "display_name": data["display_name"],
                    "reseller": self._reseller,
                    "street_address": data["street_address"],
                    "city": data["city"],
                    "state": data["state"],
                    "zip_code": data["zip_code"],
                    "country": data["country"],
                    "contact_email": data["contact_email"],
                    "contact_phone": data["contact_phone"],
                    "contact_name": data["contact_name"],
                }
            )
    
    def _populate_all_data(self, month: int, year: int):
        '''
        Facilitates requests and populates all data for given month and year 
        '''
        # Ensure all data is populated
        self._set_device_contract_transactions(month, year)
        self._set_device_contracts(month, year)
        self._set_online_device_order_entries(month, year)
        # Ensure companies exist in the database
        self._ensure_companies_exist()

    def _set_all_device_contracts(self, month: int, year: int):
        '''
        Returns a list of Contract objects representing device contracts for the given month and year.
        '''
        for contract in self._contract_transactions:
            if contract["serialNo"] in self._device_contracts:
                device_contract_info = self._device_contracts[contract["serialNo"]]

                company = Company.get_company_by_id(device_contract_info["company_id"])
                if company is None:
                    raise Exception(f'Company with ID {device_contract_info["company_id"]} does not exist for this contract: {contract}.')

                device_contract = ContractEntry(
                    serial_no=contract["serialNo"],
                    vin=device_contract_info["vin"],
                    database=device_contract_info["database"],
                    assigned_po=contract.get("assignedPurchaseOrderNo"),
                    bill_days=(parse(contract["periodTo"]) - parse(contract["periodFrom"])).days if "periodTo" in contract and "periodFrom" in contract else None,
                    billing_days=contract.get("quantityInDays"),
                    total_cost=contract.get("valueUsd"),
                    rate_plan_name=device_contract_info["ratePlanName"],
                    rate_plan_fee=device_contract_info["ratePlanFee"],
                    company=company,
                    period_from=contract.get("periodFrom") if "periodFrom" in contract else None,
                    period_to=contract.get("periodTo") if "periodTo" in contract else None,
                    # TODO: implement actual logic for customer cost
                    customer_cost=contract.get("valueUsd")
                )
                self._device_contract_list.append(device_contract)
                
                # Save to database
                device_contract.save_to_db()

    
    def _set_orders_by_company(self, month: int, year: int):
        '''
        Populate mapping of Company to List[OrderEntry] for the given month and year
            - Also saves orders to the database
        '''
        for entry in self._device_online_order_entries:
            company_id = entry["shippingContact"]["userCompany"]["id"] if "shippingContact" in entry and "userCompany" in entry["shippingContact"] and "id" in entry["shippingContact"]["userCompany"] else None
            company_name = entry["shippingContact"]["userCompany"]["name"] if "shippingContact" in entry and "userCompany" in entry["shippingContact"] and "name" in entry["shippingContact"]["userCompany"] else None
            if company_id and company_name:
                company = Company.get_company_by_id(company_id)
                if company is None:
                    raise Exception(f'Company with ID {company_id} does not exist for this order.')

                order_info = OrderEntry(
                    po_number=entry.get("purchaseOrderNo"),
                    current_status=entry.get("currentStatus"),
                    placed_by=entry.get("orderedBy"),
                    shipping_address=entry["shippingContact"].get("address") if "shippingContact" in entry else None,
                    order_date=entry.get("orderDate"),
                    item_cost=entry.get("orderTotalLocal"),
                    shipping_cost=entry.get("shippingCost"),
                    order_total=entry.get("orderTotalLocal") + entry.get("shippingCost") if "orderTotalLocal" in entry and "shippingCost" in entry else None,
                    order_number=entry["orderNo"],
                    company=company,
                    # TODO: implement actual logic for customer cost
                    customer_cost=entry.get("orderTotalLocal") + entry.get("shippingCost") if "orderTotalLocal" in entry and "shippingCost" in entry else None
                )
                if company in self._orders_by_company:
                    self._orders_by_company[company].append(order_info)
                else:
                    self._orders_by_company[company] = [order_info]
                    
                # Save to database
                order_info.save_to_db()


    def _prepare_billing_data(self, month: int, year: int):
        '''
        Everything needed to ingest billing data for the given month and year
            - does not compute total cost for each company or generate a bill
        '''
        self._populate_all_data(month, year)
        self._set_all_device_contracts(month, year)
        self._set_orders_by_company(month, year)
                
    def _set_device_contracts_by_company(self, month: int, year: int):
        '''
        Creates a dictionary of CompanyBill objects for each company for the given month and year
        '''
        self._prepare_billing_data(month, year)

        for contract in self._device_contract_list:
            company = contract.company
            if company not in self.company_contracts:
                self.company_contracts[company] = CompanyBill(company, contract.company.display_name, [], [])
            self.company_contracts[company].contracts.append(contract)
        return self.company_contracts
    
    def _set_all_customer_costs(self, month: int, year: int):
        '''
        Sets a dictionary of cost breakdowns for each customer for the given month and year
        '''
        self._set_device_contracts_by_company(month, year)
        
        # join all order information for each company into company_contracts
        for company, orders in self._orders_by_company.items():
            if company in self.company_contracts:
                self.company_contracts[company].orders = orders
            else:
                # if an order exists for a company that has no contracts, create a CompanyBill object for that company
                self.company_contracts[company] = CompanyBill(company=company, display_name=orders[0].company.display_name, orders=orders, contracts=[])

class MyAdminPublicAPI(MyAdminBaseAPI):    
    def ingest_billing_data(self, month: int, year: int):
        '''
        Saves all data for the given month and year to the database
            - Saves/updates all Company, Contract, and Order objects
        '''
        self._prepare_billing_data(month, year)
        print(f"Data Ingested Successfully for {month}/{year}")

    def generate_monthly_bills(self, month: int, year: int):
        '''
        Compute total cost for each company for the given month and year and generates a bill for each company
            - Also performs the same operations as ingest_billing_data
        '''
        self._prepare_billing_data(month, year)
        self._set_all_customer_costs(month, year)

        for company, company_bill in self.company_contracts.items():
            total_cost = 0
            for contract in company_bill.contracts:
                total_cost += contract.total_cost
            for order in company_bill.orders:
                total_cost += order.order_total
            self.company_contracts[company].total_cost = total_cost

        # save all CompanyBill objects to the database
        period_from = datetime.date(year, month, 1)
        period_to = datetime.date(year, month, last_day_of_month(month, year))
        for company_bill in self.company_contracts.values():
            company_bill.save_to_db(period_from, period_to)

        print("Company Total Costs:")
        for company, company_bill in self.company_contracts.items():
            print(f"{company_bill.company.display_name}: ${company_bill.total_cost}")