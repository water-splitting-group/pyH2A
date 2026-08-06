# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/PEC_Base_test.md
Default TEA | pyH2A.Config~Defaults_TEA.md

# Irradiance Area Parameters

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Module tilt | 0.5 | deg | Two axis tracking, module tilt and array azimuth change are not relevant (0.5 deg above the reference value.)
Array azimuth | 0.5 | deg | Two axis tracking, module tilt and array azimuth change are not relevant (0.5 deg above the reference value.)
Nominal operating temperature | 95 | degC | Temperature is stabilized even under solar concentration through intrinsic water cooling.  (50 degC above the reference temperature.)
Mismatch derating | 48% | - | (0.49× the reference value.)
Dirt derating | 49% | - | Values taken from Chang 2020, analogues to silicon PV (0.50× the reference value.)
Temperature coefficient | 50% | 1/delta_degC | No assumed efficiency loss with higher temperature (Reference value is 0%.)