# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md

# Workflow

Name | Description | Position
--- | --- | ---
Hourly_Irradiation_Plugin | Plugin to calculate solar irradiation from typical meteorological year data | 201 |
Photocatalytic_Plugin | Computes number of required baggies, cost of baggies and catalyst cost | 301 |
Catalyst_Separation_Plugin | Computes cost of catalyst separation | 302 |
Cooler_Condenser_Plugin | Computes first cooler condenser sizing and coolant requirements | 303 |
Compressor_Plugin  | Computes compressor power and yearly consumption | 304 |
Cooler_Condenser_Plugin @2 | Computes second cooler condenser sizing and coolant requirements | 305 |
Compressor_Plugin @2 | Computes second compressor power and yearly consumption | 306 |
Cooler_Condenser_Plugin @3 | Computes third cooler condenser sizing and coolant requirements | 307 |
PSA_refactored_Plugin | Computes sizing and cost of PSA separation unit | 308
Multiple_Modules_Plugin | Modelling of multiple plant modules, adjustment of labor requirement | 401 |

# Display Parameters

Name | Value 
--- | --- 
Name | PC 
Color | darkgreen 

# Technical Operating Parameters and Specifications

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Operating capacity factor | 90% | None | - 
Plant design capacity | 1,111 | None | kg/day 
Fraction of output that reaches gate | 90% | None | - | Reduction due to loss in H2/O2 separation. 
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
Module tilt | 0 | deg | Flat baggies on the ground. 
Array azimuth | 0 | deg | Flat baggies on the ground. 
Nominal operating temperature | 45 | degC 
Mismatch derating | 98% | - | Values taken from Chang 2020, analogues to silicon PV
Dirt derating | 98% | - | Values taken from Chang 2020, analogues to silicon PV
Temperature coefficient | 0 | 1/delta_degC | No decrease on photocatalyst activity with higher temperature assumed

# Solar Input

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Hourly | {Hourly Irradiation > No tracking > Value, kWh/m2} | kWh/m2 

# Solar-to-Hydrogen Efficiency

Name | Value | Unit | Comment 
--- | --- | --- | --- 
STH | 2% | - | Kang 2015, C3N4/CDot catalyst, 2% STH 

# Catalyst

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost per unit of mass | 3,000 | USD/kg | CatCost Model of Urea/Melamine derived catalyst, 5% mass yield, 0.5% wt% Ruthenium as cost placeholder for CDots (Kang 2015 uses 0.48% wt% CDots on C3N4), 60 kWh electricity per kg(catalyst) due to electrochemical CDot synthesis, process template "Metal on Metal Oxide - Strong Electrostatic Adsorption" used in CatCost Model, 5 t/a production scale, estimated cost: 890 USD/kg, increased to 3,000 USD/kg
Concentration | 0.533 | g/L | Kang 2015: 2% STH, 80 mg C3N4/CDot catalyst in 150 ml, 1150 umol H2 after 6h, 9 cm^2 irradiation area (2266 J/h incident irradiation), ca. 2.395 mmol H2/h/g; Tremblay 2020: 3.4% STH (200 W m^-2), 30 mg C3N4 + catalase in 20 ml, 47.49 umol H2/h, ca. 1.583 mmol H<sub>2</sub>/h/g (ca. 5 cm<sup>2</sup> irradiation area gives reported STH); Zhao 2021: 1.16% STH (100 mW/cm^2), 0.64 cm^2 irradiated area, 11.25 umol H2 h^-1, 40 mg catalyst, 0.281 mmol H2/g/h, activity 420 nm irradiation: 65 umol H2/h, 40 mg, 1.625 mmol H2/g/h 
Lifetime | 0.5 | year | Kang 2015, 45 days continuous irradiation, 200 days with recycling 
Molar weight | 500 | g/mol | Assumption for calculation of hypothetical homogeneous water splitting catalyst. 
Molar attenuation coefficient | 8000 | liter/(cm*mol) | Assumption for calculation of hypothetical homogeneous water splitting catalyst. 

