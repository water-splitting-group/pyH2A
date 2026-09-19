# Making `Quantity` Fast — Options Report

**Scope:** exploration only. No production code was changed. Every number below was
measured on this repository at commit `a04fb7a` using throw-away prototypes kept
outside the source tree.

**Target question:** can `Quantity` creation and use be made "extremely fast" while
keeping its current API and usage patterns, so that Monte Carlo runs with 100,000
samples become practical?

---

## 1. Executive summary

Three findings, in order of importance:

1. **`Quantity` is genuinely wasteful, and it can be made 5–10× faster** for object
   creation and 3–5× faster for cache-missing unit lookups, **without any API change
   and with bit-identical results.** Two prototypes were built and both pass the full
   test suite (247/247) with identical LCOH values to the last digit.

2. **But `Quantity` is not currently the bottleneck.** In a real discounted-cash-flow
   run it accounts for roughly **1–8 % of wall time**. Making it 10× faster therefore
   buys **~1.04–1.10× end to end** (steady-state median), or up to ~1.3× on the
   PV+electrolysis model when allocation/GC tail effects are included. The dominant
   cost is plain NumPy work inside the plugins — 60 % of the PV_E run is
   `Electrolyzer_Plugin` alone.

3. **The 100–1000× lever is elsewhere.** `Quantity` already accepts NumPy arrays.
   Carrying a *sample axis* through the model — one DCF pass over arrays of length
   100,000 instead of 100,000 scalar passes — collapses 100,000 × ~300 = 30 million
   object constructions into ~300. Measured on the unit layer alone: **389× less time
   for the same numbers.** Plus the already-written-but-commented-out multiprocessing
   path in `Monte_Carlo_Analysis` (a free ~N_cores×).

**Recommendation:** do the `Quantity` work — it is cheap, low-risk, self-contained and
also cuts memory per run by ~40 % (which matters when you fan out across processes) —
but do not expect it to solve the Monte Carlo problem on its own. Budget the real
effort for vectorisation and/or multiprocessing.

| Path | Measured / estimated gain on 100k-sample MC | Effort | Risk |
|---|---|---|---|
| Optimised `Quantity` (§4, options O1–O4) | 1.05–1.3× | ~1 day | low |
| Compiled `Quantity` (Cython, §4 O5) | 1.05–1.3× (same ceiling) | ~3 days + build chain | medium |
| Re-enable multiprocessing (§6.1) | ~N_cores × | ~hours | low |
| Vectorise the sample axis (§6.2) | 10–100× | weeks | high |
| Fix plugin NumPy hot spots (§6.3) | 1.5–2× | ~days | low |

---

## 2. How the measurements were made

