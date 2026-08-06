import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import num, convert_input_to_dictionary, parse_parameter, parse_path_with_unit, get_by_path, set_by_path
from pyH2A.Utilities.output_utilities import make_bold, Figure_Lean, dynamic_value_formatting

import pprint

# NOTE: this is a local, per-module fix. Monte_Carlo_Analysis, Optimization_Analysis, and
# Waterfall_Analysis reference the same dead dcf.h2_cost attribute and need an equivalent fix;
# consider extracting a shared utility if/when this same fix is applied there too.
def _resolve_dependent_variable(dcf, dependent_variable_string):
	'''Resolve the tracked output value from a (fully processed) ``Discounted_Cash_Flow`` object.

	Parameters
	----------
	dcf : Discounted_Cash_Flow
		Fully processed ``Discounted_Cash_Flow`` object (i.e. after its workflow has run),
		whose ``.inp`` contains resolved ``Quantity`` objects.
	dependent_variable_string : str
		Path with unit, in "{top_key > middle_key > bottom_key, unit}" notation,
		identifying which value in ``dcf.inp`` to read out.

	Returns
	-------
	value : float
		Numeric value of the resolved ``Quantity``, in the requested unit.

	Notes
	-----
	No error handling is performed here: an invalid/non-resolving path is allowed to raise
	its natural ``KeyError``/``AttributeError``, rather than silently falling back to a
	default value. Only a missing ``Dependent variable`` row/table (handled by the caller,
	before this function is ever called) defaults silently.
	'''

	path_alone, unit = parse_path_with_unit(dependent_variable_string)
	parsed_path = parse_parameter(path_alone)
	quantity = get_by_path(dcf.inp, parsed_path)

	return quantity.unit[unit]

PARAMETERS_TABLE_ROUTE_PREFIX = 'Parameters - Sensitivity_Analysis - '
DEACTIVATE_SUFFIX = ' - Deactivate'

def _find_active_parameters_table(inp):
	'''Find the single active parameters table.

	One or more ``Parameters - Sensitivity_Analysis - <Route>`` tables are
	recognized, for a multi-route input file holding several routes side by
	side, e.g. ``Sensitivity_Analysis.md``, which has PV_E, PC, and PEC
	routes, only one active at a time.

	Parameters
	----------
	inp : dict
		Input dictionary (``self.inp``). May contain zero or more tables
		named ``Parameters - Sensitivity_Analysis - <Route>``, each describing
		one route's parameters to vary. Multiple route tables can coexist in a
		single input file (e.g. for PV_E, PC, and PEC), with all but one
		deactivated by suffixing its name with `` - Deactivate`` (e.g.
		``Parameters - Sensitivity_Analysis - PC - Deactivate``).

	Returns
	-------
	active_table_name : str
		Name of the single table that is not deactivated.

	Raises
	------
	ValueError
		If zero, or more than one, non-deactivated candidate table is found.
		Exactly one must be active at a time.

	Notes
	-----
	Deactivation is detected by checking whether a table name ends with
	`` - Deactivate`` - there is no existing shared mechanism elsewhere in the
	codebase for this (checked: `Discounted_Cash_Flow.py` has no such logic
	anywhere in the file). The only related precedent is
	`check_for_meta_module()` in `input_modification.py`, which uses a broader
	`'Deactivate' in key` substring check for a different purpose (whether
	`run_pyH2A.py` auto-dispatches an entire Analysis module) and has no
	bearing on which data a module's own code reads.
	'''

	candidates = [key for key in inp if key.startswith(PARAMETERS_TABLE_ROUTE_PREFIX)]
	active = [key for key in candidates if not key.endswith(DEACTIVATE_SUFFIX)]

	if len(active) == 0:
		raise ValueError(
			f"No active '{PARAMETERS_TABLE_ROUTE_PREFIX}<Route>' table found. Found "
			f"{len(candidates)} candidate table(s) in the input file: {candidates}. "
			"Exactly one table must be active - remove the "
			f"'{DEACTIVATE_SUFFIX}' suffix from the one you want to run."
		)

	if len(active) > 1:
		raise ValueError(
			f"Multiple active '{PARAMETERS_TABLE_ROUTE_PREFIX}<Route>' tables found: "
			f"{active}. Exactly one must be active at a time - add "
			f"'{DEACTIVATE_SUFFIX}' to the name of all but one of these tables."
		)

	return active[0]

