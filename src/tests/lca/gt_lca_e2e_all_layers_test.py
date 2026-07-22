"""Combined ground-truth end-to-end tests for pyH2A.LCA.LCA across the
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
LCA._cache is a single process-wide class attribute (shared by every LCA
instance for the lifetime of the pytest process, not reset between tests or
even between test files run in the same session), and it is not keyed by
matrix folder, so running more than one matrix folder within the same
process requires manually clearing both the RAM cache and that folder's
on-disk Initial_Artifacts cache before switching folders (otherwise a later
folder would silently reuse an earlier folder's cached artifacts, producing
incorrect results). This is unchanged by routing through ``pyH2A(...)``
instead of ``LCA(...)`` directly, since ``Discounted_Cash_Flow.__init__``
still ultimately instantiates the same process-wide ``LCA`` class:

- The 1-layer and 2-layer scenarios have one call per method, so each simply
  clears both caches before running (``_run_pyH2A_cold``).
- The 3-layer scenarios deliberately exercise all three LCA caching paths
  (cold disk+RAM, warm disk, warm RAM) across each impact method's five
  scenarios, in file-definition order: the first scenario's test
  clears both caches itself before running; the remaining four rely on that
  state staying warm, exactly mirroring the original standalone scripts'
  behavior. A single module-scoped fixture clears every scenario's on-disk
  cache once after the whole module finishes, for hygiene.
"""

import shutil
from pathlib import Path

import pytest
from pyH2A.LCA.LCA import LCA
from pyH2A.LCA.config import CONFIG
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.input_modification import convert_input_to_dictionary
from pyH2A.Utilities.lca_utils import get_cache_paths


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_INPUT_FILES_DIR = _HERE / 'data' / 'input_files'


# ── Shared helpers ─────────────────────────────────────────────────────────

def _clear_ram_only():
    for k in LCA._cache:
        LCA._cache[k] = None


def _clear_disk(matrix_folder):
    disk_cache_dir = Path(matrix_folder) / 'Initial_Artifacts'
    if disk_cache_dir.exists():
        shutil.rmtree(disk_cache_dir)


def _load_scenario(input_file_stem):
    """Parse a scenario input file and return (inp, matrix_folder)."""
    inp = convert_input_to_dictionary(str(_INPUT_FILES_DIR / f'{input_file_stem}.md'))
    matrix_folder = inp['Life Cycle Assessment']['Matrix Folder']['Value']
    return inp, matrix_folder

def _run_and_assert(input_file_stem, impact_name, expected_value, expected_unit):
    """``expected_unit`` is the raw openLCA unit string (e.g. 'kg CO2-eq'), used
    as a CONFIG lookup key to check the resolved unit stored on the result
    Quantity, expressed as ``<impact unit> / <functional unit>``."""
    input_file = _INPUT_FILES_DIR / f'{input_file_stem}.md'
    result = pyH2A(str(input_file), str(_INPUT_FILES_DIR))
    lca = result.base_case.lca
    quantity = lca.lca_results[impact_name]
    result = quantity.supplied_value
    diff_pct = (result - expected_value) / expected_value * 100
    print(f'\n  pyH2A={result:.6f}  reference={expected_value:.6f}  diff={diff_pct:+.4f}%')
    assert result == pytest.approx(expected_value, rel=1e-3)
    expected = CONFIG[expected_unit]
    functional_unit_unit = str(LCA._cache['A0_column'][2][0])
    assert quantity.supplied_unit == f"{expected['unit']} / {functional_unit_unit}"


# ── Scenario data ────────────────────────────────────────────────────────────

_SCENARIOS_1LAYER = [
    ('smartphone_1layer_gwp', 'Global warming potential', 10.0, 'kg CO2-eq'),
    ('smartphone_1layer_ced', 'Cumulative energy demand', 50.0, 'kWh'),
    ('smartphone_1layer_acid', 'Acidification', 4.0, 'kg SO2-eq'),
]

_SCENARIOS_2LAYER = [
    ('smartphone_2layer_gwp', 'Global warming potential', 10.0, 'kg CO2-eq'),
    ('smartphone_2layer_ced', 'Cumulative energy demand', 50.0, 'kWh'),
    ('smartphone_2layer_acid', 'Acidification', 4.0, 'kg SO2-eq'),
]