* Machine: 4-core Intel Xeon @ 2.80 GHz container, Linux 6.18.
* Python 3.14.0rc2, NumPy 2.4.1, SciPy 1.17.0 (the project's `uv` lockfile).
* Microbenchmarks: 300 warm-up iterations, then best-of-5 blocks of 3k–30k iterations,
  `gc.collect()` before timing. Best-of is used because this container is noisy.
* End-to-end: each variant run in **its own process** (cross-variant contamination via
  the existing `@lru_cache`s otherwise corrupts the comparison), 5 warm-ups, best-of-6
  blocks of 20 runs.
* Correctness: full `pytest` suite (247 tests) run once per prototype, plus direct
  comparison of the levelized cost to the last binary digit on four end-to-end models.

**Caveat worth stating plainly:** early instrumented estimates put `Quantity` at
8–14 % of runtime. Those were inflated by `perf_counter` wrapper overhead and by a
large first-pass allocator transient (the first ~150 DCF runs in a fresh process are
up to 2× slower than steady state). The A/B numbers in §5, taken by swapping whole
implementations, are the trustworthy ones.

---

## 3. Anatomy of the current implementation

`src/pyH2A/Utilities/Unit_Handler/quantity.py`

### 3.1 What one `Quantity(value, unit_str)` does today

```
parse_reference(unit_str.strip())        # lru_cached  -> 0.083 µs (hit)
unit_str.strip()                         #             -> 0.076 µs
parse_composite_unit(clean)              # lru_cached  -> 0.084 µs (hit)
self.base_value = value * multiplier     # ALWAYS, even when multiplier == 1.0
format_with_reference() × 3              # lru_cached, only if labels present
UnitDictionary(self)                     # dict subclass + 2 setitem -> 0.342 µs
11 × slot assignment                     #             -> ~0.48 µs
                                         # TOTAL ~1.06 µs for a scalar
```

**The parsing is already solved.** All three parsers are `@lru_cache`'d and in a real
run they hit ~90 % on the very first DCF pass and ~100 % afterwards (PV_E: 289 hits /
32 misses cold; only 27 distinct unit strings exist in the whole model). A *cold*
`parse_composite_unit` costs 14.2 µs, a warm one 0.083 µs — a 170× cache benefit that
is **already being collected**. There is nothing left to win by caching the parser.

What is left is (a) Python interpreter overhead — eleven slot stores and a dict
subclass instantiation per object — and (b) an unconditional array copy.

### 3.2 The four concrete inefficiencies

| # | Issue | Cost |
|---|---|---|
| **A** | `base_value = value * multiplier` runs even when `multiplier == 1.0` | On PV_E, **389,049 array elements are copied per DCF run** (~3.1 MB of `memcpy`); only **3** of those copies are mathematically necessary |
| **B** | `UnitDictionary` is built eagerly in `__init__` | 0.34 µs/object; **37 % of the objects never have `.unit` read at all** |
| **C** | `UnitDictionary.__missing__` runs `TOKEN_PATTERN.split()` + strip/filter on every miss | **2.44 µs of the 3.7 µs miss path** — and the token list is used *only to name a token in an error message* |
| **D** | Dimension check is `a.replace(" ","") != b.replace(" ","")` on every miss | 0.32 µs, recomputed from strings that never change |

Measured miss/hit split in real runs (PV_E): 477 `.unit[...]` lookups, **only 12
misses**. `UnitDictionary.__init__` pre-seeds both the supplied unit *and* the base
unit, so the extremely common `.unit['USD']`, `.unit['J']`, `.unit['-']` are plain
dict hits at 0.058 µs. That design choice is already very good.

### 3.3 Distribution of work in a real run (PV_E, per DCF pass)

```
Quantity objects created            281
  ... holding a NumPy array         156   (389,049 elements in total)
  ... scalar                        125
base_value actually needed          225   (80 %)  -> 56 objects never needed it
.unit dict actually needed          178   (63 %)  -> 103 objects never needed it
array copies actually needed          3   (of 156)
unit[] lookups                      477   (465 hits, 12 misses)
distinct unit strings                27
```

Top unit strings by frequency: `'J'` ×131, `'-'` ×55, `'USD'` ×48 — i.e. **83 % of all
constructions use a unit whose multiplier is exactly 1.0**, so issue **A** hits almost
everything.

---

## 4. Option catalogue

Each option lists what it does, the measured effect, and what it costs you.

### O1 — One "unit spec" cache instead of three parser caches ✅ *recommended*

Replace `parse_reference` → `strip` → `parse_composite_unit` → `format_with_reference`×3
with a single `dict[str, UnitSpec]` lookup. A `UnitSpec` is an immutable `__slots__`
object precomputing everything derivable from the unit *string alone*:

```python
class UnitSpec:
    __slots__ = ('clean', 'reference', 'multiplier', 'inv_multiplier',
                 'base_unit', 'dimension', 'dim_key', 'is_abs',
                 'sup_ref', 'base_ref', 'dim_ref', 'tokens')
```

`dim_key` is `sys.intern(dimension.replace(" ", ""))`, so the dimension check in
`__missing__` becomes an `is` comparison instead of two `str.replace` calls (fixes **D**).
`tokens` is built lazily and only when an error message actually needs it (fixes **C**).

* **Measured:** cache-missing lookup `4.64 µs → 1.47 µs` (**3.2×**); construction with
  reference labels `1.39 µs → 1.06 µs` (**1.3×**).
* **Cost:** ~60 lines. The spec dict is unbounded rather than LRU-1024 — fine, unit
  strings are a closed set of a few dozen per model. Use an LRU if you want a bound.
* **Risk:** none. Pure refactor, no semantic change.

### O2 — Do not copy the array when the multiplier is 1.0 ⚠️ *recommended, with a caveat*

```python
m = spec.multiplier
self.base_value = value if (m == 1.0 and _is_float_like(value)) else value * m
```

* **Measured:** `Quantity(np.ones(8760), 'J')` **14.34 µs → 1.03 µs (14×)**. Per DCF run
  on PV_E this removes ~3.1 MB of `memcpy` and 156 array allocations.
* **The trap I hit, and you must not:** the current `value * 1.0` is silently acting as
  an **int → float cast**, and downstream code depends on it. Skipping it naively breaks
  two places:
  * `output_inserter` rejects an `int` where it expects `float`
    (`Battery_Plugin`, entry `'0'`);
  * `np.zeros_like(q.unit['-'])` in `Replacement_Plugin` produces an `int64` array and
    then `+=` a float raises `UFuncOutputCastingError`.

  The guard `_is_float_like` (skip only for exactly `float` and `ndarray` of
  `dtype == float64`) makes the optimisation safe — with it, all 247 tests pass and the
  LCOH is bit-identical.
* **Second caveat — aliasing.** After this change `base_value is supplied_value`. If any
  code ever mutates an array obtained from `.unit[...]` in place, it will now corrupt the
  `Quantity`. I grepped and tested: nothing in the current codebase does this (every
  in-place target — `self.yearly`, `electrolyzer_capacity`, `electrolyzer_energy_consumption`
  — is a freshly derived array), and the full suite passes. But it is a **new invariant
  you are taking on**. Two ways to hold the line:
  * add a test-only debug mode that sets `arr.setflags(write=False)` on returned base
    values, so accidental mutation raises loudly in CI; or
  * copy on the way *out* of `.unit[...]` only when the caller asks (`q.unit_copy[...]`).

### O3 — Build `base_value` and the `.unit` dict lazily ✅ *biggest single win*

Store only `(supplied_value, spec)` at construction; compute `base_value` and the
`UnitDictionary` on first access via properties.

* **Measured:** scalar construction **1.06 µs → 0.19 µs (5.5×)**; array construction
  **14.3 µs → 0.20 µs (70×, deferred)**.
* On a real PV_E run this skips **56** base-value computations and **103** dict
  allocations out of 281 objects entirely — they are created and never interrogated.
* **Memory:** per-object footprint **320 B → 152 B**, and live tracked objects per DCF
  run **562 → 357 (−37 %)**. This is the result that matters most for multiprocessing:
  fewer bytes per worker, fewer GC-tracked containers, shorter GC pauses.
* **Cost:** the attribute names must move to private slots (`_spec`, `_base`, `_unit`)
  with public `@property` accessors. Everything in `__slots__` today
  (`supplied_unit`, `base_unit`, `dimension`, `reference`, `*_reference`,
  `is_absolute_temp`) becomes a property reading from the shared spec — **the public API
  is unchanged**, which is why the existing 247 tests pass untouched.
* **One thing to remember:** a slots-based class with properties needs explicit
  `__deepcopy__`/`__copy__` (the default slot-pickling path tries to `setattr` onto the
  read-only properties and raises). Supplying them is ~10 lines and makes `deepcopy`
  cheaper too, since it can share the immutable spec instead of copying it.

### O4 — A leaner `__missing__`

Beyond O1's `dim_key` and lazy tokens:

* store `inv_multiplier = 1.0/multiplier` in the spec and multiply instead of divide
  (same cost for scalars, marginally better for arrays);
* skip the reference check entirely when neither side carries labels
  (`if spec.reference or q.reference:`) — saves 0.26 µs on the common path;
* use `dict.__setitem__`/`dict.__getitem__` explicitly to avoid re-entering the subclass.
* **Measured (combined with O1):** miss path **4.64 µs → 1.47 µs**.
* Worth noting this only touches 12 of 477 lookups in a real run, so the end-to-end
  effect is small — but it is free once O1 is in.

### O5 — Compile it (Cython / C extension)

I built a working Cython `cdef class` prototype to put a real number on this.

| variant | scalar construction | vs shipped |
|---|---|---|
| shipped | 1.06 µs | 1.0× |
| O1+O2 (pure Python) | 1.03 µs | 1.0× |
| O3 lazy (pure Python) | 0.19 µs | 5.5× |
| Cython, eager | 0.64 µs | 1.7× |
| **Cython + lazy** | **0.109 µs** | **9.8×** |

Two conclusions:

* **Compiling an eager design is worse than not compiling a lazy one** (0.64 µs vs
  0.19 µs). Get the design right first; the win comes from *not doing work*, not from
  doing it in C.
* Cython on top of the lazy design does add a further ~1.8× (0.19 → 0.109 µs).
  Whether that is worth a C toolchain, wheels for every platform, and a harder
  debugging story is a project-policy call. Given that the whole `Quantity` layer is
  ≤8 % of runtime, this 1.8× buys **well under 1 % end-to-end**. My view: **not worth
  it right now**; revisit only after vectorisation, if `Quantity` has become the
  bottleneck by elimination of everything else.

### O6 — Give `Quantity` `__eq__` and `__hash__`

Not a speed-up of `Quantity` itself, but it removes a real wart the codebase already
works around. `Hourly_Irradiation_Plugin` carries this comment:

> `calculate_PV_power_ratio` is `@lru_cache`'d, so every argument besides `file_name`
> is unpacked here into a plain float … `Quantity` has no `__eq__`/`__hash__`, so it
> would hash by object identity and never produce a cache hit for equal values.

A value-based `__hash__` (`hash((base_value, base_unit))` for scalars; refuse to hash
array-valued quantities, as NumPy does) would let `Quantity` objects be used directly
as memo keys, deleting the unpack/repack dance in that plugin and enabling
whole-computation memoisation elsewhere. **Careful:** `__eq__` without `__hash__` makes
the class unhashable; define both or neither.

### O7 — Direct supplied→target factor cache

Cache `(supplied_unit, target_unit) -> factor` so a conversion is one dict lookup and
one multiply, skipping the base-value round trip. **Measured benefit: negligible** here,
because `base_value` already exists and the base unit is pre-seeded into the dict.
Listed for completeness; not recommended.

### O8 — Flyweight / interning of whole `Quantity` objects

Cache `(value, unit) -> Quantity`. **Not recommended for Monte Carlo:** the whole point
of MC is that the values are all different, so the hit rate is ~0 and you pay for the
hash plus unbounded memory growth. It would only pay off for the constant-valued
quantities re-created identically on every sample — which O3 already makes nearly free.

### Things that will *not* help (checked so you don't have to)

* **Numba.** `numba` is already a declared dependency but is not used anywhere in
  `src/`. It cannot help here: `njit` accelerates numeric loops, not Python object
  construction, string handling or dict manipulation, which is 100 % of what `Quantity`
  does. In `nopython` mode a `Quantity` cannot even cross the boundary.
* **PyPy.** Would help the interpreter overhead a lot, but NumPy/SciPy/matplotlib on
  PyPy is a support burden far out of proportion to a ≤8 % slice.
* **Free-threaded (3.13t/3.14t) CPython.** Interesting for the *Monte Carlo loop*
  (see §6.1), irrelevant to `Quantity` itself.
* **`__slots__`.** Already done.
* **More/bigger LRU caches.** Already saturated; see §3.1.

---

## 5. What the optimisations are actually worth, end to end

Two prototypes were swapped in wholesale and validated:

* **`fast`** = O1 + O2 + O4 (in-place method replacement, same class, same slots).
* **`ultra`** = O1 + O2 + O3 + O4 (lazy design, public API preserved via properties).

Both: **247/247 tests pass**, LCOH bit-identical on all four end-to-end models.

### 5.1 Unit-layer microbenchmarks (µs per operation)

| operation | shipped | fast | ultra | cython+lazy |
|---|---|---|---|---|
| construct scalar, simple unit | 1.064 | 1.060 | **0.194** | 0.109 |
| construct scalar, composite unit | 1.087 | 1.033 | **0.195** | 0.109 |
| construct + base-unit lookup (dict hit) | 1.107 | 1.069 | 0.947 | 0.726 |
| construct + non-base lookup (dict miss) | 4.635 | **1.469** | 1.242 | 0.896 |
| construct array(8760), multiplier == 1 | 14.340 | **1.026** | 0.196 | 0.110 |
| construct array(8760), multiplier != 1 | 13.790 | 14.258 | **0.196** | 0.105 |
| warm `q.unit[...]` repeat lookup | 0.058 | 0.058 | 0.058 | — |
| *(reference: plain float multiply)* | 0.032 | | | |

### 5.2 Full DCF run, isolated (best-of, ms)

| model | shipped | fast | ultra |
|---|---|---|---|
| PV_E_Base | 24.19 | 22.41 (1.08×) | **22.06 (1.10×)** |
| PEC_Base | 5.491 | 5.474 (1.00×) | **5.342 (1.03×)** |
| Photocatalytic_Base | 6.096 | 6.026 (1.01×) | **5.838 (1.04×)** |
| Thermal_Base | 3.656 | 3.621 (1.01×) | **3.535 (1.03×)** |

### 5.3 Sustained Monte-Carlo-like loop (400 consecutive samples, ms/sample)

This is the regime you actually care about. Mean and median diverge because the shipped
version has a much heavier allocation tail.

| model | statistic | shipped | fast | ultra |
|---|---|---|---|---|
| PV_E | median (steady) | 24.33 | 23.47 (1.04×) | **22.82 (1.07×)** |
| PV_E | mean (steady) | 35.27 | 28.07 (1.26×) | **25.98 (1.36×)** |
| PEC | median (steady) | 5.89 | 5.47 (1.08×) | **5.43 (1.08×)** |
| PEC | mean (steady) | 6.10 | 5.71 (1.07×) | **5.60 (1.09×)** |

The mean/median gap on PV_E is the interesting part: the shipped version's 3.1 MB of
per-run array copying produces long tails (allocator + GC pauses). The lazy design
essentially removes them. On a 100,000-sample run it is the **mean** that sets the wall
clock, so the honest expectation is **1.1–1.35× on array-heavy models, ~1.08× on
scalar-heavy ones**.

Also observed and worth knowing: **a fresh process needs ~150 DCF runs to reach steady
state**, during which it runs up to 2× slower (heap growth / page faults from churning
70 KB arrays). Short MC runs and short benchmarks systematically overstate per-sample
cost. The lazy design largely removes this transient too.

### 5.4 Where the time really goes (PV_E, per DCF run)

```
Electrolyzer_Plugin                 15.395 ms   60.3 %
Photovoltaic_Plugin                  2.604 ms   10.2 %
Battery_Plugin                       1.527 ms    6.0 %
Discounted_Cash_Flow_Plugin          1.144 ms    4.5 %
Replacement_Plugin                   0.607 ms    2.4 %
Capital_Cost_Plugin                  0.588 ms    2.3 %
… 11 more plugins                    2.79  ms   11 %
```

`Electrolyzer_Plugin.calculate_H2_production` loops over 20 years × 8760 hourly values
and, per year, builds `np.c_[energy_generation, electrolyzer_energy_demand]` — a
two-column 8760×2 copy fed to `np.amin(..., axis=1)`. `np.c_` alone showed ~11 ms/run in
the call-level profile. `np.minimum(a, b)` would do the same job with no copy. That is
a bigger, cheaper win than anything in `Quantity` (see §6.3).

---

## 6. The levers that actually move a 100,000-sample Monte Carlo

At today's ~24 ms/sample (PV_E) a 100,000-sample run is **~40–60 min on one core**;
PEC is ~10 min. `Monte_Carlo_Analysis.perform_h2_cost_calculation` currently runs
strictly sequentially.

### 6.1 Re-enable multiprocessing — free ~N_cores×

`Monte_Carlo_Analysis.perform_monte_carlo_multiprocessing` already contains the pool
code, commented out (lines ~342–348), falling through to a serial call. The batching
helper `divide_into_batches` is written and unused. Restoring this is the single
highest return-on-effort change available.

Notes if you do: `self.inp` must be picklable (it is, once `Quantity` has the
`__deepcopy__`/`__reduce__` support O3 needs anyway); prefer
`ProcessPoolExecutor(..., max_workers=N)` with `chunksize` over `Pool.map` on a list of
batches; and O3's 40 % memory reduction directly reduces per-worker RSS.

A free-threaded CPython build would give the same parallelism without pickling, but
NumPy releases the GIL for the big array ops already and the per-sample Python overhead
does not — processes are the safer bet today.

### 6.2 Vectorise the sample axis — the 10–100× option

`Quantity` already holds NumPy arrays transparently, and the plugin math is already
written in NumPy. The structural change is to make the Monte Carlo sample index *an
array axis* rather than a Python loop: run the DCF **once** with every varied parameter
carrying a `(100000,)` array instead of a scalar.

Measured on the unit layer alone:

```
100,000 scalar Quantity objects (+1 conversion each):  482.41 ms
1 Quantity holding a (100,000,) array (+1 conversion):   1.24 ms
                                                        ------
                                                          389×
per-sample: 4.824 µs (scalar)  vs  0.0124 µs (vectorised)
```

Object constructions drop from ~30,000,000 to ~300 for the whole campaign.

**This is a real project, not a patch.** The blockers are the places where the model
branches on a scalar value or indexes by time in a way that collides with the sample
axis: `electrolyzer_capacity[electrolyzer_capacity > threshold] = 1` (fine — already
elementwise), the `for year in ...` loop (would need an extra axis), `np.c_` column
stacking (needs explicit axis handling), and anything using `scipy.optimize`/`np.roots`
per sample. A realistic path is incremental: vectorise the hot plugins first, keep a
scalar fallback, and validate sample-by-sample against the current code.

Note the interaction with O2: under vectorisation, `value * multiplier` on a
`(100000,)` array is 800 KB per operation, so **not copying when the multiplier is 1.0
becomes far more valuable than it is today**. O2 and O3 are prerequisites that make
vectorisation cheap rather than merely possible.

### 6.3 Fix the plugin NumPy hot spots — 1.5–2× for a few hours' work

Independent of `Quantity`, and much better value per hour than compiling the unit layer:

* `Electrolyzer_Plugin.calculate_H2_production`: replace
  `np.amin(np.c_[a, b], axis=1)` with `np.minimum(a, b)` (removes an 8760×2 copy per
  year, 20 per run);
* the same function builds `electrolyzer_energy_demand *= np.ones(len(...))` to
  broadcast a scalar — NumPy broadcasts for free;
* `check_bounds` in `Utilities/check_functions.py` accounts for ~500 `np.any`/`np.all`
  reductions per run; short-circuit it for scalars.

---

## 7. Semantics that must be preserved (regression checklist)

Anyone implementing the above should keep this list next to them. Each item is
something that actually broke in one of my prototypes.

1. **`value * 1.0` promotes `int` → `float`.** Downstream type checks and
   `np.zeros_like` dtype inference depend on it. Guard the skip. *(broke
   `Battery_Plugin` and `Replacement_Plugin`)*
2. **`base_value` must not alias `supplied_value` if anything mutates it in place.**
   Currently nothing does; make it an invariant and test it.
3. **`isinstance(x, Quantity)` is used for dispatch** in `input_resolver`,
   `output_inserter` and `input_modification`. Any reimplementation must be the same
   class, not a sibling — a subclass breaks `isinstance(old_instance, NewClass)` when
   an `@lru_cache` (e.g. `import_hourly_data`) holds objects built by the old one.
4. **`UnitDictionary` pre-seeds both the supplied and base unit keys**, which is why
   `.unit['J']` on a `Quantity(x, 'J')` is a hit, not a miss. Keep that.
5. **Error messages and exception *types* are asserted by the tests** — `KeyError` for
   an unsupported absolute-temperature unit, `ValueError` for a dimension or reference
   mismatch, with the mismatched token named. Lazily built token lists must still
   produce the same text.
6. **Reference labels are positional, compact, and display-only.** `reference=` and
   bracketed labels are mutually exclusive and must stay so.
7. **`copy.deepcopy` of a `Quantity` must work** — `Monte_Carlo_Analysis` deep-copies
   the whole input dict for every sample. A slots+properties design needs an explicit
   `__deepcopy__`.
8. **Absolute temperature (`K`, `degC`) is offset-based, not multiplicative** and must
   keep its separate path.

---

## 8. Suggested order of work

1. **O1 + O4** (unit-spec cache, lazy error tokens, interned dimension key). Pure
   refactor, no semantic change, 3× on cache-missing lookups. *~half a day.*
2. **O3** (lazy `base_value` and `.unit`). The real win: 5.5× construction, −37 %
   objects, −53 % per-object memory. Needs the property migration and `__deepcopy__`.
   *~1 day.*
3. **O2** (skip the ×1.0 copy) with the `float`/`float64` guard **plus** a CI test that
   marks returned base arrays read-only, so accidental in-place mutation is caught.
   *~half a day.*
4. **Re-enable multiprocessing** in `Monte_Carlo_Analysis`. *~hours, ~N_cores×.*
5. **Fix `np.c_`/`np.ones` in `Electrolyzer_Plugin`** and short-circuit `check_bounds`.
   *~a day, ~1.5×.*
6. Re-measure. Only then decide on **O5 (Cython)** or **§6.2 (vectorisation)** — and on
   the evidence so far, vectorisation is the one worth the money.

**Do not** start with compilation. The measurements say a compiled eager design
(0.64 µs) loses to an interpreted lazy one (0.19 µs).

---

## Appendix A — reproducing these numbers

The prototypes and benchmark scripts live outside the repository, in this session's
scratchpad (`/tmp/claude-0/.../scratchpad/`), so nothing in `src/` was touched:

| file | purpose |
|---|---|
| `fast_patch2.py` | O1+O2+O4 as in-place method replacement on the shipped classes |
| `ultra_patch.py` | O3 lazy design (subclass, API-preserving) + module patcher |
| `cyquantity.pyx`, `setup_cy.py` | Cython `cdef class` prototypes (eager + lazy) |
| `one_variant.py` | per-process end-to-end A/B (§5.2) |
| `mc_steady.py` | 400-sample sustained loop, first/middle/steady split (§5.3) |
| `plugin_profile.py` | per-plugin wall-clock breakdown (§5.4) |
| `lazy_stats.py` | how many objects never need `base_value`/`.unit` (§3.3) |
| `vector_demo.py` | scalar vs array `Quantity` throughput (§6.2) |
| `cmp_all.py` | the five-implementation microbenchmark matrix (§5.1) |

Test validation:
`PYTHONPATH=<scratchpad> pytest -q -p fastplugin` and `-p ultraplugin` → 247 passed each.

Because they are in an ephemeral container, copy anything you want to keep before the
session ends.

## Appendix B — one thing to double-check before trusting §5.3

The container has 4 shared cores and the measurements are noisy at the 5 % level. The
microbenchmarks (§5.1) and the object counts (§3.3) are solid; the end-to-end ratios
(§5.2, §5.3) should be re-taken on your own hardware before being used to justify
effort. The *ranking* of the options is robust; the exact multipliers are not.
