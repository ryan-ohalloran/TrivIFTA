#!/usr/bin/env python3

from datetime import datetime
from pprint import pprint
import os
from dotenv import load_dotenv
from geotab import MyGeotabAPI

def main():
    if not load_dotenv():
        print('Failed to load .env file')
        return

    username = os.getenv('MYGEOTAB_USERNAME')
    password = os.getenv('MYGEOTAB_PASSWORD')
    database = os.getenv('MYGEOTAB_DATABASE')

    my_geotab_api = MyGeotabAPI(username=username, password=password, database=database)

    from_date = datetime(2023, 12, 10)
    to_date = datetime(2023, 12, 13)

    geotab_ifta_data_collection = my_geotab_api.to_ifta_data_collection(from_date, to_date)
    df = geotab_ifta_data_collection.to_dataframe()

    # iterate over the df and count number of unique vins
    unique_vins = set(df['VIN'])
    print(f'Number of unique VINs: {len(unique_vins)}')


if __name__ == '__main__':
    main()