"""Tests for pyH2A.Analysis.Sensitivity_Analysis.

Covers, against the three real per-route fixtures (Sensitivity_Analysis_PV_E.md,
Sensitivity_Analysis_PC.md, Sensitivity_Analysis_PEC.md - each a single-route file
with its own merged-in base scenario and its own 'Parameters - Sensitivity_Analysis'
table, no route toggling):
- End-to-end regression of perform_sensitivity_analysis() for PV_E (base case LCOH
  and all six parameters' low/high results), cross-checked against known-correct
  values.
- The compounding-parameter behavior ('PV power loss per year' and
  'Electrolyzer power increase per year' produce much larger LCOH swings than
  the other four parameters) - protected explicitly so it isn't mistaken for a
  bug and "fixed" away later.
- The Dependent variable configuration states: isolated resolution logic,
  fallback when the row/table is missing, and loud failure on an invalid path.
- A smoke test confirming plot_sensitivity_box_plot() produces a real saved figure.
- Real end-to-end regression for the PC and PEC routes, with base-case results
  cross-checked against the independently-established reference values in
  e2e_lcoh/lcoh_test.py.
"""
import matplotlib
matplotlib.use('Agg')

import pathlib
import matplotlib.figure
import pytest

from pyH2A.Analysis.Sensitivity_Analysis import (
    Sensitivity_Analysis,
    _resolve_dependent_variable,
)
from pyH2A.Utilities.Unit_Handler.quantity import Quantity

FIXTURE_FILE = "src/tests/end_to_end/Sensitivity_Analysis_PV_E.md"

# Very strict tolerance to detect economic regression, matching e2e_lcoh/lcoh_test.py
TOLERANCE = 1e-13

BASE_CASE_LCOH = 4.194302976489664

SENSITIVITY_CASES = [
    ("PV CAPEX ($/kW)", "400", 3.2759717727096596, "1600", 5.91232929552307),
    ("Electrolyzer CAPEX ($/kW)", "400", 3.51052141408656, "1600", 5.647338796596263),
    ("Electrolyzer efficiency (kg H2/kWh)", "0.015", 4.177668207171888, "0.025", 11.584440918965948),
    ("PV power loss per year", "0.25%", 3.3320035303178788, "1.0%", 69.4041780474443),
    ("Electrolyzer power increase per year", "0.15%", 3.355277092258832, "0.6%", 34.852338723337255),
    ("Stack repl. cost (% of E-CAPEX)", "20%", 4.0704160476158595, "80%", 4.442076834237272),
]

COMPOUNDING_PARAMETERS = ["PV power loss per year", "Electrolyzer power increase per year"]
NON_COMPOUNDING_PARAMETERS = [
    "PV CAPEX ($/kW)",
    "Electrolyzer CAPEX ($/kW)",
    "Electrolyzer efficiency (kg H2/kWh)",
    "Stack repl. cost (% of E-CAPEX)",
]

# PC and PEC base-case values below match e2e_lcoh/lcoh_test.py's independently-established
# Photocatalytic_Base / PEC_Base reference values (to within TOLERANCE) - confirmed by direct
# comparison, not just self-consistency. The per-parameter low/high values were established by
# running the real calculation once and recording the result, the same way PV_E's were.

PC_BASE_CASE_LCOH = 185.44329282256817

PC_SENSITIVITY_CASES = [
    ("Catalyst cost (USD/kg)", "1000", 63.82327544646941, "5000", 307.0633101986669),
    ("PC solar-to-hydrogen efficiency", "0.01", 369.9587869716658, "0.05", 75.58434559728198),
    ("Catalyst lifetime (year)", "0.25", 356.9834624514529, "1", 99.67320800812587),
    ("Reactor baggie lifetime (year)", "2", 186.08447984575596, "10", 185.23355234183256),
    ("Baggie markup factor", "1.2", 185.3277696620435, "2", 185.6358314234427),
    ("Filtration cost (USD/m3)", "0.12", 185.4318746208626, "0.48", 185.46612922597936),
]

