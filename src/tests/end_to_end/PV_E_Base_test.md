# Functional Unit

Name | Unit of measurement | Reference
--- | --- |
Functional unit | kg | H2 at gate

# Workflow

Name | Type | Position |
--- | --- | --- |
Hourly_Irradiation_Plugin | plugin | 0 |
Photovoltaic_Plugin | plugin | 0 |
Electrolyzer_Plugin | plugin | 0 |
Battery_Plugin | plugin | 0 |
Stored_Power_Electrolysis_Plugin | plugin | 0 |
Reverse_Osmosis_Plugin | plugin | 2 |
Power_Management_Plugin | plugin | 2 |
Multiple_Modules_Plugin | plugin | 3 |

# Display Parameters

Name | Value |
--- | --- |
Name | PV + E |
Color | darkblue |

# Hourly Irradiation

Name | Value | Comment |
--- | --- | --- | --- |
File | pyH2A.Lookup_Tables.Hourly_Irradiation_Data~tmy_34.859_-116.889_2006_2015.csv | Location: Dagget, CA, USA |

# Irradiance Area Parameters

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Array azimuth | 180. | deg |
Nominal operating temperature | 45. | degC |
Mismatch derating | 0.98 | - | Based on Chang 2020. |
Dirt derating | 0.98 | - | Based on Chang 2020. |
Temperature coefficient | -0.4% | 1/delta_degC | Based on Chang 2020. |

# Irradiation Used

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Data | {Hourly Irradiation > Horizontal single axis tracking > Value, kWh/m2} | kWh/m2 | Single axis tracking based on Chang 2020. |

# Technical Operating Parameters and Specifications

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Plant modules | 10 | - | Modelling of 10 modules for calculation of staff cost to facilitate comparison with PEC and photocatalytic model. |
Fraction of output that reaches gate | 100% | -

# Construction

Name | Full Name | Value | Unit |
--- | --- | --- | --- |
Capital perc 1st | Fraction of capital | 100% | - |

# CAPEX Multiplier

Name | Value | Unit | Full Name |
--- | --- | --- | --- |
Multiplier | 1.0 | - | CAPEX multiplier for every 10-fold increase of system size. |

# Electrolyzer

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Nominal power | 5,500.0 | kW | Production of ca. 1 t of H2 per day to compare with PEC and photocatalytic models. |
CAPEX reference power | 1,000.0 | kW |
Power requirement increase per year | 0.3% | - | Based on Chang 2020 |
Minimum capacity | 10% | - | Based on Chang 2020, minimum capacity for electrolyzer to operate. |
Hydrogen yield per unit energy | 0.0185 | kg/kWh | Based on Chang 2020 |
Replacement time | 80,000.0 | h | Based on Chang 2020, operating time after which electrolyzer stacks have to be replaced. |

# Electrolysis Using Stored Power

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Fraction of stored power used for electrolysis | 0.95 | - | Additional electrolysis using stored power |

# Photovoltaic

Name | Value | Path | Unit | Comment |
--- | --- | --- | --- | --- |
Nominal power | 1.5 | {Electrolyzer > Nominal power > Value, kW} | kW | Optimal PV oversize ratio, same as Chang 2020 |
CAPEX reference power | 1,000.0 | None | kW |
Power loss per year | 0.5% | None | - | Based on Chang 2020 |
Efficiency | 22% | None | - | Only used for area calculation. |

# Battery

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Design capacity | 800000. | kWh | Full design capacity |
Lowest discharge level | 20% | - | Lowest level to which battery can be discharged |
Capacity loss per year | 1% | - | Loss of capacity per year |
Round trip efficiency | 100% | - | For lithium ion battery |

