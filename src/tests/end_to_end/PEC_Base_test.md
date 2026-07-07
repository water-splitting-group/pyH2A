# Workflow

Name | Type | Description | Position 
--- | --- | --- | --- 
Hourly_Irradiation_Plugin | plugin | Plugin to calculate solar irradiation from typical meteorological year data | 1 
PEC_Plugin | plugin | Plugin to model photoelectrochemical water splitting | 201 
Solar_Concentrator_Plugin | plugin | Plugin to model solar concentration | 202 
Multiple_Modules_Plugin | plugin | Modelling of module plant modules, adjustment of labor requirement | 301 

# Display Parameters

Name | Value 
--- | --- 
Name | PEC 
Color | darkred 

# Technical Operating Parameters and Specifications

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Operating capacity factor | 90% | None | - | ...
Plant design capacity | 1,000 | None | kg/day | ...
Fraction of output that reaches gate | 100% | None | - | ...
Plant modules | 10 | None | - | 10 identical modules, only affects labor requirement calculation. 

# Construction

Name | Value | Unit 
--- | --- | --- 
Capital spent in 1st year of construction | 100% | - 

# Hourly Irradiation

Name | Value | Comment 
--- | --- | --- 
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA 

# Irradiance Area Parameters

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Module tilt | 0 | deg | Two axis tracking, module tilt and array azimuth change are not relevant 
Array azimuth | 0 | deg | Two axis tracking, module tilt and array azimuth change are not relevant
Nominal operating temperature | 45 | degC | Temperature is stabilized even under solar concentration through intrinsic water cooling. 
Mismatch derating | 98% | - 
Dirt derating | 98% | - | Values taken from Chang 2020, analogues to silicon PV
Temperature coefficient | 0.0% | 1/delta_degC | No assumed efficiency loss with higher temperature

# Solar Input

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Mean solar input | {Hourly Irradiation > Mean solar input two axis tracking > Value, W/m2} | {Solar Concentrator > Concentration factor > Value, -} | W/m2 | Two axis tracking irradiation from hourly irradiation multiplied by solar concentration factor to give solar input incident on PEC cells. 

# Solar-to-Hydrogen Efficiency

Name | Value | Unit | Comment 
--- | --- | --- | --- 
STH | 14% | - | Reference Kistler 2020, 14% STH (Note: vapor-fed device used in reference, techno-economic analysis assumes liquid phase design, no solar concentration); alternative reference: Idriss 2020, 18% STH at 15 suns, 13% STH at 200 suns (triple junction III-V cell based system). 

# PEC Cells

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cell cost | 21,000 | USD/m2 | Price of III-V solar cells as reference, approximate USD/W to USD/m2 conversion formula: Cost (USD/W) _ conversion_efficiency (%) _ 1000 W/m2 = Cost (USD/m2), Reference: Horowitz 2018 (NREL), 70 USD/W, assuming 30% efficiency = 21,000 USD/m2. 
Lifetime | 0.33 | year | Should consider operational lifetime (irradiation for only 8 h per day), baseline 1000 h operation time (reference: Kistler 2020), 3000 h total, 0.3 years
Length | 6 | m | Based on sizing in Pinaud 2013
Width | 0.3 | m | Based on sizing in Pinaud 2013 

# Solar Concentrator

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Concentration factor | 50 | - | Concentration factor increased from 10 (Pinaud 2013) to 50 due to high PEC cell cost, within range of typical parabolic trough concentrators, see Gharbi 2011. 
Cost | 100 | USD/m2 | 100 USD/m2 parabolic trough concentrator cost based on Filas 2018

# Land Area Requirement

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cell angle | 35 | deg | Used for total land area calculation. 
South spacing | 6.71 | m 
East/West spacing | 17.3 | m 

# Direct Capital Costs - Water Management

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Water pump | 213.0 | None | USD | Based on Pinaud 2013. 
Water manifold piping | 11.58 | {PEC Cells > Number > Value, -} | USD 
Water collection piping | 1.502 | {PEC Cells > Number > Value, -} | USD 
Water column collection piping | 1.1015 | {PEC Cells > Number > Value, -} | USD 
Water final collection piping | 0.231 | {PEC Cells > Number > Value, -} | USD 

