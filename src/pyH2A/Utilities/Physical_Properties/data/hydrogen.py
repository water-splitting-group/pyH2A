from .species_data import SpeciesData
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

'''
Liquid volume value established from NIST chemistry webbook SRD69 https://webbook.nist.gov/chemistry/fluid/ 
Heat capacity is assumed to be constant. Reference conditions: null enthalpy for hydrogen gas at 298.15 K.
'''

HYDROGEN = SpeciesData(
    molecular_weight = Quantity(2.016, 'g/mol'),
    liquid_volume_coefficients = np.array([0.014]),    
    solid_volume_coefficients = np.array([]),    
    vapour_enthalpy_coefficients = np.array([-4266.5e3, 14.31e3]),
    liquid_enthalpy_coefficients = np.array([]), 
    solid_enthalpy_coefficients =  np.array([]),      
    combustion_enthalpy = Quantity(142.5e6, 'J/kg'), 
    gas_viscosity_coefficients = {'Reference value': Quantity(0.884e-5, 'Pa*s'), 
                                  'Reference temperature': Quantity(293.15, 'K'),
                                  'Sutherland constant': Quantity(72, 'K') }, 
    liquid_viscosity_coefficients = np.array([]) 
)