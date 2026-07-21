from .species_data import SpeciesData
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np

WATER = SpeciesData(
    molecular_weight = Quantity(18.015, 'g/mol'),
    liquid_volume_coefficients = np.array([9.99806282e-04, -2.33664305e-09, 5.74608202e-09, -1.80098558e-11, 4.45840291e-14]),    
    solid_volume_coefficients = np.array([0.00109]),    
    vapour_enthalpy_coefficients = np.array([-13288237.908479081, -496.0, 0.23, -5e-5]),
    liquid_enthalpy_coefficients = np.array([-17106267.0, 4.18e3]), 
    solid_enthalpy_coefficients =  np.array([-16871308.7, 2098]),
    combustion_enthalpy = Quantity(0, 'J/kg')         
)