import pytest
import numpy as np
from pyH2A.Plugins.Electrolyzer_Plugin import Electrolyzer_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

class DummyDCF:
    """Minimal DCF object for Electrolyzer_Plugin with configurable inputs."""

    def __init__(
        self,
        construction_time,
        capex_multiplier,
        nominal_power,
        capex_reference_power,
        power_increase,
        min_capacity,
        efficiency,
        replacement_time,
        available_power_hourly,
    ):

        self.inp = {
            "Financial Input Values": {
                "Construction time": {"Value": construction_time, "Unit":"year"}
            },
            "CAPEX Multiplier": {"Multiplier": {"Value": capex_multiplier, "Unit":"-"}},
            "Electrolyzer": {
                "Nominal power": {"Value": nominal_power, "Unit":"kW"},
                "CAPEX reference power": {"Value": capex_reference_power, "Unit":"kW"},
                "Power requirement increase per year": {"Value": power_increase, "Unit":"-"},
                "Minimum capacity": {"Value": min_capacity, "Unit":"-"},
                "Hydrogen yield per unit energy": {"Value": efficiency, "Unit":"kg/kWh"},
                "Replacement time": {"Value": replacement_time, "Unit":"h"},
            },
            "Power Generation": {
                "Available energy (hourly)": {
                    "Value": available_power_hourly,
                    "Unit":"kWh",
                    "Processed": "Yes",
                }
            },
        }
        
        self.operation_years = list(available_power_hourly.keys())



@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "construction_time": 2,
                "capex_multiplier": 0.9,
                "nominal_power": 5500.0,
                "capex_reference_power": 1000.0,
                "power_increase": 0.003,
                "min_capacity": 0.10,
                "efficiency": 0.0185,
                "replacement_time": 80000.0,
                "available_power_hourly": {
                    2026: np.array(
                        [
                            200000000.2,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            0.0,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                        ]
                    ),
                    2027: np.array(
                        [
                            0.0,
                            200500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            0.0,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            200500000.2,
                            201200000.2,
                            0.0,
                            201000000.2,
                            206500000.2,
                            201200000.2,
                            201200000.2,
                            201000000.2,
                            207500000.2,
                            201200000.2,
                            0.0,
                            201000000.2,
                            208500000.2,
                            201200000.2,
                            201200000.2,
                        ]
                    ),
                },
            },
            "expected": {
                "h2_production": Quantity(np.array([0.0, 0.0, 2035.0, 2035.0]), 'kg'),
                "scaling_factor": Quantity(0.9249598065992481, '-'),
                "stack_lifetime": Quantity(2.0, 'year'),
                "yearly_data_year": Quantity(np.array([2026.0, 2027.0]),'-'),
                "yearly_data_production": Quantity(np.array([2035.0, 2035.0]),'kg'),
                "yearly_data_duration": Quantity(np.array([20.0, 20.0]),'h'),                                
                "yearly_data_unused_energy": {
                    2026: Quantity(
                            np.array(
                                [
                                197622869.89416197,
                                198122869.89416197,
                                198822869.89416197,
                                198822869.89416197,
                                0.0,
                                198122869.89416197,
                                198822869.89416197,
                                198822869.89416197,
                                198622869.89416197,
                                198122869.89416197,
                                198822869.89416197,
                                198822869.89416197,
                                198622869.89416197,
                                0.0,
                                198822869.89416197,
                                198822869.89416197,
                                198622869.89416197,
                                0.0,
                                198822869.89416197,
                                198822869.89416197,
                                198622869.89416197,
                                0.0,
                                198822869.89416197,
                                198822869.89416197,
                                ]
                            ),
                            "kWh"
                    ),
                    2027: Quantity(
                            np.array(
                                [
                                    0.0,
                                    198115738.50324446,
                                    198815738.50324446,
                                    198815738.50324446,
                                    198615738.50324446,
                                    0.0,
                                    198815738.50324446,
                                    198815738.50324446,
                                    198615738.50324446,
                                    198115738.50324446,
                                    198815738.50324446,
                                    0.0,
                                    198615738.50324446,
                                    204115738.50324446,
                                    198815738.50324446,
                                    198815738.50324446,
                                    198615738.50324446,
                                    205115738.50324446,
                                    198815738.50324446,
                                    0.0,
                                    198615738.50324446,
                                    206115738.50324446,
                                    198815738.50324446,
                                    198815738.50324446,
                                ]
                        ),
                        'kWh'
                    ),    
                },
                "yearly_data_unused_energy_daily": {
                    2026: Quantity(np.array([3972357397.8832397]), 'kWh'),
                    2027: Quantity(np.array([3992814770.0648894]), 'kWh'),
                },
            },
        },
    ],
)
def test_electrolyzer_plugin(case):
    """Check plugin handles edge and real cases without errors and returns correct annualized costs."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Electrolyzer_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.h2_production.unit['kg'],
        expected["h2_production"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )

    assert plugin.electrolyzer_scaling_factor.unit['-'] == pytest.approx(
        expected["scaling_factor"].unit['-'],
        abs=tolerance
    )
    
    assert plugin.stack_lifetime.unit['year'] == pytest.approx(
        expected["stack_lifetime"].unit['year'],
        abs=tolerance
    )

    np.testing.assert_allclose(
        plugin.yearly_data_year.unit['-'],
        expected["yearly_data_year"].unit['-'],
        rtol=tolerance,
        atol=tolerance,
    )
    np.testing.assert_allclose(
        plugin.yearly_data_production.unit['kg'],
        expected["yearly_data_production"].unit['kg'],
        rtol=tolerance,
        atol=tolerance,
    )
    np.testing.assert_allclose(
        plugin.yearly_data_duration.unit['s'],
        expected["yearly_data_duration"].unit['s'],
        rtol=tolerance,
        atol=tolerance,
    )

    for year in dcf.operation_years:
        np.testing.assert_allclose(
            plugin.yearly_data_unused_energy[year].unit['J'],
            expected["yearly_data_unused_energy"][year].unit['J'],
            rtol=tolerance,
            atol=tolerance,
        )

        np.testing.assert_allclose(
            plugin.yearly_data_unused_energy_daily[year].unit['J'],
            expected["yearly_data_unused_energy_daily"][year].unit['J'],
            rtol=tolerance,
            atol=tolerance,
        )