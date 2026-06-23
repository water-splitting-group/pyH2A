# LCA Tests — pyH2A

## Overview
This directory contains all unit tests and end-to-end ground truth tests for the LCA implementation in pyH2A. The tests verify that the LCA calculation engine produces correct results by comparing against independently computed openLCA reference values.

## Directory Structure
```
src/tests/lca/
    lca_test.py                  — unit tests for LCA.py methods
    lca_utils_test.py            — unit tests for lca_utils.py functions
    01_lca_gt_e2e_test.py        — ground truth tests (direct LCA engine)
    02_mc_lca_pipeline_test.py   — Monte Carlo + LCA pipeline test (seed=42)
    input_files/
        PVE_GT_MC_seed42.md      — Monte Carlo + Parameters input file

data/LCA/LCA_Test_PVE_GT/        — toy model matrix export (openLCA)
```

## How to Run the Tests

Run all LCA tests:
```powershell
pytest src/tests/lca/ -v
```

Run with results printed (ground truth comparison):
```powershell
pytest src/tests/lca/01_lca_gt_e2e_test.py -v -s
```

Run unit tests only:
```powershell
pytest src/tests/lca/lca_test.py src/tests/lca/lca_utils_test.py -v
```

Expected result:
```
80 passed, 0 skipped
```

## Test Files

### lca_utils_test.py — 30 tests
Unit tests for all functions in `src/pyH2A/Utilities/lca_utils.py`: matrix loading, index resolution, factorization, and disk-cache path handling.

### lca_test.py — 43 tests
Unit tests for all public methods in `src/pyH2A/LCA/LCA.py`: cache-key generation, component-value resolution and application, disk/RAM cache loading, LCIA arithmetic, and full `LCA` object integration against the real matrix.

### 01_lca_gt_e2e_test.py — 6 tests
End-to-end ground truth tests that directly drive the LCA calculation engine via a `DummyDCF` with hardcoded component values — no plugins, no `.md` file parsing, no full DCF pipeline. The three caching paths (cold start, warm disk, warm RAM) are each exercised once across the 5 ground-truth scenarios below.

**What it tests:** LCA matrix math, UUID lookup, sign convention, Sherman-Morrison formula, caching

### 02_mc_lca_pipeline_test.py — 1 test
Runs `Monte_Carlo_Analysis` exactly as a normal user would: passes `input_files/PVE_GT_MC_seed42.md` (which specifies `Monte_Carlo_Analysis` and `Parameters - Monte_Carlo_Analysis` tables) with the random seed fixed at 42, and compares the resulting results array (PV, RO, GWP100 for 150 samples) against precalculated reference values.

**What it tests:** full Monte Carlo pipeline — parameter sampling, multiprocessing dispatch, and LCA evaluation — against the real `LCA_Test_PVE_GT` matrix

---

## Toy Model for Ground Truth Tests

### Background
A simplified PV+E (photovoltaic + electrolysis) hierarchical toy model was built in openLCA 2.6.1 using ecoinvent 3.12 Cutoff System background processes. This model provides fast, deterministic ground truth values for testing the LCA pipeline.

### Model Structure
```
H2 Production (Level 1 — reference process)
    ↓
PV Electricity Generation (Level 2)
Reverse Osmosis (Level 2)
Electrolyzer Manufacturing (Level 2)
    ↓
PV Module Manufacturing (Level 3)
RO Manufacturing (Level 3)
    ↓
ecoinvent 3.12 background processes (Level 4)
```

### Model Details

| Property | Value |
|---|---|
| Software | openLCA 2.6.1 |
| Background database | ecoinvent 3.12 Cutoff System |
| Impact method | IPCC 2013 no LT |
| Impact category | Climate change no LT — GWP100 |
| Foreground processes | 6 custom processes |
| Total processes | 17,188 |
| Functional unit | 1 kg H2 |
| Matrix export | `data/LCA/LCA_Test_PVE_GT/` |

