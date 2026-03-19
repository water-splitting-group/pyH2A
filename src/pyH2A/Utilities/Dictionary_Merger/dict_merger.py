"""Utilities for deep-merging input dictionaries loaded from markdown files.

This module implements the dictionary merge behavior used by pyH2A input
processing, including support for recursively loading and merging referenced
input files from a ``Base input file`` table.
"""

from pathlib import Path


def deep_merge(base, override, path=None, update=True):
    """Deep-merge ``override`` into ``base`` in place and return ``base``.

    Parameters
    ----------
    base : dict
                    Base dictionary with lower priority values.
    override : dict
                    Dictionary with higher priority values.
    path : list, optional
                    Merge path used for conflict reporting.
    update : bool, optional
                    If ``True``, conflicting non-dict values are overwritten by
                    ``override``. If ``False``, conflicts raise an exception.

    Returns
    -------
    base : dict
                    ``base`` updated with merged values.

    Notes
    -----
    Nested dictionaries are merged recursively. For lists, elements are merged
    by index while indices beyond the original list length are appended.
    """

    if path is None:
        path = []

    for key in override:
        if key in base:
            if isinstance(base[key], dict) and isinstance(override[key], dict):
                deep_merge(base[key], override[key],
                           path + [str(key)], update=update)
            elif base[key] == override[key]:
                pass
            elif isinstance(base[key], list) and isinstance(override[key], list):
                for idx, value in enumerate(override[key]):
                    if idx < len(base[key]) and isinstance(base[key][idx], dict) and isinstance(value, dict):
                        base[key][idx] = deep_merge(
                            base[key][idx],
                            value,
                            path + [str(key), str(idx)],
                            update=update
                        )
                    elif idx < len(base[key]):
                        base[key][idx] = value
                    else:
                        base[key].append(value)
            elif update:
                base[key] = override[key]
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            base[key] = override[key]

    return base


def clean_input_reference(reference):
    """Normalize a referenced input path.
    This function performs the following normalizations:
        - Strips leading and trailing whitespace.
        - Converts empty strings, 'n/a', and 'None' (case-sensitive) to None
    """

    if not isinstance(reference, str):
        return None

    cleaned_reference = reference.strip(' ')

    if cleaned_reference in ['', 'n/a', 'None']:
        return None

    return cleaned_reference


def extract_referenced_input_files(input_dictionary, table_key='Base input file',
                                   value_key='Value'):
    """Return ordered referenced input files from ``input_dictionary``.

    The returned order matches the table order and therefore defines merge
    precedence among referenced files (later entries override earlier entries).
    """

    referenced_files = []

    table = input_dictionary.get(table_key)

    if not isinstance(table, dict):
        return referenced_files

    for _, row in table.items():
        if not isinstance(row, dict):
            continue

        reference = clean_input_reference(row.get(value_key))

        if reference is not None:
            referenced_files.append(reference)

    return referenced_files


def resolve_referenced_input_file(reference, current_input_path):
    """Resolve a referenced input file from ``current_input_path`` context.
     The resolution behavior is as follows:
        - If ``reference`` contains a tilde (~), it is returned as-is without resolution.
        - If ``reference`` is an absolute path, it is returned as-is.
        - Otherwise, ``reference`` is resolved relative to the directory of
            ``current_input_path`` and the absolute path is returned.
     """

    if '~' in reference:
        return reference

    reference_path = Path(reference).expanduser()

    if reference_path.is_absolute():
        return str(reference_path)

    return str((Path(current_input_path).parent / reference_path).resolve())


def identifier_for_input_file(file_reference, resolved_path):
    """Return stable identifier used for cycle detection."""

    if '~' in file_reference:
        return file_reference

    try:
        return str(Path(resolved_path).resolve())
    except OSError:
        return str(resolved_path)


def load_input_dictionary_with_references(file_reference, load_dictionary,
                                          resolve_input_path,
                                          table_key='Base input file',
                                          value_key='Value', visited=None):
    """Load ``file_reference`` and recursively merge referenced input files.

    Parameters
    ----------
    file_reference : str
                    File path or package reference to load.
    load_dictionary : callable
                    Callable receiving a file reference and returning a parsed
                    dictionary.
    resolve_input_path : callable
                    Callable receiving a file reference and returning a resolved path
                    used for relative path resolution and cycle detection.
    table_key : str, optional
                    Name of table containing referenced input files.
    value_key : str, optional
                    Name of column inside ``table_key`` containing file references.
    visited : set, optional
                    Internal recursion state used for cycle detection.

    Returns
    -------
    merged_input_dictionary : dict
                    Merged dictionary where ``file_reference`` is the base
                    (lowest priority) and referenced files are merged in listed
                    order on top of it (later referenced files have higher
                    priority).
    """

    input_dictionary = load_dictionary(file_reference)
    resolved_path = resolve_input_path(file_reference)
    file_identifier = identifier_for_input_file(file_reference, resolved_path)

    if visited is None:
        visited = set()

    # Check for recursive loops in the reference graph.
    if file_identifier in visited:
        raise ValueError(
            'Cyclic input file reference detected for {0}'.format(
                file_identifier)
        )

    visited.add(file_identifier)

    try:
        # Start from the current file as base (lowest priority).
        merged_input_dictionary = input_dictionary
        referenced_files = extract_referenced_input_files(
            input_dictionary,
            table_key=table_key,
            value_key=value_key
        )

        for referenced_file in referenced_files:
            resolved_reference = resolve_referenced_input_file(
                referenced_file,
                resolved_path
            )
            referenced_dictionary = load_input_dictionary_with_references(
                resolved_reference,
                load_dictionary=load_dictionary,
                resolve_input_path=resolve_input_path,
                table_key=table_key,
                value_key=value_key,
                visited=visited
            )
            deep_merge(merged_input_dictionary, referenced_dictionary)

        return merged_input_dictionary
    finally:
        visited.remove(file_identifier)
