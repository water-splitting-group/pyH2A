from pyH2A.run_pyH2A import pyH2A

def test_pv_e_base():
	results = pyH2A('./tests/PV_E/Base/PV_E_Base.md', './tests/Results/PV_E/Base')
	expected_result = 3.581887505029294
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pv_e_new():
	results = pyH2A('./tests/PV_E/Base/PV_E_New.md', './tests/Results/PV_E/New', True)
	expected_result = 2.371129629524664
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pv_e_limit():
	results = pyH2A('./tests/PV_E/Limit/PV_E_Limit.md', '.tests/PV_E/Limit')
	expected_result = 1.4242951683758598
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pv_e_distance_time():
	results = pyH2A('./tests/PV_E/Historical_Data/PV_E_Distance_Time.md', './tests/PV_E/Historical_Data')
	expected_result = 185.13183678616176
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pec_base():
	results = pyH2A('./tests/PEC/Base/PEC_Base.md', './tests/PEC/Base')
	expected_result = 139.41887561917213
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pec_limit():
	results = pyH2A('./tests/PEC/Limit/PEC_Limit.md', './tests/PEC/Limit')
	expected_result = 1.4242951683758598
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_pec_limit_no_concentration():
	results = pyH2A('./tests/PEC/No_Conc/PEC_Limit_No_Concentration.md', './tests/PEC/No_Conc')
	expected_result = 15.826371459378658
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_photocatalytic_base():
	results = pyH2A('./tests/Photocatalytic/Base/Photocatalytic_Base.md', './tests/Photocatalytic/Base')
	expected_result = 185.44329282256822
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

def test_photocatalytic_limit():
	results = pyH2A('./tests/Photocatalytic/Limit/Photocatalytic_Limit.md', './tests/Photocatalytic/Limit')
	expected_result = 1.0546304750173923
	assert results.base_case.h2_cost == expected_result, f"Expected {expected_result} $/kg' but got {results.base_case.h2_cost} $/kg"

if __name__ == '__main__':
	test_pv_e_new()