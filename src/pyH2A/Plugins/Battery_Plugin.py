from pyH2A.Utilities.input_modification import insert, process_table
import numpy as np

battery_input_dict = {
    'available_power_daily': {
        'top_level': 'Power Generation',
        'mid_level': 'Available Power (daily, kWh)',
        'lower_level': 'Value',
        'unit_key': 'Unit'
    },
    'design_capacity': {
        'top_level': 'Battery',
        'mid_level': 'Design Capacity (kWh)',
        'lower_level': 'Value',
        'unit_key': 'Unit'
    },
    'lowest_discharge_level': {
        'top_level': 'Battery',
        'mid_level': 'Lowest discharge level',
        'lower_level': 'Value',
        'unit_key': 'Unit'
    },
    'capacity_loss_per_year': {
        'top_level': 'Battery',
        'mid_level': 'Capacity loss per year',
        'lower_level': 'Value',
        'unit_key': 'Unit'
    },
    'round_trip_efficiency': {
        'top_level': 'Battery',
        'mid_level': 'Round trip efficiency',
        'lower_level': 'Value',
        'unit_key': 'Unit'
    },
}

battery_output_dict = {
    'yearly_recovered_power': {
        'top_level': 'Power Generation',
        'mid_level': 'Stored Power (daily, kWh)',
        'lower_level': 'Value',
        'unit': 'kWh'
    },
    'yearly_unstored_power': {
        'top_level': 'Power Generation',
        'mid_level': 'Available Power (daily, kWh)',
        'lower_level': 'Value',
        'unit': 'kWh'
    },
    'hourly_available_power': {
        'top_level': 'Power Generation',
        'mid_level': 'Available Power (hourly, kWh)',
        'lower_level': 'Value',
        'unit': 'kWh'
    }
}

def input_resolver(io_dict, dcf):
    """
    Resolve inputs from dcf.inp using an I/O specification dictionary.
    (Value-only; unit handling is out of scope.)
    """
    resolved = {}

    for name, spec in io_dict.items():
        top = spec['top_level']
        mid = spec['mid_level']
        low = spec['lower_level']

        # Ensure tables are expanded
        process_table(dcf.inp, top, low)

        resolved[name] = dcf.inp[top][mid][low]

    return resolved


def output_resolver(output_dict, values, dcf, print_info):
    """
    Insert outputs back into dcf.inp using output specification dictionary.
    """
    for name, spec in output_dict.items():
        top = spec['top_level']
        mid = spec['mid_level']
        low = spec['lower_level']
        unit = spec.get('unit')

        insert(
            dcf,
            top,
            mid,
            low,
            values[name],
            __name__,
            print_info=print_info
        )

        if unit is not None:
            insert(
                dcf,
                top,
                mid,
                'Unit',
                unit,
                __name__,
                print_info=print_info
            )

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