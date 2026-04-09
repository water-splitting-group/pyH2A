import io
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
import pyH2A.Utilities.input_modification as input_modification
from pyH2A.Utilities.input_modification import convert_file_to_dictionary


def _convert_file_to_dictionary_with_pipe_normalization(file_obj):
    """Normalize pipe-wrapped markdown rows before calling project parser."""
    lines = file_obj.readlines()
    normalized_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            normalized_lines.append(stripped[1:-1].strip() + '\n')
        else:
            normalized_lines.append(line)

    return convert_file_to_dictionary(io.StringIO(''.join(normalized_lines)))


@pytest.fixture(autouse=True)
def patch_markdown_parser_for_pipe_tables(monkeypatch):
    """Ensure recursive loads use parser-compatible markdown normalization."""
    monkeypatch.setattr(
        input_modification,
        'convert_file_to_dictionary',
        _convert_file_to_dictionary_with_pipe_normalization,
    )


class TestMergeArbitaryInputFilesPositive:
    """Test suite for successful first-level base-file merging."""

    def setup_method(self):
        """Set path to real markdown fixture directory."""
        self.test_data_dir = Path(__file__).parent / \
            'Input_Modification' / 'arbitary_merger_test_data'

    @contextmanager
    def _working_directory(self, path):
        """Temporarily switch working directory for relative input references."""
        previous_cwd = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous_cwd)

    def test_convert_input_to_dictionary_merges_references_in_list_order(self):
        """Later listed references should override earlier ones for first-level merge."""
        with self._working_directory(self.test_data_dir):
            merged = input_modification.convert_input_to_dictionary(
                'base_input.md',
                merge_default=False,
            )

        assert merged['Process']['Temperature']['Value'] == 320
        assert merged['Process']['Pressure']['Value'] == 8
        assert merged['Process']['Owner']['Value'] == 'LayerTwo'
        assert merged['Process']['Flow']['Value'] == 25
        assert merged['Economics']['CapEx']['Value'] == 120
        assert merged['Economics']['OpEx']['Value'] == 55

    def test_convert_input_to_dictionary_without_base_table_returns_unchanged(self):
        """Input without Base input file table should remain unchanged."""
        file_input = self.test_data_dir / 'override_level_1.md'
        with Path(file_input).open(mode='r') as handle:
            expected = _convert_file_to_dictionary_with_pipe_normalization(
                handle)

        with self._working_directory(self.test_data_dir):
            merged = input_modification.convert_input_to_dictionary(
                'override_level_1.md',
                merge_default=False,
            )

        assert merged == expected


class TestMergeArbitaryInputFilesNegative:
    """Test suite for failure behavior in first-level base-file merging."""

    def setup_method(self):
        """Set path to real markdown fixture directory."""
        self.test_data_dir = Path(__file__).parent / \
            'Input_Modification' / 'arbitary_merger_test_data'

    @contextmanager
    def _working_directory(self, path):
        """Temporarily switch working directory for relative input references."""
        previous_cwd = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous_cwd)

    def test_convert_input_to_dictionary_missing_file_raises(self):
        """Test that missing referenced files surface a file-not-found error."""
        with pytest.raises(FileNotFoundError):
            with self._working_directory(self.test_data_dir):
                input_modification.convert_input_to_dictionary(
                    'missing_reference.md',
                    merge_default=False,
                )

    def test_convert_input_to_dictionary_does_not_follow_nested_references(self):
        """Method only resolves first-level references from the main input file."""
        with self._working_directory(self.test_data_dir):
            merged = input_modification.convert_input_to_dictionary(
                'cycle_a.md',
                merge_default=False,
            )

        assert merged['A']['Value']['Value'] == 1
        assert merged['B']['Value']['Value'] == 2

    def test_convert_input_to_dictionary_invalid_base_row_raises_value_error(
        self,
        monkeypatch,
    ):
        """Rows in Base input file table must be dictionaries."""
        monkeypatch.setattr(
            input_modification,
            'convert_file_to_dictionary',
            lambda _: {'Base input file': {
                'Layer 1': './override_level_1.md'}},
        )

        with self._working_directory(self.test_data_dir):
            with pytest.raises(
                ValueError,
                match='Expected row in "Base input file" table to be a dictionary',
            ):
                input_modification.convert_input_to_dictionary(
                    'base_input.md',
                    merge_default=False,
                )

    def test_convert_input_to_dictionary_non_string_reference_raises_value_error(
        self,
        monkeypatch,
    ):
        """The Value field in Base input file rows must be a string path."""
        monkeypatch.setattr(
            input_modification,
            'convert_file_to_dictionary',
            lambda _: {'Base input file': {'Layer 1': {'Value': 1}}},
        )

        with self._working_directory(self.test_data_dir):
            with pytest.raises(
                ValueError,
                match='Expected "Value" in "Base input file" table to be a string',
            ):
                input_modification.convert_input_to_dictionary(
                    'base_input.md',
                    merge_default=False,
                )

    def test_convert_input_to_dictionary_empty_reference_raises_value_error(
        self,
        monkeypatch,
    ):
        """Empty file references in Base input file rows should be rejected."""
        monkeypatch.setattr(
            input_modification,
            'convert_file_to_dictionary',
            lambda _: {'Base input file': {'Layer 1': {'Value': '   '}}},
        )

        with self._working_directory(self.test_data_dir):
            with pytest.raises(
                ValueError,
                match='Empty file reference in "Base input file" table',
            ):
                input_modification.convert_input_to_dictionary(
                    'base_input.md',
                    merge_default=False,
                )


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
