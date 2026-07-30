"""Combined ground-truth end-to-end tests for pyH2A.Plugins.Life_Cycle_Assessment_Plugin across the
Smartphone_1Layer, Smartphone_2Layer, and Smartphone_3Layer toy models.

Each scenario is run through ``pyH2A.run_pyH2A.pyH2A`` (the same entry point
as the command-line pipeline). ``Test_Plugin_C``, ``Test_Plugin_D``, and
``Test_Plugin_E`` are introduced as dummy plugins (for Circuit Board, Display,
and Battery respectively). For 2-layer and 3-layer models, these three plugins
compute the Circuit Board / Display / Battery quantities
(base quantity * scenario factor) and insert them into dedicated output tables; the
``LCA - Smartphone GT Components`` table then references those outputs via
path syntax (e.g. ``{GT Display Output > Display > Value, kg}``). The Smartphone row 
itself (the functional-unit reference flow) stays a literal ``1.0``, and the 1-layer
model -- which has no sub-components -- carries no GT plugins at all.

Model summary
-------------
- 1-layer: single foreground process (Smartphone itself, no sub-components).
  One base scenario per impact method (GWP, CED, ACIDIFICATION).
- 2-layer: Smartphone directly consumes Display, Circuit Board, and Battery
  (no further sub-components). One base scenario per impact method (GWP, CED, ACIDIFICATION).
- 3-layer: Smartphone consumes Circuit Board/Display/Battery, each of which
  in turn consumes two raw-material sub-components. Five component-quantity
  scenarios (base, S2-S5) per impact method (GWP, CED, ACIDIFICATION), driven
  by each scenario's ``GT <Component> Input > Scenario Factor`` value.

All three models share the same expected base-case totals (GWP=10.0 kg CO2-eq,
CED=50.0 kWh, ACID=4.0 kg SO2-eq), since each is a progressively finer-grained
breakdown of the same underlying bill of materials and elementary flows.

Caching note
------------
Life_Cycle_Assessment_Plugin._cache is a single process-wide class attribute (shared by every LCA
instance for the lifetime of the pytest process, not reset between tests or
even between test files run in the same session), and it is not keyed by
matrix folder, so running more than one matrix folder within the same
process (such as when running multiple scenarios within one pytest session)
requires manually clearing both the RAM cache and that folder's
on-disk Initial_Artifacts cache before switching folders (otherwise a later
folder would silently reuse an earlier folder's cached artifacts, producing
incorrect results).

All groups (1-layer, 2-layer, and 3-layer per impact method) are driven by a
single parametrized test, ``test_scenarios``, that exercises all three LCA
caching paths across each group's scenarios in parametrize-list (execution)
order: scenario labeled "base" clears both caches itself before running (cold
disk+RAM); scenario labeled "S2", where present, clears only RAM (warm disk); any
remaining scenarios (S3-S5), where present, rely on RAM staying warm from the
previous scenario. 1-layer and 2-layer groups only have a base scenario, so
they always take the cold-disk+RAM path -- structurally identical to a
3-layer group's first scenario. A single module-scoped fixture clears every
group's on-disk cache once after the whole module finishes, for hygiene.
"""

import shutil
from pathlib import Path

import pytest
from pyH2A.Plugins.Life_Cycle_Assessment_Plugin import Life_Cycle_Assessment_Plugin
from pyH2A.Plugins.Life_Cycle_Assessment_Plugin.config import CONFIG
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.input_modification import convert_input_to_dictionary
from pyH2A.Utilities.lca_utils import get_cache_paths


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_INPUT_FILES_DIR = _HERE / 'data' / 'input_files'


# ── Shared helpers ─────────────────────────────────────────────────────────

def _clear_ram_only():
    for k in Life_Cycle_Assessment_Plugin._cache:
        Life_Cycle_Assessment_Plugin._cache[k] = None


