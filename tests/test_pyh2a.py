from pyH2A.Plugins.Hydrogen import ElectrolyzerPlugin
from pyH2A.run_pyH2A import pyH2A
from pyH2A.DiscountedCashFlow import DiscountedCashFlow
from pyH2A.Plugins import *
import numpy as np
import csv
import pickle
from pyH2A.DiscountedCashFlow import DiscountedCashFlow

def compare_values(val1, val2):
    """Recursively compare two values, handling numpy arrays, dicts, and lists."""
    # Compare types first
    if type(val1) != type(val2):
        return False

    # For numpy arrays
    if isinstance(val1, np.ndarray):
        return np.array_equal(val1, val2)
    
    # For dictionaries, compare keys and then recursively compare each value
    if isinstance(val1, dict):
        if val1.keys() != val2.keys():
            return False
        for key in val1:
            if not compare_values(val1[key], val2[key]):
                return False
        return True

    # For lists, compare each element
    if isinstance(val1, list):
        if len(val1) != len(val2):
            return False
        for item1, item2 in zip(val1, val2):
            if not compare_values(item1, item2):
                return False
        return True

    return val1 == val2

def validate_dcf_insertions(
    plugin_class: type, 
    snapshot_name: str
) -> None:
    """Reusable function to test plugin insertions into DCF."""
    with open(f"tests/snapshots/{snapshot_name}-snapshot_before.pkl", "rb") as f:
        dcf_before: DiscountedCashFlow = pickle.load(f)
    with open(f"tests/snapshots/{snapshot_name}-snapshot_after.pkl", "rb") as f:
        dcf_after: DiscountedCashFlow = pickle.load(f)
    
    # Read CSV file using the csv module
    with open(f"tests/snapshots/{snapshot_name}-dict_entries.csv", "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row if present
        dict_entries: list[tuple[str, str, str]] = [tuple(row) for row in reader]

    # Run the plugin on the before snapshot
    plugin_class(dcf_before)

    # Validate each entry
    for key, subkey, field in dict_entries:
        value_before = dcf_before.inp[key].get(subkey, {}).get(field, None)
        value_after = dcf_after.inp[key].get(subkey, {}).get(field, None)
        
        if not compare_values(value_before, value_after):
            raise AssertionError(
                f"expected {value_after} but got {value_before} for "
                f"{key} -> {subkey} -> {field}"
            )

def test_pv_e():
	results = pyH2A('./tests/PV_E.md', './tests/Results/PV_E/')
	expected_result = 4.194302976489678
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pec():
	results = pyH2A('./tests/PEC.md', './tests/PEC/Base')
	expected_result = 139.41887561917213
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_photocatalytic_base():
	results = pyH2A('./tests/Photocatalytic.md', './tests/Photocatalytic/Base')
	expected_result = 185.44329282256822
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"
     
def test_hourly_irradiation_plugin():
	"""Test the HourlyIrradiationPlugin with a sample DCF."""
	validate_dcf_insertions(HourlyIrradiationPlugin, 'HourlyIrradiationPlugin')

def test_photovoltaic_plugin():
	"""Test the PhotovoltaicPlugin with a sample DCF."""
	validate_dcf_insertions(PhotovoltaicPlugin, 'PhotovoltaicPlugin')

def test_electrolyzer_plugin():
	"""Test the ElectrolyzerPlugin with a sample DCF."""
	validate_dcf_insertions(ElectrolyzerPlugin, 'ElectrolyzerPlugin')
    
def test_battery_plugin():
	"""Test the BatteryPlugin with a sample DCF."""
	validate_dcf_insertions(BatteryPlugin, 'BatteryPlugin')

def test_stored_power_electrolysis_plugin():
	"""Test the StoredPowerElectrolysisPlugin with a sample DCF."""
	validate_dcf_insertions(StoredPowerElectrolysisPlugin, 'StoredPowerElectrolysisPlugin')

def rest_reverse_osmosis_plugin():
	"""Test the ReverseOsmosisPlugin with a sample DCF."""
	validate_dcf_insertions(ReverseOsmosisPlugin, 'ReverseOsmosisPlugin')

def test_power_management_plugin():
	"""Test the PowerManagementPlugin with a sample DCF."""
	validate_dcf_insertions(PowerManagementPlugin, 'PowerManagementPlugin')

def test_multiple_modules_plugin():
	"""Test the MultipleModulesPlugin with a sample DCF."""
	validate_dcf_insertions(MultipleModulesPlugin, 'MultipleModulesPlugin')

def test_solar_concentrator_plugin():
	"""Test the SolarConcentratorPlugin with a sample DCF."""
	validate_dcf_insertions(SolarConcentratorPlugin, 'SolarConcentratorPlugin')

def test_capital_cost_plugin():
	"""Test the CapitalCostPlugin with a sample DCF."""
	validate_dcf_insertions(CapitalCostPlugin, 'CapitalCostPlugin')
     
def test_fixed_operating_cost_plugin():
	"""Test the FixedOperatingCostPlugin with a sample DCF."""
	validate_dcf_insertions(FixedOperatingCostPlugin, 'FixedOperatingCostPlugin')
    
def test_catalyst_separation_plugin():
	"""Test the CatalystSeparationPlugin with a sample DCF."""
	validate_dcf_insertions(CatalystSeparationPlugin, 'CatalystSeparationPlugin')