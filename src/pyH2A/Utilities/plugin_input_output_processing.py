from pathlib import Path
from importlib import import_module

import numpy as np

from pyH2A.Utilities.input_modification import (insert, convert_input_to_dictionary, convert_file_to_dictionary,
												file_import, check_for_meta_module, import_plugin, merge,
												parse_parameter, identify_bottom_keys)
from pyH2A.Utilities.plugin_specification import instantiate_plugin_for_docs, iter_spec_rows, iter_bottom_entries
from pyH2A.Utilities.constants import (WILDCARD_MARKER, TYPE_KEY, OPTIONS_KEY, DIMENSION_KEY,
									   DESCRIPTION_KEY)

def is_parameter_or_output(line, spaces_for_tab = 4, spaces_cutoff = 5):
	'''Detection of parameters and output values in line based on presence of more than `spaces_cuttoff`
	spaces (tabs are converted to four spaces).
	'''

	line = line.replace('\t', ' ' * spaces_for_tab) # replace tabs with given number of spaces
	return line[:spaces_cutoff] != ' ' * spaces_cutoff

def process_single_line(line, output_dict, origin, variable_string, **kwargs):
	'''Process single line to extract parameter/output information and comments'''

	if is_parameter_or_output(line, **kwargs): # is a line containing parameter/output information
		complete_string = line.split(':')
		variable_string = complete_string[0].strip(', \t')
		variable_type = complete_string[1].strip(', \t')

		output_dict[variable_string] = {'Type': variable_type, 'Origin': origin}

		return variable_string

	else:  # is a line containing comment for parameter/output
		comment = line.strip(' \t')
		bottom_key = parse_parameter(variable_string)[-1]
		comment_string = f'Comment {bottom_key}'

		if comment_string in output_dict[variable_string]:
			output_dict[variable_string][comment_string] += ' ' + comment
		else:
			output_dict[variable_string][comment_string] = comment

		return variable_string

def extract_input_output_from_docstring(target, **kwargs):
	'''Convert docstring to structured dictionary.'''

	doc_string = target.__doc__.split('\n')

	parameters_dict = {}
	output_dict = {}

	parameters = False
	output = False
	variable_string = None

	for counter, line in enumerate(doc_string):

		if '---' in line and 'Parameters' in doc_string[counter-1]:
			parameters = True

		if '---' in line and 'Returns' in doc_string[counter-1]:
			parameters = False
			output = True
	
		if line.strip(' \t') == '':
			parameters = False
			output = False

		if parameters and '---' not in line:
			variable_string = process_single_line(line, parameters_dict, 
												  target.__name__, variable_string, 
												  **kwargs)

		if output and '---' not in line:
			variable_string = process_single_line(line, output_dict, 
												  target.__name__, variable_string, 
												  **kwargs)

	plugin_dict = {'Parameters': parameters_dict, 'Output': output_dict}

	return plugin_dict

def convert_inp_to_requirements(dictionary, path = None):
	'''Convert inp dictionary structure to requirements dictionary structure.'''
	
	output = {}

	for top_key, top_item in dictionary.items():
		for middle_key, middle_item in top_item.items():
			for bottom_key, bottom_item in middle_item.items():

				path = f'{top_key} > {middle_key} > {bottom_key}'
				output[path] = {'Entry': bottom_item, 'Origin': 'Input'}

	return output

_TYPE_NAMES = {int: 'int', float: 'float', str: 'str', bool: 'bool',
			   dict: 'dict', list: 'list', tuple: 'tuple', np.ndarray: 'ndarray'}

def convert_types_to_string(types):
	'''Convert set of types from a plugin specification (e.g. `{int, float}`)
	to string (e.g. `"int or float"`), using a fixed order.'''

	if isinstance(types, type):
		types = {types}

	ordered = [t for t in _TYPE_NAMES if t in types] + [t for t in types if t not in _TYPE_NAMES]

	return ' or '.join(_TYPE_NAMES.get(t, getattr(t, '__name__', str(t))) for t in ordered)

def get_unit_key(row_dict, value_key):
	'''Get unit key paired with `value_key` in `row_dict` (`None` if there is no unit key).'''

	keys = identify_bottom_keys(row_dict)[value_key]
	unit_key = keys.get('Unit')

	return unit_key if unit_key != value_key else None

def join_path(top_key, middle_key, bottom_key):
	'''Join keys to path string (`top > middle > bottom`). The wildcard marker (`<...>`)
	is replaced by the `[...]` placeholder used in input file templates, since its `>`
	would otherwise interfere with `parse_parameter`.'''

	keys = [key.replace(WILDCARD_MARKER, '[...]') for key in (top_key, middle_key, bottom_key)]

	return ' > '.join(keys)

