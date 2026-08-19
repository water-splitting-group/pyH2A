from .species_data import SpeciesData
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

'''
Liquid volume value established from NIST chemistry webbook SRD69 https://webbook.nist.gov/chemistry/fluid/ 
Heat capacity is assumed to be constant. Reference conditions: null enthalpy for oxygen gas at 298.15 K.
'''

OXYGEN = SpeciesData(
    molecular_weight = Quantity(31.998, 'g/mol'),
    liquid_volume_coefficients = np.array([0.00087]),    
    solid_volume_coefficients = np.array([]),    
    vapour_enthalpy_coefficients = np.array([-280.3e3, 940.]),
    liquid_enthalpy_coefficients = np.array([]), 
    solid_enthalpy_coefficients =  np.array([]),
    combustion_enthalpy = Quantity(0, 'J/kg'), 
    gas_viscosity_coefficients = {'Reference value': Quantity(2.018e-5, 'Pa*s'), 
                                  'Reference temperature': Quantity(293.15, 'K'),
                                  'Sutherland constant': Quantity(127, 'K') }, 
    liquid_viscosity_coefficients = np.array([])              
)