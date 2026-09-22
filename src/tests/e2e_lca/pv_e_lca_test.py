"""End-to-end LCA test of the PV + electrolysis (PV-E) model, using the openLCA matrix
export in ``src/tests/plugins/lca_data/matrix_folders/pve_unit_test``.

Each scenario is run through ``pyH2A.run_pyH2A.pyH2A`` with a PV-E workflow
(``Hourly_Irradiation_Plugin``, ``Photovoltaic_Plugin``, ``Electrolyzer_Plugin`` and
``Reverse_Osmosis_Plugin``, merged with ``Config/Defaults_LCA.md``). pyH2A sizes and
simulates the plant, and the ``LCA - PV-E Components`` table links the plugin outputs
to the direct inputs of the export's ``H2 Production`` process, each as a plant-lifetime
total in the flow unit of the export:

========================== ============ ===================================================
Export process (flow)      Flow unit    pyH2A output
========================== ============ ===================================================
PV Electricity Generation  MJ           Electrolyzer > Electricity consumption (yearly)
Electrolyzer Manufacturing Item(s)      Electrolyzer > Number of stacks over plant life
Reverse Osmosis            kg           Reverse Osmosis > Purified water production (yearly)
========================== ============ ===================================================

The amount of H2 itself (the reference flow) is ``Total output at gate``, computed by
``Production_Plugin``. PV modules and reverse osmosis devices are not direct inputs of
``H2 Production`` in the export (they are inputs of ``PV Electricity Generation``, per MJ,
and of ``Reverse Osmosis``, per kg), so they enter the LCA through the export's own
coefficients. The PV module area and number of reverse osmosis devices computed by pyH2A
are checked as plugin outputs only.

Ground truth
------------
Nothing but ``H2 Production`` itself consumes H2 (row 0 of the technosphere matrix has
a single entry) and ``H2 Production`` has no direct elementary flows (column 0 of the
intervention matrix is empty). Rewriting column 0 therefore leaves the life cycle of
every other process untouched, and the exact impact per kg of H2 of any scenario is

    impact = (sum over components of amount * unit impact) / total output at gate,

where the unit impact of a component is the impact of one unit of its flow (1 MJ of PV
electricity, 1 electrolyzer stack, 1 kg of purified water). The unit impacts are
obtained once from a direct solve of the unmodified export (see
``test_unit_impacts_match_direct_solve_of_export``) and are stored in
``_UNIT_IMPACTS``, so that the ground truth of a scenario costs a dot product. This
does not involve any of the ``LCA_Plugin`` machinery (Sherman-Morrison update,
precomputed LCIA operator, caching, unit conversion or UUID matching), which is
exactly what is compared against it, and it makes the ground truth cheap enough to
check every sample of a Monte Carlo analysis of the same model.

Caching note
------------
As in ``lca_e2e_all_layers_test.py``, the base scenario clears the disk cache of the
export before running (cold disk and RAM), and the second scenario clears only the RAM
cache (warm disk). A module-scoped fixture removes the disk cache once all tests have
finished.
"""

import csv
import shutil
from pathlib import Path

import numpy as np
import pytest
from pyH2A.Plugins.LCA_Plugin import LCA_Plugin
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.lca_utilities import factorize, find_matrix_path, matrix_of


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_INPUT_FILES_DIR = _HERE / 'data' / 'input_files'
_MATRIX_FOLDER = _HERE.parent / 'plugins' / 'lca_data' / 'matrix_folders' / 'pve_unit_test'

# ── UUIDs (provider IDs of index_A.csv) ────────────────────────────────────

_UUID_H2_PRODUCTION    = '66b8a6b0-7b7a-4d2c-95d3-d82951c58a35'
_UUID_PV_ELECTRICITY   = 'bc18dc79-2b51-455d-9fec-decf6b2693de'
_UUID_ELECTROLYZER_MFG = '4397d5db-7fea-4916-af17-b72fa72fc02a'
_UUID_REVERSE_OSMOSIS  = '1659c3a5-5c6b-4f29-b746-e12119144b7b'

_COMPONENT_UUIDS = (_UUID_PV_ELECTRICITY, _UUID_ELECTROLYZER_MFG, _UUID_REVERSE_OSMOSIS)

# ── Impacts ────────────────────────────────────────────────────────────────

_GTP100 = 'Climate change no LT - Global temperature change potential (GTP100) no LT'
_GTP20  = 'Climate change no LT - Global temperature change potential (GTP20) no LT'
_GWP100 = 'Climate change no LT - Global warming potential (GWP100) no LT'
_GWP20  = 'Climate change no LT - Global warming potential (GWP20) no LT'

