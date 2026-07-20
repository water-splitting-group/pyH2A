import copy
import numbers
from pyH2A.Utilities.input_modification import (convert_input_to_dictionary,
												set_by_path,
												execute_plugin)
from pyH2A.LCA.LCA import LCA

def discounted_cash_flow_function(inp, 
								  values, 
								  parameters, 
								  dependent_variable = '{Dependent Variables > Levelized Cost > Value, USD/kg}',
								  attribute = 'h2_cost',
								  plugin = None, 
								  plugin_attr = None):
	'''Wrapper function for ``Discounted_Cash_Flow``, substituting provided values 
	at specified parameter positions and returning desired attribute of 
	``Discounted_Cash_Flow`` object.

	Parameters
	----------
	inp : dict or str
		Dictionary containing input information. If `inp` is a file path, the provided 
		file is converted to a dictionary using ``convert_input_to_dictionary``.
	values : ndarray
		1D (in case of one parameter) or 2D array (in case of multiple parameters)
		containing the values which are to be used.
	parameters : ndarray
		1D or 2D array containing the parameter specifications (location within inp);
		Format: [top_key, middle_key, bottom_key].
	attribute : str, optional
		Desired attribute of ``Discounted_Cash_Flow`` object, which should be returned.
		If the attribute is `plugs`, the `.plugs` dictionary attribute is accessed, which 
		contains information of all used plugins (see `plugin` and `plugin_attr`).
		Defaults to `h2_cost`.
	plugin : str, optional
		If `attribute` is set to `plugs`, a `plugin` has to be specified, which should be 
		accessed. Furthermore, a corresponding attribute of the plugin needs to be provided,
		see `plugin_attr`.
	plugin_attr : str, optional
		If `attribute` is set to `plugs`, `plugin_attr` controls which attribute of the 
		specified `plugin` is accessed.

	Returns
	-------
	results : ndarray
		For each value (1D array) or set of values (2D array), the values are 
		substituted in inp, Discounted_Cash_Flow (dcf) is executed and the dcf 
		object is generated. Then, the requested attribute is stored in results, 
		which is finally returned.
	'''

	if isinstance(inp, str):
		inp = convert_input_to_dictionary(inp)

	results = []

	for value_set in values:
		input_dict = copy.deepcopy(inp)

		if isinstance(value_set, numbers.Number):
			set_by_path(input_dict, parameters, value_set)

		else:
			for value, parameter in zip(value_set, parameters):
				set_by_path(input_dict, parameter, value)

		dcf = Discounted_Cash_Flow(input_dict, print_info = False)

		result = getattr(dcf, attribute)

		if attribute == 'plugs':
			result = result[plugin]
			result = getattr(result, plugin_attr)

		results.append(result)

	return results

def discounted_cash_flow_function_1D(values, 
									 parameters, 
									 inp, 
									 attribute = 'h2_cost', 
									 plugin = None, 
									 plugin_attr = None):
	'''
	Wrapper function for ``Discounted_Cash_Flow``, substituting provided values
	at specified parameter positions and returning desired attribute of
	``Discounted_Cash_Flow`` object.
	

	'''

	if isinstance(inp, str):
		inp = convert_input_to_dictionary(inp)

	input_dict = copy.deepcopy(inp)

	for value, parameter in zip(values, parameters):
		set_by_path(input_dict, parameter, value)
		
	dcf = Discounted_Cash_Flow(input_dict, print_info = False)

	result = getattr(dcf, attribute)

	if attribute == 'plugs':
		result = result[plugin]
		result = getattr(result, plugin_attr)

	return result

