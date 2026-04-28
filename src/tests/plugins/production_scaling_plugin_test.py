import pytest
from pyH2A.Plugins.Production_Scaling_Plugin import Production_Scaling_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class DummyDCF:
    """Minimal DCF object for Production_Scaling_Plugin testing with configurable inputs."""
    
    def __init__(
        self,
        plant_capacity,
        capacity_factor,
        max_output,
        new_plant_capacity,
        scaling_ratio,
        capital_exponent,
        labor_exponent,
    ):
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Plant design capacity": {"Value": plant_capacity, "Unit":"kg/day"},
                "Operating capacity factor": {"Value": capacity_factor, "Unit":"-"},
                "Maximum output at gate": {"Value": max_output, "Unit":"kg/day"},
                "New plant design capacity": {"Value": new_plant_capacity, "Unit":"kg/day"},
                "Scaling ratio": {"Value": scaling_ratio, "Unit":"-"},
                "Capital scaling exponent": {"Value": capital_exponent, "Unit":"-"},
                "Labor scaling exponent": {"Value": labor_exponent, "Unit":"-"},
            }
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "plant_capacity": 100.0,
                "capacity_factor": 0.9,
                "max_output": 1000.0,
                "new_plant_capacity": 200.0,
                "scaling_ratio": 0.9,
                "capital_exponent": 0.79,
                "labor_exponent": 0.26
            },
            "expected": {
                "design_output_per_day": Quantity(200.0,"kg/day"),
                "max_gate_output_per_day": Quantity(2000.0,"kg/day"),
                "output_per_year": Quantity(65700.0,"kg/year"),
                "output_per_year_at_gate": Quantity(657000.0,"kg/year")
            }
        },
    ]
)
def test_production_scaling_plugin(case):
    """Test Production_Scaling_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Production_Scaling_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12
    
    assert plugin.design_output_per_day.unit['kg/s'] == pytest.approx(
        expected["design_output_per_day"].unit['kg/s'],
        abs=tolerance
    )
    
    assert plugin.max_gate_output_per_day.unit['kg/s'] == pytest.approx(
        expected["max_gate_output_per_day"].unit['kg/s'],
        abs=tolerance
    )
    
    assert plugin.output_per_year.unit['kg/s'] == pytest.approx(
        expected["output_per_year"].unit['kg/s'],
        abs=tolerance
    )
    
    assert plugin.output_per_year_at_gate.unit['kg/s'] == pytest.approx(
        expected["output_per_year_at_gate"].unit['kg/s'],
        abs=tolerance
    )