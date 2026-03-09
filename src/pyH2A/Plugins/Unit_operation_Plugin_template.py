import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table
from pyH2A.Utilities.Physical_Constants import Fluid_properties as FP

# This is a template for a generic unit operation
# The Input and output actual names need to be adapted in the docstrings and, importantly, in self.unit_inlet_* and self.unit_outlet_* to account for the actual flowsheet connections

class Unit_operation_Plugin_template:
    # the docstrings below are just an example, and treat the unit inlets/outlets as the model input/output, respectively.
    # in reality it's frequent to specify an outlet quantity and calculate an inlet value that matches the oulet expectation
    # the exact list of variable to read and to return is therefore to be adapted on a case-by-case basis
    # the important criterion is that after running the plugin, the unit's inlet and outlet fundamental variables (species present, T, P, H, composition, flowrate) are present in dcf.inp
    '''Generic template of a unit operation: the quantities of interest are calculated, whether from physics-based or data-driven models
    Importantly, the fundamental variables (T, P, H, composition, flowrate) as well as the species present at each inlet and outlet must be fully known after calculation
    extra quantities of interest are involved such as the amount of electricity or heat exchanged by the unit. These quantities can be specified, or be the result of the caluculation, so they are actually updated by the plugin.
    The associated quantities for further fixed and variable operating costs are also returned.
    This template is meant to be copy-pasted, renamed (as per the desired unit name) and edited as needed, in such a manner that the output of a unit can be the input of the next unit based on the same template

 Parameters
    ----------
    Inlet 1 Unit operation X > Species > Value : set, str
        Chemical species present at the inlet. Each species is defined by a string in the set.    
    Inlet 1 Unit operation X > Flowrate > Value : float
        Fluid mass flowrate at the inlet of the unit operation.
    Inlet 1 Unit operation X > Pressure > Value : float
        Pressure at the inlet of the unit operation.
    Inlet 1 Unit operation X > Temperature > Value : float
        Temperature at the inlet of the unit operation.
    Inlet 1 Unit operation X > Enthalpy > Value : float
        Specific enthalpy at the inlet of the unit operation.
    Inlet 1 Unit operation X > Composition > Value : dict
        Mass fraction of the species at the inlet of the unit operation.
    Inlet 2 Unit operation X > Species > Value : set, str
        Chemical species present at the inlet. Each species is defined by a string in the set.    
    Inlet 2 Unit operation X > Flowrate > Value : float
        Fluid mass flowrate at the inlet of the unit operation.
    Inlet 2 Unit operation X > Pressure > Value : float
        Pressure at the inlet of the unit operation.
    Inlet 2 Unit operation X > Temperature > Value : float
        Temperature at the inlet of the unit operation.
    Inlet 2 Unit operation X > Enthalpy > Value : float
        Specific enthalpy at the inlet of the unit operation.
    Inlet 2 Unit operation X > Composition > Value : dict
        Mass fraction of the species at the inlet of the unit operation.
    Unit operation X > Heat rate input > Value : float 
        Thermal power injected into the system
    Unit operation X > Electricity input > Value : float 
        Electric power injected into the system
    Unit operation X > Mechanical power input > Value : float 
        Mechanical power (of non-electric origin) injected into the system        
    Unit operation X > Other input 1 > Value : float, optional 
        Any other quantity needed for the calculation. Could also be an array, or a dict, or anything useful        
        
    Returns
    -------
    Outlet 1 Unit operation X > Species > Value : set, str
        Chemical species present at the outlet. Each species is defined by a string in the set.    
    Outlet 1 Unit operation X > Flowrate > Value : float
        Fluid mass flowrate at the outlet of the unit operation.
    Outlet 1 Unit operation X > Pressure > Value : float
        Pressure at the outlet of the unit operation.
    Outlet 1 Unit operation X > Temperature > Value : float
        Temperature at the outlet of the unit operation.
    Outlet 1 Unit operation X > Enthalpy > Value : float
        Specific enthalpy at the outlet of the unit operation.
    Outlet 1 Unit operation X > Composition > Value : dict
        Mass fraction of the species at the outlet of the unit operation.
    Outlet 2 Unit operation X > Species > Value : set, str
        Chemical species present at the outlet. Each species is defined by a string in the set.    
    Outlet 2 Unit operation X > Flowrate > Value : float
        Fluid mass flowrate at the outlet of the unit operation.
    Outlet 2 Unit operation X > Pressure > Value : float
        Pressure at the outlet of the unit operation.
    Outlet 2 Unit operation X > Temperature > Value : float
        Temperature at the outlet of the unit operation.
    Outlet 2 Unit operation X > Enthalpy > Value : float
        Specific enthalpy at the outlet of the unit operation.
    Outlet 2 Unit operation X > Composition > Value : dict
        Mass fraction of the species at the outlet of the unit operation.
    Unit operation X > Heat rate input > Value : float 
        Thermal power injected into the system
    Unit operation X > Electricity input > Value : float 
        Electric power injected into the system
    Unit operation X > Mechanical power input > Value : float 
        Mechanical power (of non-electric origin) injected into the system        
    Planned Replacement > Planned Replacement Unit operation X Consumable > Cost ($) : float
        Total cost of completely replacing a consumable of the unit once.
    Planned Replacement > Planned Replacement Unit operation X Consumable > Frequency (years) : float
        Replacement frequency of the Consumable in years, identical to consumable lifetime.    
    Unit operation X Direct Capital Costs > Capital Cost 1 ($) > Value : float
        Total cost of the unit apperatus.        
    '''        
        
    def __init__(self, dcf, print_info):
        # map the generic compressor inlet and outlet to the specifics of the flowsheet 
        self.Unit_X_inlet_1 = 'Inlet 1 Unit operation X'
        self.Unit_X_inlet_2 = 'Inlet 2 Unit operation X'
        self.Unit_X_outlet_1 = 'Outlet 1 Unit operation X'                
        self.Unit_X_outlet_2 = 'Outlet 2 Unit operation X'                
        # note that we are also processing the variables on the outlet side, which is actually a good thing, as per the previous comment about the docstrings
        process_table(dcf.inp, self.Unit_X_inlet_1, 'Value')
        process_table(dcf.inp, self.Unit_X_inlet_2, 'Value')
        process_table(dcf.inp, self.Unit_X_outlet_1, 'Value')
        process_table(dcf.inp, self.Unit_X_outlet_2, 'Value')        
        process_table(dcf.inp, 'Unit operation X', 'Value')          
        
        # Call all the needed methods for the calculation here
        self.my_function(dcf)
        
        
        # insertion of the function results
        insert(dcf, Unit_X_outlet_1, 'Species', 'Value', 
        self.Outlet_1_species, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_1, 'Flowrate', 'Value', 
        self.Outlet_1_flowrate, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_1, 'Pressure', 'Value', 
        self.Outlet_1_pressure, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_1, 'Temperature', 'Value', 
        self.Outlet_1_temperature, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_1, 'Enthalpy', 'Value', 
        self.Outlet_1_enthalpy, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_1, 'Composition', 'Value', 
        self.Outlet_1_composition, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_2, 'Species', 'Value', 
        self.Outlet_2_species, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_2, 'Flowrate', 'Value', 
        self.Outlet_2_flowrate, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_2, 'Pressure', 'Value', 
        self.Outlet_2_pressure, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_2, 'Temperature', 'Value', 
        self.Outlet_2_temperature, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_2, 'Enthalpy', 'Value', 
        self.Outlet_2_enthalpy, __name__, print_info = print_info)
        
        insert(dcf, Unit_X_outlet_2, 'Composition', 'Value', 
        self.Outlet_2_composition, __name__, print_info = print_info)
        
        insert(dcf, 'Unit operation X', 'Heat rate input', 'Value', 
        self.Heat_rate_input, __name__, print_info = print_info)
        
        insert(dcf, 'Unit operation X', 'Electricity input', 'Value', 
        self.Electricity_input, __name__, print_info = print_info)
        
        insert(dcf, 'Unit operation X', 'Mechanical power input', 'Value', 
        self.Mechanical_power_input, __name__, print_info = print_info)        

        insert(dcf, 'Planned Replacement', 'Planned Replacement Unit operation X Consumable', 'Cost ($)', 
        self.planned_replacement_cost, __name__, print_info = print_info)        
        
        insert(dcf, 'Planned Replacement', 'Planned Replacement Unit operation X Consumable', 'Frequency (years)', 
        self.planned_replacement_frequency, __name__, print_info = print_info)      
        
        insert(dcf, 'Unit operation X Direct Capital Costs', 'Capital Cost 1 ($)', 'Value', 
        self.capital_cost_1, __name__, print_info = print_info)        
        
        # Define all the internal methods hereafter
        
    def my_function(self, dcf):
        

