from pyH2A.run_pyH2A import pyH2A

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