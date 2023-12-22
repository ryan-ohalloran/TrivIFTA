#!/usr/bin/env python3

import mygeotab
from pprint import pprint
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, time
from ftplib import FTP
import io
from events import NoFuelTaxDataException
from ifta import FuelTaxProcessor, VinDataCollection

KILO_TO_MILES = 0.62137119
IFTA_GROUP = [{'id': 'b279F'}] # if more groups need to be added in the future, add them to this list

class MyGeotabAPI(mygeotab.API):
    def __init__(self, username: str, password: str, database: str) -> None:
        super().__init__(username, password, database)
        # authenticate the api object then check for success. If not, raise an exception
        try:
            self.authenticate()
        except mygeotab.AuthenticationException as e:
            raise Exception(f'Failed to authenticate API.\n\t{e}')
        # Maps device id to metadata about the device
        self.detail_map = {}

    def get_fuel_tax_details(self, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        fuel_tax_details = self.get('FuelTaxDetail', 
                                    fromDate=from_date, 
                                    toDate=to_date, 
                                    includeHourlyData=False, 
                                    includeBoundaries=False)
        if not fuel_tax_details:
            raise NoFuelTaxDataException('No data returned from FuelTaxDetails endpoint.')
        
        return fuel_tax_details

    def get_ifta_devices(self, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        # Return all unique devices in the group 'Ifta Group'
        return self.get('Device', 
                        fromDate=from_date, 
                        toDate=to_date, 
                        search={'groups': IFTA_GROUP})

    def get_device_to_vin(self, from_date: datetime, to_date: datetime) -> Dict[str, str]:
        device_list = self.get_ifta_devices(from_date, to_date)
        return {device['id']: device['vehicleIdentificationNumber'] for device in device_list if device.get('vehicleIdentificationNumber', None) and device.get('id', None)}

    def get_vin(self, device_id: str) -> str:
        return self.get_device_to_vin()[device_id]

    def init_detail_map(self, from_date: datetime, to_date: datetime) -> None:

        fuel_tax_details = self.get_fuel_tax_details(from_date, to_date)
        device_to_vin = self.get_device_to_vin(from_date, to_date)
        
        for detail in fuel_tax_details:
            if detail['device']['id'] not in self.detail_map:
                self.detail_map[detail['device']['id']] = [detail]
            else:
                self.detail_map[detail['device']['id']].append(detail)

        for device_id in list(self.detail_map):
            # Skip devices that are not in IFTA group (or do  not have a VIN)
            if device_id in device_to_vin:
                for detail in self.detail_map[device_id]:
                    detail['vehicleIdentificationNumber'] = device_to_vin[device_id]
            else:
                for detail in self.detail_map[device_id]:
                    detail['vehicleIdentificationNumber'] = None
                print('Skipping: ' + device_id + ' (not in IFTA group)')


    def to_dataframe(self) -> pd.DataFrame:
        '''
        Creates a dataframe object using the data in the detail_map
        '''
        reduced_detail_map = []
        for _, details in sorted(self.detail_map.items(), key=lambda x: x[0]):
            for detail in details:
                vin = detail.get('vehicleIdentificationNumber', None)
                reduced_detail_map.append({
                    'FuelTaxVin': vin,
                    'EnterReadingDate': detail['enterTime'].date() if detail.get('enterTime', None) else None,  
                    'EnterReadingTime': detail['enterTime'].replace(microsecond=0).time() if detail.get('enterTime', None) else None,
                    'ExitReadingTime': detail['exitTime'].replace(microsecond=0).time() if detail.get('exitTime', None) else None,
                    'FuelTaxEnterOdometer': (detail['enterOdometer'] * KILO_TO_MILES) if detail.get('enterOdometer', None) else None,
                    'FuelTaxExitOdometer': (detail['exitOdometer'] * KILO_TO_MILES) if detail.get('exitOdometer', None) else None,
                    'FuelTaxJurisdiction': detail.get('jurisdiction', None),
                })
            # change the last detail in the list to have an exit time of 00:00:00
            if reduced_detail_map:
                reduced_detail_map[-1]['ExitReadingTime'] = time(0, 0)
        # iterate through the reduced_detail_map, count the number of unique vins, and print to the terminal
        unique_vins = set([detail['FuelTaxVin'] for detail in reduced_detail_map])
        print(f'Number of unique VINs: {len(unique_vins)}')


        return pd.DataFrame(reduced_detail_map)

    def to_vin_data_collection(self, fromDate: datetime, toDate: datetime) -> VinDataCollection:
        '''
        Creates a VinDataCollection object using the data from Geotab
        '''
        # initialize the device detail map
        self.init_detail_map(fromDate, toDate)

        # create a dataframe object from the device detail map
        df = self.to_dataframe()

        # return the VinDataCollection object from the dataframe
        return FuelTaxProcessor.to_vin_data_collection(df)

class GeotabFTP(FTP):
    def __init__(self, host: str):
        super().__init__(host)
    
    def login(self, username: str = 'geotab', password: str = '') -> None:
        super().login(username, password)

        # check for success
        if not self.getwelcome():
            raise Exception('Failed to login to FTP server.')
        
        self.cwd('/')
    
    def storbinary(self, command: str, file: io.BytesIO) -> None:
        super().storbinary(command, file)