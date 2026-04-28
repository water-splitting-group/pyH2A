import pytest
import numpy as np
from pyH2A.Plugins.PEC_Plugin import PEC_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """Minimal DCF object for PEC_Plugin testing with configurable inputs."""

    def __init__(
        self,
        design_output,
        cell_cost,
        lifetime,
        length,
        width,
        cell_angle,
        south_spacing,
        east_spacing,
        sth,
        solar_input,        
    ):
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Design output per day": {
                    "Value": design_output,
                    "Unit": "kg",
                },
            },
            "PEC Cells": {
                "Cell cost": {
                    "Value": cell_cost,
                    "Unit": "USD/m2"
                },
                "Lifetime": {
                    "Value": lifetime,
                    "Unit": "year"
                },
                "Length": {
                    "Value": length,
                    "Unit": "m"
                },
                "Width": {
                    "Value": width,
                    "Unit": "m"
                },
            },
            "Land Area Requirement": {
                "Cell angle": {
                    "Value": cell_angle,
                    "Unit": "deg"
                },
                "South spacing": {
                    "Value": south_spacing,
                    "Unit": "m"
                },
                "East/West spacing": {
                    "Value": east_spacing,
                    "Unit": "m"
                },
            },
            "Solar-to-Hydrogen Efficiency": {
                "STH": {
                    "Value": sth,
                    "Unit": "-"
                }
            },
            "Solar Input": {
                "Mean solar input": {
                    "Value": solar_input,
                    "Unit": "W / m2"
                }
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_output": 1000.0,
                "cell_cost": 21000.0,
                "lifetime": 0.33,
                "length": 6.0,
                "width": 0.3,
                "cell_angle": 35.0,
                "south_spacing": 6.71,
                "east_spacing": 17.3,
                "sth": 0.14,
                "solar_input": 5.0,
            },
            "expected": {
                "total_land_area_acres": Quantity(1321.7195315319523, 'acre'),
                "total_solar_collection_area": Quantity(47057.399999999994, 'm2'),
                "cell_cost": Quantity(988205399.9999998, 'USD'),
                "cell_number": Quantity(26143.0, '-'),
                "mol_H2_per_m2_per_day": Quantity(10.62569970259003, 'mol/m2/day'),
                "kg_H2_per_cell": Quantity(0.0382525189293241, 'kg'),
                "total_land_area": Quantity(5348817.431990256, 'm2'),
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
    
    assert plugin.cell_cost == pytest.approx(
        expected["cell_cost"],
        abs=tolerance
    )
    
    assert plugin.cell_number == pytest.approx(
        expected["cell_number"],
        abs=tolerance
    )
    
    assert plugin.mol_H2_per_m2_per_day == pytest.approx(
        expected["mol_H2_per_m2_per_day"],
        abs=tolerance
    )
    
    assert plugin.kg_H2_per_cell == pytest.approx(
        expected["kg_H2_per_cell"],
        abs=tolerance
    )
    
    assert plugin.total_land_area == pytest.approx(
        expected["total_land_area"],
        abs=tolerance
    )
    
