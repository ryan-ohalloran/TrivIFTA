from django.test import TestCase
from monthly_billing_job.services.myadmin import MyAdminPublicAPI
from monthly_billing_job.models import Reseller, Account, Pricing, Company, Contract, Order, Bill, BillItemBase, User, ContractBillItem, OrderBillItem
from monthly_billing_job.dataclasses import ContractEntry, OrderEntry, CompanyBill
from datetime import date
from monthly_billing_job.utils import save_all_contracts, save_all_orders
from pprint import pprint
from django.conf import settings
from rest_framework.test import APIClient
from unittest import skip
import requests

# @skip("Run the development server to use this test case class")
class CompanyBillsAPITestCase(TestCase):
    '''
    Run the development server to use this test case
    '''
    def test_get_company_bills(self):
        response = requests.get('http://127.0.0.1:8000/billing/bills/2023/12')

        self.assertEqual(response.status_code, 200)

        try:
            data = response.json()
            pprint(data)
        except requests.exceptions.JSONDecodeError as e:
            print("Failed to decode JSON response")
            print(response.text)

class MyAdminPublicAPITestCase(TestCase):
    def setUp(self) -> None:
        # Create a Reseller
        self.reseller = Reseller.objects.create(
            name='Test Reseller',
            address='123 Reseller St',
            contact_email='reseller@example.com',
            contact_phone='555-1234'
        )
        
        # Create a User with my_admin_username
        self.user = User.objects.create_user(
            username='user1',
            email=settings.MYADMIN_USERNAME,
            reseller=self.reseller,
            first_name='User',
            last_name='One',
            my_admin_username=settings.MYADMIN_USERNAME,
            my_admin_password=settings.MYADMIN_PASSWORD
        )        

        # Create an Account for this user
        self.account = Account.objects.create(account_id='OHAL01')
        self.account.users.add(self.user)

    def test_data_pipeline(self) -> None:
        try:
            for user in User.objects.all():
                print(f"User: {user} | Reseller: {user.reseller}")
                api = MyAdminPublicAPI(user=user)
                api.ingest_billing_data(12, 2023)
                # destroy api object
                del api

            self.assertTrue(True)
        except Exception as e:
            self.fail(f'get_company_total() raised an exception: {e}')
    
# class BillingSystemTest(TestCase):
#     def setUp(self):
#         # Create a Reseller
#         self.reseller = Reseller.objects.create(
#             name='Test Reseller',
#             address='123 Reseller St',
#             contact_email='reseller@example.com',
#             contact_phone='555-1234'
#         )
        
#         # Create Users
#         self.user1 = User.objects.create_user(
#             username='user1',
#             email='user1@example.com',
#             password='password',
#             reseller=self.reseller,
#             first_name='User',
#             last_name='One'
#         )

#         self.user2 = User.objects.create_user(
#             username='user2',
#             email='user2@example.com',
#             password='password',
#             reseller=self.reseller,
#             first_name='User',
#             last_name='Two'
#         )

#         # Create Pricing
#         self.pricing = Pricing.objects.create(
#             company_type='default',
#             markup_rate=1.2
#         )
        
#         # Create a Company
#         self.company = Company.objects.create(
#             company_id=1,
#             name='Test Company',
#             display_name='Test Company Display Name',
#             reseller=self.reseller,
#             street_address='456 Company St',
#             city='City',
#             state='ST',
#             zip_code='12345',
#             country='Country',
#             contact_email='company@example.com',
#             contact_phone='555-5678',
#             contact_name='John Doe',
#             company_type='default'
#         )
        
#         # Create Contracts
#         self.contract1 = Contract.objects.create(
#             company=self.company,
#             serial_no='ABC123',
#             vin='1HGCM82633A123456',
#             database='DB1',
#             assigned_po='PO123',
#             bill_days=30,
#             billing_days=30.0,
#             total_cost=100.0,
#             rate_plan_name='Basic Plan',
#             rate_plan_fee=10.0,
#             period_from=date(2023, 1, 1),
#             period_to=date(2023, 1, 31),
#             customer_cost=120.0
#         )
        
#         self.contract2 = Contract.objects.create(
#             company=self.company,
#             serial_no='DEF456',
#             vin='1HGCM82633A654321',
#             database='DB2',
#             assigned_po='PO456',
#             bill_days=30,
#             billing_days=30.0,
#             total_cost=150.0,
#             rate_plan_name='Premium Plan',
#             rate_plan_fee=15.0,
#             period_from=date(2023, 1, 1),
#             period_to=date(2023, 1, 31),
#             customer_cost=180.0
#         )
        
