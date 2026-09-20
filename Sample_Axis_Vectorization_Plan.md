# Carrying a Sample Axis Through pyH2A — Implementation Plan and Risk Analysis

Companion to `Quantity_Performance_Report.md`. Same rules: exploration only, no
production code changed, every number measured on commit `a04fb7a` with throw-away
prototypes in the session scratchpad.

**Question:** how would "one DCF pass over arrays of length 100,000" actually work,
and where does it break?

---

## 0. The two findings that reshape the plan

I set out to plan the vectorization and measured two things that change its priority.

**Finding 1 — most of the model does not depend on the Monte Carlo parameters at all.**
I ran each model twice with a perturbed parameter and diffed every numeric leaf. For a
typical cost parameter, **587 of 832,886 array elements change (0.07 %)**. The entire
hourly layer — 26,283 irradiation values, 8,760 PV output values, the electrolyzer's
357,873 hourly elements — is bit-identical between samples. It is being recomputed
100,000 times for nothing.

Exploiting that needs no vectorization at all, and I prototyped it:
**checkpoint the state just before the first affected plugin, then replay only the tail
per sample.** Measured on PV_E with a CAPEX parameter: **17.32 → 2.22 ms/sample, 7.8×,
LCOH bit-identical.**

**Finding 2 — batching the sample axis onto the *large* arrays makes things slower.**
I transcribed the electrolyzer kernel (60 % of PV_E runtime) into a batched
`(S, 20, 8760)` form. It is **2× slower per sample** at S ≥ 8 than the scalar loop:
the kernel is memory-bandwidth bound, and batching pushes the working set out of cache.
Meanwhile the *same* kernel rewritten scalar-but-sane — `np.minimum(eg, demand)` instead
of `np.amin(np.c_[eg, demand], axis=1)` — goes from **11.09 → 0.80 ms (13.9×)** on the
kernel and **1.94× end-to-end on the full DCF** (2.12× with the rest of the loop body
tidied), LCOH bit-identical, for a two-line diff.

So the honest headline is:

> Sample-axis vectorization is the right tool for the **small, year-sized arrays** at the
> cost/DCF end of the model (measured 7–41× there), and the wrong tool for the **large
> hourly arrays** at the physics end (measured 0.5×). The big early wins come from
> *skipping* work (Finding 1) and from *fixing two NumPy calls* (Finding 2), both of
> which are prerequisites that make the vectorization worth doing afterwards.

Stacked and measured, PV_E with a cost parameter:

| configuration | ms/sample | speedup | 100k samples, 1 core | 100k, 4 cores |
|---|---|---|---|---|
| today | 17.32 | 1.0× | 28.9 min | 7.2 min |
| + electrolyzer kernel fix | 8.68 | 2.0× | 14.5 min | 3.6 min |
| + checkpoint/replay (Stage 2) | 2.22 | 7.8× | 3.7 min | 0.9 min |
| both | 2.24 | 7.7× | 3.7 min | 0.9 min |
| + lazy `Quantity` | **2.18** | **7.9×** | **3.6 min** | **0.9 min** |

All five produce a bit-identical LCOH. The electrolyzer fix and the checkpoint do not
stack, because the checkpoint hoists the electrolyzer out of the loop entirely — but the
fix is what carries the deep-parameter studies, where the checkpoint cannot help.
Sample-axis vectorization (Stage 3 below) then attacks the remaining 2.18 ms, where it
should be worth a further 5–20×.

*(Protocol for every timing in this document: separate process per variant, 200 warm-up
runs to get past the allocator transient, then best of five blocks of 25. Numbers taken
without that warm-up are 30–50 % higher and not comparable.)*

---

## 1. What "carrying a sample axis" means mechanically

Today a Monte Carlo sample is a full Python pass:

```python
for value_set in values:                       # 100,000 iterations
    input_dict = copy.deepcopy(self.inp)
    for key, parameter in parameters.items():
        set_by_path(input_dict, parameter['Parameter'], value_set[parameter['Index']])
    dcf = Discounted_Cash_Flow(input_dict, print_info = False)
    h2_cost.append(dcf.h2_cost)
```
*(`Monte_Carlo_Analysis.perform_h2_cost_calculation`)*

Vectorized, a sample becomes an **index into an extra array axis**. `set_by_path` writes
a `(S,)` array instead of a float; every quantity derived from it acquires a leading (or
trailing) axis of length `S`; the model runs once; `product_cost` comes out as `(S,)`.

`Quantity` already supports this — it is unit-agnostic about the value's shape. The unit
layer measured **389× cheaper** this way (482 ms for 100,000 scalar objects vs 1.24 ms for
one 100,000-element object). The work is entirely in the plugins, in three places:
**shape conventions, control flow that branches on values, and the IO type contracts.**

---

## 2. Dependency (taint) analysis — the foundation of the whole plan

Everything below depends on knowing *which* state varies per sample. I measured it
empirically: run the model at two parameter values, walk `dcf.inp` and every
`dcf.plugs[*].__dict__`, and diff each numeric leaf. Anything bit-identical is **static**;
anything that differs is **tainted**.

### 2.1 Measured taint, PV_E (832,886 numeric array elements total)

| varied parameter | tainted leaves | tainted elements | sample axis at 100k | static share of warm runtime |
|---|---|---|---|---|
| PV + Electrolyzer CAPEX (cost only) | 107 / 563 | **587 (0.07 %)** | **0.47 GB** | **94 %** |
| H2 yield per unit energy | 127 / 563 | 1,154 (0.14 %) | 0.92 GB | 34 % |
| Electrolyzer nominal power | — | 746,196 (90 %) | **597 GB** | 1 % |
| STH efficiency (PEC model) | 213 / 563 | ≈ 600 | 0.6 GB | 29 % |

Per-plugin, for the cost-only case (warm timings, mean of 12 runs):

