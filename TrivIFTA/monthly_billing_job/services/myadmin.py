import requests
import json
from pprint import pprint
from typing import List
import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd
from django.conf import settings


class MyAdminBaseAPI:
    def __init__(self):
        self.base_url = "https://myadminapi.geotab.com/v2/MyAdminApi.ashx"
        self._authenticate(settings.MYADMIN_USERNAME, settings.MYADMIN_PASSWORD)
        self.orders_by_company = None
        self.company_contracts = None

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
        self.account_id = result["result"]["accounts"][0]["accountId"]
        print(f"Authenticated as {username} with:\n\tsession ID {self._session_id}\n\tAPI key {self._api_key}\n\tAccount ID {self.account_id}")
    
    def _get_device_contract_transactions(self, month: int, year: int):
        params = {
            "apiKey": self._api_key,
            "forAccount": self.account_id,
            "monthFilter": month,
            "sessionId": self._session_id,
            "yearFilter": year
        }
        contract_transactions =  self._send_request("GetDeviceContractTransactions", params)["result"]
        self._serial_nos = [contract["serialNo"] for contract in contract_transactions]
        self._contract_transactions = contract_transactions
    
    def _get_device_contracts(self, month: int, year: int):
        params = {
            "apiKey": self._api_key,
            "forAccount": self.account_id,
            "sessionId": self._session_id,
            "serialNos": self._serial_nos,
            "fromDate": datetime.datetime(year, month, 1, 0, 0, 0).isoformat(),
            "toDate": (datetime.datetime(year, month, 1, 0, 0, 0) + relativedelta(months=1)).isoformat(),
        }
        device_contracts = self._send_request("GetDeviceContracts", params)["result"]
        
        # Map serial number to contract object
        self._device_contracts = {
            contract["device"]["serialNumber"]: {
                "database":     contract["latestDeviceDatabase"]["databaseName"] if "latestDeviceDatabase" in contract and "databaseName" in contract["latestDeviceDatabase"] else None,
                "vin":          contract["latestDeviceDatabase"]["vin"] if "latestDeviceDatabase" in contract and "vin" in contract["latestDeviceDatabase"] else None,        
                "company_name": contract["userContact"]["userCompany"]["name"] if "userContact" in contract and "userCompany" in contract["userContact"] and "name" in contract["userContact"]["userCompany"] else None,
                "display_name": contract["userContact"]["displayName"] if "userContact" in contract and "displayName" in contract["userContact"] else None,
            }
            for contract in device_contracts if contract
        }
    
    def _get_all_device_contracts(self, month: int, year: int):
        '''
        Returns a list of objects representing device contracts for the given month and year
            "serial_no": str,
            "vin": str,
            "database": str,
            "assigned_po": str,
            "bill_days": int,
            "billing_days": float,
            "unit_cost": float,
            "total_cost": float,
            "company_name": str,
            "display_name": str.
        '''
        self._get_device_contract_transactions(month, year)
        self._get_device_contracts(month, year)
        
        self._device_contracts = [{
            "serial_no": contract["serialNo"],
            "vin": self._device_contracts[contract["serialNo"]]["vin"],
            "database": self._device_contracts[contract["serialNo"]]["database"],
            "assigned_po": contract["assignedPurchaseOrderNo"] if "assignedPurchaseOrderNo" in contract else None,
            "bill_days": (parse(contract["periodTo"]) - parse(contract["periodFrom"])).days if "periodTo" in contract and "periodFrom" in contract else None,
            "billing_days": contract["quantityInDays"] if "quantityInDays" in contract else None,
            "total_cost": contract["valueUsd"] if "valueUsd" in contract else None,
            "company_name": self._device_contracts[contract["serialNo"]]["company_name"],
            "display_name": self._device_contracts[contract["serialNo"]]["display_name"],
        } for contract in self._contract_transactions if contract["serialNo"] in self._device_contracts]

        return self._device_contracts
    
    def _get_device_contracts_by_company_df(self, month: int, year: int):
        '''
        Returns a dataframe of objects representing device contracts for the given month and year
        '''
        company_contracts = self.get_device_contracts_by_company(month, year)
        all_contracts = [contract for company in company_contracts.values() for contract in company["contracts"]]
        df = pd.DataFrame(all_contracts)
        return df
    
    def _get_online_device_order_entries(self, month: int, year: int):
        params = {
            "apiKey": self._api_key,
            "forAccount": self.account_id,
            "sessionId": self._session_id,
            "orderDateFrom": datetime.datetime(year, month, 1, 0, 0, 0).isoformat(),
            "orderDateTo": (datetime.datetime(year, month, 1, 0, 0, 0) + relativedelta(months=1)).isoformat(),
        }
        self._device_online_order_entries = self._send_request("GetOnlineOrderStatus", params)["result"]