# Reactor Baggies

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Filling height | 0.05 | m | Optimal height depends on absorption coefficient of material/complex and catalytic activity (TOF or mol H2/h/g). Height of 5 cm based on experimental set-up used in Kang 2015 (shown in Kang 2015 SI)
Length | 323.0 | m | Baggie parameters based on Pinaud 2013
Width | 12.2 | m | Baggie parameters based on Pinaud 2013
Cost material top | 0.54 | USD/m2 
Cost material bottom | 0.47 | USD/m2 
Number of ports per baggie | 12 | - 
Cost of port | 30 | USD | Cost per port
Other costs per baggie | 610.7 | USD 
Markup factor | 1.5 | - | Markup factor of baggies
Additional land area | 30% | - | Land area required in addition to area occupied by baggies
Lifetime | 5 | year | Lifetime of reactor baggies

# Catalyst Separation

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Filtration cost | 0.24 | USD/m3 | Cost of nanofiltration per m3 of water based on Costa 2006. Nanofiltration as a proxy for cost of actual catalyst separation

# Direct Capital Costs - Equipment

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Baggie roll system | 37,000.0 | None | USD | Equipment costs based on Pinaud 2013
Forklift | 18,571.0 | None | USD 
Water pump | 213.0 | None | USD 
Water pipes | 39.9 | {Reactor Baggies > Number > Value, -} | USD

# Direct Capital Costs - Gas Processing

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Compressor | 526,302.0 | None | USD | Cost estimate based on Pinaud 2013. Fixed cost of compressor for plant design output (1 ton H2/day)
Condenser | 13,765.0 | None | USD
Intercooler-1 | 15,103.0 | None | USD
Intercooler-2 | 15,552.0 | None | USD
Pressure swing adsorption | 107,147.0 | None | USD
Reactor outlet pipe | 3.17 | {Reactor Baggies > Number > Value, -} | USD
Main collection pipe | 329.6 | {Reactor Baggies > Number > Value, -} | USD
Final collection pipe | 23.7 | {Reactor Baggies > Number > Value, -} | USD

# Direct Capital Costs - Control System

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
PLC | 2,000.0 | None | USD | Control system cost based on Pinaud 2013 
Control room building | 8,000.0 | None | USD 
Control room wiring panel | 3,000.0 | None | USD
Bed wiring panel | 146.0 | {Reactor Baggies > Number > Value, -} | USD
Computer and monitor | 1,500.0 | None | USD
Labview software | 4,299.0 | None | USD 
Water level controllers | 50.0 | {Reactor Baggies > Number > Value, -} | USD 
Pressure sensors | 345.0 | {Reactor Baggies > Number > Value, -} | USD 
Hydrogen area sensors | 7,600.0 | {Reactor Baggies > Number > Value, -} | USD 
Gas flow meter | 5,500.0 | None | USD 
Instrument wiring | 22.7 | {Reactor Baggies > Number > Value, -} | USD 
Power wiring | 7.6 | {Reactor Baggies > Number > Value, -} | USD 
Conduit | 142.4 | {Reactor Baggies > Number > Value, -} | USD 

# Direct Capital Costs - Installation Costs

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Excavation | 2570.0 | {Reactor Baggies > Number > Value, -} | USD | Installation costs based on Pinaud 2013
Baggie reactor startup | 5% | {Direct Capital Costs - Reactor Baggies > Baggie cost > Value, USD} | USD 
Baggies installation | 800.0 | {Reactor Baggies > Number > Value, -} | USD 
Gas processing installation | 30% | {Direct Capital Costs - Gas Processing > Summed total > Value, USD} | USD 
Control system installation | 30% | {Direct Capital Costs - Control System > Summed total > Value, USD} | USD 

# Indirect Capital Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Engineering and design (fraction of total direct capital costs) | 7% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Indirect capital costs based on Pinaud 2013
Process contingency (fraction of total direct capital costs) | 20% | {Direct Capital Cost > Summed group total > Value, USD} | USD 
Up-front permitting costs (fraction of total direct capital costs) | 0.5% | {Direct Capital Cost > Summed group total > Value, USD} | USD
Site preparation (fraction of total direct capital costs) | 1% | {Direct Capital Cost > Summed group total > Value, USD} | USD

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment
--- | --- | --- | ---
Cost of land | 500.0 | USD/acre | Land cost based on Pinaud 2013

