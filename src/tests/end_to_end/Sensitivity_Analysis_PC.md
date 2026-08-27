# Input files to merge

Name | Value
--- | ---
Default TEA | pyH2A.Config~Defaults_TEA.md
Base | src/tests/end_to_end/Photocatalytic_Base_test.md

# Sensitivity_Analysis

Name | Value | Label
--- | --- | ---
Dependent variable | {Dependent Variables > Levelized cost > Value, USD/kg} | Levelized Cost

# Parameters - Sensitivity_Analysis

Parameter | Name | Type | Values
--- | --- | --- | ---
Catalyst > Cost per unit of mass > Value | Catalyst cost (USD/kg) | value | 1000; 5000
Solar-to-Hydrogen Efficiency > STH > Value | PC solar-to-hydrogen efficiency | value | 0.01; 0.05
Catalyst > Lifetime > Value | Catalyst lifetime (year) | value | 0.25; 1.0
Reactor Baggies > Lifetime > Value | Reactor baggie lifetime (year) | value | 2; 10
Reactor Baggies > Markup factor > Value | Baggie markup factor | value | 1.2; 2.0
Catalyst Separation > Filtration cost > Value | Filtration cost (USD/m3) | value | 0.12; 0.48
