import shutil
from pathlib import Path

import numpy as np
import pytest
from pyH2A.Plugins.LCA_Plugin import LCA_Plugin
from pyH2A.Config.OpenLCA_config import OPEN_LCA_CONFIG
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from pyH2A.Utilities.lca_utilities import find_matrix_path, matrix_of


# ── Paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_MATRIX_FOLDER = str(_HERE / 'lca_data' / 'matrix_folders' / 'pve_unit_test')
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
                },
                'PV Electricity Generation': {
                    'UUID': _UUID_PV_ELECTRICITY,
                    'Value': pv_electricity,
                    'Unit': 'MJ',
                },
                'Electrolyzer Manufacturing': {
                    'UUID': _UUID_ELECTROLYZER_MFG,
                    'Value': electrolyzer,
                    'Unit': 'item',
                },
                'Reverse Osmosis': {
                    'UUID': _UUID_REVERSE_OSMOSIS,
                    'Value': reverse_osmosis,
                    'Unit': 'kg',
                },
            }
        }


def _clear_caches():
    """Remove this folder's on-disk cache so each test starts from a cold build.

    The RAM cache needs no clearing: it is keyed by (matrix folder, export
    fingerprint), so it invalidates itself when either changes."""
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
    lca = LCA_Plugin(dcf, print_info=False)
    quantity = lca.lca_results[_GWP100_KEY]
    expected = case["expected"]

    # Tolerance
    tolerance = 1e-8

    assert quantity.supplied_value == pytest.approx(expected["gwp100_value"], rel=1e-8)

    expected_unit = OPEN_LCA_CONFIG[expected["gwp100_unit"]]
    functional_unit_unit = str(LCA_Plugin._cache['A0_column'][2][0])
    assert quantity.supplied_unit == f"{expected_unit['unit']} / {functional_unit_unit}"


# ── Cache invalidation ─────────────────────────────────────────────────────
#
# Neither test below clears any cache: that is exactly what is under test. The
# caches are keyed by (matrix folder, export fingerprint), so both switching
# folder and replacing an export in place must invalidate them on their own.

_TOY_MATRIX_FOLDERS = _HERE.parent / 'e2e_lca' / 'data' / 'matrix_folders'
_UUID_SMARTPHONE = '72d897ed-5c61-44d0-9ee0-f057dc981e58'


class SmartphoneDCF:
    """Single-component DCF for the 1-layer toy models."""

    def __init__(self, matrix_folder):
        self.functional_unit = resolve_functional_unit('kg')
        self.inp = {
            'Life Cycle Assessment': {'Matrix Folder': {'Value': str(matrix_folder)}},
            'LCA - Smartphone': {
                'Smartphone': {'UUID': _UUID_SMARTPHONE, 'Value': 1.0, 'Unit': 'kg'},
            },
        }


def _impacts(matrix_folder):
    results = LCA_Plugin(SmartphoneDCF(matrix_folder), print_info=False).lca_results
    return {name: (quantity.supplied_value, quantity.supplied_unit) for name, quantity in results.items()}


def test_second_matrix_folder_is_not_served_from_the_first_folders_cache():
    """Two matrix folders in one process must each return their own results."""

    gwp_folder = _TOY_MATRIX_FOLDERS / 'smartphone_1layer_gwp_base'
    ced_folder = _TOY_MATRIX_FOLDERS / 'smartphone_1layer_ced_base'
    shutil.rmtree(gwp_folder / 'Initial_Artifacts', ignore_errors=True)
    shutil.rmtree(ced_folder / 'Initial_Artifacts', ignore_errors=True)

    try:
        assert _impacts(gwp_folder) == {'Global warming potential': (pytest.approx(10.0), 'kg / kg')}
        assert _impacts(ced_folder) == {'Cumulative energy demand': (pytest.approx(50.0), 'kWh / kg')}
    finally:
        shutil.rmtree(gwp_folder / 'Initial_Artifacts', ignore_errors=True)
        shutil.rmtree(ced_folder / 'Initial_Artifacts', ignore_errors=True)