# Each list is (input_file_stem, impact_name, expected_value, expected_unit)
# in base, S2, S3, S4, S5 order.
_SCENARIOS_3LAYER_GWP = [
    ('smartphone_3layer_gwp_base', 'Global warming potential', 10.0, 'kg CO2-eq'),
    ('smartphone_3layer_gwp_s2', 'Global warming potential', 8.0, 'kg CO2-eq'),
    ('smartphone_3layer_gwp_s3', 'Global warming potential', 12.0, 'kg CO2-eq'),
    ('smartphone_3layer_gwp_s4', 'Global warming potential', 11.2, 'kg CO2-eq'),
    ('smartphone_3layer_gwp_s5', 'Global warming potential', 9.2, 'kg CO2-eq'),
]
_SCENARIOS_3LAYER_CED = [
    ('smartphone_3layer_ced_base', 'Cumulative energy demand', 50.0, 'kWh'),
    ('smartphone_3layer_ced_s2', 'Cumulative energy demand', 39.5, 'kWh'),
    ('smartphone_3layer_ced_s3', 'Cumulative energy demand', 60.5, 'kWh'),
    ('smartphone_3layer_ced_s4', 'Cumulative energy demand', 54.4, 'kWh'),
    ('smartphone_3layer_ced_s5', 'Cumulative energy demand', 47.4, 'kWh'),
]
_SCENARIOS_3LAYER_ACID = [
    ('smartphone_3layer_acid_base', 'Acidification', 4.0, 'kg SO2-eq'),
    ('smartphone_3layer_acid_s2', 'Acidification', 3.2, 'kg SO2-eq'),
    ('smartphone_3layer_acid_s3', 'Acidification', 4.8, 'kg SO2-eq'),
    ('smartphone_3layer_acid_s4', 'Acidification', 4.66, 'kg SO2-eq'),
    ('smartphone_3layer_acid_s5', 'Acidification', 3.46, 'kg SO2-eq'),
]


# ── 1-layer & 2-layer: single scenario per method ───────────────────────────

@pytest.mark.parametrize(
    'input_file_stem, impact_name, expected_value, expected_unit',
    _SCENARIOS_1LAYER + _SCENARIOS_2LAYER,
    ids=['1L-GWP', '1L-CED', '1L-ACID', '2L-GWP', '2L-CED', '2L-ACID'],
)
def test_1_2layer_result_matches_reference(input_file_stem, impact_name, expected_value, expected_unit):
    """Smartphone_1Layer (one foreground process, no sub-components) and
    Smartphone_2Layer (Smartphone directly consumes Display, Circuit Board,
    and Battery, no further sub-components): one base scenario per impact method."""
    _, matrix_folder = _load_scenario(input_file_stem)
    # clear the RAM cache for each test run, this is necessary because LCA._cache
    # is a single process-wide within one single @pytest session. Therefore, if
    # the RAM cache is warm from previous test runs and it should be cleared manually.
    # Otherwise,the LCA run uses the warm RAM cache and produces incorrect results.
    _clear_ram_only()
    # clear the disk cache path for this matrix folder, so that the LCA run
    # will recompute all artifacts from scratch between test runs. This is necessary
    # because LCA._cache is a single process-wide within one single @pytest session.
    get_cache_paths.cache_clear()
    # we clear initial_artifacts from disk unconditionally in the following line
    # even though we clear it at the end of the module, we still need to clear it here for instances
    # where _cleanup_disk_caches_after_module did not work (e.g. if the tests in this module was interrupted
    # before it could run) or if the tests in this module are run in isolation,
    # _cleanup_disk_caches_after_module will not run or for any reason that the artificats left from
    # the past test sessions unintentionally. This is necessary to ensure that after refactoring, we get
    # results from artifacts generated by the refactored code, rather than stale artifacts left over from
    # the old code.
    _clear_disk(matrix_folder)
    # as a result of the above cache clearing, we run pyH2A cold, which will recompute all artifacts from scratch and write them to disk and RAM.
    _run_and_assert(input_file_stem, impact_name, expected_value, expected_unit)    

# ── 3-layer: five component-quantity scenarios per method ───────────────────
#
# Each impact method's three tests below run consecutively (relying on
# file-definition order) and exercise all three LCA caching paths: cold
# disk+RAM on the first scenario, warm disk / cold RAM on the second, and
# warm RAM (no disk I/O) on the three remaining scenarios.

