Overview of pyH2A
=================

.. contents:: Table of Contents
   :depth: 2
   :local:


1. General Principle
====================

pyH2A performs a techno-economic analysis based on discounted cash flow methodology. Its purpose is to compute financial metrics such as annual cash flows and the levelized cost of hydrogen from a combination of technical assumptions and economic parameters.

The model is not evaluated in a single global calculation. Instead, it is constructed progressively through a structured series of calculation stages. Each stage contributes technical, cost, or financial quantities that are required for the final discounted cash flow analysis.

The economic results therefore emerge from the accumulation and interaction of all preceding calculations.


2. Calculation Stages and Model State
=====================================

Throughout execution, the variables of interest are read from, updated and added to a Python dictionary that serves as the “common thread” of the calculation.

These variables include, for example:

- Technical quantities (e.g., production rates, efficiencies, lifetimes)
- Capital cost components
- Operating costs (fixed and variable)
- Financial parameters (e.g., discount rate, tax rate, depreciation schedules)
- Intermediate and final financial results

The use and calculation of these variables proceeds in the following order:


2.1. Initialisation
-------------------

- User-specified input (.md) file is parsed and converted into a dictionary.

  .. note::

     Code implementation: In ``run_pyH2A`` and in ``Discounted_Cash_Flow`` classes, ``inp`` is the dictionary containing the variables of interest:

     ``self.inp = convert_input_to_dictionary(self.input_file)``

- Financial input values such as the reference year or the inflation factor are loaded from the ``Defaults.md`` file or computed.

  .. note::

     Code implementation: In ``Discounted_Cash_Flow`` class, this step is part of the ``pre_workflow`` method call.


2.2. Plugin workflow
--------------------

The calculation is organized as an ordered series of units referred to as :ref:`plugins`.

When a plugin is executed:

- It reads the quantities it requires from the current dictionary. These quantities may originate from the input (.md) file or from previous plugins.

  .. note::

     Code implementation: Within the plugin, the ``process_table`` method call retrieves the actual value from the dictionary (``dcf.inp``). More detailed explanations about the dictionary structure and processing are provided separately.

- It performs a defined set of calculations.

- It adds new variables to the dictionary or updates some of the existing ones.

  .. note::

     Code implementation: Within the plugin, the ``insert`` method call inserts new variables, or updates existing ones, in the dictionary.

The dictionary therefore represents the evolving economic model. At any stage, it contains all quantities defined up to that point, and a plugin can only rely on what is already present when it is executed. The execution order therefore defines the logical dependency structure of the model.

.. note::

   Code implementation: The ordered execution of the plugins occurs in the ``workflow`` method inside the ``Discounted_Cash_Flow`` class.


2.3. Final financial evaluation
-------------------------------

The final financial quantities of interest (e.g. levelized cost of hydrogen) are calculated.

.. note::

   Code implementation: In ``Discounted_Cash_Flow`` class, this step is part of the ``post_workflow`` method call.


3. Default plugins and Scenario-specific plugins
================================================

The calculation sequence used in pyH2A is based on two categories of plugins:

1. Default plugins, which define the common financial structure of the model.
2. Scenario-specific plugins, which introduce calculations particular to a given hydrogen production pathway or study.

The default plugins are specified in the ``Defaults.md`` file. They are always included in a calculation and provide the general discounted cash flow framework. This includes the construction of capital costs, operating costs, replacement costs, and the financial evaluation that leads to metrics such as annual cash flows and the levelized cost of hydrogen.

Scenario-specific plugins are specified in the user-defined input (.md) file. They typically introduce technical calculations (e.g., production performance, equipment sizing, technology-dependent costs) whose results enter the financial structure defined by the defaults.

At runtime, pyH2A combines the predefined default plugins with the scenario-specific plugins into a single ordered sequence. The relative position of each plugin determines how technical quantities are incorporated into capital and operating costs, and how these costs ultimately influence the discounted cash flow results.

Detailed guidance on plugin ordering is provided separately.


4. Economic Logic Implemented by the Default Structure
======================================================

The default financial structure follows a defined economic progression:

- Production definition: The hydrogen production level is established or scaled to the target output, providing the reference for subsequent cost calculations.

  .. note::

     Code implementation: this is handled by the ``Production_Scaling_Plugin``.

- Capital costs: The total investment required to construct the system at the specified production scale is calculated.

  .. note::

     Code implementation: this is handled by the ``Capital_Cost_Plugin``.

- Equipment replacement: The financial impact of component lifetimes shorter than the overall analysis period is incorporated.

  .. note::

     Code implementation: this is handled by the ``Replacement_Plugin``.

- Operating costs: Costs are separated into fixed and variable components. Fixed costs are independent of production level, while variable costs depend on hydrogen production.

  .. note::

     Code implementation: this is handled by the ``Fixed_Operating_Cost_Plugin`` and ``Variable_Operating_Cost_Plugin``.

After these quantities have been established (production, capital costs, replacement costs, and operating costs) the discounted cash flow calculation is performed. Financial parameters such as discount rate, depreciation treatment, and taxation are applied to compute annual cash flows over the project lifetime. From these, net present value–based indicators, including the levelized cost of hydrogen, are derived.

The economic results therefore arise from a clearly structured sequence: production definition, cost construction, and financial evaluation, implemented through the default plugin sequence.