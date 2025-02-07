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
    Power Consumption > [...] > Value : nd.array
        Array of yearly power consumption values
    Power Consumption > [...] > Type : str
        Type of power consumer, either 'flexible' for power consumer that can consume both 
        available power (not stored) or stored power, or 'on_demand' for power consumer that 
        can only consume stored power.
    
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


    ### Inserting unfulfilled power #### 
    '''

    def __init__(self, dcf, print_info):

        if 'Power Generation' in dcf.inp:
            process_table(dcf.inp, 'Power Generation', 'Value')

        if 'Power Consumption' in dcf.inp:
            process_table(dcf.inp, 'Power Consumption', 'Value')
            self.calculate_consumers(dcf)

        insert(dcf, 'Power Generation', 'Available Power (yearly, kWh)', 'Value',
               self.remaining_flexible, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Stored Power (yearly, kWh)', 'Value',
                self.remaining_stored, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Available Power (daily, kWh)', 'Value',
                0, __name__, print_info = print_info)
        insert(dcf, 'Power Generation', 'Stored Power (daily, kWh)', 'Value',
                0, __name__, print_info = print_info)

        ### Inserting unfulfilled power ####
        ### Changing KeyError fall back to array generated based on dcf.operating_years
        ### Handling Power Consumption that is only supplied as float, not array

    def calculate_consumers(self, dcf):
        '''Calculation of electricity supply for flexible consumers
        '''

        consumption = dcf.inp['Power Consumption']

        try:
            flexible_available_power = dcf.inp['Power Generation']['Available Power (daily, kWh)']['Value']
            flexible_available_power_yearly = daily_to_yearly_power(flexible_available_power)
        except KeyError:
            flexible_available_power_yearly = np.zeros_like(consumption[next(iter(consumption))]['Value'])

        try:
            stored_available_power = dcf.inp['Power Generation']['Stored Power (daily, kWh)']['Value']
            stored_available_power_yearly = daily_to_yearly_power(stored_available_power)
        except KeyError:
            stored_available_power_yearly = np.zeros_like(consumption[next(iter(consumption))]['Value'])

        self.total_unfulfilled, self.remaining_flexible, self.remaining_stored = allocate_power(consumption, 
                                                                                                flexible_available_power_yearly, 
                                                                                                stored_available_power_yearly)

        # print(np.c_[flexible_available_power_yearly, self.remaining_flexible, self.remaining_flexible/flexible_available_power_yearly])
        # print(np.c_[stored_available_power_yearly, self.remaining_stored, self.remaining_stored/stored_available_power_yearly])
        # print('Unfulfilled', self.total_unfulfilled)        

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
    
    return total_unfulfilled, remaining_flexible, remaining_stored
        
def calculate_fulfillment(demand, remaining_stored):
    """Calculate fulfillment of demand using stored power."""
    
    fulfilled = np.minimum(demand, remaining_stored)
    remaining_stored -= fulfilled
    unfulfilled = demand - fulfilled
    
    return remaining_stored, unfulfilled