_IMPACT_UNIT = 'kg[$CO_{2}$-Eq] / kg[H2]'

# Impact (kg CO2-Eq) of one unit of each component flow: 1 MJ of PV electricity, one
# electrolyzer stack and 1 kg of purified water, from a direct solve of the unmodified
# export (scipy SuperLU). Different sparse solvers agree on these to within a few 1e-9.
_UNIT_IMPACTS = {
    _GTP100: {_UUID_PV_ELECTRICITY:   0.002147126892435275,
              _UUID_ELECTROLYZER_MFG: 2.492451777733996,
              _UUID_REVERSE_OSMOSIS:  0.00012583342717717292},
    _GTP20:  {_UUID_PV_ELECTRICITY:   0.0025096013259351233,
              _UUID_ELECTROLYZER_MFG: 2.9529296598144836,
              _UUID_REVERSE_OSMOSIS:  0.00014876964301202108},
    _GWP100: {_UUID_PV_ELECTRICITY:   0.0022874458433345688,
              _UUID_ELECTROLYZER_MFG: 2.6785919386047565,
              _UUID_REVERSE_OSMOSIS:  0.0001349841633515652},
    _GWP20:  {_UUID_PV_ELECTRICITY:   0.002608899813045635,
              _UUID_ELECTROLYZER_MFG: 3.093934729082845,
              _UUID_REVERSE_OSMOSIS:  0.0001561523833094844},
}

# Relative tolerance of LCA results. The LCA_Plugin results match the ground truth to
# about 5e-11, but the unit impacts above and the pinned results below depend on the
# sparse solver at the level of a few 1e-9 (e.g. SuperLU vs. pypardiso).
_LCA_TOLERANCE = 1e-8

# Relative tolerance of plugin outputs, which do not involve any solve.
_PLUGIN_TOLERANCE = 1e-12

# Kilograms of water per kilogram of H2 (as used by Reverse_Osmosis_Plugin).
_WATER_PER_H2 = 18.01528 / 2.016


# ── Scenario data ────────────────────────────────────────────────────────────
#
# Pinned plugin outputs and GWP100 result of each scenario, for regression. Both
# scenarios operate for 20 years. The second scenario changes every LCA relevant input
# of the base scenario: electrolyzer size, degradation, efficiency, stack lifetime and
# unit size, as well as PV oversize ratio and efficiency, and reverse osmosis recovery
# rate and device size.

_SCENARIOS = {
    'base': {
        'input_file_stem': 'pv_e_base',
        'total_output_kg': 6708682.296429539,
        'electricity_MJ': 1342757787.8917065,
        'number_of_electrolyzers': 11.0,           # 5500 kW / 500 kW
        'number_of_stacks': 22.0,                  # 11 units * (1 + 1 replacement)
        'purified_water_kg': 59949796.62758987,
        'number_of_ro_devices': 5.3551594166740735,
        'module_area_m2': 37500.0,                 # 1.5 * 5500 kW / 0.22 kW/m2
        'electrolyzer_yield_kg_per_kWh': 0.0185,
        'electrolyzer_power_increase': 0.003,
        'gwp100': 0.45905243187039513,
    },
    'S2': {
        'input_file_stem': 'pv_e_s2',
        'total_output_kg': 5854530.270355666,
        'electricity_MJ': 1104956881.6507807,
        'number_of_electrolyzers': 16.0,           # 4000 kW / 250 kW
        'number_of_stacks': 48.0,                  # 16 units * (1 + 2 replacements)
        'purified_water_kg': 52316965.321891375,
        'number_of_ro_devices': 8.154525431243787,
        'module_area_m2': 44444.444444444445,      # 2.0 * 4000 kW / 0.18 kW/m2
        'electrolyzer_yield_kg_per_kWh': 0.02,
        'electrolyzer_power_increase': 0.005,
        'gwp100': 0.43295011610965656,
    },
}

_OPERATION_YEARS = 20


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clear_ram_only():
    """Force the next run onto the disk-cache path without touching disk."""
    LCA_Plugin._cache_key = None


def _clear_disk():
    disk_cache_dir = _MATRIX_FOLDER / 'Initial_Artifacts'
    if disk_cache_dir.exists():
        shutil.rmtree(disk_cache_dir)