def extract_input_output_from_specification(input_dict, output_dict, origin):
	'''Convert plugin `input_dict`/`output_dict` to structured dictionary.

	Parameters
	----------
	input_dict : dict
		Input specification of plugin (see input resolver).
	output_dict : dict
		Output specification of plugin (see output inserter).
	origin : str
		Name of plugin.

	Returns
	-------
	plugin_dict : dict
		Dictionary with `Parameters` and `Output`, using the same structure 
		as `extract_input_output_from_docstring`. Parameters additionally contain 
		the unit key and dimension of a value (if present).
	'''

	parameters_dict = {}
	output_dict_processed = {}

	for top_key, middle_key, row_dict in iter_spec_rows(input_dict, f'{origin} input_dict'):
		description = row_dict.get(DESCRIPTION_KEY, '')

		for bottom_key, value_spec, optional in iter_bottom_entries(row_dict):
			variable_type = convert_types_to_string(value_spec.get(TYPE_KEY, set()))

			if OPTIONS_KEY in value_spec:
				variable_type += ' {{{0}}}'.format(', '.join(repr(o) for o in sorted(value_spec[OPTIONS_KEY])))

			if optional:
				variable_type += ', optional'

			path = join_path(top_key, middle_key, bottom_key)
			entry = {'Type': variable_type, 'Origin': origin, 'Types': value_spec.get(TYPE_KEY, set())}

			unit_key = get_unit_key(row_dict, bottom_key)
			if unit_key is not None:
				entry['Unit'] = {'Key': unit_key, 
								 'Dimension': row_dict[unit_key].get(DIMENSION_KEY, '')}

			if description:
				entry[f'Comment {bottom_key}'] = description

			parameters_dict[path] = entry

	for top_key, middle_key, row_dict in iter_spec_rows(output_dict, f'{origin} output_dict'):
		for bottom_key, value_spec, _ in iter_bottom_entries(row_dict):
			path = join_path(top_key, middle_key, bottom_key)
			output_dict_processed[path] = {'Type': convert_types_to_string(value_spec.get(TYPE_KEY, set())), 
										   'Origin': origin,
										   'Types': value_spec.get(TYPE_KEY, set())}

	plugin_dict = {'Parameters': parameters_dict, 'Output': output_dict_processed}

	return plugin_dict

def get_plugin_specification(plugin_name):
	'''Get `input_dict` and `output_dict` of plugin without running it.

	Notes
	-----
	Plugins either define `input_dict`/`output_dict` at module level (see Plugin Guide)
	or set them up in `_set_up` (in this case, plugin is instantiated with `run = False`,
	see `pyH2A.Utilities.plugin_specification.instantiate_plugin_for_docs`).
	'''

	module = import_module('pyH2A.Plugins.' + plugin_name)

	if hasattr(module, 'input_dict') and hasattr(module, 'output_dict'):
		return module.input_dict, module.output_dict

	plugin = instantiate_plugin_for_docs(plugin_name)

	return plugin.input_dict, plugin.output_dict

