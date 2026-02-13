import pytest
from pyH2A.Plugins.Compression_Work_Plugin import Compression_Work_Plugin


class DummyDCF:
    """Minimal DCF object for CCompression_Work_Plugin with configurable inputs."""

    def __init__(
        self,
        compressor_train,
        product_gas_properties,

    ):

        self.inp = {
            "Compressor train": {
                key: {"Value": value} for key, value in compressor_train.items()
            },
            "Product gas properties": {
                key: {"Value": value} for key, value in product_gas_properties.items()
            },
        }
        



@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "compressor_train": {
                    "Inlet pressure": 1.0,
                    "Outlet pressure": 20.7,
                    "Number of compression stages": 2,
                    "Inlet temperature": 333,
                    "Molar flowrate": 1.0,
                    "Compressor efficiency": 0.75,
                    "Combustion to shaft efficiency": 0.25,                    
                },
                "product_gas_properties": {
                    "Hydrogen fraction in gas": 0.66,
                },
            },
            "expected": {
                "outlet_temperature": 240.381243+273.0,
                "combustion_enthalpy_per_mixture": 188100.0,
                "compression_work": 7498.4482710,
                "shaft_work": 9997.931028,
                "required_combustion_power": 39991.72411,
                "hydrogen_self_consumption_ratio": 0.212608847,                
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