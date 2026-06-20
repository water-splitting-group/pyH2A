# LCA Tests — pyH2A

## Overview
This directory contains all unit tests and end-to-end ground truth tests for the LCA implementation in pyH2A. The tests verify that the LCA calculation engine produces correct results by comparing against independently computed openLCA reference values.

## Directory Structure
```
src/tests/lca/
    test_lca.py                  — unit tests for LCA.py methods
    test_lca_utils.py            — unit tests for lca_utils.py functions
    test_lca_gt_e2e.py           — Level 1 ground truth tests (direct LCA engine)
    dcf_lca_gt_pipeline_test.py   — Level 2 ground truth tests (full DCF pipeline)
    input_files/
        PVE_GT_S1.md             — scenario 1 input file (base case)
        PVE_GT_S2.md             — scenario 2 input file (low PV)
        PVE_GT_S3.md             — scenario 3 input file (high PV)
        PVE_GT_S4.md             — scenario 4 input file (low PV + low RO)
        PVE_GT_S5.md             — scenario 5 input file (high PV + high RO)

data/LCA/LCA_Test_PVE_GT/        — toy model matrix export (openLCA)
```

## How to Run the Tests

Run all LCA tests:
```powershell
pytest src/tests/lca/ -v
```

Run with results printed (ground truth comparison):
```powershell
pytest src/tests/lca/test_lca_gt_e2e.py src/tests/lca/dcf_lca_gt_pipeline_test.py -v -s
```

Run unit tests only:
```powershell
pytest src/tests/lca/test_lca.py src/tests/lca/test_lca_utils.py -v
```

Expected result:
```
148 passed, 0 skipped
```

## Test Files

### test_lca_utils.py — 68 tests
Unit tests for all functions and classes in `src/pyH2A/Utilities/lca_utils.py`:

| Class / Function | What is tested |
|---|---|
| `TechEntry` | parsing and indexing of technosphere matrix entries |
| `ImpactEntry` | parsing and indexing of impact category entries |
| `ExportFolder` | loading matrix files from openLCA export directory |
| `Matrix` | string constants for matrix file names |
| `factorize` | sparse and dense matrix factorization |
| `_FactorizedSolver` | solver wrapper for repeated solves |

### test_lca.py — 59 tests
Unit tests for all public methods in `src/pyH2A/LCA/LCA.py`:

| Test Class | What is tested |
|---|---|
| `TestBuildMatrixCacheKey` | cache key generation from matrix metadata |
| `TestExtractComponentFields` | UUID and Value extraction from component data |
| `TestApplyComponentUpdates` | sign convention, UUID lookup, index mapping |
| `TestLoadSolverFromDiskToRam` | disk cache loading and validation |
| `TestLoadBasisVectorsFromDisk` | basis vector cache loading and validation |
| `TestStoreSolverAndArtifactsInRam` | RAM cache storage |
| `TestPerformLca` | LCIA arithmetic and result storage |
| `TestLCAIntegration` | full LCA object integration tests using real matrix |

### test_lca_gt_e2e.py — 14 tests (Level 1)
End-to-end ground truth tests that directly test the LCA calculation engine using `MagicMock` DCF with hardcoded component values. No plugins, no `.md` file parsing, no full pipeline.

**What it tests:** LCA matrix math, UUID lookup, sign convention, Sherman-Morrison formula, caching

### dcf_lca_gt_pipeline_test.py — 5 tests (Level 2)
End-to-end ground truth tests that run the full DCF pipeline by reading actual `.md` input files. Each test reads its own scenario file, runs `Discounted_Cash_Flow`, and reads the LCA result.

**What it tests:** `.md` file parsing, DCF pipeline, LCA integration, full chain from file to result

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

## Input Files for Level 2 Tests

Located in `src/tests/lca/input_files/`:

| File | Description |
|---|---|
| `PVE_GT_S1.md` | Scenario 1 — base case (H2=1.0, PV=55.0 kWh, Elec=1e-6, RO=9.0 kg) |
| `PVE_GT_S2.md` | Scenario 2 — low PV (H2=1.0, PV=41.67 kWh, Elec=2e-6, RO=7.0 kg) |
| `PVE_GT_S3.md` | Scenario 3 — high PV (H2=1.0, PV=69.44 kWh, Elec=5e-7, RO=12.0 kg) |
| `PVE_GT_S4.md` | Scenario 4 — low PV + low RO (H2=1.0, PV=27.78 kWh, Elec=3e-6, RO=5.0 kg) |
| `PVE_GT_S5.md` | Scenario 5 — high PV + high RO (H2=1.0, PV=83.33 kWh, Elec=1e-7, RO=15.0 kg) |

---

## Expected Test Output

Run with `-s` flag to see pyH2A vs openLCA comparison:
```powershell
pytest src/tests/lca/test_lca_gt_e2e.py src/tests/lca/dcf_lca_gt_pipeline_test.py -v -s
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
