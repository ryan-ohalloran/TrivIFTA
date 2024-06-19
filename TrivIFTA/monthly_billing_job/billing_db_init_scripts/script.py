#!/usr/bin/env python

import os
from subprocess import call

def run_billing_ingest_for_range(start_month, start_year, end_month, end_year):
    current_month = start_month
    current_year = start_year

    while current_year < end_year or (current_year == end_year and current_month <= end_month):
        print(f"Running billing ingest for {current_month:02d}/{current_year}")
        try:
            call(['python', '../../manage.py', 'generate_monthly_bills', '--month', f"{current_month:02d}", '--year', str(current_year)])
        except Exception as e:
            print(f"Failed to run billing ingest for {current_month:02d}/{current_year}: {e}")

        # Increment month and year
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1


if __name__ == "__main__":
    start_month = 11
    start_year = 2023
    end_month = 5
    end_year = 2024

    run_billing_ingest_for_range(start_month, start_year, end_month, end_year)

