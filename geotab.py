#!/usr/bin/env python3

import mygeotab
from pprint import pprint
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, time
from filter import FuelTaxProcessor, VinDataCollection


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
        return self.get('FuelTaxDetail', fromDate=from_date, toDate=to_date, includeHourlyData=False, includeBoundaries=False)

    def get_devices(self, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        # Return all devices in the group 'Ifta Group'
        return self.get('Device', fromDate=from_date, toDate=to_date)

    def get_vin_map(self, from_date: datetime, to_date: datetime) -> Dict[str, str]:
        device_list = self.get_devices(from_date, to_date)
        return {device['id']: device['vehicleIdentificationNumber'] for device in device_list if device.get('vehicleIdentificationNumber', None) and device.get('id', None)}

    def get_vin(self, device_id: str) -> str:
        return self.get_vin_map()[device_id]

    def init_detail_map(self, from_date: datetime, to_date: datetime) -> None:

        fuel_tax_details = self.get_fuel_tax_details(from_date, to_date)
        vin_map = self.get_vin_map(from_date, to_date)

        for detail in fuel_tax_details:
            if detail['device']['id'] not in self.detail_map:
                self.detail_map[detail['device']['id']] = [detail]
            else:
                self.detail_map[detail['device']['id']].append(detail)

        for device_id in list(self.detail_map):
            if device_id in vin_map:
                for detail in self.detail_map[device_id]:
                    detail['vehicleIdentificationNumber'] = vin_map[device_id]
            else:
                for detail in self.detail_map[device_id]:
                    detail['vehicleIdentificationNumber'] = None
                print('VIN not found for device id: ' + device_id)


    def to_dataframe(self) -> pd.DataFrame:
        '''
        Creates a dataframe object using the data in the detail_map
        '''
        reduced_detail_map = []
        for device_id, details in sorted(self.detail_map.items(), key=lambda x: x[0]):
            for detail in details:
                vin = detail['vehicleIdentificationNumber']
                reduced_detail_map.append({
                    'FuelTaxVin': vin,
                    'EnterReadingDate': detail['enterTime'].date() if detail.get('enterTime', None) else None,  
                    'EnterReadingTime': detail['enterTime'].replace(microsecond=0).time() if detail.get('enterTime', None) else None,
                    'ExitReadingTime': detail['exitTime'].replace(microsecond=0).time() if detail.get('exitTime', None) else None,
                    'FuelTaxEnterOdometer': detail.get('enterOdometer', None),
                    'FuelTaxExitOdometer': detail.get('exitOdometer', None),
                    'FuelTaxJurisdiction': detail.get('jurisdiction', None),
                })
            # change the last detail in the list to have an exit time of 00:00:00
            reduced_detail_map[-1]['ExitReadingTime'] = time(0, 0)
        
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
        

# my_geotab_api = MyGeotabAPI()

# from_date = datetime(2023, 12, 14, 0, 0, 0)
# to_date = datetime(2023, 12, 15, 0, 0, 0)

# vin_data_collection = my_geotab_api.to_vin_data_collection(from_date, to_date)
# vin_data_collection.export_data('geotab_test.csv')