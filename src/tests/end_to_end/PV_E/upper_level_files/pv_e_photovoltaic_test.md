# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/PV_E/PV_E_Base_test.md

# Photovoltaic

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | --- 
Nominal power | 3.5 | {Electrolyzer > Nominal power > Value, kW} | kW | 2.33× change from reference value (Optimal PV oversize ratio, same as Chang 2020)
Power loss per year | 0.9% | None | - | 1.8× change from reference value (Based on Chang 2020)
Efficiency | 42% | None | - | 1.91× change from reference value (Only used for area calculation)

# Irradiation Used

Name | Value | Unit | Comment
--- | --- | --- | ---
Data | {Hourly Irradiation > Two axis tracking > Value, kWh/m2} | kWh/m2 | New Component (Two-axis tracking; changed from reference value using horizontal single-axis tracking)