def _clear_disk(matrix_folder):
    disk_cache_dir = Path(matrix_folder) / 'Initial_Artifacts'
    if disk_cache_dir.exists():
        shutil.rmtree(disk_cache_dir)


def _load_scenario(input_file_stem):
    """Parse a scenario input file and return (inp, matrix_folder)."""
    inp = convert_input_to_dictionary(str(_INPUT_FILES_DIR / f'{input_file_stem}.md'))
    matrix_folder = inp['Life Cycle Assessment']['Matrix Folder']['Value']
    return inp, matrix_folder


# ── Scenario data ────────────────────────────────────────────────────────────
#
# Each group is (input_file_stem, impact_name, expected_value, expected_unit)
# in base, S2, S3, S4, S5 order. 1-layer and 2-layer groups only have a base
# scenario; 3-layer groups have all five.

_SCENARIOS_BY_GROUP = {
    '1L-gwp': [('smartphone_1layer_gwp_base', 'Global warming potential', 10.0, 'kg CO2-eq')],
    '1L-ced': [('smartphone_1layer_ced_base', 'Cumulative energy demand', 50.0, 'kWh')],
    '1L-acid': [('smartphone_1layer_acid_base', 'Acidification', 4.0, 'kg SO2-eq')],
    '2L-gwp': [('smartphone_2layer_gwp_base', 'Global warming potential', 10.0, 'kg CO2-eq')],
    '2L-ced': [('smartphone_2layer_ced_base', 'Cumulative energy demand', 50.0, 'kWh')],
    '2L-acid': [('smartphone_2layer_acid_base', 'Acidification', 4.0, 'kg SO2-eq')],
    '3L-gwp': [
        ('smartphone_3layer_gwp_base', 'Global warming potential', 10.0, 'kg CO2-eq'),
        ('smartphone_3layer_gwp_s2', 'Global warming potential', 8.0, 'kg CO2-eq'),
        ('smartphone_3layer_gwp_s3', 'Global warming potential', 12.0, 'kg CO2-eq'),
        ('smartphone_3layer_gwp_s4', 'Global warming potential', 11.2, 'kg CO2-eq'),
        ('smartphone_3layer_gwp_s5', 'Global warming potential', 9.2, 'kg CO2-eq'),
    ],
    '3L-ced': [
        ('smartphone_3layer_ced_base', 'Cumulative energy demand', 50.0, 'kWh'),
        ('smartphone_3layer_ced_s2', 'Cumulative energy demand', 39.5, 'kWh'),
        ('smartphone_3layer_ced_s3', 'Cumulative energy demand', 60.5, 'kWh'),
        ('smartphone_3layer_ced_s4', 'Cumulative energy demand', 54.4, 'kWh'),
        ('smartphone_3layer_ced_s5', 'Cumulative energy demand', 47.4, 'kWh'),
    ],
    '3L-acid': [
        ('smartphone_3layer_acid_base', 'Acidification', 4.0, 'kg SO2-eq'),
        ('smartphone_3layer_acid_s2', 'Acidification', 3.2, 'kg SO2-eq'),
        ('smartphone_3layer_acid_s3', 'Acidification', 4.8, 'kg SO2-eq'),
        ('smartphone_3layer_acid_s4', 'Acidification', 4.66, 'kg SO2-eq'),
        ('smartphone_3layer_acid_s5', 'Acidification', 3.46, 'kg SO2-eq'),
    ],
}

_SCENARIO_LABELS = ['base', 'S2', 'S3', 'S4', 'S5']


# ── All layers: five (or, for 1-layer/2-layer, one) scenarios per group ─────
#
# Each group's scenarios below run consecutively (relying on parametrize-list
# order) and exercise all three LCA caching paths: cold disk+RAM on the first
# scenario, warm disk / cold RAM on the second (3-layer groups only), and warm
# RAM (no disk I/O) on any remaining scenarios. 1-layer and 2-layer groups
# have just the one (base) scenario, so they always take the cold-disk+RAM
# path.