# NOTE: deliberately NOT named with a 'Sensitivity_Analysis' prefix, even though these
# tables are route-specific config for this module - check_for_meta_module() in
# input_modification.py auto-dispatches ANY top-level table whose name contains the
# substring 'Analysis' (unless it also contains 'Parameters'/'Methods'/'Arguments'/
# 'Deactivate'), so a table named e.g. 'Sensitivity_Analysis - PC' would be wrongly
# treated as a module-dispatch trigger if this file were ever run through the full
# pyH2A(...) orchestrator, not just built directly via Sensitivity_Analysis(file).
CONFIG_TABLE_ROUTE_PREFIX = 'Route Config - '
EXPECTED_BASE_FILE_ROW = 'Expected base file'

def _check_base_file_matches_active_route(inp, active_table):
	'''Cross-check that the active route's declared base file matches the actual one.

	Switching routes in a multi-route input file requires updating two independent
	settings: which ``Parameters - Sensitivity_Analysis - <Route>`` table is active,
	and the ``Base`` row in ``Input files to merge``. Nothing links these two settings
	together, so it's possible to change one and forget the other. This check catches
	that specific mistake early and with a clear message, instead of letting it surface
	later as an unrelated-looking ``KeyError`` deep inside parameter resolution.

	Parameters
	----------
	inp : dict
		Input dictionary (``self.inp``).
	active_table : str
		Name of the currently active parameters table, as returned by
		`_find_active_parameters_table()`.

	Raises
	------
	ValueError
		If the active route declares an expected base file (via a
		``Route Config - <Route>`` table's ``Expected base file`` row) that does not
		match the actual ``Base`` row in ``Input files to merge``.

	Notes
	-----
	This check is opt-in, not mandatory: if a route-specific input file has no
	matching ``Route Config - <Route>`` table, no ``Expected base file`` row, or no
	``Base`` row to compare against, the check is silently skipped rather than
	treated as an error - a missing declaration is not itself a mistake.

	The declaration tables (``Route Config - <Route>``) are never suffixed with
	`` - Deactivate`` themselves; only the currently active route's declaration is ever
	looked up, so there is nothing to toggle and no risk of this check itself becoming
	a third, separately-forgettable switch.
	'''

	route = active_table[len(PARAMETERS_TABLE_ROUTE_PREFIX):]
	config_table = inp.get(CONFIG_TABLE_ROUTE_PREFIX + route)

	if config_table is None or EXPECTED_BASE_FILE_ROW not in config_table:
		return

	expected_base_file = config_table[EXPECTED_BASE_FILE_ROW]['Value']

	try:
		actual_base_file = inp['Input files to merge']['Base']['Value']
	except KeyError:
		return

	if expected_base_file != actual_base_file:
		raise ValueError(
			f"Active route '{route}' expects base file '{expected_base_file}' "
			f"(declared in '{CONFIG_TABLE_ROUTE_PREFIX}{route} > {EXPECTED_BASE_FILE_ROW}'), "
			f"but 'Input files to merge > Base > Value' is currently '{actual_base_file}'. "
			"Update one to match the other before running."
		)

