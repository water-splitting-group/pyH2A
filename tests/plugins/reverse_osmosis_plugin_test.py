import pytest
import numpy as np
from src.pyH2A.Plugins.Reverse_Osmosis_Plugin import Reverse_Osmosis_Plugin


class DummyDCF:
    """DCF object for Reverse_Osmosis_Plugin with configurable inputs."""

    def __init__(
        self, 
        construction_time,
        plant_output_per_year, 
        power_demand_kWh_per_m3, 
        avg_daily_hours, 
        recovery_rate
    ):
        self.inp = {
            "Financial Input Values": {
                "construction time": {"Value": construction_time}
            },
            "Technical Operating Parameters and Specifications": {
                "Output per Year": {"Value": plant_output_per_year, "Processed": "Yes"}
            },
            "Reverse Osmosis": {
                "Power Demand (kWh/m3)": {"Value": power_demand_kWh_per_m3},
                "Average daily operating hours": {"Value": avg_daily_hours},
                "Recovery Rate": {"Value": recovery_rate},
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
                "avg_daily_hours": 24.0,                  
                "recovery_rate": 0.1,                    
            },
            "expected": {
                "electricity_demand_kWh": np.array([1613.3471844103742, 1702.977583544284]),
                "max_capacity_m3_per_hour": 0.019440383373793193
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
        plugin.electricity_demand_kWh,
        expected["electricity_demand_kWh"],
        rtol=tolerance, 
        atol=tolerance
    )

    assert plugin.maximum_sea_water_processing_m3_per_hour == pytest.approx(
        expected["max_capacity_m3_per_hour"],
        abs=tolerance
    )
    
