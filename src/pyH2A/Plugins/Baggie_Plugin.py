import numpy as np
from pyH2A.Utilities.Energy_Conversion import Energy, kWh, eV
from pyH2A.Utilities.input_modification import insert, process_table
from pyH2A.Utilities.Physical_Constants import Fluid_properties as FP

class Baggie_Plugin:
    ''' Placeholder for future physics-based calculation of the output of the Baggie ; for the moment, hardcoding the properties of the produced mixture
    Parameters
    ----------

    Returns
    -------
    Raw product gas > Pressure > Value : float
        Gas pressure in the baggie (bar).  
    Raw product gas > Temperature > Value : float
        Temperature of the gas leaving the baggie (K).
    Raw product gas > Gas composition > Value : dict
        Mass fraction of the gas produced by the baggie (H2, O2, H2O).                      
    Raw product gas > Hydrogen molar fraction > Value : float
        Molar fraction of hydrogen in the product gas
    '''
    
    def __init__(self, dcf, print_info):    
        
        self.calculate_product_fluid_properties(dcf)
        
        insert(dcf, 'Raw product gas', 'Pressure', 'Value',
                self.Pressure, __name__, print_info = print_info)   
        insert(dcf, 'Raw product gas', 'Temperature', 'Value',
                self.Temperature, __name__, print_info = print_info) 
        insert(dcf, 'Raw product gas', 'Mass_fractions', 'Value',
                self.Mass_fractions, __name__, print_info = print_info) 
        insert(dcf, 'Raw product gas', 'Hydrogen_mol_fraction', 'Value',
                self.Hydrogen_mol_fraction, __name__, print_info = print_info)                 

    def calculate_product_fluid_properties(self, dcf):    
        self.Pressure = 1.02 # slight overpressure
        self.Temperature = 333 # 60 degC
        self.Mass_fractions = {'H2':0.08101, 'O2':0.64278, 'H2O':0.27621} # From Pinaud
        self.Hydrogen_mol_fraction = (self.Mass_fractions['H2']/FP.MW['H2'])/(self.Mass_fractions['H2']/FP.MW['H2']+self.Mass_fractions['O2']/FP.MW['O2']+self.Mass_fractions['H2O']/FP.MW['H2O'])