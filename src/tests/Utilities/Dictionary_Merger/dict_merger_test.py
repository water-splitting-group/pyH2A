import copy
import io
from pathlib import Path

import pytest
import pyH2A.Utilities.Dictionary_Merger.dict_merger as dm
from pyH2A.Utilities.input_modification import convert_file_to_dictionary, file_import


class TestDictionaryMergerPositive:
    """Test suite for successful dictionary-merger behavior."""

    def setup_method(self):
        """Initialize shared paths and loader callables before each test."""
        self.test_data_dir = Path(__file__).parent / 'test_data'

    def _load_dictionary(self, file_reference):
        """Parse a markdown input file into a nested dictionary.

        The production parser expects table rows without leading/trailing pipes.
        Test fixtures may use fully pipe-wrapped markdown tables, so we
        normalize that representation before parsing.
        """
        with file_import(file_reference, mode='r') as handle:
            lines = handle.readlines()

        normalized_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                normalized_lines.append(stripped[1:-1].strip() + '\n')
            else:
                normalized_lines.append(line)

        return convert_file_to_dictionary(io.StringIO(''.join(normalized_lines)))

    def _resolve_input_path(self, file_reference):
        """Resolve a file reference to an absolute file path."""
        return str(file_import(file_reference, return_path=True))

    def test_clean_input_reference_normalizes_values(self):
        """Test normalization of valid and sentinel reference values."""
        assert dm.clean_input_reference('  ./file.md  ') == './file.md'
        assert dm.clean_input_reference('n/a') is None
        assert dm.clean_input_reference('None') is None
        assert dm.clean_input_reference('') is None
        assert dm.clean_input_reference(42) is None

    def test_extract_referenced_input_files_preserves_order(self):
        """Test extraction of base-file references in table order."""
        input_dictionary = {
            'Base input file': {
                'File A': {'Value': './a.md'},
                'File B': {'Value': './b.md'},
                'File C': {'Value': 'n/a'},
            }
        }

        references = dm.extract_referenced_input_files(input_dictionary)

        assert references == ['./a.md', './b.md']

    def test_resolve_referenced_input_file_relative_and_absolute(self):
        """Test file-reference resolution for relative and absolute paths."""
        current_file = str(self.test_data_dir / 'base_input.md')

        relative = dm.resolve_referenced_input_file(
            './override_level_1.md', current_file)
        absolute_input = str(
            (self.test_data_dir / 'override_level_2.md').resolve())
        absolute = dm.resolve_referenced_input_file(
            absolute_input, current_file)

        assert relative == str(
            (self.test_data_dir / 'override_level_1.md').resolve())
        assert absolute == absolute_input

    def test_deep_merge_merges_nested_structures(self):
        """Test deep merge for nested dicts and list extension/override."""
        base = {
            'A': {'x': 1, 'y': 2},
            'L': [1, {'k': 1}],
        }
        override = {
            'A': {'y': 5, 'z': 9},
            'L': [2, {'k': 7}, 3],
        }

        merged = dm.deep_merge(copy.deepcopy(base), override)

        assert merged['A']['x'] == 1
        assert merged['A']['y'] == 5
        assert merged['A']['z'] == 9
        assert merged['L'][0] == 2
        assert merged['L'][1]['k'] == 7
        assert merged['L'][2] == 3

    def test_load_input_dictionary_with_references_merges_in_priority_order(self):
        """Test that base file is lowest priority and later references win."""
        merged = dm.load_input_dictionary_with_references(
            file_reference=str(self.test_data_dir / 'base_input.md'),
            load_dictionary=self._load_dictionary,
            resolve_input_path=self._resolve_input_path,
        )

        assert merged['Process']['Temperature']['Value'] == 320
        assert merged['Process']['Pressure']['Value'] == 8
        assert merged['Process']['Owner']['Value'] == 'LayerTwo'
        assert merged['Process']['Flow']['Value'] == 25
        assert merged['Economics']['CapEx']['Value'] == 120
        assert merged['Economics']['OpEx']['Value'] == 55


class TestDictionaryMergerNegative:
    """Test suite for failure and conflict handling in dictionary merger."""

    def setup_method(self):
        """Initialize shared paths and loader callables before each test."""
        self.test_data_dir = Path(__file__).parent / 'test_data'

    def _load_dictionary(self, file_reference):
        """Parse a markdown input file into a nested dictionary.

        The production parser expects table rows without leading/trailing pipes.
        Test fixtures may use fully pipe-wrapped markdown tables, so we
        normalize that representation before parsing.
        """
        with file_import(file_reference, mode='r') as handle:
            lines = handle.readlines()

        normalized_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                normalized_lines.append(stripped[1:-1].strip() + '\n')
            else:
                normalized_lines.append(line)

        return convert_file_to_dictionary(io.StringIO(''.join(normalized_lines)))

    def _resolve_input_path(self, file_reference):
        """Resolve a file reference to an absolute file path."""
        return str(file_import(file_reference, return_path=True))

    def test_deep_merge_conflict_with_update_false_raises(self):
        """Test that conflicting leaves raise when update is disabled."""
        base = {'A': 1}
        override = {'A': 2}

        with pytest.raises(Exception) as excinfo:
            dm.deep_merge(base, override, update=False)

        assert 'Conflict at A' in str(excinfo.value)

    def test_load_input_dictionary_with_references_detects_cycle(self):
        """Test that cyclic base references raise a ValueError."""
        with pytest.raises(ValueError) as excinfo:
            dm.load_input_dictionary_with_references(
                file_reference=str(self.test_data_dir / 'cycle_a.md'),
                load_dictionary=self._load_dictionary,
                resolve_input_path=self._resolve_input_path,
            )

        assert 'Cyclic input file reference detected' in str(excinfo.value)

    def test_load_input_dictionary_with_references_missing_file_raises(self):
        """Test that missing referenced files surface a file-not-found error."""
        with pytest.raises(FileNotFoundError):
            dm.load_input_dictionary_with_references(
                file_reference=str(self.test_data_dir /
                                   'missing_reference.md'),
                load_dictionary=self._load_dictionary,
                resolve_input_path=self._resolve_input_path,
            )


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
