import pytest
import numpy as np
from pyH2A.Plugins.Replacement_Plugin import Replacement_Plugin

class DummyDCF:
    """Minimal DCF object for Replacement_Plugin with simple variable-value inputs."""
    def __init__(
        self,
        planned_replacement,
        unplanned_replacement,
        plant_years,
        combined_inflator,
        inflation_correction,
        inflation_factor
    ):
        self.inp = {
            "Planned Replacement": {
                key: {"Cost ($)": cost, "Frequency (years)": freq}
                for key, (cost, freq) in planned_replacement.items()
            },
            "Dummy Left Unplanned Replacement Dummy Right": {
                key: {"Value": value} for key, value in unplanned_replacement.items()
            }
        }
        
        self.plant_years = plant_years
        self.combined_inflator = combined_inflator
        self.inflation_correction = inflation_correction
        self.inflation_factor = inflation_factor


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "planned_replacement": {
                    "Electrolyzer Stack": (5000, 5),  # (cost, frequency)
                    "Valve": (2000, 3),
                },
                "unplanned_replacement": {
                    "Misc": 1000
                },
                "plant_years": np.arange(1, 11),
                "combined_inflator": 1.0,
                "inflation_correction": 1.0,
                "inflation_factor": np.ones(10),
            },
            "expected": {
                "total": 26000.0,
            },
        }
    ]
)
def test_replacement_plugin(case):
    """Test Replacement_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Replacement_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12
    
    assert np.sum(plugin.yearly) == pytest.approx(
        expected["total"],
        abs=tolerance
    )
