'''Tests of the Optimization_Analysis module.

The end-to-end test runs pyH2A with ``PV_E_Optimization_Test.md``, which minimizes the global
warming potential of the PV-E model (TEA + LCA) by varying the nominal power of the
electrolyzer and the PV system and the capacity of the battery. The module-level optimization
function is additionally tested the way other analysis modules use it (e.g. per Monte Carlo
sample).
'''

from pathlib import Path

import numpy as np
import pytest
from matplotlib.figure import Figure

import pyH2A.Analysis.Optimization_Analysis as optimization_module
from pyH2A.run_pyH2A import pyH2A
from pyH2A.Utilities.IO import input_resolver_function
from pyH2A.Utilities.input_modification import (convert_input_to_dictionary,
                                                convert_file_to_dictionary,
                                                Inp_Wrapper)
from pyH2A.Utilities.Analysis_Utilities.analysis_utilities import (read_dependent_variable,
                                                                   process_parameters)
from pyH2A.Analysis.Optimization_Analysis import (Optimization_Analysis,
                                                  evaluate_dependent_variable,
                                                  get_bounds,
                                                  optimization_objective,
                                                  perform_optimization,
                                                  read_optimization_settings)

INPUT_FILE = 'src/tests/Analysis/Optimization/PV_E_Optimization_Test.md'
OUTPUT_FILE = Path('src/tests/Analysis/Optimization/Optimization_Output.txt') # Output File specified in INPUT_FILE
TOLERANCE = 1e-12

def read_inputs(input_file):
    '''Read dependent variable and parameters from input file the way other analysis
    modules do before calling `perform_optimization`.'''

    inp = convert_input_to_dictionary(input_file)
    input_dict = Optimization_Analysis(input_file, run = False).input_dict
    inp_resolved = input_resolver_function(input_dict, Inp_Wrapper(inp), 'Optimization_Analysis')

    dependent_variable = read_dependent_variable(inp_resolved['Dependent variable'],
                                                 keys = ['Path to variable', 'Variable unit'])
    parameters = process_parameters(inp_resolved['Parameters - Optimization_Analysis'],
                                    inp,
                                    keys = ['Parameter path', 'Values'])

    return inp, dependent_variable, parameters

def test_pv_e_optimization_end_to_end(tmp_path):
    '''Full pyH2A run with optimization, report file and convergence plot.'''

    OUTPUT_FILE.unlink(missing_ok = True) # make sure the report is written by this run

    result = pyH2A(INPUT_FILE, str(tmp_path))

    module = result.meta_modules['Optimization_Analysis']
    analysis = module['Module']
    results = analysis.results
    parameters = analysis.parameters
    dependent_variable = analysis.dependent_variable

    # Settings from input file are used
    assert results['Direction'] == 'minimize'
    assert results['Settings']['maxiter'] == 20
    assert results['Settings']['popsize'] == 5
    assert results['Settings']['seed'] == 42
    assert results['Settings']['polish'] is False

    # Optimal parameters are within their bounds
    for name, parameter in parameters.items():
        lower, upper = parameter['Values']
        assert lower <= results['Optimal parameters'][name] <= upper

    # Running the model with the optimal parameters reproduces the optimal value
    optimal_value = evaluate_dependent_variable(results['Optimizer result'].x,
                                                parameters,
                                                analysis.inp,
                                                dependent_variable)
    assert optimal_value == pytest.approx(results['Optimal value'], rel = TOLERANCE)

    # Base case value is identical to the base case of the pyH2A run
    base_case = result.base_case.inp['Dependent Variables']['Climate change: fossil - Global warming potential (GWP100)']['Value']
    assert results['Base case value'] == pytest.approx(base_case.unit[dependent_variable['Unit']], rel = TOLERANCE)

    # Optimum is the best member of the final population and the history improves monotonically up to it
    best_values = [entry['Best value'] for entry in results['History']]
    assert results['Optimal value'] == np.min(results['Population values'])
    assert len(best_values) == results['Generations']
    assert np.all(np.diff(best_values) <= 0)
    assert best_values[-1] == results['Optimal value']

    # Without polishing, the initial population and one trial per member and generation are evaluated
    assert len(results['Population']) == results['Settings']['popsize'] * len(parameters)
    assert results['Function evaluations'] == len(results['Population']) * (results['Generations'] + 1)

    # Report file contains the results
    with open(OUTPUT_FILE) as file:
        report = convert_file_to_dictionary(file)

    summary = report['Optimization summary']
    assert summary['Dependent variable']['Value'] == dependent_variable['Name']
    assert summary['Variable unit']['Value'] == dependent_variable['Unit']
    assert summary['Direction']['Value'] == 'minimize'
    assert summary['Optimal value']['Value'] == pytest.approx(results['Optimal value'], rel = TOLERANCE)
    assert summary['Base case value']['Value'] == pytest.approx(results['Base case value'], rel = TOLERANCE)
    assert summary['Success']['Value'] == str(results['Success'])
    assert summary['Message']['Value'] == results['Message']
    assert summary['Generations']['Value'] == results['Generations']
    assert summary['Function evaluations']['Value'] == results['Function evaluations']
    assert summary['Model evaluations']['Value'] == results['Function evaluations'] + 1

    for name, parameter in parameters.items():
        row = report['Optimal parameters'][name]
        assert row['Parameter path'] == ' > '.join(parameter['Parameter'])
        assert [row['Lower bound'], row['Upper bound']] == list(parameter['Values'])
        assert row['Base case value'] == parameter['Reference']
        assert row['Optimal value'] == pytest.approx(results['Optimal parameters'][name], rel = TOLERANCE)

    settings = report['Optimization settings']
    assert settings['maxiter']['Value'] == 20
    assert settings['maxiter']['Input file row'] == 'Maximum iterations'
    assert settings['polish']['Value'] == 'False'

    history = report['Convergence history']
    assert len(history) == results['Generations']
    assert history[f"Generation {results['Generations']}"]['Best value'] == pytest.approx(results['Optimal value'], rel = TOLERANCE)

    # Final population is sorted (best member first) and within the bounds
    population = report['Final population']
    population_values = [row[dependent_variable['Name']] for row in population.values()]
    assert len(population) == len(results['Population'])
    assert population_values == sorted(population_values)
    assert population_values[0] == pytest.approx(results['Optimal value'], rel = TOLERANCE)

    for row in population.values():
        for name, parameter in parameters.items():
            lower, upper = parameter['Values']
            assert lower <= row[name] <= upper

    # Convergence plot requested in `Methods - Optimization_Analysis` table
    assert isinstance(module['Convergence plot'], Figure)
    assert (tmp_path / 'Optimization_Convergence_PV_E_Optimization_Test.pdf').is_file()

