import io
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
import pyH2A.Utilities.input_modification as input_modification
from pyH2A.Utilities.input_modification import (
    convert_file_to_dictionary,
    merge_arbitary_input_files,
)


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
    """Test suite for successful recursive input-file merging."""

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

    def _load_dictionary(self, file_path):
        """Load markdown fixture and normalize pipe-wrapped rows for parser compatibility."""
        with Path(file_path).open(mode='r') as handle:
            return _convert_file_to_dictionary_with_pipe_normalization(handle)

    def test_merge_arbitary_input_files_merges_in_list_order(self):
        """Test that later listed base references override earlier ones."""
        base_file = self.test_data_dir / 'base_input.md'
        input_dictionary = self._load_dictionary(base_file)

        with self._working_directory(self.test_data_dir):
            merged = merge_arbitary_input_files(
                input_dictionary, str(base_file))

        assert merged['Process']['Temperature']['Value'] == 320
        assert merged['Process']['Pressure']['Value'] == 8
        assert merged['Process']['Owner']['Value'] == 'LayerTwo'
        assert merged['Process']['Flow']['Value'] == 25
        assert merged['Economics']['CapEx']['Value'] == 120
        assert merged['Economics']['OpEx']['Value'] == 55

    def test_merge_arbitary_input_files_returns_original_when_no_base_table(self):
        """Test that dictionary is unchanged when no Base input file table exists."""
        file_input = self.test_data_dir / 'override_level_1.md'
        input_dictionary = self._load_dictionary(file_input)
        merged = merge_arbitary_input_files(input_dictionary, str(file_input))

        assert merged == input_dictionary


class TestMergeArbitaryInputFilesNegative:
    """Test suite for failure behavior in recursive input-file merging."""

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

    def _load_dictionary(self, file_path):
        """Load markdown fixture and normalize pipe-wrapped rows for parser compatibility."""
        with Path(file_path).open(mode='r') as handle:
            return _convert_file_to_dictionary_with_pipe_normalization(handle)

    def test_merge_arbitary_input_files_detects_cycle(self):
        """Test that cyclic Base input file references raise ValueError."""
        file_a = self.test_data_dir / 'cycle_a.md'
        input_dictionary = self._load_dictionary(file_a)

        with pytest.raises(ValueError) as excinfo:
            with self._working_directory(self.test_data_dir):
                merge_arbitary_input_files(input_dictionary, str(file_a))

        assert 'Circular reference detected for file' in str(excinfo.value)

    def test_merge_arbitary_input_files_missing_file_raises(self):
        """Test that missing referenced files surface a file-not-found error."""
        file_base = self.test_data_dir / 'missing_reference.md'
        input_dictionary = self._load_dictionary(file_base)

        with pytest.raises(FileNotFoundError):
            with self._working_directory(self.test_data_dir):
                merge_arbitary_input_files(input_dictionary, str(file_base))


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
