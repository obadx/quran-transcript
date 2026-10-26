import re
from dataclasses import dataclass
from typing import Callable, Iterator, Literal, TypeAlias
from uuid import uuid4

from Levenshtein import opcodes

from .. import alphabet as alph
from .moshaf_attributes import MoshafAttributes
from .tajweed_rulses import TajweedRule, TajweedRuleMetadata, TajweedRuleType


@dataclass
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
    """

    pos: tuple[int, int]  # start, (pythonic exlusive end)
    tajweed_rules: list[TajweedRule] | None = None
    deleted: bool = False

    def add_tajweed_rule(
        self, new_tajweed_rules: TajweedRule | list[TajweedRule] | None
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
        if isinstance(new_tajweed_rules, TajweedRule):
            self.tajweed_rules.append(new_tajweed_rules)
        else:
            self.tajweed_rules.extend(new_tajweed_rules)


MappingListType: TypeAlias = list[MappingPos]


def merge_mappings(
    mappings: MappingListType | None, new_mappings: MappingListType
) -> MappingListType:
    """
    Merge character position mappings from original text with mappings after regex substitution.

    * This function maintains the relationship between character positions in the original text
    and their corresponding positions after one or more regex substitution operations.

    **Important:** This function **mutates** the input `mappings` list in‑place.
    It updates each `MappingPos` object with a new `pos` tuple and a new `deleted`
    flag, and also merges the tajweed rules from the corresponding entries in
    `new_mappings`. The length of the list remains unchanged.

    Args:
        mappings: Previous character position mappings from original text. Each MappingPos
                 represents a span (start, end) in the output text. `None` values indicate
                 previously deleted characters. If `None`, returns new_mappings unchanged.
        new_mappings: New character position mappings after the latest regex substitution.
                     `None` values represent characters deleted in this substitution.

    Returns:
        Merged position mappings maintaining the relationship between the original text
        and the final substituted text. The length matches the original mappings length.

    Raises:
        ValueError: if `new_mappings` is an empty list



    Examples:
        # Identity mapping - no change
        >>> old = [MappingPos(pos=(0, 1)), MappingPos(pos=(1, 2))]
        >>> new = [MappingPos(pos=(0, 1)), MappingPos(pos=(1, 2))]
        >>> result = merge_mappings(old, new)
        # result: [MappingPos(pos=(0, 1)), MappingPos(pos=(1, 2))]

        # Expansion - single character expands to range
        >>> old = [MappingPos(pos=(0, 1))]
        >>> new = [MappingPos(pos=(0, 3))]
        >>> result = merge_mappings(old, new)
        # result: [MappingPos(pos=(0, 3))]

        # Contraction with deletions - range contracts with None values
        >>> old = [MappingPos(pos=(0, 3))]
        >>> new = [MappingPos(pos=(0, 1)), MappingPos(pos=(1, 1), deleted=True), MappingPos(pos=(1, 5))]
        >>> result = merge_mappings(old, new)
        # result: [MappingPos(pos=(0, 5))]  # spans first to last
    """

    if mappings is None:
        return new_mappings

    if new_mappings == []:
        raise ValueError("`new_mappings` should not be an empty list")

    for idx in range(len(mappings)):
        old_map = mappings[idx]
        if old_map is None:
            raise ValueError()
        start = old_map.pos[0]
        end = old_map.pos[1]

        if old_map.deleted:
            if start < len(new_mappings):
                mappings[idx].pos = (
                    new_mappings[start].pos[0],
                    new_mappings[start].pos[0],
                )
            else:
                mappings[idx].pos = (
                    new_mappings[-1].pos[1],
                    new_mappings[-1].pos[1],
                )

        else:
            mappings[idx].pos = (
                new_mappings[start].pos[0],
                new_mappings[end - 1].pos[1],
            )

        deleted = True
        for new_idx in range(start, end):
            mappings[idx].add_tajweed_rule(new_mappings[new_idx].tajweed_rules)
            deleted = deleted and new_mappings[new_idx].deleted
        mappings[idx].deleted = deleted

    return mappings


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

    def finalize(self):

        un_shifted_keys = list(self.old_map.keys())
        for idx in un_shifted_keys:
            parts = self.old_map.pop(idx)
            self.new_map.setdefault(idx, []).extend(parts)

        self.old_map = self.new_map
        self.new_map = {}

    def __iter__(self) -> Iterator[TajweedRulePart]:
        """The iterator should be called after finalize"""
        sorted_keys = sorted(self.old_map.keys())
        for idx in sorted_keys:
            yield from self.old_map[idx]

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
        if shift_val == 0 or self.old_map == {}:
            return

        for idx in range(old_start, old_end):
            new_idx = idx + shift_val
            if idx in self.old_map:
                parts = self.old_map.pop(idx)

                # updating the idx
                for p_idx in range(len(parts)):
                    parts[p_idx].ph_idx = new_idx

                self.new_map.setdefault(new_idx, []).extend(parts)

    def delete_shift(self, old_start: int, old_end: int, new_idx: int) -> None:
        """Not acully deleting but moving old idx and concatenate them to the new index
        Args:
            start (int): inclusive
            end (int): execlusive

        """
        if old_end - 1 == new_idx or self.old_map == {}:
            return

        for idx in range(old_start, old_end):
            if idx in self.old_map:
                parts = self.old_map.pop(idx)
                # updating the idx
                for p_idx in range(len(parts)):
                    parts[p_idx].ph_idx = new_idx

                self.new_map.setdefault(new_idx, []).extend(parts)


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

    def __len__(self):
        return len(self.uth_to_ph)

    def __post_init__(self):
        self._prev_pos: tuple[int, int] = (-1, -1)
        self._uth_start: int = -1
        self._taj_to_id = {}
        self._taj_parts = TajweedRulePartContainer()
        self._taj_to_first_to_watch: dict[str, Literal["TAJ", "DEP"]] = {}

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

    def find_uth_idx_or_deleted_end(self, curr_ph_pos_idx: int) -> int:
        self.init_uth_start(curr_ph_pos_idx)

        found_uth_idx = -1
        for uth_idx in range(self._uth_start, len(self.uth_to_ph)):
            if uth_idx == self._uth_start and self._is_uth_start_altered():
                start, end = self._prev_pos
            else:
                start, end = self.uth_to_ph[uth_idx].pos

            if (
                curr_ph_pos_idx >= start
                and curr_ph_pos_idx < end
                or (start == end and (curr_ph_pos_idx + 1) == start)
            ):
                found_uth_idx = uth_idx

        if found_uth_idx == -1:
            raise ValueError("Can not find uth_idx")
        else:
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
        uth_end = self.find_uth_idx_or_deleted_end(
            curr_ph_pos_start + N - 1
        )  # end is inclusive

        # assert self._is_uth_start_altered(), "a shift occured it has to be altered"

        # skiping start as it was altered
        if uth_start == self._uth_start:
            uth_start += 1

        shift = new_ph_pos_start - curr_ph_pos_start
        prev_pos = (-1, -1)
        for uth_idx in range(uth_start, uth_end + 1):
            prev_pos = self.uth_to_ph[uth_idx].pos
            self.uth_to_ph[uth_idx].pos = (
                self.uth_to_ph[uth_idx].pos[0] + shift,
                self.uth_to_ph[uth_idx].pos[1] + shift,
            )
        # Updatign our self._uth_start (states)
        if prev_pos[0] != -1:
            # A change happend so we need to udpate the:
            # self_uth_start and self._prev_pos
            self._uth_start = uth_idx
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
        uth_end = self.find_uth_idx_or_deleted_end(
            curr_ph_pos_start + N - 1
        )  # end is inclusive

        shift = new_ph_pos_start - curr_ph_pos_start
        prev_pos = (-1, -1)
        for uth_idx in range(uth_start, uth_end + 1):
            prev_pos = self.uth_to_ph[uth_idx].pos
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
        if prev_pos[0] != -1:
            # A change happend so we need to udpate the:
            # self_uth_start and self._prev_pos
            self._uth_start = uth_idx
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
    def ph_to_taj_rules(self):
        return self.get_ph_to_tajweed_rules()


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
                out_str += match.group(part.grp_id)
            case "NAME":
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


def sub_with_tagged_mapping(
    pat: str,
    rep: str,
    text: str,
    mappings: PhonetizerMappings,
    tajweed_rule_type: TajweedRuleType | None = None,
    insert_tajweed_cond: Callable[[list[TajweedRuleType], TajweedRuleType], bool]
    | None = None,
    tajweed_rule_tag: str = "",
) -> tuple[str, PhonetizerMappings]:
    """
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

    assert mappings is not None
    assert pat.startswith("M:")
    pat = pat[2:]

    out_text = ""
    mapped_tags = parse_tags(pat, rep)
    re_pat = ""
    for m_tag in mapped_tags:
        re_pat += m_tag.pat

    re_pat = re.compile(re_pat)

    in_pos = 0
    out_pos = 0
    shifted = False
    mappings.reset()
    for match in re_pat.finditer(text):
        out_text += text[in_pos : match.start()]  # text not cpatured by the pat

        keep_num = match.start() - in_pos
        # shifting mappings
        if shifted:
            mappings.shift(in_pos, out_pos, keep_num)

        in_pos = match.start()
        out_pos += keep_num
        for m_tag in mapped_tags:
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
                    shifted = True
                    # one to many
                    mappings.update_ph_one_to_many(in_pos, out_pos, tag_rep_len)
                elif tag_pat_text[:min_both_len] == tag_rep_text[:min_both_len]:
                    if tag_rep_len > tag_pat_len:
                        # insert
                        shifted = True
                        if shifted:
                            mappings.shift(in_pos, out_pos, min_both_len - 1)
                        mappings.update_ph_one_to_many(
                            in_pos + min_both_len - 1,
                            out_pos + min_both_len - 1,
                            tag_rep_len - min_both_len + 1,
                        )
                    else:
                        # delete
                        shifted = True
                        if shifted:
                            mappings.shift(in_pos, out_pos, min_both_len)
                        mappings.delete_shift(
                            in_pos + min_both_len,
                            out_pos + min_both_len,
                            tag_pat_len - tag_rep_len,
                        )

                else:
                    raise MappedTagPrasingCardinalityError(
                        f"Not supporting many to many or many to one mapping you want to map: `{tag_pat_text}` to `{tag_rep_text}` corresponds to tag: `{m_tag}`"
                    )
            elif m_tag.rep_parts == [] and tag_pat_len > 0:
                # the tag_pat_len for regs that are zero lenght like `z?`
                # Deletion
                shifted = True
                tag_rep_text = ""
                mappings.delete_shift(in_pos, out_pos, tag_pat_len)

            if m_tag.tag_tp in {"TAJWEED", "TAJWEED_DEP"}:
                mappings.insert_tajweed_rule_part(
                    in_pos,
                    out_pos,
                    out_pos + len(tag_rep_text),
                    m_tag.taj_tag,  # NOTE: the associated pivot (T) tag so a pivot and its deps share the same id
                    m_tag.dep_idx,
                    m_tag.num_deps,
                    tajweed_rule_type,
                    insert_tajweed_cond,
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


def add_tajweed_rule_with_tagged_pat(
    pat: str,
    text: str,
    mappings: PhonetizerMappings,
    tajweed_rule_type: TajweedRuleType | None = None,
    insert_tajweed_cond: Callable[[list[TajweedRuleType], TajweedRuleType], bool]
    | None = None,
    tajweed_rule_tag: str = "",
) -> PhonetizerMappings:
    """Same ruels as the `sub_with_tagged_mapping` but with no `rep`. Just adding tajweed rules to mappings"""

    assert pat.startswith("M:")
    pat = pat[2:]

    mapped_tags = parse_tags(pat, "")
    re_pat = ""
    for m_tag in mapped_tags:
        re_pat += m_tag.pat

    re_pat = re.compile(re_pat)

    mappings.reset()
    for match in re_pat.finditer(text):
        pos = match.start()
        for m_tag in mapped_tags:
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
                    tajweed_rule_type,
                    insert_tajweed_cond,
                    tajweed_rule_tag,  # NOTE: `tajweed_rule_tag` here is not the tag name but another thig raelate d to Tajweed rule we might need to rename it for disamiguity
                )

            pos += tag_pat_len

    mappings.finalize(len(text), len(text))

    return mappings


