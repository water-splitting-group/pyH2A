from functools import lru_cache, reduce
import importlib.resources
from importlib import import_module
from pathlib import Path
import ast
import operator
import numpy as np

from pyH2A.Utilities.Unit_Handler import Quantity
from pyH2A.Utilities.Unit_Handler.config import DIMENSIONS

def import_plugin(plugin_name, plugin_module):
	'''Importing module.

	Parameters
	----------
	plugin_name : str
		Name of module.
	plugin_module : bool, optional
		Flag to differentiate between plugins and analysis modules. If `True`,
		module is imported from `Plugins.` directory. If `False`, it is
		imported from `Analysis.` directory.

	Returns
	-------
	plugin_class:
		Class from imported module.

	Notes
	-----
	Module `plugin_name` is imported. It is assumed that the module contains 
	a class with the same name as `plugin_name`
	'''

	if plugin_module is True:
		prefix = 'pyH2A.Plugins.'
	else:
		prefix = 'pyH2A.Analysis.'

	plugin = import_module(prefix + plugin_name)
	plugin_class = getattr(plugin, plugin_name)

	return plugin_class

def execute_plugin(plugin_name, plugs_dict, plugin_module = True, 
				   nested_dictionary = False, **kwargs):
	'''Executing module.

	Parameters
	----------
	plugin_name : str
		Name of module.
	plugs_dict : dict
		Dictionary to store class object generated from module.
	plugin_module : bool, optional
		Flag to differentiate between plugins and analysis modules. If `True`,
		module is imported from `Plugins.` directory. If `False`, it is
		imported from `Analysis.` directory.
	nested_dictioanry : bool, optional
		If `True`, a sub dictionary is created in `plugs_dict`, where the
		class object is stored.
	**kwargs:
		Keyword arguments passed to class within module.

	Returns 
	-------
	plugin_object:
		Class objected generated from module.

	Notes
	-----
	Module `plugin_name` is imported. It is assumed that the module contains 
	a class with the same name as `plugin_name`. An instance of this class is created
	using `**kwargs`. The class object is then stored in `plugs_dict`.
	'''

	plugin_class = import_plugin(plugin_name, plugin_module)
	plugin_object = plugin_class(**kwargs)

	if nested_dictionary is True:
		plugs_dict[plugin_name] = {}
		plugs_dict[plugin_name]['Module'] = plugin_object
	else:
		plugs_dict[plugin_name] = plugin_object

	return plugin_object

def check_for_meta_module(key):
	'''Checks if `key` is a meta module that is to be executed.

	Notes
	-----
	Meta module is identified by checking if `key` contains the substring
	'Analysis' and does not contain any of the substrings in `exceptions`.
	'''

	exceptions = ['Parameters', 'Methods', 'Arguments', 'Deactivate']
	indicators = ['Analysis']

	if any(exception in key for exception in exceptions):
		return False
	elif any(indicator in key for indicator in indicators):
		return True
	else:
		return False

def file_import(file_name, mode = 'rb', return_path = False):
	'''Importing package file or file at arbitrary path and returning typing.TextIO
	instance.

	Parameters
	----------
	file_name : str
		Path to file to be read. Can be either a regular path or a path
		of the form `package.subdirectory~file_name` to refer to a file 
		in the pyH2A installation.
	mode : str
		Mode for file read. Can be either `r` or `rb`. In case of `r`, 
		a `typing.TextIO` instance is returned. In case of `rb` a 
		`typing.BinaryIO` instance is returned.

	Returns
	-------
	output : typing.BinaryIO or typing.TextIO instance
		Whether a `typing.BinaryIO` or `typing.TextIO` is returned depends 
		on `mode`.
	'''

	if '~' in file_name:
		package, file = file_name.split('~')
		if 'b' in mode:
			output = importlib.resources.open_binary(package, file)
		else:
			output = importlib.resources.open_text(package, file)

		with importlib.resources.path(package, file) as path:
			output_path = path

	else:
		output_path = Path(file_name)
		output = open(output_path, mode = mode)


	if return_path:
		return output_path
	else:
		return output

