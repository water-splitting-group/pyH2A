"""
Diagnostic test isolating which part of the OLD (buggy)
calculate_PV_power_ratio call pattern was actually responsible for the
@lru_cache memory blow-up in Hourly_Irradiation_Plugin.py.

Background
----------
The old plugin called an `@lru_cache(maxsize=None)`-decorated function with
Quantity objects as arguments. Quantity defines no __eq__/__hash__, so it
falls back to Python's default identity-based hash (object id()). Since
input_resolver_function rebuilds a brand-new Quantity every time it resolves
the input dict (e.g. once per Monte Carlo sample), the SAME underlying value
produced a DIFFERENT hash every call -> every call was a cache miss -> the
cache grew without bound, retaining a full copy of the (large) return value
for every sample forever.

This script isolates exactly which role Quantity plays that causes that:

  Scenario 1 - Quantity object(s) passed IN as arguments, nothing
               Quantity-shaped returned.
               -> Reproduces the actual bug: Quantity is part of the CACHE
               KEY, so equal-value-but-distinct-identity calls never hit.

  Scenario 2 - No Quantity passed in and none returned, but a Quantity IS
               constructed, used, and discarded *inside* the function body.
               -> Control: proves that merely creating/using Quantity
               objects inside a cached function's body is irrelevant to
               cache growth, since they are neither the cache key nor the
               retained return value (they're garbage-collected once the
               call returns).

  Scenario 3 - No Quantity passed in, none constructed inside the function,
               but a Quantity object (pre-built ONCE, outside the function)
               is returned from it.
               -> Isolates whether *retaining* Quantity objects inside
               cached return values causes unbounded growth. It doesn't,
               as long as the cache KEY itself is hashable-by-value.

Run directly for a human-readable report with a results table:
    python src/tests/Utilities/Unit_Handler/lru_cache_quantity_memory_demo.py

Results table columns:
Cache entries/currsize — how many distinct entries are currently sitting in the cache (i.e., the number of unique argument-keys the cache has stored results for so far). This is the actual memory-footprint indicator: a bigger currsize means more retained cached results.
hits + misses always equals the total number of calls made.

Hits — how many calls were answered from the cache, i.e. the arguments hashed/compared equal to a previously-seen call, so the function body didn't re-execute; the cached return value was handed back directly.

Misses — how many calls were not found in the cache, so the function body actually ran, and its result got stored (and counted toward currsize).



Concretely, in this script's three scenarios (each called N_CALLS = 2000 times):

Scenario 1: misses=2000, hits=0, currsize=2000 — every single call misses, because 
each call passes a freshly-constructed Quantity (different id(), different hash) 
even though the value is identical every time. Nothing ever matches a previous key, 
so the cache never reuses anything and ends up holding 2000 separate entries.
Scenarios 2 & 3: misses=1, hits=1999, currsize=1 — the first call is a genuine miss 
(nothing cached yet), but all 1999 subsequent calls pass the exact same (value, unit) 
floats/strings, which hash identically, so they all hit the same single cached entry. 
currsize stays at 1 forever, regardless of how many times you call it.
That's the whole point of the comparison: currsize is what actually determines the 
cache's memory usage, and Scenario 1's currsize=2000 vs. Scenarios 2/3's currsize=1 
is the smoking gun showing that putting a Quantity in the arguments (the cache key) 
— not creating one internally, not returning one — is what caused the unbounded 
growth.


"""

import tracemalloc
from functools import lru_cache

from pyH2A.Utilities.Unit_Handler.quantity import Quantity

N_CALLS = 2000
VALUE = 34.859
UNIT = 'deg'


# ── Scenario 1: Quantity IN, nothing Quantity-shaped OUT ───────────────────

@lru_cache(maxsize=None)
def scenario_1_quantity_in(q):
    '''Quantity object is part of the cache key; returns a plain float.'''
    return q.supplied_value * 2.0


def run_scenario_1():
    scenario_1_quantity_in.cache_clear()
    for _ in range(N_CALLS):
        q = Quantity(VALUE, UNIT)  # fresh object, same value, every call
        scenario_1_quantity_in(q)
    return scenario_1_quantity_in.cache_info()


# ── Scenario 2: no Quantity IN or OUT, but created+discarded inside ────────

@lru_cache(maxsize=None)
def scenario_2_quantity_internal(value, unit):
    '''Plain-value cache key; a Quantity is built and thrown away inside.'''
    q = Quantity(value, unit)  # transient: not part of key or return value
    return q.supplied_value * 2.0


def run_scenario_2():
    scenario_2_quantity_internal.cache_clear()
    for _ in range(N_CALLS):
        scenario_2_quantity_internal(VALUE, UNIT)
    return scenario_2_quantity_internal.cache_info()


# ── Scenario 3: no Quantity IN or constructed inside, but Quantity OUT ─────

_PRE_BUILT_QUANTITY = Quantity(VALUE, UNIT)  # built once, outside the function


@lru_cache(maxsize=None)
def scenario_3_quantity_out(value, unit):
    '''Plain-value cache key; returns a Quantity built elsewhere.'''
    return _PRE_BUILT_QUANTITY


def run_scenario_3():
    scenario_3_quantity_out.cache_clear()
    for _ in range(N_CALLS):
        scenario_3_quantity_out(VALUE, UNIT)
    return scenario_3_quantity_out.cache_info()


def measure(run_fn):
    '''Run `run_fn`, returning its cache_info() plus net bytes allocated
    (tracemalloc snapshot diff) while it ran.'''
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    cache_info = run_fn()
    snapshot_after = tracemalloc.take_snapshot()
    stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    net_bytes = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
    tracemalloc.stop()
    return cache_info, net_bytes


def print_results_table(rows):
    '''Print `rows` (list of tuples: label, calls, currsize, hits, misses,
    net_kib) as a plain, dependency-free aligned ASCII table.'''
    headers = ('Scenario', 'Calls', 'Cache entries', 'Hits', 'Misses', 'Net memory (KiB)')
    all_rows = [headers] + [tuple(str(c) for c in row) for row in rows]
    widths = [max(len(r[i]) for r in all_rows) for i in range(len(headers))]

    def format_row(row):
        return ' | '.join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    separator = '-+-'.join('-' * w for w in widths)

    print(format_row(all_rows[0]))
    print(separator)
    for row in all_rows[1:]:
        print(format_row(row))


if __name__ == '__main__':
    scenarios = [
        ('1: Quantity IN args, plain float OUT', run_scenario_1),
        ('2: no Quantity IN/OUT, Quantity created internally', run_scenario_2),
        ('3: no Quantity IN, pre-built Quantity OUT', run_scenario_3),
    ]

    rows = []
    for label, run_fn in scenarios:
        cache_info, net_bytes = measure(run_fn)
        rows.append((
            label,
            N_CALLS,
            cache_info.currsize,
            cache_info.hits,
            cache_info.misses,
            f'{net_bytes / 1024:.1f}',
        ))

    print_results_table(rows)
