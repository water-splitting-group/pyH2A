from .species_data import SpeciesData
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

HYDROGEN = SpeciesData(
    molecular_weight = Quantity(2.016, 'g/mol'),
    liquid_volume_coefficients = np.array([0.014]),    
    solid_volume_coefficients = np.array([]),    
    vapour_enthalpy_coefficients = np.array([-2077374.2842351808, 6.86e3, 0.46, - 3.33e-4]),
    liquid_enthalpy_coefficients = np.array([-2853700.0, 10e3]), 
    solid_enthalpy_coefficients =  np.array([]),      
    combustion_enthalpy = Quantity(142.5e6, 'J/kg')    
)