@lru_cache(maxsize = 1024)
def read_textfile(file_name, delimiter, mode = 'rb', **kwargs):
	'''Wrapper for genfromtxt with lru_cache for repeated reads of the same file.

	Parameters
	----------
	file_name : str
		Path to file.
	delimiter : str
		Delimiter used in file.
	**kwargs:
		Keyword arguments passed to ``numpy.genfromtxt()``.

	Returns
	-------
	data : ndarray
		Array containing read data.
	'''

	data = np.genfromtxt(file_import(file_name, mode = mode), delimiter = delimiter, **kwargs)

	return data

def num(s):
	'''Converting string to either an int, float, or, if neither is possible, returning the string.

	Parameters
	----------
	s : str
		String to be converted to a number.

	Returns
	-------
	num : int, float or str
		String converted to int, float or str.

	Notes
	-----
	Input strings can contain commas as thousands seperators, which will be removed if the string 
	is otherwise a valid number (float or int).
	If the input string ends with a "%" sign, it will be converted to a number divided by 100.
	'''

	if s[-1] == '%': #String ends with '%', trying to convert percentage into regular value
		try:
			return num(s[:-1])/100.
		except TypeError:
			return str(s)
	else:
		try:
			return int(s.replace(',', ''))
		except ValueError:
			try:
				return float(s.replace(',', ''))
			except ValueError:
				return str(s)

def convert_file_to_dictionary(file):
	'''Convert provided text file into dictionary. Text file has to follow GitHub 
	flavoured Markdown style.

	Parameters
	----------
	file : typing.TextIO
		typing.TextIO instance of file to be converted.

	Returns
	-------
	inp : dict
		Dictionary containing converted data from file.

	Notes
	-----
	Table format:
	
	# Table A name

	First | Second | ...
	
	--- | --- | ---
	
	Entry A | value 1 | ...
	
	Entry B | value 2 | ...

	# Table B name

	...
	
	The table name is used as `top_key`, the entries within the first column
	are used as `middle_key` and the names of the other columns are used as 
	`bottom key`. E.g. {'Table A name': {'Entry A' : {'Second': 'value 1'}}}
	'''

	inp = {}
	table = False
	header = False

	for line in file:
		
		if line[0] == '#':
			variable_name = line.strip(' #\n')
			inp[variable_name] = {}
			header = False

		if line.strip(' ') == '\n':
			table = False
			header = True

		if line[0] == '-':
			table = True
			header = False

		if header is True and line.strip(' ') != '\n':
			header_entries = line.split('|')

		if table is True and line[0] != '-':
			table_entries = line.split('|')
			inp[variable_name][table_entries[0].strip(' ')] = {}

			for i in zip(header_entries[1:], table_entries[1:]):
				header_entry = i[0].strip(' \n')

				if i[1].strip(' \n') == '':
					table_entry = 'n/a'
				else:
					table_entry = num(i[1].strip(' \n'))

				inp[variable_name][table_entries[0].strip(' ')][header_entry] = table_entry 

	file.close()

	return inp

def convert_dict_to_kwargs_dict(dictionary, middle_key = 'Value'):
	'''Converting dictionary generated by ``convert_file_to_dictionary()``
	to a dictionary that can be used to provide keyword arguments.

	Parameters
	----------
	dictionary : dict
		Dictionary to be converted.
	middle_key : str, optional
		Middle key which is present in input dictionary. This key 
		is removed in the process.

	Returns
	-------
	output : dict
		Dictionary suitable to provide keyword arguments.
	'''

	output = {}

	for key, value in dictionary.items():
		try:
			output[key] = ast.literal_eval(str(value[middle_key]))
		except (ValueError, SyntaxError):
			output[key] = value[middle_key]

	return output

