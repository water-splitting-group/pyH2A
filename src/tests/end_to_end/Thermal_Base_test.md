# Workflow

Name | Type | Description | Position |
--- | --- | --- | --- |
Solar_Thermal_Plugin | plugin | Computes land area required for thermal process | 1 |

# Display Parameters

Name | Value 
--- | --- 
Name | Thermal 
Color | darkred 

# Technical Operating Parameters and Specifications

Name | Value | Unit |
--- | --- | --- |
Operating capacity factor | 90% | - |
Plant design capacity | 1,000. | kg/day |

# Construction

Name | Full Name | Value | Unit |
--- | --- | --- | --- |
Capital perc 1st | Capital Spent in 1st Year of Construction | 100% | - |

# Solar Input

Name             | Value | Unit          | Comment                                                  |
--- | --- | --- | --- |
Mean solar input | 6.8 | kWh_per_day/m2 | Typical value in Dagget, CA, USA, with two axis tracking |

# Solar-to-Hydrogen Efficiency

Name | Value | Unit | Comment |
--- | --- | --- | --- |
STH | 20% | - | Based on DOE Technical Targets for Hydrogen Production from Thermochemical Water Splitting - 2020 Target |

# Direct Capital Costs - Equipment

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Chemical tower | 2,300,000. | USD | Equipment costs based on DOE Technical Targets for Hydrogen Production from Thermochemical Water Splitting - 2020 Target |

# Direct Capital Costs - Gas Processing

Name | Value | Unit | Comment |
--- | --- | --- | --- |
Compressor    | 526,302.0 | USD | Cost estimate based on Pinaud 2013. Fixed cost of compressor for plant design output (1 ton H2/day). |
Condenser     | 13,765.0  | USD |
Intercooler-1 | 15,103.0  | USD |
Intercooler-2 | 15,552.0  | USD |

# Non-Depreciable Capital Costs

Name | Value | Unit   | Comment                         |
--- | --- | --- | --- |
Cost of land | 500.0 | USD/acre | Land cost based on Pinaud 2013. |
Additional land area | 30%   | - | Additional land area required.  |

# Planned Replacement

Name | Frequency_Value | Frequency_Unit | Cost_Value | Cost_Unit | Comment |
--- | --- | --- | --- | --- | --- |
Reaction material | 1. | year | 89,000. | USD | Based on DOE Technical targets for Hydrogen Production from Thermochemical Water Splitting - 2020 Target |

# Fixed Operating Costs

Name | Full Name | Value | Unit |
--- | --- | --- | --- |
Staff | Number of staff | 7. | - |
Hourly labor cost | Burdened labor cost, including overhead | 50.0  | USD/h |

# Utilities

Name | Usage_Value | Usage_Path | Usage_Unit | Cost_Value | Cost_Path | Cost_Unit | Price_Conversion_Factor_Value | Price_Conversion_Factor_Unit | Comment |
--- | --- | --- | --- | --- | --- | --- | --- | --- |
Industrial electricity | 0.16 | None | -/kg | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | None | USD | 0.0036 | - | Electricity usage based on Pinaud 2013. |
Process water | 2.369 | None | -/kg | 0.0023749510945008 | None | USD | 1.0 | - | Seawater reverse osmosis: 2.369 gal/kg H2, at a cost of ca. 0.6 USD/m3 (equal to ca. 0.0023 USD/gal), based on Kibria 2021 and Driess 2021. |
