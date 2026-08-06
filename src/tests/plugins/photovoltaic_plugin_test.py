import pytest
import numpy as np
from pyH2A.Plugins.Energy.Photovoltaic_Plugin import Photovoltaic_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit

class DummyDCF:
    """Minimal DCF object for Photovoltaic_Plugin testing with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        irradiation_hourly,
        nominal_power,
        power_loss_per_year,
        efficiency,
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
            "Irradiation Used": {
                "Data": {
                    "Value": irradiation_hourly.flatten(), 
                    "Unit": "kWh/m2",
                    "Processed": "Yes"
                }
            },
            "Photovoltaic": {
                "Nominal power": {
                    "Value": nominal_power,
                    "Unit": "kW"
                },
                "Power loss per year": {
                    "Value": power_loss_per_year,
                    "Unit": "-"
                },
                "Efficiency": {
                    "Value": efficiency,
                    "Unit": "-"
                },
            },
        }

@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {
                    # in the plugin logic, years are relative to startup year, not calendar year
                    'Operation years relative': np.arange(5, 7) 
                },                    
                "irradiation_hourly": np.array([
                    [
                        10.2, 5.2, 12.2, 0, 10.2, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                    ],
                    [
                        10.2, 5.2, 12.2, 0, 10.2, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                        10.2, 5.2, 12.2, 12.2, 0, 5.2, 12.2, 12.2,
                    ]
                ]),
                "nominal_power": 1000.0,
                "power_loss_per_year": 0.05,
                "efficiency": 0.2,
            },
            "expected": {
                "area": Quantity(5000.0, 'm2'),
                "energy_generation_yearly_data": {
                    5: Quantity(np.array([
                        7892.565562499997 , 4023.660875,  9440.1274375, 0.0,
                        7892.565562499997 , 4023.660875,  9440.1274375,  9440.1274375,
                        7892.565562499997 , 4023.660875,  9440.1274375,  9440.1274375,
                        0.0, 4023.660875,  9440.1274375,  9440.1274375,
                        7892.565562499997 , 4023.660875,  9440.1274375,  9440.1274375,
                        0.0, 4023.660875,  9440.1274375,  9440.1274375,
                        7892.565562499997 , 4023.660875,  9440.1274375, 0.0,
                        7892.565562499997 , 4023.660875,  9440.1274375,  9440.1274375,
                        7892.565562499997 , 4023.660875,  9440.1274375,  9440.1274375,
                        0.0, 4023.660875,  9440.1274375,  9440.1274375,
                        7892.565562499997 , 4023.660875,  9440.1274375,  9440.1274375,
                        0.0, 4023.660875,  9440.1274375,  9440.1274375
                    ]), 'kWh'),
                    6: Quantity(np.array([
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 0.0,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        0.0, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        0.0, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 0.0,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        0.0, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        7497.937284374998, 3822.4778312499993, 8968.121065624997, 8968.121065624997,
                        0.0, 3822.4778312499993, 8968.121065624997, 8968.121065624997
                    ]), 'kWh'),
                }, 
                "energy_generation_yearly_data_daily_energy": {
                    5: Quantity(np.array([159553.62931249992 , 159553.62931249992]), 'kWh'),
                    6: Quantity(np.array([151575.94784687494, 151575.94784687494]), 'kWh'),
                },
            },
        }
    ],
    ids=[
        "Realistic case - Photovoltaic plugin"
    ]
)
def test_photovoltaic_plugin(case):
    """Test Photovoltaic_Plugin using base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Photovoltaic_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.area.unit['m2'] == pytest.approx(
        expected["area"].unit['m2'], 
        abs=tolerance
    )

    for year in plugin.input_dict_resolved['Time']['Years']['Value']['Operation years relative'].unit['-']:
        np.testing.assert_allclose(
            plugin.electric_energy_generation_yearly_data[year].unit['J'],
            expected["energy_generation_yearly_data"][year].unit['J'],
            rtol=tolerance,
            atol=tolerance,
        )

        np.testing.assert_allclose(
            plugin.electric_energy_generation_yearly_data_daily_energy[year].unit["Wh"],
            expected["energy_generation_yearly_data_daily_energy"][year].unit["Wh"],
            rtol=tolerance,
            atol=tolerance,
        )
