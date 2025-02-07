from pyH2A.Utilities.input_modification import insert, process_table, daily_to_yearly_power
from pyH2A.Plugins.Electrolyzer_Plugin import calculate_electrolyzer_power_demand, calculate_hydrogen_production, calculate_stack_replacement
import numpy as np

class Stored_Power_Electrolysis_Plugin:
    '''Simulation of hydrogen production using electrolysis.

    Parameters
    ----------
    Electrolysis Using Stored Power > Fraction of stored power used for electrolysis > Value : float
        Fraction of stored power used for electrolysis.
    Electrolyzer > Nominal Power (kW) > Value : float
        Nominal power of electrolyzer in kW.
    Electrolyzer > Power requirement increase per year > Value : float
        Electrolyzer power requirement increase per year due to stack degradation. Percentage 
        or value > 0. Increase calculated as: (1 + increase per year) ^ year.
    Electrolyzer > Minimum capacity > Value : float
        Minimum capacity required for electrolyzer operation. Percentage or value between 0 and 1.
    Electrolyzer > Conversion efficiency (kg H2/kWh) > Value : float
        Electrical conversion efficiency of electrolyzer in (kg H2)/kWh.
    Electrolyzer > Replacement time (h) > Value : float
        Operating time in hours before stack replacement of electrolyzer is required.
    Electrolyzer > Yearly Operation Data > Value : nd.array
        Yearly operation data of electrolyzer in (year, H2 produced, electrolyzer capacity) format.
    Electrolyzer > H2 Production (yearly, kg) > Value : nd.array
        Yearly hydrogen production in kg.
    Power Generation > Stored Power (daily, kWh) > Value : dict
        Power stored in battery daily in kWh (dictionary of years).

    Returns
    -------
    Technical Operating Parameters and Specifications > Plant Design Capacity (kg of H2/day) > Value : nd.array
        Plant design capacity in (kg of H2)/day calculated from installed 
        electrolysis power capacity and hourly power generation data.
    Planned Replacement > Electrolyzer Stack Replacement > Frequency (years) : float
        Frequency of electrolyzer stack replacements in years, calculated from replacement time and hourly
        irradiation data.
    Power Consumption > Stored Power Electrolysis (kWh, yearly) > Value : nd.array
        Electricity demand of electrolysis using stored power in kWh per year.
    Power Consumption > Stored Power Electrolysis (kWh, yearly) > Type : str
        Type of power consumer, type is 'on_demand' (only uses stored power).
    '''

    def __init__(self, dcf, print_info):
        process_table(dcf.inp, 'Electrolysis Using Stored Power', 'Value')
        process_table(dcf.inp, 'Power Generation', 'Value')
        process_table(dcf.inp, 'Electrolyzer', 'Value')

        self.calculate_H2_production(dcf)
        self.replacement_frequency = calculate_stack_replacement(self.operation_hours, 
                                    dcf.inp['Electrolyzer']['Replacement time (h)']['Value'])
        
        insert(dcf, 'Power Consumption', 'Stored Power Electrolysis (kWh, yearly)', 'Value',
                self.power_consumption_kWh, __name__, print_info = print_info)
        insert(dcf, 'Power Consumption', 'Stored Power Electrolysis (kWh, yearly)', 'Type',
                'on_demand', __name__, print_info = print_info)
        
        insert(dcf, 'Planned Replacement', 'Electrolyzer Stack Replacement', 'Frequency (years)', 
                self.replacement_frequency, __name__, print_info = print_info, add_processed = False,
                insert_path = False)

        insert(dcf, 'Technical Operating Parameters and Specifications', 'Plant Design Capacity (kg of H2/day)', 'Value', 
                self.new_h2_production_kg/365., __name__, print_info = print_info)

    def calculate_H2_production(self, dcf):
        '''
        '''

        HOURS_IN_A_YEAR = 8760

        electrolyzer_yearly_data = dcf.inp['Electrolyzer']['Yearly Operation Data']['Value']
        remaining_run_time_per_year_in_hours = HOURS_IN_A_YEAR - electrolyzer_yearly_data[:,2]
        
        electrolyzer_power_demand, power_increase = calculate_electrolyzer_power_demand(dcf.inp['Electrolyzer']['Power requirement increase per year']['Value'],
                                                                                        dcf.inp['Electrolyzer']['Nominal Power (kW)']['Value'],
                                                                                        dcf.operation_years)

        maximum_consumable_power_kWh = remaining_run_time_per_year_in_hours * electrolyzer_power_demand
        
        stored_power = dcf.inp['Power Generation']['Stored Power (daily, kWh)']['Value']
        stored_power_yearly = daily_to_yearly_power(stored_power)

        stored_power_yearly_available_for_use = stored_power_yearly * dcf.inp['Electrolysis Using Stored Power']['Fraction of stored power used for electrolysis']['Value']

        self.power_consumption_kWh = np.minimum(maximum_consumable_power_kWh, stored_power_yearly_available_for_use)

        # Updating H2 production

        additional_h2_production_kg = calculate_hydrogen_production(self.power_consumption_kWh, 
                                                         dcf.inp['Electrolyzer']['Conversion efficiency (kg H2/kWh)']['Value'],
                                                         power_increase)
        
        old_h2_production_kg = dcf.inp['Electrolyzer']['H2 Production (yearly, kg)']['Value']

        self.new_h2_production_kg = old_h2_production_kg.copy()
        self.new_h2_production_kg[-len(additional_h2_production_kg):] += additional_h2_production_kg
        
        # Updating operation hours

        additional_operation_hours = self.power_consumption_kWh / electrolyzer_power_demand
        self.operation_hours = additional_operation_hours + electrolyzer_yearly_data[:,2]
