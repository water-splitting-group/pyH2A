"""Ground-truth end-to-end tests for pyH2A.LCA.LCA using the PVE toy model.

Each test drives the LCA calculation engine directly via a MagicMock DCF with
pre-resolved component values and compares the GWP100 result to a reference
value computed independently from the raw openLCA matrix export.

Matrix folder: data/LCA/LCA_Test_PVE_GT
Foreground processes and their A-matrix column-0 sign convention:
  - H2 Production (index 0): positive reference (component_position=0)
  - PV Electricity Generation (index 3560): negative (component_position=1)
  - Electrolyzer Manufacturing (index 16413): negative (component_position=2)
  - Reverse Osmosis (index 16415): negative (component_position=3)
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# pyH2A.LCA.LCA imports pyH2A.Discounted_Cash_Flow, which in turn re-imports
# pyH2A.LCA.LCA.  Importing Discounted_Cash_Flow first resolves the circular
# dependency so that the LCA name is already bound when the second import runs.
import pyH2A.Discounted_Cash_Flow  # noqa: F401  (import for side-effect only)
from pyH2A.LCA.LCA import LCA


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parents[2]
_GT_MATRIX_DIR = str(_PROJECT_ROOT / 'data' / 'LCA' / 'LCA_Test_PVE_GT')

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

def _make_dcf(h2, pv, elec, ro):
    """Minimal DCF mock with four pre-resolved LCA components."""
    dcf = MagicMock()
    dcf.inp = {
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
    }
    return dcf


def _clear_caches():
    """Clear only the in-memory cache. Disk artifacts survive for reuse."""
    for k in LCA._cache:
        LCA._cache[k] = None



@pytest.fixture(autouse=True)
def _reset_lca_caches():  # noqa: F841
    """Isolate every test by clearing only the RAM cache."""
    _clear_caches()
    yield
    _clear_caches()


# ── Ground-truth tests ─────────────────────────────────────────────────────

class TestLCAGroundTruth:
    """End-to-end GWP100 comparison against openLCA reference values.

    Each parametrized case drives the LCA engine with a fixed set of
    foreground component quantities and asserts that the computed GWP100
    matches the independently-derived openLCA ground truth within rel=1e-3.
    """

    @pytest.mark.parametrize(
        'h2, pv, elec, ro, expected_gwp100',
        _SCENARIOS,
        ids=_SCENARIO_IDS,
    )
    def test_gwp100_matches_openlca_ground_truth(self, h2, pv, elec, ro, expected_gwp100):
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(h2, pv, elec, ro))
        result = lca.lca_results[_GWP100_KEY]['value']
        diff_pct = (result - expected_gwp100) / expected_gwp100 * 100
        print(f'\n  pyH2A={result:.6f}  openLCA={expected_gwp100:.6f}  diff={diff_pct:+.4f}%')
        assert result == pytest.approx(expected_gwp100, rel=1e-3)

    @pytest.mark.parametrize(
        'h2, pv, elec, ro, expected_gwp100',
        _SCENARIOS,
        ids=_SCENARIO_IDS,
    )
    def test_gwp100_result_has_correct_unit(self, h2, pv, elec, ro, expected_gwp100):
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(h2, pv, elec, ro))
        unit = lca.lca_results[_GWP100_KEY]['unit']
        assert unit == 'kg CO2-Eq'

    def test_all_scenarios_produce_distinct_gwp100(self):
        results = []
        for h2, pv, elec, ro, _ in _SCENARIOS:
            lca = LCA(_GT_MATRIX_DIR, _make_dcf(h2, pv, elec, ro))
            results.append(lca.lca_results[_GWP100_KEY]['value'])
            _clear_caches()
        assert len(set(round(v, 4) for v in results)) == len(_SCENARIOS)

    def test_higher_pv_electricity_increases_gwp100(self):
        lca_low  = LCA(_GT_MATRIX_DIR, _make_dcf(1.0, 150.0, 1e-6, 9.0))
        gwp_low  = lca_low.lca_results[_GWP100_KEY]['value']
        _clear_caches()
        lca_high = LCA(_GT_MATRIX_DIR, _make_dcf(1.0, 300.0, 1e-6, 9.0))
        gwp_high = lca_high.lca_results[_GWP100_KEY]['value']
        assert gwp_high > gwp_low

    def test_lca_results_dict_contains_gwp100_key(self):
        lca = LCA(_GT_MATRIX_DIR, _make_dcf(1.0, 198.0, 1e-6, 9.0))
        assert _GWP100_KEY in lca.lca_results

    def test_process_local_cache_reused_across_scenarios(self):
        LCA(_GT_MATRIX_DIR, _make_dcf(1.0, 198.0, 1e-6, 9.0))
        assert all(LCA._cache[k] is not None for k in LCA._cache)
        # Second instantiation with a different scenario must reuse the warm cache
        LCA(_GT_MATRIX_DIR, _make_dcf(1.0, 150.0, 2e-6, 7.0))
        assert all(LCA._cache[k] is not None for k in LCA._cache)

