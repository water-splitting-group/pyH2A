# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/Photocatalytic/Photocatalytic_Base_test.md

# Technical Operating Parameters and Specifications

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Plant design capacity | 2,111 | None | kg/day 

# Reactor Baggies

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Filling height | 0.10 | m | Optimal height depends on absorption coefficient of material/complex and catalytic activity (TOF or mol H2/h/g). Height of 5 cm based on experimental set-up used in Kang 2015 (shown in Kang 2015 SI)
Length | 623.0 | m | Baggie parameters based on Pinaud 2013
Width | 22.2 | m | Baggie parameters based on Pinaud 2013
Cost material top | 1.04 | USD/m2 
Cost material bottom | 0.97 | USD/m2 
Number of ports per baggie | 22 | - 
Cost of port | 60 | USD | Cost per port
Other costs per baggie | 1210.7 | USD 
Markup factor | 3.5 | - | Markup factor of baggies
Additional land area | 60% | - | Land area required in addition to area occupied by baggies
Lifetime | 15 | year | Lifetime of reactor baggies

# Catalyst

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost per unit of mass | 6,000 | USD/kg | CatCost Model of Urea/Melamine derived catalyst, 5% mass yield, 0.5% wt% Ruthenium as cost placeholder for CDots (Kang 2015 uses 0.48% wt% CDots on C3N4), 60 kWh electricity per kg(catalyst) due to electrochemical CDot synthesis, process template "Metal on Metal Oxide - Strong Electrostatic Adsorption" used in CatCost Model, 5 t/a production scale, estimated cost: 890 USD/kg, increased to 3,000 USD/kg
Concentration | 0.933 | g/L | Kang 2015: 2% STH, 80 mg C3N4/CDot catalyst in 150 ml, 1150 umol H2 after 6h, 9 cm^2 irradiation area (2266 J/h incident irradiation), ca. 2.395 mmol H2/h/g; Tremblay 2020: 3.4% STH (200 W m^-2), 30 mg C3N4 + catalase in 20 ml, 47.49 umol H2/h, ca. 1.583 mmol H<sub>2</sub>/h/g (ca. 5 cm<sup>2</sup> irradiation area gives reported STH); Zhao 2021: 1.16% STH (100 mW/cm^2), 0.64 cm^2 irradiated area, 11.25 umol H2 h^-1, 40 mg catalyst, 0.281 mmol H2/g/h, activity 420 nm irradiation: 65 umol H2/h, 40 mg, 1.625 mmol H2/g/h 
Lifetime | 1.5 | year | Kang 2015, 45 days continuous irradiation, 200 days with recycling 
Molar weight | 500 | g/mol | Assumption for calculation of hypothetical homogeneous water splitting catalyst. 
Molar attenuation coefficient | 8000 | liter/(cm*mol) | Assumption for calculation of hypothetical homogeneous water splitting catalyst. 

# Solar-to-Hydrogen Efficiency

Name | Value | Unit | Comment 
--- | --- | --- | --- 
STH | 4% | - | Kang 2015, C3N4/CDot catalyst, 4% STH 