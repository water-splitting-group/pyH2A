'''End-to-end test of the Monte Carlo analysis for the PV + electrolysis model with LCA.

The Monte Carlo analysis is run through pyH2A with a fixed random seed (computing and saving the
results and executing all plotting methods). The ground truth is generated outside of the Monte Carlo
pipeline: the random parameter values are regenerated with the same seed and the global warming
potential is calculated for each set of values by running Discounted_Cash_Flow directly.
'''

import copy
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from matplotlib.figure import Figure
from matplotlib.text import Text

from pyH2A import __version__
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import convert_input_to_dictionary
from pyH2A.Analysis.Monte_Carlo_Analysis import (Monte_Carlo_Analysis,
                                                 read_results_file,
                                                 write_results_file)

TOLERANCE = 1e-9

REPOSITORY = Path(__file__).resolve().parents[4]
MONTE_CARLO_INPUT = Path(__file__).resolve().parent / 'PV_E_Monte_Carlo_Test.md'
BASE_MODEL = REPOSITORY / 'src/tests/e2e_lca/data/PV_E/PV_E_TEA_LCA.md'
DEFAULTS = 'pyH2A.Config~Defaults_TEA_LCA.md'
MATRIX_FOLDER = REPOSITORY / 'src/tests/e2e_lca/data/PV_E/260930_SD-007_Foreground_Stacks'

# Settings of PV_E_Monte_Carlo_Test.md
SAMPLES = 50
RANDOM_SEED = 2026
TARGET_RANGE = (1.5, 1.6)
IMPACT_ASSESSMENT_CATEGORY = 'Climate change: fossil - Global warming potential (GWP100)'
DEPENDENT_VARIABLE = {'Name': 'Global warming potential (GWP100)',
                      'Path': ['Dependent Variables', IMPACT_ASSESSMENT_CATEGORY, 'Value'],
                      'Unit': 'kg[$CO_{2}$-Eq]/kg[H2]'}

# Name, path, type, base and limit value of the varied parameters (in table order)
PARAMETERS = [
    ('PV efficiency / -', ['Photovoltaic', 'Efficiency', 'Value'], 'value', 0.2, 0.3),
    ('Battery energy density / kWh/kg[battery]', ['Battery', 'Energy density', 'Value'], 'value', 0.144, 0.25),
    ('Electrolyzer efficiency / kg[H2]/kWh[electricity]', ['Electrolyzer', 'Hydrogen yield per unit energy', 'Value'], 'value', 0.0185, 0.022),
    ('Reverse osmosis recovery rate / -', ['Reverse Osmosis', 'Recovery rate', 'Value'], 'value', 0.4, 0.8),
    ('PV power loss per year (factor) / -', ['Photovoltaic', 'Power loss per year', 'Value'], 'factor', 1., 0.5),
]
NAMES = [parameter[0] for parameter in PARAMETERS]
BASE_VALUES = np.array([parameter[3] for parameter in PARAMETERS])
LIMIT_VALUES = np.array([parameter[4] for parameter in PARAMETERS])

def write_input(path: Path, tables: dict) -> Path:
    '''Write markdown input file with `tables` ({title: [header, *rows]}) to `path`.'''

    lines = []

    for title, (header, *rows) in tables.items():
        lines += [f'# {title}', '', ' | '.join(header), ' | '.join(['---'] * len(header))]
        lines += [' | '.join(str(cell) for cell in row) for row in rows]
        lines.append('')

    path.write_text('\n'.join(lines))

    return path

def write_read_input(path: Path,
                     results_file: Path,
                     parameters: list = PARAMETERS,
                     dependent_variable: dict = DEPENDENT_VARIABLE,
                     target_range: str = '1.5; 1.6') -> Path:
    '''Write input file which reads Monte Carlo results from `results_file`, with its own
    "Dependent variable" and "Parameters - Monte_Carlo_Analysis" tables.'''

    return write_input(path, {
        'Input files to merge': [['Name', 'Value'],
                                 ['PV-E Base Model', BASE_MODEL],
                                 ['Default TEA + LCA', DEFAULTS]],
        'Dependent variable': [['Name', 'Path to variable', 'Variable unit', 'Target range'],
                               [dependent_variable['Name'], ' > '.join(dependent_variable['Path']),
                                dependent_variable['Unit'], target_range]],
        'Monte_Carlo_Analysis': [['Name', 'Value'],
                                 ['Input File', results_file]],
        'Parameters - Monte_Carlo_Analysis': [['Name', 'Parameter path', 'Type', 'Values'],
                                              *[[name, ' > '.join(parameter_path), value_type, f'{base}; {limit}']
                                                for name, parameter_path, value_type, base, limit in parameters]],
    })

