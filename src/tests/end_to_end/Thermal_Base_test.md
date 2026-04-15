# Workflow

| Name                 | Type   | Description                                     | Position |
| -------------------- | ------ | ----------------------------------------------- | -------- |
| Solar_Thermal_Plugin | plugin | Computes land area required for thermal process | 1        |

# Display Parameters

| Name  | Value   |
| ----- | ------- |
| Name  | Thermal |
| Color | darkred |

# Technical Operating Parameters and Specifications

| Name                      | Value | Unit   |
| ------------------------- | ----- | ------ |
| Operating Capacity Factor | 90    | %      |
| Plant Design Capacity     | 1,000 | kg/day |

# Construction

| Name             | Full Name                                 | Value | Unit |
| ---------------- | ----------------------------------------- | ----- | ---- |
| capital perc 1st | Capital Spent in 1st Year of Construction | 100   | %    |

# Solar Input

| Name             | Value | Unit         | Comment                                                  |
| ---------------- | ----- | ------------ | -------------------------------------------------------- |
| Mean solar input | 6.8   | kWh/(m2*day) | Typical value in Dagget, CA, USA, with two axis tracking |

# Solar-to-Hydrogen Efficiency

| Name | Value | Unit | Comment                                                                                                  |
| ---- | ----- | ---- | -------------------------------------------------------------------------------------------------------- |
| STH  | 20    | %    | Based on DOE Technical Targets for Hydrogen Production from Thermochemical Water Splitting - 2020 Target |

# Direct Capital Costs - Equipment

| Name           | Value     | Unit | Comment                                                                                                                  |
| -------------- | --------- | ---- | ------------------------------------------------------------------------------------------------------------------------ |
| Chemical tower | 2,300,000 | $    | Equipment costs based on DOE Technical Targets for Hydrogen Production from Thermochemical Water Splitting - 2020 Target |

# Direct Capital Costs - Gas Processing

| Name          | Value     | Unit | Comment                                                                                              |
| ------------- | --------- | ---- | ---------------------------------------------------------------------------------------------------- |
| Compressor    | 526,302.0 | $    | Cost estimate based on Pinaud 2013. Fixed cost of compressor for plant design output (1 ton H2/day). |
| Condenser     | 13,765.0  | $    |
| Intercooler-1 | 15,103.0  | $    |
| Intercooler-2 | 15,552.0  | $    |

# Non-Depreciable Capital Costs

| Name                 | Value | Unit   | Comment                         |
| -------------------- | ----- | ------ | ------------------------------- |
| Cost of land         | 500.0 | $/acre | Land cost based on Pinaud 2013. |
| Additional Land Area | 30    | %      | Additional land area required.  |

# Planned Replacement

| Name              | Frequency | Frequency Unit | Cost   | Cost Unit | Comment                                                                                                  |
| ----------------- | --------- | -------------- | ------ | --------- | -------------------------------------------------------------------------------------------------------- |
| Reaction material | 1         | years          | 89,000 | $         | Based on DOE Technical Targets for Hydrogen Production from Thermochemical Water Splitting - 2020 Target |

# Fixed Operating Costs

| Name              | Full Name                               | Value | Unit   |
| ----------------- | --------------------------------------- | ----- | ------ |
| staff             | Number of staff                         | 7     |
| hourly labor cost | Burdened labor cost, including overhead | 50.0  | $/hour |

# Utilities

| Name                   | Usage per kg H2 | Usage Unit | Cost                                                                                | Cost Unit | Price Conversion Factor | Price Conversion Factor Unit | Comment                                                                                                       |
| ---------------------- | --------------- | ---------- | ----------------------------------------------------------------------------------- | --------- | ----------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Industrial Electricity | 0.16            | kWh/kg     | pyH2A.Lookup_Tables.Utility_Cost~Industrial_Electricity_AEO_2017_Reference_Case.csv | GJ        | 0.0036                  | GJ/kWh                       | Electricity usage based on Pinaud 2013.                                                                       |
| Process Water          | 2.369           | gal/kg     | 0.0023749510945008                                                                  | $/gal     | 1.                      | None                         | Seawater reverse osmosis cost ca. 0.6 $/m3 (equal to ca. 0.0023 $/gal), based on Kibria 2021 and Driess 2021. |
