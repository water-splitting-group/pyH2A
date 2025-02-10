from pyH2A.Utilities.input_modification import insert, process_table, daily_to_yearly_power
import numpy as np

class Power_Management_Plugin:
    '''Management of electricity production and consumption.
    
    Parameters
    ----------
	Power Generation > Available Power (daily, kWh) > Value : dict, optional
        Available power, daily basis, dictionary of years (in kWh)
    Power Generation > Stored Power (daily, kWh) > Value : dict, optional
        Stored power, daily basis, dictionary of years (in kWh)
    Power Consumption > [...] > Value : nd.array, optional
        Array of yearly power consumption values
    Power Consumption > [...] > Type : str, optional
        Type of power consumer, either 'flexible' for power consumer that can consume both 
        available power (not stored) or stored power, or 'on_demand' for power consumer that 
        can only consume stored power.
    Grid Electricity > Cost ($/kWh) > Value : float or nd.array, optional
        Cost of grid electricity in $/kWh, can be float or nd.array with same shape
        as Technical Operating Parameters and Specifications> Output per Year > Value

    Returns
    -------
    Power Generation > Available Power (yearly, kWh) > Value : nd.array
        Reamining available power, yearly basis, in kWh.
    Power Generation > Stored Power (yearly, kWh) > Value : nd.array
        Reamining stored power, yearly basis, in kWh.
    Power Generation > Available Power (daily, kWh) > Value : float
        Available power (daily, kWh) is set to zero, since available power is now 
        only in yearly format.
    Power Generation > Stored Power (daily, kWh) > Value : float
        Stored power (daily, kWh) is set to zero, since stored power is now
        only in yearly format.
    Grid Electricity > Used grid electricity (yearly, kWh) > Value : nd.array
        Used grid electricity, yearly basis, in kWh.
    Other Variable Operating Cost - Grid Electricity > Cost of grid electricity (yearly, $) > Value : nd.array
        Cost of grid electricity, yearly basis, in $.
    '''

    def __init__(self, dcf, print_info):

        if 'Power Generation' in dcf.inp:
            process_table(dcf.inp, 'Power Generation', 'Value')

        if 'Power Consumption' in dcf.inp:
            process_table(dcf.inp, 'Power Consumption', 'Value')
            process_table(dcf.inp, 'Grid Electricity', 'Value')
            self.calculate_consumers(dcf)
            self.calculate_electricity_cost(dcf)

        insert(dcf, 'Power Generation', 'Available Power (yearly, kWh)', 'Value',
               self.remaining_flexible, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Stored Power (yearly, kWh)', 'Value',
                self.remaining_stored, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Available Power (daily, kWh)', 'Value',
                0, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Stored Power (daily, kWh)', 'Value',
                0, __name__, print_info = print_info)
        
        insert(dcf, 'Grid Electricity', 'Used grid electricity (yearly, kWh)', 'Vale',
                self.total_unfulfilled, __name__, print_info = print_info)
        
        insert(dcf, 'Other Variable Operating Cost - Grid Electricity', 'Cost of grid electricity (yearly, $)', 'Value',
                self.electricity_cost, __name__, print_info = print_info)
        
    def calculate_consumers(self, dcf):
        '''Negoitate available and stored power with power consumers. 
        Including fall back options if power generation (either available power or stored power
        is not available). In those cases they are set to zero. 
        '''

        try:
            flexible_available_power = dcf.inp['Power Generation']['Available Power (daily, kWh)']['Value']
            flexible_available_power_yearly = daily_to_yearly_power(flexible_available_power)
        except KeyError:
            flexible_available_power_yearly = np.zeros(len(dcf.operation_years))

        try:
            stored_available_power = dcf.inp['Power Generation']['Stored Power (daily, kWh)']['Value']
            stored_available_power_yearly = daily_to_yearly_power(stored_available_power)
        except KeyError:
            stored_available_power_yearly = np.zeros(len(dcf.operation_years))

        self.total_unfulfilled, self.remaining_flexible, self.remaining_stored = allocate_power(dcf.inp['Power Consumption'], 
                                                                                                flexible_available_power_yearly, 
                                                                                                stored_available_power_yearly)

    def calculate_electricity_cost(self, dcf):

        cost_per_kWh = dcf.inp['Grid Electricity']['Cost ($/kWh)']['Value']

        electricity_cost = self.total_unfulfilled * cost_per_kWh

        self.electricity_cost = np.concatenate([np.zeros(dcf.inp['Financial Input Values']['construction time']['Value']), 
                                                electricity_cost])
    
def allocate_power(consumption, flexible_power, stored_power):
    """Allocate available power to consumers based on their type."""

    # Initialize remaining power
    remaining_flexible = flexible_power.copy()
    remaining_stored = stored_power.copy()
    
    # Initialize total unfufilled demand
    total_unfulfilled = np.zeros_like(flexible_power)
    
    # Process on_demand consumers first (stored power only)
    for key, consumer in consumption.items():
        if consumer['Type'] == 'on_demand':

            demand = consumer['Value']

            remaining_stored, unfulfilled = calculate_fulfillment(demand, remaining_stored)

            total_unfulfilled += unfulfilled
        
    # Process flexible consumers (both power sources)
    for key, consumer in consumption.items():
        if consumer['Type'] == 'flexible':

            demand = consumer['Value']
            
            # Try flexible power first
            remaining_flexible, remaining_demand = calculate_fulfillment(demand, remaining_flexible)

            # Use stored power for remaining demand
            remaining_stored, unfulfilled = calculate_fulfillment(remaining_demand, remaining_stored)
            
            total_unfulfilled += unfulfilled

        elif consumer['Type'] == 'on_demand':
            pass
        else:
            print('Warning: Unknown power consumer type:', consumer['Type'], f',    in Power Consumption > {key} > Type')
    
    return total_unfulfilled, remaining_flexible, remaining_stored
        
def calculate_fulfillment(demand, remaining):
    """Calculate fulfillment of demand using stored power."""
    
    fulfilled = np.minimum(demand, remaining)

    remaining -= fulfilled
    unfulfilled = demand - fulfilled
    
    return remaining, unfulfilled

