# Performance Improvement Changelog

## 2026-11-07 — Small-to-large `finalize` merge for tajweed parts

**File changed:** `src/quran_transcript/phonetics/conv_base_operation.py`

### Summary

`TajweedRulePartContainer.finalize` now merges the smaller of `old_map` and
`new_map` into the larger one instead of always merging `old_map` into
`new_map`. When `new_map` is smaller, the merged `old_map` becomes the result,
so `_old_keys` must be rebuilt from `old_map` and new parts must be prepended
to preserve the original new-before-old order for overlapping keys.

### Correctness note

A first version of this idea had two issues:

1. The `else` branch rebuilt `_old_keys` from `new_map`, dropping all old-only
   keys. `shift`, `delete_shift`, and `__iter__` then skipped those parts.
2. Appending new parts after old parts reversed the original order for
   overlapping keys.

The first issue is severe: on the full Quran the buggy version produced 50,345
tajweed rules instead of 110,729 and changed 5,714 of 6,236 ayas. The earlier
differential check missed it because it compared `MappingPos.tajweed_rules`,
which is empty in the standard output; the actual rules are exposed through
`out.mappings.ph_to_taj_rules`.

### Benchmarks

Measured on `Aya(2, 282)` (hafs, madd 4/4/4/4/2/6), alternating variants in
the same process, 8 rounds × 200 calls, 6 alternating rounds, median reported:

| Metric | Original | Small-to-large |
|---|---:|---:|
| `finalize` only | 0.882 ms/call | **0.327 ms/call** |
| End-to-end | 11.512 ms/call | **11.109 ms/call** |

Relative improvement: about **63%** for `finalize` itself and **3.5%**
end-to-end.

Per phonetizer call there are 215 `finalize` calls: 164 empty and 51 non-empty.
For non-empty calls the average map sizes are 78 old keys and 97.6 new keys;
`old_map` is larger in roughly 43% of them. A `dict.update` variant for
disjoint keys was tested and gave no measurable gain.

### Validation

- All 6,236 ayas: identical phonemes, mapping positions, and
  `ph_to_taj_rules` (110,729 rules total), 0 mismatches.
- `uv run pytest -q --skip-stress` → **504 passed, 6 skipped**.

---

## 2026-11-07 — Linear end search for short shifts and `delete_shift`

**File changed:** `src/quran_transcript/phonetics/conv_base_operation.py`

### Summary

The mapping end lookup was optimized in two ways:

1. `find_uth_idx_or_deleted_end_log_n` now avoids the `.pos` tuple allocation
   and the `_is_uth_start_altered()` call inside its hot loop.
2. Short ranges use a linear forward scan instead of a binary search:
   - `shift`: linear when `N < 5`, log-n when `N >= 5`;
   - `delete_shift`: linear always.

`shift` still uses `_range_add` / lazy block offsets. The `delete_shift` update
loop is unchanged and continues to read the actual `mapping.pos` of each entry.

Measured on `Aya(2, 282)` (hafs, madd 4/4/4/4/2/6), alternating processes,
8 rounds × 200 calls per process, 3 process pairs, median reported:

| Variant | ms/call |
|---|---:|
| Before (`516f5ca`, binary search in `delete_shift`) | 7.36 |
| Before + linear `delete_shift` only (working-tree revert) | 7.12 |
| **After this change** | **6.88** |

Relative improvement: roughly **6.5%** versus `516f5ca`, and **3.4%** versus
the working-tree state that only reverted `delete_shift` to a linear scan.

### Why not use a linear scan for every `shift`

Per phonetizer call on `Aya(2, 282)`:

| Operation | Calls | Total range | Mapping entries touched |
|---|---:|---:|---:|
| `shift` | 870 | 46,533 chars | 47,413 entries |
| `delete_shift` | 306 | 313 chars | ~1 entry per call |

A full linear scan for `shift` was slower end to end:

| Variant | ms/call |
|---|---:|
| Baseline | 7.16 |
| Linear scan for `shift` + `_range_add` | 8.96 |
| Linear scan for `shift` + direct per-element updates | 9.59 |

Most `shift` calls already have `N == 0` or `N == 1`, so the `N < 5` rule
captures the small-range win without paying the linear cost on large ranges.
Thresholds from 2 to 16 measured within noise of each other.

### Search helper details

- For `mid == _uth_start`, the binary search uses `_prev_pos` directly. If the
  mapping has not been altered, `_prev_pos` equals the actual position; if it
  has, `_prev_pos` is the old coordinate space the search needs.
