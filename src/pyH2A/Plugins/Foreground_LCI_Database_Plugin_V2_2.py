from pyH2A.Utilities.input_modification import insert, process_table
import numpy as np
import pprint as pp
import matplotlib.pyplot as plt
import json 

class Foreground_LCI_Database_Plugin_V2_2:
    ''' Processing of foreground LCI data for brightway calculation.

    Parameters
    ---------


    Returns
    ------
    
    '''

    def __init__(self, dcf, print_info):
        process_table(dcf.inp, 'LCA Parameters Photovoltaic', 'Value')

        self.LCI_database(dcf)

    def LCI_database(self, dcf):
        #
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
        #
        exchanges = {
            "exchanges": [
                #production of hydrogen
                {
                    "input": "sunlight",
                    "amount": 1.0,  # !!!! specify the correct amount
                    "type": "biosphere",
                    "unit": "kilowatt",
                    "activity": "production_of_hydrogen" 
                },
                {
                    "input": "sea water",
                    "amount": dcf.inp['LCA Parameters Photovoltaic']['Sea water demand (m3)']['Value'],  # !!!! specify the correct amount
                    "type": "biosphere",
                    "unit": "cubic meter",
                    "activity": "production_of_hydrogen"
                }, 
                {
                    "input": "brine",
                    "amount": 1.0,  # !!!! specify the correct amount
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "production_of_hydrogen"
                },
                {
                    "input": "hydrogen",  # for water electrolysis from PV
                    "amount": 1.0,  # !!!! specify the correct amount
                    "type": "production",
                    "unit": "kilogram",
                    "activity": "production_of_hydrogen"
                },
                {
                    "input": "oxygen",  # for water electrolysis from PV
                    "amount": 1.0,  # !!!! specify the correct amount
                    "type": "byproduct",
                    "unit": "kilogram",
                    "activity": "production_of_hydrogen"
                },
                {
                    "input": "production_pv_panels",
                    "amount": 1.0,  # !!!! specify the correct amount
                    "type": "production",
                    "unit": "kilowatt",  # !!!! specify the correct unit
                    "activity": "production_and_maintenance" 
                },
                {
                    "input": "production_battery",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "kilowatt",  # !!!! specify the correct unit
                    "activity": "production_and_maintenance" 
                },
                {
                    "input": "production_electrolyzer",
                    "amount": 1.0,  # if we need to replace this, then here it should change the amount
                    "type": "technosphere",
                    "unit": "kilowatt",
                    "activity": "production_and_maintenance" 
                },
                {
                    "input": "production_reverse_osmosis",
                    "amount": 1.0,
                    "type": "production",
                    "unit": "smt",  # !!!! specify the correct unit
                    "activity": "production_and_maintenance" 
                }
            ]
        }
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
        