def test_perform_optimization_maximize_parallel():
    '''Module-level optimization function: maximization with parallel workers.'''

    inp, dependent_variable, parameters = read_inputs(INPUT_FILE)

    settings = {'maxiter': 3, 'popsize': 2, 'polish': False, 'seed': 1}

    results = perform_optimization(inp, parameters, dependent_variable,
                                   direction = 'maximize',
                                   settings = {**settings, 'workers': 2})

    # Parallel evaluation requires deferred updating
    assert results['Settings']['workers'] == 2
    assert results['Settings']['updating'] == 'deferred'

    # Optimizer minimizes the negative dependent variable, results are reported for the dependent variable
    assert results['Optimizer result'].fun == pytest.approx(-results['Optimal value'], rel = TOLERANCE)
    assert results['Optimal value'] == np.max(results['Population values'])

    best_values = [entry['Best value'] for entry in results['History']]
    assert np.all(np.diff(best_values) >= 0)
    assert best_values[-1] == results['Optimal value']

    optimal_value = evaluate_dependent_variable(results['Optimizer result'].x, parameters, inp, dependent_variable)
    assert optimal_value == pytest.approx(results['Optimal value'], rel = TOLERANCE)
    assert results['Function evaluations'] == len(results['Population']) * (results['Generations'] + 1)

    # With deferred updating, a seeded optimization does not depend on the number of workers
    results_serial = perform_optimization(inp, parameters, dependent_variable,
                                          direction = 'maximize',
                                          settings = {**settings, 'workers': 1, 'updating': 'deferred'},
                                          evaluate_base_case = False)

    assert results_serial['Base case value'] is None
    np.testing.assert_array_equal(results_serial['Optimizer result'].x, results['Optimizer result'].x)
    assert results_serial['Optimal value'] == results['Optimal value']

def test_read_optimization_settings():
    '''Conversion of the `Optimization_Analysis` table to differential evolution settings.'''

    direction, settings = read_optimization_settings(None)
    assert direction == 'minimize'
    assert settings == {}

    table = {'Direction': {'Value': 'maximize'},
             'Output File': {'Value': 'report.txt'},
             'Maximum iterations': {'Value': 50},
             'Mutation': {'Value': '0.4 ; 0.9'},
             'Polish': {'Value': 'False'},
             'Workers': {'Value': -1}}

    direction, settings = read_optimization_settings(table)
    assert direction == 'maximize'
    assert settings == {'maxiter': 50, 'mutation': (0.4, 0.9), 'polish': False, 'workers': -1}

def test_input_errors(tmp_path):
    '''Invalid inputs raise errors before the optimization is performed.'''

    with pytest.raises(ValueError, match = 'Direction'):
        perform_optimization({}, {}, {'Unit': '-'}, direction = 'maximise')

    with pytest.raises(ValueError, match = 'smaller than its upper bound'):
        get_bounds({'A': {'Values': np.array([5, 5]), 'Index': 0}})

    with pytest.raises(ValueError, match = 'exactly two values'):
        get_bounds({'A': {'Values': np.array([1, 2, 3]), 'Index': 0}})

    # Misspelled row in `Optimization_Analysis` table
    input_file = tmp_path / 'Typo.md'
    input_file.write_text(Path(INPUT_FILE).read_text().replace('Maximum iterations', 'Maximum iteration'))

    with pytest.raises(ValueError, match = 'Maximum iteration'):
        Optimization_Analysis(str(input_file))

def test_optimization_objective(monkeypatch):
    '''Non-finite results are never selected as optimum, non-scalar results raise an error.'''

    dependent_variable = {'Name': 'Test variable'}

    monkeypatch.setattr(optimization_module, 'substitute_parameters_and_run', lambda *args: 2.)
    assert optimization_objective(np.empty(0), {}, {}, dependent_variable, sign = -1.) == -2.

    monkeypatch.setattr(optimization_module, 'substitute_parameters_and_run', lambda *args: np.nan)
    assert optimization_objective(np.empty(0), {}, {}, dependent_variable) == np.inf

    monkeypatch.setattr(optimization_module, 'substitute_parameters_and_run', lambda *args: np.ones(3))
    with pytest.raises(ValueError, match = 'scalar'):
        optimization_objective(np.empty(0), {}, {}, dependent_variable)

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
