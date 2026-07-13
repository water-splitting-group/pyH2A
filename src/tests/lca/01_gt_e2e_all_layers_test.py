"""Combined ground-truth end-to-end tests for pyH2A.LCA.LCA across the
Smartphone_1Layer, Smartphone_2Layer, and Smartphone_3Layer toy models.

Model summary
-------------
- 1-layer: single foreground process (Smartphone itself, no sub-components).
  One base scenario per impact method (GWP, CED, ACIDIFICATION).
- 2-layer: Smartphone directly consumes Display, Circuit Board, and Battery
  (no further sub-components). One base scenario per impact method (GWP, CED, ACIDIFICATION).
- 3-layer: Smartphone consumes Circuit Board/Display/Battery, each of which
  in turn consumes two raw-material sub-components. Five component-quantity
  scenarios (base, S2-S5) per impact method (GWP, CED, ACIDIFICATION).

All three models share the same expected base-case totals (GWP=10.0 kg CO2-eq,
CED=50.0 kWh, ACID=4.0 kg SO2-eq), since each is a progressively finer-grained
breakdown of the same underlying bill of materials and elementary flows.

Caching note
------------
LCA._cache is a single process-wide cache, not keyed by matrix folder, so
running more than one matrix folder within the same process requires
manually clearing both the RAM cache and that folder's on-disk
Initial_Artifacts cache before switching folders (otherwise a later folder
would silently reuse an earlier folder's cached artifacts, producing incorrect
results).:

- The 1-layer and 2-layer sections have one scenario per method, so each call
  simply clears both caches before running (``_run_lca_cold``).
- The 3-layer section deliberately exercises all three caching paths (cold
  disk+RAM, warm disk, warm RAM) within each impact method's group of five
  scenarios, so each method's test class clears both disk and RAM caches once 
  at class setup (not per call) via a class-scoped autouse fixture, matching
  the original standalone scripts' behavior.
"""

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from pyH2A.LCA.LCA import LCA
from pyH2A.LCA.config import CONFIG
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


def _run_lca(input_file_stem):
    """Load a scenario input file and run the LCA engine against it, as-is
    (no cache management -- caller is responsible for cache state)."""
    inp, matrix_folder = _load_scenario(input_file_stem)
    return LCA(matrix_folder, SimpleNamespace(inp=inp))


def _run_lca_cold(input_file_stem):
    """Load a scenario input file and run the LCA engine, first clearing both
    the RAM cache and the target folder's on-disk cache."""
    inp, matrix_folder = _load_scenario(input_file_stem)
    _clear_ram_only()
    get_cache_paths.cache_clear()
    _clear_disk(matrix_folder)
    return LCA(matrix_folder, SimpleNamespace(inp=inp))


def _assert_matches(lca, impact_name, expected_value, expected_impact_unit):
    """``expected_impact_unit`` is the raw openLCA unit string (e.g. 'kg CO2-eq'),
    used as a CONFIG lookup key to check the resolved unit stored on the result
    Quantity, expressed as ``<impact unit> / <functional unit>``."""
    quantity = lca.lca_results[impact_name]
    result = quantity.supplied_value
    diff_pct = (result - expected_value) / expected_value * 100
    print(f'\n  pyH2A={result:.6f}  reference={expected_value:.6f}  diff={diff_pct:+.4f}%')
    assert result == pytest.approx(expected_value, rel=1e-3)
    expected = CONFIG[expected_impact_unit]
    functional_unit_unit = str(LCA._cache['A0_column'][2][0])
    assert quantity.supplied_unit == f"{expected['unit']} / {functional_unit_unit}"


# ── 1-layer: single scenario per method ─────────────────────────────────────

class TestLCAGroundTruth1Layer:
    """Smartphone_1Layer: one foreground process, no sub-components."""

    _SCENARIOS = [
        ('Smartphone_1Layer_GWP', 'Global warming potential', 10.0, 'kg CO2-eq'),
        ('Smartphone_1Layer_CED', 'Cumulative energy demand', 50.0, 'kWh'),
        ('Smartphone_1Layer_ACID', 'Acidification', 4.0, 'kg SO2-eq'),
    ]

    @pytest.fixture(scope='class', autouse=True)
    def _cleanup_disk_caches(self):  # noqa: F841
        yield
        for input_file_stem, *_ in self._SCENARIOS:
            _, matrix_folder = _load_scenario(input_file_stem)
            _clear_disk(matrix_folder)

    @pytest.mark.parametrize(
        'input_file_stem, impact_name, expected_value, expected_unit',
        _SCENARIOS,
        ids=['GWP', 'CED', 'ACID'],
    )
    def test_result_matches_reference(self, input_file_stem, impact_name, expected_value, expected_unit):
        lca = _run_lca_cold(input_file_stem)
        _assert_matches(lca, impact_name, expected_value, expected_unit)


# ── 2-layer: single scenario per method ─────────────────────────────────────

