import pytest
import numpy as np
from pyH2A.Plugins.PEC_Plugin import PEC_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from tests.Utilities.check_dicts_for_testing import check_dicts

class DummyDCF:
    """Minimal DCF object for PEC_Plugin testing with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        design_output_by_year,
        cell_cost,
        lifetime,
        length,
        width,
        cell_angle,
        south_spacing,
        east_spacing,
        sth,
        hourly_solar,        
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_relative,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },                
            "Technical Operating Parameters and Specifications": {
                "Design output by year": {
                    "Value": design_output_by_year, 
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
                "Hourly": {
                    "Value": hourly_solar, 
                    "Unit":"kWh/m2", 
                    "Processed": "Yes"
                },
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {'Operation years relative': np.array([0,1])},       
                "design_output_by_year": np.array([1000*365, 1000*365]),
                "cell_cost": 21000.0,
                "lifetime": 0.33,
                "length": 6.0,
                "width": 0.3,
                "cell_angle": 35.0,
                "south_spacing": 6.71,
                "east_spacing": 17.3,
                "sth": 0.14,
                "hourly_solar": np.array(
                    [0.20833333333]*8760
                ),
            },
            "expected": {
                "total_solar_collection_area": Quantity(47057.399999999994, 'm2'),
                "cell_cost": Quantity(988205399.9999998, 'USD'),
                "cell_number": Quantity(26143.0, '-'),
                "mean_mol_rate_H2_per_surface": Quantity(10.625699702590028, 'mol/day/m2'),
                "mean_mass_rate_H2_per_cell": Quantity(0.0382525189293241, 'kg/day'),
                "total_land_area": Quantity(5348817.431990256, 'm2'),
                "cell_cost": Quantity(988205399.9999998, 'USD'), 
                "outlet_enthalpy": Quantity(-608468.9013445798, 'J/kg'), 
                "outlet_mass_fraction": {'H2': Quantity(0.9200146070273004, '-'),
                                         'H2O': Quantity(1-0.9200146070273004, '-'),
                                         },
                "hourly_mass_flow": {
                    0: Quantity(45.289136007631065*np.ones(8760), 'kg'), 
                    1: Quantity(45.289136007631065*np.ones(8760), 'kg')
                },
                "yearly_mass_flow": Quantity(np.array([396732.83142684825, 396732.83142684825]), 'kg'), 
                "peak_mass_flowrate": Quantity(1086.9392641831457, 'kg/day'),                 
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
    
    assert plugin.mean_mol_rate_H2_per_surface.unit['mol/s/m2'] == pytest.approx(
        expected["mean_mol_rate_H2_per_surface"].unit['mol/s/m2'],
        abs=tolerance
    )
    
    assert plugin.mean_mass_rate_H2_per_cell.unit['kg/s'] == pytest.approx(
        expected["mean_mass_rate_H2_per_cell"].unit['kg/s'],
        abs=tolerance
    )
    
    assert plugin.total_land_area.unit['m2'] == pytest.approx(
        expected["total_land_area"].unit['m2'],
        abs=tolerance
    )

    assert plugin.cell_cost.unit['USD'] == pytest.approx(
        expected["cell_cost"].unit['USD'],
        abs=tolerance
    )    

    assert plugin.outlet_enthalpy.unit["J/kg"] == pytest.approx(
        expected["outlet_enthalpy"].unit["J/kg"], 
        abs=tolerance
    )

    check_dicts(plugin.outlet_mass_fraction, case["expected"]["outlet_mass_fraction"])

    np.testing.assert_allclose(plugin.yearly_mass_flow.unit["kg"],case["expected"]["yearly_mass_flow"].unit["kg"],rtol=tolerance,atol=tolerance,)        

    assert plugin.peak_mass_flowrate.unit["kg/day"] == pytest.approx(
        expected["peak_mass_flowrate"].unit["kg/day"], 
        abs=tolerance
    )        

    check_dicts(plugin.hourly_mass_flow, case["expected"]["hourly_mass_flow"])    