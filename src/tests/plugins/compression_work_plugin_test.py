import pytest
from pyH2A.Plugins.Compression_Work_Plugin import Compression_Work_Plugin


class DummyDCF:
    """Minimal DCF object for Compression_Work_Plugin with configurable inputs."""

    def __init__(
        self,
        compressor_train,
        raw_product_gas,
        technical_operating_parameters_and_specifications,
        product_gas_properties
    ):

        self.inp = {
            "Compressor train": {
                key: {"Value": value} for key, value in compressor_train.items()
            },
            "Raw product gas": {
                key: {"Value": value} for key, value in raw_product_gas.items()
            },
            "Technical Operating Parameters and Specifications": {
                key: {"Value": value} for key, value in technical_operating_parameters_and_specifications.items()
            },  
            "Product gas properties": {
                key: {"Value": value} for key, value in product_gas_properties.items()
            }
        }
        



@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "compressor_train": {
                    "Outlet pressure": 20.7,
                    "Number of compression stages": 2,
                    "Compressor efficiency": 0.75,
                    "Combustion to shaft efficiency": 0.25,                    
                },
                "raw_product_gas": {
                    "Pressure": 1.,
                    "Temperature": 333.,
                    "Hydrogen molar fraction": 0.66
                },
                "technical_operating_parameters_and_specifications": {
                    "Design Output per Day" : 1111, 
                    "Maximum Output at Gate" : 1000.
                }, 
                "product_gas_properties":{}
            },
            "expected": {
                "outlet_temperature": 513.381243,
                "combustion_enthalpy_per_mixture": 188100.0,
                "compression_work": 101453.09223,
                "shaft_work": 135270.78964,
                "required_combustion_power": 541083.158532,
                "hydrogen_self_consumption_ratio": 0.33069180061,                
            }, 
        }            
    ],
)
def test_compression_work_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Compression_Work_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance 
    tolerance = 1e-4
    
    assert plugin.outlet_temperature == pytest.approx(
        expected["outlet_temperature"],
        abs=tolerance
    )
    
    assert plugin.combustion_enthalpy_per_mixture == pytest.approx(
        expected["combustion_enthalpy_per_mixture"],
        abs=tolerance
    )
    
    assert plugin.compression_work == pytest.approx(
        expected["compression_work"],
        abs=tolerance
    )

    assert plugin.shaft_work == pytest.approx(
        expected["shaft_work"],
        abs=tolerance
    )
    
    assert plugin.required_combustion_power == pytest.approx(
        expected["required_combustion_power"],
        abs=tolerance
    )
    
    assert plugin.hydrogen_self_consumption_ratio == pytest.approx(
        expected["hydrogen_self_consumption_ratio"],
        abs=tolerance
    )