class MyAdminPublicAPI(MyAdminBaseAPI):
    def get_device_contracts_by_company(self, month: int, year: int):
        '''
        Returns a dictionary of lists of objects representing device contracts for the given month and year
            "company_name": str,
            "display_name": str,
            "contracts": List[{
                "serial_no": str,
                "vin": str,
                "database": str,
                "assigned_po": str,
                "bill_days": int,
                "billing_days": float,
                "unit_cost": float,
                "total_cost": float,
            }]
        '''
        self._get_device_contract_transactions(month, year)
        self._get_device_contracts(month, year)
        self._get_all_device_contracts(month, year)

        self.company_contracts = {}
        for contract in self._device_contracts:
            company_name = contract["company_name"]
            if company_name not in self.company_contracts:
                self.company_contracts[company_name] = {
                    "company_name": company_name,
                    "display_name": contract["display_name"],
                    "contracts": []
                }
            self.company_contracts[company_name]["contracts"].append(contract)
        return self.company_contracts
    
    def export_device_contracts_by_company(self, month: int, year: int, filename: str):
        '''
        Exports a dataframe of objects representing device contracts for the given month and year to a CSV file
        '''
        df = self._get_device_contracts_by_company_df(month, year)
        df.to_csv(filename, index=False)
        print(f"Exported device contracts to {filename}")
    
    def get_online_device_order_entries(self, month: int, year: int):
        '''
        Returns a list of objects representing online device order entries for the given month and year
            "po_number": str,
            "current_status": str,
            "placed_by": str,
            "shipping_address": str,
            "order_date": str,
            "item_cost": float,
            "shipping_cost": float,
            "order_total": float, (item_cost + shipping_cost)
            "order_number": str,
            "company_name": str,
        '''
        self._get_online_device_order_entries(month, year)

        self.orders_by_company = {}
        for entry in self._device_online_order_entries:
            company_name = entry["shippingContact"]["userCompany"]["name"] if "shippingContact" in entry and "userCompany" in entry["shippingContact"] and "name" in entry["shippingContact"]["userCompany"] else None
            order_info = {
                "po_number": entry["purchaseOrderNo"] if "purchaseOrderNo" in entry else None,
                "current_status": entry["currentStatus"] if "currentStatus" in entry else None,
                "placed_by": entry["orderedBy"] if "orderedBy" in entry else None,
                "shipping_address": entry["shippingContact"]["address"] if "shippingContact" in entry and "address" in entry["shippingContact"] else None,
                "order_date": entry["orderDate"] if "orderDate" in entry else None,
                "item_cost": entry["orderTotalLocal"] if "orderTotalLocal" in entry else None,
                "shipping_cost": entry["shippingCost"] if "shippingCost" in entry else None,
                "order_total": entry["orderTotalLocal"] + entry["shippingCost"] if "orderTotalLocal" in entry and "shippingCost" in entry else None,
                "order_number": entry["orderNo"],
            }
            if company_name in self.orders_by_company:
                self.orders_by_company[company_name].append(order_info)
            else:
                self.orders_by_company[company_name] = [order_info]    

    def join_all_customer_costs(self, month: int, year: int):
        '''
        Returns a dictionary of total costs for each customer for the given month and year
            "company_name": str,
            "total_cost": float,
        '''
        self.get_device_contracts_by_company(month, year)
        self.get_online_device_order_entries(month, year)
        
        # join all order information for each company into company_contracts
        for company_name, orders in self.orders_by_company.items():
            if company_name in self.company_contracts:
                self.company_contracts[company_name]["orders"] = orders
            else:
                self.company_contracts[company_name] = {"company_name": company_name, "orders": orders, "contracts": []}

        pprint(self.company_contracts['Landmark'])

#TODO: get everything into a database
#TODO: determine how best to store upcharged prices
#TODO: set up command to call this function
#TODO: integrate with overall backend (settings.py, urls.py, etc.)
#TODO: integrate with Heroku and set up job to run this on monthly basis
#TODO: set up front-end to display this information
#TODO: set up API endpoints the front-end can consume to display this information

# Example usage
my_admin_api = MyAdminPublicAPI()
# contracts_by_company = my_admin_api.get_device_contracts_by_company(12, 2023)

# my_admin_api.export_device_contracts_by_company(12, 2023, "device_contracts.csv")
my_admin_api.join_all_customer_costs(12, 2023)