class Sensitivity_Analysis:
	'''Sensitivity analysis for multiple parameters.

	Parameters
	----------
	Sensitivity_Analysis > Dependent variable > Value : str, optional
		Path (with unit) identifying which value to track as the sensitivity analysis
		output, in "{top_key > middle_key > bottom_key, unit}" notation, e.g.
		'{Dependent Variables > Levelized cost > Value, USD/kg}'.
		If the `Sensitivity_Analysis` table or the `Dependent variable` row is missing
		entirely, this silently defaults to
		'{Dependent Variables > Levelized cost > Value, USD/kg}'.
		If a `Dependent variable` value IS provided but is an invalid/non-resolving path,
		this is NOT caught - resolution fails loudly with the natural KeyError/AttributeError
		instead of silently defaulting.
	Parameters - Sensitivity_Analysis - <Route> > [...] > Name : str
		Display name for parameter, e.g. used for plot labels.
	Parameters - Sensitivity_Analysis - <Route> > [...] > Type : str
		Type of parameter values. If `Type` is 'value', provided values are
		used as is. If `Type` is 'factor', provided values are multiplied
		with base value of parameter in input file.
	Parameters - Sensitivity_Analysis - <Route> > [...] > Values : str
		Value pair to be used for sensitivity analysis. One value should
		be higher than the base value, the other should be lower.
		Specified in following format: value A; value B (order is irrelevant).
		E.g. '0.3; 10'.

	Notes
	-----
	`Sensitivity_Analysis` and `Parameters - Sensitivity_Analysis - <Route>` are separate
	tables (mirroring the existing `Monte_Carlo_Analysis`/`Parameters - Monte_Carlo_Analysis`
	and `Optimization_Analysis`/`Parameters - Optimization_Analysis` split already used
	elsewhere in this codebase). `Sensitivity_Analysis` holds module-level configuration
	(currently just `Dependent variable`).

	`Parameters - Sensitivity_Analysis - <Route>` contains the parameters which are to be
	varied in sensitivity analysis for one particular route (e.g. `PV_E`, `PC`, `PEC`).
	A single input file may contain multiple such tables side by side - one per route - so
	that switching which route is analyzed doesn't require a separate file. Exactly one must
	be active at a time; all others must have their table name suffixed with
	`` - Deactivate`` (e.g. `Parameters - Sensitivity_Analysis - PC - Deactivate`). The active
	table is located by `_find_active_parameters_table()`, which raises `ValueError` if zero
	or more than one non-deactivated table is found. First column of each table specifies path
	to parameter in input file (top key > middle key > bottom key format, e.g.
	Catalyst > Cost per kg ($) > Value). Order of parameters is not relevant. Switching routes
	also requires updating the `Base` row in `Input files to merge` to point at the matching
	base scenario file. If a `Route Config - <Route>` table declaring an `Expected base file`
	row exists for the active route, `_check_base_file_matches_active_route()` cross-checks it
	against the actual `Base` row and raises `ValueError` if they disagree; this declaration is
	optional, so input files that don't provide one are unaffected.
	'''

	def __init__(self, input_file):
		self.inp = convert_input_to_dictionary(input_file)
		self.base_case = Discounted_Cash_Flow(input_file, print_info = False)
		self.configure_dependent_variable()
		#self.results = self.perform_sensitivity_analysis()

	def configure_dependent_variable(self):
		'''Configure the dependent variable tracked as the sensitivity analysis output.

		Notes
		-----
		Missing table or missing row both silently default; an invalid path, once provided,
		still fails loudly inside `_resolve_dependent_variable()` (see note there).
		'''

		self.dependent_variable_string = self.inp.get('Sensitivity_Analysis', {}).get(
			'Dependent variable', {}).get('Value', '{Dependent Variables > Levelized cost > Value, USD/kg}')

	def perform_sensitivity_analysis(self, format_cutoff = 7):
		'''Perform sensitivity analysis.

		Parameters
		----------
		format_cutoff : int
			Length of number string above which dyanmic formatting is applied.

		Notes
		-----
		Parameters to vary are read from the single active `Parameters - Sensitivity_Analysis
		- <Route>` table, located via `_find_active_parameters_table()` (see class docstring
		for the multi-route/`` - Deactivate`` mechanism). If the active route declares an
		`Expected base file`, `_check_base_file_matches_active_route()` confirms it matches the
		actual merged-in base file before any parameters are varied. The tracked output value
		for both the varied cases and the base case is read via `_resolve_dependent_variable()`,
		using `self.dependent_variable_string` (configured from the `Sensitivity_Analysis` table,
		see `__init__`).
		'''

		sensitivity_results = {}

		active_table = _find_active_parameters_table(self.inp)
		_check_base_file_matches_active_route(self.inp, active_table)

		for key in self.inp[active_table]:
			parameters = parse_parameter(key)
			name = self.inp[active_table][key]['Name']



			sensitivity_results[name] = {}
			sensitivity_results[name]['Base'] = dynamic_value_formatting(get_by_path(self.inp, parameters),
																		 cutoff = format_cutoff)
			sensitivity_results[name]['Values'] = {}

			values = parse_parameter(self.inp[active_table][key]['Values'],
									 delimiter = ';')

			for value in values:
				input_dict = copy.deepcopy(self.inp)
				numerical_value = num(value)

				value_type = self.inp[active_table][key]['Type']

				set_by_path(input_dict, parameters, numerical_value,
							value_type = value_type)

				if self.inp[active_table][key]['Type'] == 'factor':
					sensitivity_results[name]['Base'] = '1.0x'
					shown_value = '{0}x'.format(numerical_value)
				else:

					if '%' in value:
						shown_value = value
						sensitivity_results[name]['Base'] = '{0}%'.format(dynamic_value_formatting(
																		   get_by_path(self.inp,
																					   parameters) * 100),
																			cutoff = format_cutoff)
					else:
						shown_value = dynamic_value_formatting(numerical_value, cutoff = format_cutoff)


				dcf = Discounted_Cash_Flow(input_dict, print_info = False)

				sensitivity_results[name]['Values'][shown_value] = _resolve_dependent_variable(dcf, self.dependent_variable_string)

		return sensitivity_results

	def sort_response_values(self, data):
		'''Sort response values.
		'''

		for key in data:
			values = data[key]['Values']

			low_key = min(values, key = values.get)
			high_key = max(values, key = values.get)

			data[key]['Low - Name'] = low_key
			data[key]['Low - Value'] = values[low_key]

			data[key]['High - Name'] = high_key
			data[key]['High - Value'] = values[high_key]

			del data[key]['Values']

	def plot_sensitivity_box_plot(self, ax = None, figure_lean = True,
							 height = 0.8, label_offset = 0.1,
						     lim_extra = 0.2, format_cutoff = 7,
						     plot_kwargs = {}, **kwargs):
		'''Plot sensitivity box plot.

		Parameters
		----------
		ax : matplotlib.axes, optional
			Axes object in which plot is drawn. Default is None, creating new plot.
		figure_lean : bool, optional
			If figure_lean is True, matplotlib.fig object is returned.
		height : float, optional
			Height of bars.
		label_offset : float, optional
			Offset for bar labels.
		lim_extra : float, optional
			Fractional increase of x axis limits.
		format_cutoff : int
			Length of number string above which dyanmic formatting is applied.
		plot_kwargs: dict, optional
			Dictionary containing optional keyword arguments for
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`, has priority over `**kwargs`.
		**kwargs: 
			Additional `kwargs` passed to 
			:func:`~pyH2A.Utilities.output_utilities.Figure_Lean`

		Returns 
		-------
		figure : matplotlib.fig or None
			matplotlib.fig is returned if `figure_lean` is True.

		Notes
		-----
		In plot, parameters are sorted by descending cost increase magnitude.
		'''

		self.results = self.perform_sensitivity_analysis(format_cutoff = format_cutoff)		

		data = copy.deepcopy(self.results)

		self.sort_response_values(data)

		df = pd.DataFrame.from_dict(data)
		df.sort_values(by = ['High - Value'], axis = 1, 
					   na_position = 'first', inplace = True)

		kwargs = {**{'left': 0.45, 'right': 0.99, 'bottom': 0.2, 'top': 0.95,
				     'fig_width': 7.5, 'fig_height': 4,
				     'name': 'Sensitivity_Box_Plot'}, 
				  **kwargs, **plot_kwargs}
		
		if ax is None:
			figure = Figure_Lean(**kwargs)
			ax = figure.ax		

		number_of_entries = len(df.columns)
		base_case = _resolve_dependent_variable(self.base_case, self.dependent_variable_string)

		max_value = df.loc['High - Value'].max(skipna = True)
		min_value = df.loc['Low - Value'].min(skipna = True)

		x_width = max_value - min_value
		label_offset = x_width * label_offset
		extra = x_width * lim_extra

		xlim = [min_value - extra, max_value + extra]
		ylim = [-height, number_of_entries]	

		labels = []

		for counter, key in enumerate(df):
			lower = df[key]['Low - Value']
			upper = df[key]['High - Value']

			rectangle_left = patches.Rectangle((lower, counter-height/2), 
												base_case - lower, height, 
												edgecolor = 'none', 
												facecolor = 'darkgreen')
			rectangle_right = patches.Rectangle((base_case, counter-height/2), 
												 upper - base_case, height, 
												 edgecolor = 'none', 
												 facecolor = 'darkred')

			ax.add_patch(rectangle_left)
			ax.add_patch(rectangle_right)

			ax.annotate('${:.2f}'.format(lower), xy = (lower - label_offset, counter), 
				         va = 'center', ha = 'center')
			ax.annotate('${:.2f}'.format(upper), xy = (upper + label_offset, counter), 
				         va = 'center', ha = 'center')

			labels.append('{0}\n{1}, {2}, {3}'.format(make_bold(key), 
				                                      df[key]['Low - Name'], 
				                                      df[key]['Base'], 
				                                      df[key]['High - Name']))

		ax.set_xlabel(r'Cost sensitivity / USD per kg $H_{2}$')
		ax.set_yticks(np.arange(0, number_of_entries))
		ax.set_yticklabels(labels)
		ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2)

		ax.set_xlim(xlim[0], xlim[1])
		ax.set_ylim(ylim[0], ylim[1])
		ax.plot((base_case, base_case), (ylim[0], ylim[1]), '--', color = 'black')

		if figure_lean is True:
			figure.execute()
			return figure.fig
