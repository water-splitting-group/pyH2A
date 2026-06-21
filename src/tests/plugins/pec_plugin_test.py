import pytest
import numpy as np
from pyH2A.Plugins.PEC_Plugin import PEC_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity


class DummyDCF:
    """Minimal DCF object for PEC_Plugin testing with configurable inputs."""

    def __init__(
        self,
        design_capacity,
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
                "Plant design capacity": {
                    "Value": design_capacity,
                    "Unit": "kg/day",
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
                    "Unit": "kW / m2"
                }
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_capacity": 1000.0,
                "cell_cost": 21000.0,
                "lifetime": 0.33,
                "length": 6.0,
                "width": 0.3,
                "cell_angle": 35.0,
                "south_spacing": 6.71,
                "east_spacing": 17.3,
                "sth": 0.14,
                "solar_input": 5.0/24,
            },
            "expected": {
                "total_solar_collection_area": Quantity(47057.399999999994, 'm2'),
                "cell_cost": Quantity(988205399.9999998, 'USD'),
                "cell_number": Quantity(26143.0, '-'),
                "mol_H2_per_m2_per_day": Quantity(10.6256954979, 'mol/day/m2'),
                "flowrate_H2_per_cell": Quantity(0.0382525189293241, 'kg/day'),
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
    
    assert plugin.total_solar_collection_area.unit['m2'] == pytest.approx(
        expected["total_solar_collection_area"].unit['m2'],
        abs=tolerance
    )
    
    assert plugin.cell_cost.unit['USD'] == pytest.approx(
        expected["cell_cost"].unit['USD'],
        abs=tolerance
    )
    
    assert plugin.cell_number.unit['-'] == pytest.approx(
        expected["cell_number"].unit['-'],
        abs=tolerance
    )
    
    assert plugin.mol_rate_H2_per_surface.unit['mol/s/m2'] == pytest.approx(
        expected["mol_H2_per_m2_per_day"].unit['mol/s/m2'],
        abs=tolerance
    )
    
    assert plugin.mass_rate_H2_per_cell.unit['kg/s'] == pytest.approx(
        expected["flowrate_H2_per_cell"].unit['kg/s'],
        abs=tolerance
    )
    
    assert plugin.total_land_area.unit['m2'] == pytest.approx(
        expected["total_land_area"].unit['m2'],
        abs=tolerance
    )
    
