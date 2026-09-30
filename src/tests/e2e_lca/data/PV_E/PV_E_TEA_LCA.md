# Input files to merge

Name | Value
--- | ---
Default TEA + LCA | pyH2A.Config~Defaults_TEA_LCA.md

# Workflow

Name | Position 
--- | --- 
Hourly_Irradiation_Plugin | 201 |
Photovoltaic_Plugin | 202 |
Electrolyzer_Plugin | 203 |
Battery_Plugin | 204 |
Stored_Power_Electrolysis_Plugin | 205 |
Reverse_Osmosis_Plugin | 301 |
Power_Management_Plugin | 302 |
Multiple_Modules_Plugin | 401 |

# Display Parameters

Name | Value 
--- | --- 
Name | PV + E 
Color | darkblue 

# Hourly Irradiation

Name | Value | Comment 
--- | --- | --- | --- 
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA 

# Irradiance Area Parameters

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Array azimuth | 180 | deg 
Nominal operating temperature | 45 | degC 
Mismatch derating | 98% | - | Based on Chang 2020
Dirt derating | 98% | - | Based on Chang 2020
Temperature coefficient | -0.4% | 1/delta_degC | Based on Chang 2020

# Irradiation Used

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Data | {Hourly Irradiation > Horizontal single axis tracking > Value, kWh/m2} | kWh/m2 | Single axis tracking based on Chang 2020

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Design output by year | {Electrolyzer > H2 production (yearly) > Value, kg} | kg[H2] | Hydrogen production by electrolyzer (direct and via stored power) is considered as design output by year
Operating capacity factor | 100% | - | Set to 100%, operating capacity factor is considered during modelling of electrolyzer operation
Fraction of output that reaches gate | 100% | -
Plant modules | 1 | - | Modelling of 10 modules for calculation of staff cost to facilitate comparison with PEC and photocatalytic model

# Construction

Name | Value | Unit 
--- | --- | --- 
Capital spent in 1st year of construction | 100% | - 

# Electrolyzer

Name | Value | Unit | Comment
--- | --- | --- | --- 
Nominal power | 550 | MW | Scaled based on Palmer EES 2021
Unit nominal power | 1 | MW | Nominal power of one unit
Minimum capacity | 5% | - | Based on Palmer EES 2021
Power requirement increase per year | 0.3% | - | Based on Chang 2020
Hydrogen yield per unit energy | 0.0185 | kg/kWh | Based on Chang 2020
Replacement time | 80,000 | h | Based on Chang 2020, operating time after which electrolyzer stacks have to be replaced

# Electrolysis Using Stored Power

Name | Value | Unit | Comment
--- | --- | --- | --- 
Fraction of stored power used for electrolysis | 95% | - | Additional electrolysis using stored power 

# Photovoltaic

Name | Value | Unit | Comment
--- | --- | --- | --- 
Nominal power | 1010 | MW | PV sizing based on Palmer EES 2021
Power loss per year | 0.5% | - | Based on Chang 2020
Efficiency | 20% | - | Only used for area calculation

# Battery

Name | Value | Unit | Comment
--- | --- | --- | ---
Design capacity | 1,500 | MWh | Full design capacity
Energy density | 0.144 | kWh/kg | Li-Ion energy density
Lifetime | 10 | year | Li-Ion Lifetime placeholder
Lowest discharge level | 20% | - | Lowest level to which battery can be discharged
Capacity loss per year | 1% | - | Loss of capacity per year
Round trip efficiency | 100% | - | For lithium ion battery

# Reverse Osmosis

Name | Value | Unit | Comment
--- | --- | --- | ---
Power demand | 2.71 | kWh/m3 | based on Hausmann 2021 and Kim 2008 (this was chosen for a purity of < 10 ppm of disolved salts in the obtained water), kWh per m3 of sea water
Average operating time fraction | 0.16666666666666666 | - | Assumption that reverse osmosis runs for 4 h/day, relevant for scaling of reverse osmosis plant
Recovery rate | 40% | - | Fraction of fresh water obtained from given volume of sea water, based Palmer 2021 and Terlouw 2022
Device output | 170,500 | m3/day | Large water works purification system, only a fraction of this is needed

# Power Consumption