def get_mappings(
    text: str,
    new_text: str,
    mappings: MappingListType | None = None,
    tajweed_rule: TajweedRule | None = None,
) -> MappingListType:
    """Generate character position mappings between original and transformed text.

    The function is essential for maintaining character-level precision in Quranic text
    processing, particularly when converting between Uthmani script and phonetic
    transcription. It can associate tajweed rules with affected character spans and
    merge with existing mappings from previous transformations.

    **Important:** This function **mutates** the input `mappings` list in‑place.
    It updates each `MappingPos` object with a new `pos` tuple and a new `deleted`
    flag, and also merges the tajweed rules from the corresponding entries in
    `new_mappings`. The length of the list remains unchanged.

    Args:
        text: Original input text before transformation.
        new_text: Transformed text after operation (e.g., regex substitution).
        mappings: Existing character position mappings from previous transformations.
            Each MappingPos represents a span in intermediate text. None values
            indicate previously deleted characters. If None, creates fresh mappings.
        tajweed_rule: TajweedRule to associate with characters affected by this
            transformation. Can be None if no tajweed rule should be applied.

    Returns:
        List of MappingPos objects tracking character positions from original to
        transformed text. Length matches original text length. `MappingPos(pos=(x, x), deleted=True)`
        values indicate deleted characters, while MappingPos objects contain position spans and
        associated tajweed rules.

    Raises:
        AssertionError: if one of the generated mappings is `None`
        ValueError: If mapping continuity validation fails (detected gaps in position
            mappings that should be contiguous).

    Algorithm Details:
        The function uses Levenshtein opcodes in the order: equal, insert, replace
        to analyze differences between texts. It handles several special cases:

        1. **Madd Alif expansions**: abcd → aaabcd (equal[a] + insert[a])
        2. **Madd Alif with tashkeel**: abcd → aaaacd (equal + insert + replace)
        3. **Complete replacements**: abcd → kkkabcd
        4. **Shadda transformations**: Special handling for noon/meem with shadda
           in Quranic orthography (e.g., "لكم ما" → "لكمَّا")

    Examples:
        Basic character expansion:
        >>> text = "abcd"
        >>> new_text = "aaabcd"
        >>> mappings = get_mappings(text, new_text)
        >>> mappings[0].pos  # First 'a' expanded to position (0, 3)
        (0, 3)
        >>> mappings[1].pos  # Second character at position (3, 4)
        (3, 4)

        Quranic text transformation with alif elongation:
        >>> text = "بِسْمِ لَّاهِ" # len 13
        >>> new_text = "بِسْمِ لَّااهِ" # len 14
        >>> mappings = get_mappings(text, new_text)
        >>> len(mappings)  # Same length as original text
        13
        >>> mappings[10].pos  # 2 beats madd
        (10, 12)

        Complex transformation with existing mappings and tajweed rule:
        >>> existing_mappings = [MappingPos(pos=(0, 1)), MappingPos(pos=(1, 2))]
        >>> text = "ab"
        >>> new_text = "aab"
        >>> tajweed_rule = NormalMadd()  # Some tajweed rule instance
        >>> mappings = get_mappings(text, new_text, existing_mappings, tajweed_rule)
        >>> mappings[0].pos  # First 'a' maps to (0, 2) with tajweed rule
        (0, 2)
        >>> mappings[0].tajweed_rules
        NormalMadd()

        Character deletion:
        >>> text = "abcd"
        >>> new_text = "abc"
        >>> mappings = get_mappings(text, new_text)
        >>> mappings[-1]  # Last character deleted
        MappingsPos(pos=(3,3), deleted=True)

    Note:
        - Character positions use Python-style slice notation (inclusive start, exclusive end)
        - `MappingPos(pos=(x, x), deleted=True)` values in mappings indicate deleted characters
        - Tajweed rules are associated with affected character spans when provided
        - The function validates mapping continuity and raises errors on inconsistencies
        - Special handling exists for Quranic orthographic patterns like shadda
    """
    if text == "":
        return []

    # NOTE: Opcoes operation order is: equal, insert, replace, delete
    ops = opcodes(text, new_text)
    """
    to_overwrite_tajweed_rules: if a rule in the future occupy in the same span ignore the new rule in the `to_overwrite_tajweed_rules` and keep the old rule
    Cases:

    * Madd ALif Complete partial replacement:
    abcd -> aaabcd (equal[a] + insert[a]) or (insert[a] + equal[a])

    * Madd Alif with ~:
    abcd -> aaaacd (equal + insert + replace) && insert[0] == last_eqaul == replace[0]

    * Complete replacement
    abcd -> kkkabcd (replace or insert + replace or replace + insert)

    * Complete Deletion
    * abcd -> abc
    """
    new_mappings: list[None | MappingPos] = [None] * len(text)

    last_op = None
    curr_op = ops[0]
    next_op = ops[1] if len(ops) > 1 else None
    to_del_poses = set()
    for op_idx in range(len(ops)):
        next_op = ops[op_idx + 1] if len(ops) > (op_idx + 1) else None
        if curr_op[0] == "insert":
            eq_ins_same = False
            eq_ins_not_same = False
            if last_op is not None:
                # equal before
                if (
                    last_op[0] == "equal"
                    and new_text[last_op[4] - 1] == new_text[curr_op[3]]
                ):
                    # increae the end pos to append the insert
                    new_mappings[last_op[2] - 1].pos = (
                        new_mappings[last_op[2] - 1].pos[0],
                        curr_op[4],
                    )
                    new_mappings[last_op[2] - 1].add_tajweed_rule(tajweed_rule)
                    eq_ins_same = True
                elif last_op[0] == "equal":
                    eq_ins_not_same = True

            if next_op is not None:
                # equal + insert + replace
                if eq_ins_same:
                    # equal before
                    if (
                        next_op[0] == "replace"
                        and new_text[curr_op[4] - 1] == new_text[next_op[3]]
                    ):
                        # #increase the end
                        new_mappings[last_op[2] - 1].pos = (
                            new_mappings[last_op[2] - 1].pos[0],
                            next_op[4],
                        )
                        # increae the end pos to append the insert
                        for old_idx in range(next_op[1], next_op[2]):
                            new_mappings[old_idx] = MappingPos(
                                pos=(next_op[4], next_op[4]), deleted=True
                            )
                            to_del_poses.add(old_idx)
                # insert + replace
                else:
                    if (
                        next_op[0] == "replace"
                        # and new_text[curr_op[4] - 1] == new_text[next_op[3]]
                    ):
                        # increae the end pos to append the insert
                        new_map_pos = MappingPos(pos=(curr_op[3], next_op[4]))
                        new_map_pos.add_tajweed_rule(tajweed_rule)
                        new_mappings[next_op[1]] = new_map_pos
                        # assignign the rest to None
                        for old_idx in range(next_op[1] + 1, next_op[2]):
                            new_mappings[old_idx] = MappingPos(
                                pos=(next_op[4], next_op[4]), deleted=True
                            )
                            to_del_poses.add(old_idx)

                    # equal only
                    else:
                        # insert + equal (same)
                        assert next_op[0] == "equal"
                        if new_text[curr_op[4] - 1] == new_text[next_op[3]]:
                            # add this operation to the next equal
                            new_mappings[next_op[1]] = MappingPos(
                                pos=(curr_op[3], next_op[3] + 1)
                            )
                            new_mappings[next_op[1]].add_tajweed_rule(tajweed_rule)

                        elif eq_ins_not_same:
                            # add this insert to the last equal
                            new_mappings[last_op[2] - 1].pos = (
                                new_mappings[last_op[2] - 1].pos[0],
                                curr_op[4],
                            )
                            new_mappings[last_op[2] - 1].add_tajweed_rule(tajweed_rule)

                        else:
                            # add this operation to the next equal
                            new_mappings[next_op[1]] = MappingPos(
                                pos=(curr_op[3], next_op[3] + 1)
                            )
                            new_mappings[next_op[1]].add_tajweed_rule(tajweed_rule)

            # The insert is the last item
            elif eq_ins_not_same:
                # increae the end pos to append the insert
                new_mappings[last_op[2] - 1].pos = (
                    new_mappings[last_op[2] - 1].pos[0],
                    curr_op[4],
                )
                new_mappings[last_op[2] - 1].add_tajweed_rule(tajweed_rule)

        elif curr_op[0] == "replace":
            for old_idx, new_idx in zip(
                range(curr_op[1], curr_op[2]), range(curr_op[3], curr_op[4])
            ):
                if new_mappings[old_idx] is None and old_idx not in to_del_poses:
                    if text[old_idx] != alph.uthmani.space:
                        new_map_pos = MappingPos(pos=(new_idx, new_idx + 1))
                        new_map_pos.add_tajweed_rule(tajweed_rule)
                        new_mappings[old_idx] = new_map_pos
                    else:
                        # Move mappings assingesd to space to the last pos
                        new_mappings[old_idx] = MappingPos(
                            pos=(new_idx + 1, new_idx + 1), deleted=True
                        )
                        new_mappings[old_idx - 1].pos = (
                            new_mappings[old_idx - 1].pos[0],
                            new_idx + 1,
                        )

        elif curr_op[0] == "equal":
            for old_idx, new_idx in zip(
                range(curr_op[1], curr_op[2]), range(curr_op[3], curr_op[4])
            ):
                if new_mappings[old_idx] is None:
                    new_mappings[old_idx] = MappingPos(pos=(new_idx, new_idx + 1))
        elif curr_op[0] == "delete":
            for old_idx in range(curr_op[1], curr_op[2]):
                new_mappings[old_idx] = MappingPos(
                    pos=(curr_op[3], curr_op[3]), deleted=True
                )
                new_mappings[old_idx].add_tajweed_rule(tajweed_rule)

        last_op = curr_op
        curr_op = next_op

    # TODO: remove this
    assert all(m is not None for m in new_mappings)

    # Special case where we have Idgham tanween
    # Special sympol `tanweed_idgham_detrminer` has no meaning moving it to the tanween
    for re_out in re.finditer(f"{alph.uthmani.tanween_idhaam_dterminer}[^$]", text):
        idx = re_out.span()[0]
        if text[idx] != new_text[new_mappings[idx].pos[0]]:
            new_mappings[idx - 1].pos = (
                new_mappings[idx - 1].pos[0],
                new_mappings[idx].pos[1],
            )
            new_mappings[idx].pos = new_mappings[idx].pos[1], new_mappings[idx].pos[1]
            new_mappings[idx].deleted = True

    # This not optimal but in case of إدغام كامل we want to delete the first letter and leave the next one
    # for example:
    # لكم ما
    # becomes
    # لكمَّا
    # We want to delete the first letter and keep the later
    for re_out in re.finditer(
        f"([^{alph.uthmani.space}]){alph.uthmani.space}?\\1{alph.uthmani.shadda}", text
    ):
        first = re_out.span()[0]
        second = re_out.span()[1] - 2
        if (not new_mappings[first].deleted) and new_mappings[second].deleted:
            # Swapping
            new_mappings[second] = new_mappings[first]
            # first and space if exists
            for idx in range(first, second):
                new_mappings[idx] = MappingPos(
                    pos=(new_mappings[second].pos[0], new_mappings[second].pos[0]),
                    deleted=True,
                )

    new_mappings = merge_mappings(mappings, new_mappings)

    # Special case where skoon sign is repaced with qalalah sign
    # We want the qalqlah sign associated with the letter it self not the
    # Did not want that but no way to solve exept with this
    for re_out in re.finditer(
        f"[^{alph.uthmani.ras_haaa}{alph.uthmani.shadda}]({alph.phonetics.qlqla})",
        new_text,
    ):
        qlq_idx = re_out.span(1)[0]
        char_idx = qlq_idx - 1
        # getting skon or shadda idx in the merged mappings
        m_idx = 0
        for m_idx in range(len(new_mappings)):
            if new_mappings[m_idx].pos[0] == qlq_idx:
                break
        # Avodig the case where we have qalqlah at the end with no (shadda or skonJ)
        if new_mappings[m_idx - 1].tajweed_rules is None:
            new_mappings[m_idx - 1].pos = (
                new_mappings[m_idx - 1].pos[0],
                new_mappings[m_idx].pos[1],
            )
            new_mappings[m_idx - 1].tajweed_rules = new_mappings[m_idx].tajweed_rules
            new_mappings[m_idx].pos = (
                new_mappings[m_idx].pos[1],
                new_mappings[m_idx].pos[1],
            )
            new_mappings[m_idx].deleted = True
            new_mappings[m_idx].tajweed_rules = None

    # TODO: remove this
    curr_m = None
    next_m = None
    for idx in range(len(new_mappings)):
        curr_m = new_mappings[idx]
        if curr_m is None:
            continue
        n_idx = idx
        if (idx + 1) == len(new_mappings):
            next_m = MappingPos(pos=(len(new_text), -1))
            n_idx = None
        else:
            n_idx = idx
            for next_m in new_mappings[idx + 1 :]:
                if next_m is not None:
                    break
                n_idx += 1
            if next_m is None:
                next_m = MappingPos(pos=(len(new_text), -1))
                n_idx = None

        if curr_m.pos[1] != next_m.pos[0]:
            start = curr_m.pos[1]
            end = next_m.pos[0]
            print(f"IN MAPPINGS\n{mappings}")
            print(f"OUT MAPPINGS\n{new_mappings}")
            print("ERROR HERE")
            print(curr_m, next_m, n_idx)
            print(f"LEN_OLD_TEXT: {len(text)}")
            print(f"LEN_NEW_TEXT: {len(new_text)}")
            print(new_text[start:end])
            print(new_text[max(start - 1, 0) : end + 1])
            print(text)
            print(new_text)
            raise ValueError()

    return new_mappings