- Absolute coordinates are read inline as
  `mapping.start + block.delta` / `mapping.end + block.delta` instead of
  `mapping.pos`, avoiding one tuple allocation per probe.
- The new `find_uth_idx_or_deleted_end_linear` uses the same exclusive-end
  convention as `find_uth_idx_or_deleted_end_log_n`. The old inclusive-end
  `find_uth_idx_or_deleted_end` is kept for compatibility but is no longer
  called internally.

### Validation

- All 6,236 ayas: identical phonemes, mapping spans, `deleted` flags, and
  tajweed rules versus the pre-change baseline.
- `uv run pytest -q --skip-stress` → **504 passed, 6 skipped**.

---

## 2026-11-06 — Lazy per-block mapping shifts

**Commit:** `516f5ca` — `optimize mapping shifts with lazy per-block offsets`  
**File changed:** `src/quran_transcript/phonetics/conv_base_operation.py`  
**Diff:** 151 insertions, 51 deletions

### Summary

The phonetizer spends a large part of each call shifting mapping positions after
regex substitutions. Those shifts previously rewrote every covered `MappingPos`
and rebuilt its `(start, end)` tuple. This change replaces that work with a
lazy, block-based representation: each mapping position stores a base coordinate
and shares a block offset that is updated once per fully covered block.

Measured on `Aya(2, 282)`:

| Measurement | Before | After |
|---|---:|---:|
| Steady wall-clock per phonetizer call | 9.01 ms | **6.66 ms** |
| 1,000-call sampled profile | 9.01 ms/call | **7.05 ms/call** |
| Shift microbenchmark (705 real ranges, ~47k element updates) | ~1.35 ms | **~0.27 ms** |

Overall improvement: roughly **26% faster** end to end, with the shift loop
itself roughly **5× faster**.

Validation: `uv run pytest --skip-stress` → **504 passed, 6 skipped**.

---

## The original problem

A shift used to update every mapping entry in the range:

```python
for i in range(uth_start, uth_end + 1):
    start, end = mapping.pos
    mapping.pos = (start + shift, end + shift)
```

For `Aya(2, 282)` this happens ~705–1,000 times per phonetizer call and touches
~47k–57k mapping entries per call. Every touched entry paid for:

- a `.pos` property read that created a tuple,
- tuple arithmetic,
- a `.pos` property write,
- allocation and later garbage collection.

The work is large, repeated, and heavily clustered into contiguous ranges, which
makes it a good candidate for batching.

---

## New representation

Each `MappingPos` now stores its base coordinates and a reference to a shared
block offset:

```python
class _ShiftBlock:
    __slots__ = ("delta",)

    def __init__(self):
        self.delta = 0
```

```python
@dataclass(init=False, eq=False)
class MappingPos:
    start: int
    end: int
    _block: _ShiftBlock | None = None

    @property
    def pos(self):
        block = self._block
        delta = block.delta if block is not None else 0
        return (self.start + delta, self.end + delta)

    @pos.setter
    def pos(self, value):
        block = self._block
        delta = block.delta if block is not None else 0
        self.start = value[0] - delta
        self.end = value[1] - delta
```

The real coordinate is always:

```text
absolute position = stored base + block delta
```

`MappingPos(pos=...)`, `.pos`, `tajweed_rules`, and `deleted` keep their old
public behaviour. Standalone `MappingPos` instances created in tests have
`_block = None`, so they behave exactly as before.

---

## How a block shift works

`PhonetizerMappings` splits the mapping list into blocks of 8 entries and assigns
each entry its block in `__post_init__`:

```python
self._block_size = 8
n_blocks = ceil(len(uth_to_ph) / 8)
self._blocks = [_ShiftBlock() for _ in range(n_blocks)]

for idx, mapping_pos in enumerate(uth_to_ph):
    mapping_pos._block = self._blocks[idx // 8]
```

A shift from index 10 to 30 by `+5`, with `B = 8`:

- **Left edge:** entries 10–15 are updated individually
  (`start += 5`, `end += 5`)
- **Interior:** each fully covered block gets one update:
  `block.delta += 5`
- **Right edge:** entries 24–29 are updated individually

That is about 13 Python-level operations instead of 20. For a 1,000-entry range
it is roughly 14 boundary updates plus ~123 block updates instead of 1,000
element updates.

The entries inside fully covered blocks are never materialized. `.pos` applies
the delta when the coordinate is read.

