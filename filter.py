#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from datetime import date, time
from openpyxl import load_workbook
from typing import Dict
import io

class VinData:
    '''
    Class to hold data for each unique VIN
    '''
    def __init__(self, vin: str):
        self.vin = vin
        self.data = []
    
    def add_entry(self, reading_date: date, reading_time: time, odometer: int, jurisdiction: str) -> None:
        self.data.append( {
            'ReadingDate': reading_date,
            'ReadingTime': reading_time,
            'Odometer': odometer,
            'Jurisdiction': jurisdiction
        } )

class VinDataCollection(Dict[str, VinData]):
    '''
    Class to hold data for all VINs -- behaves like Dict[str, VinData]
    '''
    def add_vin_data(self, vin: str) -> None:
        if vin not in self:
            self[vin] = VinData(vin)
    
    def get_vin_data(self, vin: str) -> VinData:
        vin_data = self.get(vin, None)
        if not vin_data:
            raise Exception(f'VinData not found for VIN: {vin}')
        return vin_data

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert data for all VINs to a single dataframe object,
            sorted by VIN, ReadingDate, ReadingTime
        """
        all_entries = []

        # Iterate over VINs in the collection
        for vin, vin_data in self.items():
            for entry in vin_data.data:
                all_entries.append({
                    'VIN': vin,
                    'ReadingDate': entry['ReadingDate'],
                    'ReadingTime': entry['ReadingTime'],
                    'Odometer': entry['Odometer'],
                    'Jurisdiction': entry['Jurisdiction']
                })

        # Create a DataFrame from the accumulated entries
        df = pd.DataFrame(all_entries)

        # Sort the DataFrame by VIN, ReadingDate, and ReadingTime
        df.sort_values(by=['VIN', 'ReadingDate', 'ReadingTime'], inplace=True)

        # Return the dataframe
        return df
    
    def export_data(self, output_file: str) -> None:
        """
        Export data for all VINs to a CSV file
        """
        df = self.to_dataframe()
        df.to_csv(output_file, index=False, encoding='utf-8')

        
def find_header_row(input_data: bytes, header: str) -> int:
    """
    Find the row number of the header row in an Excel file
    input_data: the contents of the input file
    header: the header row to use to find the data
    rtype: int
    """
    wb = load_workbook(filename=io.BytesIO(input_data), read_only=True)
    sheet = wb['Data']  # Change 'Data' to your actual sheet name

    for row_index, row in enumerate(sheet.iter_rows(values_only=True)):
        if header in row:
            return row_index
    return None

def read_data(input_data: bytes, header: str) -> pd.DataFrame:
    """
    Read data from an Excel file and return a Pandas DataFrame
    input_data: the contents of the input file
    header: the header row to use to find the data
    rtype: Pandas DataFrame
    """
    header_row = find_header_row(input_data, header)
    if header_row is None:
        raise ValueError(f"Header '{header}' not found in data")

    df = pd.read_excel(io.BytesIO(input_data), sheet_name='Data', skiprows=header_row)
    return df

def reduce_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce dataframe to only columns:
        'FuelTaxVin', 'FuelTaxEnterTime', 'FuelTaxExitTime', 'FuelTaxJurisdiction', 'FuelTaxEnterOdometer', 'FuelTaxExitOdometer'
    df: Pandas DataFrame
    rtype: Pandas DataFrame
    """
    df = df[['FuelTaxVin', 'FuelTaxEnterTime', 'FuelTaxExitTime', 'FuelTaxJurisdiction', 'FuelTaxEnterOdometer', 'FuelTaxExitOdometer']]

    return df

def split_date_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract date and time from FuelTaxEnterTime and split into separate columns
    """
    df['FuelTaxEnterTime'] = pd.to_datetime(df['FuelTaxEnterTime']).dt.floor('S')
    df['FuelTaxExitTime'] = pd.to_datetime(df['FuelTaxExitTime']).dt.floor('S')
    df['EnterReadingDate'] = df['FuelTaxEnterTime'].dt.date
    df['EnterReadingTime'] = df['FuelTaxEnterTime'].dt.time
    df['ExitReadingTime'] = df['FuelTaxExitTime'].dt.time
    df = df.drop(columns=['FuelTaxEnterTime', 'FuelTaxExitTime'])
    return df


def process_data(input_file: any, data_type: str = 'path') -> VinDataCollection:
    """
    Read data from an Excel file and return a VinDataCollection object
    input_file: path to the input file or the contents of the input file
    data_type: 'path' if input_file is a path, 'bytes' if input_file is the contents of the file
    rtype: VinDataCollection
    """
    
    # If the input file is a path, read the data from the file
    if data_type == 'path':
        with open(input_file, 'rb') as f:
            input_file = f.read()
    elif data_type != 'bytes':
        raise ValueError(f"Unknown data_type: {data_type}")
    
    # Read the data from the input file
    df = read_data(input_file, 'DeviceName')

    # Reduce and split the dataframe
    df = reduce_df(df)
    df = split_date_time(df)

    # Create a dictionary to hold the VinData objects
    vin_data_collection = VinDataCollection()

    # Iterate over the rows in the dataframe
    for _, row in df.iterrows():
        vin = str(row['FuelTaxVin'])
        # skip rows with potentially empty VINs
        if vin in ('nan', 'None', ''):
            continue
        enter_reading_date = row['EnterReadingDate']
        enter_reading_time = row['EnterReadingTime']
        exit_reading_time = row['ExitReadingTime']
        enter_odometer = int(row['FuelTaxEnterOdometer'])
        exit_odometer = int(row['FuelTaxExitOdometer'])
        jurisdiction = row['FuelTaxJurisdiction']

        # Add this VIN to the VinDataCollection if it doesn't already exist
        vin_data_collection.add_vin_data(vin)

        # Get the VinData object for this VIN
        vin_data = vin_data_collection.get_vin_data(vin)

        # Add vin entry for enter time using enter odometer reading
        vin_data.add_entry(enter_reading_date, enter_reading_time, enter_odometer, jurisdiction)

        # Only add exit time if it is the last entry for this VIN on this day
        #   (i.e. if the exit time is 00:00, then it is the last entry for the day)
        if exit_reading_time == time(0, 0):
            # Change time to 23:59 to suit IFTA requirements
            exit_reading_time = time(23, 59)
            # In this case, use exit_reading_time and exit_odometer
            vin_data.add_entry(enter_reading_date, exit_reading_time, exit_odometer, jurisdiction)

    return vin_data_collection