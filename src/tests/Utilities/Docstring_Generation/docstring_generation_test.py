import numpy as np

from pyH2A.Utilities.docstring_generation import generate_docstring


def test_plain_row():
	input_dict = {
		'Table': {
			'Row': {
				'Value': {'type': {int, float}, 'bounds': (0, None)},
				'Unit': {'dimension': 'currency'},
				'optional': False,
				'description': 'A plain row.',
			},
		},
	}

	doc = generate_docstring('Summary.', input_dict, {})

	assert 'Table' in doc
	assert 'Row' in doc
	assert 'Value' in doc
	assert 'type: int or float' in doc
	assert 'bounds: (0, None)' in doc
	assert 'A plain row.' in doc
	assert 'False' in doc


def test_wildcard_row():
	input_dict = {
		'Construction': {
			'<...>': {
				'Value': {'type': {int, float}, 'bounds': (0, 1)},
				'Unit': {'dimension': 'dimensionless'},
				'optional': False,
				'description': 'Fraction per year.',
			},
		},
	}

	doc = generate_docstring('Summary.', input_dict, {})
	print(doc)

	assert 'Construction' in doc
	assert '<...>' in doc
	assert 'Value' in doc
	assert 'type: int or float' in doc
	assert 'bounds: (0, 1)' in doc
	assert 'dimension: dimensionless' in doc
	assert 'Fraction per year.' in doc
	assert 'False' in doc

def test_wildcard_table_group_with_sum_tables():
	input_dict = {
		'<...> Direct Capital Cost <...>': {
			'<...>': {
				'Value': {'type': {int, float}, 'bounds': (0, None)},
				'Unit': {'dimension': 'currency'},
				'optional': True,
				'description': 'Individual entry.',
			},
			'sum_tables': {
				'mode': 'all',
				'arguments': {'bottom_key': 'Value'},
			},
		},
	}

	doc = generate_docstring('Summary.', input_dict, {})

	assert 'sum_tables' not in doc


def test_categorical_options():
	input_dict = {
		'Power Consumption': {
			'<...>': {
				'Value': {'type': {int, float, np.ndarray}, 'bounds': (0, None)},
				'Unit': {'dimension': 'power'},
				'Type': {'type': {str}, 'options': {'flexible', 'on_demand'}},
				'optional': True,
				'description': 'Consumption values.',
			},
		},
	}

	doc = generate_docstring('Summary.', input_dict, {})

	assert "options: 'flexible', 'on_demand'" in doc
 

def test_suffixed_value_unit_pair():
	input_dict = {
		'Utilities': {
			'<...>': {
				'Cost_Value': {'type': {int, float}, 'bounds': (0, None)},
				'Cost_Unit': {'dimension': 'currency'},
				'Cost_Path': {'type': {str}},
				'optional': True,
				'description': 'Cost of utility.',
			},
		},
	}

	doc = generate_docstring('Summary.', input_dict, {})
	print(doc)

	assert 'Cost_Value' in doc


def test_output_plain_row():
	output_dict = {
		'Total Capital Costs': {
			'Total': {
				'Value': {'inserted_value': 'total', 'type': {int, float}, 'dimension': 'currency'},
				'description': 'Total capital costs.',
			},
		},
	}

	doc = generate_docstring('Summary.', {}, output_dict)
	print(doc)

	assert 'Total Capital Costs' in doc
	assert 'Total' in doc
	assert 'Value' in doc
	assert 'Total capital costs.' in doc
	assert 'inserted_value' in doc


def test_output_special_insertions_sum_all_tables():
	output_dict = {
		'special_insertions': {
			'sum_all_tables': {
				'<...> Direct Capital Cost <...>': {
					'Summed total': {
						'Value': {'type': {int, float}, 'dimension': 'currency'},
						'description': 'Summed total per table.',
					},
				},
				'Direct Capital Cost': {
					'Summed group total': {
						'Value': {'type': {int, float}, 'dimension': 'currency'},
						'description': 'Summed total across tables.',
					},
				},
			},
		},
	}

	doc = generate_docstring('Summary.', {}, output_dict)
	print(doc)

	assert 'Summed total' in doc
	assert 'Summed group total' in doc


def test_notes_section():
	doc = generate_docstring('Summary.', {}, {}, notes = 'Some extra information.')
	print(doc)

	assert 'Notes' in doc
	assert 'Some extra information.' in doc


def test_no_notes_section_when_absent():
	doc = generate_docstring('Summary.', {}, {})
	print(doc)

	assert 'Notes' not in doc


def test_type_prose_canonical_order():
	input_dict = {
		'Table': {
			'Row': {
				'Value': {'type': {float, int}, 'bounds': (0, None)},
				'Unit': {'dimension': 'dimensionless'},
				'optional': False,
				'description': 'Order should not depend on set iteration.',
			},
		},
	}

	doc = generate_docstring('Summary.', input_dict, {})
	print(doc)

	assert 'int or float' in doc
	assert 'float or int' not in doc