@pytest.mark.parametrize(
    'group, scenario_index',
    [
        (group, scenario_index)
        for group, scenarios in _SCENARIOS_BY_GROUP.items()
        for scenario_index in range(len(scenarios))
    ],
    ids=[
        f'{group}-{_SCENARIO_LABELS[scenario_index]}'
        for group, scenarios in _SCENARIOS_BY_GROUP.items()
        for scenario_index in range(len(scenarios))
    ],
)
def test_scenarios(group, scenario_index):
    """Exercises all three LCA caching paths across every group's scenarios,
    in parametrize-list (execution) order: scenario 0 (base) is cold RAM+disk
    (compute_all_artifacts_from_scratch runs the full LU factorization and
    writes artifacts to disk and RAM); scenario 1 (S2), where present,
    explicitly clears RAM while leaving disk warm (load_all_from_disk_to_ram
    reads the artifacts saved above, bypassing factorization); scenarios 2-4
    (S3-S5), where present, rely on RAM staying warm from the previous
    scenario (initialize_all_artifacts exits on the early-exit guard without
    any disk I/O).

    Note: The disk cache is cleared unconditionally on scenario 0, even though
    ``_cleanup_disk_caches_after_module`` also clears it at the end of the
    module: that fixture won't have run yet the first time a fresh checkout
    runs these tests, may not run at all if the module is interrupted before
    it finishes, and clearing here is what guarantees a scenario 0 run reads
    artifacts produced by the current code rather than stale ones left over
    from a previous session or from before a refactor."""
    scenarios = _SCENARIOS_BY_GROUP[group]
    if scenario_index == 0:
        # since one pytest session runs in one process, Life_Cycle_Assessment_Plugin._cache should be deleted for every group's first scenario (cold start)
        # to avoid reusing another group's cached matrices.
        _clear_ram_only()
        # clear the disk cache path, so that the LCA run will recompute all artifacts from scratch between groups.
        get_cache_paths.cache_clear()
        # clear the disk cache as explained in the docstring note above
        _, matrix_folder = _load_scenario(scenarios[0][0])
        _clear_disk(matrix_folder)
    elif scenario_index == 1:
        _clear_ram_only()

    input_file_stem, impact_name, expected_value, expected_unit = scenarios[scenario_index]
    # ``expected_unit`` is the raw openLCA unit string (e.g. 'kg CO2-eq'), used
    # as a CONFIG lookup key to check the resolved unit stored on the result
    # Quantity, expressed as ``<impact unit> / <functional unit>``.
    input_file = _INPUT_FILES_DIR / f'{input_file_stem}.md'
    result = pyH2A(str(input_file), str(_INPUT_FILES_DIR))
    lca = result.base_case.lca
    quantity = lca.lca_results[impact_name]
    diff_pct = (quantity.supplied_value - expected_value) / expected_value * 100
    print(f'\n  pyH2A={quantity.supplied_value:.6f}  reference={expected_value:.6f}  diff={diff_pct:+.4f}%')
    assert quantity.supplied_value == pytest.approx(expected_value, rel=1e-3)
    expected = CONFIG[expected_unit]
    functional_unit_unit = str(Life_Cycle_Assessment_Plugin._cache['A0_column'][2][0])
    assert quantity.supplied_unit == f"{expected['unit']} / {functional_unit_unit}"


# ── Cleanup: runs once after every test above has finished ─────────────────

@pytest.fixture(scope='module', autouse=True)
def _cleanup_disk_caches_after_module():  # noqa: F841
    """Remove every group's on-disk Initial_Artifacts cache once all tests
    in this module have finished, so no leftover cache directories remain."""
    yield
    for scenarios in _SCENARIOS_BY_GROUP.values():
        _, matrix_folder = _load_scenario(scenarios[0][0])
        _clear_disk(matrix_folder)