def column_0_amounts(inp):
    """Plant-lifetime amounts of the direct inputs of ``H2 Production``, in the flow
    units of the export (MJ, Item(s), kg), taken from the tables the plugins insert
    their outputs into.

    Parameters
    ----------
    inp : dict
        ``inp`` of a pyH2A run of the PV-E model.

    Returns
    -------
    dict
        Mapping from component UUID to amount.
    """
    return {
        _UUID_PV_ELECTRICITY: float(np.sum(
            inp['Electrolyzer']['Electricity consumption (yearly)']['Value'].unit['MJ'])),
        _UUID_ELECTROLYZER_MFG: float(
            inp['Electrolyzer']['Number of stacks over plant life']['Value'].unit['-']),
        _UUID_REVERSE_OSMOSIS: float(np.sum(
            inp['Reverse Osmosis']['Purified water production (yearly)']['Value'].unit['kg'])),
    }


def ground_truth_impacts(amounts, total_output_kg):
    """Exact impacts per kg of H2 for the given component amounts, see module docstring.

    Parameters
    ----------
    amounts : dict
        Mapping from component UUID to plant-lifetime amount, as returned by
        :func:`column_0_amounts`.
    total_output_kg : float
        Total output of H2 at gate over the plant lifetime, in kg.

    Returns
    -------
    dict
        Mapping from impact name to impact in kg CO2-Eq per kg of H2.
    """
    return {impact_name: sum(amounts[uuid] * unit_impacts[uuid] for uuid in _COMPONENT_UUIDS) / total_output_kg
            for impact_name, unit_impacts in _UNIT_IMPACTS.items()}


# ── Scenarios ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('scenario_label', list(_SCENARIOS))
def test_pv_e_lca(scenario_label):
    """Runs the PV-E model with LCA and checks, in turn, the plugin outputs sizing the
    plant, the amounts the LCA_Plugin received, and every impact against the ground truth.

    The base scenario runs on a cold disk and RAM cache, the second scenario on a warm
    disk cache with a cold RAM cache (see module docstring)."""

    scenario = _SCENARIOS[scenario_label]

    if scenario_label == 'base':
        _clear_disk()
    else:
        _clear_ram_only()

    result = pyH2A(str(_INPUT_FILES_DIR / f"{scenario['input_file_stem']}.md"), str(_INPUT_FILES_DIR))
    inp = result.base_case.inp

    # Plugin outputs sizing the plant
    total_output = inp['Technical Operating Parameters and Specifications']['Total output at gate']['Value'].unit['kg']
    amounts = column_0_amounts(inp)

    assert total_output == pytest.approx(scenario['total_output_kg'], rel=_PLUGIN_TOLERANCE)
    assert amounts[_UUID_PV_ELECTRICITY] == pytest.approx(scenario['electricity_MJ'], rel=_PLUGIN_TOLERANCE)
    assert amounts[_UUID_ELECTROLYZER_MFG] == pytest.approx(scenario['number_of_stacks'], rel=_PLUGIN_TOLERANCE)
    assert amounts[_UUID_REVERSE_OSMOSIS] == pytest.approx(scenario['purified_water_kg'], rel=_PLUGIN_TOLERANCE)

    assert (inp['Electrolyzer']['Number of electrolyzers required']['Value'].unit['-']
            == pytest.approx(scenario['number_of_electrolyzers'], rel=_PLUGIN_TOLERANCE))
    assert (inp['Reverse Osmosis']['Number of devices required']['Value'].unit['-']
            == pytest.approx(scenario['number_of_ro_devices'], rel=_PLUGIN_TOLERANCE))
    assert (inp['Photovoltaic']['Module area']['Value'].unit['m2']
            == pytest.approx(scenario['module_area_m2'], rel=_PLUGIN_TOLERANCE))

    # Physical consistency of the amounts. All H2 reaches the gate (capacity factor and
    # fraction reaching the gate are 100 %), so the water demand is exactly stoichiometric,
    # and the electricity demand per kg of H2 lies between that of a new stack and that of
    # a stack at the end of the plant life.
    assert amounts[_UUID_REVERSE_OSMOSIS] / total_output == pytest.approx(_WATER_PER_H2, rel=_PLUGIN_TOLERANCE)

    electricity_kWh_per_kg = amounts[_UUID_PV_ELECTRICITY] / 3.6 / total_output
    new_stack_kWh_per_kg = 1. / scenario['electrolyzer_yield_kg_per_kWh']
    degraded_stack_kWh_per_kg = (new_stack_kWh_per_kg
                                 * (1. + scenario['electrolyzer_power_increase']) ** (_OPERATION_YEARS - 1))
    assert new_stack_kWh_per_kg < electricity_kWh_per_kg < degraded_stack_kWh_per_kg

    # Each electrolyzer gets one stack initially and one more at every replacement
    replacement_time = inp['Electrolyzer']['Actual stack replacement time']['Value'].unit['year']
    assert amounts[_UUID_ELECTROLYZER_MFG] == pytest.approx(
        scenario['number_of_electrolyzers'] * _OPERATION_YEARS / replacement_time, rel=_PLUGIN_TOLERANCE)

    # The LCA_Plugin received exactly these amounts (the LCA table links the right outputs,
    # in the right units, to the right UUIDs), with the signs of the export's column.
    lca = result.base_case.plugs['LCA_Plugin']
    received = dict(zip(LCA_Plugin._cache['A0_column'][0], lca.component_values))

    assert received.pop(_UUID_H2_PRODUCTION) == pytest.approx(total_output, rel=_PLUGIN_TOLERANCE)
    assert received == pytest.approx({uuid: -amount for uuid, amount in amounts.items()}, rel=_PLUGIN_TOLERANCE)

    # Every impact category against the ground truth, as well as against the pinned GWP100
    expected_impacts = ground_truth_impacts(amounts, total_output)

    assert set(inp['Dependent Variables']) == set(expected_impacts)

    for impact_name, expected in expected_impacts.items():
        quantity = inp['Dependent Variables'][impact_name]['Value']

        assert quantity.supplied_value == pytest.approx(expected, rel=_LCA_TOLERANCE), impact_name
        assert quantity.supplied_unit_reference == _IMPACT_UNIT

    assert inp['Dependent Variables'][_GWP100]['Value'].supplied_value == pytest.approx(scenario['gwp100'],
                                                                                       rel=_LCA_TOLERANCE)