def add_tajweed_rule_to_mappings(
    mappings: MappingListType, text: str, pattern: str, tajweed_rule: TajweedRule
) -> MappingListType:
    """Add a TajweedRule to an existing mapping without changing the mapping itself

    Add a TajweedRule to an existing mapping without changing the mapping
    itself but by searching througt text and add the mapping to the  first re_group

    Note: the group have to point to a single character ONLY not group of character
    """
    m_start_idx = 0
    for re_out in re.finditer(pattern, text):
        assert len(re_out.groups()) == 1, (
            f"We must have only one group of matching got: `{len(re_out.groups())}`"
        )
        end = re_out.end(1)
        start = re_out.start(1)
        assert end - start == 1, (
            f"Lenght of group 1 of re has to be 1 got `{end - start}`"
        )
        for m_idx in range(m_start_idx, len(mappings)):
            # mappings[m_idx].pos[0] != mappings[m_idx].pos[1] means that
            # the character is deleted so no need to add Tajweed rule to it
            if (
                start >= mappings[m_idx].pos[0]
                and start < mappings[m_idx].pos[1]
                and mappings[m_idx].pos[0] != mappings[m_idx].pos[1]
            ):
                m_start_idx = m_idx
                mappings[m_idx].add_tajweed_rule(tajweed_rule)
                break
    return mappings


