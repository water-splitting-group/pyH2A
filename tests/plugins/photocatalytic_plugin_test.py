import pytest
import numpy as np
from src.pyH2A.Plugins.Photocatalytic_Plugin import Photocatalytic_Plugin


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
                "Design Output per Day": {"Value": design_output},
            },
            "Reactor Baggies": {
                "Cost Material Top ($/m2)": {"Value": top_cost},
                "Cost Material Bottom ($/m2)": {"Value": bottom_cost},
                "Number of ports": {"Value": ports},
                "Cost of port ($)": {"Value": port_cost},
                "Other Costs ($)": {"Value": other_costs},
                "Markup factor": {"Value": markup},
                "Length (m)": {"Value": length},
                "Width (m)": {"Value": width},
                "Height (m)": {"Value": height},
                "Additional land area (%)": {"Value": add_land},
                "Lifetime (years)": {"Value": baggie_lifetime},
            },
            "Catalyst": {
                "Cost per kg ($)": {"Value": catalyst_cost},
                "Concentration (g/L)": {"Value": catalyst_conc},
                "Lifetime (years)": {"Value": catalyst_lifetime},
                "Molar Weight (g/mol)": {"Value": molar_weight},
                "Molar Attenuation Coefficient (M^-1 cm^-1)": {
                    "Value": attenuation_coeff
                },
            },
            "Solar-to-Hydrogen Efficiency": {"STH (%)": {"Value": sth}},
            "Solar Input": {
                "Mean solar input (kWh/m2/day)": {"Value": solar_input},
                "Hourly (kWh/m2)": {"Value": hourly_solar, "Processed": "Yes"},
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_output": 1111,
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
                "solar_input": 5.5,
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
                "total_land_area_acres": 11.392780967100002,
                "total_solar_collection_area": 35465.4,
                "catalyst_cost": 2835458.73,
                "baggies_cost": 66834.53099999999,
                "baggie_number": 9.0,
                "catalyst_properties": {
                    "Peak activity / mmol H2/h/g": np.float64(26.106204419861132),
                    "Peak H2 production / mol H2/m2/h": np.float64(0.6957303477892992),
                    "Catalyst Conc. / kg/m2": 0.026650000000000004,
                    "Catalyst Conc. / g/L": 0.533,
                    "Homogeneous": {
                        "Catalyst Conc. / mol/L": 0.001066,
                        "Catalyst Conc. / mol/m2": 0.05330000000000001,
                        "Peak TOF / h^-1": np.float64(13.053102209930564),
                        "Mean daily TOF / d^-1": 313.27444848161434,
                        "TON": 57172.586847894614,
                        "Absorbance": 42.64000000000001,
                        "Absorbed light (%)": 100.0,
                    },
                },
                "total_volume_liters": 1773270.0,
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

    assert plugin.total_land_area_acres == pytest.approx(
        expected["total_land_area_acres"], 
        abs=tolerance
    )

    assert plugin.total_solar_collection_area == pytest.approx(
        expected["total_solar_collection_area"], 
        abs=tolerance
    )

    assert plugin.catalyst_cost == pytest.approx(
        expected["catalyst_cost"], 
        abs=tolerance
    )

    assert plugin.baggies_cost == pytest.approx(
        expected["baggies_cost"], 
        abs=tolerance
    )

    assert plugin.baggie_number == pytest.approx(
        expected["baggie_number"], 
        abs=tolerance
    )
    
    assert plugin.catalyst_properties == expected["catalyst_properties"]

    assert plugin.total_volume_liters == pytest.approx(
        expected["total_volume_liters"], 
        abs=tolerance
    )