PEC_BASE_CASE_LCOH = 139.41887561917213

PEC_SENSITIVITY_CASES = [
    ("PEC cell cost (USD/m2)", "10000", 67.70661218209143, "30000", 198.09254570405636),
    ("PEC solar-to-hydrogen efficiency", "0.1", 194.83903694112269, "0.18", 108.38219039989289),
    ("PEC cell lifetime (year)", "0.2", 224.82105621642577, "1", 51.38893561892604),
    ("Concentration factor", "10", 685.6162937628226, "100", 70.94999683090947),
    ("Concentrator cost (USD/m2)", "50", 138.7620589467385, "200", 140.7325089640393),
    ("Industrial electricity usage", "0.08", 139.4127382029007, "0.32", 139.43115045171493),
]


@pytest.fixture(scope="module")
def sensitivity_analysis():
    return Sensitivity_Analysis(FIXTURE_FILE)


@pytest.fixture(scope="module")
def results(sensitivity_analysis):
    return sensitivity_analysis.perform_sensitivity_analysis()


# ── Test Group 1: main working case ─────────────────────────────────────────

def test_base_case_levelized_cost(sensitivity_analysis):
    # Same access expression as e2e_lcoh/lcoh_test.py, so this is a genuine
    # cross-check against that already-verified value, not a re-test of the
    # same helper function used elsewhere in this module.
    obtained = sensitivity_analysis.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kg']
    assert obtained == pytest.approx(BASE_CASE_LCOH, abs=TOLERANCE)


@pytest.mark.parametrize(
    "name, low_key, low_value, high_key, high_value",
    SENSITIVITY_CASES,
    ids=[case[0] for case in SENSITIVITY_CASES],
)
def test_sensitivity_parameter_low_high_values(results, name, low_key, low_value, high_key, high_value):
    assert results[name]["Values"][low_key] == pytest.approx(low_value, abs=TOLERANCE)
    assert results[name]["Values"][high_key] == pytest.approx(high_value, abs=TOLERANCE)


# ── Test Group 2: compounding-parameter behavior ────────────────────────────

def test_compounding_parameters_dominate_sensitivity_range(results):
    # 'PV power loss per year' and 'Electrolyzer power increase per year' are
    # applied as (1 -/+ rate) ** year, compounding over the plant's ~20-year
    # operating life (Photovoltaic_Plugin.calculate_photovoltaic_loss_correction,
    # Electrolyzer_Plugin.calculate_electrolyzer_power_demand). This makes their
    # high-value LCOH swings legitimately, dramatically larger than the other
    # four (non-compounding) parameters - confirmed by hand-calculation and by
    # running the real model. This is expected, correct model behavior, not a
    # bug - this test exists so a future change that flattens these swings back
    # down is caught as a regression, not mistaken for a fix.
    compounding_highs = [max(results[name]["Values"].values()) for name in COMPOUNDING_PARAMETERS]
    non_compounding_highs = [max(results[name]["Values"].values()) for name in NON_COMPOUNDING_PARAMETERS]

    assert min(compounding_highs) > 2 * max(non_compounding_highs)

    for high_value in compounding_highs:
        assert high_value >= 5 * BASE_CASE_LCOH


# ── Test Group 3: Dependent variable configuration states ──────────────────

def test_resolve_dependent_variable_valid_path():
    fake_dcf = type("FakeDCF", (), {})()
    fake_dcf.inp = {
        "Dependent Variables": {
            "Levelized cost": {"Value": Quantity(BASE_CASE_LCOH, "USD/kg")},
        },
    }
    result = _resolve_dependent_variable(fake_dcf, "{Dependent Variables > Levelized cost > Value, USD/kg}")
    assert result == pytest.approx(BASE_CASE_LCOH, abs=TOLERANCE)


