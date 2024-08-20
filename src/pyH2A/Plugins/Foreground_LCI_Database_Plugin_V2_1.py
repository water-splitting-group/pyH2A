from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
import numpy as np
import pprint as pp
import matplotlib.pyplot as plt
import json 

class Foreground_LCI_Database_Plugin_V2_1:
    ''' Processing of foreground LCI data for brightway calculation.

    Parameters
    ---------


    Returns
    ------
    
    '''

    def __init__(self, dcf, print_info):
        process_table(dcf.inp, 'Irradiation Used', 'Value')
        process_table(dcf.inp, 'LCA Parameters Photovoltaic', 'Value')

        self.calculate_sunlight(dcf)
        self.activities()
        self.exchanges(dcf)
        self.LCI_database(self.activities(), self.exchanges(dcf))

    def calculate_sunlight(self, dcf):
        '''Calculating the amount of sunlight.'''
    
        if isinstance(dcf.inp['Irradiation Used']['Data']['Value'], str):
            data = read_textfile(dcf.inp['Irradiation Used']['Data']['Value'], delimiter='  ')[:, 1]
        else:
            data = dcf.inp['Irradiation Used']['Data']['Value']

        if len(data.shape) > 1:
            raise ValueError("Expected 1D array for sunlight data.")
    
        total_amount_sunlight = np.sum(data)
        print(total_amount_sunlight)
        return total_amount_sunlight

    
    def activities(self):
        activities = {
            "activities": [
                {
                    "name":"Production of hydrogen",
                    "location": "GLO",
                    "reference product": "hydrogen",
                    "unit": "kilogram",
                    "code": "production_of_hydrogen"
                },
                {
                    "name": "Production and maintenance of individual parts",
                    "location": "GLO",
                    "reference product": "hydrogen",
                    "unit": "unit",
                    "code": "production_and_maintenance" 
                }
            ]
        }
        return activities
    
    def exchanges(self, dcf):
        exchanges = {
            "exchanges": [
                #production of hydrogen
                {
                    "input": "sunlight",
                    "amount": 1.0,  
                    "type": "biosphere",
                    "unit": "kilowatt",
                    "activity": "production_of_hydrogen" 
                },
                {
                    "input": "sea water",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Sea water demand (m3)']['Value'], 
                    "type": "biosphere",
                    "unit": "cubic meter",
                    "activity": "production_of_hydrogen"
                }, 
                {
                    "input": "brine",
                    "amount": 1.0,  
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "production_of_hydrogen"
                },
                {
                    "input": "hydrogen",  
                    "amount": 1.0,  
                    "type": "production",
                    "unit": "kilogram",
                    "activity": "production_of_hydrogen"
                },
                {
                    "input": "oxygen",  
                    "amount": 1.0,  
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "production_of_hydrogen"
                },
                {
                    "input": "production_pv_panels",
                    "amount": 1.0,  
                    "type": "production",
                    "unit": "kilowatt",  
                    "activity": "production_and_maintenance" 
                },
                {
                    "input": "production_battery",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilowatt",  
                    "activity": "production_and_maintenance" 
                },
                {
                    "input": "production_electrolyzer",
                    "amount": 1.0,  
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "production_and_maintenance" 
                },
                {
                    "input": "production_reverse_osmosis",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "smt",  
                    "activity": "production_and_maintenance" 
                }
            ]
        }
        return exchanges
    
    
    def LCI_database(self, activities, exchanges):
        # Write the activities to a JSON file
        with open('activities.json', 'w') as file:
            json.dump(activities, file, indent=4)
        # Write the exchanges to a JSON file
        with open('exchanges.json', 'w') as file:
            json.dump(exchanges, file, indent=4)
        #
        #loading activities from JSON
        with open('activities.json', 'r') as file:
            foreground_LCI_database_activities = json.load(file)['activities']
        #loading exchanges from JSON
        with open('exchanges.json', 'r') as file:
            foreground_LCI_database_exchanges = json.load(file)['exchanges']
        #
        #LCI database, associating the activities with their respective exhanges
        db_name = "foreground_LCI_database"
        LCI_database = {}
        #processing activities
        for activity in foreground_LCI_database_activities:
            activity_code = activity.pop('code')
            LCI_database[activity_code] = activity
        #processing exchanges
        for exchange in foreground_LCI_database_exchanges:
            input_code = exchange.pop('input') 
            activity_code = exchange.pop('activity')
            exchange['input'] = (activity_code, input_code)  # this was added to differentiate between the same variables but for different activities, e.g., electricity
            #exchange['output'] = (input_code, activity_code)
            LCI_database[activity_code].setdefault('exchanges', []).append(exchange)
        #
        #print(json.dumps(self.activities, indent=4))
        #print(json.dumps(self.exchanges, indent=4))
        #print(json.dumps(LCI_database, indent=4))
        #pp.pprint(LCI_database)