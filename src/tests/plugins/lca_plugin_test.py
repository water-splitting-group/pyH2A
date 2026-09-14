import shutil
from pathlib import Path

import numpy as np
import pytest
from pyH2A.Plugins.LCA_Plugin import LCA_Plugin
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
    """DCF object for LCA with configurable PVE-GT foreground component values.

    The product itself is not a component row: it is named by ``UUID of product``
    and its amount is the total output at gate that ``Production_Plugin`` would
    have computed in a full workflow run.
    """

    def __init__(self, total_output, pv_electricity, electrolyzer, reverse_osmosis,
                 functional_unit = 'kg[H2]', total_output_unit = 'kg[H2]'):
        self.functional_unit = resolve_functional_unit(functional_unit)
        self.inp = {
            'Technical Operating Parameters and Specifications': {
                'Total output at gate': {
                    'Value': total_output,
                    'Unit': total_output_unit,
                },
            },
            'Life Cycle Assessment': {
                'Matrix Folder': {
                    'Value': _MATRIX_FOLDER,
                },
                'UUID of product': {
                    'Value': _UUID_H2_PRODUCTION,
                },
            },
            'LCA - PVE GT Components': {
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
                "total_output": 1.0,
                "pv_electricity": 198.0,
                "electrolyzer": 1e-6,
                "reverse_osmosis": 9.0,
            },
            "expected": {
                "gwp100_value": 0.4541318146171765,
                "gwp100_unit": "kg[$CO_{2}$-Eq] / kg[H2]",
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

    assert quantity.supplied_value == pytest.approx(expected["gwp100_value"], rel=1e-8)

    # The impact unit of index_C.csv ('kg CO2-Eq') as translated by Config/OpenLCA_config.py,
    # over the declared Functional Unit.
    assert quantity.supplied_unit_reference == expected["gwp100_unit"]


def test_total_output_at_gate_sets_the_reference_flow_amount():
    """Impacts are reported per unit of product, so twice the output halves them."""

    components = {'pv_electricity': 198.0, 'electrolyzer': 1e-6, 'reverse_osmosis': 9.0}

    single = LCA_Plugin(DummyDCF(total_output=1.0, **components), print_info=False)
    double = LCA_Plugin(DummyDCF(total_output=2.0, **components), print_info=False)

    assert (double.lca_results[_GWP100_KEY].supplied_value
            == pytest.approx(single.lca_results[_GWP100_KEY].supplied_value / 2, rel=1e-8))


def test_functional_unit_is_converted_into_the_exports_reference_flow_unit():
    """A Functional Unit in another unit of the same dimension is converted, not rejected.

    The export's reference flow is in kg, so one tonne of product is the same
    scenario as 1000 kg, with the results restated per tonne."""

    components = {'pv_electricity': 198.0, 'electrolyzer': 1e-6, 'reverse_osmosis': 9.0}

    in_kg = LCA_Plugin(DummyDCF(total_output=1000.0, **components), print_info=False)
    in_ton = LCA_Plugin(DummyDCF(total_output=1.0, functional_unit='ton[H2]',
                                 total_output_unit='ton[H2]', **components), print_info=False)

    per_ton = in_ton.lca_results[_GWP100_KEY]
    assert per_ton.supplied_value == pytest.approx(in_kg.lca_results[_GWP100_KEY].supplied_value * 1000,
                                                   rel=1e-8)
    assert per_ton.supplied_unit_reference == 'kg[$CO_{2}$-Eq] / ton[H2]'


def test_functional_unit_of_another_dimension_is_rejected():
    """A Functional Unit whose dimension the reference flow cannot be expressed in
    would report cost and LCA results on two different physical bases."""

    with pytest.raises(ValueError, match='Dimension mismatch'):
        LCA_Plugin(DummyDCF(total_output=1.0, pv_electricity=198.0, electrolyzer=1e-6,
                            reverse_osmosis=9.0, functional_unit='kWh[H2]',
                            total_output_unit='kWh[H2]'), print_info=False)


def test_functional_unit_without_a_reference_is_rejected():
    """Results are reported per unit of a named product, so the label is required."""

    dcf = DummyDCF(total_output=1.0, pv_electricity=198.0, electrolyzer=1e-6,
                   reverse_osmosis=9.0, functional_unit='kg', total_output_unit='kg')
    with pytest.raises(ValueError, match='carries no reference'):
        LCA_Plugin(dcf, print_info=False)


# ── Cache invalidation ─────────────────────────────────────────────────────
#
# Neither test below clears any cache: that is exactly what is under test. The
# caches are keyed by (matrix folder, export fingerprint), so both switching
# folder and replacing an export in place must invalidate them on their own.

_TOY_MATRIX_FOLDERS = _HERE.parent / 'e2e_lca' / 'data' / 'matrix_folders'
_UUID_SMARTPHONE = '72d897ed-5c61-44d0-9ee0-f057dc981e58'


class SmartphoneDCF:
    """DCF for the 1-layer toy models, whose only process is the product itself."""

    def __init__(self, matrix_folder):
        self.functional_unit = resolve_functional_unit('kg[smartphones]')
        self.inp = {
            'Technical Operating Parameters and Specifications': {
                'Total output at gate': {'Value': 1.0, 'Unit': 'kg[smartphones]'},
            },
            'Life Cycle Assessment': {
                'Matrix Folder': {'Value': str(matrix_folder)},
                'UUID of product': {'Value': _UUID_SMARTPHONE},
            },
        }


def _impacts(matrix_folder):
    results = LCA_Plugin(SmartphoneDCF(matrix_folder), print_info=False).lca_results
    return {name: (quantity.supplied_value, quantity.supplied_unit_reference)
            for name, quantity in results.items()}


def test_second_matrix_folder_is_not_served_from_the_first_folders_cache():
    """Two matrix folders in one process must each return their own results."""

    gwp_folder = _TOY_MATRIX_FOLDERS / 'smartphone_1layer_gwp_base'
    ced_folder = _TOY_MATRIX_FOLDERS / 'smartphone_1layer_ced_base'
    shutil.rmtree(gwp_folder / 'Initial_Artifacts', ignore_errors=True)
    shutil.rmtree(ced_folder / 'Initial_Artifacts', ignore_errors=True)

    try:
        assert _impacts(gwp_folder) == {
            'Global warming potential': (pytest.approx(10.0), 'kg[$CO_{2}$-Eq] / kg[smartphones]')}
        assert _impacts(ced_folder) == {
            'Cumulative energy demand': (pytest.approx(50.0), 'kWh / kg[smartphones]')}
    finally:
        shutil.rmtree(gwp_folder / 'Initial_Artifacts', ignore_errors=True)
        shutil.rmtree(ced_folder / 'Initial_Artifacts', ignore_errors=True)


def test_scaling_vector_solves_the_scenario_technosphere_system():
    """The on-demand scaling vector must still satisfy A x = f for the scenario."""

    dcf = DummyDCF(total_output=1.0, pv_electricity=198.0,
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
    assert _impacts(work) == {
        'Global warming potential': (pytest.approx(10.0), 'kg[$CO_{2}$-Eq] / kg[smartphones]')}

    # The user re-exports a different model from openLCA into the same folder.
    # shutil.copy (not copy2) leaves the new files with a current modification time.
    for source in (_TOY_MATRIX_FOLDERS / 'smartphone_1layer_ced_base').iterdir():
        if source.is_file():
            shutil.copy(source, work / source.name)

    assert _impacts(work) == {
        'Cumulative energy demand': (pytest.approx(50.0), 'kWh / kg[smartphones]')}


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


def test_negative_component_value_is_rejected():
    dcf = DummyDCF(total_output=1.0, pv_electricity=198.0,
                   electrolyzer=1e-6, reverse_osmosis=-9.0)
    with pytest.raises(ValueError, match='Negative value for LCA component'):
        LCA_Plugin(dcf, print_info=False)


def test_component_missing_from_the_input_tables_is_rejected():
    """Every nonzero entry of the technosphere column needs a scenario value."""

    dcf = DummyDCF(total_output=1.0, pv_electricity=198.0,
                   electrolyzer=1e-6, reverse_osmosis=9.0)
    del dcf.inp['LCA - PVE GT Components']['Reverse Osmosis']
    with pytest.raises(ValueError, match='Mismatch between A0 column UUIDs'):
        LCA_Plugin(dcf, print_info=False)


def test_component_absent_from_the_technosphere_column_is_rejected():
    """A row whose UUID is not in the technosphere column is just as wrong as a missing one."""

    dcf = DummyDCF(total_output=1.0, pv_electricity=198.0,
                   electrolyzer=1e-6, reverse_osmosis=9.0)
    dcf.inp['LCA - PVE GT Components']['Not In The Export'] = {
        'UUID': 'ffffffff-ffff-ffff-ffff-ffffffffffff', 'Value': 1.0, 'Unit': 'kg'}
    with pytest.raises(ValueError, match='Mismatch between A0 column UUIDs'):
        LCA_Plugin(dcf, print_info=False)


def test_impact_unit_that_is_not_a_known_unit_is_named(tmp_path):
    """openLCA impact units that are neither a pyH2A unit nor mapped in
    Config/OpenLCA_config.py have to surface, naming the offending unit."""

    work = _toy_export(tmp_path)
    _rewrite_csv(work / 'index_C.csv', lambda rows: rows[0].__setitem__(3, 'kg 1,4-DCB'))
    with pytest.raises(ValueError, match=r"1,4-DCB"):
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
                "total_output": 1.0,
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