#         # Create Orders
#         self.order1 = Order.objects.create(
#             company=self.company,
#             po_number='PO789',
#             current_status='Shipped',
#             placed_by='John Doe',
#             shipping_address='789 Order St',
#             order_date=date(2023, 1, 1),
#             item_cost=50.0,
#             shipping_cost=5.0,
#             order_total=55.0,
#             order_number='ORD123',
#             customer_cost=66.0
#         )
        
#         self.order2 = Order.objects.create(
#             company=self.company,
#             po_number='PO101',
#             current_status='Shipped',
#             placed_by='Jane Doe',
#             shipping_address='101 Order St',
#             order_date=date(2023, 1, 1),
#             item_cost=75.0,
#             shipping_cost=7.5,
#             order_total=82.5,
#             order_number='ORD456',
#             customer_cost=99.0
#         )
    
#     def test_billing_system(self):
#         # Create ContractEntry and OrderEntry dataclasses
#         contract_entries = [
#             ContractEntry(
#                 serial_no=self.contract1.serial_no,
#                 vin=self.contract1.vin,
#                 database=self.contract1.database,
#                 assigned_po=self.contract1.assigned_po,
#                 bill_days=self.contract1.bill_days,
#                 billing_days=self.contract1.billing_days,
#                 total_cost=self.contract1.total_cost,
#                 rate_plan_name=self.contract1.rate_plan_name,
#                 rate_plan_fee=self.contract1.rate_plan_fee,
#                 company=self.company,
#                 display_name=self.contract1.company.display_name,
#                 period_from=self.contract1.period_from,
#                 period_to=self.contract1.period_to
#             ),
#             ContractEntry(
#                 serial_no=self.contract2.serial_no,
#                 vin=self.contract2.vin,
#                 database=self.contract2.database,
#                 assigned_po=self.contract2.assigned_po,
#                 bill_days=self.contract2.bill_days,
#                 billing_days=self.contract2.billing_days,
#                 total_cost=self.contract2.total_cost,
#                 rate_plan_name=self.contract2.rate_plan_name,
#                 rate_plan_fee=self.contract2.rate_plan_fee,
#                 company=self.company,
#                 display_name=self.contract2.company.display_name,
#                 period_from=self.contract2.period_from,
#                 period_to=self.contract2.period_to
#             )
#         ]
        
#         order_entries = [
#             OrderEntry(
#                 po_number=self.order1.po_number,
#                 current_status=self.order1.current_status,
#                 placed_by=self.order1.placed_by,
#                 shipping_address=self.order1.shipping_address,
#                 order_date=self.order1.order_date,
#                 item_cost=self.order1.item_cost,
#                 shipping_cost=self.order1.shipping_cost,
#                 order_total=self.order1.order_total,
#                 order_number=self.order1.order_number,
#                 company=self.company
#             ),
#             OrderEntry(
#                 po_number=self.order2.po_number,
#                 current_status=self.order2.current_status,
#                 placed_by=self.order2.placed_by,
#                 shipping_address=self.order2.shipping_address,
#                 order_date=self.order2.order_date,
#                 item_cost=self.order2.item_cost,
#                 shipping_cost=self.order2.shipping_cost,
#                 order_total=self.order2.order_total,
#                 order_number=self.order2.order_number,
#                 company=self.company
#             )
#         ]
        
#         # Save entries
#         save_all_contracts(contract_entries)
#         save_all_orders(order_entries)
        
#         # Create CompanyBill dataclass
#         company_bill = CompanyBill(
#             company=self.company,
#             display_name=self.company.display_name,
#             contracts=[self.contract1, self.contract2],
#             orders=[self.order1, self.order2]
#         )
        
#         # Generate bill
#         bill = company_bill.generate_bill(date(2023, 1, 1), date(2023, 1, 31))
        
#         # Check Bill
#         self.assertEqual(bill.company, self.company)
#         self.assertEqual(bill.period_from, date(2023, 1, 1))
#         self.assertEqual(bill.period_to, date(2023, 1, 31))
#         self.assertEqual(bill.total_cost, 465.0)
#         print("Bill Passed:")
#         pprint(bill.__dict__)
        
#         # Check BillItems
#         bill_items = BillItem.objects.filter(bill=bill)
#         self.assertEqual(bill_items.count(), 4)
#         print("Bill Items Passed:")
#         # Print each bill item from the queryset
#         for item in bill_items:
#             pprint(item.__dict__)
        
#         item_costs = [item.item_cost for item in bill_items]
#         self.assertIn(120.0, item_costs)
#         self.assertIn(180.0, item_costs)
#         self.assertIn(66.0, item_costs)
#         self.assertIn(99.0, item_costs)

#     def test_reseller_users(self):
#         # Ensure the reseller can access its associated users
#         users = self.reseller.users.all()
#         self.assertEqual(users.count(), 2)
#         self.assertIn(self.user1, users)
#         self.assertIn(self.user2, users)
#         print("Reseller Users Passed:")
#         pprint([user.email for user in users])