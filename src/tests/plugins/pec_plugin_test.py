import pytest
import numpy as np
from pyH2A.Plugins.PEC_Plugin import PEC_Plugin


class DummyDCF:
    """Minimal DCF object for PEC_Plugin testing with configurable inputs."""

    def __init__(
        self,
        sth,
        cell_cost,
        length,
        width,
        cell_angle,
        south_spacing,
        east_spacing,
        solar_input,
        lifetime,
        conc_factor,
        design_output,
    ):
        self.inp = {
            "PEC Cells": {
                "Cell Cost ($/m2)": {"Value": cell_cost},
                "Lifetime (years)": {"Value": lifetime},
                "Length (m)": {"Value": length},
                "Width (m)": {"Value": width},
            },
            "Land Area Requirement": {
                "Cell Angle (degree)": {"Value": cell_angle},
                "South Spacing (m)": {"Value": south_spacing},
                "East/West Spacing (m)": {"Value": east_spacing},
            },
            "Solar Input": {"Mean solar input (kWh/m2/day)": {"Value": solar_input}},
            "Solar-to-Hydrogen Efficiency": {"STH (%)": {"Value": sth}},
            "Solar Concentrator": {
                "Concentration Factor": {"Value": conc_factor},
            },
            "Technical Operating Parameters and Specifications": {
                "Design Output per Day": {"Value": design_output},
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "sth": 0.14,
                "cell_cost": 21000.0,
                "length": 6,
                "width": 0.3,
                "cell_angle": 35,
                "south_spacing": 6.71,
                "east_spacing": 17.3,
                "solar_input": 5.0,
                "lifetime": 0.33,
                "conc_factor": 50,
                "design_output": 1000,
            },
            "expected": {
                "total_land_area_acres": 1321.7195315319523,
                "total_solar_collection_area": 47057.399999999994,
                "cell_cost": 988205399.9999998,
                "cell_number": 26143.0,
                "mol_H2_per_m2_per_day": 10.62569970259003,
                "kg_H2_per_cell": 0.0382525189293241,
                "total_land_area": 5348817.431990256,
            },
        },
    ],
)
def test_pec_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = PEC_Plugin(dcf, print_info=False)
    expected = case["expected"]

    assert plugin.total_land_area_acres == expected["total_land_area_acres"]
    assert plugin.total_solar_collection_area == expected["total_solar_collection_area"]
    assert plugin.cell_cost == expected["cell_cost"]
    assert plugin.cell_number == expected["cell_number"]
    assert plugin.mol_H2_per_m2_per_day == expected["mol_H2_per_m2_per_day"]
    assert plugin.kg_H2_per_cell == expected["kg_H2_per_cell"]
    assert plugin.total_land_area == expected["total_land_area"]
