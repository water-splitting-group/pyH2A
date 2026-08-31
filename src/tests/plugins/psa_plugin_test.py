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
        operating_pressure,
        operating_temperature,
        feed_gas_velocity,
        length_to_diameter_ratio,
        number_of_beds,
        feed_gas_viscosity,
        bed_void_fraction,
        bed_usage_fraction,
        uptake_fraction,
        residual_loading_fraction,
        bulk_density,
        particle_diameter,
        adsorbent_cost_per_kg,
        adsorbent_replacement_interval,
        material,
        weld_efficiency,
        current_year_for_capital_costs,
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
                "Operating pressure": {
                    "Value": operating_pressure,
                    "Unit": "bar"
                },
                "Operating temperature": {
                    "Value": operating_temperature,
                    "Unit": "K"
                },
                "Feed gas velocity": {
                    "Value": feed_gas_velocity,
                    "Unit": "m/s"
                },
                "Length to diameter ratio": {
                    "Value": length_to_diameter_ratio,
                    "Unit": "-"
                },
                "Feed gas viscosity": {
                    "Value": feed_gas_viscosity,
                    "Unit": "Pa*s"
                },
                "Number of beds": {
                    "Value": number_of_beds,
                    "Unit": "-"
                },
                "Material": {
                    "Value": material,
                },
                "Weld efficiency": {
                    "Value": weld_efficiency,
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
                "Adsorbent particle diameter": {
                    "Value": particle_diameter,
                    "Unit": "mm"
                },
                "Adsorbent cost per kg": {
                    "Value": adsorbent_cost_per_kg,
                    "Unit": "USD/kg"
                },
                "Adsorbent replacement interval": {
                    "Value": adsorbent_replacement_interval,
                    "Unit": "year"
                },
            },
            "Financial Input Values": {
                "Current year for capital costs": {
                    "Value": current_year_for_capital_costs,
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
                "operating_pressure": 20.0,
                "operating_temperature": 300.0,
                "feed_gas_velocity": 0.35,
                "length_to_diameter_ratio": 3.0,
                "number_of_beds": 4,
                "feed_gas_viscosity": 1.5e-5,
                "bed_void_fraction": 0.36,
                "bed_usage_fraction": 0.769,
                "uptake_fraction": 0.0390,
                "residual_loading_fraction": 0.00188,
                "bulk_density": 700.0,
                "particle_diameter": 2.5,
                "adsorbent_cost_per_kg": 5.0,
                "adsorbent_replacement_interval": 4.0,
                "material": "low_alloy_steel",
                "weld_efficiency": 0.85,
                "current_year_for_capital_costs": 2016,
            },
            "expected": {
                "adsorbate_mass_flow": Quantity(0.1596824467763889, "kg/s"),
                "adsorbent_mass": Quantity(75.87353342504323, "kg"),
                "bed_volume": Quantity(0.16936056568090008, "m3"),
                "adsorption_time": Quantity(3.390841166218064, "s"),
                "vessel_steel_mass": Quantity(112.7970482746962, "kg"),
                "vessel_cost": Quantity(35416.51710185572, "USD"),
                "adsorbent_cost": Quantity(379.36766712521614, "USD"),
                "psa_cost": Quantity(35795.88476898094, "USD"),
                "pressure_drop": Quantity(9696.36612264019, "Pa"),
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

    assert plugin.adsorption_time.unit['s'] == pytest.approx(
        expected["adsorption_time"].unit['s'],
        abs=tolerance
    )

    assert plugin.vessel_steel_mass.unit['kg'] == pytest.approx(
        expected["vessel_steel_mass"].unit['kg'],
        abs=tolerance
    )

    assert plugin.vessel_cost.unit['USD'] == pytest.approx(
        expected["vessel_cost"].unit['USD'],
        abs=tolerance
    )

    assert plugin.adsorbent_cost.unit['USD'] == pytest.approx(
        expected["adsorbent_cost"].unit['USD'],
        abs=tolerance
    )

    assert plugin.psa_cost.unit['USD'] == pytest.approx(
        expected["psa_cost"].unit['USD'],
        abs=tolerance
    )

    assert plugin.pressure_drop.unit['Pa'] == pytest.approx(
        expected["pressure_drop"].unit['Pa'],
        abs=tolerance
    )
