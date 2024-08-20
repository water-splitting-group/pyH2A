from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np
import pprint as pp
import json

class Foreground_LCI_Database_Plugin_V1:
    '''Processing of foreground LCI data for brightway calculation for Photovoltaics Version 1.'''
    
    def __init__(self, dcf, print_info):
        process_table(dcf.inp, 'Irradiation Used', 'Value')
        process_table(dcf.inp, 'LCA Parameters Photovoltaic', 'Value')
        
        self.calculate_sunlight(dcf)
        self.activities()
        self.exchanges(dcf, self.calculate_sunlight(dcf))
        self.LCI_database(self.activities(), self.exchanges(dcf, self.calculate_sunlight(dcf)))

    def calculate_sunlight(self, dcf):
        '''Calculating the amount of sunlight.'''
        value = dcf.inp['Irradiation Used']['Data']['Value']
        if isinstance(value, str):
            data = read_textfile(value, delimiter='  ')[:, 1]
        else:
            data = np.array(value)
        
        if len(data.shape) > 1:
            raise ValueError("Expected 1D array for sunlight data.")
        
        total_amount_sunlight = np.sum(data)
        return total_amount_sunlight

    def activities(self):
        activities = {
            "activities": [
                {
                    "name": "Pure water production",
                    "location": "GLO",
                    "reference product": "pure water",
                    "unit": "cubic meter",
                    "code": "pure_water_production"
                },
                {
                    "name": "Electrolysis of water",
                    "location": "GLO",
                    "reference product": "hydrogen",
                    "unit": "kilogram",
                    "code": "electrolysis_of_water"
                },
                {
                    "name": "PV electricity production",
                    "location": "GLO/local",
                    "reference product": "electricity",
                    "unit": "kilowatt",
                    "code": "pv_electricity_production"
                },
                {
                    "name": "excessive power storage",
                    "location": "GLO/local",
                    "reference product": "electricity",
                    "unit": "kilowatt",
                    "code": "excessive_power_storage"
                }
            ]
        }
        return activities

    def exchanges(self, dcf, total_amount_sunlight):
        exchanges = {
            "exchanges": [
                {
                    "input": "electricity",
                    "amount": 1.0,
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "pure_water_production"
                },
                {
                    "input": "production_reverse_osmosis",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "smt",
                    "activity": "pure_water_production"
                },
                {
                    "input": "sea water",
                    "amount": 1.0,
                    "type": "biosphere",
                    "unit": "cubic meter",
                    "activity": "pure_water_production"
                },
                {
                    "input": "pure water",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "cubic meter",
                    "activity": "pure_water_production"
                },
                {
                    "input": "brine",
                    "amount": 1.0,
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "pure_water_production"
                },
                {
                    "input": "electricity",
                    "amount": 1.0,
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "pure water",
                    "amount": 1.0,
                    "type": "technosphere",
                    "unit": "cubic meter",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "production_electrolyzer",
                    "amount": 1.0,
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "hydrogen",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilogram",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "oxygen",
                    "amount": 1.0,
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "sunlight",
                    "amount": total_amount_sunlight,
                    "type": "biosphere",
                    "unit": "unit",
                    "activity": "pv_electricity_production"
                },
                {
                    "input": "production_pv_panels",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilowatt",
                    "activity": "pv_electricity_production"
                },
                {
                    "input": "electricity",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilowatt",
                    "activity": "pv_electricity_production"
                },
                {
                    "input": "electricity",
                    "amount": 1.0,
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "excessive_power_storage"
                },
                {
                    "input": "production_battery",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilowatt",
                    "activity": "excessive_power_storage"
                },
                {
                    "input": "electricity",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilowatt",
                    "activity": "excessive_power_storage"
                }
            ]
        }
        return exchanges

    def LCI_database(self, activities, exchanges):
        LCI_database = {}
        
        # Process activities
        for activity in activities['activities']:
            activity_code = activity.pop('code')
            LCI_database[activity_code] = activity
        
        # Process exchanges
        for exchange in exchanges['exchanges']:
            input_code = exchange.pop('input')
            activity_code = exchange.pop('activity')
            exchange['input'] = (activity_code, input_code)
            LCI_database[activity_code].setdefault('exchanges', []).append(exchange)
        
        pp.pprint(LCI_database)
