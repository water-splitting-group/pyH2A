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
    assert result == ('kg', ['H2'])

def test_parse_reference_without_bracket():
    result = parse_reference('kg')
    assert result == ('kg', [])

def test_parse_reference_empty_bracket():
    result = parse_reference('kg[]')
    assert result == ('kg', [None])

def test_quantity_with_reference():
    q = Quantity(10, 'kg[H2]')
    assert q.reference == ['H2']
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
    assert result == ('kg/J', ['H2', 'electricity'])

def test_parse_reference_multiple_brackets_spaced():
    result = parse_reference('J[energy] / kg[H2]')
    assert result == ('J / kg', ['energy', 'H2'])

def test_parse_reference_malformed_bracket_order():
    result = parse_reference('[kg]H2')
    assert result == ('[kg]H2', [])

def test_quantity_composite_reference():
    q = Quantity(10, 'kg[H2]/J[electricity]')
    assert q.reference == ['H2', 'electricity']
    assert q.dimension == 'mass / energy'

def test_quantity_composite_reference_repr():
    q = Quantity(5, 'J[energy] / kg[H2]')
    assert '[energy]' in repr(q)
    assert '[H2]' in repr(q)

def test_quantity_composite_reference_real_pattern():
    q = Quantity(10, 'kWh[solar]/m2[area]')
    assert q.reference == ['solar', 'area']
    assert q.unit['J / m2'] == pytest.approx(3.6e7)

def test_quantity_lca_unit_with_reference():
    q = Quantity(1, 'MJ[impact category]')
    assert q.reference == ['impact category']
    assert q.unit['J'] == 1000000.0

def test_quantity_absolute_temperature_with_reference():
    q = Quantity(25, 'degC[reactor]')
    assert q.reference == ['reactor']
    assert q.unit['K'] == pytest.approx(298.15)

def test_quantity_unregistered_lca_unit_with_reference_fails_cleanly():
    # CTUe is not registered in FLAT_MULTIPLIERS today (separate, pre-existing
    # gap, unrelated to #95). Confirms the bracket feature doesn't mask that
    # gap — it still fails with a clear "unknown unit" error.
    with pytest.raises(ValueError, match="Unknown unit"):
        Quantity(1, 'CTUe[toxicity]')

def test_quantity_lca_unit_ton_with_reference():
    q = Quantity(2, 'ton[steel]')
    assert q.reference == ['steel']
    assert q.unit['kg'] == 2000.0

def test_quantity_lca_composite_conversion_with_reference():
    q = Quantity(1, 'kWh[grid electricity]')
    assert q.reference == ['grid electricity']
    assert q.unit['MJ'] == pytest.approx(3.6)

def test_quantity_leading_numeric_reference():
    q = Quantity(1, '1/day[TOF]')
    assert q.reference == [None, 'TOF']
    assert q.unit['1 / s'] == pytest.approx(1/86400)

def test_quantity_duplicate_unit_different_labels():
    q = Quantity(1, 'kg[H2] / kg[H2O]')
    assert q.reference == ['H2', 'H2O']

def test_quantity_three_token_duplicate_unit():
    q = Quantity(1, 'kg[H2] / m2 / kg[H2O]')
    assert q.reference == ['H2', None, 'H2O']

def test_quantity_multiword_label():
    q = Quantity(1, 'MJ[impact category]')
    assert q.reference == ['impact category']
    assert repr(q) == "Quantity(1000000.0, 'J[impact category]')"

def test_quantity_multiword_label_composite():
    q = Quantity(1, 'kg[sea water] / m3[fresh water]')
    assert q.reference == ['sea water', 'fresh water']
    assert repr(q) == "Quantity(1.0, 'kg[sea water] / m3[fresh water]')"

def test_unit_lookup_reference_match():
    q = Quantity(1, 'kg[H2]')
    assert q.unit['g[H2]'] == 1000.0

def test_unit_lookup_reference_mismatch_raises():
    q = Quantity(1, 'kg[H2]')
    with pytest.raises(ValueError, match="Reference mismatch") as exc_info:
        _ = q.unit['g[H2O]']
    assert 'H2' in str(exc_info.value)
    assert 'H2O' in str(exc_info.value)

def test_unit_lookup_reference_requested_but_none_stored_raises():
    q = Quantity(1, 'kg')
    with pytest.raises(ValueError, match="no stored reference"):
        _ = q.unit['g[H2]']

def test_unit_lookup_no_reference_anywhere():
    q = Quantity(1, 'kg')
    assert q.unit['g'] == 1000.0

def test_unit_lookup_stored_but_not_requested():
    q = Quantity(1, 'kg[H2]')
    assert q.unit['g'] == 1000.0

