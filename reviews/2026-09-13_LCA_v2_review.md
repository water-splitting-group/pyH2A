# Critical review of the LCA implementation on `feat/lca-v2`

**Date:** 2026-09-13
**Branch reviewed:** `feat/lca-v2` at `c8b2c06` (*Merge branch 'feat/lca' into feat/lca-v2*)
**Scope:** `Plugins/Life_Cycle_Assessment_Plugin/`, `Utilities/lca_utils.py`, `pyH2A/LCA/`, the
LCA test suites (`tests/plugins/life_cycle_assessment_plugin_test.py`,
`tests/e2e_lca/`, `tests/Utilities/Lca_Utils/`) and `doc/lca_guide.rst`.
**Status:** review only — **no production code was changed** by this report.

---

## 1. How this review was done

Every finding below was checked against the running code, not inferred from reading it.
The test suite was installed and executed (`22 passed` for the LCA tests, `53 passed`
including `Lca_Utils`), and each claim was reproduced with a short throwaway script.
Where a number is quoted it was measured on this branch, on:

* the bundled toy exports in `src/tests/e2e_lca/data/matrix_folders/` (n = 1…10 processes), and
* synthetic openLCA-shaped exports built for this review at background-database scale
  (n = 1,200 / 8,000 / 20,000 processes, m = 400 / 2,500 / 4,000 elementary flows,
  nnz(B) up to 4 × 10⁶), with ~15 inputs per technosphere column.

Measurements were taken on the session container (Python 3.14, NumPy 2.x, SciPy 1.17),
so absolute timings are indicative; the *ratios* are the point.

---

## 2. What the implementation gets right

It is worth stating this plainly before the criticism, because the core design decision is
sound and the review should not be read as a case for reworking it.

**The Sherman–Morrison engine is the right call, and it is numerically solid.**
Scenario variation only ever touches column 0 of the technosphere matrix, so a rank-1 update
of a single pre-computed factorisation is exactly the right structure. Measured against a full
re-factorisation + solve of the updated system:

| scenario (non-reference exchanges scaled by) | `1 + z[0]` | max relative error of the SM result vs. a direct solve |
|---|---|---|
| ×1.5 | 0.9977 | 5.9 × 10⁻¹⁵ |
| ×10 | 0.9595 | 8.9 × 10⁻¹⁵ |
| ×100 | 0.5544 | 6.2 × 10⁻¹⁴ |
| ×10,000 | −44.01 | 7.6 × 10⁻¹⁴ |
| ×0.01 | 1.0045 | 5.1 × 10⁻¹³ |

*(n = 1,200 randomly-structured synthetic export; the bundled toy models are triangular and
give exactly 0 error, which is why a non-triangular case was used.)*

So the update is accurate to ~10⁻¹³ relative across four orders of magnitude of scenario
perturbation. The cost it avoids is large: on the n = 8,000 synthetic export a full
re-factorisation + solve takes **50.5 s**, versus **0.02 ms** for the rank-1 update. The
design is correct and the payoff is real. Everything below is about the scaffolding
around it.

Other things that check out and should *not* be changed:

* `A0_column` / `basis_component` / `delta_coeff` are all consistently ordered, so the
  update is invariant to the ordering of `index_A.csv` rows (verified by reversing the file —
  the impact result was identical; see M4 for the one part that is *not* invariant).
* Declaring the functional flow in a different unit of the same dimension (e.g. `ton` where
  the export says `kg`) produces a self-consistent, correctly-labelled result
  (`1 ton` functional flow → `0.01 kg / kg`), because the result `Quantity` carries the
  export's own flow unit. This is right; see M5 for the residual hazard.
* A duplicated UUID across two `# LCA - ...` tables is caught, not silently applied — the
  row-count guard and the missing-UUID completeness check together close that hole.
  (Only the *error message* is misleading; see §7.)

---

## 3. Findings at a glance

| # | Severity | Finding | Evidence |
|---|---|---|---|
| **C1** | **Critical** | `_cache` is class-level and **not keyed by matrix folder** — a second matrix folder in the same process silently returns the first folder's results | reproduced |
| **C2** | **Critical** | The on-disk `Initial_Artifacts` cache is **never invalidated** when the openLCA export in the same folder changes — stale results survive across processes and CI runs | reproduced |
| **H1** | High | A corrupt/partial cache file is a **permanent hard failure** (`BadZipFile`); only `FileNotFoundError` is recovered, and `shutil.copy2` of B/C is not atomic | reproduced |
| **H2** | High | `get_cache_paths` memoises a `mkdir` side effect; deleting the cache dir mid-process causes an **uncaught `FileNotFoundError`** (`save_all_to_disk` guards only `PermissionError`) | reproduced |
| **H3** | High | `_load_tech_index` keys on the **provider UUID**, so a multi-output process silently collapses technosphere rows | reproduced |
| **H4** | High | An impact unit absent from `Plugins/.../config.py` `CONFIG` raises a bare `KeyError` — this blocks most real LCIA methods | reproduced |
| **M1** | Medium | Demand-vector entries other than `f[0]` are silently retained, while results are still labelled "per 1 unit" | reproduced |
| **M2** | Medium | A negative component `Value` is silently turned positive by `abs()` | reproduced |
| **M3** | Medium | `_SM_TOL` is an **absolute** guard at 1e-12; ~10⁻⁵ relative error is reached long before it fires, and there is no fallback | measured |
| **M4** | Medium | "`A0_column[0]` is technosphere index 0" is an unchecked assumption about `index_A.csv` row order | reproduced |
| **M5** | Medium | The Functional Unit cross-check compares **dimension only**, which is weaker than the guarantee its own error message claims | code + reproduced |
| **M6** | Medium | openLCA flow-unit handling is a duplicated `.replace('(s)', '')` hack with no alias table | code |
| **M7** | Low | The `reference` labels in `CONFIG` are dead — GWP and Acidification both come back as `'kg / kg'` | code |
| **P1** | **Perf** | Per-sample LCIA recomputes `C @ (B @ x)`; precomputing `C@B` (and `(C@B)@basis`) gives **500–1600×** on that step at ecoinvent scale | measured |
| **P2** | Perf | `factorize()`'s pypardiso branch does not do what its docstring says; the `performance` extra is worth ~12× on cold start and is **not installed in CI** | measured |
| **P3** | Perf | B and C are duplicated into `Initial_Artifacts` for no benefit — 71 % of the cache footprint in the measured case | measured |
| **P4** | Perf | Per-sample `Quantity` churn and `input_resolver_function` dominate the warm path once P1 lands | measured |

