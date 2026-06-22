"""Ground-truth end-to-end tests for pyH2A.LCA.LCA using the PVE toy model.

Each test drives the LCA calculation engine directly via a DummyDCF with
pre-resolved component values and compares the GWP100 result to a reference
value computed independently from the raw openLCA matrix export.

Matrix folder: src/tests/lca/LCA_Test_PVE_GT
Foreground processes (A-matrix column-0 indices):
  - H2 Production        (index 0)     — A[0,0]     > 0  (diagonal reference flow)
  - PV Electricity       (index 3560)  — A[3560,0]  < 0  (input to H2 process)
  - Electrolyzer Mfg     (index 16413) — A[16413,0] < 0  (input to H2 process)
  - Reverse Osmosis      (index 16415) — A[16415,0] < 0  (input to H2 process)

Sign convention: apply_component_updates enforces
  component_values[i] = sign(A[i,0]) * abs(user_value)
so table inputs are always positive magnitudes; the sign is taken from the matrix.
"""
import shutil
from pathlib import Path
import pytest
from pyH2A.LCA.LCA import LCA
from pyH2A.Utilities.lca_utils import get_cache_paths


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_GT_MATRIX_DIR = str(_HERE / 'LCA_Test_PVE_GT')
_DISK_CACHE_DIR = Path(_GT_MATRIX_DIR) / 'Initial_Artifacts'

# ── UUIDs ──────────────────────────────────────────────────────────────────

_UUID_H2_PRODUCTION            = '66b8a6b0-7b7a-4d2c-95d3-d82951c58a35'
_UUID_PV_ELECTRICITY           = 'bc18dc79-2b51-455d-9fec-decf6b2693de'
_UUID_ELECTROLYZER_MFG         = '4397d5db-7fea-4916-af17-b72fa72fc02a'
_UUID_REVERSE_OSMOSIS          = '1659c3a5-5c6b-4f29-b746-e12119144b7b'

_GWP100_KEY = 'Climate change no LT - Global warming potential (GWP100) no LT'

# ── Ground-truth scenarios ─────────────────────────────────────────────────
# Each entry: (h2_prod, pv_elec_mj, electrolyzer_item, ro_kg, expected_gwp100)
# Expected GWP100 values (kg CO2-Eq per kg H2) are openLCA reference results.

_SCENARIOS = [
    (1.0, 198.0, 1e-6, 9.0,  0.454132),  # base scenario
    (1.0, 150.0, 2e-6, 7.0,  0.34409),   # low PV electricity
    (1.0, 250.0, 5e-7, 12.0, 0.57345),   # high PV electricity
    (1.0, 100.0, 3e-6, 5.0,  0.22945),   # low PV + low RO
    (1.0, 300.0, 1e-7, 15.0, 0.68823),   # high PV + high RO
]

_SCENARIO_IDS = [
    'base',
    'low_pv',
    'high_pv',
    'low_pv_low_ro',
    'high_pv_high_ro',
]


# ── Helpers ────────────────────────────────────────────────────────────────

class DummyDCF:
    def __init__(self, inp):
        self.inp = inp


def _make_dcf(h2, pv, elec, ro):
    """DummyDCF with the four PVE-GT foreground components."""
    return DummyDCF({
        'LCA - PVE GT Components': {
            'H2 Production': {
                'UUID': _UUID_H2_PRODUCTION,
                'Value': h2,
                'Processed': 'Yes',
            },
            'PV Electricity Generation': {
                'UUID': _UUID_PV_ELECTRICITY,
                'Value': pv,
                'Processed': 'Yes',
            },
            'Electrolyzer Manufacturing': {
                'UUID': _UUID_ELECTROLYZER_MFG,
                'Value': elec,
                'Processed': 'Yes',
            },
            'Reverse Osmosis': {
                'UUID': _UUID_REVERSE_OSMOSIS,
                'Value': ro,
                'Processed': 'Yes',
            },
        }
    })


def _clear_ram_only():
    for k in LCA._cache:
        LCA._cache[k] = None


def _clear_caches():
    _clear_ram_only()
    get_cache_paths.cache_clear()
    if _DISK_CACHE_DIR.exists():
        shutil.rmtree(_DISK_CACHE_DIR)


@pytest.fixture(scope='module', autouse=True)
def _manage_lca_caches():  # noqa: F841
    """Start from a clean slate; keep the disk cache after tests for reuse."""
    _clear_caches()
    yield
    _clear_ram_only()


# ── Ground-truth tests ─────────────────────────────────────────────────────

class TestLCAGroundTruth:
    """End-to-end GWP100 comparison against openLCA reference values, validated
    against the independently-computed openLCA ground truth. Also exercises the
    Sherman-Morrison rank-1 update used in place of a full matrix solve.

    The three test methods run in definition order and together exercise all
    three caching paths within a single pytest session:

    - ``test_base_computes_from_scratch``: cold RAM + cold disk (module
      fixture cleared both) → ``compute_all_artifacts_from_scratch`` runs
      the full LU factorization and writes artifacts to disk and RAM. This corresponds
      to the first-ever run of a given matrix export.
    - ``test_warm_disk_path_loads_correctly``: explicitly clears RAM while leaving
      disk warm → ``load_all_from_disk_to_ram`` reads the artifacts saved
      above, bypassing factorization and artifacts initialization. This corresponds
      to a subsequent run of the same scenario after restarting the Python process.
    - ``test_remaining_scenarios_use_ram_cache``: RAM is warm from the
      previous test → ``initialize_all_artifacts`` exits on the early-exit
      guard without any disk I/O. This corresponds to multiple runs of different
      scenarios within the same Python session, e.g. Monte Carlo analysis within one 
      worker or interactive use. 
    """

    def test_base_computes_from_scratch(self):
        h2, pv, elec, ro, expected = _SCENARIOS[0]
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(h2, pv, elec, ro))
        result = lca.lca_results[_GWP100_KEY]['value']
        diff_pct = (result - expected) / expected * 100
        print(f'\n  pyH2A={result:.6f}  openLCA={expected:.6f}  diff={diff_pct:+.4f}%')
        assert result == pytest.approx(expected, rel=1e-3)

    def test_warm_disk_path_loads_correctly(self):
        _clear_ram_only()
        h2, pv, elec, ro, expected = _SCENARIOS[1]
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(h2, pv, elec, ro))
        result = lca.lca_results[_GWP100_KEY]['value']
        diff_pct = (result - expected) / expected * 100
        print(f'\n  pyH2A={result:.6f}  openLCA={expected:.6f}  diff={diff_pct:+.4f}%')
        assert result == pytest.approx(expected, rel=1e-3)

    @pytest.mark.parametrize(
        'h2, pv, elec, ro, expected_gwp100',
        _SCENARIOS[2:],
        ids=_SCENARIO_IDS[2:],
    )
    def test_remaining_scenarios_use_ram_cache(self, h2, pv, elec, ro, expected_gwp100):
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(h2, pv, elec, ro))
        result = lca.lca_results[_GWP100_KEY]['value']
        diff_pct = (result - expected_gwp100) / expected_gwp100 * 100
        print(f'\n  pyH2A={result:.6f}  openLCA={expected_gwp100:.6f}  diff={diff_pct:+.4f}%')
        assert result == pytest.approx(expected_gwp100, rel=1e-3)

    def test_gwp100_result_has_correct_unit(self):
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(*_SCENARIOS[0][:4]))
        assert lca.lca_results[_GWP100_KEY]['unit'] == 'kg CO2-Eq'

