import pytest
import numpy as np
from pyH2A.Plugins.Photocatalytic_Plugin import Photocatalytic_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """DCF object for Photocatalytic_Plugin with configurable inputs."""

    def __init__(
        self,
        design_output,
        top_cost,
        bottom_cost,
        ports,
        port_cost,
        other_costs,
        markup,
        length,
        width,
        height,
        add_land,
        baggie_lifetime,
        catalyst_cost,
        catalyst_conc,
        catalyst_lifetime,
        molar_weight,
        attenuation_coeff,
        sth,
        solar_input,
        hourly_solar,
    ):

        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Design output per day": {"Value": design_output, "Unit":"kg"},
            },
            "Reactor Baggies": {
                "Cost material top": {"Value": top_cost, "Unit":"USD/m2"},
                "Cost material bottom": {"Value": bottom_cost, "Unit":"USD/m2"},
                "Number of ports per baggie": {"Value": ports, "Unit":"-"},
                "Cost of port": {"Value": port_cost, "Unit":"USD"},
                "Other costs per baggie": {"Value": other_costs, "Unit":"USD"},
                "Markup factor": {"Value": markup, "Unit":"-"},
                "Length": {"Value": length, "Unit":"m"},
                "Width": {"Value": width, "Unit":"m"},
                "Filling height": {"Value": height, "Unit":"m"},
                "Additional land area": {"Value": add_land, "Unit":"-"},
                "Lifetime": {"Value": baggie_lifetime, "Unit":"year"},
            },
            "Catalyst": {
                "Cost per unit of mass": {"Value": catalyst_cost, "Unit":"USD/kg"},
                "Concentration": {"Value": catalyst_conc, "Unit":"g/liter"},
                "Lifetime": {"Value": catalyst_lifetime, "Unit":"year"},
                "Molar Weight": {"Value": molar_weight, "Unit":"g/mol"},
                "Molar attenuation coefficient": {
                    "Value": attenuation_coeff, "Unit":"liter/(cm * mol)"
                },
            },
            "Solar-to-Hydrogen Efficiency": {"STH": {"Value": sth, "Unit":"-"}},
            "Solar Input": {
                "Mean solar input": {"Value": solar_input, "Unit":"kW/m2"},
                "Hourly": {"Value": hourly_solar, "Unit":"kWh/m2", "Processed": "Yes"},
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_output": 1111.,
                "top_cost": 0.54,
                "bottom_cost": 0.47,
                "ports": 12,
                "port_cost": 30.0,
                "other_costs": 610.7,
                "markup": 1.5,
                "length": 323.0,
                "width": 12.2,
                "height": 0.05,
                "add_land": 0.30,
                "baggie_lifetime": 5.0,
                "catalyst_cost": 3000.0,
                "catalyst_conc": 0.533,
                "catalyst_lifetime": 0.5,
                "molar_weight": 500.0,
                "attenuation_coeff": 8000.0,
                "sth": 0.2,
                "solar_input": 5.5/24.,
                "hourly_solar": np.array(
                    [
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                        0.22916667,
                        0.22916667,
                        0.22916667,
                        0,
                    ]
                ),
            },
            "expected": {
                "total_land_area": Quantity(46105.020000000004,"m2"),
                "total_solar_collection_area": Quantity(35465.4,"m2"),
                "catalyst_cost": Quantity(2835458.73,"USD"),
                "baggies_cost": Quantity(66834.53099999999,"USD"),
                "baggie_number": Quantity(9,"-"),
                "total_volume": Quantity(1773270.0,"liter")
            },
        },
    ],
)
def test_photocatalytic_plugin_optional_catalyst(case):
    """Test Photocatalytic_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Photocatalytic_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.total_land_area.unit["m2"] == pytest.approx(
        expected["total_land_area"].unit["m2"], 
        abs=tolerance
    )

    assert plugin.total_solar_collection_area.unit["m2"] == pytest.approx(
        expected["total_solar_collection_area"].unit["m2"], 
        abs=tolerance
    )

    assert plugin.catalyst_cost.unit["USD"] == pytest.approx(
        expected["catalyst_cost"].unit["USD"], 
        abs=tolerance
    )

    assert plugin.baggies_cost.unit["USD"] == pytest.approx(
        expected["baggies_cost"].unit["USD"], 
        abs=tolerance
    )

    assert plugin.baggie_number.unit["-"] == pytest.approx(
        expected["baggie_number"].unit["-"], 
        abs=tolerance
    )

    assert plugin.total_volume.unit["liter"] == pytest.approx(
        expected["total_volume"].unit["liter"], 
        abs=tolerance
    )
