import pytest
import numpy as np
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
                "Module Tilt (degrees)": {"Value": module_tilt},
                "Array Azimuth (degrees)": {"Value": array_azimuth},
                "Nominal Operating Temperature (Celsius)": {"Value": nominal_temp},
                "Mismatch Derating": {"Value": mismatch_derating},
                "Dirt Derating": {"Value": dirt_derating},
                "Temperature Coefficient (per Celsius)": {"Value": temp_coeff},
            },
        }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "hourly_file": "pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv",
                "module_tilt": 34.859,
                "array_azimuth": 180,
                "nominal_temp": 45,
                "mismatch_derating": 0.98,
                "dirt_derating": 0.98,
                "temp_coeff": -0.004,
            },
            "expected": {
                "latitude": 34.859,
                "longitude": -116.889,
                "mean_power_dat_kW": 6.801704863179404,
                "mean_power_kW": 5.499228123213646,
                "mean_power_sat_kW": 6.8301271595436885,
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

    assert np.sum(plugin.power_dat_kW) / 365.0 == pytest.approx(
        expected["mean_power_dat_kW"],
        abs=tolerance
    )
    assert np.sum(plugin.power_kW) / 365.0 == pytest.approx(
        expected["mean_power_kW"],
        abs=tolerance    
    )
    assert np.sum(plugin.power_sat_kW) / 365.0 == pytest.approx(
        expected["mean_power_sat_kW"],
        abs=tolerance
    )
    assert location["Latitude (decimal degrees)"] == expected["latitude"]
    assert location["Longitude (decimal degrees)"] == expected["longitude"]
