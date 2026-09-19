import pytest
from pyH2A.Utilities.functional_unit import resolve_functional_unit, FunctionalUnit

TEST_CASES = [
    {
        "input": {
            "Unit": "kg[H2]",
        },
        "expected": {
            "functional_dimension_per_time": "mass/time",
            "functional_unit_SI_per_s": "kg[H2]/s",
            "functional_unit_per_year": "kg[H2]/year",
        },
    },
    {
        "input": {
            "Unit": "kWh[electricity]",
        },
        "expected": {
            "functional_dimension_per_time": "power",
            "functional_unit_SI_per_s": "W",
            "functional_unit_per_year": "kWh[electricity]_per_year",
        },
    },
]

UNITS_WITHOUT_REFERENCE = ["kg", "kWh"]

@pytest.mark.parametrize("case", TEST_CASES)
def test_set_functional_unit(case):
    functional_unit = resolve_functional_unit(case["input"]["Unit"])

    expected = case["expected"]

    assert functional_unit.dimension_per_time == expected["functional_dimension_per_time"]
    assert functional_unit.unit_SI_per_s == expected["functional_unit_SI_per_s"]
    assert functional_unit.unit_per_year == expected["functional_unit_per_year"]

@pytest.mark.parametrize("unit", UNITS_WITHOUT_REFERENCE)
def test_functional_unit_without_reference_is_rejected(unit):
    with pytest.raises(ValueError, match="carries no reference"):
        resolve_functional_unit(unit)