```
plugin                              ms    elements  tainted
Electrolyzer_Plugin              23.233     357873        0   static
Photovoltaic_Plugin               9.418     191391        0   static
Battery_Plugin                    1.253      22012        0   static
Discounted_Cash_Flow_Plugin       0.900        664      388   TAINTED
Replacement_Plugin                0.575        177       45   TAINTED
Capital_Cost_Plugin               0.515        199       33   TAINTED
Other_Fixed_Operating_Cost        0.222        158       26   TAINTED
Hourly_Irradiation_Plugin         0.174      26296        0   static
… 9 more, all static
```

Three regimes, and they need different treatments:

* **Shallow (cost) parameters** — 94 % of the runtime is static. Skip it (Stage 2). The
  remaining work is all year-sized arrays, perfect for vectorization (Stage 3).
* **Mid-depth parameters** (H2 yield) — the Electrolyzer *plugin* is tainted, but only
  **21 of its 357,873 elements** are: the hourly capacity/consumption arrays do not depend
  on the yield, only the summed yearly production does. Sub-plugin granularity recovers
  most of the static work here.
* **Deep parameters** (nominal power) — everything is tainted; 597 GB for a full
  sample axis. Chunking is mandatory and batching the hourly arrays is counterproductive
  (§6). For these, the answer is the algorithmic fixes plus multiprocessing.

### 2.2 How to get the taint set in production

Three options, in increasing order of cost and rigour:

1. **Declarative** — plugins already declare their inputs and outputs (`input_dict` /
   `output_dict` with full paths). Build the plugin-level dependency graph from those
   declarations and mark everything reachable from the MC parameter paths. Cheap, static,
   no extra runs. **Recommended.** Risk: a plugin that reads something it did not declare
   is invisible to the analysis, so the graph must be validated against (2).
2. **Empirical, two-run perturbation** — exactly what I did above (~70 lines). Run the
   model at two parameter values, diff, mark. Use it as a **CI check** that the declared
   graph is not missing an edge.
3. **Full dynamic taint** — wrap values in a tracking type. Accurate, invasive, slow.
   Not worth it here.

Note both (1) and (2) must be re-derived whenever the MC parameter set changes; cache the
result keyed by the sorted tuple of parameter paths.

---

## 3. Stage 2 — checkpoint and replay (no vectorization, measured 7.8×)

This is the highest-value step and it is independent of everything else.

```
run the workflow once
    ...static plugins...
    <-- CHECKPOINT here: the state immediately before the first tainted plugin
    ...tainted tail...

per sample:  restore checkpoint -> set_by_path(parameter) -> run the tail only
```

### 3.1 Two traps I hit building it

**Trap A — plugins are not idempotent.** My first attempt re-ran only the *tainted*
plugins on the fully solved `inp`. It fails:

```
TypeError: 'Direct Capital Cost > Contributions > Value'
  (entry: {'Data': {...}, 'Table Group': ..., 'Total': Quantity(11095392.78, 'USD')}):
  Expected (<class 'int'>, <class 'float'>), but got <class 'dict'>
```

`Capital_Cost_Plugin` writes a `Contributions` dict into a slot it later reads as a
number. Re-running a plugin over its own output is not supported.

**The fix is to checkpoint state, not to re-run selected plugins.** Restore the snapshot
taken *before* the first tainted plugin and run the whole tail from there, including the
static plugins that happen to sit after it. Each plugin then sees exactly the state it
saw in the original run. With that, results are **bit-identical** on both models I tested.

**Trap B — restoring the checkpoint is the new bottleneck.** The snapshot holds the solved
state, including all the hourly arrays:

| | `deepcopy(raw input)` | `deepcopy(solved state)` |
|---|---|---|
| PV_E | 0.105 ms | **9.512 ms (91×)** |
| PEC | 0.130 ms | 2.969 ms (23×) |

At 9.5 ms a restore, more than half the remaining per-sample budget went on copying
state that the tail never touches. The fix is a **structural copy**: rebuild
the nested-dict spine, *share* every leaf (`Quantity`, `ndarray`, `str`) rather than
copying it.

```python
def structural_copy(obj):
    if type(obj) is dict:
        return {k: structural_copy(v) for k, v in obj.items()}
    return obj          # leaves are shared, not copied
```

Measured, PV_E cost-only, results bit-identical in both cases:

| restore strategy | ms/sample | speedup vs full run (17.16 ms) |
|---|---|---|
| `copy.deepcopy` | 4.33 | 4.0× |
| **structural copy** | **2.20** | **7.8×** |

This is safe only under the same invariant the `Quantity` copy-elision needs: **no plugin
may mutate a shared leaf array in place.** Nothing currently does (verified by the
bit-identical results and the full suite), but it must become an enforced rule — see §8.

### 3.2 When Stage 2 does *not* pay

Measured on PEC with STH efficiency: the tail is 9 of 13 steps and hoisting gives **1.2×**
(and 1.0× with a deepcopy restore — i.e. nothing). Stage 2 pays only when
the static prefix is expensive. Gate it on the measured static share, and fall back to the
plain loop when it is below, say, 50 %.

---

## 4. Axis convention — the decision that determines how much breaks

Once values carry a sample axis, every array in the model is one rank higher. Two choices,
and neither is free, because the existing code relies on **both** positional year indexing
and axis-defaulting reductions.

| | **sample axis first** `(S, Y)` | **sample axis last** `(Y, S)` |
|---|---|---|
| `x[-1] = v`, `x[:idx] = v`, `full[start:] = op` | ❌ silently hits samples | ✅ still hits years |
| `np.diff(x)` (defaults to `axis=-1`) | ✅ correct | ❌ diffs across samples |
| `np.cumsum(x)` (no axis → **flattens**) | ❌ | ❌ |
| `values.sum(axis=0)` in `numpy_npv` | ❌ sums samples | ✅ |
| `np.r_[np.zeros(1), x]` | ❌ | ❌ |
| broadcasting a `(S,)` scalar against a `(Y,)` year array | ✅ needs `[:, None]` | ✅ needs `[None, :]` |