def expected_parameter_values() -> np.ndarray:
    '''Random parameter values regenerated with the random seed of the input file.'''

    rng = np.random.default_rng(RANDOM_SEED)

    return np.column_stack([rng.uniform(min(base, limit), max(base, limit), SAMPLES)
                            for *_, base, limit in PARAMETERS])

def calculate_ground_truth(parameter_values: np.ndarray, matrix_folder: Path) -> np.ndarray:
    '''Global warming potential for each set of parameter values, calculated directly with
    Discounted_Cash_Flow (outside of the Monte Carlo pipeline).'''

    base_inp = convert_input_to_dictionary(str(BASE_MODEL))
    base_inp['Life Cycle Assessment']['Matrix Folder']['Value'] = str(matrix_folder)

    results = []

    for values in parameter_values:
        inp = copy.deepcopy(base_inp)

        for (_, (table, row, column), value_type, *_), value in zip(PARAMETERS, values):
            if value_type == 'factor':
                inp[table][row][column] *= value
            else:
                inp[table][row][column] = value

        dcf = Discounted_Cash_Flow(inp, print_info = False)
        results.append(dcf.inp['Dependent Variables'][IMPACT_ASSESSMENT_CATEGORY]['Value'].unit[DEPENDENT_VARIABLE['Unit']])

    return np.array(results)

@pytest.fixture(scope = 'module')
def matrix_folder(tmp_path_factory) -> Path:
    '''Copy of the openLCA matrix export, so that cached LCA artifacts are written to a temporary directory.'''

    folder = tmp_path_factory.mktemp('lca') / MATRIX_FOLDER.name
    shutil.copytree(MATRIX_FOLDER, folder, ignore = shutil.ignore_patterns('Initial_Artifacts'))

    return folder

@pytest.fixture(scope = 'module')
def compute_run(tmp_path_factory, matrix_folder) -> dict:
    '''Monte Carlo analysis computed through pyH2A, with results file and figures saved in a temporary directory.'''

    directory = tmp_path_factory.mktemp('monte_carlo')
    results_file = directory / 'Monte_Carlo_Results.npz'

    # Nested input files are not merged, hence all input files of PV_E_Monte_Carlo_Test.md are listed
    input_file = write_input(directory / 'PV_E_Monte_Carlo_Run.md', {
        'Input files to merge': [['Name', 'Value'],
                                 ['Monte Carlo Test', MONTE_CARLO_INPUT],
                                 ['PV-E Base Model', BASE_MODEL],
                                 ['Default TEA + LCA', DEFAULTS]],
        'Monte_Carlo_Analysis': [['Name', 'Value'], ['Output File', results_file]],
        'Life Cycle Assessment': [['Name', 'Value'], ['Matrix Folder', matrix_folder]],
    })

    result = pyH2A(str(input_file), str(directory))

    return {'result': result,
            'monte_carlo': result.meta_modules['Monte_Carlo_Analysis']['Module'],
            'figures': result.meta_modules['Monte_Carlo_Analysis'],
            'directory': directory,
            'input_file': input_file,
            'results_file': results_file}

@pytest.fixture(scope = 'module')
def ground_truth(matrix_folder) -> np.ndarray:
    '''Ground truth for the dependent variable of all samples.'''

    return calculate_ground_truth(expected_parameter_values(), matrix_folder)

def test_random_values_reproduced(compute_run):
    '''Sampled parameter values are reproduced with the random seed.'''

    monte_carlo = compute_run['monte_carlo']

    np.testing.assert_array_equal(monte_carlo.values, expected_parameter_values())
    np.testing.assert_array_equal(monte_carlo.results[:,:-1], monte_carlo.values)
    assert monte_carlo.samples == SAMPLES
    assert monte_carlo.random_seed == RANDOM_SEED
    assert monte_carlo.principal == NAMES

