import pytest
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Plugins.Electricity_Consumer_Plugin import Electricity_Consumer_Plugin
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Electricity_Consumer_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years,
        hourly_file,
        available_energy_hourly
    ):

        self.functional_unit = resolve_functional_unit('kWh')
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },            
            "Hourly Main Consumer Profile": {"File": {"Value": hourly_file}},
            "Power Generation": {
                "Available energy (hourly)": {"Value": available_energy_hourly, "Unit" : "kWh"},
            },           
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years": {'Operation years relative': np.arange(0, 2), 
                                    'Operation years ones': np.ones(2)},       
                "hourly_file": "pyH2A.Lookup_Tables.Hourly_Consumption~Constant_consumption_10MW.csv ",
                "available_energy_hourly": {0: 2*np.arange(0, 8760), 1:2*np.arange(0, 8760)},
            },
            "expected": {
                "first_6h_default_energy":Quantity(np.array([
                    1e4, 9998, 9996, 
                    9994, 9992, 9990
                    ]), 'kWh'),
                "last_6h_available_energy":Quantity(np.array([
                    7508, 7510, 7512, 
                    7514, 7516, 7518
                    ]), 'kWh'),
                "yearly_consumption": Quantity(np.array([87.6, 87.6]),
                                               "GWh"),
                "last_6h_default_energy":Quantity(np.zeros(6), 'kWh'),
                "first_6h_available_energy":Quantity(np.zeros(6), 'kWh'),                    
            },
        },
    ],
)
def test_electricity_consumer_plugin(case):
    """Test Electricity_Consumer_Plugin."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Electricity_Consumer_Plugin(dcf, print_info=False)
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.unsatisfied_demand[0].unit["J"][0:6] == pytest.approx(
        expected["first_6h_default_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.unsatisfied_demand[1].unit["J"][-6:] == pytest.approx(
        expected["last_6h_default_energy"].unit["J"],
        abs=tolerance
    )

    np.testing.assert_allclose(
        plugin.yearly_consumption.unit["kWh"],
        expected["yearly_consumption"].unit["kWh"],
        rtol=1e-12,
        atol=1e-12,
    )

    assert plugin.total_electric_energy_available_yearly_data[0].unit["J"][0:6] == pytest.approx(
        expected["first_6h_available_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.total_electric_energy_available_yearly_data[1].unit["J"][-6:] == pytest.approx(
        expected["last_6h_available_energy"].unit["J"],
        abs=tolerance
    )    