def sub_with_mapping(
    pattern: str,
    repl,
    text: str,
    mappings: MappingListType | None = None,
    tajweed_rule: TajweedRule | None = None,
) -> tuple[str, MappingListType]:
    """Perform regex substitution while maintaining character position mappings.

    This function applies a regex substitution to the input text and tracks how character
    positions change during the transformation. It maintains the relationship between
    the original text and the transformed text, allowing for precise mapping of each
    character to its new position. Additionally, it can associate tajweed rules with
    specific character spans that are affected by the substitution.

    The function uses Levenshtein opcodes to analyze the differences between the
    original and transformed text, handling various operations like insertions,
    replacements, deletions, and combinations thereof.

    Args:
        pattern: Regular expression pattern to match in the input text.
        repl: Replacement string (can contain backreferences like r"\1\1\1").
        text: Input text to transform.
        mappings: Existing character position mappings from previous transformations.
            Each MappingPos represents a span in the intermediate text. None values
            indicate previously deleted characters. If None, creates new mappings.
        tajweed_rule: TajweedRule to associate with characters affected by this
            substitution. Can be None if no tajweed rule should be applied.

    Returns:
        Tuple containing:
        - Transformed text after applying the regex substitution
        - Updated position mappings maintaining relationship from original text to
          the final transformed text. Length matches original text length.

    Examples:
        Pattern expansion - tripling a character with tajweed rule:
        >>> pattern = r"(a)"
        >>> repl = r"\1\1\1"
        >>> text = "abcd"
        >>> tajweed_rule = NormalMadd()  # Some tajweed rule instance
        >>> result_text, result_mappings = sub_with_mapping(pattern, repl, text, None, tajweed_rule)
        >>> result_text
        'aaabcd'
        >>> result_mappings[0].pos  # First character 'a' expanded to position (0, 3)
        (0, 3)

        Deletion with existing mappings:
        >>> pattern = r"d$"
        >>> repl = r""
        >>> text = "aaabcd"
        >>> existing_mappings = [
        ...     MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
        ...     MappingPos(pos=(3, 4)),
        ...     MappingPos(pos=(4, 5)),
        ...     MappingPos(pos=(5, 6)),
        ... ]
        >>> result_text, result_mappings = sub_with_mapping(pattern, repl, text, existing_mappings)
        >>> result_text
        'aaabc'
        >>> result_mappings[-1]  # Last character deleted
        None

    Note:
        - The function handles complex regex operations including backreferences
        - Character positions use Python-style slice notation (inclusive start, exclusive end)
        - None values in mappings indicate deleted characters
        - Tajweed rules are associated with affected character spans when provided
    """
    if text == "":
        return "", []

    # Apply the regex substitution
    new_text = re.sub(pattern, repl, text)
    # If no changes occur, then skip remapping
    if new_text == text and mappings is not None:
        return text, mappings
    new_mappings = get_mappings(text, new_text, mappings, tajweed_rule=tajweed_rule)
    return new_text, new_mappings


