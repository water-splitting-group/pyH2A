from pyH2A.Utilities.input_modification import insert, process_table
import numpy as np

class Reverse_Osmosis_Plugin:
    '''Simulation of purified water production using reverse osmosis.
    
    Parameters
    ----------
    Financial Input Values > construction time > Value : int
        Construction time of hydrogen production plant in years.
	Technical Operating Parameters and Specifications > Output per Year > Value : float
		Yearly output taking operating capacity factor into account, in (kg of H2)/year.
    Reverse Osmosis > Power Demand (kWh/m3) > Value : float
        Power demand of reverse osmosis plant in kWh per m3 of sea water.
    Reverse Osmosis > Average daily operating hours > Value : float
        Average daily operating hours of reverse osmosis plant, used for scaling of reverse osmosis plant.
    Reverse Osmosis > Recovery Rate > Value : float
        Fraction of fresh water obtained from given volume of sea water.
  
    Returns
    -------
    Power Consumption > Reverse Osmosis Consumption (kWh, yearly) > Value : nd.array
        Electricity demand of reverse osmosis plant in kWh per year.
    Power Consumption > Reverse Osmosis Consumption (kWh, yearly) > Type : str
        Type of power consumer, type is 'flexible', uses both stored and available power.
    Reverse Osmosis > Capacity (m3/h) > Value : float
        Maximum sea water processing capacity per hour of reverse osmosis plant.   
    '''

    def __init__(self, dcf, print_info):
        process_table(dcf.inp, 'Reverse Osmosis', 'Value')
        process_table(dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')
 
        self.calculate_electricity_demand(dcf)
        self.calculate_reverse_osmosis_scaling(dcf)

        insert(dcf, 'Power Consumption', 'Reverse Osmosis Consumption (kWh, yearly)', 'Value',
                self.electricity_demand_kWh, __name__, print_info = print_info)
        insert(dcf, 'Power Consumption', 'Reverse Osmosis Consumption (kWh, yearly)', 'Type',
                'flexible', __name__, print_info = print_info)
                
        insert(dcf, 'Reverse Osmosis', 'Capacity (m3/h)', 'Value',
                self.maximum_sea_water_processing_m3_per_hour, __name__, print_info = print_info)
                
    def calculate_electricity_demand(self, dcf):
        '''Calculation of electricity demand for reverse osmosis based on
        yearly amount of hydrogen production.
        '''
        MOLAR_RATIO_WATER = 18.01528 / 2.016
        DENSITY_WATER_KG_PER_M3 = 997

        output_per_year_kg_H2 = dcf.inp['Technical Operating Parameters and Specifications']['Output per Year']['Value']

        fresh_water_demand_kg = output_per_year_kg_H2 * MOLAR_RATIO_WATER
        fresh_water_demand_m3 = fresh_water_demand_kg / DENSITY_WATER_KG_PER_M3

        self.sea_water_demand_m3 = fresh_water_demand_m3 / dcf.inp['Reverse Osmosis']['Recovery Rate']['Value']

        electricity_demand_kWh = self.sea_water_demand_m3 * dcf.inp['Reverse Osmosis']['Power Demand (kWh/m3)']['Value']
        self.electricity_demand_kWh = electricity_demand_kWh[dcf.inp['Financial Input Values']['construction time']['Value']:]

    def calculate_reverse_osmosis_scaling(self, dcf):
        '''
        Calculation of maximum sea water processing capacity per hour based on
        yearly sea water demand and average daily operating hours.
        '''

        DAYS_IN_A_YEAR = 365

        average_daily_operating_hours = dcf.inp['Reverse Osmosis']['Average daily operating hours']['Value']
        yearly_operating_hours = average_daily_operating_hours * DAYS_IN_A_YEAR
        
        try:
            maximum_yearly_sea_water_demand_m3 = max(self.sea_water_demand_m3)
        except TypeError:
            maximum_yearly_sea_water_demand_m3 = self.sea_water_demand_m3

        self.maximum_sea_water_processing_m3_per_hour = maximum_yearly_sea_water_demand_m3 / yearly_operating_hours