**Recommendation: sample axis LAST, year axis last-but-one is not an option — put the
sample axis first, `(S, …, Y)`, and make the year axis always `-1`.** Rationale: with the
year axis last, every reduction written without an explicit axis that *should* be over
years (`np.diff`, `np.trapz`) happens to be right, `np.cumsum` needs `axis=-1` added
anyway, and the positional writes are mechanically rewritable by prefixing `...`:

```python
self.decommissioning_costs[-1]   ->  self.decommissioning_costs[..., -1]
self.annual_sales[:self.start_idx] = 0   ->  self.annual_sales[..., :self.start_idx] = 0
full[start_idx:] = operation_array       ->  full[..., start_idx:] = operation_array
```

The `...` form is **correct in both the scalar and the batched case**, which is the key
property: it lets you convert the code incrementally while every existing test still
passes on 1-D inputs. Adopt it as a blanket rule before any batching is switched on.

### 4.1 What a scan finds

Counting constructs whose meaning changes when a leading axis appears (excluding the
post-processing `Analysis/` modules, which are outside the sample loop):

| pattern | hits | worst offender |
|---|---|---|
| reduction with no explicit `axis=` | 30 | `np.cumsum(after_tax_post_depreciation_cash_flow)` |
| `np.zeros_like` / `np.ones` shape assumptions | 30 | `np.zeros_like(self.analysis_years_ones.unit['-'])` |
| positional `[-1]` / `[0]` writes | 20 | `self.working_capital_reserve[-1] = -np.sum(...)` |
| `int()` / `round()` casts of model values | 16 | `int(round(fin['Plant life'].unit['year']))` |
| `np.r_` / `np.c_` / stacking | 14 | `np.r_[np.zeros(1), self.working_capital_reserve]` |
| `len()` of a value array | 13 | `numpy_npv`: `np.arange(0, len(values))` |
| slice assignment | 10 | `self.annual_sales[:self.start_up_time_idx] *= ...` |
| scalar truth-test on a value | 6 | `if abs(npv_after_tax_post_depreciation) > 1e-6:` |
| `np.outer` | 1 | `MACRS_depreciation` |

By file: `Discounted_Cash_Flow_Plugin.py` 26, `input_modification.py` 14,
`Replacement_Plugin.py` 9, `Electrolyzer_Plugin.py` 8.

**The dangerous ones are the silent ones.** `np.cumsum(x)` on a 2-D array flattens and
returns the wrong shape *and* the wrong numbers; `x[-1] = v` on `(S, Y)` writes a whole
sample's year series. Neither raises. `if abs(...) > 1e-6` at least fails loudly
("truth value of an array is ambiguous"). Plan for a scripted audit, not a code review.

---

## 5. The IO type contracts — the biggest mechanical obstacle

Plugins declare their inputs and outputs with type sets that are then enforced by
`check_type`:

```python
"type": {int, float},
```

Across `Plugins/` and `Utilities/` there are **293 such declarations, and 208 of them
(71 %) accept only scalars** — no `np.ndarray`. The first value that arrives with a sample
axis raises `TypeError` in `input_resolver`/`output_inserter`.

This is not hard, but it is *pervasive*, and widening them all to
`{int, float, np.ndarray}` throws away the type safety they were written for. Better:
introduce a **batch-aware check** that validates the *element* type and lets the container
be scalar or an array of the declared element type:

```python
"type": {int, float}, "batchable": True     # accepts 2.5 and np.ndarray[float64]
```

with `check_type` testing `value.dtype` against the declared element types when the value
is an `ndarray` and `batchable` is set. Roughly 208 declarations to annotate; the check
itself is ~15 lines. Do this as its own mechanical, separately reviewable commit.

### 5.1 Validation semantics also change

`check_bounds` currently does:

```python
if lower_bound is not None and np.any(base_value < lower_bound):
    raise ValueError(...)
```

With a sample axis, **one bad sample aborts the entire batch** — and the error message
prints the whole array. A 100,000-sample run that dies on sample 43,197 because a drawn
value went slightly negative is a bad experience and hides the other 99,999 results.

Required change: in batch mode, bounds violations must produce a **per-sample invalid
mask** that propagates to the output as `NaN`, with a summary at the end
("1,043 of 100,000 samples rejected: Electrolyzer > Minimum capacity below 0"). The
scalar path keeps raising. This is a genuine behavioural change and needs a decision from
you, not just an implementation.

---

## 6. Where batching helps, and where it hurts

This is the part I would have got wrong without measuring.

### 6.1 The large hourly arrays — do NOT batch

The electrolyzer kernel, transcribed faithfully and batched to `(S, 20, 8760)`:

| S | scalar loop | batched | ratio | peak temporaries |
|---|---|---|---|---|
| 1 | 11.05 ms/sample | 3.15 ms/sample | 3.5× | 4.2 MB |
| 8 | 11.03 | 23.03 | **0.5×** | 33.6 MB |
| 32 | 10.95 | 22.99 | **0.5×** | 134.6 MB |
| 128 | 11.00 | 21.64 | **0.5×** | 538.2 MB |

Batched output is numerically identical; it is simply slower. The per-sample arrays are
70 KB and live in L2; the batched ones stream from RAM. There is no Python overhead left
to amortize — 20 iterations of a handful of NumPy calls is already negligible bookkeeping
around real memory traffic.

And the 3.5× at S=1 is not batching at all — it is the algorithmic fix hidden inside the
rewrite. Isolated:

| electrolyzer kernel, one sample | ms |
|---|---|
| current: `np.amin(np.c_[eg, demand], axis=1)`, `demand *= np.ones(len(eg))` | 11.09 |
| `np.minimum(eg, demand)` with a scalar `demand` | **0.80** |

