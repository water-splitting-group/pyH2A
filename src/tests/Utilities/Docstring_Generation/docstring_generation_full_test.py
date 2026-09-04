from pyH2A.Plugins.Battery_Plugin import Battery_Plugin
from pyH2A.Utilities.docstring_generation import generate_docstring


def test_docstring_generation_full():
    """Test the full automatic doc generation feature for the battery plugin."""

    class DocDCF:
        class functional_unit:
            dimension = 'dimensionless'

        unit = None

    battery_plugin = Battery_Plugin(DocDCF, False, False)

    input_dict = battery_plugin.input_dict
    output_dict = battery_plugin.output_dict

    summary = """
        Simulation of electricity storage using a battery.
        Simulation assumes that battery is charged and completely discharged every day.
        (no electricity storage across days, only one discharge per day, not multiple ones).
    """

    auto_gen_doc = generate_docstring(summary, input_dict, output_dict)

    correct_doc = """Simulation of electricity storage using a battery.
Simulation assumes that battery is charged and completely discharged every day.
(no electricity storage across days, only one discharge per day, not multiple ones).

Parameters
----------

Time
----

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25 25

   * - Name
     - Value
     - Unit
     - optional
     - description
   * - ``Years``
     - | type: dict
       | bounds: (None, None)
     - | dimension: dimensionless
     - False
     - Dictionary containing all time-related quantities.

Power Generation
----------------

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25 25

   * - Name
     - Value
     - Unit
     - optional
     - description
   * - ``Available energy (daily)``
     - | type: dict
       | bounds: (0, None)
     - | dimension: energy
     - False
     -  Available energy, daily basis, dictionary of years.

Battery
-------

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25 25

   * - Name
     - Value
     - Unit
     - optional
     - description
   * - ``Design capacity``
     - | type: int or float
       | bounds: (0, None)
     - | dimension: energy
     - False
     - Full design capacity of battery.
   * - ``Lowest discharge level``
     - | type: int or float
       | bounds: (0, 1)
     - | dimension: dimensionless
     - False
     - Lowest level to which battery can be discharged.
   * - ``Capacity loss per year``
     - | type: int or float
       | bounds: (0, 1)
     - | dimension: dimensionless
     - False
     - Loss of capacity per year.
   * - ``Round trip efficiency``
     - | type: int or float
       | bounds: (0, 1)
     - | dimension: dimensionless
     - False
     - Round trip efficiency of battery.

Outputs
-------

Power Generation
----------------

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Name
     - Value
     - description
     - optional
   * - ``Stored energy (daily)``
     - | inserted_value: yearly_recovered_energy
       | type: dict
       | dimension: energy
     - Energy stored in battery daily (dictionary of years)
     - False
   * - ``Available energy (daily)``
     - | inserted_value: yearly_unstored_energy
       | type: dict
       | dimension: energy
     - Available energy, daily basis, dictionary of years - energy which has not been stored in battery
     - False
   * - ``Available energy (hourly)``
     - | inserted_value: Quantity(0, 'J')
       | type: float
       | dimension: energy
     - Available energy is set to zero, since available energy is now only in daily format.
     - False
"""

    assert auto_gen_doc == correct_doc