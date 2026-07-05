# Input files to merge

Name | Value
--- | ---
File A | data/PV_E/Base/PV_E_Base.md

# Life Cycle Assessment 

Name | Value
--- | ---
Matrix Folder | data/LCA/LCA_Test_PVE_EF

# LCA - PVE Components

Name | Value | Unit | UUID
--- | --- | --- | ---
Total H2 Production |Technical Operating Parameters and Specifications > Output per Year at Gate > Value | kg | 50e1c844-e481-4c14-a3ca-1948f1d2fe37
PV Area | Non-Depreciable Capital Costs > Solar Collection Area (m2) > Value | m2 | 0c88e490-56a5-3099-807c-06645527c90e
Electrolyzer unit number | Electrolyzer > Number of electrolyzers required > Value | - | 98f950b2-39b0-4374-a400-05984b438be9
Battery weight | Battery > Mass (kg) > Value | kg | c341bfcb-5959-3a70-839e-913e8250b237
Reverse Osmosis Units | Reverse Osmosis > Number of devices required > Value | - | 056a11ab-0a7a-38dd-a1d3-4058c2a8662d

# Electrolyzer

Name | Value | Unit | Comment
--- | --- | --- | ---
Unit nominal power | 3,900.0 | kW | Size of one electrolyzer unit used to calculate required unit count based on Palmer et al. 2021 paper.

# Electrolysis Using Stored Power

Name | Value | Comment
--- | --- | ---
Fraction of stored power used for electrolysis | 0% | Additional electrolysis using stored power

# Photovoltaic

Name | Value | Path | Comment
--- | --- | --- | --- 
Efficiency | 20% | None | Only used for area calculation.

# Battery

Name | Value | Unit | Comment
--- | --- | --- | ---
Energy density | 0.2 | kWh/kg | Battery specific energy for analyses and Monte Carlo sampling

# Reverse Osmosis

Name | Value | Unit | Comment
--- | --- | --- | ---
Device throughput | 6.23e10 | L/year | Throughput of one reverse osmosis device used to calculate number of required devices

# Direct Capital Costs - Reverse Osmosis

Name | Value | Path | Comment 
--- | --- | --- | ---
Reverse Osmosis CAPEX ($ per m3/h capacity) | 0 | Reverse Osmosis > Capacity (m3/h) > Value | Based on https://samcotech.com/much-reverse-osmosis-nanofiltration-membrane-systems-cost/, Conversion factor of 4.5 from GPM to m3/h (6000 $/m3/h)

# Monte_Carlo_Analysis

Name | Value | Comment
--- | --- | ---
Samples | 50000 | Number of samples in Monte Carlo simulation.
Dependent Variable | Climate change | Supported: h2_cost, Climate change, or Cumulative energy demand.
Target Response Range | 0; 100 | Used for Dependent Variable response filtering.
Output File | data/LCA/Monte_Carlo_Output.csv

# Parameters - Monte_Carlo_Analysis

Parameter | Name | Type | Values | File Index | Comment
--- | --- | --- | --- | --- | --- 
Photovoltaic > Efficiency > Value | PV efficiency (%) | value | Base; 0.4 | 0 | PV module efficiency uncertainty range.
Battery > Energy density > Value |Battery density kWh / kg | value | 0.1; 0.2 | 1 | Battery specific energy uncertainty range.
Reverse Osmosis > Recovery Rate > Value | Reverse osmosis recovery rate | value | 0.4; 0.9 | 2 | Reverse osmosis recovery range.
Electrolyzer > Conversion efficiency (kg H2/kWh) > Value | Electrolyzer efficiency kg($H_{2}$) / kWh | value | Base; 0.025 | 3 | Same Monte Carlo range convention as other PV_E files.

# Methods - Monte_Carlo_Analysis

Name | Method Name | Arguments
--- | --- | ---
distance_histogram | plot_distance_histogram | {'show': True, 'xlabel': True, 'save': True, 'pdf': True, 'image_kwargs': {'path': 'pyH2A.Other~PV_E_Clipart.png'}}
target_parameters | plot_target_parameters_by_distance | {'show': True}
