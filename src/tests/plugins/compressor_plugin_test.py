import pytest
from pyH2A.Plugins.Compressor_Plugin import Compressor_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """DCF object for Compressor_Plugin with configurable inputs."""

    def __init__(
        self, compression_ratio, efficiency, temperature, pressure, specific_enthalpy, mass_fraction, mass_flowrate
    ):
        self.inp = {
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
                "Mass flowrate": {
                    "Value": mass_flowrate,
                    "Unit": "kg/s"
                },                                                                                
                                
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "compression_ratio": 5,
                "efficiency": 0.75,
                "temperature": 40,
                "pressure": 1.01315e5,
                "specific_enthalpy": -1380293.484041347,
                "mass_fraction": {'H2': 0.10011201927262867, 'O2': 0.7944901767573346, 'H2O': 0.10539780397003685},
                "mass_flowrate": 0.12844408083787381

            },
            "expected": {
                "compression_power": Quantity(55900.361277530894, 'W'),
                "shaft_power": Quantity(74533.81503670786, 'W'),
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

    assert plugin.compression_power.base_value == case["expected"]["compression_power"].base_value
    assert plugin.shaft_power.base_value == case["expected"]["shaft_power"].base_value
    assert plugin.outlet_temperature.base_value == case["expected"]["outlet_temperature"].base_value
    assert plugin.outlet_pressure.base_value == case["expected"]["outlet_pressure"].base_value
    assert plugin.outlet_enthalpy.base_value == case["expected"]["outlet_enthalpy"].base_value