def test_results_match_ground_truth(compute_run, ground_truth):
    '''Dependent variable of each sample matches the ground truth calculated outside of the Monte Carlo pipeline.'''

    np.testing.assert_allclose(compute_run['monte_carlo'].results[:,-1], ground_truth, rtol = TOLERANCE, atol = 0.)

def test_results_file(compute_run):
    '''Results file contains the results and all metadata, readable with NumPy and json only.'''

    monte_carlo = compute_run['monte_carlo']

    with np.load(compute_run['results_file'], allow_pickle = False) as data:
        assert set(data.files) == {'parameter_values', 'dependent_variable_values', 'metadata'}
        np.testing.assert_array_equal(data['parameter_values'], monte_carlo.values)
        np.testing.assert_array_equal(data['dependent_variable_values'], monte_carlo.results[:,-1])
        metadata = json.loads(data['metadata'].item())

    assert metadata == monte_carlo.metadata

    datetime.fromisoformat(metadata.pop('Created'))
    assert metadata == {
        'File format version': 1,
        'pyH2A version': __version__,
        'NumPy version': np.__version__,
        'Input file': str(compute_run['input_file']),
        'Samples': SAMPLES,
        'Random seed': RANDOM_SEED,
        'Dependent variable': {**DEPENDENT_VARIABLE, 'Target range': list(TARGET_RANGE)},
        'Parameters': [{'Name': name, 'Path': path, 'Type': value_type, 'Values': sorted([base, limit]),
                        'Reference': base, 'Limit': limit} for name, path, value_type, base, limit in PARAMETERS],
    }

    parameter_values, dependent_variable_values, metadata_read = read_results_file(compute_run['results_file'])

    np.testing.assert_array_equal(parameter_values, monte_carlo.values)
    np.testing.assert_array_equal(dependent_variable_values, monte_carlo.results[:,-1])
    assert metadata_read == monte_carlo.metadata

def test_target_range_and_development_distance(compute_run, ground_truth):
    '''Selection of samples within the target range and development distances match an independent calculation.'''

    monte_carlo = compute_run['monte_carlo']
    values = expected_parameter_values()

    within_target_range = (ground_truth >= TARGET_RANGE[0]) & (ground_truth <= TARGET_RANGE[1])
    order = np.argsort(ground_truth[within_target_range])
    target_values = values[within_target_range][order]
    target_ground_truth = ground_truth[within_target_range][order]

    assert len(target_values) > 0
    np.testing.assert_array_equal(monte_carlo.target_range_data[:,:-1], target_values)
    np.testing.assert_allclose(monte_carlo.target_range_data[:,-1], target_ground_truth, rtol = TOLERANCE)

    # Cityblock development distance: mean of normalized parameter changes (0: base, 1: limit)
    target_distances = np.mean(np.abs((target_values - BASE_VALUES) / (LIMIT_VALUES - BASE_VALUES)), axis = 1)
    np.testing.assert_allclose(monte_carlo.distances, target_distances, rtol = 1e-12)

    shortest = np.argmin(target_distances)
    assert monte_carlo.shortest_target_distance['Distance'] == pytest.approx(target_distances[shortest], rel = 1e-12)
    assert monte_carlo.shortest_target_distance[f'{DEPENDENT_VARIABLE["Name"]} / {DEPENDENT_VARIABLE["Unit"]}'] == pytest.approx(target_ground_truth[shortest], rel = TOLERANCE)
    assert [monte_carlo.shortest_target_distance[name] for name in NAMES] == list(target_values[shortest])

    distances = np.mean(np.abs((values - BASE_VALUES) / (LIMIT_VALUES - BASE_VALUES)), axis = 1)
    np.testing.assert_allclose(monte_carlo.results_distances_sorted[:,-1], np.sort(distances), rtol = 1e-12)
    assert monte_carlo.distances_cost_savgol.shape == (SAMPLES, 2)

