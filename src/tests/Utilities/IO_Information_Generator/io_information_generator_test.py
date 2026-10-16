'''Tests for :mod:`pyH2A.Utilities.io_information_generator`.

A dummy plugin specification is converted into Plugin I/O rows and the
result is compared with the expected JSON written in this file.
'''

import json

from pyH2A.Utilities.io_information_generator import collect_plugin_rows


# Dummy ``input_dict`` of a plugin. It covers a required and an optional
# input, a wildcard table group with a prefixed ``Cost_Value``/``Cost_Unit``
# pair and a ``sum_tables`` entry, which must not become a variable.
INPUT_DICT = {
	'Table': {
		'Required': {
			'Value': {'type': {float}},
			'Unit': {'dimension': 'currency'},
			'optional': False,
			'description': 'Required input.',
		},
		'Optional': {
			'Value': {'type': {float}},
			'Unit': {'dimension': 'currency'},
			'optional': True,
			'description': 'Optional input.',
		},
	},
	'<...> Group <...>': {
		'<...>': {
			'Cost_Value': {'type': {float}},
			'Cost_Unit': {'dimension': 'currency'},
			'optional': True,
		},
		'sum_tables': {'mode': 'all', 'arguments': {'bottom_key': 'Value'}},
	},
}

# Dummy ``output_dict`` of the same plugin. ``Table > Optional`` is also an
# input, so it becomes ``Input/Output``. The ``special_insertions`` wrapper
# must be removed so that ``Group > Summed total`` looks like a regular output.
OUTPUT_DICT = {
	'Table': {
		'Optional': {
			'Value': {'inserted_value': 'value', 'type': {float}},
			'description': 'Written back.',
		},
	},
	'special_insertions': {
		'sum_all_tables': {
			'Group': {
				'Summed total': {'Value': {'type': {float}}},
			},
		},
	},
}

# Expected result: one row per variable. sum_tables is skipped,
# special_insertions is unwrapped, Cost_Value becomes Cost, and a variable
# that is both input and output becomes Input/Output with optional per direction.
EXPECTED_JSON = '''
[
    {
        "plugin": "Example",
        "top": "Table",
        "medium": "Required",
        "bottom": "Value",
        "direction": "Input",
        "optional": {"Input": false},
        "description": "Required input."
    },
    {
        "plugin": "Example",
        "top": "Table",
        "medium": "Optional",
        "bottom": "Value",
        "direction": "Input/Output",
        "optional": {"Input": true, "Output": false},
        "description": "Optional input."
    },
    {
        "plugin": "Example",
        "top": "<...> Group <...>",
        "medium": "<...>",
        "bottom": "Cost",
        "direction": "Input",
        "optional": {"Input": true},
        "description": ""
    },
    {
        "plugin": "Example",
        "top": "Group",
        "medium": "Summed total",
        "bottom": "Value",
        "direction": "Output",
        "optional": {"Output": false},
        "description": ""
    }
]
'''


def test_collect_plugin_rows():
	'''Check the rows collected from the dummy plugin specification.

	The test passes if :func:`collect_plugin_rows` returns exactly the rows
	in ``EXPECTED_JSON``.

	Notes
	-----
	The comparison covers the full end result: skipped ``sum_tables``,
	unwrapped ``special_insertions``, the ``Cost_Value`` to ``Cost`` name,
	the combined ``Input/Output`` direction and ``optional`` per direction.
	'''

	rows = collect_plugin_rows(INPUT_DICT, OUTPUT_DICT, 'Example')

	assert rows == json.loads(EXPECTED_JSON)