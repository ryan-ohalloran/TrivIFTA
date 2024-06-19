import requests
import json
from pprint import pprint
from typing import List, Dict, Set
import datetime
from dateutil.parser import parse
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import pandas as pd
from django.conf import settings
from monthly_billing_job.models import Company, User, RatePlan, CompanyType
from monthly_billing_job.dataclasses import OrderEntry, ContractEntry, CompanyBill, OrderItemEntry, ShipItemEntry, ProductEntry, RatePlanEntry
from monthly_billing_job.utils import last_day_of_month
from monthly_billing_job.services.billing import BillingManager


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

        # print(f"Authenticated as {username} with:\n\tsession ID {self._session_id}\n\tAPI key {self._api_key}\n\tAccount ID {self._account_id}")
    
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
        
    def _get_product_data(self, month: int, year):
        params = {
            "apiKey": self._api_key,
            "forAccount": self._account_id,
            "sessionId": self._session_id,
        }
        self._product_data = self._send_request("GetAvailableProducts", params)["result"]

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

    def _ensure_rate_plans_exist(self):
        date = timezone.now()
        # Add/update rate plans to database
        for contract in self._device_contracts.values():
            rate_plan = RatePlanEntry(
                name=contract["ratePlanName"],
                monthly_fee=contract["ratePlanFee"],
                reseller=self._reseller,
                month_and_year=date.strftime("%Y-%m")
            )
            rate_plan.save_to_db()

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
            
            # Check if this company already exists
            company = Company.get_company_by_id(company_id)
            if company is None:
                company_type = CompanyType.objects.filter(type_name='default').first()
            else:
                company_type = company.company_type

            company, created = Company.objects.update_or_create(
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
                    "company_type": company_type,
                }
            )
    
    def _ensure_products_exist(self, month: int, year: int):
        self._get_product_data(month, year)
        
        # Track updated product codes
        updated_product_codes = set()

        for product_data in self._product_data:
            product_entry = ProductEntry(
                product_code=product_data['code'],
                name=product_data['name'] if 'name' in product_data else None,
                price=product_data['pricings'][0]['purchasePrice'] if 'pricings' in product_data and product_data['pricings'] else None,
                mrsp_price=product_data['pricings'][0]['msrpPurchasePrice'] if 'pricings' in product_data and product_data['pricings'] else None,
                category=product_data['productCategory']['name'] if 'productCategory' in product_data else None,
                last_updated=parse(product_data['asAtDate']) if 'asAtDate' in product_data else timezone.now(),
            )

            product_entry.save_to_db()
            # Mark this product as updated
            updated_product_codes.add(product_data['code'])

        # Deactivate products not updated in the last 14 days or not found in the API data
        ProductEntry.deactivate_old_products(threshold_days=14, updated_product_codes=updated_product_codes)

    
    def _populate_all_data(self, month: int, year: int):
        '''
        Facilitates requests and populates all data for given month and year 
        '''
        # Ensure all data is populated
        self._set_device_contract_transactions(month, year)
        self._set_device_contracts(month, year)
        self._set_online_device_order_entries(month, year)
        # Ensure rate plans, companies, and products exist in the database
        self._ensure_rate_plans_exist()
        self._ensure_companies_exist()
        self._ensure_products_exist(month, year)

    def _set_all_device_contracts(self, month: int, year: int):
        '''
        Returns a list of Contract objects representing device contracts for the given month and year.
        '''
        for contract in self._contract_transactions:
            if contract["serialNo"] in self._device_contracts:
                device_contract_info = self._device_contracts[contract["serialNo"]]

                company = Company.get_company_by_id(device_contract_info["company_id"])
                if company is None:
                    raise Exception(f'Exception in MyAdminAPI._set_all_device_contracts\nCompany with ID {device_contract_info["company_id"]} does not exist for this contract: {contract}.')

                rate_plan = RatePlan.get_rate_plan_by_name_and_reseller(device_contract_info["ratePlanName"], self._reseller)
                if rate_plan is None:
                    raise Exception(f'Exception in MyAdminAPI._set_all_device_contracts\nRate Plan with name {device_contract_info["ratePlanName"]} does not exist for this contract: {contract}.')
                
                billing_manager = BillingManager(company.company_type, self._reseller)
                customer_cost = billing_manager.get_rate_plan_price(rate_plan)

                days_in_month = last_day_of_month(year=year, month=month)
                total_customer_cost = customer_cost * (contract.get("quantityInDays", 0) / days_in_month)

                start_time = parse(contract["periodFrom"]) if "periodFrom" in contract else None
                end_time = parse(contract["periodTo"]) if "periodTo" in contract else None

                device_contract = ContractEntry(
                    serial_no=contract["serialNo"],
                    vin=device_contract_info["vin"],
                    database=device_contract_info["database"],
                    assigned_po=contract.get("assignedPurchaseOrderNo"),
                    bill_days=(parse(contract["periodTo"]) - parse(contract["periodFrom"])).days if "periodTo" in contract and "periodFrom" in contract else None,
                    billing_days=contract.get("quantityInDays"),
                    total_cost=contract.get("valueUsd"),
                    rate_plan=rate_plan,
                    company=company,
                    month=month,
                    year=year,
                    customer_cost=customer_cost,
                    total_customer_cost=total_customer_cost,
                    start_time=start_time,
                    end_time=end_time,
                )
                self._device_contract_list.append(device_contract)
                device_contract.save_to_db()
    
    def _set_orders_by_company(self, month: int, year: int):
        '''
        Populate mapping of Company to List[OrderEntry] for the given month and year
            - Also saves Order, OrderItemEntry, and ShipItemEntry objects to the database
        '''
        for entry in self._device_online_order_entries:
            company_id = entry["shippingContact"]["userCompany"]["id"] if "shippingContact" in entry and "userCompany" in entry["shippingContact"] and "id" in entry["shippingContact"]["userCompany"] else None
            company_name = entry["shippingContact"]["userCompany"]["name"] if "shippingContact" in entry and "userCompany" in entry["shippingContact"] and "name" in entry["shippingContact"]["userCompany"] else None
            
            if company_id and company_name:
                company = Company.get_company_by_id(company_id)
                if company is None:
                    raise Exception(f'Company with ID {company_id} does not exist for this order.')

                billing_manager = BillingManager(company.company_type, self._reseller)

                # Initialize total customer cost
                total_customer_cost = 0

                # Calculate total customer cost for the order items
                for item in entry.get("onlineOrderItems", []):
                    # Find product code in product data
                    product_code = item.get("productCode")
                    product = ProductEntry.get_product_by_code(product_code)

                    if product is None:
                        # Create a new ProductEntry with available information
                        product_entry = ProductEntry(
                            product_code=product_code,
                            name=item.get('productDescription', 'Unknown Product'),
                            price=item.get('unitCost', 0),
                            mrsp_price=item.get('monthlyCost', 0),
                            category='Unknown',
                            last_updated=timezone.now(),
                            active=False
                        )
                        product = product_entry.save_to_db()
                        print(f"Created missing product with code {product_code}.")

                    customer_cost = billing_manager.get_product_price(product) * item.get("quantity", 0)
                    total_customer_cost += customer_cost

                # Add shipping cost to total customer cost
                shipping_cost = entry.get("shippingCost", 0)
                total_customer_cost += shipping_cost

                # Create and save the OrderEntry with the calculated customer cost
                order_info = OrderEntry(
                    po_number=entry.get("purchaseOrderNo"),
                    current_status=entry.get("currentStatus"),
                    placed_by=entry.get("orderedBy"),
                    shipping_address=entry["shippingContact"].get("address") if "shippingContact" in entry else None,
                    order_date=entry.get("orderDate"),
                    item_cost=entry.get("orderTotalLocal"),
                    shipping_cost=shipping_cost,
                    order_total=entry.get("orderTotalLocal") + shipping_cost if "orderTotalLocal" in entry and "shippingCost" in entry else None,
                    order_number=entry["orderNo"],
                    company=company,
                    customer_cost=total_customer_cost,
                    comment=entry.get("comment"),
                )
                if company in self._orders_by_company:
                    self._orders_by_company[company].append(order_info)
                else:
                    self._orders_by_company[company] = [order_info]

                # Ensure order is saved
                order = order_info.save_to_db()

                # Create and save OrderItemEntry objects
                for item in entry.get("onlineOrderItems", []):
                    # Find product code in product data
                    product_code = item.get("productCode")
                    product = ProductEntry.get_product_by_code(product_code)

                    if product is None:
                        # Create a new ProductEntry with available information
                        product_entry = ProductEntry(
                            product_code=product_code,
                            name=item.get('productDescription', 'Unknown Product'),
                            price=item.get('unitCost', 0),
                            mrsp_price=item.get('monthlyCost', 0),
                            category='Unknown',
                            last_updated=timezone.now(),
                            active=False
                        )
                        product = product_entry.save_to_db()
                        print(f"Created missing product with code {product_code}.")

                    customer_cost = billing_manager.get_product_price(product)

                    order_item_entry = OrderItemEntry(
                        order=order,
                        product=product,
                        device_id=item["devicePlan"].get("deviceId") if "devicePlan" in item else None,
                        device_plan_name=item["devicePlan"].get("devicePlanName") if "devicePlan" in item else None,
                        quantity=item.get("quantity", 0),
                        unit_cost=customer_cost,
                    )
                    order_item_entry.save_to_db()

                # Create and save ShipItemEntry objects
                for ship_item in entry.get("shipItems", []):
                    ship_item_entry = ShipItemEntry(
                        order=order,
                        tracking_number=ship_item.get("trackingNo"),
                        tracking_url=ship_item.get("trackingURL"),
                        erp_reference=ship_item.get("erpReference"),
                        purchase_order_no=ship_item.get("purchaseOrderNo"),
                    )
                    ship_item_entry.save_to_db()

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
                self.company_contracts[company] = CompanyBill(company, company.display_name, [], [])
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
    def populate_data(self, month: int, year: int):
        '''
        Populates all data for the given month and year
        '''
        self._populate_all_data(month, year)
        print(f"Data Populated Successfully for {month}/{year}")

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
        self._set_all_customer_costs(month, year)

        for company, company_bill in self.company_contracts.items():
            total_bill_cost, total_expense_cost = 0.0, 0.0
            for contract in company_bill.contracts:
                total_bill_cost += contract.total_customer_cost
                total_expense_cost += contract.total_cost
            for order in company_bill.orders:
                total_bill_cost += order.customer_cost
                total_expense_cost += order.order_total
            self.company_contracts[company].total_bill_cost = total_bill_cost
            self.company_contracts[company].total_expense_cost = total_expense_cost

        # save all CompanyBill objects to the database
        period_from = datetime.date(year, month, 1)
        period_to = datetime.date(year, month, last_day_of_month(year=year, month=month))
        for company_bill in self.company_contracts.values():
            company_bill.save_to_db(period_from, period_to)

        print("Company Total Costs:")
        for company, company_bill in self.company_contracts.items():
            print(f"{company_bill.company.display_name} - Bill: ${company_bill.total_bill_cost} | Expense: ${company_bill.total_expense_cost}")