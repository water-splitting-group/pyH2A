from pathlib import Path
import copy

from pyH2A.Utilities.input_modification import insert, convert_input_to_dictionary, check_for_meta_module, import_plugin, merge, parse_parameter, convert_file_to_dictionary, file_import
from pyH2A.Utilities.plugin_specification import instantiate_plugin_for_docs, iter_spec_rows, iter_bottom_entries

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

def convert_types_to_string(types):
	'''Convert set of types from plugin specification (e.g. `{int, float}`) to string (e.g. `int or float`).'''

	names = {int: 'int', float: 'float', str: 'str', bool: 'bool', dict: 'dict', list: 'list', tuple: 'tuple'}

	return ' or '.join(names.get(t, t.__name__) for t in sorted(types, key = lambda t: list(names).index(t) if t in names else len(names)))

def extract_input_output_from_plugin(plugin_name):
	'''Convert plugin `input_dict` and `output_dict` to structured dictionary
	(same structure as `extract_input_output_from_docstring`).'''

	plugin = instantiate_plugin_for_docs(plugin_name)

	plugin_dict = {'Parameters': {}, 'Output': {}}

	for key, spec_dict in (('Parameters', plugin.input_dict), ('Output', plugin.output_dict)):
		for top_key, middle_key, row_dict in iter_spec_rows(spec_dict, plugin_name):
			for bottom_key, value_spec, optional in iter_bottom_entries(row_dict):

				variable_string = f'{top_key} > {middle_key} > {bottom_key}'.replace('<...>', '[...]')
				variable_type = convert_types_to_string(value_spec.get('type', set()))

				if optional:
					variable_type += ', optional'

				plugin_dict[key][variable_string] = {'Type': variable_type, 'Origin': plugin_name}

				if row_dict.get('description'):
					plugin_dict[key][variable_string][f'Comment {bottom_key}'] = row_dict['description']

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

# Tables which are always requested by template generation (independent of plugins and analysis modules)
TEMPLATE_BASE_REQUIREMENTS = {
	'Functional Unit > Functional Unit > Unit': {
		'Type': 'str', 
		'Origin': 'Generate_Template_Input_File',
		'Comment Unit': 'Unit in which all results are reported. It has to name the product it refers to as bracketed reference, e.g. kg[H2].'},
	'Input files to merge > [...] > Value': {
		'Type': 'str, optional', 
		'Origin': 'Generate_Template_Input_File',
		'Comment Value': 'Path to input file which is merged into this input file, e.g. pyH2A.Config~Defaults_TEA.md. Files listed first have higher priority.'},
}

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
	Template generation has three levels:

	1. Workflow and analysis modules, specified in input file stub. A ``Workflow`` 
	   table is required, analysis modules are optional.
	2. Tables requested by template generation itself (``TEMPLATE_BASE_REQUIREMENTS``): 
	   ``Functional Unit`` (required) and ``Input files to merge`` (optional).
	3. Inputs requested by plugins (from their ``input_dict``) and analysis modules
	   (from their docstrings).
	'''

	def __init__(self, input_file_stub, output_file, 
				 origin = False, comment = False):
		if isinstance(input_file_stub, str):
			self.inp_stub = convert_input_to_dictionary(input_file_stub)
		else:
			self.inp_stub = input_file_stub

		if 'Workflow' not in self.inp_stub:
			raise KeyError('Input file stub has to contain a `Workflow` table.')

		self.inp = {}

		post_workflow_position = self.get_post_workflow_position()

		self.get_analysis_modules(post_workflow_position)

		self.sorted_keys = sorted(self.inp_stub['Workflow'], 
								  key = lambda x: self.inp_stub['Workflow'][x]['Position'])

		self.requirements = {}
		self.output = {}

		self.provided_inp = convert_inp_to_requirements(self.inp_stub)
		self.generate_requirements()
		self.convert_requirements_to_inp(insert_origin = origin, insert_comment = comment)

		self.inp = merge(self.inp, 
						 convert_file_to_dictionary(file_import(input_file_stub, mode = 'r')))

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

		base_requirements = copy.deepcopy(TEMPLATE_BASE_REQUIREMENTS)
		if 'Input files to merge' in self.inp_stub: # placeholder only requested if no files to merge are provided
			del base_requirements['Input files to merge > [...] > Value']

		requirements = self.check_parameters(base_requirements, output)

		for key in self.sorted_keys:
			data = self.get_docstring_data(key, self.inp_stub['Workflow'][key].get('Type', 'plugin'))

			needed_parameters = self.check_parameters(data['Parameters'], output)
			requirements = merge(requirements, needed_parameters)

			output = merge(output, data['Output'])

		self.requirements = requirements

	def get_docstring_data(self, target_name, target_type):
		'''Get parameter requirements and outputs from plugin `input_dict` and `output_dict`
		(plugins) or docstrings (analysis modules).
		'''

		if target_type == 'plugin':
			data = extract_input_output_from_plugin(target_name)

		else:
			target = import_plugin(target_name, False)
			data = extract_input_output_from_docstring(target)

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

				try:
					if output[key]['Type'] != item['Type']:
						print('Warning: type of output and requirement differs for: `{0}`. `{1}` required, `{2}` provided'.format(key, item['Type'], output[key]['Type']))
				except KeyError:
					pass

		return requirements

	def convert_requirements_to_inp(self, insert_origin = False, insert_comment = False):
		'''Convert dictionary of requirements to formatted self.inp
		'''

		for key, item in self.requirements.items():
			path = parse_parameter(key)
			path = ['<...>' if x == '' else x.replace('[...]', '<...>') for x in path] # replacing '>>' and '[...]' with '<...>'

			insert(self, *path, item['Type'], None, print_info = False, 
				  add_processed = False, insert_path = False)

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