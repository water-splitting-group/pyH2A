from dataclasses import dataclass
import numpy as np

@dataclass
class SpeciesData:
    molecular_weight: object
    liquid_volume_coefficients: np.ndarray
    solid_volume_coefficients: np.ndarray
    vapour_enthalpy_coefficients: np.ndarray
    liquid_enthalpy_coefficients: np.ndarray
    solid_enthalpy_coefficients: np.ndarray
    combustion_enthalpy: object
    gas_viscosity_coefficients: dict
    liquid_viscosity_coefficients: np.ndarray