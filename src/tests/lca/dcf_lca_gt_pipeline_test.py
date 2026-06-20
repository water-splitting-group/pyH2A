"""End-to-end tests for Discounted_Cash_Flow with LCA enabled.

Each test runs Discounted_Cash_Flow with a dedicated input file whose LCA
component values are baked in — no programmatic value modification.  Results
are verified against openLCA ground truth (GT) values exported from the same
toy-model matrix, confirming that pyH2A's Sherman-Morrison engine reproduces
openLCA's impact scores to within 1%.

Input files:  src/tests/lca/input_files/PVE_GT_S{1..5}.md
Matrix:       src/tests/lca/LCA_Test_PVE_GT
"""
import shutil
from pathlib import Path
import numpy as np
import pytest

# pyH2A.LCA.LCA imports pyH2A.Discounted_Cash_Flow, which in turn re-imports
# pyH2A.LCA.LCA.  Importing Discounted_Cash_Flow first resolves the circular
# dependency so that the LCA name is already bound when the second import runs.
import pyH2A.Discounted_Cash_Flow  # noqa: F401  (import for side-effect only)
from pyH2A.LCA.LCA import LCA
from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.lca_utils import get_cache_paths


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_E2E_DIR = _HERE / 'input_files'
_DISK_CACHE_DIR = _HERE / 'LCA_Test_PVE_GT' / 'Initial_Artifacts'

_GWP100_KEY = 'Climate change no LT - Global warming potential (GWP100) no LT'

# ── Scenarios ──────────────────────────────────────────────────────────────
# Each entry: (scenario_id, md_file, openlca_gwp100)
# openLCA GT values are ground truth from the exported toy-model matrix.

_SCENARIOS = [
    ('S1_base',       'PVE_GT_S1.md', 0.454132),
    ('S2_low_pv',     'PVE_GT_S2.md', 0.34409),
    ('S3_high_pv',    'PVE_GT_S3.md', 0.57345),
    ('S4_low_pv_ro',  'PVE_GT_S4.md', 0.22945),
    ('S5_high_pv_ro', 'PVE_GT_S5.md', 0.68823),
]


# ── Cache management ───────────────────────────────────────────────────────

def _clear_all_caches():
    for k in LCA._cache:
        LCA._cache[k] = None
    get_cache_paths.cache_clear()
    if _DISK_CACHE_DIR.exists():
        shutil.rmtree(_DISK_CACHE_DIR)


@pytest.fixture(scope='module', autouse=True)
def _manage_lca_caches():
    """Clear all caches before and after this module's tests."""
    _clear_all_caches()
    yield
    _clear_all_caches()


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    'scenario_id, md_file, openlca_gwp100',
    _SCENARIOS,
    ids=[s[0] for s in _SCENARIOS],
)
def test_dcf_lca_gwp100(scenario_id, md_file, openlca_gwp100):
    input_file = str(_E2E_DIR / md_file)
    dcf = Discounted_Cash_Flow(input_file, print_info=False, check_processing=False)
    gwp100 = dcf.lca.lca_results[_GWP100_KEY]['value']
    diff_pct = (gwp100 - openlca_gwp100) / openlca_gwp100 * 100
    print(
        f'\n  [{scenario_id}]'
        f'  pyH2A={gwp100:.6f}'
        f'  openLCA={openlca_gwp100:.6f}'
        f'  diff={diff_pct:+.4f}%'
    )
    assert np.isfinite(gwp100) and gwp100 > 0
    assert gwp100 == pytest.approx(openlca_gwp100, rel=1e-2)