# Reverse Osmosis

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Power demand | 2.71 | kWh/m3 | based on Hausmann 2021 and Kim 2008 (this was chosen for a purity of < 10 ppm of disolved salts in the obtained water), kWh per m3 of sea water |
Average operating time fraction | 0.16666666666666666 | - | Assumption that reverse osmosis runs for 4 h/day, relevant for scaling of reverse osmosis plant |
Recovery rate | 40% | - | Fraction of fresh water obtained from given volume of sea water, based Palmer 2021 and Tewlour 2022 |

# Power Consumption

Name | Value | Unit | Type |
--- | --- | --- | --- |
Test consumer | 0. | kWh | on_demand |

# Direct Capital Costs - Reverse Osmosis

Name | Value | Path | Unit | Comment |
--- | --- | --- | --- | --- |
Reverse osmosis CAPEX | 6000. | {Reverse Osmosis > Capacity > Value, m3/h} | USD | Based on https://samcotech.com/much-reverse-osmosis-nanofiltration-membrane-systems-cost/, Conversion factor of 4.5 from GPM to m3/h |

# Direct Capital Costs - Battery

Name | Value | Path | Unit |
--- | --- | --- | --- |
Battery CAPEX | 0. | {Battery > Design capacity > Value, kWh} | USD |

# Direct Capital Costs - PV

Name | Value | Path | Unit | Comment |
--- | --- | --- | --- | --- |
PV CAPEX | 818. | {Photovoltaic > Nominal power > Value, kW} ; {Photovoltaic > Scaling factor > Value, -} | USD | Based on Chang 2020, Chiesa 2021 Middle East PV installation cost, Shah 2021. |

# Direct Capital Costs - Electrolyzer

Name | Value | Path | Unit | Comment |
--- | --- | --- | --- | --- |
Electrolyzer CAPEX | 784. | {Electrolyzer > Nominal power > Value, kW} ; {Electrolyzer > Scaling factor > Value, -} | USD | Based on Chang 2020, IRENA 2020 Green Hydrogen (PEM System CAPEX 700 - 1400 USD/kg), Shah 2021. |

# Non-Depreciable Capital Costs

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Cost of land | 500.0 | USD/acre | Same as PEC and Photocatalytic model, based on Pinaud 2013. |

# Fixed Operating Costs

Name | Full Name | Value | Unit | Comment |
--- | --- | --- | --- | --- |
Solar collection area per staffer | Area per staff | 405,000. | m2 | Same as photocatalytic model, solar collection area that can be overseen by one staff member. |
Number of supervisors | Shift supervisor | 1 | - | Same as PEC and photocatalytic model, number of shift supervisors. |
Number of 8-hour shifts | Shifts | 3 | - | Same as PEC and photocatalytic model, number of shifts per day. |
Hourly labor cost | Burdened labor cost, including overhead (USD per man-hr) | 50.0 | USD/h | Same as PEC and photocatalytic model. |

# Other Fixed Operating Costs

Name | Value | Path | Unit | Comment |
--- | --- | --- | --- | --- |
Electrolyzer OPEX (fraction of CAPEX) | 2% | {Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value, USD} | USD | Based on Stolten 2020, Shah 2021. |
PV OPEX (fraction of CAPEX) | 2% | {Direct Capital Costs - PV > PV CAPEX > Value, USD} | USD | Based on Stolten 2020. |

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment |
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Process Water | 10. | None | 1/kg | 0.0006 | None | USD | 1. | - | Seawater reverse osmosis cost ca. 0.6 USD/m3 (equal to 0.0006 USD/L), based on Kibria 2021 and Driess 2021. |

# Grid Electricity

Name | Value | Unit |
--- | --- | --- |
Cost | 10000.12 | USD/kWh |

# Planned Replacement

Name | Cost_Value | Cost_Path | Cost_Unit | Frequency_Value | Frequency_Unit | Comment |
--- | --- | --- | --- | --- |
Electrolyzer stack replacement | 40% | {Direct Capital Costs - Electrolyzer > Electrolyzer CAPEX > Value, USD} | USD | {Electrolyzer > Stack lifetime > Value, year} | year | Based on Chang 2020 |

