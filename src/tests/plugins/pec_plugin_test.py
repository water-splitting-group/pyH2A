import pytest
import numpy as np
from pyH2A.Plugins.PEC_Plugin import PEC_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """Minimal DCF object for PEC_Plugin testing with configurable inputs."""

    def __init__(
        self,
        relative_years,
        output_by_year,
        operating_capacity_factor,
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
        self.functional_unit = resolve_functional_unit('kg[H2]')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": {'Operation years relative': relative_years},
                    "Unit": "-"
                },               
            },                
            "Technical Operating Parameters and Specifications": {
                "Design output by year": {
                    "Value": output_by_year, 
                    "Unit":"kg"
                },
                "Operating capacity factor": {
                    "Value": operating_capacity_factor, 
                    "Unit":"-"
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
                "Hourly": {
                    "Value": solar_input,
                    "Unit": "kWh / m2"
                }
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "relative_years":  np.array([0, 1]),
                "output_by_year": np.array([1000, 1000]),
                "operating_capacity_factor": 0.9,
                "cell_cost": 21000.0,
                "lifetime": 0.33,
                "length": 6.0,
                "width": 0.3,
                "cell_angle": 35.0,
                "south_spacing": 6.71,
                "east_spacing": 17.3,
                "sth": 0.14,
                "solar_input": np.array(
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
                "total_land_area": Quantity(5834943.363153812, 'm2'),
                "total_solar_collection_area": Quantity(51334.2, 'm2'),
                "cell_cost": Quantity(1078018199.9999998, 'USD'),
                "cell_number": Quantity(28519.0, '-'),
                "gross_yearly_mass": Quantity(np.array([8159.778720932961, 8159.778720932961]), 'kg'), 
                "net_yearly_mass" : Quantity(np.array([8042.410714285714, 8042.410714285714]), 'kg'),
                "outlet_enthalpy": {'first': Quantity(-608468.9013445798, 'J/kg'), 
                                        'last': Quantity(-608468.9013445798, 'J/kg')}, 
                "outlet_mass_fraction_H2": {'first':Quantity(0.9200146070273004, '-'),
                                         'last':Quantity(0.9200146070273004, '-')
                                        }, 
                "hourly_mass_flow": {'first': Quantity(54.346963209157295, 'kg'), 
                                        'last': Quantity(0, 'kg')},                
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
    

    assert plugin.total_land_area.unit['m2'] == pytest.approx(
        expected["total_land_area"].unit['m2'],
        abs=tolerance
    )
    
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
        
    assert plugin.gross_yearly_mass.unit["kg"] == pytest.approx(
        expected["gross_yearly_mass"].unit["kg"], 
        abs=tolerance
    )

    assert plugin.net_yearly_mass.unit["kg"] == pytest.approx(
        expected["net_yearly_mass"].unit["kg"], 
        abs=tolerance
    )    

    assert plugin.outlet_enthalpy[0].unit["J/kg"][0] == pytest.approx(
        expected["outlet_enthalpy"]['first'].unit["J/kg"], 
        abs=tolerance
    )        

    assert plugin.outlet_enthalpy[1].unit["J/kg"][-1] == pytest.approx(
        expected["outlet_enthalpy"]['last'].unit["J/kg"], 
        abs=tolerance
    )   

    assert plugin.outlet_mass_fraction[0]['H2'].unit["-"][0] == pytest.approx(
        expected["outlet_mass_fraction_H2"]['first'].unit["-"], 
        abs=tolerance
    )        

    assert plugin.outlet_mass_fraction[1]['H2'].unit["-"][-1] == pytest.approx(
        expected["outlet_mass_fraction_H2"]['last'].unit["-"], 
        abs=tolerance
    )  

    assert plugin.hourly_mass_flow[0].unit["kg"][0] == pytest.approx(
        expected["hourly_mass_flow"]['first'].unit["kg"], 
        abs=tolerance
    )        

    assert plugin.hourly_mass_flow[1].unit["kg"][-1] == pytest.approx(
        expected["hourly_mass_flow"]['last'].unit["kg"], 
        abs=tolerance
    )                   
