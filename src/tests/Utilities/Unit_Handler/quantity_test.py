import pytest
import numpy as np

from pyH2A.Utilities.Unit_Handler.quantity import parse_composite_unit, parse_reference, UnitDictionary, Quantity

def test_parse_composite_unit_simple():
    multiplier, base, dim = parse_composite_unit("kWh")
    assert multiplier == 3.6e6
    assert base == "J"
    assert dim == "energy"

def test_parse_composite_unit_complex():
    multiplier, base, dim = parse_composite_unit("kWh / m2 / day")
    # kWh (3.6e6) / m2 (1.0) / day (86400.0) -> 3.6e6 / 86400 = 41.666...
    assert pytest.approx(multiplier, 1e-4) == 3.6e6 / 86400.0
    assert base == "J / m2 / s"
    assert dim == "energy / area / time"

def test_parse_composite_unit_parentheses():
    multiplier, base, dim = parse_composite_unit("( kWh * m ) / m2")
    assert multiplier == 3.6e6
    assert base == "( J * m ) / m2"
    assert dim == "( energy * length ) / area"

def test_parse_composite_unit_leading_number():
    multiplier, base, dim = parse_composite_unit("1 / day")
    assert multiplier == 1.0 / 86400.0
    assert base == "1 / s"
    assert dim == "1 / time"

def test_parse_composite_unit_unknown_unit():
    with pytest.raises(ValueError, match="Unknown unit encountered"):
        parse_composite_unit("unknown_fake_unit / m2")

def test_quantity_init_absolute_temperature_k():
    q = Quantity(300, "K")
    assert q.is_absolute_temp is True
    assert q.base_value == 300
    assert q.base_unit == "K"
    assert q.dimension == "absolute_temperature"
    assert q.unit["K"] == 300
    assert q.unit["degC"] == pytest.approx(26.85)

def test_quantity_init_absolute_temperature_degc():
    q = Quantity(25, "degC")
    assert q.is_absolute_temp is True
    assert q.base_value == pytest.approx(298.15)
    assert q.base_unit == "K"
    assert q.dimension == "absolute_temperature"
    assert q.unit["K"] == pytest.approx(298.15)
    assert q.unit["degC"] == 25

def test_unit_dictionary_absolute_temperature_invalid():
    q = Quantity(25, "degC")
    with pytest.raises(KeyError, match="Unsupported absolute temperature unit"):
        _ = q.unit["F"]

def test_quantity_init_standard():
    q = Quantity(2, "kWh")
    assert q.is_absolute_temp is False
    assert q.base_value == 7.2e6  # 2 * 3.6e6
    assert q.dimension == "energy"
    assert q.base_unit == "J"
    # test standard cache access
    assert q.unit["kWh"] == 2
    assert q.unit["J"] == 7.2e6

def test_unit_dictionary_lazy_evaluation():
    q = Quantity(1, "m")
    # Requesting cm conversions triggers lazy eval
    assert q.unit["cm"] == 100.0
    # Next time it shouldn't trigger, proving it stored it
    assert "cm" in q.unit

def test_unit_dictionary_dimension_mismatch():
    q = Quantity(10, "kg")
    with pytest.raises(ValueError, match="Dimension mismatch"):
        _ = q.unit["J"]  # kg to J is invalid

def test_unit_dictionary_dimension_mismatch_composite():
    q = Quantity(10, "kWh / m2")
    with pytest.raises(ValueError, match="Dimension mismatch"):
        _ = q.unit["kWh / m3"]

def test_quantity_with_numpy_array():
    arr = np.array([1.0, 2.0, 3.0])
    q = Quantity(arr, "km")
    
    assert np.array_equal(q.base_value, np.array([1000.0, 2000.0, 3000.0]))
    assert np.array_equal(q.unit["m"], np.array([1000.0, 2000.0, 3000.0]))
    assert np.array_equal(q.unit["cm"], np.array([100000.0, 200000.0, 300000.0]))

