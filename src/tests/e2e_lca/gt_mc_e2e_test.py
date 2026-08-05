"""
Matrix: src/tests/e2e_lca/data/matrix_folders/smartphone_3layer_ced_base
Input:  src/tests/e2e_lca/data/input_files/smartphone_3layer_mc_ced_seed42.md

Plugin/path-driven GT components
---------------------------------
The Monte Carlo `Parameters - Monte_Carlo_Analysis` table targets each 
component's own plugin input cell
(``GT Circuit Board Input > Scenario Factor > Value`` / ``GT Display Input >
Scenario Factor > Value`` / ``GT Battery Input > Scenario Factor > Value``).
``Test_Plugin_C`` / ``Test_Plugin_D`` / ``Test_Plugin_E`` (Circuit Board /
Display / Battery, respectively) read the sampled factor on every Monte
Carlo sample (each sample deep-copies `inp` and reconstructs
`Discounted_Cash_Flow` from scratch, so the plugins re-run every
time) and multiply it by their fixed Base Quantity
into a dedicated output table; the LCA GT Components table then references
that output via path syntax (e.g. ``{GT Display Output > Display > Value,
kg}``). The three parameters are sampled in table-row order (Circuit Board,
then Display, then Battery); each parameter's call to `np.random.uniform`
consumes the next `Samples` values from the single shared stream, so
changing the row order or the sample count changes every downstream value.

Sample count
------------
Samples is set to 10 for a fast test run. Monte_Carlo_Analysis.__init__
unconditionally calls full_distance_response_relationship(), whose
Savitzky-Golay smoothing needs window_length > poly_order (window_length =
int(samples/reduction_factor), reduction_factor=25 by default) -- with only
10 samples that would raise a ValueError from scipy.signal.savgol_filter.
Therefore, this test monkeypatches it to a no-op for its own duration (see
test_monte_carlo_pipeline_matches_seed42_reference below).
"""
import os
import shutil
from pathlib import Path

import numpy as np
import pytest
from pyH2A.Plugins.Life_Cycle_Assessment_Plugin import Life_Cycle_Assessment_Plugin
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Analysis.Monte_Carlo_Analysis import Monte_Carlo_Analysis
from pyH2A.Utilities.input_modification import convert_input_to_dictionary
from pyH2A.Utilities.lca_utils import get_cache_paths

_HERE = Path(__file__).parent
_INPUT_FILE = _HERE / 'data' / 'input_files' / 'smartphone_3layer_mc_ced_seed42.md'
_OUTPUT_FILE = _HERE / 'data' / 'input_files' / 'smartphone_3layer_mc_ced_seed42_output.csv'


_MATRIX_FOLDER = convert_input_to_dictionary(str(_INPUT_FILE))['Life Cycle Assessment']['Matrix Folder']['Value']

_SEED = 42

# Precalculated results (sampled Scenario Factor for Circuit Board, Display, and
# Battery, followed by CED [kWh/kg Smartphone]) for 10 samples, produced by running
# pyH2A(input_file, output_directory) with np.random.seed(42). Each factor is
# dimensionless (see GT Circuit Board/Display/Battery Input > Scenario Factor);
# it numerically equals the resulting Circuit Board [item] / Display [kg] /
# Battery [kg] quantity fed into the LCA GT Components table only because each
# component's Base Quantity is 1.0 here.
# Each of the 10 sampled (Circuit Board, Display, Battery) triplets was fed into openLCA to
# independently compute the reference CED value used below, so this array
# doubles as ground truth for validating that the Monte Carlo pipeline
# reproduces openLCA's results. The corresponding openLCA model for each
# sample point is zipped up in its own matrix folder:
# src/tests/e2e_lca/data/matrix_folders/smartphone_3layer_ced_mc_spN/smartphone_3layer_ced_mc_spN.zip,
# where N (1-10) is the sample point number, matching this array's row order
# (row 0 -> sp1, row 1 -> sp2, etc.).

_REFERENCE_RESULTS = np.array([
    [1.37454012, 1.02058449, 1.61185289, 70.17907215],
    [1.95071431, 1.96990985, 1.13949386, 75.90150093],
    [1.73199394, 1.83244264, 1.29214465, 76.13004796],
    [1.59865848, 1.21233911, 1.36636184, 68.25244368],
    [1.15601864, 1.18182497, 1.45606998, 66.26360688],
    [1.15599452, 1.18340451, 1.78517596, 75.17136478],
    [1.05808361, 1.30424224, 1.19967378, 60.17333603],
    [1.86617615, 1.52475643, 1.51423444, 79.02650519],
    [1.60111501, 1.43194502, 1.59241457, 77.45245873],
    [1.70807258, 1.29122914, 1.04645041, 61.70402231],
])


def _clear_ram_cache():
    for k in Life_Cycle_Assessment_Plugin._cache:
        Life_Cycle_Assessment_Plugin._cache[k] = None
    get_cache_paths.cache_clear()


def _clear_disk_cache():
    disk_cache_dir = Path(_MATRIX_FOLDER) / 'Initial_Artifacts'
    if disk_cache_dir.exists():
        shutil.rmtree(disk_cache_dir)


@pytest.fixture(autouse=True)
def _manage_lca_cache():
    # RAM cache is process-wide and not keyed by matrix folder, so it must be
    # cleared to avoid reusing another folder's cached matrices. The on-disk
    # Initial_Artifacts cache is also cleared here (both before and after),
    # so this test is self-contained and does not depend on whether
    # gt_lca_e2e_all_layers_test.py (which targets the same
    # smartphone_3layer_ced_base folder) has already run in this session --
    # this test always exercises its own cold-start LU factorization.
    _clear_ram_cache()
    _clear_disk_cache()
    yield
    _clear_ram_cache()
    _clear_disk_cache()
    if _OUTPUT_FILE.exists():
        os.remove(_OUTPUT_FILE)


def test_monte_carlo_pipeline_matches_seed42_reference(monkeypatch):
    # Monte_Carlo_Analysis.__init__ unconditionally calls
    # full_distance_response_relationship(), whose Savitzky-Golay smoothing needs
    # window_length > poly_order (window_length = int(samples/reduction_factor),
    # reduction_factor=25 by default) -- with only 10 samples that raises a
    # ValueError from scipy.signal.savgol_filter. That smoothing only feeds the
    # optional plot_distance_response_relationship plotting method, unused here, so
    # it is monkeypatched to a no-op for this test only.
    monkeypatch.setattr(Monte_Carlo_Analysis, 'full_distance_response_relationship', lambda self, *args, **kwargs: None)

    np.random.seed(_SEED)
    result = pyH2A(str(_INPUT_FILE), str(_HERE / 'data' / 'input_files'))
    mc = result.meta_modules['Monte_Carlo_Analysis']['Module']
    np.testing.assert_allclose(mc.results, _REFERENCE_RESULTS, rtol=1e-8)
