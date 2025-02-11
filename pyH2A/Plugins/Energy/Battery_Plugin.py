from pyH2A.Utilities.input_modification import insert, process_table
import numpy as np

class Battery_Plugin:
    '''Simulation of electricity storage using a battery.
    Simulation assumes that battery is charged and completely discharged every day.
    (no electricity storage across days, only one discharge per day, not multiple ones).

    Parameters
    ----------
    Power Generation > Available Power (daily, kWh) > Value : dict
        Available power, daily basis, dictionary of years (in kWh).
    Battery > Design Capacity (kWh) > Value : float
        Full design capacity of battery in kWh.
    Battery > Lowest discharge level > Value : float
        Lowest level to which battery can be discharged. Percentage or value between 0 and 1.
    Battery > Capacity loss per year > Value : float
        Loss of capacity per year. Percentage or value > 0.
    Battery > Round trip efficiency > Value : float
        Round trip efficiency of battery. Percentage or value between 0 and 1.
    
    Returns
    -------
    Power Generation > Stored Power (daily, kWh) > Value : dict
        Power stored in battery daily in kWh (dictionary of years).
    Power Generation > Available Power (daily, kWh) > Value : dict
        Available power, daily basis, dictionary of years (in kWh) - power which 
        has not been stored in battery
    Power Generation > Available Power (hourly, kWh) > Value : float
        Available power (hourly, kWh) is set to zero, since available power is now 
        only in daily format. 
    '''

    def __init__(self, dcf, print_info):
        process_table(dcf.inp, 'Power Generation', 'Value')
        process_table(dcf.inp, 'Battery', 'Value')

        self.calculate_electricity_storage(dcf)

        insert(dcf, 'Power Generation', 'Stored Power (daily, kWh)', 'Value',
                self.yearly_recovered_power, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Available Power (daily, kWh)', 'Value',
                self.yearly_unstored_power, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Available Power (hourly, kWh)', 'Value',
                0, __name__, print_info = print_info)

    def calculate_electricity_storage(self, dcf):
        '''Using hourly power generation data and electrolyzer parameters,
        H2 production is calculated.
        '''

        available_power_yearly = dcf.inp['Power Generation']['Available Power (daily, kWh)']['Value']

        yearly_recovered_power = {}
        yearly_unstored_power = {}

        for year in dcf.operation_years:
            daily_available_power = available_power_yearly[year]

            capacity, capacity_decrease = self.calculate_battery_capacity(dcf, year)

            capacity *= np.ones(len(daily_available_power))
            daily_stored_power = np.amin(np.c_[daily_available_power, capacity], axis = 1)
            daily_recovered_power = daily_stored_power * dcf.inp['Battery']['Round trip efficiency']['Value']

            unstored_power = daily_available_power - daily_stored_power

            yearly_recovered_power[year] = daily_recovered_power
            yearly_unstored_power[year] = unstored_power  
      
        self.yearly_recovered_power = yearly_recovered_power
        self.yearly_unstored_power = yearly_unstored_power
    
    def calculate_battery_capacity(self, dcf, year):

        capacity_decrease = (1. - dcf.inp['Battery']['Capacity loss per year']['Value']) ** year
        nominal_capacity = dcf.inp['Battery']['Design Capacity (kWh)']['Value'] * (1. - dcf.inp['Battery']['Lowest discharge level']['Value'])

        capacity = nominal_capacity * capacity_decrease

        return capacity, capacity_decrease