class TestLCAGroundTruth2Layer:
    """Smartphone_2Layer: Smartphone directly consumes Display, Circuit Board,
    and Battery (no further sub-components)."""

    _SCENARIOS = [
        ('Smartphone_2Layer_GWP', 'Global warming potential', 10.0, 'kg CO2-eq'),
        ('Smartphone_2Layer_CED', 'Cumulative energy demand', 50.0, 'kWh'),
        ('Smartphone_2Layer_ACID', 'Acidification', 4.0, 'kg SO2-eq'),
    ]

    @pytest.fixture(scope='class', autouse=True)
    def _cleanup_disk_caches(self):  # noqa: F841
        yield
        for input_file_stem, *_ in self._SCENARIOS:
            _, matrix_folder = _load_scenario(input_file_stem)
            _clear_disk(matrix_folder)

    @pytest.mark.parametrize(
        'input_file_stem, impact_name, expected_value, expected_unit',
        _SCENARIOS,
        ids=['GWP', 'CED', 'ACID'],
    )
    def test_result_matches_reference(self, input_file_stem, impact_name, expected_value, expected_unit):
        lca = _run_lca_cold(input_file_stem)
        _assert_matches(lca, impact_name, expected_value, expected_unit)


# ── 3-layer: five component-quantity scenarios per method ───────────────────
#
# Each method's test class exercises all three LCA caching paths across its
# five scenarios (base, S2-S5): cold disk+RAM on the first scenario, warm
# disk / cold RAM on the second, and warm RAM (no disk I/O) on the rest.
# A class-scoped autouse fixture clears caches once before each class's own
# scenarios run, so the three method classes below don't interfere with each
# other (or with the 1-layer/2-layer tests above) regardless of run order.

class _ThreeLayerCachePathBase:
    """Shared scaffolding for one impact method's five 3-layer scenarios.

    Subclasses set IMPACT_NAME, UNIT, and SCENARIOS (a list of
    (input_file_stem, expected_value) tuples in base, S2, S3, S4, S5 order).
    """

    IMPACT_NAME: str
    UNIT: str
    SCENARIOS: list

    @pytest.fixture(scope='class', autouse=True)
    def _manage_lca_caches(self):
        _clear_ram_only()
        get_cache_paths.cache_clear()
        _, matrix_folder = _load_scenario(self.SCENARIOS[0][0])
        _clear_disk(matrix_folder)
        yield
        _clear_ram_only()
        _clear_disk(matrix_folder)

    def test_base_computes_from_scratch(self):
        """Cold RAM + cold disk -> compute_all_artifacts_from_scratch runs the
        full LU factorization and writes artifacts to disk and RAM."""
        input_file_stem, expected = self.SCENARIOS[0]
        lca = _run_lca(input_file_stem)
        _assert_matches(lca, self.IMPACT_NAME, expected, self.UNIT)

    def test_warm_disk_path_loads_correctly(self):
        """Explicitly clear RAM while leaving disk warm -> load_all_from_disk_to_ram
        reads the artifacts saved above, bypassing factorization."""
        _clear_ram_only()
        input_file_stem, expected = self.SCENARIOS[1]
        lca = _run_lca(input_file_stem)
        _assert_matches(lca, self.IMPACT_NAME, expected, self.UNIT)

    @pytest.mark.parametrize('scenario_index, scenario_id', [(2, 'S3'), (3, 'S4'), (4, 'S5')])
    def test_remaining_scenarios_use_ram_cache(self, scenario_index, scenario_id):
        """RAM is warm from the previous test -> initialize_all_artifacts exits
        on the early-exit guard without any disk I/O."""
        input_file_stem, expected = self.SCENARIOS[scenario_index]
        lca = _run_lca(input_file_stem)
        _assert_matches(lca, self.IMPACT_NAME, expected, self.UNIT)


class TestLCAGroundTruth3LayerGWP(_ThreeLayerCachePathBase):
    IMPACT_NAME = 'Global warming potential'
    UNIT = 'kg CO2-eq'
    SCENARIOS = [
        ('Smartphone_3Layer_GWP', 10.0),
        ('Smartphone_3Layer_S2_GWP', 8.0),
        ('Smartphone_3Layer_S3_GWP', 12.0),
        ('Smartphone_3Layer_S4_GWP', 11.2),
        ('Smartphone_3Layer_S5_GWP', 9.2),
    ]


class TestLCAGroundTruth3LayerCED(_ThreeLayerCachePathBase):
    IMPACT_NAME = 'Cumulative energy demand'
    UNIT = 'kWh'
    SCENARIOS = [
        ('Smartphone_3Layer_CED', 50.0),
        ('Smartphone_3Layer_S2_CED', 39.5),
        ('Smartphone_3Layer_S3_CED', 60.5),
        ('Smartphone_3Layer_S4_CED', 54.4),
        ('Smartphone_3Layer_S5_CED', 47.4),
    ]


class TestLCAGroundTruth3LayerACID(_ThreeLayerCachePathBase):
    IMPACT_NAME = 'Acidification'
    UNIT = 'kg SO2-eq'
    SCENARIOS = [
        ('Smartphone_3Layer_ACID', 4.0),
        ('Smartphone_3Layer_S2_ACID', 3.2),
        ('Smartphone_3Layer_S3_ACID', 4.8),
        ('Smartphone_3Layer_S4_ACID', 4.66),
        ('Smartphone_3Layer_S5_ACID', 3.46),
    ]
