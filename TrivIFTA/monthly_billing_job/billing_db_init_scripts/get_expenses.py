#!/usr/bin/env python

import os
import requests
import csv

# Define the base URL for your API
base_url = "http://127.0.0.1:8000/billing"

# Define the folder to store the CSV files
output_folder = "../../AscendanceGeotabExpenses3"

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
        # Fetch and save company expense
        company_expense_endpoint = f"{base_url}/company-expensing/{company_name}/{month}/{year}/"
        fetch_and_save_data(company_expense_endpoint, company_name, month, year, "company_expense")
        
        # Fetch and save itemized expense
        itemized_expense_endpoint = f"{base_url}/itemized-expensing/{company_name}/{month}/{year}/"
        fetch_and_save_data(itemized_expense_endpoint, company_name, month, year, "itemized_expense")

print("Expense Data retrieval and saving completed.")