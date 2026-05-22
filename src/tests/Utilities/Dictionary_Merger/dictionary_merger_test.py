import pytest
from pyH2A.Utilities.input_modification import convert_input_to_dictionary

@pytest.mark.parametrize( 
    "case",
    [
        {
            "input": {
                "file_path": "src/tests/Utilities/Dictionary_Merger/dictionary_merger_test_data/override_two.md"
            },
            "expected": {
                "Process > Temperature > Value": 320,
                "Process > Pressure > Value": 8,
                "Process > Owner > Value": "LayerTwo",
                "Process > Flow > Value": 25,
                "Economics > CapEx > Value": 120,
                "Economics > OpEx > Value": 55
            },
        },
        {
             "input": {
                "file_path": "src/tests/Utilities/Dictionary_Merger/dictionary_merger_test_data/cycle_a.md"
            },
            "expected": {
                "A > Value > Value": 1,
                "B > Value > Value": 2,
            },
        },
    ],
    ids = [
        "with_base_file",
        "without_base_file"
    ]
)
def test_dictionary_merger(case, request):
    """
    Tests Dictionary merger functionality for two different scenarios:

    1. "with_base_file"
        - Input contains a Base input file table
        - Multiple files are merged in priority order
        - Full Process + Economics structure is expected

    2. "without_base_file"
        - No Base input file table is present
        - Only direct file content is parsed
        - Only A and B tables are expected

    The behavior is selected using pytest ids via:
        ids=["with_base_file", "without_base_file"]
    """

    input_data = case["input"]
    expected_data = case["expected"]

    file_path = input_data["file_path"]

    # Run conversion on the selected input file
    merged_result = convert_input_to_dictionary(file_path, merge_default=False)

    # Get pytest case identifier (used for branching logic)
    test_id = request.node.callspec.id

    # Case 1: Full base-file merge
    if test_id == "with_base_file":

        assert merged_result['Process']['Temperature']['Value'] == expected_data["Process > Temperature > Value"]
        assert merged_result['Process']['Pressure']['Value'] == expected_data["Process > Pressure > Value"]
        assert merged_result['Process']['Owner']['Value'] == expected_data["Process > Owner > Value"]
        assert merged_result['Process']['Flow']['Value'] == expected_data["Process > Flow > Value"]

        assert merged_result['Economics']['CapEx']['Value'] == expected_data["Economics > CapEx > Value"]
        assert merged_result['Economics']['OpEx']['Value'] == expected_data["Economics > OpEx > Value"]

        return  # guard clause: stop further evaluation for this case

    # Case 2: No base file (cycle input)
    assert merged_result['A']['Value']['Value'] == expected_data["A > Value > Value"]
    assert merged_result['B']['Value']['Value'] == expected_data["B > Value > Value"]

    
    