class Generate_Template_Input_File:
	'''Generate input file template from a minimal input file.

	Parameters
	----------
	input_file_stub : str
		Path to input file containing workflow and analysis specifications.
	output_file : str
		Path to file where input template is to be written.
	origin : bool, optional
		Include origin of each requested input parameter in input template
		file ("requested by" information).
	comment : bool, optional
		Include comments for each requested input parameter (additional
		information on parameter).

	Returns
	-------
	Template : object
		Template object which contains information on requirements and
		output. Input template is written to specified output file.

	Notes
	-----
	Input files referenced in the ``Input files to merge`` table of the input
	file stub (e.g. ``pyH2A.Config~Defaults_TEA.md``) are merged into the stub.
	Their workflow is used and the parameters they provide are not requested
	in the template.

	Requirements and outputs of plugins are read from their ``input_dict`` 
	and ``output_dict`` specifications. Analysis modules are read from their
	docstrings.
	'''

	def __init__(self, input_file_stub, output_file, 
				 origin = False, comment = False):
		if isinstance(input_file_stub, str):
			self.inp_stub = convert_input_to_dictionary(input_file_stub)
			inp_stub_unmerged = convert_file_to_dictionary(file_import(input_file_stub, mode = 'r'))
		else:
			self.inp_stub = input_file_stub
			inp_stub_unmerged = input_file_stub

		self.inp = {}

		for key in self.inp_stub['Workflow']:
			self.inp_stub['Workflow'][key].setdefault('Type', 'plugin')

		post_workflow_position = self.get_post_workflow_position()
		self.get_analysis_modules(post_workflow_position)

		self.sorted_keys = sorted(self.inp_stub['Workflow'], 
								  key = lambda x: self.inp_stub['Workflow'][x]['Position'])

		self.requirements = {}
		self.output = {}

		self.provided_inp = convert_inp_to_requirements(self.inp_stub)
		self.generate_requirements()
		self.convert_requirements_to_inp(insert_origin = origin, insert_comment = comment)

		self.inp = merge(self.inp, inp_stub_unmerged)

		template_file = Template_File(self.inp)
		template_file.write_template_file(output_file)

	def get_post_workflow_position(self):

		max_position = max(item['Position'] for item in self.inp_stub['Workflow'].values()) 

		return max_position + 1

	def get_analysis_modules(self, post_workflow_position):
		'''Get analysis modules from input stub.
		'''

		position = post_workflow_position

		for key in self.inp_stub:
			if check_for_meta_module(key):
				position += 1
				module = {'Description': 'meta module',
						  'Position': position,
						  'Type': 'analysis'}

				self.inp_stub['Workflow'][key] = module

	def generate_requirements(self):
		'''Generate dictionary with input requirements.
		'''

		output = self.provided_inp
		requirements = {}

		for key in self.sorted_keys:
			data = self.get_input_output_data(key, self.inp_stub['Workflow'][key]['Type'])

			needed_parameters = self.check_parameters(data['Parameters'], output)
			requirements = merge(requirements, needed_parameters)

			output = merge(output, data['Output'])

		self.requirements = requirements
		self.output = output

	def get_input_output_data(self, target_name, target_type):
		'''Get parameter requirements and outputs from plugin specifications
		(`input_dict`/`output_dict`) or, for analysis modules, from docstrings.
		'''

		if target_type == 'analysis':
			target = import_plugin(target_name, False)
			data = extract_input_output_from_docstring(target)

		else:
			input_dict, output_dict = get_plugin_specification(target_name)
			data = extract_input_output_from_specification(input_dict, output_dict, target_name)

		return data

	def check_parameters(self, data, output):
		'''Check if needed parameter is in output.
		'''

		requirements = {}

		for key, item in data.items():
			if key not in output:
				requirements[key] = item
			else:
				item['Fullfilled by'] = output[key]['Origin']

				required_types = item.get('Types')
				provided_types = output[key].get('Types')

				if required_types and provided_types and not set(provided_types) <= set(required_types):
					print('Warning: type of output and requirement differs for: `{0}`. `{1}` required, `{2}` provided'.format(key, item['Type'], output[key]['Type']))

		return requirements

	def convert_requirements_to_inp(self, insert_origin = False, insert_comment = False):
		'''Convert dictionary of requirements to formatted self.inp
		'''

		for key, item in self.requirements.items():
			path = parse_parameter(key)
			path = ['[...]' if x == '' else x for x in path] # replacing '>>' with '> [...] >'

			insert(self, *path, item['Type'], None, print_info = False, 
				  add_processed = False, insert_path = False)

			if 'Unit' in item:
				insert(self, *path[:-1], item['Unit']['Key'], item['Unit']['Dimension'], None,
					   print_info = False, add_processed = False, insert_path = False)

			if insert_origin:
				insert(self, *path[:-1], 'Requested by', item['Origin'], None, 
					   print_info = False, add_processed = False, insert_path = False)

			if insert_comment:
				for key in item:
					if 'Comment' in key:
						insert(self, *path[:-1], key, item[key], None, 
							   print_info = False, add_processed = False, insert_path = False)
		
class Template_File:
	'''Generate input file from inp dictionary.

	Parameters
	----------
	inp : dict
		Dictionary containing information on requested input (generated by
		`Generate_Template_Input_File`)

	Returns
	-------
	Template_File : object
		Object containing formatted string for output file.
	'''

	def __init__(self, inp):
		self.inp = inp
		self.convert_inp_to_string()

	def convert_inp_to_string(self):
		'''Convert inp to string.'''

		output = ''

		for top_key, top_item in self.inp.items():
			output += f'# {top_key}'

			columns = list(top_item)
			column_names = self.get_column_names(top_item)

			output += '\n\n' + self.convert_column_names_to_string(column_names)
			output += '\n' + '--- | ' * (len(column_names) - 1) + '---'
			output += self.get_row_entries(columns, column_names, top_item)

		self.output = output

	def get_column_names(self, dictionary):
		'''Get names of table columns.'''

		column_names_array = [['Parameter']]

		for key, item in dictionary.items():
			column_names_array.append(list(item))

		column_names_flat_list = [item for sublist in column_names_array for item in sublist]
		column_names = list(dict.fromkeys(column_names_flat_list))

		return column_names

	def convert_column_names_to_string(self, names):
		'''Convert list of names to markdown style table string.'''

		string = ''

		for name in names[:-1]:
			string += f'{name} | '

		string += names[-1]

		return string

	def get_row_entries(self, columns, column_names, dictionary):
		'''Get entries for each row of table.'''

		string = ''

		for column in columns:
			string += f'\n{column} | '
			string += self.get_single_row(column_names, column, dictionary)

		string += '\n\n'

		return string

	def get_single_row(self, column_names, column, dictionary):
		'''Get entries for a single row.'''

		string = ''

		for counter, name in enumerate(column_names[1:]):
			try:
				entry = dictionary[column][name]
			except KeyError:
				entry = 'n/a'

			string += str(entry) 

			if counter < len(column_names[1:]) - 1:
				string += ' | '

		return string

	def write_template_file(self, file_name):
		'''Write output string to file.'''

		with open(Path(file_name), 'w') as text_file:
			text_file.write(self.output)