def merge(a, b, path=None, update=True):
	'''Deep merge two dictionaries, with b having priority over a'''

	if path is None: path = []

	for key in b:
		if key in a:
			if isinstance(a[key], dict) and isinstance(b[key], dict):
				merge(a[key], b[key], path + [str(key)])
			elif a[key] == b[key]:
				pass # same leaf value
			elif isinstance(a[key], list) and isinstance(b[key], list):
				for idx, val in enumerate(b[key]):
					a[key][idx] = merge(a[key][idx], b[key][idx], path + [str(key), str(idx)], update=update)
			elif update:
				a[key] = b[key]
			else:
				raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
		
		else:
			a[key] = b[key]
	return a

def convert_input_to_dictionary(file):
	'''
	Read markdown input file into dictionary and merge
	one level of external base-input files.

	Parameters
	----------
	file : str
		Path to input file.

	Returns
	-------
	inp : dict
		Input dictionary.

	Notes
	-----
	If a ``Input files to merge`` table exists, each row's ``Value`` is treated as a
	referenced file path. Referenced files are loaded in listed order and merged
	into the current dictionary. Files listed first have higher priority. 

	Only first-level references from the main input file are resolved. Nested
	``Input files to merge`` tables inside referenced files are not followed.
 	'''
 

	inp = convert_file_to_dictionary(file_import(file, mode = 'r'))

	if 'Input files to merge' in inp:

		for _, row in inp['Input files to merge'].items():
			raw_file = row['Value']
			inp_file = convert_file_to_dictionary(file_import(raw_file, mode = 'r'))
			inp = merge(inp_file, inp)

	return inp

def deep_get(dictionary, *keys, default=None):
	'''Get a value from a nested dictionary using a sequence of keys. If any key is not found, return default.'''

	for key in keys:
		if not isinstance(dictionary, dict):
			return default
		
		dictionary = dictionary.get(key)

		if dictionary is None:
			return default
		
	return dictionary

def get_by_path(root, items):
	'''Access a nested object in `root` by item sequence.'''
	return reduce(operator.getitem, items, root)

def set_by_path(root, items, value, value_type = 'value'):
	'''Set a value in a nested object in root by item sequence.

	Notes
	-----
	Existing value is either multiplied by provided one 
	(value_type = factor) or is replaced by provided one.
	In-place replacement, should only be used on deep copy of self.inp dictionary
	'''
	if value_type == 'factor':
		get_by_path(root, items[:-1])[items[-1]] *= value
	else:
		get_by_path(root, items[:-1])[items[-1]] = value

def insert(class_object, top_key, middle_key, bottom_key, value, name, 
		   print_info = True, add_processed = True, insert_path = True, path_key = 'Path'):
	'''Insert function used in plugins. 

	Parameters
	----------
	class_object: Discounted_Cash_Flow object
		Dicounted_Cash_Flow object with .inp attribute, which is modified.
	top_key : str
		Top key.
	middle_key : str
		Middle key.
	bottom_key : str
		Bottom key.
	Value : int, float, str or ndarray
		Value inserted at top_key > middle_key > bottom_key position.
	name : str
		Name of plugin performing insertion.
	print_info : bool, optional
		Flag to control if information on action of ``insert()`` is printed.
	add_processed : bool, optional
		Flag to control if 'Processed' key is added.
	insert_path : bool, optional
		Flag to control if 'Path' key is added.
	path_key : str, optional
		Key for the path entry.

	Notes
	-----
	`inp` attribute of `class_object` is modified by inserting `value` at the position defined
	by `top_key > middle_key > bottom_key`.
	If there already is a value at this position, it will be overwritten. In this case, the 
	'Path' entry will be set to 'None' to avoid issues if value at this position already 
	existed and had a path specified.
	If there is not already a value at this position, it will be created
	`name` is the name of plugin using `insert` for insertion.
	If `print_info` is True, action of `insert` will be printed.
	'''

	try:
		class_object.inp[top_key][middle_key][bottom_key] = value
		if insert_path is True: 
			class_object.inp[top_key][middle_key][path_key] = 'None' # setting path to "None" to avoid processing
		if print_info is True: print("'{0} > {1} > {2}' is being overwritten by {3}".format(top_key, 
																							middle_key, 
																							bottom_key, 
																							name))

	except KeyError:
		try:
			class_object.inp[top_key][middle_key] = {}
			class_object.inp[top_key][middle_key][bottom_key] = value
			if print_info is True: print("'{0} > {1}' is being created by {2}".format(top_key, 
																					  middle_key, 
																					  name))

		except KeyError:
			class_object.inp[top_key] = {}
			class_object.inp[top_key][middle_key] = {}
			class_object.inp[top_key][middle_key][bottom_key] = value
			if print_info is True: print("'{0}' is being created by {1}".format(top_key, name))

	if add_processed is True:
		class_object.inp[top_key][middle_key]['Processed'] = 'Yes'