def test_unit_lookup_reference_mismatch_names_correct_token():
    q = Quantity(1, 'kg[H2] / J[electricity]')
    with pytest.raises(ValueError, match="Reference mismatch for 'MJ'"):
        _ = q.unit['g[H2]/ MJ[wrong]']

def test_quantity_reference_kwarg_basic():
    q = Quantity(1, 'J / kg', reference=['H2', 'H2'])
    assert q.reference == ['H2', 'H2']
    assert repr(q) == "Quantity(1.0, 'J[H2] / kg[H2]')"

def test_quantity_reference_kwarg_length_mismatch_raises():
    with pytest.raises(ValueError, match="lengths must match"):
        Quantity(1, 'J / kg', reference=['H2'])

def test_quantity_reference_kwarg_and_brackets_conflict_raises():
    with pytest.raises(ValueError, match="choose one"):
        Quantity(1, 'kg[H2]', reference=['H2O'])

def test_quantity_no_reference_and_no_kwarg():
    q = Quantity(1, 'kg')
    assert q.reference == []

def test_parse_reference_composite_multiply():
    result = parse_reference('kW[grid] * h[duration]')
    assert result == ('kW * h', ['grid', 'duration'])

def test_quantity_composite_multiply():
    q = Quantity(1, 'kW[grid] * h[duration]')
    assert q.reference == ['grid', 'duration']
    assert q.dimension == 'power * time'
    assert repr(q) == "Quantity(3600000.0, 'W[grid] * s[duration]')"

def test_quantity_composite_parens_then_divide():
    q = Quantity(1, '(kg[H2] * m[distance]) / s[time]')
    assert q.reference == ['H2', 'distance', 'time']
    assert q.dimension == '( mass * length ) / time'
    assert repr(q) == "Quantity(1.0, '( kg[H2] * m[distance] ) / s[time]')"

def test_parse_reference_composite_triple_divide():
    result = parse_reference('kWh[solar] / m2[area] / day[production]')
    assert result == ('kWh / m2 / day', ['solar', 'area', 'production'])

def test_quantity_composite_triple_divide():
    q = Quantity(1, 'kWh[solar] / m2[area] / day[production]')
    assert q.reference == ['solar', 'area', 'production']
    assert q.dimension == 'energy / area / time'
    assert repr(q) == "Quantity(41.666666666666664, 'J[solar] / m2[area] / s[production]')"

def test_quantity_composite_divide_by_parens():
    q = Quantity(1, 'kg[H2] / (m[length] * s[time])')
    assert q.reference == ['H2', 'length', 'time']
    assert q.dimension == 'mass / ( length * time )'
    assert repr(q) == "Quantity(1.0, 'kg[H2] / ( m[length] * s[time] )')"

def test_parse_reference_composite_nested_duplicate_tokens():
    result = parse_reference('(kg[H2] * m[distance]) / (s[t1] * s[t2])')
    assert result == ('(kg * m) / (s * s)', ['H2', 'distance', 't1', 't2'])

def test_quantity_composite_nested_duplicate_tokens():
    q = Quantity(1, '(kg[H2] * m[distance]) / (s[t1] * s[t2])')
    assert q.reference == ['H2', 'distance', 't1', 't2']
    assert q.dimension == '( mass * length ) / ( time * time )'
    assert repr(q) == "Quantity(1.0, '( kg[H2] * m[distance] ) / ( s[t1] * s[t2] )')"

def test_quantity_voltage_with_reference():
    q = Quantity(1, 'V[cell]')
    assert q.reference == ['cell']
    assert q.dimension == 'voltage'
    assert repr(q) == "Quantity(1.0, 'V[cell]')"

def test_quantity_current_with_reference():
    q = Quantity(1, 'A[stack]')
    assert q.reference == ['stack']
    assert q.dimension == 'current'
    assert repr(q) == "Quantity(1.0, 'A[stack]')"

def test_quantity_pressure_with_reference():
    q = Quantity(1, 'bar[reactor]')
    assert q.reference == ['reactor']
    assert q.dimension == 'pressure'
    assert q.unit['Pa[reactor]'] == 100000.0

def test_quantity_force_with_reference():
    q = Quantity(1, 'N[load]')
    assert q.reference == ['load']
    assert q.dimension == 'force'
    assert repr(q) == "Quantity(1.0, 'N[load]')"

def test_quantity_frequency_with_reference():
    q = Quantity(1, 'Hz[pulse]')
    assert q.reference == ['pulse']
    assert q.dimension == 'frequency'
    assert repr(q) == "Quantity(1.0, 'Hz[pulse]')"

def test_quantity_substance_composite_real_pattern():
    q = Quantity(1, 'mol[H2]/h/kg[catalyst]')
    assert q.reference == ['H2', None, 'catalyst']
    assert q.dimension == 'substance / time / mass'
    assert q.unit['mol[H2] / h / kg[catalyst]'] == 1.0