def test_scaling_vector_solves_the_scenario_technosphere_system():
    """The on-demand scaling vector must still satisfy A x = f for the scenario."""

    dcf = DummyDCF(h2_production=1.0, pv_electricity=198.0,
                   electrolyzer=1e-6, reverse_osmosis=9.0)
    lca = LCA_Plugin(dcf, print_info=False)

    matrix_a = matrix_of(find_matrix_path(_MATRIX_FOLDER, 'A'))
    # Rebuild the scenario's first technosphere column from the resolved component values.
    scenario_a = matrix_a.tolil()
    for index, value in zip(_nonzero_column_0_indices(matrix_a), lca.component_values):
        scenario_a[index, 0] = value

    demand = np.zeros(matrix_a.shape[0])
    demand[0] = 1.0
    np.testing.assert_allclose(scenario_a.tocsc() @ lca.scaling_vector, demand, atol=1e-10)


def _nonzero_column_0_indices(matrix_a):
    column_0 = np.asarray(matrix_a[:, 0].todense()).reshape(-1)
    return np.flatnonzero(column_0)


def test_replacing_the_export_invalidates_the_cache(tmp_path):
    """Re-exporting a different model into a folder must not reuse its cached artifacts."""

    work = tmp_path / 'export'
    shutil.copytree(_TOY_MATRIX_FOLDERS / 'smartphone_1layer_gwp_base', work)
    assert _impacts(work) == {'Global warming potential': (pytest.approx(10.0), 'kg / kg')}

    # The user re-exports a different model from openLCA into the same folder.
    # shutil.copy (not copy2) leaves the new files with a current modification time.
    for source in (_TOY_MATRIX_FOLDERS / 'smartphone_1layer_ced_base').iterdir():
        if source.is_file():
            shutil.copy(source, work / source.name)

    assert _impacts(work) == {'Cumulative energy demand': (pytest.approx(50.0), 'kWh / kg')}


# ── Inputs and exports that must be rejected ───────────────────────────────

def _toy_export(tmp_path):
    work = tmp_path / 'export'
    shutil.copytree(_TOY_MATRIX_FOLDERS / 'smartphone_1layer_gwp_base', work)
    return work


def _rewrite_csv(path, mutate):
    import csv
    with open(path, encoding='utf-8') as stream:
        reader = csv.reader(stream)
        header, rows = next(reader), list(reader)
    mutate(rows)
    with open(path, 'w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def test_negative_component_value_is_rejected(tmp_path):
    dcf = SmartphoneDCF(_toy_export(tmp_path))
    dcf.inp['LCA - Smartphone']['Smartphone']['Value'] = -1.0
    with pytest.raises(ValueError, match='Negative value for LCA component'):
        LCA_Plugin(dcf, print_info=False)


def test_functional_unit_must_match_the_exports_reference_flow_unit(tmp_path):
    dcf = SmartphoneDCF(_toy_export(tmp_path))
    dcf.functional_unit = resolve_functional_unit('ton')   # export's reference flow is in kg
    with pytest.raises(ValueError, match='Functional Unit mismatch'):
        LCA_Plugin(dcf, print_info=False)


def test_impact_unit_absent_from_config_is_named(tmp_path):
    work = _toy_export(tmp_path)
    _rewrite_csv(work / 'index_C.csv', lambda rows: rows[0].__setitem__(3, 'kg 1,4-DCB'))
    with pytest.raises(KeyError, match=r"kg 1,4-DCB"):
        LCA_Plugin(SmartphoneDCF(work), print_info=False)


def test_duplicate_provider_id_is_rejected(tmp_path):
    work = _toy_export(tmp_path)
    _rewrite_csv(work / 'index_A.csv',
                 lambda rows: rows.append(['1', rows[0][1], '', '', '', '', '', '', 'kg', 'product']))
    with pytest.raises(ValueError, match='duplicate provider IDs'):
        LCA_Plugin(SmartphoneDCF(work), print_info=False)


if __name__ == '__main__':

    from timeit import default_timer as timer

    inputs = {
                "h2_production": 1.0,
                "pv_electricity": 198.0,
                "electrolyzer": 1e-6,
                "reverse_osmosis": 9.0,
    }

    dcf = DummyDCF(**inputs)

    # Run LCA

    start = timer()

    for _ in range(100000):
        lca = LCA_Plugin(dcf, print_info=False)
        quantity = lca.lca_results[_GWP100_KEY]

    end = timer()

    print("Time passed:", end - start)

