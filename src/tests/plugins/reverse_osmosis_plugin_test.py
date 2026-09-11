import pytest
import numpy as np
from pyH2A.Plugins.Reverse_Osmosis_Plugin import Reverse_Osmosis_Plugin
from pyH2A.Utilities.Unit_Handler.quantity import Quantity
from pyH2A.Utilities.functional_unit import resolve_functional_unit


class DummyDCF:
    """DCF object for Reverse_Osmosis_Plugin with configurable inputs."""

    def __init__(
        self, 
        design_output_by_year, 
        operating_capacity_factor,
        power_demand_kWh_per_m3, 
        operating_time_fraction, 
        recovery_rate,
        device_throughput=None,
    ):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            "Technical Operating Parameters and Specifications": {
                "Design output by year": {
                    "Value": design_output_by_year, 
                    "Unit": "kg",
                    "Processed": "Yes"
                }, 
                "Operating capacity factor": {
                    "Value": operating_capacity_factor, 
                    "Unit": "-",
                }                
            },
            "Reverse Osmosis": {
                "Power demand": {
                    "Value": power_demand_kWh_per_m3,
                    "Unit": "kWh / m3",
                },
                "Average operating time fraction": {
                    "Value": operating_time_fraction,
                    "Unit": "-"
                },
                "Recovery rate": {
                    "Value": recovery_rate,
                    "Unit": "-"
                },
            },
        }

        # "Device throughput" is an optional input, only added to dcf.inp when provided,
        # matching how a real input file would omit an unused optional row.
        if device_throughput is not None:
            self.inp["Reverse Osmosis"]["Device throughput"] = {
                "Value": device_throughput,
                "Unit": "m3/year",
            }

# case 1 is a realistic case for Reverse Osmosis Plugin, with no device throughput provided
# (so number of devices required is not calculated). However, the second case, which is defined 
# based on case 1, is tested except the device throughput is provided as an input, so number of
# devices required is calculated.
_CASE_1_INPUT = {
    "design_output_by_year": np.array([0.0, 2250.0, 2375.0]),
    "operating_capacity_factor": 0.8,
    "power_demand_kWh_per_m3": 10.0,
    "operating_time_fraction": 1.,
    "recovery_rate": 0.1,
    "device_throughput": None,
}

_CASE_1_EXPECTED = {
    "electricity_demand_kWh": Quantity(np.array([0.0,
                                                 1613.3471844103742,
                                                 1702.9775835442838]),
                                       "kWh"),
    "max_capacity_m3_per_hour": Quantity(0.019440383373793193, "m3/h"),
    "number_of_devices_required": None,
}


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": _CASE_1_INPUT,
            "expected": _CASE_1_EXPECTED,
        },
        {
            "input": {**_CASE_1_INPUT, "device_throughput": 100.0},
            "expected": {**_CASE_1_EXPECTED, "number_of_devices_required": Quantity(1.7029775835442837, "-")},
        },
    ],
    ids=[
        "Realistic case - Reverse Osmosis Plugin",
        "Realistic case - Reverse Osmosis Plugin with device throughput (device count calculated)",
    ]
)
def test_reverse_osmosis_plugin(case):
    """Test Reverse_Osmosis_Plugin using base inputs (direct names style), as well as
    number of devices required when device throughput is provided."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run plugin
    plugin = Reverse_Osmosis_Plugin(dcf, print_info=False)
    expected = case["expected"]

    # Tolerance (very small)
    tolerance = 1e-12

    np.testing.assert_allclose(
        plugin.electricity_demand_by_year.unit["J"],
        expected["electricity_demand_kWh"].unit["J"],
        rtol=tolerance,
        atol=tolerance
    )

    assert plugin.maximum_sea_water_processing_flowrate.unit["m3/s"] == pytest.approx(
        expected["max_capacity_m3_per_hour"].unit["m3/s"],
        abs=tolerance
    )

    if expected["number_of_devices_required"] is None:
        # No device throughput provided: number of devices required should not be calculated.
        assert not hasattr(plugin, "number_of_devices_required")
    else:
        assert plugin.number_of_devices_required.unit["-"] == pytest.approx(
            expected["number_of_devices_required"].unit["-"],
            abs=tolerance
        )


def test_reverse_osmosis_plugin_zero_device_throughput_raises():
    """Number of devices required calculation must raise when device throughput is zero,
    to avoid division by zero."""

    dcf = DummyDCF(
        design_output_by_year=np.array([0.0, 2250.0, 2375.0]),
        operating_capacity_factor=0.8,
        power_demand_kWh_per_m3=10.0,
        operating_time_fraction=1.,
        recovery_rate=0.1,
        device_throughput=0.0,
    )

    with pytest.raises(ValueError):
        Reverse_Osmosis_Plugin(dcf, print_info=False)

