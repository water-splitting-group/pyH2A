"""
Generate an Excel overview of all pyH2A plugin interfaces.

The generated Excel file contains three columns:

    Plugin
        Name of the plugin.

    Name
        Full path of the interface, e.g.
        ``Power Generation > Available energy (daily) > Value``.

    Type
        ``Input``, ``Output``, or ``Input/Output``.

An interface that occurs in both the input and output dictionaries
of the same plugin is listed only once as ``Input/Output``.
"""


import inspect
from importlib import import_module

import openpyxl
from openpyxl.styles import Font

from pyH2A.Utilities.input_modification import import_plugin


# =============================================================================
# SETTINGS
# =============================================================================

OUTPUT_FILE = "plugin_interfaces.xlsx"


# =============================================================================
# FUNCTIONS
# =============================================================================

def get_plugin_names():
    """
    Get the names of all plugins in ``pyH2A.Plugins``.

    Returns
    -------
    list of str
        Names of all plugin modules whose filenames end with
        ``_Plugin.py``.
    """

    import pkgutil
    import pyH2A.Plugins

    plugin_names = []

    for module_info in pkgutil.iter_modules(
        pyH2A.Plugins.__path__
    ):

        name = module_info.name

        if name.endswith("_Plugin"):
            plugin_names.append(name)

    print(plugin_names)

    return sorted(plugin_names)

class DummyDCF:
    """
    Minimal DCF object required to initialize plugins for interface inspection.

    This object is used only for reading ``input_dict`` and ``output_dict``.
    No plugin calculations are performed.
    """

    class functional_unit:
        dimension = 'dimensionless'   # placeholder, only used for doc generation
        unit = None

def extract_interface_names(dictionary, parent_path=""):
    """
    Recursively extract interface names from a nested dictionary.

    Parameters
    ----------
    dictionary : dict
        Plugin ``input_dict`` or ``output_dict``.

    parent_path : str, optional
        Path accumulated during recursive traversal.

    Returns
    -------
    list of str
        Full hierarchical interface paths.

    Examples
    --------
    A dictionary containing::

        {
            "Battery": {
                "Design capacity": {
                    "Value": {...}
                }
            }
        }

    produces::

        [
            "Battery > Design capacity > Value"
        ]

    Notes
    -----
    The keys ``type``, ``bounds``, ``dimension``, ``optional``,
    ``description``, and ``inserted_value`` are metadata keys and
    therefore indicate that the interface definition has been reached.
    """

    interface_names = []

    metadata_keys = {
        "type",
        "bounds",
        "dimension",
        "optional",
        "description",
        "inserted_value",
    }

    for key, value in dictionary.items():

        if parent_path:
            current_path = f"{parent_path} > {key}"
        else:
            current_path = key

        if not isinstance(value, dict):
            continue

        # We have reached the definition of an interface.
        if any(metadata_key in value for metadata_key in metadata_keys):
            interface_names.append(current_path)

        # Otherwise, continue through the nested dictionary.
        else:
            interface_names.extend(
                extract_interface_names(
                    value,
                    current_path
                )
            )

    return interface_names


def get_plugin_interfaces(plugin_name):
    """
    Get the input and output interfaces of a plugin.

    Parameters
    ----------
    plugin_name : str
        Name of the plugin.

    Returns
    -------
    tuple of list
        Input interface names and output interface names.

    Notes
    -----
    The existing :func:`import_plugin` function from
    ``pyH2A.Utilities.IO`` is used to import the plugin.

    The plugin is initialized with ``run=False`` so that its
    calculations are not executed.
    """

    # Use the existing pyH2A plugin import function.
    plugin_class = import_plugin(
        plugin_name,
        plugin_module=True
    )

    # Create the plugin object without running the simulation.
    #
    # Your plugins have:
    #
    #     __init__(self, dcf, print_info, run=True)
    #
    # and therefore run=False prevents _run() from being called.
    #
    # _set_up() still creates input_dict and output_dict.
    plugin_object = plugin_class(
        DummyDCF,
        print_info=False,
        run=False
    )

    input_names = extract_interface_names(
        plugin_object.input_dict
    )

    output_names = extract_interface_names(
        plugin_object.output_dict
    )

    return input_names, output_names


def create_excel(interface_data, output_file):
    """
    Create an Excel file containing plugin interfaces.

    Parameters
    ----------
    interface_data : dict
        Dictionary containing plugin interface information.

    output_file : str
        Name of the Excel file to create.

    Returns
    -------
    None
        The Excel file is written to ``output_file``.
    """

    workbook = openpyxl.Workbook()

    worksheet = workbook.active
    worksheet.title = "Plugin Interfaces"

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------

    worksheet.append([
        "Plugin",
        "Name",
        "Type",
    ])

    # Make header bold.
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    for plugin_name in sorted(interface_data):

        for name, interface_type in interface_data[plugin_name]:

            worksheet.append([
                plugin_name,
                name,
                interface_type,
            ])

    # -------------------------------------------------------------------------
    # Formatting
    # -------------------------------------------------------------------------

    # Keep header visible while scrolling.
    worksheet.freeze_panes = "A2"

    # Add Excel filters.
    worksheet.auto_filter.ref = worksheet.dimensions

    # Set column widths.
    worksheet.column_dimensions["A"].width = 30
    worksheet.column_dimensions["B"].width = 80
    worksheet.column_dimensions["C"].width = 18

    workbook.save(output_file)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """
    Generate the Excel interface overview for all plugins.

    Returns
    -------
    None
    """

    plugin_names = get_plugin_names()

    print(f"Found {len(plugin_names)} plugins.")

    interface_data = {}

    for plugin_name in plugin_names:

        print(f"Processing {plugin_name}...")

        try:
            input_names, output_names = get_plugin_interfaces(
                plugin_name
            )

            # Use a set to combine input/output interfaces.
            interfaces = {}

            for name in input_names:
                interfaces.setdefault(name, set())
                interfaces[name].add("Input")

            for name in output_names:
                interfaces.setdefault(name, set())
                interfaces[name].add("Output")

            # Convert sets into the requested type.
            plugin_interfaces = []

            for name, types in interfaces.items():

                if types == {"Input", "Output"}:
                    interface_type = "Input/Output"

                elif types == {"Input"}:
                    interface_type = "Input"

                elif types == {"Output"}:
                    interface_type = "Output"

                else:
                    continue

                plugin_interfaces.append(
                    (name, interface_type)
                )

            # Sort interfaces alphabetically.
            plugin_interfaces.sort(
                key=lambda item: item[0]
            )

            interface_data[plugin_name] = plugin_interfaces

            print("  OK")

        except Exception as error:
            print(f"  ERROR: {error}")

    # -------------------------------------------------------------------------
    # Create Excel
    # -------------------------------------------------------------------------

    create_excel(
        interface_data,
        OUTPUT_FILE
    )

    total_interfaces = sum(
        len(interfaces)
        for interfaces in interface_data.values()
    )

    print()
    print(f"Created: {OUTPUT_FILE}")
    print(f"Plugins: {len(interface_data)}")
    print(f"Interfaces: {total_interfaces}")


if __name__ == "__main__":
    main()