from pyH2A.Plugins.Plugin import Plugin
import numpy as np
import logging

class BatteryPlugin(Plugin):
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
    def __init__(
            self, 
            dcf : dict, 
            print_info : bool
            ) -> None:
        super().__init__(dcf, print_info)

        self.logger = logging.getLogger("pyH2A.Plugins.Energy.BatteryPlugin")
        self.logger.info("Starting BatteryPlugin")

        table_keys = ['Power Generation', 'Battery']
        self.process_table(table_keys)

        self.calculate_electricity_storage()

        self.insert_table()

    def calculate_electricity_storage(
            self
            ) -> None:
        '''Using hourly power generation data and electrolyzer parameters,
        H2 production is calculated.
        '''

        available_power_yearly = self.dcf.inp['Power Generation']['Available Power (daily, kWh)']['Value']

        yearly_recovered_power = {}
        yearly_unstored_power = {}

        for year in self.dcf.operation_years:
            daily_available_power = available_power_yearly[year]

            capacity, capacity_decrease = self.calculate_battery_capacity(year)

            capacity *= np.ones(len(daily_available_power))
            daily_stored_power = np.amin(np.c_[daily_available_power, capacity], axis = 1)
            daily_recovered_power = daily_stored_power * self.dcf.inp['Battery']['Round trip efficiency']['Value']

            unstored_power = daily_available_power - daily_stored_power

            yearly_recovered_power[year] = daily_recovered_power
            yearly_unstored_power[year] = unstored_power  
      
        self.insert_queue.extend([
            ('Power Generation', 'Stored Power (daily, kWh)', yearly_recovered_power),
            ('Power Generation', 'Available Power (daily, kWh)', yearly_unstored_power),
            ('Power Generation', 'Available Power (hourly, kWh)', 0)
        ])
    
    def calculate_battery_capacity(self, year):

        capacity_decrease = (1. - self.dcf.inp['Battery']['Capacity loss per year']['Value']) ** year
        nominal_capacity = self.dcf.inp['Battery']['Design Capacity (kWh)']['Value'] * (1. - self.dcf.inp['Battery']['Lowest discharge level']['Value'])

        capacity = nominal_capacity * capacity_decrease

        return capacity, capacity_decrease