and on the full PV_E discounted cash flow, each measured in its own process:

| variant | ms/run | speedup | LCOH |
|---|---|---|---|
| shipped | 17.96 | 1.00× | reference |
| **minimal two-line diff** (`np.minimum`, drop the `np.ones` broadcast) | **9.26** | **1.94×** | bit-identical |
| + capacity mask via comparison instead of two fancy-index assignments | 8.87 | 2.03× | bit-identical |
| full loop-body tidy | 8.49 | 2.12× | bit-identical |

**13.9× on the kernel, 1.94× on the full DCF from two lines.** `np.c_` builds
an 8760×2 copy per year (20 per run) purely to take an elementwise minimum, and the
`demand *= np.ones(...)` broadcast materializes another 8760-element array that NumPy
would have broadcast for free.

### 6.2 The small year-sized arrays — DO batch

The same experiment on a 22-element year array (the shape everything from
`Capital_Cost_Plugin` through `Discounted_Cash_Flow_Plugin` works on):

| S | scalar loop | batched | ratio |
|---|---|---|---|
| 100 | 4.70 µs/sample | 0.633 µs | 7× |
| 1,000 | 4.24 | 0.209 | 20× |
| 10,000 | 6.87 | 0.167 | **41×** |

Here Python and NumPy call overhead is 95 % of the cost and batching removes essentially
all of it. This is precisely the 2.18 ms/sample that Stage 2 leaves behind.

### 6.3 The rule

> Batch an operation over samples when its per-sample array is small enough that
> per-call overhead dominates (year-sized, ≲ a few hundred elements). Keep the loop when
> the per-sample array already saturates memory bandwidth (hourly-sized, ≳ 10⁴ elements),
> and fix the algorithm instead.

The crossover on this machine is around 10³–10⁴ elements per operation; measure it on
yours before fixing a threshold.

---

## 7. Validated rewrite recipes for the hard kernels

I implemented and checked the three constructs that looked most likely to block the DCF
tail. All three work.

### 7.1 `numpy_npv` — explicit year axis

```python
def numpy_npv(rate, values):                      # year axis is LAST
    disc = (1.0 + np.asarray(rate)) ** np.arange(values.shape[-1])
    return (values / disc).sum(axis=-1)
```

`rate` may be a scalar or `(S, 1)` for a per-sample discount rate. **Bit-exact** against
the current implementation (max abs error 0.0) for both cases over 5,000 samples. The
current version's `len(values)` and `.sum(axis=0)` are the two things that break.

### 7.2 `MACRS_depreciation` — the diagonal loop is a convolution

The current code builds `np.outer(annual_depreciable_capital, macrs_values)` and then
sums each anti-diagonal in a Python loop. That is a convolution of the yearly depreciable
capital with the MACRS schedule, which batches trivially:

```python
def macrs_batched(plant_years, dep_len, cap):     # cap: (..., Y)
    sched = macrs_schedule(dep_len)               # (K,) — unchanged lookup
    n, K = len(plant_years), len(sched)
    T = np.zeros((n, n + K - 1))                  # built once, cached per dep_len
    for k in range(K):
        T[np.arange(n), np.arange(n) + k] = sched[k]
    full = cap @ T                                # (..., n+K-1)
    out = full[..., :n].copy()
    out[..., -1] += full[..., n:].sum(axis=-1)    # fold the tail into the last year
    return out
```

Checked against the current function on 200 random samples: **max absolute error
1.9 × 10⁻⁹ on values of order 10⁶ (≈ 10⁻¹⁵ relative)** — floating-point reassociation, not
a logic difference. Timing for 5,000 samples:

| | ms |
|---|---|
| current Python loop | 905.3 |
| `np.convolve` via `apply_along_axis` | 14.19 (64×) |
| **matrix multiply (above)** | **1.26 (718×)** |

### 7.3 Planned replacement — a ragged stride becomes a dense mask

This is the hardest site in the codebase. `Planned_Replacement.calculate_yearly_cost`
does:

```python
replacement_frequency = int(np.ceil(dictionary['Frequency_Value'].unit['year']))
initial_replacement_year_idx = fn.find_nearest(plant_years_relative, replacement_frequency)[0]
self.years = plant_years_relative[initial_replacement_year_idx:][0::replacement_frequency]
self.years_idx = fn.find_nearest(plant_years_relative, self.years)
...
self.yearly[planned_replacement.years_idx] += planned_replacement.cost.unit['USD']
```

A **per-sample stride** producing a **ragged index set** — different samples get different
numbers of replacement years. There is no array slice for that. But there is a mask:

```python
def replacement_mask(plant_years_relative, freq):        # freq: (S,)
    f = np.ceil(freq).astype(int)
    start = np.searchsorted(plant_years_relative, f, side='left')     # (S,)
    rel = np.arange(len(plant_years_relative))[None, :] - start[:, None]
    return (rel >= 0) & (rel % f[:, None] == 0)                       # (S, Y) bool

yearly += mask * cost[:, None]
```

Verified **identical to the index-scatter version for 500 random frequencies**. The
general recipe: **replace index-scatter with mask-multiply**; it turns ragged per-sample
index sets into one dense boolean array. It costs `S × Y` bools (22 bytes/sample here —
nothing) and is branch-free.

---

## 8. Parameter tiers — not every MC parameter can share one array shape

The repository's own Monte Carlo configurations vary parameters from all three tiers, so
this cannot be waved away.

### Tier A — value-only (broadcasts cleanly)
Costs, rates, efficiencies, fractions. They change magnitudes, not shapes or index
positions. Examples in the shipped configs: `PEC Cells > Cell Cost ($/m2)`,
`Solar Concentrator > Cost ($/m2)`, `Solar-to-Hydrogen Efficiency > STH (%)`,
`Direct Capital Costs - PV > PV CAPEX`, `Electrolyzer > Conversion efficiency`.
**Fully vectorizable.** This is the easy majority.