Name | Value | Unit | Type
--- | --- | --- | ---
Test consumer | 0 | kWh | on_demand

# Direct Capital Costs - Reverse Osmosis

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Reverse osmosis CAPEX | 6000 | {Reverse Osmosis > Capacity > Value, m3/h} | USD | Based on https://samcotech.com/much-reverse-osmosis-nanofiltration-membrane-systems-cost/, Conversion factor of 4.5 from GPM to m3/h, cost of 6000 USD/(m3/h) of capacity

# Direct Capital Costs - Battery

Name | Value | Path | Unit
--- | --- | --- | ---
Battery CAPEX | 0. | {Battery > Design capacity > Value, kWh} | USD

# Direct Capital Costs - PV

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
PV CAPEX | 818 | {Photovoltaic > Nominal power > Value, kW} | USD | Based on Chang 2020, Chiesa 2021 Middle East PV installation cost, Shah 2021

# Direct Capital Costs - Electrolyzer

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Electrolyzer CAPEX | 784 | {Electrolyzer > Nominal power > Value, kW} | USD | Based on Chang 2020, IRENA 2020 Green Hydrogen (PEM System CAPEX 700 - 1400 USD/kg), Shah 2021

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 500.0 | USD/acre | Same as PEC and Photocatalytic model, based on Pinaud 2013

# Fixed Operating Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Solar collection area per staffer | 405,000 | m2 | Same as photocatalytic model, solar collection area that can be overseen by one staff member
Number of supervisors | 1 | - | Same as PEC and photocatalytic model, number of shift supervisors
Number of 8-hour shifts | 3 | - | Same as PEC and photocatalytic model, number of shifts per day
Hourly labor cost | 50.0 | USD/h | Same as PEC and photocatalytic model,  Burdened labor cost, including overhead (USD per man-hr)

# Other Fixed Operating Costs

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Electrolyzer OPEX (fraction of CAPEX) | 2% | {Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value, USD} | USD | Based on Stolten 2020, Shah 2021
PV OPEX (fraction of CAPEX) | 2% | {Direct Capital Costs - PV > PV CAPEX > Value, USD} | USD | Based on Stolten 2020

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Process Water | 10. | None | 1/kg[H2] | 0.0006 | None | USD | 1. | - | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to 0.0006 USD/L), based on Kibria 2021 and Driess 2021

# Grid Electricity

Name | Value | Unit
--- | --- | ---
Cost | 0.12 | USD/kWh

# Planned Replacement

Name | Cost_Value | Cost_Path | Cost_Unit | Frequency_Value | Frequency_Unit | Comment
--- | --- | --- | --- | ---
Electrolyzer stack replacement | 40% | {Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value, USD} | USD | {Electrolyzer > Actual stack replacement time > Value, year} | year | Based on Chang 2020

# Life Cycle Assessment

Name | Value
--- | ---
Matrix Folder | src/tests/e2e_lca/data/PV_E/260930_SD-007_Foreground_Stacks
UUID of product | d8785e18-bacc-4706-a500-06d92aa2cbc6

# LCA - Photovoltaic

Name | Value | Unit | UUID
--- | --- | --- | ---
PV Modules (by area) | {Photovoltaic > Module area > Value, m2} | m2 | 0c88e490-56a5-3099-807c-06645527c90e

# LCA - Electrolysis

Name | Value | Unit | UUID
--- | --- | --- | ---
Electrolysis BOP (installed once) | {Electrolyzer > Number of units > Value, -} | - | 570be296-be1b-4de6-916a-655587019c43
Electrolysis stacks (lifetime) | {Electrolyzer > Number of stacks > Value, -} | - | 786f737e-0c91-42e0-b909-880cb4d97006

# LCA - Battery

Name | Value | Unit | UUID
--- | --- | --- | ---
Battery lifetime mass | {Battery > Lifetime battery mass > Value, kg} | kg | c341bfcb-5959-3a70-839e-913e8250b237

# LCA - Reverse Osmosis

Name | Value | Unit | UUID
--- | --- | --- | ---
Number of reverse osmosis units | {Reverse Osmosis > Number of devices > Value, -} | - | 056a11ab-0a7a-38dd-a1d3-4058c2a8662d