### Foreground Process UUIDs

| Process | Matrix Index | UUID |
|---|---|---|
| H2 Production | 0 | `66b8a6b0-7b7a-4d2c-95d3-d82951c58a35` |
| RO Manufacturing | 3559 | `49e80fd1-939e-4723-8b29-bd969c10d1db` |
| PV Electricity Generation | 3560 | `bc18dc79-2b51-455d-9fec-decf6b2693de` |
| PV Module Manufacturing | 16247 | `a376df26-acc5-4fae-80e4-670a6b63a063` |
| Electrolyzer Manufacturing | 16413 | `4397d5db-7fea-4916-af17-b72fa72fc02a` |
| Reverse Osmosis | 16415 | `1659c3a5-5c6b-4f29-b746-e12119144b7b` |

### Original A Matrix First Column Values

| Process | Index | Value |
|---|---|---|
| H2 Production | 0 | +1.0 |
| PV Electricity Generation | 3560 | -198.0 MJ |
| Electrolyzer Manufacturing | 16413 | -1e-6 Item |
| Reverse Osmosis | 16415 | -9.0 kg |

---

## The 5 Test Scenarios

All scenarios vary all 4 component values simultaneously to test the full A matrix update logic. The functional unit is always 1 kg H2.

> **Note:** PV electricity is stored as MJ in the A matrix (openLCA internal unit). kWh values are shown for readability — conversion: kWh × 3.6 = MJ.

| Scenario | H2 (kg) | PV (kWh) | PV (MJ) | Electrolyzer (Item) | RO (kg) | openLCA GWP100 (kg CO2-Eq) |
|---|---|---|---|---|---|---|
| S1 — Base | 1.0 | 55.0 | 198.0 | 1e-6 | 9.0 | 0.454132 |
| S2 — Low PV | 1.0 | 41.67 | 150.0 | 2e-6 | 7.0 | 0.34409 |
| S3 — High PV | 1.0 | 69.44 | 250.0 | 5e-7 | 12.0 | 0.57345 |
| S4 — Low PV + Low RO | 1.0 | 27.78 | 100.0 | 3e-6 | 5.0 | 0.22945 |
| S5 — High PV + High RO | 1.0 | 83.33 | 300.0 | 1e-7 | 15.0 | 0.68823 |

### How Ground Truth Values Were Obtained

For each scenario:

1. Copied H2 Production process in openLCA 2.6.1 — renamed `H2 Production S1` through `S5`
2. Changed exchange amounts to match scenario values 
3. Created a new product system with auto-link and preferred default providers
4. Calculated LCIA with IPCC 2013 no LT impact method
5. Recorded `Climate change no LT — Global warming potential (GWP100) no LT` result

Each scenario was created as a separate product system (`PVE_TEST_GT_S1` through `PVE_TEST_GT_S5`) to preserve all runs independently.

---

## Expected Test Output

Run with `-s` flag to see pyH2A vs openLCA comparison:
```powershell
pytest src/tests/lca/01_lca_gt_e2e_test.py -v -s
```

Ground truth comparison results:

| Scenario | pyH2A GWP100 (kg CO2-Eq) | openLCA GWP100 (kg CO2-Eq) | Diff (%) |
|---|---|---|---|
| S1 — Base | 0.454132 | 0.454132 | 0.0000% |
| S2 — Low PV | 0.344067 | 0.344090 | 0.0066% |
| S3 — High PV | 0.573483 | 0.573450 | 0.0057% |
| S4 — Low PV + Low RO | 0.229428 | 0.229450 | 0.0098% |
| S5 — High PV + High RO | 0.688259 | 0.688230 | 0.0042% |


---

## Notes

- The toy model matrix (`data/LCA/LCA_Test_PVE_GT/`) must be present for ground truth tests to run.
- Tests were developed and verified on `design/lca-prototype`   and `feat/lca-calculate-shortcut-method` branches.