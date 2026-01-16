from pyH2A.Utilities.input_modification import input_resolver, output_resolver
import numpy as np

battery_input_dict = {
    'available_power_daily': {
        'top_level': 'Power Generation',
        'mid_level': 'Available Power (daily, kWh)',
        'lower_level': 'Value',
        'dimension': 'Energy_Battery'  
    },
    'design_capacity': {
        'top_level': 'Battery',
        'mid_level': 'Design Capacity (kWh)',
        'lower_level': 'Value',
        'dimension': 'Energy_Battery'  
    },
    'lowest_discharge_level': {
        'top_level': 'Battery',
        'mid_level': 'Lowest discharge level',
        'lower_level': 'Value',
        'dimension': 'Dimensionless'  
    },
    'capacity_loss_per_year': {
        'top_level': 'Battery',
        'mid_level': 'Capacity loss per year',
        'lower_level': 'Value',
        'dimension': 'Dimensionless'  
    },
    'round_trip_efficiency': {
        'top_level': 'Battery',
        'mid_level': 'Round trip efficiency',
        'lower_level': 'Value',
        'dimension': 'Dimensionless'  
    },
}

battery_output_dict = {
    'yearly_recovered_power': {
        'top_level': 'Power Generation',
        'mid_level': 'Stored Power (daily, kWh)',
        'lower_level': 'Value',
        'dimension': 'Energy'
    },
    'yearly_unstored_power': {
        'top_level': 'Power Generation',
        'mid_level': 'Available Power (daily, kWh)',
        'lower_level': 'Value',
        'dimension': 'Energy'
    },
    'hourly_available_power': {
        'top_level': 'Power Generation',
        'mid_level': 'Available Power (hourly, kWh)',
        'lower_level': 'Value',
        'dimension': 'Energy'
    }
}

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
        try:
            inputs = input_resolver(battery_input_dict, dcf)
        except ValueError as e:
            # Only show the final message
            print(f"[ERROR] {e}")
            raise SystemExit(1)  # stops execution without full traceback
        
        self.available_power_yearly = inputs['available_power_daily']
        self.design_capacity = inputs['design_capacity']

        self.lowest_discharge_level = inputs['lowest_discharge_level']
        self.capacity_loss_per_year = inputs['capacity_loss_per_year']
        self.round_trip_efficiency = inputs['round_trip_efficiency']

        self.calculate_electricity_storage(dcf)

        outputs = {
            'yearly_recovered_power': self.yearly_recovered_power,
            'yearly_unstored_power': self.yearly_unstored_power,
            'hourly_available_power': 0,
        }

        output_resolver(battery_output_dict, outputs, dcf, print_info)

    def calculate_electricity_storage(self, dcf):

        yearly_recovered_power = {}
        yearly_unstored_power = {}

        for year in dcf.operation_years:
            daily_available_power = [q.magnitude for q in self.available_power_yearly[year]]

            print(daily_available_power)
            
            capacity, _ = self.calculate_battery_capacity(year)

            capacity_arr = capacity * np.ones(len(daily_available_power))
            daily_stored_power = np.minimum(daily_available_power, capacity_arr)

            daily_recovered_power = daily_stored_power * self.round_trip_efficiency
            unstored_power = daily_available_power - daily_stored_power

            yearly_recovered_power[year] = daily_recovered_power
            yearly_unstored_power[year] = unstored_power

        self.yearly_recovered_power = yearly_recovered_power
        self.yearly_unstored_power = yearly_unstored_power

    def calculate_battery_capacity(self, year):

        capacity_decrease = (1. - self.capacity_loss_per_year) ** year

        nominal_capacity = (
            self.design_capacity
            * (1. - self.lowest_discharge_level)
        )

        capacity = nominal_capacity * capacity_decrease
        return capacity, capacity_decrease