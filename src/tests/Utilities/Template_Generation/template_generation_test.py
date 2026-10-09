'''End-to-end test of the input file template generation
(:class:`pyH2A.Utilities.plugin_input_output_processing.Generate_Template_Input_File`).

Templates are generated from input file stubs and compared with ground truth templates:

* ``input_stub.md``: only ``# Workflow`` and an analysis module.
* ``input_stub_with_merge.md``: additionally contains ``# Input files to merge``
  (``pyH2A.Config~Defaults_TEA.md``), so the default plugins and the parameters 
  provided by the merged file are used.
'''

import pytest

from tests.Utilities.check_dicts_for_testing import check_dicts
from pyH2A.Utilities.input_modification import convert_input_to_dictionary
from pyH2A.Utilities.plugin_input_output_processing import Generate_Template_Input_File

TEST_DATA = 'src/tests/Utilities/Template_Generation/template_generation_test_data/'


@pytest.mark.parametrize(
	'input_stub, ground_truth_template',
	[
		('input_stub.md', 'ground_truth_template.md'),
		('input_stub_with_merge.md', 'ground_truth_template_with_merge.md'),
	]
)
def test_template_generation(tmp_path, input_stub, ground_truth_template):
	'''Template generated from input file stub has to match ground truth template.'''

	actual_template = tmp_path / 'actual_template.md'

	Generate_Template_Input_File(TEST_DATA + input_stub, str(actual_template))

	ground_truth_dict = convert_input_to_dictionary(TEST_DATA + ground_truth_template)
	actual_dict = convert_input_to_dictionary(str(actual_template))

	check_dicts(actual_dict, ground_truth_dict)


def test_template_generation_without_workflow(tmp_path):
	'''Template generation has to raise an error if no `Workflow` table is provided.'''

	input_stub = tmp_path / 'input_stub_without_workflow.md'
	input_stub.write_text('# Monte_Carlo_Analysis\n')

	with pytest.raises(KeyError, match = 'Workflow'):
		Generate_Template_Input_File(str(input_stub), str(tmp_path / 'actual_template.md'))