def test_quantity_repr():
    q = Quantity(5, "kWh")
    expected_repr = "Quantity(18000000.0, 'J')"
    assert repr(q) == expected_repr

def test_dimensionless_quantity():
    q = Quantity(0.5, "-")
    assert q.dimension == "dimensionless"
    assert q.unit["-"] == 0.5
    assert q.unit["ppm"] == 500000.0

def test_parse_reference_with_bracket():
    result = parse_reference('kg[H2]')
    assert result == ('kg', {'kg': 'H2'})

def test_parse_reference_without_bracket():
    result = parse_reference('kg')
    assert result == ('kg', {})

def test_parse_reference_empty_bracket():
    result = parse_reference('kg[]')
    assert result == ('kg', {})

def test_quantity_with_reference():
    q = Quantity(10, 'kg[H2]')
    assert q.reference == {'kg': 'H2'}
    assert q.unit['g'] == 10000.0
    assert q.dimension == 'mass'

def test_quantity_repr_with_reference():
    q = Quantity(5, 'kg[H2]')
    assert '[H2]' in repr(q)

def test_quantity_reference_dimension_mismatch_still_raises():
    q = Quantity(10, 'kg[H2]')
    with pytest.raises(ValueError, match="Dimension mismatch"):
        _ = q.unit['J']

def test_parse_reference_multiple_brackets():
    result = parse_reference('kg[H2]/J[electricity]')
    assert result == ('kg/J', {'kg': 'H2', 'J': 'electricity'})

def test_parse_reference_multiple_brackets_spaced():
    result = parse_reference('J[energy] / kg[H2]')
    assert result == ('J / kg', {'J': 'energy', 'kg': 'H2'})

def test_parse_reference_malformed_bracket_order():
    result = parse_reference('[kg]H2')
    assert result == ('[kg]H2', {})

def test_quantity_composite_reference():
    q = Quantity(10, 'kg[H2]/J[electricity]')
    assert q.reference == {'kg': 'H2', 'J': 'electricity'}
    assert q.dimension == 'mass / energy'

def test_quantity_composite_reference_repr():
    q = Quantity(5, 'J[energy] / kg[H2]')
    assert '[energy]' in repr(q)
    assert '[H2]' in repr(q)

def test_quantity_composite_reference_real_pattern():
    q = Quantity(10, 'kWh[solar]/m2[area]')
    assert q.reference == {'kWh': 'solar', 'm2': 'area'}
    assert q.unit['J / m2'] == pytest.approx(3.6e7)

def test_quantity_lca_unit_with_reference():
    q = Quantity(1, 'MJ[impact category]')
    assert q.reference == {'MJ': 'impact category'}
    assert q.unit['J'] == 1000000.0

def test_quantity_absolute_temperature_with_reference():
    q = Quantity(25, 'degC[reactor]')
    assert q.reference == {'degC': 'reactor'}
    assert q.unit['K'] == pytest.approx(298.15)

def test_quantity_unregistered_lca_unit_with_reference_fails_cleanly():
    # CTUe is not registered in FLAT_MULTIPLIERS today (separate, pre-existing
    # gap, unrelated to #95). Confirms the bracket feature doesn't mask that
    # gap — it still fails with a clear "unknown unit" error.
    with pytest.raises(ValueError, match="Unknown unit"):
        Quantity(1, 'CTUe[toxicity]')

def test_quantity_lca_unit_ton_with_reference():
    q = Quantity(2, 'ton[steel]')
    assert q.reference == {'ton': 'steel'}
    assert q.unit['kg'] == 2000.0

def test_quantity_lca_composite_conversion_with_reference():
    q = Quantity(1, 'kWh[grid electricity]')
    assert q.reference == {'kWh': 'grid electricity'}
    assert q.unit['MJ'] == pytest.approx(3.6)

def test_quantity_leading_numeric_reference():
    q = Quantity(1, '1/day[TOF]')
    assert q.reference == {'day': 'TOF'}
    assert q.unit['1 / s'] == pytest.approx(1/86400)
