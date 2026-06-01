import pytest
from pyH2A.Utilities.input_modification import convert_input_to_dictionary


@pytest.mark.parametrize(
    "case",
    [
        {
            "input": {
                "file_path": "src/tests/Utilities/Arbitary_Input_Merger/arbitary_input_merger_test_data/override_two.md"
            },
            "expected": {
                "Process > Temperature > Value": 320,
                "Process > Pressure > Value": 8,
                "Process > Pressure > Unit": "bar",
                "Process > Owner > Value": "LayerTwo",
                "Process > Flow > Value": 25,
                "Economics > CapEx > Value": 120,
                "Economics > OpEx > Value": 55,
            },
        },
    ],
    ids=["with_base_file"],
)
def test_arbitrary_input_merger(case):
    """
    Tests input merger functionality:

    "with_base_file"
        - Input contains a Base input file table
        - Multiple files are merged in priority order
        - Full Process + Economics structure is expected
    """

    input_data = case["input"]
    expected_data = case["expected"]

    file_path = input_data["file_path"]

    # Run conversion on the selected input file
    merged_result = convert_input_to_dictionary(file_path, merge_default=False)

    assert (
        merged_result["Process"]["Temperature"]["Value"]
        == expected_data["Process > Temperature > Value"]
    )

    assert (
        merged_result["Process"]["Pressure"]["Value"]
        == expected_data["Process > Pressure > Value"]
    )

    assert (
        merged_result["Process"]["Pressure"]["Unit"]
        == expected_data["Process > Pressure > Unit"]
    )

    assert (
        merged_result["Process"]["Owner"]["Value"]
        == expected_data["Process > Owner > Value"]
    )

    assert (
        merged_result["Process"]["Flow"]["Value"]
        == expected_data["Process > Flow > Value"]
    )

    assert (
        merged_result["Economics"]["CapEx"]["Value"]
        == expected_data["Economics > CapEx > Value"]
    )

    assert (
        merged_result["Economics"]["OpEx"]["Value"]
        == expected_data["Economics > OpEx > Value"]
    )