# ── Ground truth ─────────────────────────────────────────────────────────────

def test_unit_impacts_match_direct_solve_of_export():
    """The stored unit impacts are those of a direct solve of the unmodified export, and
    the export has the structure the ground truth formula relies on."""

    matrix_a = matrix_of(find_matrix_path(str(_MATRIX_FOLDER), 'A'))
    matrix_b = matrix_of(find_matrix_path(str(_MATRIX_FOLDER), 'B'))
    matrix_c = matrix_of(find_matrix_path(str(_MATRIX_FOLDER), 'C'))

    # Only H2 Production itself consumes H2, and it has no direct elementary flows, so the
    # life cycles of its inputs do not depend on column 0.
    np.testing.assert_array_equal(matrix_a.tocsr()[0].nonzero()[1], [0])
    assert matrix_b.tocsc()[:, 0].nnz == 0

    with open(_MATRIX_FOLDER / 'index_A.csv', 'r', encoding='utf-8') as stream:
        row_of_uuid = {row['provider ID']: int(row['index']) for row in csv.DictReader(stream)}

    with open(_MATRIX_FOLDER / 'index_C.csv', 'r', encoding='utf-8') as stream:
        impact_names = [row['indicator name'] for row in csv.DictReader(stream)]

    # One unit of demand of each component flow
    demand = np.zeros((matrix_a.shape[0], len(_COMPONENT_UUIDS)))
    for column, uuid in enumerate(_COMPONENT_UUIDS):
        demand[row_of_uuid[uuid], column] = 1.0

    scaling_vectors = np.asarray(factorize(matrix_a)(demand))
    unit_impacts = np.asarray(matrix_c @ (matrix_b @ scaling_vectors))

    assert set(impact_names) == set(_UNIT_IMPACTS)

    for row, impact_name in enumerate(impact_names):
        for column, uuid in enumerate(_COMPONENT_UUIDS):
            assert unit_impacts[row, column] == pytest.approx(_UNIT_IMPACTS[impact_name][uuid],
                                                              rel=_LCA_TOLERANCE)


# ── Cleanup: runs once after every test above has finished ─────────────────

@pytest.fixture(scope='module', autouse=True)
def _cleanup_disk_cache_after_module():  # noqa: F841
    """Remove the export's on-disk Initial_Artifacts cache once all tests in this
    module have finished, so no leftover cache directory remains."""

    yield

    _clear_disk()


if __name__ == '__main__':

    result = pyH2A('src/tests/e2e_lca/data/input_files/pv_e_base.md', 'src/tests/e2e_lca/data/input_files')
    print(result.base_case.inp['Dependent Variables'])