### Why point writes remain correct

Individual operations such as `delete_shift` and `update_ph_one_to_many` still
assign absolute positions. The `pos` setter subtracts the current block delta
before storing:

```python
mapping.pos = (new_start, new_end)
# stored as:
# start = new_start - block.delta
# end   = new_end   - block.delta
```

Reading `.pos` adds the delta back. This keeps both representations consistent
no matter how many block shifts happened earlier.

---

## Other mapping improvements in this change

### 1. Sparse Tajweed keys instead of scanning ranges

`TajweedRulePartContainer.shift` used to scan every index in
`[old_start, old_end)`:

```python
for idx in range(old_start, old_end):
    if idx in self.old_map:
        ...
```

The range width is ~43 entries, but only ~5 keys usually exist. A sorted
`_old_keys` list plus `bisect_left` now moves only the keys that actually exist:

```python
i = bisect_left(keys, old_start)
j = bisect_left(keys, old_end)
moved = keys[i:j]
```

`delete_shift` uses the same approach.

### 2. Empty-`finalize` fast path

Most `sub` calls insert no Tajweed rules. `finalize` now returns immediately
when `new_map` is empty instead of rebuilding the dictionaries and the sorted
key list. Around 180 of 236 `finalize` calls per phonetizer take this path.

### 3. Deferred `ph_idx` updates

`TajweedRulePart` objects no longer rewrite `ph_idx` every time a key moves.
`ph_idx` is assigned once during iteration, after all shifts and merges are
finished.

### 4. Log-n end lookup in `delete_shift`

The end index is found with the existing binary search over the monotone mapping
positions rather than a linear scan.

---

## Performance intuition

### The workload is “range add, point query”

Shifts are:

- frequent,
- large,
- contiguous,
- and applied to already piecewise-contiguous mapping ranges.

Point reads are comparatively rare: a few coordinate searches plus final output
construction.

This is the classic shape where a lazy representation wins. Pay a tiny extra
cost on each read (one integer addition) and avoid paying the shift cost on
every element.

### Batch at the right granularity

The unit of work should be the block, not the element. A block of 8 is:

- small enough that edge work stays cheap and point updates stay local,
- large enough that long shifts collapse into a handful of integer increments.

### Exploit sparsity

Tajweed rules are sparse. Scanning 43 indices to find 5 keys is wasteful; a
sorted key list plus binary search skips the empty space entirely. This is the
sparse analogue of block compression.

### Avoid allocation in the hot loop

The old shift created a new tuple for every entry on every shift. Block shifting
creates no tuples for interior blocks and only two integer additions for
boundary entries. Less allocation means less garbage collection.

### In Python, constant factors beat asymptotics

Several theoretically attractive options were slower in practice because they
add Python-level overhead to the hot path:

| Approach | Measured time |
|---|---:|
| Direct per-element attribute updates | ~1.05 ms |
| Block-lazy, `B = 8` | **~0.27 ms** |
| NumPy slice-add | ~0.84 ms |
| Two-level blocks | ~0.31–0.35 ms |
| Fenwick-style structure | more Python operations per read |

NumPy loses because ~705 small slice operations per call are dominated by
per-call overhead. Two-level and Fenwick-style structures lose because they add
indirection to every read, while a block lookup is just an array index and one
addition.

### Keep the optimization local

The public contract stayed the same. Consumers such as `search.py`,
`explain_error`, and the tests never need to know about blocks. That is what
keeps the optimization contained instead of spreading through the codebase.

---

## Block size tuning

`B = 8` was chosen by benchmarking the real shift ranges:

| Block size | Time |
|---|---:|
| 4 | 0.315 ms |
| **8** | **0.266 ms** |
| 16 | 0.279 ms |
| 32 | 0.330 ms |
| 64 | 0.429 ms |
| 128 | 0.555 ms |

`B = 8` was fastest, with `B = 16` close behind.

---

## Validation

- Full test suite: **504 passed, 6 skipped**
- Benchmark: `Aya(2, 282)`, `hafs`, warm-up calls followed by steady-state
  timing and a 1,000-call sampling profile
- The mapping-bound search used during development was differentially checked
  against the original start/end searches over 2,335 calls across 16 ayas with
  no mismatches (that helper was later removed during cleanup in favour of the
  simpler original searches)

## Notes

- Measured numbers are from a single development machine; expect some variance.
- The block representation assumes position ranges are shifted as contiguous
  ranges, which is how the substitution pipeline operates.
- No public API changes were required.
