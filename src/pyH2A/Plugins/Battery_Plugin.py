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

    def __init__(self, dcf, print_info):

        inputs = input_resolver(battery_input_dict, dcf)

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
            daily_available_power = self.available_power_yearly[year]

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
