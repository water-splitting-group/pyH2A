# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md
Base | src/tests/end_to_end/PV_E_Base_test.md

# Sensitivity_Analysis

Name | Value | Label
--- | --- | ---
Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg} | Levelized Cost

# Parameters - Sensitivity_Analysis

Parameter | Name | Type | Values
--- | --- | --- | ---
Direct Capital Costs - PV > PV CAPEX > Value | PV CAPEX ($/kW) | value | 400; 1600
Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value | Electrolyzer CAPEX ($/kW) | value | 400; 1600
Electrolyzer > Hydrogen yield per unit energy > Value | Electrolyzer efficiency (kg H2/kWh) | value | 0.015; 0.025
Photovoltaic > Power loss per year > Value | PV power loss per year | value | 0.25%; 1.0%
Electrolyzer > Power requirement increase per year > Value | Electrolyzer power increase per year | value | 0.15%; 0.6%
Planned Replacement > Electrolyzer stack replacement > Cost_Value | Stack repl. cost (% of E-CAPEX) | value | 20%; 80%
