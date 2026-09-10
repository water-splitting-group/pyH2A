import json
import pkgutil
from pathlib import Path

import pyH2A.Plugins as plugins
from pyH2A.Utilities.input_modification import import_plugin


METADATA_KEYS = {
    "type",
    "bounds",
    "dimension",
    "optional",
    "description",
    "inserted_value",
    "Unit",
    "_Unit"
}


class DummyDCF:
    class functional_unit:
        dimension = "dimensionless"
        unit = None


def _is_variable(data):
    """Return True if a dictionary describes a variable."""

    if not isinstance(data, dict):
        return False

    return any(
        key in data
        for key in (
            "type",
            "dimension",
            "bounds",
            "inserted_value",
        )
    )


def _walk_dict(
    data,
    path="",
    inherited_optional=False,
):
    """Recursively collect complete variable paths."""

    rows = []

    if not isinstance(data, dict):
        return rows

    optional = data.get(
        "optional",
        inherited_optional,
    )

    for key, value in data.items():

        if key in METADATA_KEYS:
            continue
        
        if key == "sum_all_tables": rows.append({"path": f"{path} > {key}", "optional": optional}); continue        
        
        current_path = (
            f"{path} > {key}"
            if path
            else str(key)
        )

        if not isinstance(value, dict):
            continue

        if _is_variable(value):
            rows.append(
                {
                    "path": current_path,
                    "optional": value.get(
                        "optional",
                        optional,
                    ),
                }
            )

            continue

        rows.extend(
            _walk_dict(
                value,
                current_path,
                optional,
            )
        )

    return rows


def _get_plugins():
    """Discover all pyH2A plugins."""

    plugin_modules = []

    for module in pkgutil.iter_modules(
        plugins.__path__
    ):
        if module.name.endswith("_Plugin"):
            plugin_modules.append(module.name)

    return sorted(plugin_modules)


def _load_plugin(plugin_module_name):
    """Load a plugin without running a model."""

    plugin_class = import_plugin(
        plugin_module_name,
        plugin_module=True,
    )

    return plugin_class(
        DummyDCF,
        print_info=False,
        run=False,
    )


def _collect_plugin_data(plugin_module_name):
    """Collect input and output paths for one plugin."""

    plugin = _load_plugin(
        plugin_module_name
    )

    plugin_name = plugin_module_name.removesuffix(
        "_Plugin"
    )

    rows = []

    for row in _walk_dict(
        plugin.input_dict
    ):
        rows.append(
            {
                "plugin": plugin_name,
                "path": row["path"],
                "direction": "Input",
                "optional": row["optional"],
            }
        )

    for row in _walk_dict(
        plugin.output_dict
    ):
        rows.append(
            {
                "plugin": plugin_name,
                "path": row["path"],
                "direction": "Output",
                "optional": row["optional"],
            }
        )

    return rows


def _combine_input_output(rows):
    """Combine identical input and output paths."""

    combined = {}

    for row in rows:

        key = (
            row["plugin"],
            row["path"],
        )

        if key not in combined:
            combined[key] = row.copy()
            continue

        combined[key]["direction"] = "Input/Output"

        combined[key]["optional"] = (
            combined[key]["optional"]
            or row["optional"]
        )

    return list(combined.values())


def _write_json(rows, output_path):
    """Write rows to a JSON file."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            rows,
            file,
            indent=4,
        )


def generate():
    """Generate Plugin I/O data for the documentation."""

    repository_root = (
        Path(__file__).resolve().parents[3]
    )

    data_path = (
        repository_root
        / "doc"
        / "data"
        / "io_data.json"
    )

    rows = []

    for plugin_module_name in _get_plugins():
        rows.extend(
            _collect_plugin_data(
                plugin_module_name
            )
        )

    rows = _combine_input_output(
        rows
    )

    rows.sort(
        key=lambda row: (
            row["path"],
            row["plugin"],
        )
    )

    _write_json(
        rows,
        data_path,
    )
    
    print(
        f"Generated Plugin I/O data: "
        f"{data_path}"
    )

    return data_path


if __name__ == "__main__":
    generate()