def test_target_range_2D_region(compute_run, matrix_folder):
    '''Grid evaluation used for the colored scatter plot matches the ground truth.'''

    monte_carlo = compute_run['monte_carlo']
    grid = monte_carlo.target_range_2D_grid # Computed by plot_colored_scatter (grid_points = 5)

    np.testing.assert_array_equal(grid['Grid Values'][0][0], np.linspace(0.2, 0.3, 5))
    np.testing.assert_array_equal(grid['Grid Values'][1][:,0], np.linspace(0.144, 0.25, 5))
    assert grid['Dependent variable 2D'].shape == (5, 5)

    # Upper corner of grid: all parameters at their limit values
    all_limits = calculate_ground_truth(LIMIT_VALUES[np.newaxis], matrix_folder)[0]
    assert grid['Dependent variable 2D'][-1,-1] == pytest.approx(all_limits, rel = TOLERANCE)

    base_value = compute_run['result'].base_case.inp['Dependent Variables'][IMPACT_ASSESSMENT_CATEGORY]['Value'].unit[DEPENDENT_VARIABLE['Unit']]
    assert grid['Base value'] == pytest.approx(base_value, rel = TOLERANCE)

def test_plots(compute_run):
    '''All plotting methods are executed and saved, using the name and unit of the dependent variable
    and the parameter names as labels.'''

    figures = compute_run['figures']
    dependent_variable_label = f'{DEPENDENT_VARIABLE["Name"]} / {DEPENDENT_VARIABLE["Unit"]}'
    title = f'Target range: 1.5 - 1.6 {DEPENDENT_VARIABLE["Unit"]}'

    for name in ['Monte_Carlo_Complete_Histogram', 'Monte_Carlo_Colored_Scatter', 'Monte_Carlo_Colored_Scatter_3D',
                 'Monte_Carlo_Distance_Histogram', 'Monte_Carlo_Distance_Cost_Relationship',
                 'Monte_Carlo_Target_Parameters_By_Distance']:
        assert (compute_run['directory'] / f'{name}_{compute_run["input_file"].stem}.png').is_file()

    assert figures['complete_histogram'].axes[0].get_xlabel() == dependent_variable_label

    scatter, colorbar = figures['colored_scatter'].axes
    assert [scatter.get_xlabel(), scatter.get_ylabel(), colorbar.get_ylabel()] == NAMES[:3]
    assert scatter.get_title() == title

    scatter_3D, colorbar_3D = figures['colored_scatter_3D'].axes
    assert [scatter_3D.get_xlabel(), scatter_3D.get_ylabel(), colorbar_3D.get_ylabel(), scatter_3D.get_zlabel()] == NAMES[:4]
    assert scatter_3D.get_title() == title

    distance_histogram = figures['distance_histogram'].axes[0]
    assert distance_histogram.get_title() == title
    assert distance_histogram.get_xlabel() == 'Development distance'

    assert figures['distance_cost_relationship'].axes[0].get_ylabel() == dependent_variable_label

    target_parameters = figures['target_parameters_by_distance']
    assert [ax.get_title(loc = 'left') for ax in target_parameters.axes] == NAMES
    assert target_parameters.get_suptitle() == title

    for figure in figures.values():
        if isinstance(figure, Figure):
            assert not any('PLACEHOLDER' in text.get_text() for text in figure.findobj(Text))

def test_read_results_with_renamed_and_reordered_parameters(compute_run, tmp_path, monkeypatch):
    '''Saved results are read without running the model, parameters are mapped by their path so that they
    can be renamed and reordered, and a different target range can be used.'''

    def fail(*args, **kwargs):
        raise AssertionError('Model must not be evaluated when results are read.')

    monkeypatch.setattr(Monte_Carlo_Analysis, 'perform_monte_carlo_multiprocessing', fail)

    computed = compute_run['monte_carlo']
    renamed_parameters = [(f'{name} (renamed)', *rest) for name, *rest in reversed(PARAMETERS)]
    input_file = write_read_input(tmp_path / 'Read_Results.md', compute_run['results_file'],
                                  parameters = renamed_parameters,
                                  dependent_variable = {**DEPENDENT_VARIABLE, 'Name': 'GWP'},
                                  target_range = '1.4; 1.5')

    monte_carlo = Monte_Carlo_Analysis(str(input_file))

    assert monte_carlo.principal == [parameter[0] for parameter in renamed_parameters]
    np.testing.assert_array_equal(monte_carlo.values, computed.values[:,::-1])
    np.testing.assert_array_equal(monte_carlo.results[:,-1], computed.results[:,-1])
    assert monte_carlo.metadata == computed.metadata
    assert (monte_carlo.samples, monte_carlo.random_seed) == (SAMPLES, RANDOM_SEED)

    dependent_variable_values = computed.results[:,-1]
    within_target_range = (dependent_variable_values >= 1.4) & (dependent_variable_values <= 1.5)
    np.testing.assert_array_equal(np.sort(monte_carlo.target_range_data[:,-1]), np.sort(dependent_variable_values[within_target_range]))
    np.testing.assert_allclose(monte_carlo.results_distances_sorted[:,-1], computed.results_distances_sorted[:,-1], rtol = 1e-12)

    figure = monte_carlo.plot_target_parameters_by_distance(directory = tmp_path)
    assert [ax.get_title(loc = 'left') for ax in figure.axes] == monte_carlo.principal

    figure = monte_carlo.plot_complete_histogram(directory = tmp_path)
    assert figure.axes[0].get_xlabel() == f'GWP / {DEPENDENT_VARIABLE["Unit"]}'

    # Plotting into provided axes does not create (or return) a figure
    figure = Figure()
    assert monte_carlo.plot_distance_cost_relationship(ax = figure.add_subplot(), parameter_table = False) is None

