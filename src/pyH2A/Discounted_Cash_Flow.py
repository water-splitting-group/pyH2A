from pyH2A.Utilities.input_modification import (convert_input_to_dictionary,
												execute_plugin)

from pyH2A.Utilities.functional_unit import resolve_functional_unit

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
	plugs : dict 
		Dictionary containing plugin class objects used during analysis.
	
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
		self.plugs = {}
		self.functional_unit = resolve_functional_unit(self.inp['Functional Unit']['Functional Unit']['Unit'])

		self.workflow(self.inp, self.plugs)  # execution of all functions and plugins specified in "Workflow"

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
					  'Functional Unit',
					  'Input files to merge']
		
		exception_group = 'Analysis'  # tables with this term in their name are also exempted

		for top_key in self.inp:
			if top_key not in exceptions and exception_group not in top_key:
				for middle_key in self.inp[top_key]:
					if 'Processed' not in self.inp[top_key][middle_key]:
						print('Warning: "{0} > {1}" has not been processed'.format(top_key, middle_key))

