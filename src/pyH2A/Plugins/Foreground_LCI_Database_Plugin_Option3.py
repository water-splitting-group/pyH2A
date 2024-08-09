import json
#listing of the ACTIVITIES
activities = {
    "activities": [
        {
            "name":"Pure water production",
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
            "location": "GLO/local", #not sure since the sunlight (one of the inputs) is dependent on the location
            "reference product": "electricity",
            "unit": "kilowatt",
            "code": "pv_electricity_production" 
        },
        {
            "name": "excessive power storage",
            "location": "GLO/local", #same as above
            "reference product": "electricity",
            "unit": "kilowatt",
            "code": "excessive_power_storage" 
        }
    ]
}
#listing of the EXCHANGES
exchanges = {
    "exchanges": [
        #reverse osmosis
        {
            "input": "electricity",  # for reverse osmosis from PV
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "technosphere",
            "unit": "kilowatt",
            "activity": "pure_water_production"
        },
        {
            "input": "production_reverse_osmosis",
            "amount": 1.0,
            "type": "production",
            "unit": "smt",  # !!!! specify the correct unit
            "activity": "pure_water_production"
        },
        {
            "input": "sea water",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "biosphere",
            "unit": "cubic meter",
            "activity": "pure_water_production"
        },
        {
            "input": "pure water",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "production",
            "unit": "cubic meter",
            "activity": "pure_water_production"
        },
        {
            "input": "brine",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "byproduct",
            "unit": "kilogram",
            "activity": "pure_water_production"
        },
        # water electrolysis
        {
            "input": "electricity",  # for water electrolysis from PV
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "technosphere",
            "unit": "kilowatt",
            "activity": "electrolysis_of_water"
        },
        {
            "input": "pure water",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "technosphere",
            "unit": "cubic meter",
            "activity": "electrolysis_of_water"
        },
        {
            "input": "production_electrolyzer",
            "amount": 1.0,  # if we need to replace this, then here it should change the amount
            "type": "technosphere",
            "unit": "kilowatt",
            "activity": "electrolysis_of_water"
        },
        {
            "input": "hydrogen",  # for water electrolysis from PV
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "production",
            "unit": "kilogram",
            "activity": "electrolysis_of_water"
        },
        {
            "input": "oxygen",  # for water electrolysis from PV
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "byproduct",
            "unit": "kilogram",
            "activity": "electrolysis_of_water"
        },
        # PV electricity production
        {
            "input": "sunlight",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "biosphere",
            "unit": "unit",
            "activity": "pv_electricity_production" 
        },
        {
            "input": "production_pv_panels",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "production",
            "unit": "kilowatt",  # !!!! specify the correct unit
            "activity": "pv_electricity_production"
        },
        {
            "input": "electricity",  # produced from PV
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "production",
            "unit": "kilowatt",
            "activity": "pv_electricity_production"
        },
        # excessive power storage
        {
            "input": "electricity",  # from PV modules
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "technosphere",
            "unit": "kilowatt",
            "activity": "excessive_power_storage"
        },
        {
            "input": "production_battery",
            "amount": 1.0,
            "type": "production",
            "unit": "kilowatt",  # !!!! specify the correct unit
            "activity": "excessive_power_storage"
        },
        {
            "input": "electricity",
            "amount": 1.0,  # !!!! specify the correct amount
            "type": "production",
            "unit": "kilowatt",
            "activity": "excessive_power_storage"
        }
    ]
}
#
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
    LCI_database[activity_code].setdefault('exchanges', []).append(exchange)
#
#print(json.dumps(activities, indent=4))
#print(json.dumps(exchanges, indent=4))
print(json.dumps(LCI_database, indent=4))
#import pprint
#pprint.pprint(LCI_database)

