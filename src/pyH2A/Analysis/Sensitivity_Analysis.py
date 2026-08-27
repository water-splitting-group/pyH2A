import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pyH2A.Discounted_Cash_Flow import Discounted_Cash_Flow
from pyH2A.Utilities.input_modification import num, convert_input_to_dictionary, parse_parameter, parse_path_with_unit, get_by_path, set_by_path
from pyH2A.Utilities.output_utilities import make_bold, Figure_Lean, dynamic_value_formatting

# NOTE: this is a local, per-module fix; the same dead-attribute pattern may exist
# elsewhere in the Analysis package - see tracked issue if one exists.
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
	Parameters - Sensitivity_Analysis > [...] > Name : str
		Display name for parameter, e.g. used for plot labels.
	Parameters - Sensitivity_Analysis > [...] > Type : str
		Type of parameter values. If `Type` is 'value', provided values are
		used as is. If `Type` is 'factor', provided values are multiplied
		with base value of parameter in input file.
	Parameters - Sensitivity_Analysis > [...] > Values : str
		Value pair to be used for sensitivity analysis. One value should
		be higher than the base value, the other should be lower.
		Specified in following format: value A; value B (order is irrelevant).
		E.g. '0.3; 10'.

	Notes
	-----
	`Sensitivity_Analysis` and `Parameters - Sensitivity_Analysis` are separate tables
	(mirroring the existing `Monte_Carlo_Analysis`/`Parameters - Monte_Carlo_Analysis`
	and `Optimization_Analysis`/`Parameters - Optimization_Analysis` split already used
	elsewhere in this codebase). `Sensitivity_Analysis` holds module-level configuration
	(currently just `Dependent variable`).

	`Parameters - Sensitivity_Analysis` contains the parameters which are to be varied in
	sensitivity analysis for one particular route (e.g. `PV_E`, `PC`, `PEC`). Each route is
	a separate input file, merging in that route's own base scenario file via the `Base` row
	in `Input files to merge`. First column of the table specifies path to parameter in input
	file (top key > middle key > bottom key format, e.g. Catalyst > Cost per kg ($) > Value).
	Order of parameters is not relevant.

	Display label and unit for the tracked dependent variable are read directly from the
	`Dependent variable` row itself (`Value` for the path/unit, `Label` for the display
	name) - the row is self-describing, no shared or per-module config dict is consulted.
	See `configure_dependent_variable()`.
	'''

	def __init__(self, input_file):
		self.inp = convert_input_to_dictionary(input_file)
		self.base_case = Discounted_Cash_Flow(input_file, print_info = False)
		self.configure_dependent_variable()

	def configure_dependent_variable(self):
		'''Configure the dependent variable tracked as the sensitivity analysis output.

		Notes
		-----
		Missing table or missing row both silently default; an invalid path, once provided,
		still fails loudly inside `_resolve_dependent_variable()` (see note there). Display
		label and unit are read directly from the `Dependent variable` row itself (`Value`
		for the path/unit, `Label` for the display name) - the row is self-describing, no
		shared or per-module config dict is consulted. A missing `Label` column falls back
		to `None`, same as a missing row entirely, and callers fall back to today's
		hardcoded default display text.
		'''

		dependent_variable_row = self.inp.get('Sensitivity_Analysis', {}).get('Dependent variable', {})

		self.dependent_variable_string = dependent_variable_row.get(
			'Value', '{Dependent Variables > Levelized cost > Value, USD/kg}')
		self.dependent_variable_label = dependent_variable_row.get('Label')

		_, self.dependent_variable_unit = parse_path_with_unit(self.dependent_variable_string)

	def perform_sensitivity_analysis(self, format_cutoff = 7):
		'''Perform sensitivity analysis.

		Parameters
		----------
		format_cutoff : int
			Length of number string above which dynamic formatting is applied.

		Returns
		-------
		sensitivity_results : dict
			Per-parameter results: `Base` (formatted base-case value) and `Values`
			(dict mapping each tested value's shown label to its resolved dependent
			variable value).

		Notes
		-----
		Parameters to vary are read from the `Parameters - Sensitivity_Analysis` table. The
		tracked output value for both the varied cases and the base case is read via
		`_resolve_dependent_variable()`, using `self.dependent_variable_string` (configured
		from the `Sensitivity_Analysis` table, see `__init__`).
		'''

		sensitivity_results = {}

		for key in self.inp['Parameters - Sensitivity_Analysis']:
			parameters = parse_parameter(key)
			name = self.inp['Parameters - Sensitivity_Analysis'][key]['Name']



			sensitivity_results[name] = {}
			sensitivity_results[name]['Base'] = dynamic_value_formatting(get_by_path(self.inp, parameters),
																		 cutoff = format_cutoff)
			sensitivity_results[name]['Values'] = {}

			values = parse_parameter(self.inp['Parameters - Sensitivity_Analysis'][key]['Values'],
									 delimiter = ';')

			for value in values:
				input_dict = copy.deepcopy(self.inp)
				numerical_value = num(value)

				value_type = self.inp['Parameters - Sensitivity_Analysis'][key]['Type']

				set_by_path(input_dict, parameters, numerical_value,
							value_type = value_type)

				if self.inp['Parameters - Sensitivity_Analysis'][key]['Type'] == 'factor':
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

		Parameters
		----------
		data : dict
			Per-parameter sensitivity results, as returned by
			`perform_sensitivity_analysis()`. Mutated in place: each parameter's
			`Values` dict is replaced with `Low - Name`/`Low - Value`/
			`High - Name`/`High - Value` entries.
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
							 height = 0.8,
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
		lim_extra : float, optional
			Fractional increase of x axis limits.
		format_cutoff : int
			Length of number string above which dynamic formatting is applied.
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

		Value annotations use a fixed pixel offset from their bar, not a fraction of
		the data range, so spacing stays correct across widely varying bar widths.
		On rows whose bar is very narrow relative to the chart's overall value range,
		the low-value annotation can still visually collide with the y-axis parameter
		label - known, open issue; see comment above `kwargs` for what was tried.
		'''

		self.results = self.perform_sensitivity_analysis(format_cutoff = format_cutoff)		

		data = copy.deepcopy(self.results)

		self.sort_response_values(data)

		df = pd.DataFrame.from_dict(data)
		df.sort_values(by = ['High - Value'], axis = 1, 
					   na_position = 'first', inplace = True)

		# left=0.5 (up from 0.45): confirmed via real measurement to eliminate the
		# pre-existing y-axis label clipping past the figure's left edge, at every
		# fig_width tested. It does not (and structurally cannot) resolve the separate,
		# still-open issue of the low-value annotation colliding with the y-axis label
		# on the narrowest-spread rows - left/fig_width/lim_extra were all tested and
		# ruled out for that; it needs a different mechanism (e.g. shrinking the
		# annotation text itself), not attempted here.
		kwargs = {**{'left': 0.5, 'right': 0.99, 'bottom': 0.2, 'top': 0.95,
				     'fig_width': 7.5, 'fig_height': 4,
				     'name': 'Sensitivity_Box_Plot'},
				  **kwargs, **plot_kwargs}
		
		if ax is None:
			figure = Figure_Lean(**kwargs)
			ax = figure.ax		

		number_of_entries = len(df.columns)
		base_case = _resolve_dependent_variable(self.base_case, self.dependent_variable_string)

		if self.dependent_variable_label is None:
			xlabel = r'Cost sensitivity / USD per kg $H_{2}$'
			value_format = '${0:.2f}'.format
		else:
			xlabel = '{0} / {1}'.format(self.dependent_variable_label, self.dependent_variable_unit)
			value_format = lambda value: '{0:.2f} {1}'.format(value, self.dependent_variable_unit)

		max_value = df.loc['High - Value'].max(skipna = True)
		min_value = df.loc['Low - Value'].min(skipna = True)

		x_width = max_value - min_value
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

			# Fixed pixel offset (not a fraction of the data range), so spacing stays
			# correct regardless of how much bar widths vary across rows.
			ax.annotate(value_format(lower), xy = (lower, counter), xytext = (-8, 0),
				         textcoords = 'offset points', va = 'center', ha = 'right')
			ax.annotate(value_format(upper), xy = (upper, counter), xytext = (8, 0),
				         textcoords = 'offset points', va = 'center', ha = 'left')

			labels.append('{0}\n{1}, {2}, {3}'.format(make_bold(key), 
				                                      df[key]['Low - Name'], 
				                                      df[key]['Base'], 
				                                      df[key]['High - Name']))

		ax.set_xlabel(xlabel)
		ax.set_yticks(np.arange(0, number_of_entries))
		ax.set_yticklabels(labels)
		ax.grid(color = 'grey', linestyle = '--', linewidth = 0.2)

		ax.set_xlim(xlim[0], xlim[1])
		ax.set_ylim(ylim[0], ylim[1])
		ax.plot((base_case, base_case), (ylim[0], ylim[1]), '--', color = 'black')

		if figure_lean is True:
			figure.execute()
			return figure.fig
