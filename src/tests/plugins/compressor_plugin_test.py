import pytest
from pyH2A.Plugins.Compressor_Plugin import Compressor_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts
import numpy as np


class DummyDCF:
    """DCF object for Compressor_Plugin with configurable inputs."""

    def __init__(
        self, relative_years, compression_ratio, efficiency, capacity_factor, temperature, pressure, specific_enthalpy, mass_fraction, hourly_mass_flow, yearly_mass, peak_flowrate
    ):
        
        self.functional_unit = resolve_functional_unit('kg')

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
                }                
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
                "Design mass flow by year": {
                    "Value": yearly_mass,
                    "Unit": "kg"
                },  
                "Peak mass flowrate": {
                    "Value": peak_flowrate,
                    "Unit": "kg/s"
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
                "capacity_factor": 0.9,
                "temperature": 40,
                "pressure": 1.01315e5,
                "specific_enthalpy": -1380293.484041347,
                "mass_fraction": {'H2': 0.10011201927262867, 'O2': 0.7944901767573346, 'H2O': 0.10539780397003685},
                "hourly_mass_flow": {0: np.arange(0, 2), 
                                     1: np.arange(2,4)},
                "yearly_mass": np.array([0.12844408083787381*86400*365, 0.12844408083787381*86400*365*2]),
                "peak_flowrate": 0.2

            },
            "expected": {
                "peak_compression_power": Quantity(87042.33143774077, 'W'),
                "peak_shaft_power": Quantity(116056.4419169877, 'W'),
                "hourly_shaft_energy": {0: Quantity(np.array([0, 580282.2095849385]), 'J'), 
                                        1: Quantity(np.array([1160564.419169877, 1740846.6287548153]), 'J')},
                "yearly_shaft_energy": Quantity(np.array([2115448551897.8577, 2115448551897.8577*2]), 'J'),
                "outlet_temperature": Quantity(495.9731104852541, 'K'),
                "outlet_pressure": Quantity(506575.0, 'Pa'),
                "outlet_enthalpy": Quantity(-945081.8268526432, 'J/kg'),
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

    assert plugin.peak_compression_power.base_value == case["expected"]["peak_compression_power"].base_value
    assert plugin.peak_shaft_power.base_value == case["expected"]["peak_shaft_power"].base_value
    check_dicts(plugin.hourly_shaft_energy, case["expected"]["hourly_shaft_energy"])
    np.testing.assert_allclose(plugin.yearly_shaft_energy.base_value,case["expected"]["yearly_shaft_energy"].base_value,rtol=1e-12,atol=1e-12,)      
    assert plugin.outlet_temperature.base_value == case["expected"]["outlet_temperature"].base_value
    assert plugin.outlet_pressure.base_value == case["expected"]["outlet_pressure"].base_value
    assert plugin.outlet_enthalpy.base_value == case["expected"]["outlet_enthalpy"].base_value