### Tier B — index-shifting (needs the mask recipe)
Values that end up selecting *positions* in the year grid. Examples actually used:
`PEC Cells > Lifetime (years)` and `Catalyst > Lifetime (years)` in the PEC configs —
both flow into `replacement_frequency`. Also `Start-up time`,
`Depreciation schedule length` (which picks a *column* of the MACRS table via
`find_nearest`).
**Vectorizable with real work**: mask-multiply for strides, `np.take_along_axis` for
per-sample table lookups. `find_nearest` itself is already fine — it wraps
`np.searchsorted`, which is vectorized; only its Python `for` loop and the scalar
`[0]` unwrapping need changing.

### Tier C — shape-changing (cannot share an array)
`Financial Input Values > Plant life`, the construction-time (derived from
`len(self.input_dict_resolved['Construction'])`), anything that changes the length of the
year grid or the hourly series. `Time_Plugin.generate_time` does
`int(round(finance_dict['Plant life']['Value'].unit['year']))` and builds every array from
it.
**Not vectorizable within one batch.** Handle by **grouping samples by shape**: bucket the
draws by their integer plant life, run one batch per bucket, concatenate. With a handful
of distinct lifetimes this is nearly free; with a continuous lifetime distribution it
degenerates and you should fall back to the loop plus multiprocessing.

**Action:** the MC parameter table should declare each parameter's tier (or the framework
should infer it), and the runner should pick the strategy per study rather than assuming
everything is Tier A.

---

## 9. Memory budget and chunking

Chunking is not optional. Peak memory is roughly

```
bytes ≈ S × (tainted elements per sample) × 8 × k       k ≈ 3 for NumPy temporaries
```

Measured tainted-element counts per sample for PV_E, and what they imply:

| varied parameter | tainted elements | per sample | S = 100,000 | S = 1,000 | S = 250 |
|---|---|---|---|---|---|
| CAPEX (cost only) | 587 | 4.7 kB | 1.4 GB | 14 MB | 3.5 MB |
| H2 yield | 1,154 | 9.2 kB | 2.8 GB | 28 MB | 7 MB |
| Nominal power | 746,196 | 6.0 MB | **1.8 TB** | 18 GB | 4.5 GB |

So: Tier-A cost studies could in principle run **unchunked** at 100,000 samples
(≈1.4 GB with temporaries). Deep-parameter studies need `S` in the low hundreds — at
which point §6.1 says batching the hourly arrays is a loss anyway, and the right answer is
the scalar loop across processes.

**Design the runner to chunk from day one**, with the chunk size chosen from a memory
budget and the measured per-sample footprint:

```python
S_chunk = clamp(int(budget_bytes / (tainted_elements * 8 * 3)), 1, n_samples)
```

Chunking also bounds the blast radius of a bad batch and gives natural progress reporting
and checkpointing for long runs — worth having regardless of memory.

---

## 10. Staged plan

Each stage is independently shippable, independently testable, and gated on a measurement.

### Stage 0 — safety net (prerequisite, ~1 day)
* Freeze reference results: for each e2e model, store LCOH **and** every plugin's
  numeric state (the `walk()` snapshot from the taint tooling) as a golden file.
* Add the perturbation-based taint tool as a CI-runnable script.
* Add a test asserting no plugin mutates a shared array in place (set
  `arr.setflags(write=False)` on values handed out during a test run).
* **Gate:** golden files reproduce bit-identically on the current code.

### Stage 1 — algorithmic fixes (~1 day, measured 1.94–2.12× on PV_E)
* `Electrolyzer_Plugin.calculate_H2_production`: `np.minimum` instead of
  `np.amin(np.c_[...])`; drop the `*= np.ones(len(...))` broadcast.
* Same audit for the other `np.c_` / `np.r_` sites (14 total).
* Short-circuit `check_bounds` for scalars (≈500 `np.any`/`np.all` reductions per run).
* **Gate:** LCOH bit-identical on all e2e models; measure the speedup.

### Stage 2 — checkpoint and replay (~1 week, measured 7.8× on PV_E cost-only)
* Plugin-level dependency graph from the declared `input_dict`/`output_dict` paths,
  validated against the perturbation tool.
* `structural_copy` restore; the in-place-mutation test from Stage 0 is what makes it safe.
* Fall back to the plain loop when the static share is below threshold (PEC/STH measured
  only 1.3×, so this matters).
* **Gate:** bit-identical LCOH per sample vs the current loop on every e2e model, for at
  least 1,000 random draws.

### Stage 3 — vectorize the year-sized tail (~3–4 weeks, expected 5–20× on what remains)
Order matters; do it one plugin at a time, innermost-output first:
1. Adopt the `[..., idx]` convention and add explicit `axis=` everywhere — **as a
   no-op refactor on the scalar path**, merged and verified before any batching.
2. Batch-aware `check_type` + annotate the 208 scalar-only specs.
3. Convert `Discounted_Cash_Flow_Plugin` (the recipes in §7 cover its three hard spots),
   then `Capital_Cost_Plugin`, `Replacement_Plugin`, `Other_Fixed_Operating_Cost_Plugin`,
   `Variable_Operating_Cost_Plugin`.
4. Chunked batch runner with per-sample invalid masks (§5.1).
* Keep the scalar path alive as the reference implementation, selected by a flag. Do not
  delete it — it is the oracle for every future test.
* **Gate:** for each converted plugin, batched output matches the scalar path within
  `rtol=1e-12` for 10,000 random draws (see §11 on why not bit-exact).

