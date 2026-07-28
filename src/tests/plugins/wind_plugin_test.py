import pytest
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Plugins.Wind_Plugin import (
    Wind_Plugin,
    import_hourly_data,
)


class DummyDCF:
    """DCF object for Hourly_Irradiation_Plugin with configurable inputs."""

    def __init__(
        self,
        operation_years_relative,
        hourly_file,
        available_energy_hourly,
        installed_wind_capacity,
        power_per_wind_turbine,
        power_loss_per_year
    ):
        self.inp = {
            "Time": {
                "Years": {
                    "Value": operation_years_relative,
                    "Unit": "-",   
                    "Processed": "Yes",                    
                },
            },            
            "Meteorological Data": {"File": {"Value": hourly_file}},
            "Power Generation": {
                "Available energy (hourly)": {"Value": available_energy_hourly, "Unit" : "kWh"},
            },
            "Wind Turbine": {
                "Installed wind capacity": {"Value": installed_wind_capacity, "Unit" : "MW"},
                "Power per wind turbine": {"Value": power_per_wind_turbine, "Unit" : "MW"},
                "Power loss per year": {"Value": power_loss_per_year, "Unit" : "-"},
            },            
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "operation_years_relative": {'Operation years relative': np.arange(0, 2)},       
                "hourly_file": "pyH2A.Lookup_Tables.Hourly_Meteorological_Data~Jena.615_2005_2023.csv",
                "available_energy_hourly": {0: np.arange(0, 8760), 1:np.arange(0, 8760)},
                "installed_wind_capacity": 20.,
                "power_per_wind_turbine": 4.,
                "power_loss_per_year": 0.01,
            },
            "expected": {
                "number_turbines": Quantity(5,"-"),
                "last_half_day_available_energy":Quantity(np.array([
                        31492800000.0,  31496400000, 31500000000,  31503600000, 
                        31507200000,  31510800000,31514400000, 31518000000, 
                        31521600000, 31525200000, 31528800000, 31532400000
                    ]), 'J'),
                "first_day_wind_energy":Quantity(np.array([
                        0, 0, 0, 0, 
                        0, 0, 0, 0, 
                        0, 0, 0, 0, 
                        0, 0, 0, 0, 
                        3006888977.5945992 ,  3422031955.855719,  3906197542.9547396, 5915441564.042187, 
                        6972642911.208555, 8566416338.770905,  10790912763.99429, 11276236627.601461,                         
                    ]), 'J'),
            },
        },
    ],
)
def test_wind_plugin(case):
    """Test Wind_Plugin."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Wind_Plugin(dcf, print_info=False)
   # data = import_hourly_data(case["input"]["hourly_file"])
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.number_turbines.unit["-"] == pytest.approx(
        expected["number_turbines"].unit["-"],
        abs=tolerance
    )

    assert plugin.total_electric_energy_generation_yearly_data[1].unit["J"][-12:] == pytest.approx(
        expected["last_half_day_available_energy"].unit["J"],
        abs=tolerance
    )

    assert plugin.wind_electric_energy_generation_yearly_data[1].unit["J"][0:24] == pytest.approx(
        expected["first_day_wind_energy"].unit["J"],
        abs=tolerance
    )    
