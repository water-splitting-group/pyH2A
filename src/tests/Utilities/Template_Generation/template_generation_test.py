'''End-to-end test of the input file template generation
(:class:`pyH2A.Utilities.plugin_input_output_processing.Generate_Template_Input_File`).

A template is generated from an input file stub (only ``# Workflow`` and an
analysis module) and compared with a ground truth template.
'''

import pytest

from tests.Utilities.check_dicts_for_testing import check_dicts
from pyH2A.Utilities.input_modification import convert_file_to_dictionary, file_import
from pyH2A.Utilities.plugin_input_output_processing import Generate_Template_Input_File

TEST_DATA = 'src/tests/Utilities/Template_Generation/template_generation_test_data/'


def read_template(file_name):
	'''Read template file into dictionary.

	Notes
	-----
	The template contains an ``Input files to merge`` table with a placeholder 
	row, which ``convert_input_to_dictionary`` would try to open as a file. 
	The template is therefore read without merging other input files.
	'''

	return convert_file_to_dictionary(file_import(file_name, mode = 'r'))


def test_template_generation(tmp_path):
	'''Template generated from input file stub has to match ground truth template.'''

	actual_template = tmp_path / 'actual_template.md'

	Generate_Template_Input_File(TEST_DATA + 'input_stub.md', str(actual_template))

	ground_truth_dict = read_template(TEST_DATA + 'ground_truth_template.md')
	actual_dict = read_template(str(actual_template))

	check_dicts(actual_dict, ground_truth_dict)


def test_template_generation_without_workflow(tmp_path):
	'''Template generation has to raise an error if no `Workflow` table is provided.'''

	input_stub = tmp_path / 'input_stub_without_workflow.md'
	input_stub.write_text('# Monte_Carlo_Analysis\n')

	with pytest.raises(KeyError, match = 'Workflow'):
		Generate_Template_Input_File(str(input_stub), str(tmp_path / 'actual_template.md'))