# Construction

Parameter | Value | Unit
--- | --- | ---
<...> | int or float | n/a
Capital spent in 1st year of construction | 1.0 | -

# Irradiance Area Parameters

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Module tilt | int or float, optional | n/a | n/a
Array azimuth | 180 | deg | n/a
Nominal operating temperature | 45 | degC | n/a
Mismatch derating | 0.98 | - | Based on Chang 2020
Dirt derating | 0.98 | - | Based on Chang 2020
Temperature coefficient | -0.004 | 1/delta_degC | Based on Chang 2020

# Technical Operating Parameters and Specifications

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Plant design capacity | int or float, optional | n/a | n/a
Design output by year | {Electrolyzer > H2 production (yearly) > Value, kg} | kg[H2] | Hydrogen production by electrolyzer (direct and via stored power) is considered as design output by year
Operating capacity factor | 1.0 | - | Set to 100%, operating capacity factor is considered during modelling of electrolyzer operation
Fraction of output that reaches gate | 1.0 | - | n/a
Plant modules | 10 | - | Modelling of 10 modules for calculation of staff cost to facilitate comparison with PEC and photocatalytic model

# Power Consumption

Parameter | Value | Type | Unit
--- | --- | --- | ---
<...> | int or float or ndarray, optional | str, optional | n/a
Test consumer | 0 | on_demand | kWh

# <...> Direct Capital Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# <...> Indirect Capital Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# <...> Other Non-Depreciable Capital Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# Planned Replacement

Parameter | Frequency_Value | Cost_Value | Cost_Path | Cost_Unit | Frequency_Unit | Comment
--- | --- | --- | --- | --- | --- | ---
<...> | int or float, optional | int or float, optional | n/a | n/a | n/a | n/a
Electrolyzer stack replacement | {Electrolyzer > Actual stack replacement time > Value, year} | 0.4 | {Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value, USD} | USD | year | Based on Chang 2020

# <...> Unplanned Replacement <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# <...> Other Fixed Operating Cost <...>

Parameter | Value
--- | ---
<...> | int or float, optional

# Utilities

Parameter | Cost_Value | Usage_Value | Price_Conversion_Factor_Value | Usage_Path | Usage_Unit | Cost_Path | Cost_Unit | Price_Conversion_Factor_Unit | Comment
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---
<...> | int or float or str or ndarray, optional | int or float, optional | int or float, optional | n/a | n/a | n/a | n/a | n/a | n/a
Process Water | 0.0006 | 10.0 | 1.0 | None | 1/kg[H2] | None | USD | - | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to 0.0006 USD/L), based on Kibria 2021 and Driess 2021

# <...> Other Variable Operating Cost <...>

Parameter | Value
--- | ---
<...> | int or float or ndarray, optional

# Input files to merge

Parameter | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md

# Workflow

Parameter | Position
--- | ---
Hourly_Irradiation_Plugin | 201
Photovoltaic_Plugin | 202
Electrolyzer_Plugin | 203
Battery_Plugin | 204
Stored_Power_Electrolysis_Plugin | 205
Reverse_Osmosis_Plugin | 301
Power_Management_Plugin | 302
Multiple_Modules_Plugin | 401

# Display Parameters

Parameter | Value
--- | ---
Name | PV + E
Color | darkblue

# Hourly Irradiation

Parameter | Value | Comment
--- | --- | ---
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA

# Irradiation Used

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Data | {Hourly Irradiation > Horizontal single axis tracking > Value, kWh/m2} | kWh/m2 | Single axis tracking based on Chang 2020

# Electrolyzer

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Nominal power | 5500 | kW | Production of ca. 1 t of H2 per day to compare with PEC and photocatalytic models
Power requirement increase per year | 0.003 | - | Based on Chang 2020
Minimum capacity | 0.1 | - | Based on Chang 2020, minimum capacity for electrolyzer to operate
Hydrogen yield per unit energy | 0.0185 | kg/kWh | Based on Chang 2020
Replacement time | 80000 | h | Based on Chang 2020, operating time after which electrolyzer stacks have to be replaced

# Electrolysis Using Stored Power

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Fraction of stored power used for electrolysis | 0.95 | - | Additional electrolysis using stored power

# Photovoltaic

Parameter | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Nominal power | 1.5 | {Electrolyzer > Nominal power > Value, kW} | kW | Optimal PV oversize ratio, same as Chang 2020
Power loss per year | 0.005 | None | - | Based on Chang 2020
Efficiency | 0.22 | None | - | Only used for area calculation

# Battery

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Design capacity | 800 | MWh | Full design capacity
Lowest discharge level | 0.2 | - | Lowest level to which battery can be discharged
Capacity loss per year | 0.01 | - | Loss of capacity per year
Round trip efficiency | 1.0 | - | For lithium ion battery

# Reverse Osmosis

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Power demand | 2.71 | kWh/m3 | based on Hausmann 2021 and Kim 2008 (this was chosen for a purity of < 10 ppm of disolved salts in the obtained water), kWh per m3 of sea water
Average operating time fraction | 0.16666666666666666 | - | Assumption that reverse osmosis runs for 4 h/day, relevant for scaling of reverse osmosis plant
Recovery rate | 0.4 | - | Fraction of fresh water obtained from given volume of sea water, based Palmer 2021 and Terlouw 2022

# Direct Capital Costs - Reverse Osmosis

Parameter | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Reverse osmosis CAPEX | 6000 | {Reverse Osmosis > Capacity > Value, m3/h} | USD | Based on https://samcotech.com/much-reverse-osmosis-nanofiltration-membrane-systems-cost/, Conversion factor of 4.5 from GPM to m3/h, cost of 6000 USD/(m3/h) of capacity

# Direct Capital Costs - Battery

Parameter | Value | Path | Unit
--- | --- | --- | ---
Battery CAPEX | 0.0 | {Battery > Design capacity > Value, kWh} | USD

# Direct Capital Costs - PV

Parameter | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
PV CAPEX | 818 | {Photovoltaic > Nominal power > Value, kW} | USD | Based on Chang 2020, Chiesa 2021 Middle East PV installation cost, Shah 2021

# Direct Capital Costs - Electrolyzer

Parameter | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Electrolyzer CAPEX | 784 | {Electrolyzer > Nominal power > Value, kW} | USD | Based on Chang 2020, IRENA 2020 Green Hydrogen (PEM System CAPEX 700 - 1400 USD/kg), Shah 2021

# Non-Depreciable Capital Costs

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Cost of land | 500.0 | USD/acre | Same as PEC and Photocatalytic model, based on Pinaud 2013

# Fixed Operating Costs

Parameter | Value | Unit | Comment
--- | --- | --- | ---
Solar collection area per staffer | 405000 | m2 | Same as photocatalytic model, solar collection area that can be overseen by one staff member
Number of supervisors | 1 | - | Same as PEC and photocatalytic model, number of shift supervisors
Number of 8-hour shifts | 3 | - | Same as PEC and photocatalytic model, number of shifts per day
Hourly labor cost | 50.0 | USD/h | Same as PEC and photocatalytic model,  Burdened labor cost, including overhead (USD per man-hr)

# Other Fixed Operating Costs

Parameter | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Electrolyzer OPEX (fraction of CAPEX) | 0.02 | {Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value, USD} | USD | Based on Stolten 2020, Shah 2021
PV OPEX (fraction of CAPEX) | 0.02 | {Direct Capital Costs - PV > PV CAPEX > Value, USD} | USD | Based on Stolten 2020

# Grid Electricity

Parameter | Value | Unit
--- | --- | ---
Cost | 10000.12 | USD/kWh