def test_read_results_unit_conversion(compute_run, tmp_path):
    '''Read results are converted to the unit specified in the input file.'''

    computed = compute_run['monte_carlo']
    input_file = write_read_input(tmp_path / 'Read_Results_g.md', compute_run['results_file'],
                                  dependent_variable = {**DEPENDENT_VARIABLE, 'Unit': 'g[$CO_{2}$-Eq]/kg[H2]'},
                                  target_range = '1500; 1600')

    monte_carlo = Monte_Carlo_Analysis(str(input_file))

    np.testing.assert_allclose(monte_carlo.results[:,-1], computed.results[:,-1] * 1000., rtol = 1e-12)
    assert len(monte_carlo.target_range_data) == len(computed.target_range_data)

@pytest.mark.parametrize('changes, message', [
    ({'parameters': [(PARAMETERS[0][0], PARAMETERS[0][1], 'factor', 1., 1.5), *PARAMETERS[1:]]}, 'have to be recomputed'),
    ({'parameters': [(*PARAMETERS[0][:4], 0.35), *PARAMETERS[1:]]}, 'have to be recomputed'),
    ({'parameters': PARAMETERS[:-1]}, 'do not match'),
    ({'parameters': [*PARAMETERS, ('Battery lifetime / year', ['Battery', 'Lifetime', 'Value'], 'value', 10, 15)]}, 'do not match'),
    ({'dependent_variable': {'Name': 'Levelized cost', 'Path': ['Dependent Variables', 'Levelized cost', 'Value'], 'Unit': 'USD/kg[H2]'}}, 'contains results for'),
    ({'dependent_variable': {**DEPENDENT_VARIABLE, 'Unit': 'kWh/kg[H2]'}}, 'cannot be converted'),
    ({'results_file': 'Monte_Carlo_Results.csv'}, 'has to be a NumPy ".npz" file'),
], ids = ['type changed', 'values changed', 'parameter missing', 'additional parameter',
         'dependent variable changed', 'incompatible unit', 'legacy file format'])
def test_read_results_mismatch(compute_run, tmp_path, changes, message):
    '''Reading results which do not match the input file raises an error.'''

    input_file = write_read_input(tmp_path / 'Read_Results.md',
                                  **{'results_file': compute_run['results_file'], **changes})

    with pytest.raises(ValueError, match = message):
        Monte_Carlo_Analysis(str(input_file))

@pytest.mark.parametrize('metadata, message', [
    ({'File format version': 99}, 'file format version 99'),
    ({'File format version': 1, 'Samples': 2, 'Parameters': [{}]}, 'do not match its metadata'),
], ids = ['unsupported version', 'inconsistent shapes'])
def test_invalid_results_file(tmp_path, metadata, message):
    '''Results files with an unsupported file format version or inconsistent arrays are rejected.'''

    results_file = tmp_path / 'Results.npz'
    write_results_file(results_file, np.zeros((1, 1)), np.zeros(1), metadata)

    with pytest.raises(ValueError, match = message):
        read_results_file(results_file)

    assert [path.name for path in tmp_path.iterdir()] == ['Results.npz'] # No temporary files are left behind

