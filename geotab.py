#!/usr/bin/env python3

import mygeotab
from pprint import pprint
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, time
from ftplib import FTP
import io
from events import NoFuelTaxDataException
from ifta import FuelTaxProcessor, IftaDataCollection

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

        skipped_devices = set()
        for detail in fuel_tax_details:
            # Skip devices that are not in the IFTA group
            if detail['device']['id'] not in device_to_vin:
                skipped_devices.add(detail['device']['id'])
                continue
            # Add details to the detail map
            if detail['device']['id'] not in self.detail_map:
                self.detail_map[detail['device']['id']] = [detail]
                self.detail_map[detail['device']['id']][0]['vehicleIdentificationNumber'] = device_to_vin[detail['device']['id']]
            else:
                self.detail_map[detail['device']['id']].append(detail)
                self.detail_map[detail['device']['id']][-1]['vehicleIdentificationNumber'] = device_to_vin[detail['device']['id']]

        print(f'Skipped devices: {skipped_devices}')
                
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


        return pd.DataFrame(reduced_detail_map)

    def to_ifta_data_collection(self, fromDate: datetime, toDate: datetime) -> IftaDataCollection:
        '''
        Creates a IftaDataCollection object using the data from Geotab
        '''
        # initialize the device detail map
        self.init_detail_map(fromDate, toDate)

        # create a dataframe object from the device detail map
        df = self.to_dataframe()

        # return the IftaDataCollection object from the dataframe
        return FuelTaxProcessor.to_ifta_data_collection(df)

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