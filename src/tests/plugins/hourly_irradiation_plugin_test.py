import pytest
import numpy as np
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Plugins.Hourly_Irradiation_Plugin import (
    Hourly_Irradiation_Plugin,
    import_hourly_data,
)


class DummyDCF:
    """DCF object for Hourly_Irradiation_Plugin with configurable inputs."""

    def __init__(
        self,
        hourly_file,
        module_tilt,
        array_azimuth,
        nominal_temp,
        mismatch_derating,
        dirt_derating,
        temp_coeff,
    ):
        self.inp = {
            "Hourly Irradiation": {"File": {"Value": hourly_file}},
            "Irradiance Area Parameters": {
                "Module tilt": {"Value": module_tilt, "Unit":"deg"}, # we can actually comment-out this line, it's just the latitude, which is the default
                "Array azimuth": {"Value": array_azimuth, "Unit":"deg"},
                "Nominal operating temperature": {"Value": nominal_temp, "Unit":"degC"},
                "Mismatch derating": {"Value": mismatch_derating, "Unit":"-"},
                "Dirt derating": {"Value": dirt_derating, "Unit":"-"},
                "Temperature coefficient": {"Value": temp_coeff, "Unit":"-/delta_degC"},
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "hourly_file": "pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv",
                "module_tilt": 34.859,
                "array_azimuth": 180.,
                "nominal_temp": 45.,
                "mismatch_derating": 0.98,
                "dirt_derating": 0.98,
                "temp_coeff": -0.004,
            },
            "expected": {
                "latitude": Quantity(34.859,"deg"),
                "longitude": Quantity(-116.889,"deg"),
                "mean_power_dat": Quantity(6.801704863179404,"kWh_per_day/m2"), 
                "mean_power": Quantity(5.499228123213646,"kWh_per_day/m2"),
                "mean_power_sat": Quantity(6.8301271595436885,"kWh_per_day/m2"),
            },
        },
    ],
)
def test_hourly_irradiation_plugin(case):
    """Test Hourly_Irradiation_Plugin using PV_E base inputs (direct names style)."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Hourly_Irradiation_Plugin(dcf, print_info=False)
    data, location = import_hourly_data(case["input"]["hourly_file"])
    expected = case["expected"]
    
    # Tolerance (very small)
    tolerance = 1e-12

    assert plugin.yearly_averaged_power_dat.unit["W/m2"] == pytest.approx(
        expected["mean_power_dat"].unit["W/m2"],
        abs=tolerance
    )
    assert plugin.yearly_averaged_power.unit["W/m2"] == pytest.approx(
        expected["mean_power"].unit["W/m2"],
        abs=tolerance    
    )
    assert plugin.yearly_averaged_power_sat.unit["W/m2"] == pytest.approx(
        expected["mean_power_sat"].unit["W/m2"],
        abs=tolerance
    )
    assert location["Latitude (decimal degrees)"] == expected["latitude"].unit['deg']
    assert location["Longitude (decimal degrees)"] == expected["longitude"].unit['deg']
