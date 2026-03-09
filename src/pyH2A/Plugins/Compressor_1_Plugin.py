import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table
from pyH2A.Utilities.Physical_Constants import Fluid_properties as FP
from pyH2A.Utilities.Process_flow_mapping import Process_flow_map as PFM

# This is based on the compressor plugin template
# The unit is here called Compressor 1 

# map the generic compressor inlet and outlet to the specifics of the flowsheet 
compressor_inlet = 'Raw product gas'
compressor_outlet = 'Compressor 1 outlet' 
compressor = 'Compressor 1'

class Compressor_1_Plugin:
    '''

    Parameters
    ----------
    Technical Operating Parameters and Specifications > Maximum Output at Gate > Value : float
        Amount of hydrogen effectively delivered after the separation step  
    Raw product gas > Species > Value : set, str
        Chemical species present at the inlet. Each species is defined by a string in the set.    
    Raw product gas > Flowrate > Value : float
        Fluid mass flowrate at the inlet of the unit operation.
    Raw product gas > Pressure > Value : float
        Pressure at the inlet of the unit operation.
    Raw product gas > Temperature > Value : float
        Temperature at the inlet of the unit operation.
    Raw product gas > Enthalpy > Value : float
        Specific enthalpy at the inlet of the unit operation.
    Raw product gas > Composition > Value : dict
        Mass fraction of the species at the inlet of the unit operation.       
    Compressor 1 outlet > Pressure > Value : float
        Pressure at the outlet of the first compressor.                
    Compressor 1 > Polytropic coefficient > Value : float, optional
        Polytropic coefficient of the compression (-). Defaults to 1.4.
    Compressor 1 > Compressor efficiency > Value : float
        Compression work per shaft work provided to the compressor (-).          
    Compressor 1 > Combustion to shaft efficiency > Value : float
        Actual shaft work obtained per energy obtained from combustion (-).   
    Product gas properties > Hydrogen combustion enthalpy > Value : float, optional
        Combustion enthalpy of hydrogen (J/mol). Defaults to 285E3.                  
        
    Returns
    -------
    Compressor 1 outlet > Species > Value : set, str
        Chemical species present at the outlet. Each species is defined by a string in the set.    
    Compressor 1 outlet > Flowrate > Value : float
        Fluid mass flowrate at the outlet of the unit operation.
    Compressor 1 outlet > Temperature > Value : float
        Temperature at the outlet of the unit operation.
    Compressor 1 outlet > Enthalpy > Value : float
        Specific enthalpy at the outlet of the unit operation.
    Compressor 1 outlet > Composition > Value : dict
        Mass fraction of the species at the outlet of the unit operation.
    Compressor 1 > Electricity input > Value : float 
        Electric power injected into the system 
    Compressor 1 Direct Capital Costs > Capital Cost ($) > Value : float
        Total cost of the unit apperatus.        
    '''        
        
    def __init__(self, dcf, print_info):        

        # read the specified outlet pressure from input file
        process_table(dcf.inp, 'Technical Operating Parameters and Specifications', 'Value')
        process_table(dcf.inp, compressor, 'Value')
        process_table(dcf.inp, compressor_outlet, 'Value')
        
        # Physics-based model
        if 'Polytropic coefficient' not in dcf.inp[compressor]:
            self.polytropic_coefficient = FP.IG_heat_capacity_ratio # ideal diatomic gas heat capacity ratio
            insert(dcf, compressor, 'Polytropic coefficient', 'Value', 
                self.polytropic_coefficient, __name__, print_info = print_info)
        else:
            self.polytropic_coefficient = dcf.inp[compressor]['Polytropic coefficient']['Value']

        if 'Hydrogen combustion enthalpy' not in dcf.inp['Product gas properties']:
            self.hydrogen_combustion_enthalpy = FP.H2_combustion_enthalpy_std
            insert(dcf, 'Product gas properties', 'Hydrogen combustion enthalpy', 'Value', 
                    self.hydrogen_combustion_enthalpy, __name__, print_info = print_info)
        else:
            self.hydrogen_combustion_enthalpy = dcf.inp['Product gas properties']['Hydrogen combustion enthalpy']['Value']            

        self.temperature_out(dcf)
        self.thermodynamic_compression_work(dcf)
        self.mechanical_work(dcf)
        self.compressor_cost(dcf)
        
        
        # insertion of the function results

        insert(dcf, compressor_outlet, 'Species', 'Value', 
        dcf.inp[compressor_inlet]['Species']['Value'], __name__, print_info = print_info)   
        insert(dcf, compressor_outlet, 'Flowrate', 'Value', 
        dcf.inp[compressor_inlet]['Flowrate']['Value'], __name__, print_info = print_info)           
        insert(dcf, compressor_outlet, 'Composition', 'Value', 
        dcf.inp[compressor_inlet]['Composition']['Value'], __name__, print_info = print_info)        
        
        insert(dcf, compressor, 'Electricity input', 'Value', 
        self.specific_compression_electricity, __name__, print_info = print_info)
        
        insert(dcf, 'Compressor 1 Direct Capital Costs', 'Capital Cost ($)', 'Value', 
        self.capital_cost, __name__, print_info = print_info)        

        insert(dcf, compressor_outlet, 'Temperature', 'Value', 
        self.outlet_temperature, __name__, print_info = print_info)
        
        insert(dcf, compressor_outlet, 'Enthalpy', 'Value', 
        FP.Enthalpy(dcf.inp[compressor_outlet]['Temperature']['Value'], dcf.inp[compressor_outlet]['Pressure']['Value'], dcf.inp[compressor_outlet]['Composition']['Value'], 'V'), __name__, print_info = print_info)        
    
        # Define all the internal methods hereafter
    def temperature_out(self, dcf):
        '''Calculation of the outlet temperature of the compressor.
        '''
        
        self.outlet_temperature =  dcf.inp[compressor_inlet]['Temperature']['Value'] * (dcf.inp[compressor_outlet]['Pressure']['Value']/dcf.inp[compressor_inlet]['Pressure']['Value'])**((self.polytropic_coefficient-1)/self.polytropic_coefficient)      

    def thermodynamic_compression_work(self, dcf):
        '''Calculation of the power associated to the pressure increase of the gas.
        '''
        MW_mixture = 1/(dcf.inp[compressor_inlet]['Composition']['Value']['H2'] / FP.MW['H2'] + dcf.inp[compressor_inlet]['Composition']['Value']['H2O'] /FP.MW['H2O']) 
        molar_flowrate_to_compress =  dcf.inp[compressor_inlet]['Flowrate']['Value'] / MW_mixture # mol / s
        self.compression_work = (dcf.inp[compressor_outlet]['Pressure']['Value']/dcf.inp[compressor_inlet]['Pressure']['Value'])**((self.polytropic_coefficient-1)/self.polytropic_coefficient)-1  
        self.compression_work *= FP.IG_constant * molar_flowrate_to_compress * dcf.inp[compressor_inlet]['Temperature']['Value'] * self.polytropic_coefficient / (self.polytropic_coefficient - 1)
        
    def mechanical_work(self, dcf):
        '''Calculation of the mechanical power to drive the compressors shafts, and of the elctricity consummed per unit of product available at gate.
        '''
        
        self.shaft_work = self.compression_work / dcf.inp[compressor]['Compressor efficiency']['Value']   
        self.specific_compression_electricity = self.shaft_work/(3.6e6 * dcf.inp['Technical Operating Parameters and Specifications']['Maximum Output at Gate']['Value']/86400) 
        
    def compressor_cost(self, dcf):
        self.capital_cost = self.shaft_work # assuming a capex of 1 $ per watt of power

