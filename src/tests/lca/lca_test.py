import shutil
from pathlib import Path

import pytest
from pyH2A.Plugins.Life_Cycle_Assessment_Plugin import Life_Cycle_Assessment_Plugin
from pyH2A.Plugins.Life_Cycle_Assessment_Plugin.config import CONFIG
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from pyH2A.Utilities.lca_utils import get_cache_paths


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_MATRIX_FOLDER = str(_HERE / 'data' / 'matrix_folders' / 'pve_unit_test')
_DISK_CACHE_DIR = Path(_MATRIX_FOLDER) / 'Initial_Artifacts'

# ── UUIDs ──────────────────────────────────────────────────────────────────

_UUID_H2_PRODUCTION    = '66b8a6b0-7b7a-4d2c-95d3-d82951c58a35'
_UUID_PV_ELECTRICITY   = 'bc18dc79-2b51-455d-9fec-decf6b2693de'
_UUID_ELECTROLYZER_MFG = '4397d5db-7fea-4916-af17-b72fa72fc02a'
_UUID_REVERSE_OSMOSIS  = '1659c3a5-5c6b-4f29-b746-e12119144b7b'

_GWP100_KEY = 'Climate change no LT - Global warming potential (GWP100) no LT'


class DummyDCF:
    """DCF object for LCA with configurable PVE-GT foreground component values."""

    def __init__(self, h2_production, pv_electricity, electrolyzer, reverse_osmosis):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            'Life Cycle Assessment': {
                'Matrix Folder': {
                    'Value': _MATRIX_FOLDER,
                },
            },
            'LCA - PVE GT Components': {
                'H2 Production': {
                    'UUID': _UUID_H2_PRODUCTION,
                    'Value': h2_production,
                    'Unit': 'kg',
                    'Processed': 'Yes',
                },
                'PV Electricity Generation': {
                    'UUID': _UUID_PV_ELECTRICITY,
                    'Value': pv_electricity,
                    'Unit': 'MJ',
                    'Processed': 'Yes',
                },
                'Electrolyzer Manufacturing': {
                    'UUID': _UUID_ELECTROLYZER_MFG,
                    'Value': electrolyzer,
                    'Unit': 'item',
                    'Processed': 'Yes',
                },
                'Reverse Osmosis': {
                    'UUID': _UUID_REVERSE_OSMOSIS,
                    'Value': reverse_osmosis,
                    'Unit': 'kg',
                    'Processed': 'Yes',
                },
            }
        }


def _clear_caches():
    """Life_Cycle_Assessment_Plugin._cache is a process-wide class attribute, not
    per-instance, so it must be cleared to avoid reusing another test's cached
    matrices."""
    for k in Life_Cycle_Assessment_Plugin._cache:
        Life_Cycle_Assessment_Plugin._cache[k] = None
    get_cache_paths.cache_clear()
    if _DISK_CACHE_DIR.exists():
        shutil.rmtree(_DISK_CACHE_DIR)


@pytest.fixture(autouse=True)
def _reset_lca_caches():
    _clear_caches()
    yield
    _clear_caches()


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "h2_production": 1.0,
                "pv_electricity": 198.0,
                "electrolyzer": 1e-6,
                "reverse_osmosis": 9.0,
            },
            "expected": {
                "gwp100_value": 0.4541318146171765,
                "gwp100_unit": "kg CO2-Eq",
            },
        },
    ],
    ids=[
        "Base case - PVE LCA",
    ],
)
def test_lca(case):
    """Check LCA computes a GWP100 result expected value and the correct composite unit."""

    # Unpack inputs from case
    dcf = DummyDCF(**case["input"])

    # Run LCA
    lca = Life_Cycle_Assessment_Plugin(dcf, print_info=False)
    quantity = lca.lca_results[_GWP100_KEY]
    expected = case["expected"]

    # Tolerance
    tolerance = 1e-8

    assert quantity.supplied_value == pytest.approx(expected["gwp100_value"], rel=1e-8)

    expected_unit = CONFIG[expected["gwp100_unit"]]
    functional_unit_unit = str(Life_Cycle_Assessment_Plugin._cache['A0_column'][2][0])
    assert quantity.supplied_unit == f"{expected_unit['unit']} / {functional_unit_unit}"