@pytest.mark.parametrize(
    'scenario_index, scenario_id',
    [(0, 'base'), (1, 'S2'), (2, 'S3'), (3, 'S4'), (4, 'S5')],
)
def test_3layer_gwp_scenarios(scenario_index, scenario_id):
    """Exercises all three LCA caching paths across the five GWP scenarios, in
    parametrize-list (execution) order: scenario 0 (base) is cold RAM+disk
    (compute_all_artifacts_from_scratch runs the full LU factorization and
    writes artifacts to disk and RAM); scenario 1 (S2) explicitly clears RAM
    while leaving disk warm (load_all_from_disk_to_ram reads the artifacts
    saved above, bypassing factorization); scenarios 2-4 (S3-S5) rely on RAM
    staying warm from the previous scenario (initialize_all_artifacts exits on
    the early-exit guard without any disk I/O)."""
    if scenario_index == 0:
        _clear_ram_only()
        get_cache_paths.cache_clear()
        _, matrix_folder = _load_scenario(_SCENARIOS_3LAYER_GWP[0][0])
        _clear_disk(matrix_folder)
    elif scenario_index == 1:
        _clear_ram_only()

    input_file_stem, impact_name, expected, expected_unit = _SCENARIOS_3LAYER_GWP[scenario_index]
    _run_and_assert(input_file_stem, impact_name, expected, expected_unit)


@pytest.mark.parametrize(
    'scenario_index, scenario_id',
    [(0, 'base'), (1, 'S2'), (2, 'S3'), (3, 'S4'), (4, 'S5')],
)
def test_3layer_ced_scenarios(scenario_index, scenario_id):
    """Exercises all three LCA caching paths across the five CED scenarios, in
    parametrize-list (execution) order: scenario 0 (base) is cold RAM+disk
    (compute_all_artifacts_from_scratch runs the full LU factorization and
    writes artifacts to disk and RAM); scenario 1 (S2) explicitly clears RAM
    while leaving disk warm (load_all_from_disk_to_ram reads the artifacts
    saved above, bypassing factorization); scenarios 2-4 (S3-S5) rely on RAM
    staying warm from the previous scenario (initialize_all_artifacts exits on
    the early-exit guard without any disk I/O)."""
    if scenario_index == 0:
        _clear_ram_only()
        get_cache_paths.cache_clear()
        _, matrix_folder = _load_scenario(_SCENARIOS_3LAYER_CED[0][0])
        _clear_disk(matrix_folder)
    elif scenario_index == 1:
        _clear_ram_only()

    input_file_stem, impact_name, expected, expected_unit = _SCENARIOS_3LAYER_CED[scenario_index]
    _run_and_assert(input_file_stem, impact_name, expected, expected_unit)


@pytest.mark.parametrize(
    'scenario_index, scenario_id',
    [(0, 'base'), (1, 'S2'), (2, 'S3'), (3, 'S4'), (4, 'S5')],
)
def test_3layer_acid_scenarios(scenario_index, scenario_id):
    """Exercises all three LCA caching paths across the five ACID scenarios, in
    parametrize-list (execution) order: scenario 0 (base) is cold RAM+disk
    (compute_all_artifacts_from_scratch runs the full LU factorization and
    writes artifacts to disk and RAM); scenario 1 (S2) explicitly clears RAM
    while leaving disk warm (load_all_from_disk_to_ram reads the artifacts
    saved above, bypassing factorization); scenarios 2-4 (S3-S5) rely on RAM
    staying warm from the previous scenario (initialize_all_artifacts exits on
    the early-exit guard without any disk I/O)."""
    if scenario_index == 0:
        _clear_ram_only()
        get_cache_paths.cache_clear()
        _, matrix_folder = _load_scenario(_SCENARIOS_3LAYER_ACID[0][0])
        _clear_disk(matrix_folder)
    elif scenario_index == 1:
        _clear_ram_only()

    input_file_stem, impact_name, expected, expected_unit = _SCENARIOS_3LAYER_ACID[scenario_index]
    _run_and_assert(input_file_stem, impact_name, expected, expected_unit)


# ── Cleanup: runs once after every test above has finished ─────────────────

@pytest.fixture(scope='module', autouse=True)
def _cleanup_disk_caches_after_module():  # noqa: F841
    """Remove every scenario's on-disk Initial_Artifacts cache once all tests
    in this module have finished, so no leftover cache directories remain."""
    yield
    all_stems = (
        [stem for stem, *_ in _SCENARIOS_1LAYER]
        + [stem for stem, *_ in _SCENARIOS_2LAYER]
        + [_SCENARIOS_3LAYER_GWP[0][0], _SCENARIOS_3LAYER_CED[0][0], _SCENARIOS_3LAYER_ACID[0][0]]
    )
    for stem in all_stems:
        _, matrix_folder = _load_scenario(stem)
        _clear_disk(matrix_folder)
