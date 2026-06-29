.. _Overview:


Overview of pyH2A
=================

.. contents:: Table of Contents
   :depth: 2
   :local:
   :class: this-will-duplicate-information-and-it-is-still-useful-here   

This page introduces the general logic of pyH2A, as well as its concrete implementation in the pyh2A code.


0. Navigating the pyH2A Codebase
--------------------------------

The pyH2A codebase is organized into a set of folders that separate the core calculation workflow, the :ref:`plugins`, and supporting functions for handling inputs / outputs / post-processing (referred to as "utilities").

The main entry point of the code is located in:

::

   pyH2A/src/pyH2A/


Overview of the folder structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- To understand how a calculation is executed, start with ``run_pyH2A.py`` and ``Discounted_Cash_Flow.py``.
- To follow or modify the calculation steps, look at the files in the :ref:`plugins` folder.
- To understand how input and output data are read and processed, refer to the ``Utilities`` folder.
- To locate default parameters and the standard calculation structure, see ``Config/Defaults.md``.
- To explore example inputs or test cases, consult the ``tests`` and ``Lookup_Tables`` folders.

The structure below can be read as a map indicating where each of these elements is implemented.
::

   pyH2A/src/pyH2A/
   │
   ├── run_pyH2A.py
   │   Entry point of the calculation:
   │   - Initializes the model: calls methods to read and convert the input (.md) file into a dictionary
   │   - Launches the base case (single point) calculation: calls Discounted_Cash_Flow and puts the results in self.base_case
   │   - Launches the eventual meta workflow (Analysis modules)
   │
   ├── Discounted_Cash_Flow.py
   │   Core of the techno-economic calculation:
   │   - Defines the pre_workflow, workflow and post_workflow (see section 2 below)
   │
   ├── LCA/
   │   └── LCA.py
   │       Life Cycle Analysis module:
   │       - Contains the ``LCA`` class 
   │       - Called by ``Discounted_Cash_Flow`` to run an LCA on a single point
   │
   ├── Config/
   │   └── Defaults.md
   │       Default configuration:
   │       - Defines the default plugin workflow (sections 3 and 4 below)
   │       - Contains financial input values (section 2.1 below)
   │
   ├── Plugins/
   │   Contains all ``*_Plugin`` files:
   │   - Each plugin processes its necessary inputs (input_resolver_function call), performs calculations, and inserts the results (output_resolver call) in the dcf.inp dictionary (see part 2.2)
   │   - Plugins are executed sequentially in the workflow
   │
   ├── Utilities/
   │   │
   │   └── IO/ 
   │   │   Modules for handling inputs and outputs
   │   │   └── input_resolver.py 
   │   │   │   - Orchestrates the resolution of the inputs: retrieving values, conversion into Quantity objects and sanity checks
   │   │   │   - Contains the input_resolver_function and the related functions 
   │   │   │
   │   │   └── output_inserter.py 
   │   │       - Orchestrates the resolution of the outputs: dimension and type checks, insertion in the dcf.inp dictionary
   │   │       - Contains the output_inserter_function and the related functions 
   │   │
   │   └── Unit_Handler/ 
   │   │   └── quantity.py    
   │   │   │   - Modules for creating ``quantity`` objects, which associate a value to a unit
   │   │   └── config.py       
   │   │       - Contains the conversion factors between the base units (considered as the reference) and the units that are supported in the input file
   │   │   
   │   └── check_functions.py 
   │   │    - Functions performing sanity checks, called by the input resolver and by the output inserter
   │   │            
   │   └── input_modification.py 
   │   │   Functions for handling inputs and outputs, that is: to modify the dcf.inp dictionary :     
   │   │   - Conversion of input (.md) files into the dictionary structure
   │   │   - Functions such as ``convert_input_to_dictionary``, ``process_input``, ``insert``, ``sum_table``  etc. 
   │   │
   │   └── plugin_input_output_processing.py
   │   │   Serves to generate an input file template, based on a user-specified Workflow    
   │   │
   │   └── output_utilities.py
   │   │   Serves to define the final outputs format
   │   │
   │   └── find_nearest.py  
   │        - used in plugins (for example to identify the year index corresponding to a certain duration), and in some analysis modules   
   │
   ├── Analysis/
   │   Advanced analysis modules (not used in the base case calculation):
   │   - Monte_Carlo analysis, Comparative_MC_analysis
   │   - Cost_Contributions_Analysis
   │   - Sensitivity_Analysis 
   │   - Optimization_Analysis
   │   - Development_Distance_Time_Analysis
   │   - Waterfall_Analysis
   │
   └── Lookup_Tables/
       Input data for example calculations:
       - Contains files used as inputs in provided examples (for example: hourly irradiation data)


Additional test structure
~~~~~~~~~~~~~~~~~~~~~~~~~

Files are available to test pyH2A execution.

::

   pyH2A/
   │
   ├── e2e_lcoh/
   │   Executable test file for various complete hydrogen production pathways, checking if the calcualted levelized cost of hydrogen corresponds to the expected value
   |
   ├── end_to_end/
   │   Input (.md) files for the e2e_lcoh/lcoh_test.py test 
   │
   ├── plugins/
   │   Tests for individual plugin robustness
   │
   └── Utilities/
       Tests for input/output processing:
       - Verifies correct handling of dictionary entries and data resolution


1. General Principle of pyH2A
-----------------------------

