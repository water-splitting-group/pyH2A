from .species_data import SpeciesData
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
import numpy as np


OXYGEN = SpeciesData(
    molecular_weight = Quantity(31.998, 'g/mol'),
    liquid_volume_coefficients = np.array([0.00087]),    
    solid_volume_coefficients = np.array([]),    
    vapour_enthalpy_coefficients = np.array([-530612.50468932625, 9.453e2, 3.207, - 1.37e-3]),
    liquid_enthalpy_coefficients = np.array([-767634.0, 1.67e3]), 
    solid_enthalpy_coefficients =  np.array([]),
    combustion_enthalpy = Quantity(0, 'J/kg')         
)