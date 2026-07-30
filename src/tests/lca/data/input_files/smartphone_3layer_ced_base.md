# Input files to merge

Name | Value
--- | ---
Defaults | pyH2A.Config~Defaults_TEA_LCA.md

# Life Cycle Assessment

Name | Value
--- | ---
Matrix Folder | src/tests/lca/data/matrix_folders/smartphone_3layer_ced_base

# LCA - Smartphone GT Components

Name | Value | Unit | UUID
--- | --- | --- | ---
Smartphone | 1.0 | kg | 927ba7de-2e36-4192-a585-91b7db8a07e4
Circuit Board | {GT Circuit Board Output > Circuit Board > Value, item} | item | 86c3e6eb-2103-4a36-87e0-5abaa79ee289
Display | {GT Display Output > Display > Value, kg} | kg | 49092338-ccb5-4102-8d7b-d9a55ebecdaf
Battery | {GT Battery Output > Battery > Value, kg} | kg | 91c3199d-cf4c-452e-979a-c467fc9c8404

# Workflow

Name | Type | Position
--- | --- | ---
Test_Plugin_C | plugin | 50
Test_Plugin_D | plugin | 50
Test_Plugin_E | plugin | 50

# GT Circuit Board Input

Name | Value | Unit
--- | --- | ---
Base Quantity | 1.0 | item
Scenario Factor | 1.0 | -

# GT Display Input

Name | Value | Unit
--- | --- | ---
Base Quantity | 1.0 | kg
Scenario Factor | 1.0 | -

# GT Battery Input

Name | Value | Unit
--- | --- | ---
Base Quantity | 1.0 | kg
Scenario Factor | 1.0 | -

# Construction

Name | Full Name | Value | Unit
--- | --- | --- | ---
capital perc 1st | % of capital spent in 1st year of construction | 100% | -

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
