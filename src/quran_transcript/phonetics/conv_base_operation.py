import re
from bisect import bisect_left
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Literal, TypeAlias
from uuid import uuid4

from .moshaf_attributes import MoshafAttributes
from .tajweed_rulses import TajweedRule, TajweedRuleMetadata, TajweedRuleType


class _ShiftBlock:
    """Shared lazy offset for a block of mapping positions.

    Range shifts are applied by changing ``delta`` once per fully covered block
    instead of updating every ``MappingPos`` inside it.


    ShiftBlok Idea:
    * The idea is simple: split mapping into blocks have constat delta.
    * Whever update to the pos we ensure that delta unchanged
    """

    __slots__ = ("delta",)

    def __init__(self):
        self.delta = 0


@dataclass(init=False, eq=False)
class MappingPos:
    """Represents character position mappings in Quranic text transformations.

    This dataclass tracks the relationship between character positions in the original
    text and their corresponding positions after regex substitution operations in the
    Quran transcription system. It maintains position spans and associated tajweed rules
    that apply to those character ranges.

    Attributes:
        pos: Tuple of (start, end) positions in the transformed text. The start is
            inclusive and the end is exclusive (Python-style slice notation).
        tajweed_rules: List of TajweedRule objects that apply to this character span.
            None indicates no tajweed rules are associated with this mapping.
        deleted(bool): Wheter this location is deleted or not. If deleted pos[0] == pos[1]

    Example:
        >>> mapping = MappingPos(pos=(0, 3), tajweed_rules=[])
        >>> print(mapping.pos)
        (0, 3)
        >>> # Add a tajweed rule to this mapping
        >>> mapping.add_tajweed_rule(None)  # No rule added
        >>> mapping.add_tajweed_rule(None)  # Still no rules


    ShiftBlok Idea:
    * The idea is simple: split mapping into blocks have constat delta.
    * Whever update to the pos we ensure that delta unchanged
    """

    # TODO: fill the uthmani tajweed rules
    start: int
    end: int  # pythonic exclusive end
    tajweed_rules: list[TajweedRuleType] | None = None
    deleted: bool = False
    _block: _ShiftBlock | None = field(default=None, repr=False, compare=False)

    def __init__(
        self,
        pos: tuple[int, int],
        tajweed_rules: list[TajweedRuleType] | None = None,
        deleted: bool = False,
    ):
        self._block = None
        self.start, self.end = pos
        self.tajweed_rules = tajweed_rules
        self.deleted = deleted

    @property
    def pos(self) -> tuple[int, int]:
        block = self._block
        delta = block.delta if block is not None else 0
        return (self.start + delta, self.end + delta)

    @pos.setter
    def pos(self, value: tuple[int, int]) -> None:
        block = self._block
        delta = block.delta if block is not None else 0
        self.start = value[0] - delta
        self.end = value[1] - delta

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MappingPos):
            return NotImplemented
        return (
            self.pos == other.pos
            and self.tajweed_rules == other.tajweed_rules
            and self.deleted == other.deleted
        )

    def add_tajweed_rule(
        self, new_tajweed_rules: TajweedRuleType | list[TajweedRuleType] | None
    ) -> None:
        """Add a tajweed rule to this mapping position.

        Appends the new tajweed rule to the existing list of rules if both the
        current rules list and the new rule are not None.

        Args:
            new_tajweed_rule: The TajweedRule to add, or None if no rule to add.

        Example:
            >>> mapping = MappingPos(pos=(0, 3), tajweed_rules=[])
            >>> # This will add the rule if tajweed_rules exists and rule is not None
            >>> # mapping.add_tajweed_rule(some_rule)
        """
        if not new_tajweed_rules:  # covers None and []
            return
        if self.tajweed_rules is None:
            self.tajweed_rules = []
        # if new_tajweed_rules is a single rule, make it a list
        if isinstance(new_tajweed_rules, TajweedRuleType):
            self.tajweed_rules.append(new_tajweed_rules)
        else:
            self.tajweed_rules.extend(new_tajweed_rules)


TagType: TypeAlias = Literal["TAJWEED", "TAJWEED_DEP", "TAG"]
TajweedRulePartType: TypeAlias = Literal[
    "PIVOT_START", "PIVOT_END", "DEP_START", "DEP_END"
]


@dataclass
class TajweedRulePart:
    id: str
    part_type: TajweedRulePartType
    taj_type: TajweedRuleType
    tag: str
    ph_idx: int
    dep_idx: int
    num_deps: int


class TajweedRulePartContainer:
    """
    Shift or deleted assumed to be called before insert
    Attributes:
        temp_map: in the old idx space
    """

    def __init__(self):
        self.new_map: dict[int, list[TajweedRulePart]] = {}
        self.old_map: dict[
            int, list[TajweedRulePart]
        ] = {}  # temp is in the old idx space
        self._old_keys: list[int] = []

    def finalize(self):
        if not self.new_map:
            return

        new_map = self.new_map
        old_map = self.old_map

        # getting keys from the minimum of both (old and new) to reduced the copy overhead
        if len(new_map) >= len(old_map):
            for idx, parts in old_map.items():
                new_map.setdefault(idx, []).extend(parts)

            self.old_map = new_map
            self.new_map = {}
            self._old_keys = sorted(new_map)
        else:
            for idx, parts in new_map.items():
                existing = old_map.get(idx)
                if existing is None:
                    old_map[idx] = parts
                else:
                    # Keep the original new-before-old order for overlapping
                    # keys.
                    existing[:0] = parts
            self.new_map = {}
            self._old_keys = sorted(old_map)

    def __iter__(self) -> Iterator[TajweedRulePart]:
        """The iterator should be called after finalize"""
        for idx in self._old_keys:
            for part in self.old_map[idx]:
                part.ph_idx = idx
                yield part

    def insert(self, idx: int, taj_rule_part: TajweedRulePart) -> None:
        self.new_map.setdefault(idx, []).append(taj_rule_part)

    def get_tjaweed_types(
        self, old_ph_pos_start, new_ph_pos_start: int
    ) -> list[TajweedRuleType]:
        L = []
        if old_ph_pos_start not in self.old_map:
            return L
        for part in self.old_map[old_ph_pos_start]:
            if part.part_type == "PIVOT_START":
                L.append(part.taj_type)

        if new_ph_pos_start not in self.new_map:
            return L
        for part in self.new_map[new_ph_pos_start]:
            if part.part_type == "PIVOT_START":
                L.append(part.taj_type)

        return L

    def shift(self, old_start: int, old_end: int, shift_val: int) -> None:
        """
        Args:
            start (int): inclusive
            end (int): execlusive

        """
        if shift_val == 0 or not self.old_map:
            return

        keys = self._old_keys
        # avoid recomputing self._old_keys at finalize
        i = bisect_left(keys, old_start)
        j = bisect_left(keys, old_end)
        if i == j:
            return

        moved = keys[i:j]
        del keys[i:j]

        old_map = self.old_map
        new_map = self.new_map
        for idx in moved:
            parts = old_map.pop(idx)
            new_map.setdefault(idx + shift_val, []).extend(parts)

    def delete_shift(self, old_start: int, old_end: int, new_idx: int) -> None:
        """Not acully deleting but moving old idx and concatenate them to the new index
        Args:
            start (int): inclusive
            end (int): execlusive

        """
        if old_end - 1 == new_idx or not self.old_map:
            return

        keys = self._old_keys
        # avoid recomputing self._old_keys at finalize
        i = bisect_left(keys, old_start)
        j = bisect_left(keys, old_end)
        if i == j:
            return

        moved = keys[i:j]
        del keys[i:j]

        old_map = self.old_map
        new_map = self.new_map
        for idx in moved:
            parts = old_map.pop(idx)
            new_map.setdefault(new_idx, []).extend(parts)