# class FilterTages(StrEnum):
#     # المدود
#     MADD = "مد"
#     MADD_NORMAL = "مد طبيعي"
#     MADD_EWAD = ""
#     MADD_MONFASel = ""
#     MADD_MOTTASel = ""
#     MADD_LAZEM = ""
#     MADD_MOTTASEL_PUASE = ""
#     MADD_ARRED = ""
#
#
# @dataclass
# class SubOperation:
#     tags: list[FilterTages] = field(default_factory=lambda: [])


@dataclass
class ConversionOperation:
    regs: (
        list[
            tuple[str, TajweedRuleType]
            | tuple[str, str, TajweedRuleType]
            | tuple[str, str]
        ]
        | tuple[str, TajweedRuleType]
        | tuple[str, str, TajweedRuleType]
        | tuple[str, str]
    )
    """Regex substitution operations applied by :meth:`forward`.

    `regs` accepts either a single operation tuple or a list of operation
    tuples. In :meth:`__post_init__` a plain tuple is wrapped in a list, so
    internally it is always a ``list``. Each entry is one of three forms,
    executed in order:

    * ``(input_regex, output_regex)`` — Plain substitution. ``input_regex``
      is the pattern to match in the text and ``output_regex`` is the
      replacement string (may use backreferences like ``r"\\1"``). No
      Tajweed rule is attached. Applied via :func:`sub_with_mapping`.

      Example (from ``BeginWithSaken``):
      ``(f"(^.){uth.ras_haaa}", f"\\1{uth.kasra}")``

    * ``(input_regex, output_regex, tajweed_rule)`` — Substitution that also
      associates ``tajweed_rule`` with the characters affected by the match.
      Applied via :func:`sub_with_mapping`.

      Example (from ``Qalqla``):
      ``(f"([{uth.qlqla_group}])", f"\\1{ph.qlqla}", Qalqalah())``

    * ``(pattern, tajweed_rule)`` — Rule-only tagging. The text is **not**
      changed; ``pattern`` is searched in the current text and
      ``tajweed_rule`` is added to the mappings of the captured character
      (the pattern must contain exactly one group capturing exactly one
      character). Applied via :func:`add_tajweed_rule_to_mappings`. Because
      :meth:`forward` returns immediately after this form, it must be the
      only entry in ``regs``.

      Example: ``(f"({uth.alif}{uth.madd})", NormalMaddRule())``

    Any other tuple length raises ``ValueError``.
    """
    arabic_name: str
    ops_before: list["ConversionOperation"] | None = None

    def __post_init__(self):
        if type(self.regs) is tuple:
            self.regs = [self.regs]

        if self.ops_before is None:
            self.ops_before = []

    def forward(
        self,
        text,
        moshaf: MoshafAttributes,
        mappings: MappingListType,
        sura_idx: int = 0,
    ) -> tuple[str, MappingListType]:
        """
        Args:
            sura_idx (int): the sura index from 1 to 114. If zero then there is no sura set.
                Used when a specific rule is tied to a specific sura.
                This is used particularly if the user pronounced ONLY `ضَعْفًا` so we cannot infer whether this
                is from surah Alroom so we have two ways with damma or fatha; or from surah AlAnfal so we only
                pronounce it with fatha.
        """

        for reg in self.regs:
            if len(reg) == 2:
                if type(reg[1]) is str:
                    input_reg, out_reg = reg
                else:
                    assert mappings is not None
                    if reg[0].startswith("M:"):
                        if isinstance(mappings, list):
                            mappings = PhonetizerMappings(uth_to_ph=mappings)
                        mappings = add_tajweed_rule_with_tagged_pat(
                            reg[0],
                            text,
                            mappings,
                            reg[1],
                        )
                    else:
                        mappings = add_tajweed_rule_to_mappings(
                            mappings=mappings,
                            pattern=reg[0],
                            text=text,
                            tajweed_rule=reg[1],
                        )
                    continue
                taj_rule = None
            elif len(reg) == 3:
                input_reg, out_reg, taj_rule = reg
            else:
                raise ValueError("Invalid Input")

            if input_reg.startswith("M:"):
                if isinstance(mappings, list):
                    mappings = PhonetizerMappings(uth_to_ph=mappings)
                text, mappings = sub_with_tagged_mapping(
                    input_reg,
                    out_reg,
                    text,
                    mappings,
                    taj_rule,
                )
            else:
                text, mappings = sub_with_mapping(
                    input_reg, out_reg, text, mappings, tajweed_rule=taj_rule
                )
        return text, mappings

    def apply(
        self,
        text: str,
        moshaf: MoshafAttributes,
        mappings: MappingListType | None,
        sura_idx: int = 0,
        discard_ops: list["ConversionOperation"] = [],
        mode: Literal["inference", "test"] = "inference",
    ) -> tuple[str, MappingListType]:
        """
        Args:
            sura_idx (int): the sura index from 1 to 114. If zero then there is no sura set.
                Used when a specific rule is tied to a specific sura.
                This is used particularly if the user pronounced ONLY `ضَعْفًا` so we cannot infer whether this
                is from surah Alroom so we have two ways with damma or fatha; or from surah AlAnfal so we only
                pronounce it with fatha.
        """
        # TODO: only using mappinsg no None
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