class Discounted_Cash_Flow:
	'''Class to perform discounted cash flow analysis.

	Parameters
	----------
	input_file : str or dict
		Path to input file or dictionary containing input file data.
	print_info : bool
		Boolean flag to control if detailed info on action of plugins is printed.
	check_processing : bool
		Boolean flag to control if `check_processing` is run at the end of discounted 
		cash flow analysis, which checks if all tables in input file have been processed
		during run.

	Returns
	-------
	Discounted_Cash_Flow : object
		Discounted cash flow analysis object.

	Attributes
	----------
	h2_cost : float
		Levelized H2 cost per kg.
	contributions : dict
		Cost contributions to H2 price.
	plugs : dict 
		Dictionary containing plugin class objects used during analysis.
	lca : LCA object
		Life cycle assessment object, containing life cycle assessment results 
	
	Notes
	-----
	**Numerical inputs**

	Numbers use decimal points. Commas can be used as thousands seperator, they are removed from numbers
	during processing. the "%" can be used after a number, indicating that it will be divided by 100
	before being used. 

	**Special symbols**

	Tables in the input file are formatted using GitHub flavoured Markdown. 
	This means that "#" at the beginning of a line indicates a header.
	"|" is used to seperate columns.
	"---" is used on its own line to seperate table headers from table entries.

	Paths to locations in the input file/in self.inp are specified using ">". Paths are always composed
	of three levels: top key > middle key > bottom key.

	File name paths are specified using "/".

	In cases where multiple numbers are used in one field (e.g. during sensitivity analysis), these numbers
	are seperated using ";".

	**Order in the input file**

	Order matters in the following cases: 

	1. For a group of ``sum_all_tables()`` processed tables (sharing the specified part of their key, e.g. "Direct
	Capital Cost"), they are processed in their provided order.
	
	2. Within a table, the first column will be used to generate the "middle key" of self.inp. The order of the
	other columns is not important.

	**Input**

	Processed input cells can contain either a number or path(s) (if multiple paths are used, they have to
	be seperated by ";") to other cells. The use of process_input() (and hence, process_table(), sum_table() and 
	sum_all_tables()) also allows for the value of an input cell to be multiplied by another cell by including
	path(s) in an additiona column (column name typically "Path").

	**Workflow**

	Workflow specifies which plugins are used and in which order they are executed. Plugins can be inserted at 
	appropiate positions (Type: "plugin"). Plugins have to be located in the ./Plugins/ directory. Execution
	order is determined by the "Position" input. If the specified position is equal to an already exisiting one,
	the function/plugin will be executed after the already specified one. If multiple plugins/function are
	specified with the same position, they will be executed in the order in which they are listed in the 
	input file.

	**Plugins**

	Plugins needs to be composed of a class with the same name as the plugin file name. This class uses two inputs, 
	a discounted cash flow object (usually indicated by "self") and "print_info", which controls the printing of run time
	statements. Within the __init__ function of the class the actions of the plugins are specified.
	'''

	def __init__(self, input_file, print_info = True, check_processing = True):

		if isinstance(input_file, str):
			self.inp = convert_input_to_dictionary(input_file)
		else:
			self.inp = input_file

		self.print_info = print_info

		self.npv_dict = {}	
		self.plugs = {}

		self.workflow(self.inp, self.plugs)  # execution of all functions and plugins specified in "Workflow"

		##################### This section is to be changed (LCA should also be executed as a plugin)
		######################## And removing dcf attributes ################

		# The actual discounted cash flow analysis is performed by "Discounted_Cash_Flow_Plugin"
		# (executed as part of "Workflow" above). Its results are exposed directly on this object
		# for convenience and backwards compatibility.
		dcf_plugin = self.plugs['Discounted_Cash_Flow_Plugin']
		self.h2_cost = dcf_plugin.h2_cost
		self.contributions = dcf_plugin.contributions
		self.npv_dict.update(dcf_plugin.npv_dict)

		if 'Life Cycle Assessment' in self.inp:
			self.lca = LCA(self.inp['Life Cycle Assessment']['Matrix Folder']['Value'], self)

		###################################################################

		if check_processing is True:
			self.check_processing()


	def workflow(self, inp, plugs_dict):
		'''Executing plugins and functions for discounted cash flow.
		'''

		sorted_keys = sorted(inp['Workflow'], key = lambda x: inp['Workflow'][x]['Position'])

		for key in sorted_keys:
			execute_plugin(key, plugs_dict, print_info = self.print_info, dcf = self)

	def check_processing(self):
		'''Check whether all tables in input file were used.

		Notes
		-----
		'Workflow' and 'Display Parameters' tables are exempted.
		Furthermore, all tables that have the term 'Analysis' in their name
		are also exempted.

		'''

		exceptions = ['Workflow', 
					  'Display Parameters', 
					  'Life Cycle Assessment',
					  'Input files to merge']

		for top_key in self.inp:
			if top_key not in exceptions and 'Analysis' not in top_key:
				for middle_key in self.inp[top_key]:
					if 'Processed' not in self.inp[top_key][middle_key]:
						print('Warning: "{0} > {1}" has not been processed'.format(top_key, middle_key))

