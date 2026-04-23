import pytest
from src.pyH2A.Plugins.Production_Scaling_Plugin import Production_Scaling_Plugin

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
                "Plant Design Capacity (kg of H2/day)": {"Value": plant_capacity},
                "Operating Capacity Factor (%)": {"Value": capacity_factor},
                "Maximum Output at Gate": {"Value": max_output},
                "New Plant Design Capacity (kg of H2/day)": {"Value": new_plant_capacity},
                "Scaling Ratio": {"Value": scaling_ratio},
                "Capital Scaling Exponent": {"Value": capital_exponent},
                "Labor Scaling Exponent": {"Value": labor_exponent},
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
                "design_output_per_day": 200.0,
                "max_gate_output_per_day": 2000.0,
                "output_per_year": 65700.0,
                "output_per_year_at_gate": 657000.0
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
    
    assert plugin.design_output_per_day == pytest.approx(
        expected["design_output_per_day"],
        abs=tolerance
    )
    
    assert plugin.max_gate_output_per_day == pytest.approx(
        expected["max_gate_output_per_day"],
        abs=tolerance
    )
    
    assert plugin.output_per_year == pytest.approx(
        expected["output_per_year"],
        abs=tolerance
    )
    
    assert plugin.output_per_year_at_gate == pytest.approx(
        expected["output_per_year_at_gate"],
        abs=tolerance
    )