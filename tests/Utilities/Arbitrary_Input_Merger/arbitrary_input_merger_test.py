import pytest
from tests.Utilities.check_dicts_for_testing import check_dicts
from pyH2A.Utilities.input_modification import convert_input_to_dictionary


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "file_path": "tests/Utilities/Arbitrary_Input_Merger/arbitrary_input_merger_test_data/override_two.md"
            },
            "expected": {
                "Process": {
                    "Temperature": {
                        "Value": 320,
                        "Unit": "K",
                    },
                    "Pressure": {
                        "Value": 8,
                        "Unit": "bar",
                    },
                    "Owner": {
                        "Value": "LayerTwo",
                        "Unit": "-",
                    },
                    "Flow": {
                        "Value": 25,
                        "Unit": "sccm",
                    },
                },
                "Economics": {
                    "CapEx": {
                        "Value": 120,
                    },
                    "OpEx": {
                        "Value": 55,
                    },
                },
                "Input files to merge": {
                    "Mid priority": {
                        "Value": "tests/Utilities/Arbitrary_Input_Merger/arbitrary_input_merger_test_data/override_one.md",
                    },
                    "Lowest priority": {
                        "Value": "tests/Utilities/Arbitrary_Input_Merger/arbitrary_input_merger_test_data/base_input.md",
                    },
                },
            },
        },
        {
            "input": {
                "file_path": "tests/Utilities/Arbitrary_Input_Merger/arbitrary_input_merger_test_data/missing_reference.md"
            },
            "expected": {
                "Error": FileNotFoundError,
            },
        },
    ],
    ids=[
        "with_base_file",
        "missing_reference",
    ],
)
def test_arbitrary_input_merger(case, request):
    """
    Tests input merger functionality:

    "with_base_file"
        - Input contains a Base input file table
        - Multiple files are merged in priority order
        - Full Process + Economics structure is expected

    "missing_reference"
        - Input references a Base input file that is missing
    """

    input_data = case["input"]
    expected_data = case["expected"]

    file_path = input_data["file_path"]

    # Get pytest case identifier (used for branching logic)
    test_id = request.node.callspec.id

    # Case 2: Missing reference merges should raise FileNotFoundError
    if test_id == "missing_reference":
        with pytest.raises(expected_data["Error"]):
            convert_input_to_dictionary(file_path, merge_default=False)
        return

    # Run conversion on the selected input file
    merged_result = convert_input_to_dictionary(file_path, merge_default=False)

    # Case 1: Full base-file merge
    check_dicts(merged_result, expected_data)