def write_compute_input(path: Path, 
                        monte_carlo_rows: list, 
                        parameter_type: str = 'value', 
                        parameter_path: str = 'Photovoltaic > Efficiency > Value') -> Path:
    '''Write input file for computing Monte Carlo results with one parameter.'''

    return write_input(path, {
        'Input files to merge': [['Name', 'Value'],
                                 ['PV-E Base Model', BASE_MODEL],
                                 ['Default TEA + LCA', DEFAULTS]],
        'Dependent variable': [['Name', 'Path to variable', 'Variable unit', 'Target range'],
                               [DEPENDENT_VARIABLE['Name'], ' > '.join(DEPENDENT_VARIABLE['Path']), DEPENDENT_VARIABLE['Unit'], '1.5; 1.6']],
        'Monte_Carlo_Analysis': [['Name', 'Value'], *monte_carlo_rows],
        'Parameters - Monte_Carlo_Analysis': [['Name', 'Parameter path', 'Type', 'Values'],
                                              ['Varied parameter', parameter_path, parameter_type, 'Base; 0.3']],
    })

@pytest.mark.parametrize('monte_carlo_rows, parameter_type, parameter_path, error, message', [
    ([['Output File', 'Results.npz']], 'value', 'Photovoltaic > Efficiency > Value', KeyError, 'Samples'),
    ([['Samples', 10]], 'value', 'Photovoltaic > Efficiency > Value', KeyError, 'Output File'),
    ([['Samples', 10], ['Output File', 'Results.txt']], 'value', 'Photovoltaic > Efficiency > Value', ValueError, 'has to be a NumPy ".npz" file'),
    ([['Samples', 10], ['Output File', 'Results.npz']], 'Factor', 'Photovoltaic > Efficiency > Value', ValueError, 'Expected one of'),
    ([['Samples', 10], ['Output File', 'Results.npz']], 'value', 'Hourly Irradiation > File > Value', ValueError, 'is not a number'),
], ids = ['samples missing', 'output file missing', 'output file not npz', 'invalid type', 'non-numerical parameter'])
def test_invalid_compute_input(tmp_path, monkeypatch, monte_carlo_rows, parameter_type, parameter_path, error, message):
    '''Invalid inputs for computing results raise an error before the model is evaluated.'''

    def fail(*args, **kwargs):
        raise AssertionError('Model must not be evaluated for invalid inputs.')

    monkeypatch.setattr(Monte_Carlo_Analysis, 'perform_monte_carlo_multiprocessing', fail)

    input_file = write_compute_input(tmp_path / 'Invalid.md', monte_carlo_rows, 
                                     parameter_type = parameter_type, parameter_path = parameter_path)

    with pytest.raises(error, match = message):
        Monte_Carlo_Analysis(str(input_file))

def test_random_seed_drawn_if_not_specified(tmp_path, monkeypatch):
    '''If no random seed is specified, a seed is drawn and stored, so that the values can be reproduced.'''

    def constant_response(self, inp, values, return_full_array = True):
        return np.c_[values, np.full(len(values), 1.55)]

    monkeypatch.setattr(Monte_Carlo_Analysis, 'perform_monte_carlo_multiprocessing', constant_response)

    results_file = tmp_path / 'Results.npz'
    input_file = write_compute_input(tmp_path / 'No_Seed.md', [['Samples', 3], ['Output File', results_file]])

    monte_carlo = Monte_Carlo_Analysis(str(input_file))

    assert isinstance(monte_carlo.random_seed, int)
    assert read_results_file(results_file)[2]['Random seed'] == monte_carlo.random_seed
    np.testing.assert_array_equal(monte_carlo.generate_random_values(3, monte_carlo.random_seed), monte_carlo.values)

def test_no_samples_within_target_range(compute_run, tmp_path):
    '''A target range without samples issues a warning, plots depending on these samples raise an error.'''

    input_file = write_read_input(tmp_path / 'Read_Results.md', compute_run['results_file'], target_range = '10; 11')

    with pytest.warns(UserWarning, match = 'No Monte Carlo sample'):
        monte_carlo = Monte_Carlo_Analysis(str(input_file))

    assert len(monte_carlo.target_range_data) == 0
    assert monte_carlo.shortest_target_distance == {}

    with pytest.raises(ValueError, match = 'Target range'):
        monte_carlo.plot_distance_histogram(directory = tmp_path)