### Stage 4 — parallelism (~hours, ~N_cores×, independent of all the above)
Re-enable the commented-out pool in
`Monte_Carlo_Analysis.perform_monte_carlo_multiprocessing` (lines ~342–348). Compose with
chunking: one chunk per worker.

### Do NOT do
* Batch the hourly arrays (§6.1 — measured 0.5×).
* Vectorize Tier-C parameters within a batch (§8 — group by shape instead).
* Start with `Quantity` micro-optimization: measured 3 % of the stacked result
  (2.24 → 2.18 ms). Its value here is the memory reduction that makes chunks bigger, not
  the speed.

---

## 11. Risks, ranked

1. **Silent wrong answers from axis defaults.** `np.cumsum(x)` flattens; `x[-1] = v`
   writes a sample. Neither raises. *Mitigation:* the `[..., idx]` / explicit-`axis`
   refactor lands **before** any batching and is verified on the scalar path, so the
   diff that introduces the axis contains no behaviour change.

2. **Numerical reproducibility.** Vectorized rewrites change summation order. MACRS via
   matmul differs by 1.9 × 10⁻⁹ absolute (≈10⁻¹⁵ relative). The e2e tests assert
   `abs=1e-13` on LCOH — **that tolerance may not survive**, and it is a deliberate
   regression guard you should not loosen casually. *Mitigation:* decide up front that
   the scalar path stays the bit-exact reference and the batched path is validated at
   `rtol=1e-12`; keep the strict e2e tests bound to the scalar path.

3. **Per-sample failures aborting a batch** (§5.1). A behavioural change that needs your
   decision, not just code.

4. **The in-place mutation invariant.** Both `structural_copy` and the `Quantity`
   copy-elision depend on it. Nothing violates it today; nothing enforces it either.
   *Mitigation:* the read-only-array test in Stage 0, run in CI.

5. **Plugins reading undeclared inputs.** Would make the dependency graph wrong and
   Stage 2 silently stale. *Mitigation:* the perturbation tool as a CI cross-check.

6. **Divergent code paths.** Two implementations of every cost plugin is a real
   maintenance cost, and the scalar one will rot. *Mitigation:* the batched path must be
   the *only* implementation of the arithmetic, with the scalar path being the same code
   called with `S = 1`. That is what the `[..., idx]` convention buys — it is correct for
   both ranks, so there is one body of code, not two.

7. **Effort vs. benefit for deep-parameter studies.** For a study varying nominal power,
   Stage 2 gives 1.0× and Stage 3 cannot batch the dominant kernel. Those studies get
   Stage 1 (≈2×) and Stage 4 (N_cores) and nothing else. Be explicit about that with
   users rather than promising a blanket speedup.

---

## 12. Expected outcome

For a PV_E Monte Carlo over cost parameters, 100,000 samples, measured except where
marked:

| after | ms/sample | 1 core | 4 cores |
|---|---|---|---|
| today | 17.3 | 29 min | 7.2 min |
| Stage 1 | 8.7 | 14.5 min | 3.6 min |
| Stage 2 | 2.2 | 3.7 min | 0.9 min |
| Stage 3 *(projected, from the 7–41× measured on year-sized kernels)* | 0.1–0.4 | 10–40 s | 3–10 s |

Only the Stage 3 row is a projection; the rest are measured end to end with a
bit-identical LCOH.

For a study varying a deep physical parameter, the realistic endpoint is Stage 1 plus
Stage 4: ≈8.7 ms/sample, 100,000 samples in ~15 min on one core, ~4 min on four.

---

## 13. Compatibility with `Optimization_Analysis` and the other analyses

Short answer: **yes, and optimization benefits more than Monte Carlo does — but only if
the checkpoint scheme is built in its general form.** A prefix checkpoint, which is enough
for Monte Carlo, collapses to 1.05× on a realistic optimization parameter set. The
generalized version measured **8.4×**, and a full `differential_evolution` run
**21.08 s → 2.23 s (8.7×) with an identical optimum**.

There is also a blocker that has to be cleared first, and it is not a performance issue.

### 13.1 Blocker: the analysis entry points do not currently run

`dcf.h2_cost` is **read in five places and assigned nowhere**:

```
Analysis/Waterfall_Analysis.py:52    results['Base Case'] = {'Value': self.base_case.h2_cost}
Analysis/Waterfall_Analysis.py:102   output[variable]['Value'] = dcf.h2_cost
Analysis/Sensitivity_Analysis.py:93  sensitivity_results[name]['Values'][shown_value] = dcf.h2_cost
Analysis/Sensitivity_Analysis.py:172 base_case = self.base_case.h2_cost
Analysis/Monte_Carlo_Analysis.py:317 h2_cost.append(dcf.h2_cost)
```

plus `attribute = 'h2_cost'` as the default in both `discounted_cash_flow_function` and
`discounted_cash_flow_function_1D`, which is what `Optimization_Analysis` calls.
Verified against a working input file:

```
>>> discounted_cash_flow_function_1D([1000.], params, inp)
AttributeError: 'Discounted_Cash_Flow' object has no attribute 'h2_cost'
```

The value exists — `Discounted_Cash_Flow_Plugin` writes it to
`inp['Dependent Variables']['Levelized cost']['Value']` as a `Quantity` — the attribute
was simply never reconnected. No test covers any analysis module, which is why the suite
is green. (The older `Example/*.md` inputs are also stale: they predate the
`Functional Unit` table and raise `KeyError: 'Functional Unit'` before reaching any of
this.)

**This matters for the plan, not just as a bug.** Whatever restores `h2_cost` defines the
seam every accelerated path returns through, so it should be designed for both modes at
once:

```python
@property
def h2_cost(self):                      # scalar today, (S,) under a sample axis
    return self.inp['Dependent Variables']['Levelized cost']['Value'].unit[
        f'USD/{self.functional_unit.unit}']
```

Fix this in Stage 0, with a test per analysis module, before anything else.

