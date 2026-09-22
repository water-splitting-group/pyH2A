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
        self.functional_unit = resolve_functional_unit('kg[H2]')
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

        # "Device throughput" is optional, so it is only added when provided,
        # in the same way as an input file would omit it.
        if device_throughput is not None:
            self.inp["Reverse Osmosis"]["Device throughput"] = {
                "Value": device_throughput,
                "Unit": "m3/h",
            }


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "design_output_by_year": np.array([2250.0, 2375.0]),
                "operating_capacity_factor": 0.8,
                "power_demand_kWh_per_m3": 10.0,          
                "operating_time_fraction": 1.,                  
                "recovery_rate": 0.1,                    
            },
            "expected": {
                "electricity_demand_kWh": Quantity(np.array([1613.3471844103742, 
                                                             1702.977583544284]), 
                                                   "kWh"),
                "max_capacity_m3_per_hour": Quantity(0.019440383373793193, "m3/h"),
                # Design output * capacity factor * 18.01528 / 2.016 kg of water per kg of H2
                "purified_water_kg": Quantity(np.array([16085.07142857143, 
                                                        16978.68650793651]), 
                                              "kg"),
            },
        }
    ]
)
def test_reverse_osmosis_plugin(case):
    """Test Reverse_Osmosis_Plugin using base inputs (direct names style)."""
    
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

    np.testing.assert_allclose(
        plugin.fresh_water_production_by_year.unit["kg"],
        expected["purified_water_kg"].unit["kg"],
        rtol=tolerance,
    )

    # Without device throughput, the number of devices is not calculated (or inserted).
    assert not hasattr(plugin, "number_of_devices_required")
    assert "Number of devices required" not in dcf.inp["Reverse Osmosis"]


def test_reverse_osmosis_plugin_number_of_devices():
    """Check purified water production and number of devices, using inputs different
    from the base case and values derived by hand.

    - purified water: design output * 18.01528 / 2.016 kg of water per kg of H2, which
      is exactly 18015.28 kg for 2016 kg of H2,
    - sea water: 18015.28 kg / (997 kg/m3) / 0.5 recovery rate = 36.13897693079238 m3 in
      the year of maximum demand,
    - capacity: 36.13897693079238 m3 / 0.25 operating time fraction = 144.55590772316953 m3/year,
    - devices: 144.55590772316953 m3/year / (0.005 m3/h * 8760 h/year) = 3.300363190026701.
    """

    dcf = DummyDCF(
        design_output_by_year=np.array([1000.0, 2016.0]),
        operating_capacity_factor=1.0,
        power_demand_kWh_per_m3=3.0,
        operating_time_fraction=0.25,
        recovery_rate=0.5,
        device_throughput=0.005,
    )

    plugin = Reverse_Osmosis_Plugin(dcf, print_info=False)

    tolerance = 1e-12

    np.testing.assert_allclose(plugin.fresh_water_production_by_year.unit["kg"],
                               [8936.150793650795, 18015.28],
                               rtol=tolerance)
    np.testing.assert_allclose(plugin.electricity_demand_by_year.unit["kWh"],
                               [53.77823948034581, 108.41693079237714],
                               rtol=tolerance)
    assert plugin.maximum_sea_water_processing_flowrate.unit["m3/year"] == pytest.approx(
        144.55590772316953, rel=tolerance)
    assert plugin.number_of_devices_required.unit["-"] == pytest.approx(3.300363190026701, rel=tolerance)

    # Both outputs are inserted into the Reverse Osmosis table for use by other plugins (e.g. LCA).
    assert dcf.inp["Reverse Osmosis"]["Number of devices required"]["Value"].unit["-"] == pytest.approx(
        3.300363190026701, rel=tolerance)
    np.testing.assert_allclose(dcf.inp["Reverse Osmosis"]["Purified water production (yearly)"]["Value"].unit["kg"],
                               [8936.150793650795, 18015.28],
                               rtol=tolerance)


def test_reverse_osmosis_plugin_zero_device_throughput_raises():
    """A device throughput of zero would divide by zero, so it is rejected."""

    dcf = DummyDCF(
        design_output_by_year=np.array([1000.0, 2016.0]),
        operating_capacity_factor=1.0,
        power_demand_kWh_per_m3=3.0,
        operating_time_fraction=0.25,
        recovery_rate=0.5,
        device_throughput=0.0,
    )

    with pytest.raises(ValueError, match="device throughput must be greater than zero"):
        Reverse_Osmosis_Plugin(dcf, print_info=False)

