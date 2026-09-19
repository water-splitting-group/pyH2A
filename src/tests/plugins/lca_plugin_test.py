import shutil
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse
from pyH2A.Plugins.LCA_Plugin import LCA_Plugin
from pyH2A.Utilities.functional_unit import resolve_functional_unit
from pyH2A.Utilities.lca_utilities import dense_column, find_matrix_path, matrix_of


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

    def __init__(self, matrix_folder, total_output = 1.0):
        self.functional_unit = resolve_functional_unit('kg[smartphones]')
        self.inp = {
            'Technical Operating Parameters and Specifications': {
                'Total output at gate': {'Value': total_output, 'Unit': 'kg[smartphones]'},
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


@pytest.mark.parametrize('scale', [1.0, 1e4, 2e7, 1e12])
def test_scaling_vector_solves_the_scenario_technosphere_system(scale):
    """The on-demand scaling vector must still satisfy A x = f for the scenario.

    Parametrised over the reference amount because the interesting case is a rescaled
    one: at `scale` = 1 the scenario column equals the export's, so the rank-1 update
    is a no-op and the assertion holds whatever the update does. The reference entry
    x[0] is 1/scale, and computing it as `y[0] - correction[0] * factor` cancels away
    about log10(scale) digits, which the large rewritten column entries then amplify -
    at 2e7 the residual was 1.2e-7, three orders above the tolerance asserted here."""

    dcf = DummyDCF(total_output=scale, pv_electricity=198.0 * scale,
                   electrolyzer=1e-6 * scale, reverse_osmosis=9.0 * scale)
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
    return np.flatnonzero(dense_column(matrix_a, 0))


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


# ── Independence from the size the product system was exported at ──────────
#
# An openLCA product system is drawn at whatever size its author chose - 1 kg of
# product, or 1000. pyH2A rewrites that column with the scenario's own amounts, so
# the exported size must cancel: the same physical system described at k times the
# size has to give the same impact per functional unit. It only does if the
# foreground process's own elementary flows (column 0 of B) are restated along with
# its technosphere exchanges, which `compute_all_artifacts_from_scratch` folds into
# column 0 of `h_basis`.

_UUID_2L = {
    'product':      '0c81c05f-a6ed-4f17-a399-43eb698a3b59',   # Smartphone, kg,      A[0, 0] = +1
    'display':      'a3c98060-7b10-4ba2-abb2-0ea0ddfbd3c2',   # Display, kg,         A[1, 0] = -1
    'circuit':      '47760afd-6a67-454a-98a8-03063250f4aa',   # Circuit Board, Item(s)
    'battery':      '042f97ea-dbbe-4ef4-ab8f-3a2d23084b73',   # Battery, kg
}


class TwoLayerDCF:
    """DCF for the 2-layer toy model, whose three inputs carry 10.0 kg CO2-eq per kg."""

    def __init__(self, matrix_folder, total_output, components = None, product_uuid = None):
        self.functional_unit = resolve_functional_unit('kg[smartphones]')
        amounts = components if components is not None else {}
        self.inp = {
            'Technical Operating Parameters and Specifications': {
                'Total output at gate': {'Value': total_output, 'Unit': 'kg[smartphones]'},
            },
            'Life Cycle Assessment': {
                'Matrix Folder': {'Value': str(matrix_folder)},
                'UUID of product': {'Value': product_uuid or _UUID_2L['product']},
            },
            'LCA - Smartphone Components': {
                'Display':       {'UUID': _UUID_2L['display'],
                                  'Value': amounts.get('display', total_output), 'Unit': 'kg'},
                'Circuit Board': {'UUID': _UUID_2L['circuit'],
                                  'Value': amounts.get('circuit', total_output), 'Unit': 'item'},
                'Battery':       {'UUID': _UUID_2L['battery'],
                                  'Value': amounts.get('battery', total_output), 'Unit': 'kg'},
            },
        }


def _export_copy(tmp_path, name, direct_emission = None):
    """Copy a toy export into tmp_path, optionally giving its foreground process a
    direct elementary flow.

    Row 0 of index_B.csv is carbon dioxide, characterised at 1.0, so `direct_emission`
    is added straight onto the impact per unit of product. Neither bundled export has a
    nonzero B[:, 0] for a *multi-process* system, so the mixed direct/indirect case has
    to be built here; the 1-layer export is the pure-direct case as shipped."""
    work = tmp_path / name
    shutil.copytree(_TOY_MATRIX_FOLDERS / name, work)

    if direct_emission is not None:
        intervention = np.load(work / 'B.npy')
        intervention[0, 0] = direct_emission
        np.save(work / 'B.npy', intervention)

    return work


@pytest.mark.parametrize('total_output', [1.0, 10.0, 1e3, 2e7, 1e12])
def test_direct_foreground_emissions_survive_a_rescaled_reference_amount(tmp_path, total_output):
    """The 1-layer model's whole impact is a direct flow of the foreground process.

    Its export is written at 1 kg of product. Restating the reference amount as a
    plant-lifetime output must not dilute that flow: before column 0 of B was restated
    with column 0 of A, a 20,000 t scenario returned 5e-7 instead of 10.0."""

    work = _export_copy(tmp_path, 'smartphone_1layer_gwp_base')
    lca = LCA_Plugin(SmartphoneDCF(work, total_output = total_output), print_info = False)

    assert lca.lca_results['Global warming potential'].supplied_value == pytest.approx(10.0, rel = 1e-12)


@pytest.mark.parametrize('k', [1.0, 2.0, 10.0, 1e3, 2e7, 1e12])
def test_impacts_are_invariant_to_the_size_the_product_system_was_exported_at(tmp_path, k):
    """Direct and technosphere burdens together: 0.5 direct + 10.0 from the inputs.

    Every k describes the same physical system, written down at k times the size."""

    work = _export_copy(tmp_path, 'smartphone_2layer_gwp_base', direct_emission = 0.5)
    lca = LCA_Plugin(TwoLayerDCF(work, total_output = k), print_info = False)

    assert lca.lca_results['Global warming potential'].supplied_value == pytest.approx(10.5, rel = 1e-12)


def test_rescaled_scenario_matches_a_direct_solve_of_the_scenario_matrices(tmp_path):
    """Cross-check the rank-1 update, and the restatement of B[:, 0], against the
    textbook C B A^-1 f on matrices rebuilt for the scenario from scratch."""

    work = _export_copy(tmp_path, 'smartphone_2layer_gwp_base', direct_emission = 0.5)
    components = {'display': 3.0e6, 'circuit': 5.0e5, 'battery': 2.0e6}
    total_output = 1.0e6

    lca = LCA_Plugin(TwoLayerDCF(work, total_output = total_output, components = components),
                     print_info = False)

    matrix_a = np.asarray(matrix_of(find_matrix_path(str(work), 'A')), dtype = float)
    matrix_b = np.asarray(matrix_of(find_matrix_path(str(work), 'B')), dtype = float)
    matrix_c = matrix_of(find_matrix_path(str(work), 'C'))
    matrix_c = np.asarray(matrix_c.todense() if scipy.sparse.issparse(matrix_c) else matrix_c)

    # The scenario's own matrices: column 0 of A carries the scenario amounts, and column 0
    # of B is restated by the ratio of the scenario's reference amount to the export's.
    scenario_a = matrix_a.copy()
    scenario_a[:, 0] = 0.0
    scenario_a[_nonzero_column_0_indices(matrix_a), 0] = lca.component_values

    scenario_b = matrix_b.copy()
    scenario_b[:, 0] = matrix_b[:, 0] * (total_output / matrix_a[0, 0])

    demand = np.zeros(matrix_a.shape[0])
    demand[0] = 1.0
    expected = matrix_c @ (scenario_b @ np.linalg.solve(scenario_a, demand))

    assert (lca.lca_results['Global warming potential'].supplied_value
            == pytest.approx(expected[0], rel = 1e-12))


# ── Inputs and exports that must be rejected ───────────────────────────────

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


def test_product_uuid_that_is_not_the_reference_flow_is_rejected(tmp_path):
    """Declaring an input as the product leaves the UUID sets matching and the units
    converting, so nothing else catches it - but the demand vector, the rank-1 update
    and the product flow unit all address row 0, so the answer would be a different
    question's."""

    work = _export_copy(tmp_path, 'smartphone_2layer_gwp_base')
    dcf = TwoLayerDCF(work, total_output = 1.0, product_uuid = _UUID_2L['display'])
    # Give the (mis-declared) product row a component entry, so the UUID sets still match.
    dcf.inp['LCA - Smartphone Components']['Display']['UUID'] = _UUID_2L['product']

    with pytest.raises(ValueError, match='is not the reference flow of the export'):
        LCA_Plugin(dcf, print_info = False)


def test_duplicate_component_uuid_is_rejected(tmp_path):
    """A UUID on two rows used to be overwritten by the last one, and the set comparison
    could not see it: a duplicate paired with a missing component leaves both sets the
    same size, so 600 kg + 400 kg of battery silently became 400 kg."""

    work = _export_copy(tmp_path, 'smartphone_2layer_gwp_base')
    dcf = TwoLayerDCF(work, total_output = 1.0)
    dcf.inp['LCA - Smartphone Components']['Battery (second half)'] = {
        'UUID': _UUID_2L['battery'], 'Value': 0.4, 'Unit': 'kg'}

    with pytest.raises(ValueError, match='declared more than once'):
        LCA_Plugin(dcf, print_info = False)


def test_export_whose_first_column_does_not_produce_its_reference_flow_is_rejected(tmp_path):
    """Everything downstream addresses the reference flow by position, so an export
    whose first technosphere column has no positive row 0 has to be refused outright."""

    work = _export_copy(tmp_path, 'smartphone_1layer_gwp_base')
    technosphere = np.asarray(matrix_of(find_matrix_path(str(work), 'A')), dtype = float)
    technosphere[0, 0] = -technosphere[0, 0]
    np.save(work / 'A.npy', technosphere)

    with pytest.raises(ValueError, match='does not produce'):
        LCA_Plugin(SmartphoneDCF(work), print_info = False)


def test_incomplete_cache_directory_is_rebuilt(tmp_path):
    """A matching fingerprint is not enough: an Initial_Artifacts folder left by an
    older pyH2A, or partially deleted, has to be rebuilt rather than loaded from."""

    work = _export_copy(tmp_path, 'smartphone_2layer_gwp_base')
    assert (LCA_Plugin(TwoLayerDCF(work, total_output = 1.0), print_info = False)
            .lca_results['Global warming potential'].supplied_value == pytest.approx(10.0))

    (work / 'Initial_Artifacts' / 'h_basis.npz').unlink()
    LCA_Plugin._cache_key = None

    assert (LCA_Plugin(TwoLayerDCF(work, total_output = 1.0), print_info = False)
            .lca_results['Global warming potential'].supplied_value == pytest.approx(10.0))


def test_impact_unit_that_is_not_a_known_unit_is_named(tmp_path):
    """openLCA impact units that are neither a pyH2A unit nor mapped in
    Config/OpenLCA_config.py have to surface, naming the offending unit."""

    work = _export_copy(tmp_path, 'smartphone_1layer_gwp_base')
    _rewrite_csv(work / 'index_C.csv', lambda rows: rows[0].__setitem__(3, 'kg 1,4-DCB'))
    with pytest.raises(ValueError, match=r"1,4-DCB"):
        LCA_Plugin(SmartphoneDCF(work), print_info=False)


def test_duplicate_provider_id_is_rejected(tmp_path):
    work = _export_copy(tmp_path, 'smartphone_1layer_gwp_base')
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
