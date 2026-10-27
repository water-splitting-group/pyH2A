import pytest
from pyH2A.Plugins.Compressor_Plugin import Compressor_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts
import numpy as np


class DummyDCF:
    """DCF object for Compressor_Plugin with configurable inputs."""

    def __init__(
        self, relative_years, compression_ratio, efficiency, power_per_unit, weight_per_unit, capacity_factor, temperature, pressure, specific_enthalpy, mass_fraction, hourly_mass_flow
    ):
        
        self.functional_unit = resolve_functional_unit('kg[H2]')

        self.inp = {
            "Time": {
                "Years": {
                    "Value": {'Operation years relative': relative_years},
                    "Unit": "-"
                },               
            },             
            "Compressor": {
                "Compression ratio": {
                    "Value": compression_ratio,
                    "Unit": "-"
                }, 
                "Efficiency": {
                    "Value": efficiency,
                    "Unit": "-"
                },   
                "Power per compressor unit": {
                    "Value": power_per_unit,
                    "Unit": "kW"
                },
                "Weight per compressor unit": {
                    "Value": weight_per_unit,
                    "Unit": "kg"
                },                   
            },     
            "Technical Operating Parameters and Specifications": {
                "Operating capacity factor": {
                    "Value": capacity_factor,
                    "Unit": "-"
                },               
            },                 
            "Main Stream": {
                "Temperature": {
                    "Value": temperature,
                    "Unit": "degC"
                },
                "Pressure": {
                    "Value": pressure,
                    "Unit": "Pa"
                },
                "Specific enthalpy": {
                    "Value": specific_enthalpy,
                    "Unit": "J/kg"
                },
                "Mass fraction": {
                    "Value": mass_fraction,
                    "Unit": "-"
                },
                "Mass flow (hourly)": {
                    "Value": hourly_mass_flow,
                    "Unit": "kg"
                },          
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "relative_years":  np.array([0, 1]),
                "compression_ratio": 5,
                "efficiency": 0.75,
                "power_per_unit": 22,
                "weight_per_unit": 200,
                "capacity_factor": 0.9,
                "temperature": {0: np.asarray([40, 40]), 
                                1: np.asarray([40, 40])},
                "pressure": 1.01315e5,
                "specific_enthalpy": {0: np.asarray([-1380293.484041347, -1380293.484041347]), 
                                     1: np.asarray([-1380293.484041347,-1380293.484041347])},
                "mass_fraction": {0: {'H2': np.asarray([0.10011201927262867, 0.10011201927262867]), 'O2': np.asarray([0.7944901767573346,0.7944901767573346]), 'H2O': np.asarray([0.10539780397003685, 0.10539780397003685])}, 
                                  1: {'H2': np.asarray([0.10011201927262867, 0.10011201927262867]), 'O2': np.asarray([0.7944901767573346,0.7944901767573346]), 'H2O': np.asarray([0.10539780397003685, 0.10539780397003685])}},
                "hourly_mass_flow": {0: np.arange(0, 2), 
                                     1: np.arange(2,4)},
            },
            "expected": {
                "peak_shaft_power": Quantity(483.56850798744864, 'W'),
                "hourly_shaft_energy": {0: Quantity(np.array([0, 580282.2095849385]), 'J'), 
                                        1: Quantity(np.array([1160564.419169877, 1740846.6287548153]), 'J')},
                "yearly_shaft_energy": Quantity(np.array([522253.98862644454, 2611269.9431322226]), 'J'),
                "total_shaft_energy": Quantity(3133523.9317586673, 'J'),
                "number_compressor_units": Quantity(1, '-'),
                "mass_compressor":Quantity(200, 'kg'),
                "outlet_temperature": {0: Quantity(np.array([495.9731104852541, 495.9731104852541]), 'K'), 
                                       1: Quantity(np.array([495.9731104852541, 495.9731104852541]), 'K')},
                "outlet_pressure": Quantity(506575.0, 'Pa'),
                "outlet_enthalpy": {0: Quantity(np.array([-945081.8268526432, -945081.8268526432]), 'J/kg'), 
                                    1: Quantity(np.array([-945081.8268526432, -945081.8268526432]), 'J/kg')},
            },
        },
    ],
    ids=[
        "Realistic case - Post-condensation compression"
    ]
)
def test_compressor_plugin(case):
    """Check Compressor_Plugin calculates compresison work correctly."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Compressor_Plugin(dcf, print_info=False)

    assert plugin.peak_shaft_power.base_value == case["expected"]["peak_shaft_power"].base_value
    check_dicts(plugin.hourly_shaft_energy, case["expected"]["hourly_shaft_energy"])
    np.testing.assert_allclose(plugin.yearly_shaft_energy.base_value,case["expected"]["yearly_shaft_energy"].base_value,rtol=1e-12,atol=1e-12,)      
    assert plugin.total_shaft_energy.base_value == case["expected"]["total_shaft_energy"].base_value
    assert plugin.number_compressor_units.base_value == case["expected"]["number_compressor_units"].base_value
    assert plugin.mass_compressor.base_value == case["expected"]["mass_compressor"].base_value
    check_dicts(plugin.outlet_temperature, case["expected"]["outlet_temperature"])
    assert plugin.outlet_pressure.base_value == case["expected"]["outlet_pressure"].base_value
    check_dicts(plugin.outlet_enthalpy, case["expected"]["outlet_enthalpy"])
