import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pint

from pyH2A.Utilities.input_modification import process_table
from pyH2A.Utilities.Unit_handler.Unit_conversion import UnitConversionHandler


class InputResolver:
    """Resolve and validate inputs from dcf.inp based on a schema-like input_dict."""

    _SPECIAL_KEYS = {"optional", "description"}

    def __init__(self, dcf, plugin_name: Optional[str] = None, unit_registry: Optional[pint.UnitRegistry] = None):
        self.dcf = dcf
        self.plugin_name = plugin_name or "input_resolver"
        self.ureg = unit_registry or pint.UnitRegistry()
        self.converter = UnitConversionHandler()
        self.converter.ureg = self.ureg
        self.converter.dimension_handler.ureg = self.ureg
        self._ensure_currency_units()

    def resolve(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}

        for key, spec in input_dict.items():
            if self._is_param_spec(spec):
                resolved[key] = self._resolve_param_spec(spec)
                continue

            if self._is_wildcard_key(key):
                resolved.update(self._resolve_table_group(key, spec))
            else:
                resolved[key] = self._resolve_table(key, spec)

        return resolved

    def _ensure_currency_units(self) -> None:
        try:
            self.ureg.Unit("USD")
        except Exception:
            self.ureg.define("USD = [currency]")
        try:
            self.ureg.Unit("m3")
        except Exception:
            self.ureg.define("m3 = meter ** 3")

    def _is_param_spec(self, spec: Any) -> bool:
        return isinstance(spec, dict) and any(k in spec for k in ("top_level", "mid_level", "lower_level", "bottom_level"))

    def _is_wildcard_key(self, key: str) -> bool:
        return "<...>" in key

    def _resolve_param_spec(self, spec: Dict[str, Any]) -> Any:
        top_key = spec.get("top_level")
        mid_key = spec.get("mid_level")
        bottom_key = spec.get("lower_level") or spec.get("bottom_level")

        if top_key is None or mid_key is None or bottom_key is None:
            raise KeyError(
                f"{self.plugin_name}: Parameter spec missing required key(s).")

        if self._is_wildcard_key(top_key):
            return self._resolve_table_group(top_key, {"<...>": {bottom_key: spec}})

        if self._is_wildcard_key(mid_key):
            return self._resolve_table(top_key, {"<...>": {bottom_key: spec}})

        self._process_table_for_spec(top_key, {mid_key: {bottom_key: spec}})
        return self._resolve_specific_value(top_key, mid_key, bottom_key, spec)

    def _resolve_table_group(self, top_pattern: str, table_spec: Dict[str, Any]) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}
        matching_top_keys = self._match_keys(self.dcf.inp.keys(), top_pattern)

        if not matching_top_keys:
            raise KeyError(
                f"{self.plugin_name}: No tables found matching pattern '{top_pattern}'.")

        for top_key in matching_top_keys:
            resolved[top_key] = self._resolve_table(top_key, table_spec)

        return resolved

    def _resolve_table(self, top_key: str, table_spec: Dict[str, Any]) -> Dict[str, Any]:
        actual_top_key = self._find_key_case_insensitive(self.dcf.inp, top_key)
        if actual_top_key is None:
            raise KeyError(f"{self.plugin_name}: Missing table '{top_key}'.")

        self._process_table_for_spec(actual_top_key, table_spec)

        if "<...>" in table_spec:
            row_spec = table_spec["<...>"]
            return self._resolve_flexible_rows(actual_top_key, row_spec)

        resolved_table: Dict[str, Any] = {}
        for mid_key, row_spec in table_spec.items():
            if mid_key in self._SPECIAL_KEYS:
                continue
            actual_mid_key = self._find_key_case_insensitive(
                self.dcf.inp[actual_top_key], mid_key)
            if actual_mid_key is None:
                if row_spec.get("optional") is True:
                    continue
                raise KeyError(
                    f"{self.plugin_name}: Missing key '{actual_top_key} > {mid_key}'.")
            row = self.dcf.inp[actual_top_key][actual_mid_key]
            resolved_table[actual_mid_key] = self._resolve_row(
                actual_top_key, actual_mid_key, row, row_spec)

        return resolved_table

    def _resolve_flexible_rows(self, top_key: str, row_spec: Dict[str, Any]) -> Dict[str, Any]:
        resolved_rows: Dict[str, Any] = {}
        for mid_key, row in self.dcf.inp[top_key].items():
            resolved_rows[mid_key] = self._resolve_row(
                top_key, mid_key, row, row_spec)
        return resolved_rows

    def _resolve_specific_value(self, top_key: str, mid_key: str, bottom_key: str, value_spec: Dict[str, Any]) -> Any:
        actual_mid_key = self._find_key_case_insensitive(
            self.dcf.inp[top_key], mid_key)
        if actual_mid_key is None:
            raise KeyError(
                f"{self.plugin_name}: Missing key '{top_key} > {mid_key}'.")

        row = self.dcf.inp[top_key][actual_mid_key]
        if bottom_key not in row:
            raise KeyError(
                f"{self.plugin_name}: Missing key '{top_key} > {actual_mid_key} > {bottom_key}'.")

        row_spec = {bottom_key: value_spec}
        unit_key = "Unit" if bottom_key == "Value" else bottom_key.replace(
            "_Value", "_Unit")
        if unit_key in row:
            row_spec[unit_key] = {"dimension": value_spec.get("dimension")}

        return self._resolve_row(top_key, actual_mid_key, row, row_spec).get(bottom_key)

    def _resolve_row(self, top_key: str, mid_key: str, row: Dict[str, Any], row_spec: Dict[str, Any]) -> Dict[str, Any]:
        resolved_row: Dict[str, Any] = {}

        value_keys = [k for k in row_spec.keys() if "Value" in k]
        for key, spec in row_spec.items():
            if key in self._SPECIAL_KEYS:
                continue

            if key not in row:
                if row_spec.get("optional") is True:
                    continue
                raise KeyError(
                    f"{self.plugin_name}: Missing key '{top_key} > {mid_key} > {key}'.")

            value = row[key]

            if "Value" in key:
                unit_key = "Unit" if key == "Value" else key.replace(
                    "_Value", "_Unit")
                unit_spec = row_spec.get(unit_key, {})
                if unit_key not in row:
                    raise KeyError(
                        f"{self.plugin_name}: Missing unit '{top_key} > {mid_key} > {unit_key}' for '{key}'."
                    )

                self._validate_value(value, spec, top_key,
                                     mid_key, key, check_bounds=False)
                resolved_value = self._convert_value_with_unit(
                    value,
                    row[unit_key],
                    unit_spec.get("dimension"),
                    top_key,
                    mid_key,
                    key,
                )
                bounds = spec.get("bounds")
                if bounds is not None:
                    self._check_bounds_on_quantity(
                        resolved_value, bounds, top_key, mid_key, key)
                resolved_row[key] = resolved_value

            elif key.endswith("_Unit") or key == "Unit":
                continue

            else:
                self._validate_value(value, spec, top_key,
                                     mid_key, key, check_bounds=True)
                if "options" in spec and value not in spec["options"]:
                    raise ValueError(
                        f"{self.plugin_name}: Invalid option '{value}' for '{top_key} > {mid_key} > {key}'."
                    )
                resolved_row[key] = value

        for key in value_keys:
            resolved_row.setdefault(key, resolved_row.get(key))

        return resolved_row

    def _validate_value(
        self,
        value: Any,
        spec: Dict[str, Any],
        top_key: str,
        mid_key: str,
        key: str,
        check_bounds: bool,
    ) -> None:
        expected_types = spec.get("type")
        bounds = spec.get("bounds")
        expected_length = spec.get("length")

        if expected_types:
            expected_tuple = self._normalize_types(expected_types)
            if not isinstance(value, expected_tuple):
                raise TypeError(
                    f"{self.plugin_name}: '{top_key} > {mid_key} > {key}' expected {expected_tuple}, got {type(value)}."
                )

        if expected_length is not None and hasattr(value, "__len__"):
            if len(value) != expected_length:
                raise ValueError(
                    f"{self.plugin_name}: '{top_key} > {mid_key} > {key}' expected length {expected_length}."
                )

        if check_bounds and bounds is not None:
            self._check_bounds(value, bounds, top_key, mid_key, key)

    def _convert_value_with_unit(
        self,
        value: Any,
        unit_str: str,
        dimension: Optional[str],
        top_key: str,
        mid_key: str,
        key: str,
    ) -> Any:
        normalized_unit = self._normalize_unit(unit_str)

        if isinstance(value, dict):
            return {k: self._convert_single_value(v, normalized_unit) for k, v in value.items()}

        return self._convert_single_value(value, normalized_unit)

    def _convert_single_value(self, value: Any, unit: str) -> pint.Quantity:
        if unit == "percent":
            return (value * self.ureg.Unit("percent")).to("dimensionless")
        try:
            return self.converter.convert(value, unit)
        except Exception:
            return value * self.ureg.Unit(unit)

    def _normalize_unit(self, unit_str: str) -> str:
        unit_str = unit_str.replace("$", "USD")
        unit_str = unit_str.replace(
            "liters", "liter").replace("litres", "liter")
        unit_str = unit_str.replace("years", "year")
        unit_str = unit_str.replace("%", "percent")
        return unit_str

    def _check_bounds(self, value: Any, bounds: Tuple[Optional[float], Optional[float]], top_key: str, mid_key: str, key: str) -> None:
        lower, upper = bounds
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                self._check_bounds(sub_value, bounds, top_key,
                                   mid_key, f"{key}.{sub_key}")
            return

        values = np.asarray(value) if isinstance(value, np.ndarray) else value
        if lower is not None:
            if np.any(values < lower):
                raise ValueError(
                    f"{self.plugin_name}: '{top_key} > {mid_key} > {key}' below lower bound {lower}.")
        if upper is not None:
            if np.any(values > upper):
                raise ValueError(
                    f"{self.plugin_name}: '{top_key} > {mid_key} > {key}' above upper bound {upper}.")

    def _check_bounds_on_quantity(
        self,
        value: Any,
        bounds: Tuple[Optional[float], Optional[float]],
        top_key: str,
        mid_key: str,
        key: str,
    ) -> None:
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                self._check_bounds_on_quantity(
                    sub_value, bounds, top_key, mid_key, f"{key}.{sub_key}")
            return
        if hasattr(value, "magnitude"):
            self._check_bounds(value.magnitude, bounds, top_key, mid_key, key)
            return
        self._check_bounds(value, bounds, top_key, mid_key, key)

    def _normalize_types(self, expected_types: Any) -> Tuple[type, ...]:
        if isinstance(expected_types, set):
            types = list(expected_types)
        elif isinstance(expected_types, (list, tuple)):
            types = list(expected_types)
        else:
            types = [expected_types]

        if float in types and np.floating not in types:
            types.append(np.floating)
        if float in types and int not in types:
            types.append(int)
        if float in types and np.integer not in types:
            types.append(np.integer)
        if int in types and np.integer not in types:
            types.append(np.integer)

        return tuple(types)

    def _process_table_for_spec(self, top_key: str, table_spec: Dict[str, Any]) -> None:
        bottom_keys = self._collect_value_keys(table_spec)
        if not bottom_keys:
            return

        safe_bottom_keys: List[str] = []
        for bottom_key in bottom_keys:
            has_non_scalar_value = False
            for row in self.dcf.inp.get(top_key, {}).values():
                if not isinstance(row, dict) or bottom_key not in row:
                    continue
                value = row[bottom_key]
                if isinstance(value, (dict, np.ndarray)):
                    has_non_scalar_value = True
                    break
            if not has_non_scalar_value:
                safe_bottom_keys.append(bottom_key)

        if safe_bottom_keys:
            process_table(self.dcf.inp, top_key, safe_bottom_keys)

    def _collect_value_keys(self, table_spec: Dict[str, Any]) -> List[str]:
        if "<...>" in table_spec:
            row_spec = table_spec["<...>"]
            return [key for key in row_spec.keys() if "Value" in key]

        bottom_keys: List[str] = []
        for _, row_spec in table_spec.items():
            if isinstance(row_spec, dict):
                for key in row_spec.keys():
                    if "Value" in key:
                        bottom_keys.append(key)
        return list(dict.fromkeys(bottom_keys))

    def _match_keys(self, keys: Iterable[str], pattern: str) -> List[str]:
        regex = re.escape(pattern).replace(re.escape("<...>"), ".*")
        compiled = re.compile(f"^{regex}$")
        return [key for key in keys if compiled.match(key)]

    def _find_key_case_insensitive(self, dictionary: Dict[str, Any], key: str) -> Optional[str]:
        if key in dictionary:
            return key
        lowered = key.lower()
        for existing in dictionary.keys():
            if existing.lower() == lowered:
                return existing
        return None


def input_resolver(dcf, input_dict: Dict[str, Any], plugin_name: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper for InputResolver."""
    return InputResolver(dcf, plugin_name=plugin_name).resolve(input_dict)