---

## 4. Critical: the caching layer

Both critical findings are in the caching layer, and both fail the same way — **silently, with
plausible-looking numbers**. Neither raises, neither warns, neither leaves a trace in the
output. For an LCA tool whose entire output is a set of numbers a user will put in a paper,
this is the worst available failure mode.

### C1 — `_cache` is not keyed by the matrix folder

`Life_Cycle_Assessment_Plugin._cache` (line 84) is a plain class attribute, and the cache-hit
guard is:

```python
# Life_Cycle_Assessment_Plugin.py:186
if all(Life_Cycle_Assessment_Plugin._cache[k] is not None for k in Life_Cycle_Assessment_Plugin._cache):
    return
```

Nothing in that guard — or anywhere else — checks that the cached artifacts came from
`self.matrix_folder`. The first matrix folder touched in a process wins for the lifetime of
that process.

Reproduced by running two of the repo's own toy exports back to back in one process, with no
cache clearing (i.e. exactly what production code does):

```
--- reference values, each computed in a clean cache state ---
GWP folder -> {'Global warming potential': (10.0, 'kg / kg')}
CED folder -> {'Cumulative energy demand': (50.0, 'kWh / kg')}

--- same two folders, back-to-back in one process, no cache clearing ---
1st call (GWP folder) -> {'Global warming potential': (10.0, 'kg / kg')}
2nd call (CED folder) -> {'Global warming potential': (10.0, 'kg / kg')}   <-- wrong folder's result

CED result correct? False
```

The second call asked for the CED export and got the GWP export's matrices, impact index and
units. No exception, no warning.

**This is already known to the team — but only to the tests.** Both LCA test modules carry
explicit workarounds and explicit comments:

```python
# tests/plugins/life_cycle_assessment_plugin_test.py:63-71
def _clear_caches():
    """Life_Cycle_Assessment_Plugin._cache is a process-wide class attribute, not
    per-instance, so it must be cleared to avoid reusing another test's cached
    matrices."""
```

and, at length, in `tests/e2e_lca/gt_lca_e2e_all_layers_test.py:31-40`:

> "…it is not keyed by matrix folder, so running more than one matrix folder within the same
> process … requires manually clearing both the RAM cache and that folder's on-disk
> Initial_Artifacts cache before switching folders (otherwise a later folder would silently
> reuse an earlier folder's cached artifacts, producing **incorrect results**)."

So the tests pass *because* they know to clear the cache. No production code path does. Any
user who compares two LCA models in one Python session, scripts a sweep over matrix folders,
or works in a Jupyter notebook gets silently wrong numbers. `Comparative_MC_Analysis` — which
exists precisely to run several input files together — is the obvious in-repo trigger.

**Fix.** Key the cache by the resolved matrix folder. The minimal change is a stored
`_cache_key` compared against `os.path.realpath(self.matrix_folder)` in the guard, dropping
the cache on mismatch. A dict keyed by folder is better if more than one folder is expected
to be hot at once (it also removes the "clear before switching" requirement from the tests).

### C2 — the on-disk cache is never invalidated when the export changes

`Initial_Artifacts/` is written inside the matrix export folder and is read back on any
process whose RAM cache is cold. Nothing records *which* export produced it — no hash, no
mtime, no file size, no shape check.

Reproduced by copying an export to a scratch folder, running LCA (which builds the cache),
then overwriting `A/B/C/f/index_*.csv` in place with a different model — as a user does when
they re-export from openLCA into the same directory:

```
run 1 (GWP export in folder)      -> {'Global warming potential': (10.0, 'kg / kg')}
Initial_Artifacts created         -> ['A0_column.npz', 'base_scaling_vector.npz',
                                      'basis_component.npz', 'impact_index.npz',
                                      'matrix_B.npy', 'matrix_C.npz']
source export replaced with the CED model (A/B/C/f/index_*.csv all overwritten)
run 2 (CED export in same folder) -> {'Global warming potential': (10.0, 'kg / kg')}

expected after re-export: {'Cumulative energy demand': (50.0, 'kWh / kg')}
```

This is strictly worse than C1: it persists **across processes**, across reboots, and into CI.
A fresh `pyH2A run` reads the stale artifacts. The only cure is knowing to delete the folder.

The documentation already concedes this, in bold:

> `doc/lca_guide.rst`: "The artifacts are valid as long as the matrix export does not change.
> **Delete the `Initial_Artifacts` folder whenever you export the new matrices from openLCA**."

Relying on user discipline for a silent-wrong-answer failure is not a reasonable trade when
the fix is a few lines. Note also that a *partial* re-export — say only `index_C.csv` changes
because the user switched impact method — is even easier to miss than a full one.

**Fix.** Write a fingerprint alongside the artifacts and compare it on load: the
`(size, mtime_ns)` of each source file (`A`, `B`, `C`, `f`, `index_A.csv`, `index_C.csv`) is
cheap and sufficient; a content hash of the index CSVs plus the matrix shapes/nnz is stronger
and still cheap relative to the factorisation being protected. On mismatch, recompute rather
than raising — the user should not have to do anything. A schema/format version in the same
file guards against a future change to the artifact layout silently reading old files.

---

## 5. High-severity findings

### H1 — a corrupt or partially-written cache file is fatal and permanent

`initialize_all_artifacts` recovers from exactly one failure mode:

```python
# Life_Cycle_Assessment_Plugin.py:192-199
try:
    self.load_all_from_disk_to_ram(paths)
except FileNotFoundError:
    self.compute_all_artifacts_from_scratch()
    self.save_all_to_disk(paths)
```

Anything other than a missing file propagates. Reproduced by truncating cache files to half
their length (simulating an interrupted copy, a full disk, or a killed process):

```
half-copied matrix_C.npz (interrupted shutil.copy2)  -> BadZipFile: File is not a zip file
truncated basis_component.npz                        -> BadZipFile: File is not a zip file
```

The run dies, and it dies the same way on every subsequent run, with an error that points at
zip internals rather than at "delete `Initial_Artifacts`".

Two things make this reachable rather than theoretical:

1. `atomic_savez` (`lca_utils.py:130`) is genuinely atomic — temp file then `os.replace` —
   but the B and C artifacts do not go through it:

   ```python
   # Life_Cycle_Assessment_Plugin.py:302-305
   shutil.copy2(mat_b, str(paths['matrix_B']))
   shutil.copy2(mat_c, str(paths['matrix_C']))
   ```

   `shutil.copy2` writes in place. A concurrent reader — or an interrupted writer — observes a
   partial file, and B is typically the largest artifact (1.9 MB of 2.9 MB in the measured
   case; tens of MB for ecoinvent), so the window is the widest of all six.

2. The plugin docstring explicitly anticipates concurrent writers: *"Not shared across
   multiprocessing workers; disk caching covers cross-process reuse"*, and `save_all_to_disk`'s
   own docstring describes "multiple processes attempt to write the same cache file
   simultaneously" as an expected condition. Multiprocessing in `Monte_Carlo_Analysis` is
   currently commented out (`Monte_Carlo_Analysis.py:342-348`), so the window is narrow
   *today* — but the moment it is re-enabled, or two jobs share an export on a network drive,
   this is live.

**Fix.** Catch the realistic load failures (`OSError`, `zipfile.BadZipFile`, `ValueError`,
`EOFError`, `KeyError`) and fall through to recompute — a corrupt cache should self-heal, not
brick the folder. Route the B/C copies through `atomic_savez`-style temp-then-`os.replace`
(or drop them entirely per P3, which removes the problem).

### H2 — `get_cache_paths` memoises a `mkdir`, and only `PermissionError` is caught

```python
# lca_utils.py:258
@lru_cache(maxsize=None)
def get_cache_paths(matrix_folder: str) -> dict:
    cache_dir = Path(matrix_folder) / 'Initial_Artifacts'
    cache_dir.mkdir(parents=True, exist_ok=True)
```

Memoising a function whose value depends on a filesystem side effect means the directory is
created **at most once per process**. If it is removed afterwards, the memo hands back paths
into a directory that no longer exists:

```
1st call created          : True
2nd call re-created dir   : False (memoized, so no)
save raised               : FileNotFoundError: .../Initial_Artifacts/base_scaling_vector.npz.2518.tmp.npz
save_all_to_disk catches  : PermissionError only -> this propagates and aborts the run
```

Again the test suite knows: every `shutil.rmtree` of a cache dir in the tests is paired with a
`get_cache_paths.cache_clear()`. Production code has no such pairing.

Separately, `save_all_to_disk` (line 294–307) narrows its guard to `PermissionError` alone.
Its docstring says cache-write failure is "a non-critical failure … Log the error and
continue" — but it neither logs nor continues for `OSError` (disk full, read-only mount,
network drive hiccup), which is the more common real-world case and which will abort a
long Monte Carlo run at the point of writing a cache it did not need.

**Fix.** Drop `lru_cache` from `get_cache_paths` (it is a handful of `os.path` joins — the
memo buys nothing) or split the pure path construction from the `mkdir`. Widen the guard to
`OSError` and actually emit a warning rather than `pass`.

### H3 — `_load_tech_index` collapses multi-output processes

```python
# lca_utils.py:62
return {row[1]: (int(row[0]), row[8]) for row in _csv_rows(path)}
```

`row[1]` is `provider ID` — the **process** UUID. In an openLCA matrix export `index_A.csv`
has one row per *(process, product flow)* pair, so a multi-functional process (any process
with co-products, and any process modelled with a by-product) appears on several rows with
the same provider ID and different flow IDs. The dict silently keeps only the last.

Reproduced on the 3-layer toy export by giving row 1 the same provider ID as row 0 — i.e.
turning them into one two-product process:

```
rows in index_A.csv  : 10
entries after dict   : 9   <-- row collapsed, index 0 lost to 1
_load_tech_index     : {'927ba7de-...': (1, 'Item(s)'), ...}
```

Note what happened: the functional-flow entry did not just disappear, it was **remapped** —
UUID `927ba7de` (index 0, `kg`) now points at index 1 with unit `Item(s)`. Downstream this
either produces a spurious unit/dimension error or, if the units coincide, a wrong basis and
wrong results.

The same pattern is in the legacy `LCA_lib.TechEntry.dict_of` (`LCA_lib.py:57-63`), so it is
a consistent modelling assumption rather than a typo: the code assumes one product per
process. That assumption is fine for a foreground model the user builds themselves; it is not
fine as an unchecked assumption about an arbitrary openLCA export.

**Fix.** Key on the *flow* ID (`row[5]`) or on the `(provider ID, flow ID)` pair, matching how
openLCA identifies a technosphere column. If keying on provider ID is a deliberate constraint,
detect duplicates at load time and raise an error that names the offending process, rather
than silently dropping a column.

### H4 — most real LCIA methods crash on an unmapped impact unit

```python
# Life_Cycle_Assessment_Plugin.py:467
unit_map = CONFIG[i['impact_unit']]
```

`Plugins/Life_Cycle_Assessment_Plugin/config.py` hard-codes 21 unit strings. Anything else is
an unhandled `KeyError`:

```
KeyError: KeyError('kg 1,4-DCB')
```

`kg 1,4-DCB` is the standard ReCiPe / USEtox toxicity unit. Also absent: `kg NOx-Eq`,
`m2*a crop-Eq`, `species.yr`, `USD2013`, `kg Cu-Eq`, `kg PM2.5-Eq`, `m3`, `ha*a` and most of
the rest of ReCiPe, IMPACT World+ and TRACI. The bundled list covers a subset of EF 3.x plus
CED, which is roughly "the methods used in the toy tests".

Two problems compound:

* The failure is a bare `KeyError` at the very end of the run, after the expensive
  factorisation and every plugin has executed. There is no message saying what to do.
* It is all-or-nothing: **one** unmapped category kills the whole result set, including the
  eighteen categories that *are* mapped.

The exact-string matching is also brittle in a way the config itself shows: both
`'kg CO2-Eq'` and `'kg CO2-eq'` are listed, i.e. the case variants were discovered the hard
way. openLCA exports also emit trailing newlines inside quoted unit fields (visible in the
bundled `index_C.csv`); `_load_impact_index` strips them, so that one is already handled —
but the legacy `LCA_lib.ImpactEntry._from_csv` does not.

**Fix.** Make the lookup total: fall back to treating an unknown impact unit as an opaque
dimensionless label (keep the raw string for display, skip unit math) and emit one warning
listing the unmapped categories, so a single exotic category does not destroy the run. If
strictness is wanted, raise once at the end with the full list of unmapped units and the file
to add them to — not a bare `KeyError` on the first one.

---

## 6. Medium-severity findings

### M1 — demand-vector entries other than `f[0]` silently survive

```python
# Life_Cycle_Assessment_Plugin.py:249-250
f_vector = np.asarray(f, dtype=float).reshape(-1).copy()
f_vector[0] = 1.0
```

