# Input files to merge

Name | Value
--- | ---
Base | src/tests/e2e_lca/data/input_files/pv_e_base.md
Defaults | pyH2A.Config~Defaults_LCA.md

# Electrolyzer

Name | Value | Unit | Comment
--- | --- | --- | ---
Nominal power | 4,000 | kW | Smaller electrolyzer than in base scenario
Power requirement increase per year | 0.5% | - | Faster stack degradation than in base scenario
Hydrogen yield per unit energy | 0.02 | kg/kWh | More efficient electrolyzer than in base scenario
Replacement time | 40,000 | h | Shorter stack lifetime than in base scenario
Unit nominal power | 250 | kW | Smaller electrolyzer units than in base scenario

# Photovoltaic

Name | Value | Path | Unit | Comment
--- | --- | --- | --- | ---
Nominal power | 2.0 | {Electrolyzer > Nominal power > Value, kW} | kW | Larger PV oversize ratio than in base scenario
Efficiency | 18% | None | - | Less efficient PV modules than in base scenario

# Reverse Osmosis

Name | Value | Unit | Comment
--- | --- | --- | ---
Recovery rate | 45% | - | Higher recovery rate than in base scenario
Device throughput | 0.5 | m3/h | Smaller reverse osmosis devices than in base scenario