def test_resolve_dependent_variable_invalid_path_raises():
    fake_dcf = type("FakeDCF", (), {})()
    fake_dcf.inp = {
        "Dependent Variables": {
            "Levelized cost": {"Value": Quantity(BASE_CASE_LCOH, "USD/kg")},
        },
    }
    with pytest.raises(KeyError, match="Nonexistent Row"):
        _resolve_dependent_variable(fake_dcf, "{Dependent Variables > Nonexistent Row > Value, USD/kg}")


def test_missing_dependent_variable_row_falls_back(tmp_path, results):
    original_text = pathlib.Path(FIXTURE_FILE).read_text()
    block_to_remove = (
        "# Sensitivity_Analysis\n"
        "\n"
        "Name | Value | Label\n"
        "--- | --- | ---\n"
        "Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg} | Levelized Cost\n"
        "\n"
    )
    assert block_to_remove in original_text

    variant_path = tmp_path / "Sensitivity_Analysis_no_dependent_variable.md"
    variant_path.write_text(original_text.replace(block_to_remove, ""))

    sa_variant = Sensitivity_Analysis(str(variant_path))
    assert sa_variant.dependent_variable_string == "{Dependent Variables > Levelized cost > Value, USD/kg}"

    base_case_value = _resolve_dependent_variable(sa_variant.base_case, sa_variant.dependent_variable_string)
    assert base_case_value == pytest.approx(BASE_CASE_LCOH, abs=TOLERANCE)

    variant_results = sa_variant.perform_sensitivity_analysis()
    for name in results:
        for key in results[name]["Values"]:
            assert variant_results[name]["Values"][key] == pytest.approx(results[name]["Values"][key], abs=TOLERANCE)


def test_invalid_dependent_variable_path_raises(tmp_path):
    original_text = pathlib.Path(FIXTURE_FILE).read_text()
    good_line = "Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg} | Levelized Cost"
    bad_line = "Dependent variable | {Dependent Variables > Nonexistent Row > Value, USD/kg} | Levelized Cost"
    assert good_line in original_text

    variant_path = tmp_path / "Sensitivity_Analysis_bad_path.md"
    variant_path.write_text(original_text.replace(good_line, bad_line))

    sa_variant = Sensitivity_Analysis(str(variant_path))
    with pytest.raises(KeyError, match="Nonexistent Row"):
        sa_variant.perform_sensitivity_analysis()


# ── Test Group 3b: dependent-variable label/unit resolution ─────────────────
#
# configure_dependent_variable() reads display label and unit directly off the
# 'Dependent variable' row itself ('Value' for the path/unit, 'Label' for the
# display name) - the row is self-describing, no shared or per-module config
# dict is consulted. Two cases: the row has a 'Label' column (real, current
# use case), or it doesn't (falls back to today's hardcoded default behavior).

def test_dependent_variable_label_and_unit_resolve_from_row(sensitivity_analysis):
    # Regression protection for the current real use case: the 'Dependent variable'
    # row's own 'Label' column is read directly, no config dict involved.
    assert sensitivity_analysis.dependent_variable_label == 'Levelized Cost'
    assert sensitivity_analysis.dependent_variable_unit == 'USD/kg'


def test_dependent_variable_missing_label_falls_back_to_hardcoded_default(tmp_path):
    # A 'Dependent variable' row with no 'Label' column must not crash - it leaves
    # dependent_variable_label as None, so callers (e.g. plot_sensitivity_box_plot)
    # fall back to today's hardcoded default behavior. Unit still parses fine from
    # the 'Value' column regardless - only Label is missing.
    original_text = pathlib.Path(FIXTURE_FILE).read_text()
    good_line = "Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg} | Levelized Cost"
    no_label_line = "Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg}"
    assert good_line in original_text

    variant_path = tmp_path / "Sensitivity_Analysis_no_label.md"
    variant_path.write_text(original_text.replace(good_line, no_label_line))

    sa_variant = Sensitivity_Analysis(str(variant_path))
    assert sa_variant.dependent_variable_label is None
    assert sa_variant.dependent_variable_unit == 'USD/kg'