def parse_parameter(key, delimiter = '>'):
	'''Provided `key` is split at delimiter(s) and returned as cleaned array'''

	key = str(key)

	path_components = key.split(delimiter)
	output = []

	for i in path_components:
		output.append(i.strip(' '))
		
	return output

def reverse_parameter_to_string(parameter):
	'''Reverts processed parameter list to string.'''

	output = str(parameter[0])

	for item in parameter[1:]:
		output += f' > {item}'

	return output

def sum_table_quantity(dictionary, 
					   top_key, 
					   bottom_key,
			   		   base_unit = None,
					   insert_total = False,
					   middle_key_total_insertion = 'Summed Total',
					   bottom_key_insertion = 'Value',
					   class_object = None,
					   print_info = True):
	'''For the provided `dictionary`, all entries in dictionary[top_key] are summed.

	Parameters
	----------
	dictionary : dict
		Dictionary within which function operates.
	top_key : str
		Top key.
	bottom_key : str, ndarray or list
		Bottom key.
	base_unit : str, optional
		Base unit which is used for the creation of the output quantity object.	
	insert_total : bool, optional
		If `insert_total` is True, the total of each table is inserted in the
		respective table.
	middle_key_total_insertion : str, optional
		Middle key used for insertion of total.
	bottom_key_insertion : str, optional
		Bottom key used for insertion of total.
	class_object : Discounted_Cash_Flow object
		Discounted_Cash_Flow object whose .inp attribute is modified.
	print_info : bool, optional
		Flag to control if information on action of ``insert()`` is printed.

	Returns
	-------
	value : Quantity
		Summed value across all entries in dictionary[top_key] at position bottom_key.
	'''

	value = 0.

	for key in dictionary[top_key]:
		quantity = dictionary[top_key][key][bottom_key]
		value += quantity.base_value

	value = Quantity(value, base_unit)

	if insert_total is True:
		insert(class_object, top_key, middle_key_total_insertion, bottom_key_insertion, 
					    value, __name__, print_info = print_info)

	return value