pyH2A performs a techno-economic analysis based on discounted cash flow methodology. Its purpose is to compute financial metrics such as annual cash flows and the levelized cost of a deliverable (e.g. hydrogen) from a combination of technical assumptions and economic parameters.

The model is not evaluated in a single global calculation. Instead, it is constructed progressively through a structured series of calculation stages. Each stage contributes technical, cost, or financial quantities that are required for the final discounted cash flow analysis.

The economic results therefore emerge from the accumulation and interaction of all preceding calculations.


2. Calculation Stages and Model State
-------------------------------------

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

  .. admonition:: Code implementation

     In ``run_pyH2A`` and in ``Discounted_Cash_Flow`` classes, ``inp`` is the dictionary containing the variables of interest:

     ``self.inp = convert_input_to_dictionary(self.input_file)``

- Financial input values such as the reference year or the inflation factor are loaded from the ``Defaults.md`` file or computed.

  .. admonition:: Code implementation

     In ``Discounted_Cash_Flow`` class, this step is part of the ``pre_workflow`` method call.


2.2. Plugin workflow
--------------------

The calculation is organized as an ordered series of units referred to as :ref:`plugins`.

When a plugin is executed:

- It reads the variables it requires from the current dictionary. These variables may originate from the input (.md) file or from previous plugins.

  .. admonition:: Code implementation

     Within the plugin, the ``input_resolver_function`` call retrieves the actual value from the shared dictionary (``dcf.inp``), applies checks and creates the Quantity objects from the respective variables. 
     The Quantity objects are stored in a local dictionary called ``self.input_dict_resolved``
     More detailed explanations about the dictionary structure and processing :ref:`are provided separately <dictionary-structure>`.

- It performs a defined set of calculations.

- It adds new variables to the dictionary or updates some of the existing ones.

  .. admonition:: Code implementation

     Within the plugin, the ``output_inserter_function`` method call inserts new variables, or updates existing ones, in the dcf.inp dictionary.

The ``dcf.inp`` dictionary therefore represents the evolving economic model. At any stage, it contains all quantities defined up to that point, and a plugin can only rely on what is already present when it is executed. 
The execution order therefore defines the logical dependency structure of the model.

.. admonition:: Code implementation

   The ordered execution of the plugins occurs in the ``workflow`` method inside the ``Discounted_Cash_Flow`` class.


2.3. Final financial evaluation
-------------------------------

The final financial quantities of interest (e.g. levelized cost of product) are calculated.

.. admonition:: Code implementation

   In the ``Discounted_Cash_Flow`` class, this step is part of the ``post_workflow`` method call.



3. Default plugins and Scenario-specific plugins
------------------------------------------------

The calculation sequence used in pyH2A is based on two categories of plugins:

1. Default plugins, which define the common financial structure of the model.
2. Scenario-specific plugins, which introduce calculations particular to a given production pathway or study.

The default plugins are specified in the ``Defaults.md`` file. They are always included in a calculation and provide the general discounted cash flow framework. 
This includes the construction of capital costs, operating costs, replacement costs, and the financial evaluation that leads to metrics such as annual cash flows and the levelized cost of the delivered product. 
Note that the default Workflow (as defined in the ``Defaults.md`` file) also calls functions after each default plugin execution. These functions can be found as methods of the Discounted_Cash_Flow class.

Scenario-specific plugins are specified in the user-defined input (.md) file. They typically introduce technical calculations (e.g., production performance, equipment sizing, technology-dependent costs) whose results enter the financial structure defined by the defaults.

At runtime, pyH2A combines the predefined default plugins with the scenario-specific plugins into a single ordered sequence. 
The relative position of each plugin determines how technical quantities are incorporated into capital and operating costs, and how these costs ultimately influence the discounted cash flow results.

Detailed guidance on plugin ordering is provided separately.


4. Economic Logic Implemented by the Default Structure
------------------------------------------------------

- Prior to the economic progression itself, quantities related to the plant lifetime (e.g. array ranging from 0 to the number of prodution years) and to the inflation (e.g. inflation correction between the reference year and the startup year) are generated.

  .. admonition:: Code implementation

     this is handled by the ``Time_Plugin`` followed by the ``Inflation_Plugin``.

The default financial structure then follows a defined economic progression:

- Production definition: The production at gate is established as a function of the plant design production, providing the reference for subsequent cost calculations.

  .. admonition:: Code implementation

     this is handled by the ``Production_Plugin``.

- Capital costs: The total investment required to construct the system at the specified design production is calculated.

  .. admonition:: Code implementation

     this is handled by the ``Capital_Cost_Plugin``.

- Equipment replacement: The financial impact of component lifetimes shorter than the overall analysis period is incorporated.

  .. admonition:: Code implementation

     this is handled by the ``Replacement_Plugin``.

- Operating costs: Costs are separated into fixed and variable components. Fixed costs are independent of production level, while variable costs depend on the delivered production.

  .. admonition:: Code implementation

     this is handled by the ``Labor_Operating_Cost_Plugin``, ``Other_Fixed_Operating_Cost_Plugin`` and ``Variable_Operating_Cost_Plugin``.

After these quantities have been established (production, capital costs, replacement costs, and operating costs) the discounted cash flow calculation is performed. 
Financial parameters such as discount rate, depreciation treatment, and taxation are applied to compute annual cash flows over the project lifetime. From these, net present value-based indicators, including the levelized cost of product, are derived.

The economic results therefore arise from a clearly structured sequence: production definition, cost construction, and financial evaluation, implemented through the default plugin sequence.