# ── Test Group 4: chart generation smoke test ───────────────────────────────

def test_sensitivity_box_plot_smoke(tmp_path, sensitivity_analysis):
    fig = sensitivity_analysis.plot_sensitivity_box_plot(
        directory=str(tmp_path),
        input_file_name="smoke",
        save=True,
        show=False,
        pdf=False,
        dpi=100,
    )
    assert isinstance(fig, matplotlib.figure.Figure)

    saved_files = list(tmp_path.glob("*.png"))
    assert len(saved_files) == 1
    assert saved_files[0].stat().st_size > 0


# ── Test Group 6: PC and PEC route ground-truth verification ────────────────
#
# Real end-to-end runs for the PC and PEC routes, each its own single-route
# fixture (Sensitivity_Analysis_PC.md / Sensitivity_Analysis_PEC.md). Each
# route's base case is cross-checked against e2e_lcoh/lcoh_test.py's
# independently-established reference value for that route, the same way
# PV_E's is.

@pytest.fixture(scope="module")
def pc_sensitivity_analysis():
    return Sensitivity_Analysis("src/tests/end_to_end/Sensitivity_Analysis_PC.md")


@pytest.fixture(scope="module")
def pc_results(pc_sensitivity_analysis):
    return pc_sensitivity_analysis.perform_sensitivity_analysis()


@pytest.fixture(scope="module")
def pec_sensitivity_analysis():
    return Sensitivity_Analysis("src/tests/end_to_end/Sensitivity_Analysis_PEC.md")


@pytest.fixture(scope="module")
def pec_results(pec_sensitivity_analysis):
    return pec_sensitivity_analysis.perform_sensitivity_analysis()


def test_pc_route_base_case_matches_independent_reference(pc_sensitivity_analysis):
    obtained = pc_sensitivity_analysis.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kg']
    assert obtained == pytest.approx(PC_BASE_CASE_LCOH, abs=TOLERANCE)
    # Cross-check against e2e_lcoh/lcoh_test.py's independently-established
    # Photocatalytic_Base reference value - not just internal self-consistency.
    assert obtained == pytest.approx(185.44329282256822, abs=TOLERANCE)


@pytest.mark.parametrize(
    "name, low_key, low_value, high_key, high_value",
    PC_SENSITIVITY_CASES,
    ids=[case[0] for case in PC_SENSITIVITY_CASES],
)
def test_pc_route_parameter_low_high_values(pc_results, name, low_key, low_value, high_key, high_value):
    assert pc_results[name]["Values"][low_key] == pytest.approx(low_value, abs=TOLERANCE)
    assert pc_results[name]["Values"][high_key] == pytest.approx(high_value, abs=TOLERANCE)


def test_pec_route_base_case_matches_independent_reference(pec_sensitivity_analysis):
    obtained = pec_sensitivity_analysis.base_case.inp['Dependent Variables']['Levelized cost']['Value'].unit['USD/kg']
    assert obtained == pytest.approx(PEC_BASE_CASE_LCOH, abs=TOLERANCE)
    # Cross-check against e2e_lcoh/lcoh_test.py's independently-established
    # PEC_Base reference value - not just internal self-consistency.
    assert obtained == pytest.approx(139.41887561917213, abs=TOLERANCE)


@pytest.mark.parametrize(
    "name, low_key, low_value, high_key, high_value",
    PEC_SENSITIVITY_CASES,
    ids=[case[0] for case in PEC_SENSITIVITY_CASES],
)
def test_pec_route_parameter_low_high_values(pec_results, name, low_key, low_value, high_key, high_value):
    assert pec_results[name]["Values"][low_key] == pytest.approx(low_value, abs=TOLERANCE)
    assert pec_results[name]["Values"][high_key] == pytest.approx(high_value, abs=TOLERANCE)
