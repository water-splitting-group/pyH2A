# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md
Base | src/tests/end_to_end/PV_E_Base_test.md

# Sensitivity_Analysis

Name | Value
--- | ---
Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg}

# Parameters - Sensitivity_Analysis - PV_E

Parameter | Name | Type | Values
--- | --- | --- | ---
Direct Capital Costs - PV > PV CAPEX > Value | PV CAPEX ($/kW) | value | 400; 1600
Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value | Electrolyzer CAPEX ($/kW) | value | 400; 1600
Electrolyzer > Hydrogen yield per unit energy > Value | Electrolyzer efficiency (kg H2/kWh) | value | 0.015; 0.025
Photovoltaic > Power loss per year > Value | PV power loss per year | value | 0.25%; 1.0%
Electrolyzer > Power requirement increase per year > Value | Electrolyzer power increase per year | value | 0.15%; 0.6%
Planned Replacement > Electrolyzer stack replacement > Cost_Value | Stack repl. cost (% of E-CAPEX) | value | 20%; 80%

# Route Config - PV_E

Name | Value
--- | ---
Expected base file | src/tests/end_to_end/PV_E_Base_test.md

# Parameters - Sensitivity_Analysis - PC - Deactivate

Parameter | Name | Type | Values
--- | --- | --- | ---
Catalyst > Cost per unit of mass > Value | Catalyst cost (USD/kg) | value | 1000; 5000
Solar-to-Hydrogen Efficiency > STH > Value | PC solar-to-hydrogen efficiency | value | 0.01; 0.05
Catalyst > Lifetime > Value | Catalyst lifetime (year) | value | 0.25; 1.0
Reactor Baggies > Lifetime > Value | Reactor baggie lifetime (year) | value | 2; 10
Reactor Baggies > Markup factor > Value | Baggie markup factor | value | 1.2; 2.0
Catalyst Separation > Filtration cost > Value | Filtration cost (USD/m3) | value | 0.12; 0.48

# Route Config - PC

Name | Value
--- | ---
Expected base file | src/tests/end_to_end/Photocatalytic_Base_test.md

# Parameters - Sensitivity_Analysis - PEC - Deactivate

Parameter | Name | Type | Values
--- | --- | --- | ---
PEC Cells > Cell cost > Value | PEC cell cost (USD/m2) | value | 10000; 30000
Solar-to-Hydrogen Efficiency > STH > Value | PEC solar-to-hydrogen efficiency | value | 0.10; 0.18
PEC Cells > Lifetime > Value | PEC cell lifetime (year) | value | 0.2; 1.0
Solar Concentrator > Concentration factor > Value | Concentration factor | value | 10; 100
Solar Concentrator > Cost > Value | Concentrator cost (USD/m2) | value | 50; 200
Utilities > Industrial electricity > Usage_Value | Industrial electricity usage | value | 0.08; 0.32

# Route Config - PEC

Name | Value
--- | ---
Expected base file | src/tests/end_to_end/PEC_Base_test.md
