# Life Cycle Assessment

Name | Value
--- | ---
Matrix Folder | src/tests/lca/data/matrix_folders/smartphone_3layer_ced_base

# LCA - Smartphone GT Components

Name | Value | Unit | UUID
--- | --- | --- | ---
Smartphone | 1.0 | kg | 927ba7de-2e36-4192-a585-91b7db8a07e4
Circuit Board | 1.0 | item | 86c3e6eb-2103-4a36-87e0-5abaa79ee289
Display | 1.0 | kg | 49092338-ccb5-4102-8d7b-d9a55ebecdaf
Battery | 1.0 | kg | 91c3199d-cf4c-452e-979a-c467fc9c8404

# Construction

Name | Full Name | Value
--- | --- | ---
capital perc 1st | % of capital spent in 1st year of construction | 100%

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment
--- | --- | --- | ---
Plant design capacity | 1.0 | kg/day | Reference production for GT LCA tests
Operating capacity factor | 90% | - | Capacity factor
Fraction of output that reaches gate | 100% | - | No gate losses assumed for minimal LCA test

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment
--- | --- | --- | ---
Cost of land | 0 | USD/m2 | No land cost for LCA test
Land required | 0 | m2 | No land for LCA test

# Fixed Operating Costs

Name | Value | Unit | Comment
--- | --- | --- | ---
Staff | 0 | - | No staff for minimal LCA test
Hourly labor cost | 0 | USD/h | No labor cost

# Planned Replacement

Name | Cost ($) | Path | Comment
--- | --- | --- | ---

# Utilities

Name | Usage per kg H2 | Usage Unit | Cost | Cost Unit | Price Conversion Factor | Comment
--- | --- | --- | --- | --- | --- | ---

# Monte_Carlo_Analysis

Name | Value | Comment
--- | --- | ---
Samples | 150 | Sized so full_distance_cost_relationship's default reduction_factor=25 gives window_length=7 > poly_order=4, so Monte_Carlo_Analysis(input_file) runs without error.
Dependent Variable | Cumulative energy demand | Already registered in _DEPENDENT_VARIABLE_CONFIG (unlike 'Global warming potential', which would require adding a new entry), and matches smartphone_3layer_ced_base's actual impact category key exactly.
Target Response Range | 0; 100 | Brackets the expected CED range for Display in [1,2] kg and Battery in [1,2] kg (CED = 9*CircuitBoard + 14*Display + 27*Battery gives 50.0-91.0 for this range).
Output File | src/tests/lca/data/input_files/Smartphone_3Layer_CED_MC_seed42_output.csv

# Parameters - Monte_Carlo_Analysis

Parameter | Name | Type | Values | Comment
--- | --- | --- | --- | ---
{LCA - Smartphone GT Components > Display > Value, kg} | Display (kg) | value | Base; 2.0 | Base resolves to 1.0 (set above), as required by check_parameter_integrity.
{LCA - Smartphone GT Components > Battery > Value, kg} | Battery (kg) | value | Base; 2.0 | Base resolves to 1.0 (set above), as required by check_parameter_integrity.
