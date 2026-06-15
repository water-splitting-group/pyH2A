"""Full MC LCA pipeline tests using per-scenario .md files.

Each test runs Discounted_Cash_Flow with a dedicated input file whose LCA
component values are baked in — no programmatic value modification.  This
mirrors what an individual MC worker does (read file → DCF → LCA result)
while keeping the scenario inputs fully explicit and auditable.

Input files:  src/tests/lca/input_files/PVE_GT_S{1..5}.md
Matrix:       data/LCA/LCA_Test_PVE_GT
"""
from pathlib import Path

import numpy as np
import pytest

# pyH2A.LCA.LCA imports pyH2A.Discounted_Cash_Flow, which in turn re-imports
# pyH2A.LCA.LCA.  Importing Discounted_Cash_Flow first resolves the circular
# dependency so that the LCA name is already bound when the second import runs.
import pyH2A.Discounted_Cash_Flow  # noqa: F401  (import for side-effect only)
from pyH2A.LCA.LCA import LCA
from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parents[2]
_E2E_DIR = _PROJECT_ROOT / 'src' / 'tests' / 'lca' / 'input_files'

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

@pytest.fixture(scope='module', autouse=True)
def _manage_lca_caches():
    """Clear LCA caches at module boundaries; let the cache warm within."""
    LCA._base_solver_cache.clear()
    LCA._component_basis_cache.clear()
    LCA.load_matrices_from_folder.cache_clear()
    yield
    LCA._base_solver_cache.clear()
    LCA._component_basis_cache.clear()
    LCA.load_matrices_from_folder.cache_clear()


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    'scenario_id, md_file, openlca_gwp100',
    _SCENARIOS,
    ids=[s[0] for s in _SCENARIOS],
)
def test_mc_lca_pipeline_gwp100(scenario_id, md_file, openlca_gwp100):
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
