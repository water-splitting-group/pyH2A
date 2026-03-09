import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table
from pyH2A.Utilities.Physical_Constants import Fluid_properties as FP

# This is a template for a generic cooler with possible condensation of part of the water contained in the inlet gas mixture. The vapour and the liquid phase are directed toward two different outlets. Gas dissolution in the liquid water is ignored

# map the generic compressor inlet and outlet to the specifics of the flowsheet 
Cooler_condenser_inlet = 'Cooler condenser Inlet'
Cooler_condenser_outlet_gas = 'Cooler condenser outlet gas'                
Cooler_condenser_outlet_liq = 'Cooler condenser outlet liq'                
Cooler_condenser = 'Cooler condenser'

class Cooler_condenser_Plugin_template:

    '''
 Parameters
    ----------
    Cooler condenser Inlet > Species > Value : set, str
        Chemical species present at the inlet. Each species is defined by a string in the set.    
    Cooler condenser Inlet > Flowrate > Value : float
        Fluid mass flowrate at the inlet of the unit operation.
    Cooler condenser Inlet > Pressure > Value : float
        Pressure at the inlet of the unit operation.
    Cooler condenser Inlet > Temperature > Value : float
        Temperature at the inlet of the unit operation.
    Cooler condenser Inlet > Enthalpy > Value : float
        Specific enthalpy at the inlet of the unit operation.
    Cooler condenser Inlet > Composition > Value : dict
        Mass fraction of the species at the inlet of the unit operation.
    Cooler condenser > Outlet temperature > Value : float
        Temperature at the outlet of the unit operation.
        
    Returns
    -------
    Cooler condenser outlet gas > Species > Value : set, str
        Chemical species present at the outlet. Each species is defined by a string in the set.    
    Cooler condenser outlet gas > Flowrate > Value : float
        Fluid mass flowrate at the outlet of the unit operation.
    Cooler condenser outlet gas > Pressure > Value : float
        Pressure at the outlet of the unit operation.
    Cooler condenser outlet gas > Temperature > Value : float
        Temperature at the outlet of the unit operation.
    Cooler condenser outlet gas > Enthalpy > Value : float
        Specific enthalpy at the outlet of the unit operation.
    Cooler condenser outlet gas > Composition > Value : dict
        Mass fraction of the species at the outlet of the unit operation.
    Cooler condenser outlet liq > Species > Value : set, str
        Chemical species present at the outlet. Each species is defined by a string in the set.    
    Cooler condenser outlet liq > Flowrate > Value : float
        Fluid mass flowrate at the outlet of the unit operation.
    Cooler condenser outlet liq > Pressure > Value : float
        Pressure at the outlet of the unit operation.
    Cooler condenser outlet liq > Temperature > Value : float
        Temperature at the outlet of the unit operation.
    Cooler condenser outlet liq > Enthalpy > Value : float
        Specific enthalpy at the outlet of the unit operation.
    Cooler condenser outlet liq > Composition > Value : dict
        Mass fraction of the species at the outlet of the unit operation.
    Cooler condenser > Heat rate input > Value : float 
        Thermal power injected into the system
    Cooler condenser Direct Capital Costs > Capital Cost 1 ($) > Value : float
        Total cost of the unit apperatus.        
    '''        
        
    def __init__(self, dcf, print_info):
        # note that we are also processing the variables on the outlet side, which is actually a good thing, as per the previous comment about the docstrings
        process_table(dcf.inp, Cooler_condenser, 'Value')          
        
        # Call all the needed methods for the calculation here
        self.imposed_outlet_conditions(dcf)
        self.mass_balance(dcf)
        self.energy_balance(dcf)
        self.cooler_capex(dcf)        
        
        # insertion of the function results
        insert(dcf, Cooler_condenser_outlet_gas, 'Species', 'Value', 
        self.Outlet_1_species, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_gas, 'Flowrate', 'Value', 
        self.Outlet_1_flowrate, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_gas, 'Pressure', 'Value', 
        self.Outlet_1_pressure, __name__, print_info = print_info)

        insert(dcf, Cooler_condenser_outlet_gas, 'Temperature', 'Value', 
        self.Outlet_1_temperature, __name__, print_info = print_info)        
        
        insert(dcf, Cooler_condenser_outlet_gas, 'Enthalpy', 'Value', 
        self.Outlet_1_enthalpy, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_gas, 'Composition', 'Value', 
        self.Outlet_1_composition, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_liq, 'Species', 'Value', 
        self.Outlet_2_species, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_liq, 'Flowrate', 'Value', 
        self.Outlet_2_flowrate, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_liq, 'Pressure', 'Value', 
        self.Outlet_2_pressure, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_liq, 'Temperature', 'Value', 
        self.Outlet_2_temperature, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_liq, 'Enthalpy', 'Value', 
        self.Outlet_2_enthalpy, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser_outlet_liq, 'Composition', 'Value', 
        self.Outlet_2_composition, __name__, print_info = print_info)
        
        insert(dcf, Cooler_condenser, 'Heat rate input', 'Value', 
        self.Heat_rate_input, __name__, print_info = print_info)
        
        insert(dcf, 'Cooler condenser Direct Capital Costs', 'Capital Cost 1 ($)', 'Value', 
        self.capital_cost, __name__, print_info = print_info)        
        
        # Define all the internal methods hereafter
        
    def imposed_outlet_conditions(self, dcf):
        ''' Pressure is assumed to be constant in the condenser
        The outlet temperature is specified for the cooler as a whole
        '''
        self.Outlet_1_pressure = dcf.inp[Cooler_condenser_inlet]['Pressure']['Value']
        self.Outlet_2_pressure = dcf.inp[Cooler_condenser_inlet]['Pressure']['Value']
        self.Outlet_1_temperature = dcf.inp[Cooler_condenser]['Outlet temperature']['Value']
        self.Outlet_2_temperature = dcf.inp[Cooler_condenser]['Outlet temperature']['Value']            

    def mass_balance(self, dcf):
        ''' Determination of the partial pressure of vapour at the outlet temperature
            Followed by a calculation of the water amount in the respective phases
            The other gases are not affected by condensation 
        '''
        self.Outlet_2_species = {'H2O'}        
        water_pressure = FP.water_saturation_pressure(self.Outlet_2_temperature) # bars
        water_condensate_fraction = 1 - (water_pressure/(self.Outlet_2_pressure-water_pressure)) * (FP.MW['H2O'] / FP.MW['H2']) * (dcf.inp[Cooler_condenser_inlet]['Composition']['Value']['H2'] / dcf.inp[Cooler_condenser_inlet]['Composition']['Value']['H2O'])
        self.Outlet_2_flowrate = water_condensate_fraction * dcf.inp[Cooler_condenser_inlet]['Composition']['Value']['H2O'] * dcf.inp[Cooler_condenser_inlet]['Flowrate']['Value']
        self.Outlet_2_composition = {'H2O' : 1.0}

        self.Outlet_1_species = {'H2O', 'H2'}
        self.Outlet_1_flowrate = dcf.inp[Cooler_condenser_inlet]['Flowrate']['Value'] - self.Outlet_2_flowrate
        self.Outlet_1_composition = {'H2O' : 1.0 - dcf.inp[Cooler_condenser_inlet]['Composition']['Value']['H2'] * dcf.inp[Cooler_condenser_inlet]['Flowrate']['Value'] / self.Outlet_1_flowrate, 'H2' : dcf.inp[Cooler_condenser_inlet]['Composition']['Value']['H2'] * dcf.inp[Cooler_condenser_inlet]['Flowrate']['Value'] / self.Outlet_1_flowrate}
        

    def energy_balance(self, dcf):
        ''' Determination of the outlet enthalpies and of the heat input (negative because it cools down)
        '''
        self.Outlet_2_enthalpy = FP.Enthalpy(self.Outlet_2_temperature, self.Outlet_2_pressure, self.Outlet_2_composition, 'L')
        self.Outlet_1_enthalpy = FP.Enthalpy(self.Outlet_1_temperature, self.Outlet_1_pressure, self.Outlet_1_composition, 'V')       
        self.Heat_rate_input = self.Outlet_1_flowrate * self.Outlet_1_enthalpy + self.Outlet_2_flowrate * self.Outlet_2_enthalpy - dcf.inp[Cooler_condenser_inlet]['Flowrate']['Value'] * dcf.inp[Cooler_condenser_inlet]['Enthalpy']['Value']
        
    def cooler_capex(self, dcf):
        ''' extra fixed cost for cooling
        '''
        self.capital_cost = abs(self.Heat_rate_input) # 1 $ per watt to exchange