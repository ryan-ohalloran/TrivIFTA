#!/usr/bin/env python3

import mygeotab
from pprint import pprint
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

class MyGeotabAPI(mygeotab.API):
    def __init__(self, username: str, password: str, database: str) -> None:
        super().__init__(username, password, database)
        # authenticate the api object then check for success. If not, raise an exception
        try:
            self.authenticate()
        except mygeotab.AuthenticationException as e:
            raise Exception(f'Failed to authenticate API.\n\t{e}')

    def get_fuel_tax_details(self, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        return self.get('FuelTaxDetail', fromDate=from_date, toDate=to_date, includeHourlyData=False, includeBoundaries=False)

    def get_devices(self, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        return self.get('Device', fromDate=from_date, toDate=to_date)

    def get_vin_map(self, from_date: datetime, to_date: datetime) -> Dict[str, str]:
        device_list = self.get_devices(from_date, to_date)
        return {device['id']: device['vehicleIdentificationNumber'] for device in device_list if device.get('vehicleIdentificationNumber', None)}

    def get_vin(self, device_id: str) -> str:
        return self.get_vin_map()[device_id]

    def get_fuel_tax_details_by_vin(self, from_date: datetime, to_date: datetime) -> Dict[str, Any]:
        fuel_tax_details = self.get_fuel_tax_details(from_date, to_date)
        vin_map = self.get_vin_map(from_date, to_date)
        detail_map = {}

        for detail in fuel_tax_details:
            if detail['device']['id'] not in detail_map:
                detail_map[detail['device']['id']] = [detail]
            else:
                detail_map[detail['device']['id']].append(detail)

        for device_id in list(detail_map):
            if device_id in vin_map:
                detail_map['vehicleIdentificationNumber'] = vin_map[device_id]
            else:
                detail_map['vehicleIdentificationNumber'] = None
                print('VIN not found for device id: ' + device_id)

        return detail_map

    def get_fuel_tax_details_by_vin_dataframe(self, from_date, to_date):
        fuel_tax_details_by_vin = self.get_fuel_tax_details_by_vin(from_date, to_date)
        all_entries = []

        for vin, details in fuel_tax_details_by_vin.items():
            for detail in details:
                all_entries.append({
                    'VIN': vin,
                    'ReadingDate': detail['readingDate'],
                    'ReadingTime': detail['readingTime'],
                    'Odometer': detail['odometer'],
                    'Jurisdiction': detail['jurisdiction']
                })

        return pd.DataFrame(all_entries)


