import pytest
import numpy as np
from pyH2A.Plugins.Reverse_Osmosis_Plugin import Reverse_Osmosis_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """DCF object for Reverse_Osmosis_Plugin with configurable inputs."""

    def __init__(
        self, 
        construction_time,
        plant_output_per_year, 
        power_demand_kWh_per_m3, 
        operating_time_fraction, 
        recovery_rate
    ):
        self.inp = {
            "Financial Input Values": {
                "construction time": {
                    "Value": construction_time,
                    "Unit": "year",
                }
            },
            "Technical Operating Parameters and Specifications": {
                "Output per year": {
                    "Value": plant_output_per_year, 
                    "Unit": "kg / year",
                    "Processed": "Yes"
                }
            },
            "Reverse Osmosis": {
                "Power demand": {
                    "Value": power_demand_kWh_per_m3,
                    "Unit": "kWh / m3",
                },
                "Average operating time fraction": {
                    "Value": operating_time_fraction,
                    "Unit": "-"
                },
                "Recovery rate": {
                    "Value": recovery_rate,
                    "Unit": "-"
                },
            },
        }
        

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "plant_output_per_year": np.array([0.0, 1800.0, 1900.0]),      
                "construction_time": 1,                   
                "power_demand_kWh_per_m3": 10.0,          
                "operating_time_fraction": 1.,                  
                "recovery_rate": 0.1,                    
            },
            "expected": {
                "electricity_demand_kWh": Quantity(np.array([1613.3471844103742, 1702.977583544284]), "kWh"),
                "max_capacity_m3_per_hour": Quantity(0.019440383373793193, "m3/h")
            },
        }
    ]
)
def test_reverse_osmosis_plugin(case):
    """Test Reverse_Osmosis_Plugin using base inputs (direct names style)."""
    
    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Reverse_Osmosis_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.electricity_demand.unit["J"],
        expected["electricity_demand_kWh"].unit["J"],
        rtol=tolerance, 
        atol=tolerance
    )

    assert plugin.maximum_sea_water_processing_flowrate.unit["m3/s"] == pytest.approx(
        expected["max_capacity_m3_per_hour"].unit["m3/s"],
        abs=tolerance
    )
    
