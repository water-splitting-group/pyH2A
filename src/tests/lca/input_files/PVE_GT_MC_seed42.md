# Life Cycle Assessment

Name | Value
--- | ---
Matrix Folder | src/tests/lca/LCA_Test_PVE_GT

# LCA - PVE GT Components

Name | Value | Unit | UUID
--- | --- | --- | ---
H2 Production | 1.0 | kg | 66b8a6b0-7b7a-4d2c-95d3-d82951c58a35
PV Electricity Generation | 198.0 | MJ | bc18dc79-2b51-455d-9fec-decf6b2693de
Electrolyzer Manufacturing | 1e-6 | item | 4397d5db-7fea-4916-af17-b72fa72fc02a
Reverse Osmosis | 9.0 | kg | 1659c3a5-5c6b-4f29-b746-e12119144b7b

# Construction

Name | Full Name | Value
--- | --- | ---
capital perc 1st | % of capital spent in 1st year of construction | 100%

# Technical Operating Parameters and Specifications

Name | Value | Comment
--- | --- | ---
Plant Design Capacity (kg of H2/day) | 1.0 | Reference production for GT LCA tests
Operating Capacity Factor (%) | 90% | Capacity factor
Plant Modules | 1 | Single module

# Non-Depreciable Capital Costs

Name | Value | Comment
--- | --- | ---
Cost of land ($ per acre) | 0 | No land cost for LCA test
Land required (acres) | 0 | No land for LCA test

# Fixed Operating Costs

Name | Full Name | Value | Comment
--- | --- | --- | ---
staff | Number of staff | 0 | No staff for minimal LCA test
hourly labor cost | Burdened labor cost ($ per man-hr) | 0 | No labor cost

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
Dependent Variable | Climate change no LT - Global warming potential (GWP100) no LT | Registered as its own _DEPENDENT_VARIABLE_CONFIG entry; matches LCA_Test_PVE_GT's actual impact category key exactly.
Target Response Range | 0; 1 | Brackets the expected GWP100 range for PV in [198,300] MJ and RO in [9,15] kg (GT scenarios S1/S5 give 0.454-0.688 for a wider range).
Output File | src/tests/lca/input_files/PVE_GT_MC_seed42_output.csv

# Parameters - Monte_Carlo_Analysis

Parameter | Name | Type | Values | Comment
--- | --- | --- | --- | ---
LCA - PVE GT Components > PV Electricity Generation > Value | PV (MJ/kg H2) | value | Base; 300 | Base resolves to 198.0 (set above), as required by check_parameter_integrity.
LCA - PVE GT Components > Reverse Osmosis > Value | RO (kg/kg H2) | value | Base; 15 | Base resolves to 9.0 (set above), as required by check_parameter_integrity.