@dataclass
class PhonetizerMappings:
    """The main Idea here it to update the mappings progressivly (avoid looping
        at every partial update or shift)

    Attributes:
    _taj_parts: TajweedRulePartContainer holding tajweed rule parts keyed by
        their phonetic space index.


    """

    uth_to_ph: list[MappingPos]

    def __getitem__(self, idx: int):
        return self.uth_to_ph[idx]

    def __setitem__(self, idx: int, val):
        self.uth_to_ph[idx] = val
        if getattr(val, "_block", None) is None and self._blocks:
            val._block = self._blocks[idx // self._block_size]

    def __len__(self):
        return len(self.uth_to_ph)

    def __post_init__(self):
        self._prev_pos: tuple[int, int] = (-1, -1)
        self._uth_start: int = -1
        self._taj_to_id = {}
        self._taj_parts = TajweedRulePartContainer()
        self._taj_to_first_to_watch: dict[str, Literal["TAJ", "DEP"]] = {}
        self._ph_to_taj_rules = []
        self._ph_to_uth = []

        # Positions are shifted lazily per block. A range update only touches
        # the boundary blocks and a single integer per fully covered block.
        self._block_size = 8
        n_blocks = (len(self.uth_to_ph) + self._block_size - 1) // self._block_size
        self._blocks = [_ShiftBlock() for _ in range(n_blocks)]
        for idx, mapping_pos in enumerate(self.uth_to_ph):
            mapping_pos._block = self._blocks[idx // self._block_size]

    def range_add(self, start: int, end: int, delta: int) -> None:
        """Add ``delta`` to mapping positions in the half-open range [start, end).

        A Simply adding offset to the delta for a block instead of loop over every entry.
        A block's ``delta`` is shared by all mappings in that block, so only
        fully covered interior blocks can use the one-integer shortcut.
        Boundary blocks are usually partial and must be updated element by
        element.

        Example with ``block_size = 8`` and ``range_add(5, 21, +3)``::

            indices:  0 1 2 3 4 | 5 6 7 | 8 9 10 11 12 13 14 15 | 16 17 18 19 20 | 21 22 23
            range:                [--------------------------------------------)
                                  ^^^^^   ^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^
                                  tail      block.delta += 3          head
        """
        if start >= end or delta == 0:
            # Empty range or no-op shift.
            return

        uth_to_ph = self.uth_to_ph
        blocks = self._blocks
        block_size = self._block_size
        # `end` is exclusive, so `end - 1` is the last affected index.
        first_block = start // block_size
        last_block = (end - 1) // block_size

        if first_block == last_block:
            # Range is inside one block: update only the covered mappings.
            # Changing block.delta would also move the rest of the block.
            for mapping_pos in uth_to_ph[start:end]:
                mapping_pos.start += delta
                mapping_pos.end += delta
            return

        # First block is partial: update only its tail.
        first_block_end = (first_block + 1) * block_size
        for mapping_pos in uth_to_ph[start:first_block_end]:
            mapping_pos.start += delta
            mapping_pos.end += delta

        # Fully covered interior blocks: one integer update per block.
        for block_idx in range(first_block + 1, last_block):
            blocks[block_idx].delta += delta

        # Last block is partial: update only its head.
        for mapping_pos in uth_to_ph[last_block * block_size : end]:
            mapping_pos.start += delta
            mapping_pos.end += delta

    def reset(self):
        self._uth_start = -1
        self._prev_pos = (-1, -1)
        self._taj_to_id = {}
        self._taj_to_first_to_watch = {}

    @classmethod
    def init_mappings(cls, text: str):
        """Initialize Mappings"""
        uth_to_ph = []
        for idx in range(len(text)):
            uth_to_ph.append(MappingPos(pos=(idx, idx + 1)))
        return cls(uth_to_ph=uth_to_ph)

    def init_uth_start(self, ph_pos_idx: int) -> None:
        if self._uth_start != -1:
            return
        lo, hi = 0, len(self.uth_to_ph) - 1
        found_uth_idx = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            start, end = self.uth_to_ph[mid].pos
            if ph_pos_idx < start:
                hi = mid - 1
            elif ph_pos_idx >= end:
                lo = mid + 1
            else:
                found_uth_idx = mid
                break
        if found_uth_idx == -1:
            raise ValueError("Can not find uth_idx at first time")

        self._uth_start = found_uth_idx
        self._prev_pos = self.uth_to_ph[found_uth_idx].pos

    def _is_uth_start_altered(self) -> bool:
        return self.uth_to_ph[self._uth_start].pos != self._prev_pos

    def find_uth_idx(self, curr_ph_pos_idx: int) -> int:
        self.init_uth_start(curr_ph_pos_idx)

        for uth_idx in range(self._uth_start, len(self.uth_to_ph)):
            if uth_idx == self._uth_start and self._is_uth_start_altered():
                start, end = self._prev_pos
            else:
                start, end = self.uth_to_ph[uth_idx].pos

            if curr_ph_pos_idx >= start and curr_ph_pos_idx < end:
                return uth_idx
        raise ValueError("Can not find uth_idx")

    def find_uth_idx_or_deleted_start(self, curr_ph_pos_idx: int) -> int:
        self.init_uth_start(curr_ph_pos_idx)

        for uth_idx in range(self._uth_start, len(self.uth_to_ph)):
            if uth_idx == self._uth_start and self._is_uth_start_altered():
                start, end = self._prev_pos
            else:
                start, end = self.uth_to_ph[uth_idx].pos

            if curr_ph_pos_idx >= start and curr_ph_pos_idx <= end:
                return uth_idx
        raise ValueError("Can not find uth_idx")

    def find_uth_idx_or_deleted_end_log_n(self, curr_ph_pos_idx: int) -> int:
        """curr_ph_pos_idx: is exclusive"""
        self.init_uth_start(curr_ph_pos_idx)

        uth_to_ph = self.uth_to_ph
        uth_start = self._uth_start
        prev_start, prev_end = self._prev_pos

        lo = uth_start
        hi = len(uth_to_ph) - 1
        found_uth_idx = -1
        while lo <= hi:
            mid = (lo + hi) // 2

            if mid == uth_start:
                start, end = prev_start, prev_end
            else:
                mapping = uth_to_ph[mid]
                block = mapping._block
                if block is None:
                    start, end = mapping.start, mapping.end
                else:
                    delta = block.delta
                    start, end = mapping.start + delta, mapping.end + delta

            if curr_ph_pos_idx < start or (curr_ph_pos_idx == start and start != end):
                hi = mid - 1
            elif curr_ph_pos_idx > end:
                lo = mid + 1
            else:
                found_uth_idx = mid
                break
        if found_uth_idx == -1:
            raise ValueError("Can not find uth_idx at first time")

        # Checking we have the most last end
        for uth_idx in range(found_uth_idx, len(uth_to_ph)):
            if uth_idx == uth_start:
                start, end = prev_start, prev_end
            else:
                mapping = uth_to_ph[uth_idx]
                block = mapping._block
                if block is None:
                    start, end = mapping.start, mapping.end
                else:
                    delta = block.delta
                    start, end = mapping.start + delta, mapping.end + delta

            if (
                curr_ph_pos_idx > start
                and curr_ph_pos_idx <= end
                or (start == end and curr_ph_pos_idx == start)
            ):
                found_uth_idx = uth_idx
            elif start > curr_ph_pos_idx:
                break

        return found_uth_idx

    def find_uth_idx_or_deleted_end_linear(
        self, curr_ph_pos_idx: int, start_idx: int | None = None
    ) -> int:
        """Linear variant of `find_uth_idx_or_deleted_end_log_n`.

        `curr_ph_pos_idx` is exclusive, matching the log-n variant. `start_idx`
        may be passed when the caller already resolved the start mapping with
        `find_uth_idx_or_deleted_start`.
        """
        self.init_uth_start(curr_ph_pos_idx)

        uth_to_ph = self.uth_to_ph
        uth_start = self._uth_start
        prev_start, prev_end = self._prev_pos
        if start_idx is None:
            start_idx = uth_start

        found_uth_idx = -1
        for uth_idx in range(start_idx, len(uth_to_ph)):
            if uth_idx == uth_start:
                start, end = prev_start, prev_end
            else:
                mapping = uth_to_ph[uth_idx]
                block = mapping._block
                if block is None:
                    start, end = mapping.start, mapping.end
                else:
                    delta = block.delta
                    start, end = mapping.start + delta, mapping.end + delta

            if (
                curr_ph_pos_idx > start
                and curr_ph_pos_idx <= end
                or (start == end and curr_ph_pos_idx == start)
            ):
                found_uth_idx = uth_idx
            elif start > curr_ph_pos_idx:
                break

        if found_uth_idx == -1:
            raise ValueError("Can not find uth_idx")
        return found_uth_idx

    def update_ph_one_to_many(
        self, curr_ph_pos_start: int, new_ph_pos_start: int, N: int
    ) -> None:
        """Update one to many relation ship"""
        # update uth_to_ph
        uth_idx = self.find_uth_idx(curr_ph_pos_start)
        if uth_idx == self._uth_start:
            # This implies two cases:
            # 1. That the one to many update is the first change to the mappings
            # 2. Or is altered (chages happends before)
            start = self.uth_to_ph[uth_idx].pos[0]
            old_span = self.uth_to_ph[uth_idx].pos[1] - self.uth_to_ph[uth_idx].pos[0]

        elif uth_idx > self._uth_start:
            # This implies a shift has occured in ids before uth_idx

            # Moving the _uth_start
            self._uth_start = uth_idx
            self._prev_pos = self.uth_to_ph[uth_idx].pos

            start = self.uth_to_ph[uth_idx - 1].pos[1]
            old_span = self.uth_to_ph[uth_idx].pos[1] - self.uth_to_ph[uth_idx].pos[0]
        else:
            raise ValueError("UnCaptured case for `update_ph_one_to_many`")

        self.uth_to_ph[uth_idx].pos = (
            start,
            start + old_span + N - 1,
        )
        # Shifting rest of items (as a delete might occur after the one to many)
        if self._uth_start < len(self.uth_to_ph) - 1:
            self.shift(curr_ph_pos_start + 1, new_ph_pos_start + N, 0)

    def shift(
        self,
        curr_ph_pos_start: int,
        new_ph_pos_start: int,
        N: int,
    ) -> None:
        # Shifting Tajweed Rules
        self._taj_parts.shift(
            curr_ph_pos_start,
            curr_ph_pos_start + N,
            new_ph_pos_start - curr_ph_pos_start,
        )

        uth_start = self.find_uth_idx_or_deleted_start(curr_ph_pos_start)
        curr_end = curr_ph_pos_start + N
        if N < 5:
            # Short ranges are cheaper to resolve with a forward scan from the
            # already-known start mapping.
            uth_end = self.find_uth_idx_or_deleted_end_linear(curr_end, uth_start)
        else:
            uth_end = self.find_uth_idx_or_deleted_end_log_n(curr_end)

        # assert self._is_uth_start_altered(), "a shift occured it has to be altered"

        # skiping start as it was altered
        if uth_start == self._uth_start:
            uth_start += 1

        if uth_start <= uth_end:
            # Keep the pre-shift position of the last shifted entry. `_prev_pos`
            # is a snapshot used by `_is_uth_start_altered`, not the new value.
            prev_pos = self.uth_to_ph[uth_end].pos
            shift = new_ph_pos_start - curr_ph_pos_start
            self.range_add(uth_start, uth_end + 1, shift)

            # Updatign our self._uth_start (states)
            # avoiding updaing state with new pos
            if uth_end != self._uth_start:
                # A change happend so we need to udpate the:
                # self_uth_start and self._prev_pos
                self._uth_start = uth_end
                self._prev_pos = prev_pos

    def delete_shift(
        self,
        curr_ph_pos_start: int,
        new_ph_pos_start: int,
        N: int,
    ) -> None:
        # Shifting Tajweed rule parts
        self._taj_parts.delete_shift(
            curr_ph_pos_start, curr_ph_pos_start + N, new_ph_pos_start
        )
        uth_start = self.find_uth_idx_or_deleted_start(curr_ph_pos_start)
        uth_end = self.find_uth_idx_or_deleted_end_linear(
            curr_ph_pos_start + N, uth_start
        )

        if uth_start > uth_end:
            return

        shift = new_ph_pos_start - curr_ph_pos_start
        prev_pos = self.uth_to_ph[uth_end].pos
        for uth_idx in range(uth_start, uth_end + 1):
            start, end = self.uth_to_ph[uth_idx].pos
            if uth_idx != self._uth_start:
                # self._uth_start is already shifted
                start += shift
                end += shift

            # Now start, end in the new_ph_pos space
            start = min(start, new_ph_pos_start)
            end = max(new_ph_pos_start, end - N)

            self.uth_to_ph[uth_idx].pos = (start, end)
            if start == end:
                # delete the entire map
                self.uth_to_ph[uth_idx].deleted = True

        # Updating our self._uth_start (states)
        # avoiding updaing state with new pos
        if uth_end != self._uth_start:
            # A change happend so we need to udpate the:
            self._uth_start = uth_end
            self._prev_pos = prev_pos

    def insert_tajweed_rule_part(
        self,
        old_ph_pos_start: int,
        new_ph_pos_start: int,
        new_ph_pos_end: int,
        parsed_taj_rule_tag: str,
        dep_idx: int,
        num_deps: int,
        tajweed_rule_type: TajweedRuleType | None,
        insert_tajweed_cond: Callable[[list[TajweedRuleType], TajweedRuleType], bool]
        | None,
        tajweed_rule_tag: str,
    ) -> None:
        """
        WARN: insert is assumed to be called after shift
        """
        # WARN: insert is assumed to be called after shift

        if tajweed_rule_type is None:
            return

        # Generating diffrrent id of evey ocuurance of the tajweed rule in the same text
        if parsed_taj_rule_tag not in self._taj_to_first_to_watch:
            if dep_idx == -1:
                self._taj_to_first_to_watch[parsed_taj_rule_tag] = "TAJ"
            else:
                self._taj_to_first_to_watch[parsed_taj_rule_tag] = "DEP"
        if (
            dep_idx == 0 and self._taj_to_first_to_watch[parsed_taj_rule_tag] == "DEP"
        ) or (
            dep_idx == -1 and self._taj_to_first_to_watch[parsed_taj_rule_tag] == "TAJ"
        ):
            self._taj_to_id[parsed_taj_rule_tag] = str(uuid4())

        if insert_tajweed_cond is None:
            cond = True
        else:
            cond = insert_tajweed_cond(
                self._taj_parts.get_tjaweed_types(old_ph_pos_start, new_ph_pos_start),
                tajweed_rule_type,
            )

        if cond:
            # Start
            taj_part = TajweedRulePart(
                id=self._taj_to_id[parsed_taj_rule_tag],
                part_type="DEP_START" if dep_idx != -1 else "PIVOT_START",
                taj_type=tajweed_rule_type,
                tag=tajweed_rule_tag,
                ph_idx=new_ph_pos_start,
                num_deps=num_deps,
                dep_idx=dep_idx,
            )
            self._taj_parts.insert(new_ph_pos_start, taj_part)

            # End
            taj_part = TajweedRulePart(
                id=self._taj_to_id[parsed_taj_rule_tag],
                part_type="DEP_END" if dep_idx != -1 else "PIVOT_END",
                taj_type=tajweed_rule_type,
                tag=tajweed_rule_tag,
                ph_idx=new_ph_pos_end,
                num_deps=num_deps,
                dep_idx=dep_idx,
            )
            self._taj_parts.insert(new_ph_pos_end, taj_part)

    def finalize(self, curr_ph_text_len, new_ph_text_len):
        self._taj_parts.shift(
            curr_ph_text_len, curr_ph_text_len + 1, new_ph_text_len - curr_ph_text_len
        )
        self._taj_parts.finalize()

    def get_ph_to_tajweed_rules(self) -> list[list[TajweedRuleMetadata]]:
        """ """
        max_ph = self.uth_to_ph[-1].pos[1] if self.uth_to_ph else 0
        ph_to_taj_rules: list[list[TajweedRuleMetadata]] = [
            [] for _ in range(max_ph + 1)
        ]

        taj_to_meta: dict[str, TajweedRuleMetadata] = {}
        for part in self._taj_parts:  # parts are yielded sorted by ph_idx
            if part.id not in taj_to_meta:
                taj_to_meta[part.id] = TajweedRuleMetadata(
                    pivot=(-1, -1),
                    deps=[(-1, -1) for _ in range(part.num_deps)],
                    tag=part.tag,
                    rule_type=part.taj_type,
                )

            match part.part_type:
                case "PIVOT_START":
                    taj_to_meta[part.id].update_pivot_start(part.ph_idx)
                case "PIVOT_END":
                    taj_to_meta[part.id].update_pivot_end(part.ph_idx)
                case "DEP_START":
                    taj_to_meta[part.id].update_dep_start(part.dep_idx, part.ph_idx)
                case "DEP_END":
                    taj_to_meta[part.id].update_dep_end(part.dep_idx, part.ph_idx)

        taj_ids = list(taj_to_meta.keys())
        for taj_id in taj_ids:
            taj_meta = taj_to_meta.pop(taj_id)
            ph_to_taj_rules[taj_meta.pivot[0]].append(taj_meta)
        return ph_to_taj_rules

    @property
    def ph_to_taj_rules(self) -> list[list[TajweedRuleMetadata]]:
        if self._ph_to_taj_rules:
            return self._ph_to_taj_rules
        self._ph_to_taj_rules = self.get_ph_to_tajweed_rules()
        return self._ph_to_taj_rules

    @property
    def ph_to_uth(self) -> list[int]:
        if self._ph_to_uth:
            return self._ph_to_uth
        ph_to_uth = []
        for uth_idx in range(len(self.uth_to_ph)):
            for ph_idx in range(
                self.uth_to_ph[uth_idx].pos[0], self.uth_to_ph[uth_idx].pos[1]
            ):
                ph_to_uth.append(uth_idx)

        # last index
        ph_to_uth.append(len(self.uth_to_ph))

        self._ph_to_uth = ph_to_uth
        return self._ph_to_uth


def init_mappings(text: str) -> PhonetizerMappings:
    """Initialize Mappings"""
    return PhonetizerMappings.init_mappings(text)


# Avoiding catching preious tag patter for example <x:aa><y:aa> we will hit the same match again so we want to have a moving cursor to avoid that

_groups = re.compile(
    r"""
      (?P<escape>\\\\)                              # literal backslash  \\
    | \\g<(?P<gname>[A-Za-z_][A-Za-z0-9_]*|\d+)>    # \g<name>  or  \g<1>
    | \\(?P<gnum>[0-9]{1,2})                        # \1 .. \99
    """,
    re.VERBOSE,
)
# `D` is included in the [DTa-z] to be nicly explained in the parser
_mapped_tags = re.compile(
    r"<(D[0-9][0-9]|D[0-9]|[DTa-z][0-9]?):((?:\\.|\[(?:\\.|[^\]\\])*\]|\(\?P<\w+>|[^>\\])*)>"
)


@dataclass(frozen=True)
class RepPart:
    t: Literal["ID", "NAME", "STR"]
    grp_id: int
    grp_name: str
    text: str


@dataclass
class MapTag:
    start: int
    end: int
    tag: str
    tag_tp: TagType
    taj_tag: str  # Which taj tag dep is associated to
    taj_deps: list[str]  # list of taj dep tags (filled only for pivot `T` tags)
    pat: str
    rep_parts: list[RepPart]
    compiled_pat: re.Pattern
    dep_idx: int = -1  # 0..n-1 for dependency `D` tags, -1 for everything else
    num_deps: int = 0  # total number of deps of the associated pivot


def parse_replacement(rep: str) -> list[RepPart]:
    result = []
    last_end = 0

    for m in _groups.finditer(rep):
        if last_end != m.start():
            rep_part = RepPart(
                t="STR",
                grp_id=-1,
                grp_name="",
                text=rep[last_end : m.start()],
            )
            result.append(rep_part)
        if m.group("escape"):
            rep_part = RepPart(
                t="STR",
                grp_id=-1,
                grp_name="",
                text="\\",
            )
            result.append(rep_part)
        elif m.group("gname") is not None:
            name = m.group("gname")
            if name.isdigit():
                rep_part = RepPart(
                    t="ID",
                    grp_id=int(name),
                    grp_name="",
                    text="",
                )
                result.append(rep_part)
            else:
                rep_part = RepPart(
                    t="NAME",
                    grp_id=-1,
                    grp_name=name,
                    text="",
                )
                result.append(rep_part)
        elif m.group("gnum") is not None:
            rep_part = RepPart(
                t="ID",
                grp_id=int(m.group("gnum")),
                grp_name="",
                text="",
            )
            result.append(rep_part)
        last_end = m.end()

    # last segment
    if last_end != len(rep):
        result.append(
            RepPart(
                t="STR",
                grp_id=-1,
                grp_name="",
                text=rep[last_end:],
            )
        )
    return result


def expand_replacement(rep_parts: list[RepPart], match: re.Match) -> str:
    """Expand backreferences in a replacement string for a single match."""
    out_str = ""
    for part in rep_parts:
        match part.t:
            case "STR":
                out_str += part.text
            case "ID":
                if match.group(part.grp_id):
                    out_str += match.group(part.grp_id)
            case "NAME":
                if match.group(part.grp_name):
                    out_str += match.group(part.grp_name)
    return out_str


class MappedTagPrasingError(Exception): ...


class MappedTagPrasingCardinalityError(Exception): ...


_taj_tag_re = re.compile(r"^T([0-9])$")
_dep_tag_re = re.compile(r"^D([0-9])([0-9])?$")


def _classify_tag_type(tag: str) -> TagType:
    """Classify a tag name into its `TagType`.

    * Tajweed pivot tags: `T` or `T0`-`T9` -> `"TAJWEED"`.
    * Tajweed dependency tags: `D0`-`D9` or `D00`-`D99` -> `"TAJWEED_DEP"`.
    * Anything else (including literal pattern segments) -> `"TAG"`.
    """
    if tag == "T" or _taj_tag_re.match(tag):
        return "TAJWEED"
    if _dep_tag_re.match(tag):
        return "TAJWEED_DEP"
    return "TAG"


def _add_tajweed_tags(mapped_tags: list[MapTag]) -> None:
    """Associate each dependency (`D`) tag with its Tajweed (`T`) tag.

    It fills `taj_tag`, `dep_idx` and `num_deps` for `T`/`D` tags and validates
    the Tajweed tags rules:

    * No duplicated Tajweed (`T`) tags.
    * A single digit dependency (`D0`-`D9`) can not be used with a numbered
      Tajweed tag (`T1`) and a two digit dependency (`D00`-`D99`) can not be
      used with an unnumbered Tajweed tag (`T`).
    * Every dependency has to refer to an existing Tajweed tag.
    * Dependencies of each Tajweed tag have to start from 0 and increment with
      one in order.

    Raises:
        MappedTagPrasingError: on any of the invalid usages above.
    """
    # Unique pivot tags
    taj_tag_to_map: dict[str, MapTag] = {}
    for m_tag in mapped_tags:
        if m_tag.tag_tp != "TAJWEED":
            continue
        if m_tag.tag in taj_tag_to_map:
            raise MappedTagPrasingError(
                f"Duplicated Tajweed tag `{m_tag.tag}` each Tajweed rule needs a "
                f"unique tag use `T0`-`T9` for multiple Tajweed rules"
            )
        taj_tag_to_map[m_tag.tag] = m_tag
        m_tag.taj_tag = m_tag.tag

    has_numbered_taj = any(tag != "T" for tag in taj_tag_to_map)

    for m_tag in mapped_tags:
        if m_tag.tag_tp != "TAJWEED_DEP":
            continue

        # `D0`-`D9` depends on the `T` tag
        # `D00`-`D99` depends on the `T<first digit>` tag
        if len(m_tag.tag) == 2:
            if has_numbered_taj:
                raise MappedTagPrasingError(
                    f"Single digit dependency tag `{m_tag.tag}` can not be used "
                    f"with a numbered Tajweed tag use `D<rule digit><dep digit>` "
                    f"like `D10` with `T1`"
                )
            taj_tag = "T"
            dep_idx = int(m_tag.tag[1])
        else:
            taj_tag = f"T{m_tag.tag[1]}"
            dep_idx = int(m_tag.tag[2])

        if taj_tag not in taj_tag_to_map:
            raise MappedTagPrasingError(
                f"Dependency tag `{m_tag.tag}` refers to the Tajweed tag "
                f"`{taj_tag}` which does not exist"
                + (
                    ""
                    if has_numbered_taj
                    else " two digit dependencies need a numbered Tajweed tag like `T1`"
                )
            )

        taj_map_tag = taj_tag_to_map[taj_tag]
        # The length of the collected deps is the next expected dependency index
        if dep_idx != len(taj_map_tag.taj_deps):
            raise MappedTagPrasingError(
                f"Dependencies of the Tajweed tag `{taj_tag}` have to start "
                f"from 0 and increment by one in order but got dependency "
                f"index: `{dep_idx}` for tag `{m_tag.tag}`"
            )

        m_tag.taj_tag = taj_tag
        m_tag.dep_idx = dep_idx
        taj_map_tag.taj_deps.append(m_tag.tag)

    # num_deps is the total deps of the pivot (deps may come after the pivot)
    for taj_map_tag in taj_tag_to_map.values():
        taj_map_tag.num_deps = len(taj_map_tag.taj_deps)
    for m_tag in mapped_tags:
        if m_tag.tag_tp == "TAJWEED_DEP":
            m_tag.num_deps = taj_tag_to_map[m_tag.taj_tag].num_deps


def parse_tags(pat: str, rep: str) -> list[MapTag]:

    rep_tag_to_text = {}
    last_idx = 0
    for match in _mapped_tags.finditer(rep):
        if last_idx != match.start():
            raise MappedTagPrasingError(
                f"`rep` should be connected like `<a:abc><b:cde>` but found "
                f"out-of-bounds element at position {match.start()}: "
                f"`{rep[last_idx : match.start()]}`",
            )
        tag = match.group(1)
        tag_pat = match.group(2)
        if tag in rep_tag_to_text:
            raise MappedTagPrasingError(
                f"Repeated tag `{tag}` at position `{match.start(1)}` in `rep` pattern. Tag should be used only once in the rep!"
            )
        rep_tag_to_text[tag] = tag_pat
        last_idx = match.end()
    if last_idx != len(rep):
        raise MappedTagPrasingError(
            f"`rep` should be connected like `<a:abc><b:cde>` but found "
            f"out-of-bounds element from position {last_idx}: `{rep[last_idx:]}`",
        )

    mapped_tags = []
    pat_tags = set()
    offset = 0
    last_idx = 0
    for match in _mapped_tags.finditer(str(pat)):
        # non tag pattern
        tag = match.group(1)
        start = match.start()

        if tag == "D":
            raise MappedTagPrasingError(
                f"Using only `D` to describe Tajweed Rule Dependency is not supported. It has to be followed by an index starting from `0` to `9`. Current tag position is `{match.start(1)}`"
            )

        if tag in pat_tags:
            raise MappedTagPrasingError(
                f"Repeated tag `{tag}` at position `{match.start(1)}` in `pat` pattern. Tag should be used only once in the pat!"
            )
        pat_tags.add(tag)

        if start != last_idx:
            mapped_tags.append(
                MapTag(
                    start=last_idx,
                    end=start,
                    tag="",
                    tag_tp="TAG",
                    taj_tag="",
                    taj_deps=[],
                    pat=pat[last_idx:start],
                    rep_parts=[],
                    compiled_pat=re.compile(pat[last_idx:start]),
                )
            )
        start_offset = match.end(1) - match.start(1) + 2
        mapped_tag = MapTag(
            start=match.start(2) - offset - start_offset,
            end=match.end(2) - offset - start_offset,
            tag=tag,
            tag_tp=_classify_tag_type(tag),
            taj_tag="",
            taj_deps=[],
            pat=match.group(2),
            rep_parts=parse_replacement(rep_tag_to_text.get(tag, "")),
            compiled_pat=re.compile(match.group(2)),
        )
        offset += start_offset + 1
        mapped_tags.append(mapped_tag)
        last_idx = match.end()

    # last non tag pattern
    start = len(pat)
    if start != last_idx:
        mapped_tags.append(
            MapTag(
                start=last_idx,
                end=start,
                tag="",
                tag_tp="TAG",
                taj_tag="",
                taj_deps=[],
                pat=pat[last_idx:start],
                rep_parts=[],
                compiled_pat=re.compile(pat[last_idx:start]),
            )
        )

    # Every tag in the `rep` has to exist in the `pat`
    for rep_tag in rep_tag_to_text:
        if rep_tag not in pat_tags:
            raise MappedTagPrasingError(
                f"tag: `{rep_tag}` exists in the `rep` but does not exist in the `pat`"
            )

    # Associate dependencies (`D`) with their Tajweed (`T`) tags
    _add_tajweed_tags(mapped_tags)

    return mapped_tags


class QuranREWithMapping:
    """A minimal layer on top of ``re`` that defines an explicit mapping from
    ``pat`` to ``rep``, with optional Tajweed rule insertion.

    The pattern and replacement are parsed and compiled once when the object is
    created. The instance then works in one of two modes:

    * ``SUB`` when ``rep`` is provided: apply the substitution with :meth:`sub`.
    * ``INS_TAJ`` when ``rep`` is ``None``: insert Tajweed rules only with
      :meth:`insert_tajweed`.

    Attributes:
        pat: The pattern with the leading ``M:`` prefix removed.
        rep: The replacement template. ``None`` means rule-only insertion mode.
        mapped_tags: The parsed :class:`MapTag` objects containing the pattern
            segments, tag metadata, replacement parts, and compiled patterns.
        re_pat: The full compiled regex built from all mapped tag patterns.
        taj_rule_type: The default Tajweed rule type attached to matches, or
            ``None`` when the operation only performs substitution.
        insert_taj_cond: Optional callback that decides whether a Tajweed rule
            should be inserted based on the existing rules and the new rule.


        Rules:
        * This a modified re.sub the defines explicit mapping from `pat` to `rep`
        * `pat` should start with `M:`
        * EX: pat = r"<x:abc>D<y1:(def)>"
              rep = r"<x:ABC><y1:\1>"
        <x:abc>
        ^^    ^
        -^----- This is called a `tag` These brackets holds the pattern and is no rleated to re gropus.
         ^
         ^ `x` is called  the tag name and composed only of a single charcter and it can followed by a number like `x`
         `abc` is called `tag pattern`

        * for the rep <x:ABC> `ABC` is called `tag replacement`
        * rep patterns Have to be connected like r"<x:ABC><y1:\1>" but not r"<x:ABC>N<y1:\1>" (N) is not mapped
        * if a group of patterns is existis in the `pat` and does not exist in the `rep` it will be deleted like `D` in the example
        * a tag in the `rep` has to exist in the `pat` as well otherwise a parsing error is raised
        * tag names have to be unique in both `pat` and `rep`; repeating a tag raises
          `MappedTagPrasingError`
        EX: pat = r"<x:a><x:b>"  # repeated `x` in `pat`
            rep = r"<x:a>"

        EX: pat = r"<x:a><y:b>"
            rep = r"<x:a><x:c>"  # repeated `x` in `rep`

        * Tag pattern/replacement length rules:
          - Equal lengths: normal one-to-one mapping.
          - Pattern length is 1 and replacement is longer: one-to-many mapping.
          - Otherwise, if the lengths differ, the shorter tag text must be an exact
            prefix of the longer tag text:
            - replacement longer: the extra replacement characters are inserted.
            - pattern longer: the extra pattern characters are deleted.
          If the shorter text is not a prefix of the longer one,
          `MappedTagPrasingCardinalityError` is raised.

        EX: pat = r"<x:abc>"
            rep = r"<x:abcd>"  # insert `d`

        EX: pat = r"<x:abc>"
            rep = r"<x:ab>"    # delete `c`

        ## Adding Tajweed Rule
        * You can add tajweed rules using Tajweed tag `T` with our wihout numbers from 0 to 9 like `T0`
        * Also you can annoated depedencies which the Tajweed Rule relies on. Using `D` tag followed by a single digit number or two.
        * If you you used `T` tag only without any number digit you can you use `D` followed by a single digit either before the Tajweed Rule or after it like:
        EX: pat = r"<D0:ab><T:cd><D1:ef>"
            rep = r"<D0:ab><T:CD><D1:ef>"
        * If you used a Tajweed tag `T` followed by a single digit like `T1`, Tajweed dpedencies has to have two digits like `D10`. The first digit corrresponds to the digit following the Tajweed tag and the second on is the Depdency index
        EX: pat = r"<T0:ab><D00:cd><T1:ef><D10:gh>"
            rep = r"<T0:AB><D00:cd><T1:EF><D10:gh>"
        * Depdeny order matters, increments with one and have to start from 0 like:
        EX: pat = r"<D0:ab><T:cd><D1:ef>"
            rep = r"<D0:ab><T:CD><D1:ef>"


        ### What is not Allowed with Tajweed Tags
        * Using a single digit depenceis like `D0` with a Tajweed Tag with a digit `T1`
        * Using a two digit depdency like `D12` with no digit Tajweed tag like: `T`
        * Out of order depencies or increment more than one or start with non zero depdency index like:
        EX: pat = r"<D5:ab><T:cd><D3:ef>"
            rep = r"<D5:ab><T:CD><D3:ef>"

        EX: pat = r"<D2:ab><T:cd><D4:ef>"
            rep = r"<D2:ab><T:CD><D4:ef>"


        EX: pat = r"<D2:ab><T:cd><D3:ef>"
            rep = r"<D2:ab><T:CD><D3:ef>"



        Limitation:
        * not supporting named group followed by the end of tag brackets in `rep` like this: `r"<x:X><r:\\g<c>>"`
                                               -------------------------------------------------------------^
        Because the parser will think that the end of named group is the group name closing
    """

    def __init__(
        self,
        pat: str,
        rep: str | None,
        taj_rule_type: TajweedRuleType | None,
        insert_taj_cond: Callable[[list[TajweedRuleType], TajweedRuleType], bool]
        | None = None,
    ):
        assert pat.startswith("M:")
        pat = pat[2:]

        if rep is None:
            # Add tjaweed only mode
            self.mapped_tags = parse_tags(pat, "")
        else:
            # sub with mapping
            self.mapped_tags = parse_tags(pat, rep)

        re_pat = ""
        for m_tag in self.mapped_tags:
            re_pat += m_tag.pat
        self.re_pat = re.compile(re_pat)

        self.pat = pat
        self.rep = rep
        self.taj_rule_type = taj_rule_type
        self.insert_taj_cond = insert_taj_cond

    def get_mode(self) -> Literal["SUB", "INS_TAJ"]:
        if self.rep is None:
            return "INS_TAJ"
        return "SUB"

    def sub(
        self,
        text: str,
        mappings: PhonetizerMappings,
        tajweed_rule_tag: str = "",
    ) -> tuple[str, PhonetizerMappings]:
        """Apply the compiled pattern/replacement to ``text``.

        The substitution does not mutate ``text`` in place. It returns the newly
        transformed text and must be used by the caller. ``mappings`` is updated
        to relate the original characters to their new spans in the output text
        and to any inserted Tajweed rule parts.

        Args:
            text: Input text to apply the substitution to.
            mappings: Mappings to update and return.
            tajweed_rule_tag: Optional tag attached to the created Tajweed rule
                parts. This is not the same as the ``T`` tag name.

        Returns:
            A tuple of ``(out_text, mappings)``.

        Raises:
            AssertionError: If this instance was created with ``rep=None`` and is
                therefore in ``INS_TAJ`` mode.
            MappedTagPrasingCardinalityError: If a tag mapping has unsupported
                many-to-many or many-to-one cardinality.
        """

        assert self.get_mode() == "SUB", (
            "IN sub mode we `pat` has to be valid not `None`"
        )

        out_text = ""

        in_pos = 0
        out_pos = 0
        shifted = False
        mappings.reset()
        for match in self.re_pat.finditer(text):
            out_text += text[in_pos : match.start()]  # text not cpatured by the pat

            keep_num = match.start() - in_pos
            # shifting mappings
            if shifted:
                mappings.shift(in_pos, out_pos, keep_num)

            in_pos = match.start()
            out_pos += keep_num
            for m_tag in self.mapped_tags:
                tag_rep_text = ""
                # pattern exist not deleted
                tag_mat = m_tag.compiled_pat.match(
                    text, pos=in_pos
                )  # Avoiding catching preious tag patter for example <x:aa><y:aa> we will hit the same match again so we want to have a moving cursor to avoid that
                assert tag_mat != None
                tag_pat_text = tag_mat.group()
                tag_pat_len = len(tag_pat_text)

                if m_tag.tag != "" and m_tag.rep_parts != []:
                    tag_rep_text = expand_replacement(m_tag.rep_parts, match)
                    tag_rep_len = len(tag_rep_text)
                    min_both_len = min(tag_pat_len, tag_rep_len)
                    if (tag_pat_len == tag_rep_len) and shifted:
                        # equal mapping
                        mappings.shift(in_pos, out_pos, tag_pat_len)
                    elif (tag_pat_len == tag_rep_len) and not shifted:
                        ...
                    elif tag_pat_len == 1 and (len(tag_rep_text) > 1):
                        # one to many
                        mappings.update_ph_one_to_many(in_pos, out_pos, tag_rep_len)
                        shifted = True
                    elif tag_pat_text[:min_both_len] == tag_rep_text[:min_both_len]:
                        if tag_rep_len > tag_pat_len:
                            # insert
                            if shifted:
                                mappings.shift(in_pos, out_pos, min_both_len - 1)
                            mappings.update_ph_one_to_many(
                                in_pos + min_both_len - 1,
                                out_pos + min_both_len - 1,
                                tag_rep_len - min_both_len + 1,
                            )
                            shifted = True
                        else:
                            # delete
                            if shifted:
                                mappings.shift(in_pos, out_pos, min_both_len)
                            mappings.delete_shift(
                                in_pos + min_both_len,
                                out_pos + min_both_len,
                                tag_pat_len - tag_rep_len,
                            )
                            shifted = True

                    else:
                        raise MappedTagPrasingCardinalityError(
                            f"Not supporting many to many or many to one mapping you want to map: `{tag_pat_text}` to `{tag_rep_text}` corresponds to tag: `{m_tag}`"
                        )
                elif m_tag.rep_parts == [] and tag_pat_len > 0:
                    # the tag_pat_len for regs that are zero lenght like `z?`
                    # Deletion
                    tag_rep_text = ""
                    mappings.delete_shift(in_pos, out_pos, tag_pat_len)
                    shifted = True

                if m_tag.tag_tp in {"TAJWEED", "TAJWEED_DEP"}:
                    mappings.insert_tajweed_rule_part(
                        in_pos,
                        out_pos,
                        out_pos + len(tag_rep_text),
                        m_tag.taj_tag,  # NOTE: the associated pivot (T) tag so a pivot and its deps share the same id
                        m_tag.dep_idx,
                        m_tag.num_deps,
                        self.taj_rule_type,
                        self.insert_taj_cond,
                        tajweed_rule_tag,  # NOTE: `tajweed_rule_tag` here is not the tag name but another thig raelate d to Tajweed rule we might need to rename it for disamiguity
                    )

                in_pos += tag_pat_len
                out_pos += len(tag_rep_text)
                out_text += tag_rep_text
            in_pos = match.end()

        # The rest of positions
        out_text += text[in_pos:]
        if shifted and in_pos < len(text):
            mappings.shift(in_pos, out_pos, len(text) - in_pos)
        mappings.finalize(len(text), len(out_text))

        return out_text, mappings

    def insert_tajweed(
        self,
        text: str,
        mappings: PhonetizerMappings,
        tajweed_rule_tag: str = "",
    ) -> PhonetizerMappings:
        """Attach Tajweed rules to ``mappings`` without changing ``text``.

        This is the rule-only mode. The compiled pattern is searched in ``text``
        and the affected spans are recorded in ``mappings``; no replacement text
        is produced.

        Args:
            text: Input text to search for Tajweed rule patterns.
            mappings: Mappings to update and return.
            tajweed_rule_tag: Optional tag attached to the created Tajweed rule
                parts. This is not the same as the ``T`` tag name.

        Returns:
            The updated :class:`PhonetizerMappings`.

        Raises:
            AssertionError: If this instance was created with a replacement
                (``rep`` is not ``None``) and is therefore in ``SUB`` mode.
        """

        assert self.get_mode() == "INS_TAJ", (
            "IN insert_tajweed mode we `rep` has to be `None`"
        )

        mappings.reset()
        for match in self.re_pat.finditer(text):
            pos = match.start()
            for m_tag in self.mapped_tags:
                # pattern exist not deleted
                tag_mat = m_tag.compiled_pat.match(
                    text, pos=pos
                )  # Avoiding catching preious tag patter for example <x:aa><y:aa> we will hit the same match again so we want to have a moving cursor to avoid that
                assert tag_mat != None
                tag_pat_text = tag_mat.group()
                tag_pat_len = len(tag_pat_text)

                if m_tag.tag_tp in {"TAJWEED", "TAJWEED_DEP"}:
                    mappings.insert_tajweed_rule_part(
                        pos,
                        pos,
                        pos + tag_pat_len,
                        m_tag.taj_tag,  # NOTE: the associated pivot (T) tag so a pivot and its deps share the same id
                        m_tag.dep_idx,
                        m_tag.num_deps,
                        self.taj_rule_type,
                        self.insert_taj_cond,
                        tajweed_rule_tag,  # NOTE: `tajweed_rule_tag` here is not the tag name but another thig raelate d to Tajweed rule we might need to rename it for disamiguity
                    )

                pos += tag_pat_len

        mappings.finalize(len(text), len(text))

        return mappings


@dataclass
class ConversionOperation:
    """A single phonetic conversion step built from precompiled tagged regex operations.

    Subclasses configure their work through :attr:`regs` and may override
    :meth:`forward` when patterns depend on runtime values such as ``moshaf``
    or ``sura_idx``. :meth:`apply` runs the operation and returns the new text
    together with an updated :class:`PhonetizerMappings`, which relates the
    original Uthmani characters to their spans in the phonetic text and to any
    attached Tajweed rules.

    For the full rules of the tagged ``M:`` patterns -- tag syntax, mapping and
    cardinality behavior, and Tajweed ``T``/``D`` tags -- see
    :meth:`QuranREWithMapping.__init__`.

    ``regs`` forms
    --------------
    ``regs`` accepts a single :class:`QuranREWithMapping` or a list of them; a
    single object is normalized to a list in :meth:`__post_init__`. Entries run
    in order. Each entry dispatches according to its mode:

    * ``QuranREWithMapping(pat, rep, tajweed_rule_type)`` - tagged substitution
      with an optional Tajweed rule, applied with
      :meth:`QuranREWithMapping.sub`.

      Example from ``BeginWithSaken``::

          QuranREWithMapping(
              f"M:<r:(^.){uth.ras_haaa}>",
              f"<r:\\1{uth.kasra}>",
              None,
          )

      Example from ``Qalqla``::

          QuranREWithMapping(
              f"M:<T:([{uth.qlqla_group}](?:{uth.shadda}$|{uth.ras_haaa}|$))>",
              f"<T:\\1{ph.qlqla}>",
              TajweedRuleType.QALQALAH,
          )

    * ``QuranREWithMapping(pat, None, tajweed_rule_type)`` - rule-only tagging:
      the text is not changed; ``pat`` is searched and the rule is attached to
      the affected span. Applied with
      :meth:`QuranREWithMapping.insert_tajweed`.

      Example from ``PrepareGhonnaIdghamIqlab``::

          QuranREWithMapping(
              f"M:<T:{uth.meem}>{uth.space}?<D0:{uth.meem}{uth.shadda}>",
              None,
              TajweedRuleType.IDGHAM_MEEM,
          )

    A rule-only entry may be mixed with substitutions in the same list; the loop
    continues with the next entry. :meth:`forward` dispatches each entry using
    :meth:`QuranREWithMapping.get_mode`.

    ``ops_before`` lists operations run first in ``"test"`` mode; entries whose
    ``arabic_name`` appears in ``discard_ops`` are skipped. In ``"inference"``
    mode only :meth:`forward` runs. :meth:`apply` initializes mappings from
    ``text`` when they are not provided.
    """

    regs: list[QuranREWithMapping]
    arabic_name: str
    ops_before: list["ConversionOperation"] | None = None

    def __post_init__(self):
        if type(self.regs) is not list:
            self.regs = [self.regs]

        if self.ops_before is None:
            self.ops_before = []

    def forward(
        self,
        text,
        moshaf: MoshafAttributes,
        mappings: PhonetizerMappings,
        sura_idx: int = 0,
    ) -> tuple[str, PhonetizerMappings]:
        """Apply each precompiled :class:`QuranREWithMapping` in ``regs``.

        Entries are applied in order. Substitution entries are run with
        :meth:`QuranREWithMapping.sub`; rule-only entries (``rep=None``) are run
        with :meth:`QuranREWithMapping.insert_tajweed`.

        Subclasses override this method when their patterns or replacements
        depend on runtime values such as ``moshaf`` or ``sura_idx``.

        Args:
            text: Input text to transform.
            moshaf: Recitation options used by runtime-dependent operations.
            mappings: Mappings to update and return.
            sura_idx (int): the sura index from 1 to 114. If zero then there is no sura set.
                Used when a specific rule is tied to a specific sura.
                This is used particularly if the user pronounced ONLY `ضَعْفًا` so we cannot infer whether this
                is from surah Alroom so we have two ways with damma or fatha; or from surah AlAnfal so we only
                pronounce it with fatha.

        Returns:
            A tuple of ``(text, mappings)``.
        """

        for reg in self.regs:
            match reg.get_mode():
                case "SUB":
                    text, mappings = reg.sub(text, mappings)
                case "INS_TAJ":
                    mappings = reg.insert_tajweed(text, mappings)

        return text, mappings

    def apply(
        self,
        text: str,
        moshaf: MoshafAttributes,
        mappings: PhonetizerMappings,
        sura_idx: int = 0,
        discard_ops: list["ConversionOperation"] = [],
        mode: Literal["inference", "test"] = "inference",
    ) -> tuple[str, PhonetizerMappings]:
        """Run this operation and return the transformed text with mappings.

        In ``"test"`` mode, ``ops_before`` operations are applied first, except
        those whose ``arabic_name`` appears in ``discard_ops``. In both
        ``"inference"`` and ``"test"`` modes, :meth:`forward` is then applied.

        Args:
            text: Input text to transform.
            moshaf: Recitation options used by runtime-dependent operations.
            mappings: Mappings to update. If ``None``, they are initialized
                from ``text``.
            sura_idx (int): the sura index from 1 to 114. If zero then there is no sura set.
                Used when a specific rule is tied to a specific sura.
                This is used particularly if the user pronounced ONLY `ضَعْفًا` so we cannot infer whether this
                is from surah Alroom so we have two ways with damma or fatha; or from surah AlAnfal so we only
                pronounce it with fatha.
            discard_ops: Operations in ``ops_before`` to skip in ``"test"``
                mode, matched by ``arabic_name``.
            mode: ``"inference"`` or ``"test"``.

        Returns:
            A tuple of ``(text, mappings)``.

        Raises:
            ValueError: If ``mode`` is neither ``"inference"`` nor ``"test"``.
        """

        if mappings is None:
            mappings = init_mappings(text)

        if mode == "test":
            discard_ops_names = {o.arabic_name for o in discard_ops}
            for op in self.ops_before:
                if op.arabic_name not in discard_ops_names:
                    print(f"Applying: {type(op)}")
                    text, mappings = op.apply(
                        text,
                        moshaf,
                        mappings,
                        sura_idx=sura_idx,
                        mode="test",
                        discard_ops=discard_ops,
                    )

        if mode in {"inference", "test"}:
            # TODO: Add real mapping
            new_text, new_mappings = self.forward(
                text, moshaf, mappings, sura_idx=sura_idx
            )
            return new_text, new_mappings
        else:
            raise ValueError(f"Invalid Model got: `{mode}`")
