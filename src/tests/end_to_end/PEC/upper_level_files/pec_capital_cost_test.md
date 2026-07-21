# Input files to merge

Name | Value
--- | ---
File A | src/tests/end_to_end/PEC/PEC_Base_test.md

# Direct Capital Costs - Water Management

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Water pump | 415.0 | None | USD | Based on Pinaud 2013. (1.95× the reference value.)
Water manifold piping | 36.58 | {PEC Cells > Number > Value, -} | USD | (3.16× the reference value.)
Water collection piping | 3.202 | {PEC Cells > Number > Value, -} | USD | (2.13× the reference value.)
Water column collection piping | 3.5015 | {PEC Cells > Number > Value, -} | USD | (3.18× the reference value.)
Water final collection piping | 2.531 | {PEC Cells > Number > Value, -} | USD | (10.96× the reference value.)

# Indirect Capital Costs

Name | Value | Path | Unit | Comment 
--- | --- | --- | --- | --- 
Engineering and design | 15% | {Direct Capital Cost > Summed group total > Value, USD} | USD | Based on Pinaud 2013. (2.14× the reference value.)
Process contingency | 35% | {Direct Capital Cost > Summed group total > Value, USD} | USD | (1.75× the reference value.)
Up-front permitting costs | 1.8% | {Direct Capital Cost > Summed group total > Value, USD} | USD | (3.60× the reference value.)
Site preparation | 5% | {Direct Capital Cost > Summed group total > Value, USD} | USD | (5.00× the reference value.)

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment 
--- | --- | --- | --- 
Cost of land | 1550.0 | USD/acre | Land cost based on Pinaud 2013. (3.10× the reference value.)
