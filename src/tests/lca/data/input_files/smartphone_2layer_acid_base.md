# Input files to merge

Name | Value
--- | ---
Defaults | pyH2A.Config~Defaults_TEA_LCA.md

# Life Cycle Assessment

Name | Value
--- | ---
Matrix Folder | src/tests/lca/data/matrix_folders/smartphone_2layer_acid_base

# LCA - Smartphone GT Components

Name | Value | Unit | UUID
--- | --- | --- | ---
Smartphone | 1.0 | kg | 0c81c05f-a6ed-4f17-a399-43eb698a3b59
Display | {GT Display Output > Display > Value, kg} | kg | a3c98060-7b10-4ba2-abb2-0ea0ddfbd3c2
Circuit Board | {GT Circuit Board Output > Circuit Board > Value, item} | item | 47760afd-6a67-454a-98a8-03063250f4aa
Battery | {GT Battery Output > Battery > Value, kg} | kg | 042f97ea-dbbe-4ef4-ab8f-3a2d23084b73

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
