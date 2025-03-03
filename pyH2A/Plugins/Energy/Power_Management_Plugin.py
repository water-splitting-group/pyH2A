from pyH2A.Utilities.input_modification import daily_to_yearly_power
from pyH2A.Plugins.Plugin import Plugin
import numpy as np
import logging

class Power_Management_Plugin(Plugin):
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

    def __init__(
            self, 
            dcf: dict, 
            print_info: bool
            ) -> None:
        super().__init__(dcf, print_info)

        self.logger = logging.getLogger("pyH2A.Plugins.Energy.Power_Management_Plugin")
        self.logger.info("Starting Power_Management_Plugin")

        table_keys = []
        if 'Power Generation' in self.dcf.inp:
            table_keys.append('Power Generation')

        if 'Power Consumption' in self.dcf.inp:
            table_keys.append('Power Consumption')
            table_keys.append('Grid Electricity')
            self.calculate_consumers()
            self.calculate_electricity_cost()

        self.insert_table()
        
    def calculate_consumers(
            self
            ) -> None:
        '''Negoitate available and stored power with power consumers. 
        Including fall back options if power generation (either available power or stored power
        is not available). In those cases they are set to zero. 
        '''

        try:
            flexible_available_power = self.dcf.inp['Power Generation']['Available Power (daily, kWh)']['Value']
            flexible_available_power_yearly = daily_to_yearly_power(flexible_available_power)
        except KeyError:
            flexible_available_power_yearly = np.zeros(len(self.dcf.operation_years))

        try:
            stored_available_power = self.dcf.inp['Power Generation']['Stored Power (daily, kWh)']['Value']
            stored_available_power_yearly = daily_to_yearly_power(stored_available_power)
        except KeyError:
            stored_available_power_yearly = np.zeros(len(self.dcf.operation_years))

        (self.total_unfulfilled, 
         remaining_flexible, 
         remaining_stored) = allocate_power(
            self.dcf.inp['Power Consumption'], 
            flexible_available_power_yearly, 
            stored_available_power_yearly
        )
        self.insert_queue.extend([
            ('Power Generation', 'Available Power (yearly, kWh)', remaining_flexible),
            ('Power Generation', 'Stored Power (yearly, kWh)', remaining_stored),
            ('Power Generation', 'Available Power (daily, kWh)', 0),
            ('Power Generation', 'Stored Power (daily, kWh)', 0),
            ('Grid Electricity', 'Used grid electricity (yearly, kWh)', self.total_unfulfilled)
        ])

    def calculate_electricity_cost(
            self
            ) -> None:
        '''Calculate cost of grid electricity used to fulfill power consumption.
        '''

        cost_per_kWh = self.dcf.inp['Grid Electricity']['Cost ($/kWh)']['Value']

        electricity_cost = self.total_unfulfilled * cost_per_kWh

        self.electricity_cost = np.concatenate([np.zeros(self.dcf.inp['Financial Input Values']['construction time']['Value']), 
                                                electricity_cost])
        self.insert_queue.append(('Other Variable Operating Cost - Grid Electricity', 'Cost of grid electricity (yearly, $)', self.electricity_cost))
    
def allocate_power(
        consumption: dict, 
        flexible_power: np.ndarray, 
        stored_power: np.ndarray
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''Allocate available power to consumers based on their type.
    '''

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
        
def calculate_fulfillment(
        demand: np.ndarray, 
        remaining: np.ndarray
        ) -> tuple[np.ndarray, np.ndarray]:
    """Calculate fulfillment of demand using stored power."""
    
    fulfilled = np.minimum(demand, remaining)

    remaining -= fulfilled
    unfulfilled = demand - fulfilled
    
    return remaining, unfulfilled