Only element 0 is overwritten. The docstring (and `perform_lca`'s) claim the result is
"inherently expressed per 1 unit of the functional flow … without needing a separate
normalization step". That holds only if `f` is a multiple of `e₀` — an assumption about the
export that is never stated and never checked. Any other nonzero entry has its burdens quietly
added to the "per 1 kg" figure:

```
as exported (f = e0)          : {'Global warming potential': 10.0}
f[5] = 3.0 added to the export: {'Global warming potential': 16.0}   <-- still labelled "per 1 kg"
```

**Fix.** Build the demand vector rather than patching it: `f_vector = np.zeros(n); f_vector[0] = 1.0`.
If the exported `f` having other nonzeros should be an error, check for it explicitly and say
so. Either way the current half-measure is the one option that is wrong.

### M2 — negative component values are silently made positive

```python
# Life_Cycle_Assessment_Plugin.py:377
self.component_values[i] = np.sign(A0_values[i]) * abs(converted_value)
```

```
all Values = +1.0 : {'Global warming potential': 10.0}
all Values = -1.0 : {'Global warming potential': 10.0}   <-- identical
```

Inheriting the sign from the export is a documented and defensible decision
(`doc/lca_guide.rst`: *"Users always supply positive magnitudes. pyH2A inherits the sign from
the original matrix"*). The problem is `abs()` rather than the sign inheritance: most LCA
component values come from **plugin outputs via path references**, not from literals. A sign
error upstream — a mass computed as a difference, a yield that goes negative at the edge of a
Monte Carlo range — is exactly the bug a user needs to see, and `abs()` is the one operation
guaranteed to hide it.

**Fix.** Keep the sign inheritance; reject a negative resolved value with an error naming the
component and its source path. If avoided-burden / credit modelling is ever wanted, that needs
an explicit opt-in, not a silent `abs()`.

### M3 — the Sherman–Morrison singularity guard is absolute, and fires far too late

```python
# Life_Cycle_Assessment_Plugin.py:82, 429-434
_SM_TOL = 1e-12
...
denominator = 1.0 + correction[0]
if abs(denominator) <= self._SM_TOL:
    raise ZeroDivisionError(...)
```

Measured degradation as the reference-output entry is driven towards zero (n = 1,200
synthetic; errors relative to a direct solve of the updated system):

| `1 + z[0]` | max relative error | plugin behaviour |
|---|---|---|
| 1.0 × 10⁻² | 8.5 × 10⁻¹⁶ | accepted |
| 1.0 × 10⁻⁴ | 1.1 × 10⁻¹³ | accepted |
| 1.0 × 10⁻⁶ | 2.9 × 10⁻¹¹ | accepted |
| 1.0 × 10⁻⁸ | 5.0 × 10⁻⁹ | accepted |
| 1.0 × 10⁻¹⁰ | 8.3 × 10⁻⁸ | accepted |
| 1.0 × 10⁻¹² | **2.2 × 10⁻⁵** | accepted (right at the tolerance) |
| 1.0 × 10⁻¹³ | **3.1 × 10⁻⁴** | raises |

There are roughly seven orders of magnitude between "machine precision" and "raises", and the
guard only trips after the answer is already wrong in the fifth significant figure. Worse,
`abs(denominator) <= 1e-12` is an *absolute* test on a quantity whose scale is set by the
model — it says nothing about cancellation. The measurements in §2 also show `1 + z[0]`
changing sign between a ×100 and a ×10,000 scenario, i.e. a Monte Carlo sweep can pass
*through* the singular point; a sample landing near the crossing gets a badly wrong result
and no complaint.

**Fix.** Use a relative criterion — compare `|1 + z[0]|` against `|z[0]|` (or against the
norm of the correction), which is the actual cancellation measure — and act at a much looser
threshold (~1e-8) by falling back to a direct solve rather than raising. The factorisation
is already cached, so a fallback solve costs one triangular solve, not a re-factorisation; the
"fallback direct solve is disabled" note in the error message reads like a deliberate
simplification that is now cheap to undo. A near-singular denominator means the *scenario's*
technosphere matrix is near-singular, which is worth surfacing as a warning naming the
offending component, not as a bare `ZeroDivisionError`.

### M4 — `A0_column[0]` is assumed to be technosphere index 0

`perform_lca` reads the result's denominator unit from `A0_column[2][0]`, and
`apply_component_updates` cross-checks the Functional Unit against `A0_uuids[0]`. The
docstring justifies this as *"always first in `A0_column` since it is the lowest possible row
index"* — but `tech_process_indices` (`lca_utils.py:200-205`) builds its rows by iterating
`_load_tech_index(...).items()`, i.e. in **`index_A.csv` file order**, which it never sorts or
checks.

The Sherman–Morrison math itself is order-invariant (verified: reversing `index_A.csv` left
the impact result unchanged). What is *not* invariant is which row is treated as the
functional flow. Moving the `Item(s)`-unit Circuit Board row to the top of `index_A.csv`:

```
index_A.csv in ascending index order : {'Global warming potential': (10.0, 'kg / kg')}
Circuit Board row listed first       : ValueError: Functional Unit mismatch: the input file
                                       declares Functional Unit 'kg' (dimension 'mass'), ...
```

openLCA does write ascending order today, so this is latent rather than live. But it is an
undefended dependency on another tool's output format, and when it breaks the symptom
(a Functional Unit error) points nowhere near the cause. If the units happen to coincide there
is no error at all — just a mislabelled denominator.

**Fix.** Sort by index in `tech_process_indices`, or select the row with `index == 0`
explicitly, and assert that it exists.

### M5 — the Functional Unit cross-check is weaker than its own error message claims

```python
# Life_Cycle_Assessment_Plugin.py:390
if functional_flow_quantity.dimension != dcf.functional_unit.dimension:
```

The error text motivates the check as preventing *"Cost results (per {fu}) and LCA results
(per {ff}) … silently expressed on two different physical bases"*. A dimension comparison does
not deliver that. `kg` and `ton` are both `mass`, so the check passes while the two results
differ by 1,000×.

To be precise about what is and is not broken here: the LCA result is internally consistent —
`perform_lca` labels the denominator with the export's own flow unit (`A0_column[2][0]`), so a
consumer that converts through `Quantity.unit[...]` gets the right number. The hazard is a
consumer that reads `.supplied_value` and pairs it with a cost per functional unit — which is
exactly what `doc/lca_guide.rst`'s own "Access LCA results" example does:

```python
gwp100 = result.base_case.inp[...]['Value'][gwp100_key].supplied_value
```

**Fix.** Either convert the result to `dcf.functional_unit.unit` before storing it (so
"per functional unit" is true by construction), or tighten the check to require the same unit,
not merely the same dimension. The first is better — it makes the coupling real rather than
merely validated.

### M6 — openLCA flow-unit handling is an ad-hoc, duplicated string hack

```python
# Life_Cycle_Assessment_Plugin.py:375 and again at 463
target_unit = str(A0_units[i]).replace('(s)', '')
```

The same one-liner, with the same explanatory comment, appears in two methods. It handles
exactly one openLCA pluralisation (`Item(s)` → `Item`, which the unit config happens to define)
and nothing else. openLCA also emits `p`, `Unit(s)`, `m2*a`, `m3*a`, `kg*km`, `t*km`,
`MJ, net calorific value` and similar — none of which parse, and each of which will surface as
`ValueError: Unknown unit encountered during parsing`.

Note the asymmetry: *impact* units get a dedicated mapping table (`config.py` `CONFIG`), but
*flow* units get a `str.replace`. The flow-unit side is the one that feeds the actual unit
conversion of every component value, so it is the side that deserves the table.

**Fix.** Add an openLCA-flow-unit alias map next to `CONFIG` and a single
`_normalise_openlca_unit()` helper used by both call sites.

### M7 — the `reference` labels in `CONFIG` are dead, so distinct impacts share a unit string

`CONFIG` carries a `reference` field for every entry (`"['CO2-Eq']"`, `"['SO2-Eq']"`, …) but
`perform_lca` only ever reads `unit_map['unit']`. Consequences:

* GWP (`kg CO2-Eq`) and Acidification (`kg SO2-Eq`) both come back as `Quantity(..., 'kg / kg')`.
  The `Quantity` class has a reference-label mechanism designed precisely to stop two
  incommensurable `kg` quantities being mixed, and the LCA plugin is the clearest use case for
  it in the codebase — and does not use it.
* The stored values are *strings containing a Python list literal* (`"['CO2-Eq']"`), not lists.
  That shape is only meaningful if something `eval`s them, and nothing does. It reads like a
  generated artefact that was never wired up.

**Fix.** Pass the reference through: `Quantity(h, f"{unit} / {fu_unit}", reference=[...])`, and
store the field as a real list. Low risk, and it makes the result units self-describing.

---

## 7. Error messages that point at the wrong thing

Not bugs, but each one costs a user an hour:

* **Duplicate UUID across tables** → `"Expected 4 LCA components (one per nonzero column-0
  entry), but got 5."` The real problem is that one UUID is declared twice; the message
  suggests deleting a row, which is the right action for the wrong reason. Detect the
  duplicate explicitly and name it.
* **Unmapped impact unit** → bare `KeyError('kg 1,4-DCB')` (H4).
* **Corrupt cache** → `BadZipFile: File is not a zip file`, with no mention of
  `Initial_Artifacts` (H1).
* **Reordered `index_A.csv`** → a Functional Unit mismatch error about units the user never
  wrote (M4).
* **`load_matrices_from_folder`** prints a bare `"Loading matrices from folder:"` with the
  folder name missing (`lca_utils.py:238`) — a stray debug print that is both useless and
  unconditional. It should name the folder or be removed (a `print` in library code on the
  cold path is itself questionable).

---

## 8. Performance

### P1 — precompute `C @ B`: 500–1600× on the per-sample LCIA step

This is the single largest available win, and it is a pure cache-layer change.

`perform_lca` currently does, per Monte Carlo sample:

```python
# Life_Cycle_Assessment_Plugin.py:458-459
g = _cache['matrix_B'] @ self.scaling_vector     # O(nnz(B))
h = _cache['matrix_C'] @ g                       # O(nnz(C))
```

But `h` is an affine function of the small vector `δ` (the k-element change in column 0).
Writing `y` for the base scaling vector, `P` for `basis_component` and `CB = C @ B`:

```
x  = y − (Pδ)·( y[0] / (1 + (Pδ)[0]) )
h  = CB·x
   = CB·y − (CB·P)·δ · ( y[0] / (1 + P[0,:]·δ) )
```

So `CB·y` (length p), `CB·P` (p × k) and `P[0,:]` (length k) can all be computed **once**, at
cache-build time, and every sample becomes a p × k matrix-vector product — independent of
n, of nnz(B) and of nnz(C).

Measured (identical results to 1.7 × 10⁻¹⁵ relative):

| n | m | nnz(B) | impacts | k | current / sample | proposed / sample | speed-up | one-off `C@B` |
|---|---|---|---|---|---|---|---|---|
| 8,000 | 2,500 | 200,000 | 18 | 12 | 0.226 ms | 2.2 µs | **102×** | 7.7 ms |
| 20,000 | 2,500 | 1,500,000 | 18 | 12 | 1.359 ms | 2.3 µs | **593×** | 30.6 ms |
| 20,000 | 2,500 | 1,500,000 | 18 | 40 | 1.465 ms | 2.7 µs | **535×** | 31.9 ms |
| 20,000 | 4,000 | 4,000,000 | 25 | 12 | 3.638 ms | 2.3 µs | **1607×** | 78.0 ms |

At ecoinvent scale the LCIA step stops being measurable. For a 50,000-sample Monte Carlo (the
sample count in `doc/lca_guide.rst`'s own example) the last row is ~3 minutes of pure LCIA
arithmetic today versus ~0.1 s.

Two further benefits fall out:

* `matrix_B` and `matrix_C` no longer need to be cached or copied at all — only `CB·y`,
  `CB·P` and `P[0,:]` do. That deletes P3 below, deletes the largest and riskiest disk
  artifacts (H1), and shrinks the cache from megabytes to kilobytes (`CB·P` was 1,728 bytes in
  the measured case).
* Cold-start RAM drops correspondingly: `basis_component` (n × k dense) is still needed for
  nothing but `P[0,:]` and `CB·P`, so it need not be retained in RAM after the cache is built.

The one caveat: `C @ B` is dense at p × n (1.15 MB for p = 18, n = 8,000; ~3 MB at ecoinvent
scale), which is fine, and it is only needed transiently to form the p × k product.

### P2 — `factorize()` does not do what its docstring says on the fast path

```python
# lca_utils.py:168-170
if scipy.sparse.issparse(matrix):
    if pypardiso is not None:
        return lambda rhs: pypardiso.spsolve(matrix, numpy.asarray(rhs))
```

The docstring promises *"Performs the (potentially expensive) factorization once and returns a
callable `solver(rhs)` that reuses the stored factors"*. The pypardiso branch returns a closure
over the matrix; no factorisation has happened, and every call re-enters pypardiso's
module-level global solver. Measured on the n = 8,000 synthetic export:

| backend | `factorize()` | 1st solve | 12-RHS solve | repeat 1-RHS solve |
|---|---|---|---|---|
| scipy `splu` (SuperLU) | **50,443 ms** | 95 ms | 387 ms | 63 ms |
| pypardiso (Intel MKL) | **24 ms** | **4,205 ms** | 109 ms | 44 ms |

Two conclusions:

1. **The docstring is wrong for the default fast path on Linux and Windows** — all the cost is
   deferred into the first solve. Since only two solves happen per cold start this is currently
   harmless, but it will mislead the next person who assumes the returned callable is cheap.
   It also means the returned "solver" is not safe to hold across a matrix change: pypardiso's
   global solver refactorises whenever it sees a different matrix (measured: alternating
   between two matrices cost 2.2× per solve versus staying on one).
2. **The `performance` extra matters a great deal and is not being exercised.** Total cold
   start: 50.9 s with SuperLU versus 4.3 s with pypardiso — ~12× on this matrix. Yet
   `pypardiso` sits behind an optional extra, and coverage confirms
   `lca_utils.py` lines 170 and 173-174 (the pypardiso and scikit-umfpack branches) are
   **never executed by the test suite**. The one code path most users on Linux and Windows will
   actually run is the one with zero test coverage.

   *(The synthetic matrix has random sparsity and therefore pathological LU fill-in; real LCI
   matrices are far better structured and both backends will be much faster. The ordering of
   the backends, and the fact that the fast one is untested, are the transferable results.)*

   Note also the macOS asymmetry in `pyproject.toml`: `scikit-umfpack` requires a working
   SuiteSparse install and commonly fails to build, so Mac users likely fall back to SuperLU
   without noticing.

**Fix.** Correct the docstring. Consider using `pypardiso.PyPardisoSolver` directly with
`factorize=True` semantics instead of the global `spsolve` alias, so the returned callable
really is a factor handle and is not shared global state. Install the `performance` extra in
CI so both branches are covered.

### P3 — B and C are duplicated into the cache for no benefit

`save_all_to_disk` copies `B` and `C` into `Initial_Artifacts/` and
`load_all_from_disk_to_ram` reads them back from there — byte-identical files, in the same
directory tree, under a different name. Measured on the n = 8,000 export:

```
source export files total :    4,044,554 bytes
  Initial_Artifacts/matrix_B.npz                1,926,757 bytes
  Initial_Artifacts/matrix_C.npz                  124,286 bytes
  ... (the four real artifacts)                   835,141 bytes
artifact total            :    2,886,184 bytes
```

The copies are **71 %** of the cache footprint and buy nothing: they are not a snapshot
(nothing detects that the originals changed — see C2), and the non-atomic copy is the main
corruption vector (H1). For an ecoinvent-scale export this is tens of MB duplicated per
matrix folder.

**Fix.** Load B and C from their original paths (`find_matrix_path` already resolves them), or
— better — delete the need for them entirely by adopting P1.

*(Compression is not worth pursuing: `savez_compressed` on `basis_component` saved 4 % —
768 KB → 734 KB — because the data are dense doubles.)*

### P4 — what remains on the warm path once P1 lands

Measured per-sample breakdown on the n = 8,000 export, warm RAM cache:

```
full plugin run (per sample)                     :   0.570 ms
  input_resolver_function                        :   0.110 ms
  initialize_all_artifacts (cache-hit guard)     :   0.0004 ms
  apply_component_updates                        :   0.048 ms
  build_scaling_vector (Sherman-Morrison)        :   0.020 ms
  perform_lca (B@x, C@g, Quantity construction)  :   0.201 ms
    of which  B @ scaling_vector                 :   0.182 ms
```

With P1 the `perform_lca` line drops to ~0.02 ms and the profile becomes dominated by
`input_resolver_function` (shared plugin infrastructure, not LCA-specific) and by `Quantity`
object churn. Two cheap follow-ups, only worth doing *after* P1:

* `apply_component_updates` builds a fresh `Quantity` per component per sample and then does a
  `UnitDictionary.__missing__` lookup to convert into the flow unit. Since the target flow unit
  is fixed by the export, the conversion factor per UUID can be resolved once at cache-build
  time and each sample reduced to a float multiply. (`parse_composite_unit` is already
  `lru_cache`d, so this is a modest win — worth doing when touching the code, not on its own.)
* `perform_lca` constructs p `Quantity` objects per sample. The unit strings are identical
  across samples, so only the values change.

Also, for the cold path: `compute_all_artifacts_from_scratch` solves all k basis columns in a
single call (`solver(eye_subset)`), which is measurably better than looping — 387 ms versus
804 ms for k = 12 on the n = 8,000 export. That is already the right choice; noting it so it
does not get "simplified" into a loop later.

---

## 9. Test and CI gaps

Statement coverage of the LCA code is high, which is misleading:

```
Life_Cycle_Assessment_Plugin.py     113      7    94%   306-307, 354, 364, 379, 391, 431
lca_utils.py                         88      4    95%   170, 173-174, 254
```

The uncovered lines are **every single error path**:

| line | uncovered path |
|---|---|
| 306-307 | `except PermissionError: pass` in `save_all_to_disk` |
| 354 | "No LCA component tables found in input" |
| 364 | "Expected N LCA components … but got M" |
| 379 | "UUID … is missing from the input LCA component tables" |
| 391 | "Functional Unit mismatch" |
| 431 | `ZeroDivisionError` — Sherman-Morrison denominator |
| lca_utils 170, 173-174 | the pypardiso and scikit-umfpack solver backends |
| lca_utils 254 | "could not be loaded from the specified folder" |

Beyond the raise paths, three structural gaps:

1. **No test asserts that two matrix folders in one process give the right answers.** The
   tests explicitly clear the cache to avoid the situation (C1). A regression test that
   *doesn't* clear — and asserts correct results — is the test that would have caught C1 and
   would guard the fix.
2. **No test covers a changed export in a warm cache folder** (C2), a corrupt artifact (H1),
   or a missing `Initial_Artifacts` directory with a warm `get_cache_paths` memo (H2).
3. **The fast solver backend is untested** (P2). CI installs the base dependencies only, so
   the branch most users run never executes under test. Adding the `performance` extra to the
   CI matrix is a one-line change.

Minor test-data observation: of the 21 folders in
`src/tests/e2e_lca/data/matrix_folders/`, only the 9 `*_base` folders are ever loaded. The
12 `smartphone_3layer_*_s2..s5` folders are referenced by nothing — the S2–S5 scenario input
files inherit `Matrix Folder` from their base file. They should be removed or wired up.

Housekeeping: `Initial_Artifacts/` is **not in `.gitignore`**. The test module cleans up after
a full pass, but an interrupted run — or a user pointing `Matrix Folder` at an in-repo
export — leaves untracked binary artifacts that can be committed, and given C2 a committed
stale cache would poison every checkout.

---

## 10. Documentation vs. code

`doc/lca_guide.rst` is good and thorough, which makes the divergences more dangerous than
absent docs would be.

| doc claim | reality |
|---|---|
| "LCA is fully compatible with Monte Carlo sampling … the impact results are collected in a CSV file", with a worked `Dependent Variable \| Climate change` example | **Not implemented.** `Monte_Carlo_Analysis.perform_h2_cost_calculation` hard-codes `dcf.h2_cost` (`Monte_Carlo_Analysis.py:317`). Grepping the whole package, no code reads a `Dependent Variable` key from the `# Monte_Carlo_Analysis` table. The documented workflow will silently produce an H2-cost CSV, not impacts. |
| "subsequent runs (including every Monte Carlo worker) …", "Multiprocessing workers each build their own RAM cache from disk" | Multiprocessing is commented out (`Monte_Carlo_Analysis.py:342-348`); Monte Carlo currently runs single-process. |
| Example output `Climate change …: 0.454132 kg CO2-Eq` from `entry.supplied_unit` | `supplied_unit` is the composite `'kg / kg'`, never `'kg CO2-Eq'` (see M7). |
| `examples/LCA_example/PVE.md`, `examples/LCA_example/LCA_Test_PVE_EF`, `examples/LCA_example/Monte_Carlo_Output.csv` | No `LCA_example` directory exists anywhere in the repo. The only LCA data shipped is `data/LCA/LCA_Test_Data`, which is used solely by the dead `LCA.py` demo (§11). |
| "LCA is an optional feature: adding a `# Life Cycle Assessment` section to the input file activates it." | Activation is by which defaults file is merged (`Defaults_LCA.md` / `Defaults_TEA_LCA.md` include the plugin in `# Workflow`; `Defaults_TEA.md` omits it) — as the plugin's own docstring correctly states. With an LCA defaults file merged, omitting the section is an error (`Matrix Folder` is `optional: False`), not a deactivation. |
| "The `(n, 4)` multiply replaces an `(n³)` factorisation" | Sparse LU is not O(n³); its cost is governed by fill-in under the chosen ordering. The qualitative point stands, the complexity claim does not. |
| "**Delete the `Initial_Artifacts` folder whenever you export the new matrices**" | Correct, and the reason C2 is a bug rather than a design: correctness should not depend on the user reading this sentence. |

---

## 11. Dead code and dependency housekeeping

**`src/pyH2A/LCA/` is dead, and actively misleading.** Nothing imports `pyH2A.LCA.LCA` or
`pyH2A.LCA.LCA_lib` except `LCA.py` importing `LCA_lib` (verified by grep across the whole
repo); coverage reports the package as *"never imported"*. It is a superseded first
implementation that is still importable as `pyH2A.LCA.LCA`, and it computes a **different and
incorrect** model:

* `LCA.build_scaling_vector` populates the scaling vector directly from the input tables and
  `perform_LCA` then does `g = B @ scaling_vector` — it **never solves `A x = f`**. That treats
  user-supplied exchange amounts as final activity levels, which is only valid if every
  background process is also supplied by hand. The `np.any(self.scaling_vector == 0)` guard
  makes that explicit: it demands the user enumerate *every* technosphere process, which is
  impossible for any real background database.
* `LCA.import_folder` returns `None` when the export has no impacts and the caller then
  dereferences it (`AttributeError`).
* `process_LCA_table` carries a hard-coded four-entry unit table (`ton`/`kg`/`kWh`/`MJ`) that
  predates the `Quantity` unit handler.
* `ImpactEntry._from_csv` does not strip the trailing newline openLCA writes into quoted unit
  fields — `lca_utils._load_impact_index` does.
* `perform_LCA` prints every impact to stdout unconditionally.
* Module-level `from pyH2A import Discounted_Cash_Flow` creates an import-cycle risk for a
  type annotation that resolves to a module, not a class.

Someone comparing the two implementations, or importing the obvious-looking `pyH2A.LCA.LCA`,
will get wrong numbers. **Recommendation: delete `src/pyH2A/LCA/` outright** (it is in version
control if needed), or if the openLCA-derived `LCA_lib.py` reader is wanted as reference,
strip it to the MPL-licensed reader and delete `LCA.py`.

**Unused hard dependencies.** `pyproject.toml` declares `numba>=0.60.0` and `pint>=0.24.4` as
required. Neither is imported anywhere in `src/` — `pint` is precisely what
`Utilities/Unit_Handler/quantity.py` was written to replace ("Lightweight computational
replacement for Pint in pyH2A"). `numba` in particular is a heavy dependency that constrains
the NumPy version range for every installation. Both should be dropped unless there is a
near-term plan for them.

**Minor.** `np.load(..., allow_pickle=True)` on `impact_index.npz`
(`Life_Cycle_Assessment_Plugin.py:223`) deserialises pickled objects from a file inside a
possibly shared or network-mounted export folder. The payload is three parallel lists of
`int`/`str`, so storing them as three plain arrays would remove `allow_pickle` entirely — a
free hardening.

The `NpzFile` objects returned by `np.load` in `load_all_from_disk_to_ram` are never closed.
This was checked and does **not** leak descriptors under CPython (refcounting closes them
promptly, and no `ResourceWarning` is emitted) — noted only because a context manager would be
tidier, not as a defect.

---

## 12. Recommended order of work

**Before this branch merges**

1. **C1** — key `_cache` by the resolved matrix folder. Add the regression test that runs two
   folders in one process *without* clearing, and drop the clearing workarounds from the
   existing tests once it passes.
2. **C2** — fingerprint the source export (sizes + mtimes, or hashes of the index CSVs plus
   matrix shapes/nnz) and recompute on mismatch. Add a format version to the artifacts.
3. **H4** — make the impact-unit lookup total so one exotic category cannot kill a run; report
   unmapped units once, clearly.
4. **H1/H2** — recover from corrupt caches instead of bricking the folder; widen
   `save_all_to_disk`'s guard to `OSError` and warn; un-`lru_cache` the `mkdir`.
5. Add `Initial_Artifacts/` to `.gitignore`.

**Next**

6. **P1** — precompute `C@B`, `(C@B)@basis` and `(C@B)@y`. Largest performance win by an order
   of magnitude, and it simultaneously removes P3 and shrinks H1's blast radius.
7. **H3** — key the technosphere index on the flow (or the process/flow pair), or detect and
   reject duplicate provider IDs.
8. **M1, M2, M4** — three small, self-contained correctness hardenings: build `f` rather than
   patch it; reject negative component values instead of `abs()`-ing them; sort or assert the
   `index_A.csv` ordering.
9. **M3** — relative singularity criterion plus a direct-solve fallback.
10. **P2** — fix the `factorize()` docstring and add the `performance` extra to CI so the fast
    backend is covered.

**Then**

11. **M5, M6, M7** — express results in `dcf.functional_unit.unit`; a real openLCA flow-unit
    alias table; wire up the impact `reference` labels.
12. Reconcile `doc/lca_guide.rst` with the code: either implement the documented Monte Carlo
    `Dependent Variable` support for impacts, or mark that section as planned; fix the
    `supplied_unit` example; ship the referenced `examples/LCA_example/` files or repoint the
    paths; correct the activation and complexity claims.
13. Delete `src/pyH2A/LCA/`; drop `numba` and `pint` from `pyproject.toml`; remove or wire up
    the 12 unused `*_s2..s5` test matrix folders.
