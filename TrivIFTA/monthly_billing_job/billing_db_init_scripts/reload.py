#!/usr/bin/env python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrivIFTA.settings')

application = get_wsgi_application()


from monthly_billing_job.models import *
from monthly_billing_job.services.myadmin import MyAdminPublicAPI

def main():
    # Issue a dropdb and createdb command to reset the database 'TrivIFTA'
    print('Resetting the database...')
    os.system('dropdb TrivIFTA')
    os.system('createdb TrivIFTA')
    print('Database reset complete.')

    # Make migrations and migrate
    print('Migrating the database...')
    os.system('python manage.py makemigrations')
    os.system('python manage.py migrate')
    print('Migration complete.')

    # Create a reseller
    print('Creating a reseller...')
    reseller = Reseller.objects.create(
        name='Ascendance Truck Centers',
        address='3311 Adventureland Dr., Altoona, IA 50009',
        contact_email='rohalloran123@gmail.com',
        contact_phone='515-967-3300',
    )

    # create a user
    print('Creating a user...')
    if not User.objects.filter(username='rohalloran').exists():
        user = User.objects.create_user(
            username='rohalloran',
            phone_number='515-371-5295',
            reseller=reseller,
            my_admin_username='rohallo2@nd.edu',
            my_admin_password='Sr3e3s*$F!VC5da',
            database_name='o_halloran',
        )
    print(f'User created: {user}')

    # create an account
    print('Creating an account...')
    account = Account.objects.create(
        account_id='OHAL01',
    )
    print(f'Account created: {account}')
    # Link the user to the account
    user.accounts.add(account)

    # Create three CompanyTypes
    print('Creating company types...')
    internal = CompanyType.objects.create(
        type_name='internal',
    )
    sourcewell = CompanyType.objects.create(
        type_name='sourcewell',
    )
    default = CompanyType.objects.create(
        type_name='default',
    )
    print('Company types created.')

    # Populate data
    api = MyAdminPublicAPI(user)
    for month in (11, 12):
        api.populate_data(month=month, year=2023)
    for month in (1, 2, 3, 4, 5):
        api.populate_data(month=month, year=2024)

if __name__ == '__main__':
    main()