def sum_all_tables_quantity(dictionary, 
							table_group, 
							insert_total_table_group = False,
				   			class_object = None, 
							base_unit = None,
							middle_key_total_insertion = 'Summed Total', 
							middle_key_total_group_insertion = 'Summed Group Total',
							middle_key_contributions_insertion = 'Contributions',
				   			bottom_key_insertion = 'Value', 
							print_info = True, 
							return_contributions = False):
	'''
	Sums all sums of tables within table group (assumes that sum_all_tables_quantity has already been applied to all tables in table group, 
	so that the dictionary[top_key][middle_key_total_insertion][bottom_key_insertion] position of each table contains a Quantity object 
	representing the sum of that table).
	
	Parameters
	----------
	dictionary : dict
		Dictionary within which function operates.
	table_group : str
		String to identify table group. If a dictionary key contains the `table_group`
		substring it is part of the table group.
	insert_total_table_group : bool, optional
		If `insert_total_table_group` is True, the total of across all tables
		is inserted in class_object.inp at table_group > middle_key_total_group_insertion > bottom_key_insertion.
	class_object : Discounted_Cash_Flow object
		Discounted_Cash_Flow object whose .inp attribute is modified.
	base_unit : str, optional
		Base unit which is used for the creation of the output quantity object.
	middle_key_total_insertion : str, optional
		Middle key, in which the total of each table was previously inserted by ``sum_table_quantity()``.
	middle_key_total_group_insertion : str, optional
		Middle key used for insertion of total across all tables in table group.
	middle_key_contributions_insertion : str, optional
		Middle key used for insertion of contributions breakdown.
	bottom_key_insertion : str, optional
		Bottom key, in which the total of each table was previously inserted by ``sum_table_quantity()``. 
		Also used for insertion of total across all tables in table group and contributions breakdown.
	print_info : bool, optional
		Flag to control if information on action of ``insert()`` is printed.
	return_contributions : bool, optional
		Flag to control if a dictionary with contributions breakdown (for use 
		in cost ``Cost_Contributions_Analysis`` module) is returned and inserted in class_object.inp at 
		table_group > middle_key_contributions_insertion > bottom_key_insertion.

	Notes
	-----
	The contributions of each table in table_group are stored in `contributions` dictionary, 
	which is returned if `return_contributions` is set to True. Dictionary is structured so 
	that it can be provided to "Cost_Contributions_Analysis" class to generate a cost breakdown plot.
	'''

	total = 0.

	contributions = {}
	contributions['Data'] = {}
	contributions['Table Group'] = table_group
	
	for key in dictionary:

		if table_group in key:
			value = dictionary[key][middle_key_total_insertion][bottom_key_insertion]
			total += value.base_value
			contributions['Data'][key] = value

	total = Quantity(total, base_unit)
	contributions['Total'] = total

	# Inserting total sum across all tables in table group
	if insert_total_table_group is True:
		insert(class_object, table_group, middle_key_total_group_insertion, bottom_key_insertion, 
							total, __name__, print_info = print_info)

	# Inserting contributions breakdown and returning contributions breakdown dictionary if return_contributions is True
	if return_contributions is True:
		insert(class_object, table_group, middle_key_contributions_insertion, bottom_key_insertion, 
							contributions, __name__, print_info = print_info)
		return total, contributions
	
	else:
		return total

def hourly_to_daily_power(array):
	'''Convert array of hourly power values to array of daily power values.'''
		
	if len(array) % 24 != 0:
		raise ValueError("Data length is not a multiple of 24")
	
	daily_array = array.reshape(-1, 24)
	daily_array = daily_array.sum(axis=1)	

	return daily_array
	
def daily_to_yearly_power(dictionary):
	'''Convert dictionary with daily power values to array with yearly power values.
	'''

	stacked_array = np.vstack(list(dictionary.values()))
	yearly_power = stacked_array.sum(axis = 1)

	return yearly_power

def retrieve_base_unit(table_dictionary):
	'''Retrieve dimension of unit from input dictionary.
	Return base unit of retrieved dimension using DIMENSIONS from unit handler.
	'''

	for row in table_dictionary.values():
		if isinstance(row, dict):
			for key, value in row.items():
				if "Unit" in key and isinstance(value, dict):

					dimension = value.get("dimension")
					return DIMENSIONS[dimension]["base"]



def daily_to_yearly_power_quantity(dictionary):
	'''Convert dictionary with daily power values to array with yearly power values.
	(when values are Quantity objects)
	'''

	stacked_array = np.vstack([entry.base_value for entry in dictionary.values()])

	yearly_power = stacked_array.sum(axis = 1)
	base_unit = dictionary[list(dictionary.keys())[0]].base_unit

	return Quantity(yearly_power, base_unit)

class Inp_Wrapper:
	def __init__(self, input_dict):
		self.inp = input_dict