import re
from pyH2A.Utilities.input_modification import insert, process_table


def resolve_top_levels(inp, pattern):
    """
    Identify top-level tables in input dictionary that match a given pattern.

    Parameters
    ----------
    inp : dict
        Input dictionary (typically `dcf.inp`) to search for tables.
    pattern : str
        Pattern string, e.g., '<...> Direct Capital Cost <...>',
        where '<...>' acts as a wildcard.

    Returns
    -------
    list of str
        List of top-level keys in `inp` matching the pattern.
    """
    core = pattern.replace("<...>", "").strip()
    return [k for k in inp if k == core or k.split(" - ", 1)[0] == core]


def resolve_inner_input(dcf, tops, mid, low):
    """
    Resolve and collect input values from nested input tables based on hierarchy level.

    This function processes each top-level input table, ensures it is initialized,
    and extracts values at the specified mid- and low-level keys. If the mid-level
    key indicates a <...> structure, all matching low-level values across
    rows are collected into a list.

    Parameters
    ----------
    dcf : object
        Data container object holding the input dictionary (typically accessed
        as `dcf.inp`).
    tops : iterable of str
        Top-level keys identifying input tables to process.
    mid : str
        Mid-level key within each top-level table. If this key starts with
        '<...>' (case-insensitive), the table is treated as a <...>
        structure.
    low : str
        Low-level key whose value(s) should be extracted.

    Returns
    -------
    dict
        Dictionary mapping each top-level key to the resolved value(s):
        - a list of values if the mid-level key is <...>
        - a single value otherwise

    Notes
    -----
    - Assumes the input tables follow the expected nested dictionary structure.
    - Does not perform validation on key existence or data types.
    - Calls `process_table` to ensure each top-level table is prepared before
      value extraction.
    """
    collected = {}

    for top in tops:
        process_table(dcf.inp, top, low)

        if mid == "<...>":
            values = []
            for row in dcf.inp[top].values():
                if isinstance(row, dict) and low in row:
                    values.append(row[low])
            collected[top] = values
        else:
            collected[top] = dcf.inp[top][mid][low]

    return collected


def input_resolver(input_dict, dcf):
    """
    Resolve inputs from `dcf.inp` using a specification dictionary.

    Parameters
    ----------
    input_dict : dict
        Dictionary specifying top-level, mid-level, and lower-level keys for inputs.
        Example:
        {
            'planned_replacement_cost': {
                'top_level': 'Planned Replacement',
                'mid_level': '<...>',
                'lower_level': 'Cost ($)'
            },
            ...
        }
    dcf : object
        DCF object containing `dcf.inp`, the hierarchical input dictionary.

    Returns
    -------
    resolved : dict
        Dictionary of resolved values according to the input specification.
        For <...> tables, values are returned as lists.
    """
    resolved = {}

    for name, spec in input_dict.items():
        top_pattern = spec["top_level"]
        mid = spec["mid_level"]
        low = spec["lower_level"]

        tops = resolve_top_levels(dcf.inp, top_pattern)
        collected = resolve_inner_input(dcf, tops, mid, low)

        if len(collected) == 1:
            resolved[name] = list(collected.values())[0]
        else:
            resolved[name] = collected

    return resolved


def output_resolver(output_dict, values, dcf, print_info=True):
    """
    Insert resolved output values into `dcf.inp` according to output specification.

    Parameters
    ----------
    output_dict : dict
        Dictionary specifying where outputs should be inserted.
        Example:
        {
            'replacement_total': {
                'top_level': 'Replacement',
                'mid_level': 'Total',
                'lower_level': 'Value'
            },
            ...
        }
    values : dict
        Dictionary containing values to be inserted, keys matching `output_dict`.
    dcf : object
        DCF object containing `dcf.inp`.
    print_info : bool, optional
        Whether to print insert information. Default is True.

    Notes
    -----
    - Handles <...> top-level tables (identified by '<...>' in top_level).
    - Inserts single values or lists depending on the table structure.
    """

    for name, spec in output_dict.items():
        top_pattern = spec["top_level"]
        mid = spec["mid_level"]
        low = spec["lower_level"]

        # Handle '<...>' tables
        if "<...>" in top_pattern:
            if isinstance(values[name], dict):
                for top, val in values[name].items():
                    insert(dcf, top, mid, low, val, __name__, print_info=print_info)
            else:
                # fallback: find matching table(s) in dcf.inp
                for top_key in dcf.inp.keys():
                    if re.search(top_pattern.replace("<...>", ".*"), top_key):
                        insert(
                            dcf,
                            top_key,
                            mid,
                            low,
                            values[name],
                            __name__,
                            print_info=print_info,
                        )
        else:
            insert(
                dcf,
                top_pattern,
                mid,
                low,
                values[name],
                __name__,
                print_info=print_info,
            )