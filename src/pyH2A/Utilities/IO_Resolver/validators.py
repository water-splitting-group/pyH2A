from typing import Any, Dict, Optional, Tuple
import numpy as np


class ValidationError(Exception):
    """Raised when a value fails validation."""

    pass


def normalize_types(expected_types: Any) -> Tuple[type, ...]:
    """
    Normalize type specifications to a tuple of types.

    Automatically includes numpy equivalents for numeric types
    to ensure proper isinstance() checks work with numpy values.

    Args:
        expected_types: A type, or set/list/tuple of types.

    Returns:
        Tuple of types suitable for isinstance() checking.

    Example:
        >>> normalize_types(float)
        (float, np.floating, int, np.integer)
        >>> normalize_types({str, int})
        (str, int, np.integer)
    """
    if isinstance(expected_types, set):
        types = list(expected_types)
    elif isinstance(expected_types, (list, tuple)):
        types = list(expected_types)
    else:
        types = [expected_types]

    # Add numpy equivalents for numeric types
    if float in types and np.floating not in types:
        types.append(np.floating)
    if float in types and int not in types:
        types.append(int)
    if float in types and np.integer not in types:
        types.append(np.integer)
    if int in types and np.integer not in types:
        types.append(np.integer)

    return tuple(types)


def check_bounds(
    value: Any,
    bounds: Tuple[Optional[float], Optional[float]],
    context: str,
) -> None:
    """
    Validate that a value falls within specified bounds.

    Handles scalar values, numpy arrays, and nested dictionaries.

    Args:
        value: The value to check.
        bounds: Tuple of (lower_bound, upper_bound). Either can be None.
        context: Description of the value location for error messages.

    Raises:
        ValueError: If value is outside the specified bounds.

    Example:
        >>> check_bounds(5, (0, 10), "my_param")  # OK
        >>> check_bounds(-1, (0, 10), "my_param")  # Raises ValueError
    """
    lower, upper = bounds

    # Handle nested dictionaries recursively
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            check_bounds(sub_value, bounds, f"{context}.{sub_key}")
        return

    # Convert to array for uniform handling
    values = np.asarray(value) if isinstance(value, np.ndarray) else value

    if lower is not None and np.any(values < lower):
        raise ValueError(f"'{context}' below lower bound {lower}.")

    if upper is not None and np.any(values > upper):
        raise ValueError(f"'{context}' above upper bound {upper}.")


def check_bounds_on_quantity(
    value: Any,
    bounds: Tuple[Optional[float], Optional[float]],
    context: str,
) -> None:
    """
    Validate bounds on a pint Quantity or plain value.

    Extracts the magnitude from Quantity objects before checking bounds.

    Args:
        value: A pint Quantity, dict of Quantities, or plain numeric value.
        bounds: Tuple of (lower_bound, upper_bound). Either can be None.
        context: Description of the value location for error messages.

    Raises:
        ValueError: If value is outside the specified bounds.
    """
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            check_bounds_on_quantity(sub_value, bounds, f"{context}.{sub_key}")
        return

    if hasattr(value, "magnitude"):
        check_bounds(value.magnitude, bounds, context)
        return

    check_bounds(value, bounds, context)


def validate_type(
    value: Any,
    expected_types: Any,
    context: str,
) -> None:
    """
    Validate that a value is of an expected type.

    Args:
        value: The value to check.
        expected_types: Expected type(s) - a type or collection of types.
        context: Description of the value location for error messages.

    Raises:
        TypeError: If value is not of an expected type.
    """
    if expected_types is None:
        return

    expected_tuple = normalize_types(expected_types)
    if not isinstance(value, expected_tuple):
        raise TypeError(
            f"'{context}' expected {expected_tuple}, got {type(value)}."
        )


def validate_length(
    value: Any,
    expected_length: int,
    context: str,
) -> None:
    """
    Validate that a value has an expected length.

    Args:
        value: The value to check (must have __len__).
        expected_length: The expected length.
        context: Description of the value location for error messages.

    Raises:
        ValueError: If value has incorrect length.
    """
    if not hasattr(value, "__len__"):
        return

    if len(value) != expected_length:
        raise ValueError(f"'{context}' expected length {expected_length}.")


def validate_options(
    value: Any,
    options: Any,
    context: str,
) -> None:
    """
    Validate that a value is one of the allowed options.

    Args:
        value: The value to check.
        options: Collection of allowed values.
        context: Description of the value location for error messages.

    Raises:
        ValueError: If value is not in the allowed options.
    """
    if options is None:
        return

    if value not in options:
        raise ValueError(f"Invalid option '{value}' for '{context}'.")


def validate_value(
    value: Any,
    spec: Dict[str, Any],
    context: str,
    check_bounds_flag: bool = True,
) -> None:
    """
    Perform full validation of a value against its specification.

    Validates type, length, and optionally bounds based on the spec.

    Args:
        value: The value to validate.
        spec: Specification dict with optional keys: 'type', 'length', 'bounds'.
        context: Description of the value location for error messages.
        check_bounds_flag: Whether to check bounds (default True).

    Raises:
        TypeError: If type validation fails.
        ValueError: If length or bounds validation fails.

    Example:
        >>> spec = {"type": float, "bounds": (0, 100)}
        >>> validate_value(50.0, spec, "my_param")  # OK
        >>> validate_value("bad", spec, "my_param")  # Raises TypeError
    """
    expected_types = spec.get("type")
    bounds = spec.get("bounds")
    expected_length = spec.get("length")

    if expected_types:
        validate_type(value, expected_types, context)

    if expected_length is not None:
        validate_length(value, expected_length, context)

    if check_bounds_flag and bounds is not None:
        check_bounds(value, bounds, context)