### 13.2 Why optimization fits the design well

`Optimization_Analysis.perform_optimization` uses
`scipy.optimize.differential_evolution` — a **population-based** optimizer. Within a
generation every candidate is independent; only generations are sequential. That is the
same structure as a Monte Carlo batch, just narrower.

Measured on PV_E (SciPy 1.17):

| parameters | evaluations | generations | batchable share | max batch width |
|---|---|---|---|---|
| 2 (both CAPEX) | 429 | 13 | **94 %** | 30 |
| 3 (CAPEX ×2 + after-tax IRR) | 988 | 19 | **93 %** | 45 |

SciPy's `vectorized=True` hands the objective an `(n_params, S)` array and expects
`(S,)` back — **exactly the batched-callable interface Stage 3 produces**. I ran it with a
batched wrapper and it returns the same optimum as the serial path.

Two consequences:

* The batch width is `popsize × n_params` (default `popsize=15`), i.e. **30–45, not
  100,000**. Memory and chunking (§9) are therefore non-issues for optimization; but the
  vectorization payoff is the ~5–7× end of the §6.2 curve, not 41×.
* The remaining 6–7 % of evaluations are the final `polish=True` L-BFGS-B step, which is
  strictly sequential and single-point. Its numerical gradients (`n_params + 1`
  evaluations each) could be batched by supplying a batched `jac`, but that is a separate,
  optional refinement.

### 13.3 The finding that changes the design: prefix checkpoints are not enough

Stage 2 as described in §3 snapshots the state **before the earliest tainted plugin** and
replays the whole tail. For Monte Carlo over cost parameters that is fine — the earliest
tainted plugin sits at workflow position 10 of 17.

Optimization parameter sets are usually not that tidy. Adding
`Financial Input Values > After-tax real IRR` — an ordinary thing to optimize — taints
`Time_Plugin` and `Inflation_Plugin`, which are at **position 0**. The tail becomes the
entire workflow and the checkpoint buys nothing:

| optimized parameters | earliest tainted plugin | tail | per evaluation | speedup |
|---|---|---|---|---|
| 2 × CAPEX | position 10 / 17 | 7 steps | 18.80 → 2.22 ms | **8.47×** |
| + after-tax IRR | **position 0 / 17** | 17 steps | 22.14 → 18.15 ms | **1.22×** |

The two tainted plugins at the front cost 0.18 ms each; the ten expensive static ones
behind them (Hourly_Irradiation, Photovoltaic, Electrolyzer, Battery, …) are still
untainted. A prefix checkpoint simply cannot express "re-run these two, skip those ten,
then re-run the rest".

**The fix is to skip static plugins individually rather than taking one prefix
checkpoint.** In the base run, record which leaves of `inp` each plugin writes (a diff of
the structural snapshot before and after it). On replay, execute the tainted plugins and,
for each static plugin, splice its recorded writes back in and reuse its recorded plugin
object:

```python
for key in workflow_tail:
    if key in tainted:
        execute_plugin(key, shim.plugs, print_info=False, dcf=shim)
    else:
        for path, value in writes[key].items():   # recorded in the base run
            splice(shim.inp, path, value)
        shim.plugs[key] = base_plugs[key]
```

Prototyped and measured on the three-parameter case above (302 leaf writes spliced per
evaluation, all shared references, no copying):

| | ms/evaluation | speedup | LCOH |
|---|---|---|---|
| full DCF | 18.04 | 1.00× | reference |
| prefix checkpoint only | 17.18 | 1.05× | bit-identical |
| **+ splicing static plugins** | **2.16** | **8.37×** | **bit-identical** |

**Recommendation: build the splice form in Stage 2, not the prefix form.** It subsumes the
prefix checkpoint, it is barely more code once the per-plugin write sets are recorded, and
it removes the "one early parameter ruins it" failure mode from Monte Carlo too.

### 13.4 End-to-end on a real optimization run

`differential_evolution` over three parameters, `seed=0`, `tol=0.01`, `polish=True`:

