import pytest
from pyH2A.Plugins.Catalyst_Separation_Plugin import Catalyst_Separation_Plugin


class DummyDCF:
    """Minimal DCF object for Catalyst_Separation_Plugin unit testing."""

    def __init__(
        self, water_volume_liters, filtration_cost_per_m3, catalyst_lifetime_years
    ):
        self.inp = {
            "Water Volume": {"Volume (liters)": {"Value": water_volume_liters}},
            "Catalyst": {"Lifetime (years)": {"Value": catalyst_lifetime_years}},
            "Catalyst Separation": {
                "Filtration cost ($/m3)": {"Value": filtration_cost_per_m3}
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "water_volume_liters": 0.0,
                "filtration_cost_per_m3": 50.0,
                "catalyst_lifetime_years": 5.0,
            },
            "expected": {
                "yearly_cost": 0,
            },
        },
        {
            "input": {
                "water_volume_liters": 0.0,
                "filtration_cost_per_m3": 0.0,
                "catalyst_lifetime_years": 5.0,
            },
            "expected": {
                "yearly_cost": 0,
            },
        },
        {
            "input": {
                "water_volume_liters": 10000.0,
                "filtration_cost_per_m3": 0.0,
                "catalyst_lifetime_years": 5.0,
            },
            "expected": {
                "yearly_cost": 0,
            },
        },
        {
            "input": {
                "water_volume_liters": 1000.0,
                "filtration_cost_per_m3": 50.0,
                "catalyst_lifetime_years": 2.0,
            },
            "expected": {
                "yearly_cost": 25.0,
            },
        },
    ],
)
def test_catalyst_separation_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Catalyst_Separation_Plugin(dcf, print_info=False)

    assert plugin.yearly_cost == case["expected"]["yearly_cost"]
