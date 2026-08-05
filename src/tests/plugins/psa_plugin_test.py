import pytest
import numpy as np
from pyH2A.Plugins.PSA_Plugin import PSA_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """Minimal DCF object for PSA_Plugin testing with configurable inputs."""

    def __init__(
        self,
        design_capacity,
        feed_adsorbate_mole_fraction,
        adsorbate_molar_mass,
        recovery,
        adsorption_time,
        number_of_beds,
        bed_void_fraction,
        bed_usage_fraction,
        uptake_fraction,
        residual_loading_fraction,
        bulk_density,
        reference_bed_volume,
        reference_cost,
        scaling_exponent,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Plant design capacity": {
                    "Value": design_capacity,
                    "Unit": "kg/day",
                },
            },
            "PSA": {
                "Feed adsorbate mole fraction": {
                    "Value": feed_adsorbate_mole_fraction,
                    "Unit": "-"
                },
                "Adsorbate molar mass": {
                    "Value": adsorbate_molar_mass,
                    "Unit": "g/mol"
                },
                "Recovery": {
                    "Value": recovery,
                    "Unit": "-"
                },
                "Adsorption time": {
                    "Value": adsorption_time,
                    "Unit": "minute"
                },
                "Number of beds": {
                    "Value": number_of_beds,
                    "Unit": "-"
                },
            },
            "PSA Adsorbent Parameters": {
                "Bed void fraction": {
                    "Value": bed_void_fraction,
                    "Unit": "-"
                },
                "Bed usage fraction": {
                    "Value": bed_usage_fraction,
                    "Unit": "-"
                },
                "Adsorption uptake fraction": {
                    "Value": uptake_fraction,
                    "Unit": "-"
                },
                "Residual loading fraction": {
                    "Value": residual_loading_fraction,
                    "Unit": "-"
                },
                "Bulk density": {
                    "Value": bulk_density,
                    "Unit": "kg/m3"
                },
            },
            "Reference PSA System": {
                "Reference bed volume": {
                    "Value": reference_bed_volume,
                    "Unit": "L"
                },
                "Reference cost": {
                    "Value": reference_cost,
                    "Unit": "USD"
                },
                "Scaling exponent": {
                    "Value": scaling_exponent,
                    "Unit": "-"
                },
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_capacity": 1500.0,
                "feed_adsorbate_mole_fraction": 0.33,
                "adsorbate_molar_mass": 32.0,
                "recovery": 0.85,
                "adsorption_time": 10.0,
                "number_of_beds": 4,
                "bed_void_fraction": 0.36,
                "bed_usage_fraction": 0.769,
                "uptake_fraction": 0.0390,
                "residual_loading_fraction": 0.00188,
                "bulk_density": 700.0,
                "reference_bed_volume": 6065.0,
                "reference_cost": 100000.0,
                "scaling_exponent": 0.5,
            },
            "expected": {
                "adsorbate_mass_flow": Quantity(0.1596824467763889, "kg/s"),
                "adsorbent_mass": Quantity(13425.61264991387, "kg"),
                "bed_volume": Quantity(29.96788537927203, "m3"),
                "psa_cost": Quantity(222286.2743505983, "USD"),
            },
        },
    ],
)
def test_psa_plugin(case):
    """Check plugin handles inputs without errors and returns correct bed sizing and cost."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = PSA_Plugin(dcf, print_info=False)
    expected = case["expected"]

    tolerance = 1e-12

    assert plugin.adsorbate_mass_flow.unit['kg/s'] == pytest.approx(
        expected["adsorbate_mass_flow"].unit['kg/s'],
        abs=tolerance
    )

    assert plugin.adsorbent_mass.unit['kg'] == pytest.approx(
        expected["adsorbent_mass"].unit['kg'],
        abs=tolerance
    )

    assert plugin.bed_volume.unit['m3'] == pytest.approx(
        expected["bed_volume"].unit['m3'],
        abs=tolerance
    )

    assert plugin.psa_cost.unit['USD'] == pytest.approx(
        expected["psa_cost"].unit['USD'],
        abs=tolerance
    )