# Direct Capital Costs - Gas Processing

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Condenser | 7,098.0 | None | USD | Based on Pinaud 2013. 
Manifold piping | 11.58 | {PEC Cells > Number > Value, -} | USD 
Collection piping | 1.502 | {PEC Cells > Number > Value, -} | USD 
Column collection piping | 1.1015 | {PEC Cells > Number > Value, -} | USD 
Final collection piping | 0.231 | {PEC Cells > Number > Value, -} | USD 

# Direct Capital Costs - Control System

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
PLC | 3,000.0 | None | USD | Based on Pinaud 2013. 
Control room building | 17,527.0 | None | USD 
Control room wiring panel | 3,000.0 | None | USD 
Computer and monitor | 1,500.0 | None | USD 
Labview software | 4,299.0 | None | USD 
Hydrogen flow meter | 5,500.0 | None | USD 
Water level controllers | 50.0 | {PEC Cells > Number > Value, -} | USD 
Pressure sensors | 3.333 | {PEC Cells > Number > Value, -} | USD 
Hydrogen area sensors | 73.42 | {PEC Cells > Number > Value, -} | USD 
Instrument wiring | 0.252 | {PEC Cells > Number > Value, -} | USD 
Power wiring | 0.1256 | {PEC Cells > Number > Value, -} | USD 
Conduit | 3.759 | {PEC Cells > Number > Value, -} | USD 

# Direct Capital Costs - Installation Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Piping installation | 5.65 | {PEC Cells > Number > Value, -} | USD | Based on Pinaud 2013
Reactor installation | 22.0 | {Non-Depreciable Capital Costs > Solar collection area > Value, m2} | USD 
Pump installation | 30% | {Direct Capital Costs - Water Management > Water pump > Value, USD} | USD 
Gas processing installation | 30% | {Direct Capital Costs - Gas Processing > Summed total > Value, USD} | USD 
Control system installation | 30% | {Direct Capital Costs - Control System > Summed total > Value, USD} | USD 

# Indirect Capital Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Engineering and design | 7% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Based on Pinaud 2013. 
Process contingency | 20% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Up-front permitting costs | 0.5% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Site preparation | 1% | {Direct Capital Cost > Summed group total > Value, USD} | USD 

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 500.0 | USD/acre | Land cost based on Pinaud 2013

# Fixed Operating Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Solar collection area per staffer | 60,000 | m2 | Based on Pinaud et al. 2013, smaller area per staff compared to PV+E and photocatalytic model due to smaller size of individual units, more connections and sensors.
Number of supervisors | 1 | - | Number of shift supervisors
Number of 8-hour shifts | 3 | - | Number of shifts per day 
Hourly labor cost | 50.0 | USD/h | Burdened labor cost, including overhead

# Other Fixed Operating Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
G&A | 20% | {Fixed Operating Costs > Labor cost > Value, USD} | USD | Based on Pinaud 2013. 
Property tax | 2% | {Total Capital Costs > Inflated > Value, USD} | USD | Property tax and insurance rate
Repairs | 0.5% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Production maintenance and repairs
Fees | 1000.0 | None | USD | Licensing, permits and fees

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment 
--- | --- | --- | --- | --- | --- | --- | --- | --- 
Industrial electricity | 0.16 | None | 1/kg | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | None | USD | 0.0036 | - | Electricity usage based on Pinaud 2013
Process water | 2.369 | None | 1/kg | 0.0023749510945008 | None | USD | 1. | - | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to ca. 0.0023 USD/gal), based on Kibria 2021 and Driess 2021.

# Unplanned Replacement

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Unplanned replacement | 0.5% | {Depreciable Capital Costs > Inflated > Value, USD} | USD | Based on Pinaud 2013, Total unplanned replacement capital cost factor (fraction of total direct depreciable costs per year)
