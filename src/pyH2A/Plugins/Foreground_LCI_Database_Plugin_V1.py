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

        insert(dcf, 'Foreground LCI Database', 'Row', 'Value',
               self.LCI_database, __name__, print_info = print_info)  

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
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Electricity reverse osmosis (kW)']['Value'],
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "pure_water_production"
                },
                {
                    "input": "production_reverse_osmosis",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "unit",
                    "activity": "pure_water_production"
                },
                {
                    "input": "sea water",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Sea water demand (m3)']['Value'],
                    "type": "biosphere",
                    "unit": "cubic meter",
                    "activity": "pure_water_production"
                },
                {
                    "input": "pure water",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Amount of fresh water (m3)']['Value'],
                    "type": "production",
                    "unit": "cubic meter",
                    "activity": "pure_water_production"
                },
                {
                    "input": "brine",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Mass of brine (kg)']['Value'],
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "pure_water_production"
                },
                #electrolysis
                {
                    "input": "electricity",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Electrolyzer power consumption (kW)']['Value'] + dcf.inp['LCA Parameters Photovoltaic']['Electricity from battery (kW)']['Value'],
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "pure water",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Amount of fresh water (m3)']['Value'],
                    "type": "technosphere",
                    "unit": "cubic meter",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "production_electrolyzer",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Production and maintenance electrolyzer']['Value'],
                    "type": "technosphere",
                    "unit": "unit",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "hydrogen",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['H2 produced (kg)']['Value'],
                    "type": "production",
                    "unit": "kilogram",
                    "activity": "electrolysis_of_water"
                },
                {
                    "input": "oxygen",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['O2 produced (kg)']['Value'],
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "electrolysis_of_water"
                },
                #PV
                {
                    "input": "sunlight",
                    "amount": total_amount_sunlight,
                    "type": "biosphere",
                    "unit": "unit",
                    "activity": "pv_electricity_production"
                },
                {
                    "input": "production_pv_panels",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Amount of PV modules']['Value'],
                    "type": "production",
                    "unit": "unit",
                    "activity": "pv_electricity_production"
                },
                {
                    "input": "electricity",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Electrolyzer power consumption (kW)']['Value'] + dcf.inp['LCA Parameters Photovoltaic']['Electricity stored in battery (kW)']['Value'] + dcf.inp['LCA Parameters Photovoltaic']['Electricity reverse osmosis (kW)']['Value'],
                    "type": "production",
                    "unit": "kilowatt",
                    "activity": "pv_electricity_production"
                },
                #battery
                {
                    "input": "electricity",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Electricity stored in battery (kW)']['Value'],
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
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Electricity from battery (kW)']['Value'],
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
    
        self.LCI_database = LCI_database
        
        #pp.pprint(LCI_database)