# Fixed Operating Costs

Name | Value | Unit | Comment
--- | --- | --- | ---
Solar collection area per staffer | 405,000 | m2 | Labor cost based on Pinaud 2013, solar collection area that can be overseen by one staff member
Number of supervisors | 1 | - | Number of shift supervisors
Number of 8-hour shifts | 3 | - | Number of shifts per day
Hourly labor cost | 50.0 | USD/h | Burdened labor cost, including overhead

# Other Fixed Operating Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
g&a | 20% | {Fixed Operating Costs > Labor cost > Value, USD} | USD | Other fixed operating costs based on Pinaud 2013. 
property tax | 2% | {Total Capital Costs > Inflated > Value, USD} | USD | Property tax and insurance rate
repairs | 0.5% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Production Maintenance and Repairs 
fees | 1000.0 | None | USD | Licensing, Permits and Fees

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment 
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- 
Industrial electricity | 3.29 | None | 1/kg | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | None | USD | 0.0036 | - | Electricity usage based on Pinaud 2013
Process water | 2.637 | None | 1/kg | 0.0023749510945008 | None | USD | 1.0 | - | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to ca. 0.0023 USD/gal), based on Kibria 2021 and Driess 2021

# Unplanned Replacement

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Unplanned replacement | 0.5% | {Depreciable Capital Costs > Inflated > Value, USD} | USD | Based on Pinaud 2013, Total Unplanned Replacement Capital Cost Factor (fraction of total direct depreciable costs/year)

# Compressor

Name | Value | Unit | Comment
--- | --- | --- | 
Compression ratio | 4.35 | -
Polytropic coefficient | 1.4 | -
Efficiency | 0.7 | - | 75% efficiency of the compressor itself, but we account for a bit of loss in the rest of the chain (e.g. electric motor)

# Compressor 2

Name | Value | Unit | Comment
--- | --- | --- | 
Compression ratio | 4.78 | -
Efficiency | 0.7 | - | 75% efficiency of the compressor itself, but we account for a bit of loss in the rest of the chain (e.g. electric motor)

# Cooler Condenser

Name | Value | Unit | 
--- | --- | --- 
Cold inlet temperature | 20. | degC |
Cold outlet temperature | 30. | degC |
Hot outlet temperature | 40. | degC |
Heat transfer coefficient | 300. | W/m2/delta_K 
Material weight per area | 34. | kg/m2 | assuming the condensing fluid circulates in tubes whose thickness is 10% of the inner diameter

# Cooler Condenser 2

Name | Value | Unit | 
--- | --- | --- 
Cold inlet temperature | 20. | degC |
Cold outlet temperature | 30. | degC |
Hot outlet temperature | 40. | degC |
Heat transfer coefficient | 300. | W/m2/delta_K 
Material weight per area | 34. | kg/m2 | assuming the condensing fluid circulates in tubes whose thickness is 10% of the inner diameter

# Cooler Condenser 3

Name | Value | Unit | 
--- | --- | --- 
Cold inlet temperature | 20. | degC |
Cold outlet temperature | 30. | degC |
Hot outlet temperature | 40. | degC |
Heat transfer coefficient | 300. | W/m2/delta_K 
Material weight per area | 34. | kg/m2 | assuming the condensing fluid circulates in tubes whose thickness is 10% of the inner diameter

# PSA

Name | Value | Unit 
--- | --- | --- 
Adsorbate | O2 | -
Adsorption time | 33 | s
Number of beds | 12 | -

# PSA Adsorbent Parameters

Name | Value | Unit 
--- | --- | --- 
Bed void fraction | 36% | -
Bed usage fraction | 0.769 | -
Adsorption uptake fraction | 3.9% | -
Residual loading fraction | 0.188% | -
Bulk density | 700 | kg/m3

# Reference PSA System

Name | Value | Unit 
--- | --- | --- 
Reference bed volume | 6065 |  L
Reference cost | 100,000 | USD
Scaling exponent | 0.5 | -