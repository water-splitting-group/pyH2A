from pathlib import Path
import json
import pkgutil

import pyH2A.Plugins as Plugins
from pyH2A.Utilities.input_modification import import_plugin


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = PROJECT_ROOT / "doc" / "data" / "io_data.json"

METADATA_KEYS = {
    "type",
    "bounds",
    "dimension",
    "optional",
    "description",
    "inserted_value",
}


class DummyDCF:
    class functional_unit:
        dimension = "dimensionless"
        unit = None


def is_interface(value):
    return (
        isinstance(value, dict)
        and any(key in value for key in METADATA_KEYS)
    )


def read_tree(tree, plugin_name, direction, path=""):
    rows = []

    if not isinstance(tree, dict):
        return rows

    for name, value in tree.items():

        current_path = f"{path}.{name}" if path else name

        if is_interface(value):

            rows.append({
                "plugin": plugin_name,
                "path": current_path,
                "direction": direction,
                "type": value.get("type", ""),
                "dimension": value.get("dimension", ""),
                "description": value.get("description", ""),
                "optional": bool(value.get("optional", False)),
            })

        elif isinstance(value, dict):

            rows.extend(
                read_tree(
                    value,
                    plugin_name,
                    direction,
                    current_path,
                )
            )

    return rows


def find_plugins():
    return sorted(
        module.name
        for module in pkgutil.iter_modules(Plugins.__path__)
        if module.name.endswith("_Plugin")
    )


def load_plugin(name):
    plugin_class = import_plugin(
        name,
        plugin_module=True,
    )

    return plugin_class(
        DummyDCF,
        print_info=False,
        run=False,
    )


def generate():

    print("Generating Plugin I/O data...")

    plugins = find_plugins()

    print(f"Found {len(plugins)} plugins.")

    rows = []

    for name in plugins:

        print(f"  {name}")

        plugin = load_plugin(name)

        rows.extend(
            read_tree(
                plugin.input_dict,
                name,
                "Input",
            )
        )

        rows.extend(
            read_tree(
                plugin.output_dict,
                name,
                "Output",
            )
        )

    # Merge Input + Output entries with the same path.
    merged = {}

    for row in rows:

        key = (
            row["plugin"],
            row["path"],
        )

        if key not in merged:
            merged[key] = row

        else:
            merged[key]["direction"] = "Input/Output"

    rows = sorted(
        merged.values(),
        key=lambda row: (
            row["plugin"].lower(),
            row["path"].lower(),
        ),
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            rows,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Done. Wrote {len(rows)} interfaces to:"
    )
    print(f"  {OUTPUT}")


if __name__ == "__main__":
    generate()