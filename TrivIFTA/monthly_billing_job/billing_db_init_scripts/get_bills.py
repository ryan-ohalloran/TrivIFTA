#!/usr/bin/env python

import os
import requests
import csv

# Define the base URL for your API
base_url = "http://127.0.0.1:8000/billing"

# Define the folder to store the CSV files
output_folder = "../../AscendanceGeotabBills3"

# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Fetch the list of all companies
companies_response = requests.get(f"{base_url}/companies/")
companies_data = companies_response.json()
company_names = companies_data['companies']

# Define the months and years to fetch data for
months = [2, 3, 4, 5]
year = 2024

# Function to fetch and save data
def fetch_and_save_data(endpoint, company_name, month, year, file_suffix):
    response = requests.get(endpoint)
    csv_data = response.text
    # Ensure the company subfolder exists
    company_folder = os.path.join(output_folder, company_name)
    if not os.path.exists(company_folder):
        os.makedirs(company_folder)
    # Define the file path
    file_path = os.path.join(company_folder, f"{company_name}_{month:02}_{year}_{file_suffix}.csv")
    # Write the CSV data to the file
    with open(file_path, 'w', newline='') as file:
        file.write(csv_data)

# Loop through each company and fetch data for each month
for company_name in company_names:
    for month in months:
        # Fetch and save itemized receipt
        itemized_receipt_endpoint = f"{base_url}/itemized-receipt/{company_name}/{month}/{year}/"
        fetch_and_save_data(itemized_receipt_endpoint, company_name, month, year, "itemized_receipt")
        
        # Fetch and save company bill
        company_bill_endpoint = f"{base_url}/company-bill/{company_name}/{month}/{year}/"
        fetch_and_save_data(company_bill_endpoint, company_name, month, year, "company_bill")

# Fetch and save company bills for all companies over the given month and year
for month in months:
    company_bills_for_month_endpoint = f"{base_url}/company-bills/{month}/{year}/"
    response = requests.get(company_bills_for_month_endpoint)
    company_bills_data = response.json()

    # Convert the JSON response to CSV with new field names
    csv_file_path = os.path.join(output_folder, f"company_bills_{month:02}_{year}.csv")
    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['Company', 'Period From', 'Period To', 'Total Bill']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in company_bills_data:
            # Map old field names to new field names
            new_row = {
                'Company': row['company_name'],
                'Period From': row['period_from'],
                'Period To': row['period_to'],
                'Total Bill': f"{row['total_cost']:.2f}"  # Ensure the total cost is rounded to 2 decimal places
            }
            writer.writerow(new_row)

print("Data retrieval and saving completed.")