| configuration | evaluations | wall | ms/eval | optimum |
|---|---|---|---|---|
| serial, full DCF (today's path, once `h2_cost` is restored) | 988 | 21.08 s | 21.33 | f* = 2.607913778845 |
| + splice-replay | 988 | 2.41 s | 2.44 | identical |
| + electrolyzer kernel fix | 988 | 2.30 s | 2.33 | identical |
| + lazy `Quantity` | 988 | **2.23 s** | **2.26** | identical |

**8.7×**, with the same number of evaluations and the same optimum to every printed digit.
The evaluation count being unchanged is the important part: because the objective stays
bit-identical, the optimizer follows exactly the same search trajectory, so the result is
reproducible against the old path rather than merely "as good".

### 13.5 What is different about optimization, and what to watch

1. **The optimizer visits the corners of the bounds.** Monte Carlo samples a
   distribution; `differential_evolution` deliberately probes the extremes and the
   mutation step can push candidates to the bound edges. Regimes that never occur in an
   MC run — zero denominators, negative costs, out-of-bounds intermediate quantities —
   *will* be visited. The per-sample validity mask of §5.1 is therefore **mandatory**, not
   optional, and invalid candidates must return a **large finite value or `np.inf`, never
   `NaN`**: NaN comparisons are always false, so a NaN in the initial population is never
   displaced and quietly poisons the run.

2. **Numerical reassociation can change the search path.** §11 risk 2 said batched
   rewrites differ in the last ulp. For Monte Carlo that shifts a histogram
   imperceptibly. For an optimizer it can flip an accept/reject at a near-tie and send the
   search down a different branch — same quality of optimum, different numbers, different
   evaluation count. Everything measured above is bit-identical and so reproduces exactly;
   once Stage 3 lands, optimization results must be reported with the mode and seed, and
   comparisons against old runs made on quality, not on equality.

3. **Tier B/C parameters are worse here than in Monte Carlo.** Optimizing a lifetime
   (`PEC Cells > Lifetime`, `Catalyst > Lifetime`) or `Plant life` runs through
   `int(np.ceil(...))`, so the objective is **piecewise constant** in that parameter — it
   already is today, which is presumably why a derivative-free global optimizer was
   chosen. Under batching, a Tier-C parameter additionally gives different array shapes to
   different population members, so a generation must be **grouped by shape** before being
   batched. With `popsize × n_params` ≈ 30–45 candidates and a handful of distinct integer
   values, that is cheap; but it has to be written.

4. **`workers` and `vectorized` are mutually exclusive in SciPy.** `workers=-1` is
   available today and needs nothing from this plan. Everything is picklable (solved input
   dict 3.76 MB, plugin objects 7.08 MB, `Quantity` fine), but shipping ~11 MB per task is
   wasteful — use a pool **initializer that builds the checkpoint once per worker** from
   the raw input instead. For small populations on few cores, `workers=-1` and
   `vectorized=True` are comparable; do not try to combine them.

5. **The taint set is *more* stable than in Monte Carlo.** The optimized parameters are
   declared once in `Parameters - Optimization_Analysis` and never change during the run,
   so the dependency analysis and the write-set recording are amortized over hundreds to
   thousands of evaluations instead of being recomputed. Optimization is the best case for
   Stage 2.

### 13.6 The other analysis modules

| module | how it drives the model | compatible? |
|---|---|---|
| `Sensitivity_Analysis` | `deepcopy(inp)` + `set_by_path` + full DCF, a few values per parameter | Yes — same pattern as MC. One taint set per swept parameter; each sweep is a natural batch. Also blocked on `h2_cost`. |
| `Waterfall_Analysis` | cumulative: each step modifies a *growing* set of keys, then a full DCF | Yes, with care — the taint set grows along the waterfall, so record it per step (or take the union). Only ~n_parameters runs, so this is about correctness, not speed. Blocked on `h2_cost`. |
| `Comparative_MC_Analysis` | instantiates `Monte_Carlo_Analysis` per model | Yes — inherits whatever MC does; the models are independent and are themselves a natural outer parallel axis. |
| `Cost_Contributions_Analysis` | one base-case DCF | Unaffected. |
| `Development_Distance_Time_Analysis` | curve-fits *already-computed* MC results; never calls the DCF | Unaffected. |
| `Monte_Carlo_Analysis.target_price_2D_region` | evaluates a `grid_points²` grid through `perform_monte_carlo_multiprocessing` | Yes — a regular grid is the easiest possible batch. |

### 13.7 Revised guidance

* Move the `h2_cost` fix and one smoke test per analysis module into **Stage 0**. Nothing
  downstream can be validated until the analyses run at all.
* Build **Stage 2 in its splice form** (§13.3). The prefix form is a special case of it
  and fails on ordinary optimization parameter sets.
* Treat the per-sample validity mask (§5.1) as a **Stage 2 requirement** rather than a
  Stage 3 one, because optimization reaches invalid regions long before batching does.
* Expect optimization to gain **~8–9× from Stages 1–2** (measured) and a further ~5× from
  Stage 3 at a batch width of 30–45 — not the 41× that a 10,000-wide Monte Carlo batch
  reaches.

---

## Appendix A — scripts backing every number

In this session's scratchpad (`/tmp/claude-0/.../scratchpad/`), outside the repository:

| file | what it measures | § |
|---|---|---|
| `taint.py`, `taint2.py`, `taint3.py` | perturbation taint analysis, per-plugin, with warm timings | 2 |
| `hoist_proto.py` | the non-idempotence failure (Trap A) | 3.1 |
| `hoist_proto2.py` | checkpoint/replay with `deepcopy` restore | 3.1 |
| `hoist_proto3.py` | checkpoint/replay with `structural_copy` — 7.8× | 3.1 |
| `electro_vec.py` | batched vs scalar electrolyzer kernel; year-sized kernel batching | 6 |
| `electro_patch.py` | the algorithmic fix, end-to-end on the full DCF | 6.1 |
| `macrs_vec.py` | MACRS convolution/matmul, vectorized npv, replacement mask | 7 |
| `combo.py` | all measures stacked | 0 |
| `minimal_diff.py`, `electro_final.py` | attributing the electrolyzer speedup to individual lines | 6.1 |
| `axis_scan.py` | static scan for axis-fragile constructs | 4.1 |
| `opt_probe.py`, `opt_probe2.py` | differential evolution: evaluation counts, batch widths, early-taint case | 13.2–13.3 |
| `splice_proto.py` | per-plugin splice replay — 8.37× where a prefix checkpoint gives 1.05× | 13.3 |
| `opt_stack.py` | full differential evolution run under each configuration | 13.4 |

Environment: 4-core Intel Xeon @ 2.80 GHz container, Python 3.14.0rc2, NumPy 2.4.1.
Absolute millisecond figures move by up to ~50 % between measurement regimes on this
shared machine (best-of vs mean, and a ~150-run allocator warm-up transient); the ratios
were taken back-to-back in one process and are stable. Re-measure on your own hardware
before committing effort.

## Appendix B — the single highest-value line of code

If you do nothing else from this document:

```python
# Electrolyzer_Plugin.calculate_H2_production
- electrolyzer_energy_demand *= np.ones(len(energy_generation))
- electrolyzer_energy_consumption = np.amin(np.c_[energy_generation, electrolyzer_energy_demand], axis = 1)
+ electrolyzer_energy_consumption = np.minimum(energy_generation, electrolyzer_energy_demand)
```

**1.94× on the full PV_E discounted cash flow** (17.96 → 9.26 ms), LCOH bit-identical.
Tidying the rest of the loop body — building the capacity mask with a comparison rather
than two fancy-index assignments — takes it to 2.12×.
