"""
Unit dimension detection and validation.

This module provides :class:`UnitDimensionHandler`, which maps a unit string
(e.g. ``'kWh/kg'``) to a human-readable dimension label (e.g. ``'energy'``) by
using pint to inspect the unit's dimensionality and looking it up in the
:data:`~pyH2A.Utilities.Unit_handler.constants.DIMENSION_MAPPING` table.

Custom units (e.g. ``USD`` for currency) that are not part of pint's default
registry are registered at initialisation time using
:data:`~pyH2A.Utilities.Unit_handler.constants.CUSTOM_UNITS`.  Unit name
aliases that pint cannot register as identifiers (e.g. ``$`` → ``USD``) are
normalised before parsing via
:data:`~pyH2A.Utilities.Unit_handler.constants.UNIT_ALIASES`.
"""
import pint
from pyH2A.Utilities.Unit_handler.constants import CUSTOM_UNITS, DIMENSION_MAPPING, UNIT_ALIASES


class UnitDimensionHandler:
    """
    Map unit strings to dimension labels using pint.

    This handler resolves the physical dimension of a unit string by combining
    pint's dimensionality inspection with the project's curated
    :data:`~pyH2A.Utilities.Unit_handler.constants.DIMENSION_MAPPING` table.
    It supports custom units (e.g. ``USD``) and non-identifier aliases
    (e.g. ``$``) that pint cannot handle natively.

    Attributes:
        ureg (pint.UnitRegistry): Registry with custom units pre-registered.

    Example::

        handler = UnitDimensionHandler()
        handler.get_dimension('kJ')        # 'energy'
        handler.get_dimension('USD/kWh')   # raises ValueError (compound)
        handler.get_dimension('$')         # 'currency'  (alias resolved)
    """

    def __init__(self):
        """
        Initialise the unit registry and register custom units.

        Iterates over :data:`~pyH2A.Utilities.Unit_handler.constants.CUSTOM_UNITS`
        and registers each entry with pint if it is not already known.  Entries
        that pint cannot register (e.g. names containing special characters) are
        silently skipped — they should instead be listed in
        :data:`~pyH2A.Utilities.Unit_handler.constants.UNIT_ALIASES` so that
        :meth:`get_dimension` can normalise them before parsing.
        """
        self.ureg = pint.UnitRegistry()
        for unit_name, definition in CUSTOM_UNITS:
            try:
                self.ureg.Unit(unit_name)
            except (pint.UndefinedUnitError, pint.errors.UndefinedUnitError):
                self.ureg.define(f"{unit_name} = {definition}")
            except Exception:
                pass

    def get_dimension(self, unit_str):
        """
        Return the dimension label for a unit string.

        The unit string is first normalised through
        :data:`~pyH2A.Utilities.Unit_handler.constants.UNIT_ALIASES` (e.g.
        ``'$'`` → ``'USD'``), then parsed by pint to obtain a dimensionality
        object, which is looked up in
        :data:`~pyH2A.Utilities.Unit_handler.constants.DIMENSION_MAPPING`.

        .. note::
            Only *simple* (single-dimension) units are supported.  Compound
            units such as ``'kWh/kg'`` have a composite dimensionality that is
            not present in ``DIMENSION_MAPPING`` and will raise ``ValueError``.
            Dimension validation of compound units is handled at a higher level
            by :class:`~pyH2A.Utilities.IO_Resolver.unit_processor.UnitProcessor`.

        Args:
            unit_str (str): Unit string to look up (e.g. ``'kJ'``, ``'USD'``,
                ``'meter**3'``, ``'$'``).

        Returns:
            str: A dimension label such as ``'energy'``, ``'mass'``,
            ``'currency'``, ``'volume'``, or ``'dimensionless'``.

        Raises:
            ValueError: If ``unit_str`` is not a valid pint unit, or if its
                dimensionality is not in ``DIMENSION_MAPPING``.

        Examples::

            handler = UnitDimensionHandler()
            handler.get_dimension('kJ')          # 'energy'
            handler.get_dimension('kilogram')    # 'mass'
            handler.get_dimension('USD')         # 'currency'
            handler.get_dimension('$')           # 'currency'
            handler.get_dimension('meter**3')    # 'volume'
            handler.get_dimension('not_a_unit')  # raises ValueError
        """
        unit_str = UNIT_ALIASES.get(unit_str, unit_str)
        try:
            unit = self.ureg.Unit(unit_str)
        except Exception:
            raise ValueError(
                f"'{unit_str}' is not a valid unit. Please provide a valid unit.")

        dimensionality_str = str(unit.dimensionality)
        dimension = DIMENSION_MAPPING.get(dimensionality_str)

        if dimension is None:
            raise ValueError(
                f"'{unit_str}' is not a recognized or supported unit in this context.")

        return dimension
