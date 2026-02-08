from dataclasses import dataclass, field
import re
from typing import Literal, TypeAlias
from Levenshtein import opcodes

from .moshaf_attributes import MoshafAttributes
from .tajweed_rulses import TajweedRule


@dataclass
class MappingPos:
    pos: tuple[int, int]  # start, (pythonic exlusive end)
    tajweed_rules: list[TajweedRule] | None = None

    def add_tajweed_rule(self, new_tajweed_rule: TajweedRule | None) -> None:
        if self.tajweed_rules is not None and new_tajweed_rule is not None:
            self.tajweed_rules.append(new_tajweed_rule)


MappingListType: TypeAlias = list[MappingPos | None]


def merge_mappings(
    mappings: MappingListType | None, new_mappings: MappingListType
) -> MappingListType:
    """
    Merge character position mappings from original text with mappings after regex substitution.

    * This function maintains the relationship between character positions in the original text
    and their corresponding positions after one or more regex substitution operations.

    Args:
        mappings: Previous character position mappings from original text. Each MappingPos
                 represents a span (start, end) in the output text. `None` values indicate
                 previously deleted characters. If `None`, returns new_mappings unchanged.
        new_mappings: New character position mappings after the latest regex substitution.
                     `None` values represent characters deleted in this substitution.

    Returns:
        Merged position mappings maintaining the relationship between the original text
        and the final substituted text. The length matches the original mappings length.

    Logic:
        - For each non-None old mapping, searches its position range in new_mappings
        - Finds the first and last non-None mapping in that range
        - Creates a new MappingPos spanning from the first to last non-None position
        - If only start or end found, uses that position alone
        - Preserves None values for deleted characters

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
        >>> new = [MappingPos(pos=(0, 1)), None, MappingPos(pos=(2, 5))]
        >>> result = merge_mappings(old, new)
        # result: [MappingPos(pos=(0, 5))]  # spans first to last non-None
    """
    if mappings is None:
        return new_mappings

    # TODO: add Tajweed rules depencance
    merged_mappings = [None for _ in range(len(mappings))]
    for idx, old_map in enumerate(mappings):
        if old_map is not None:
            start_map = None
            end_map = None
            for start_map in new_mappings[old_map.pos[0] : old_map.pos[1]]:
                if start_map is not None:
                    break
            for end_map in new_mappings[old_map.pos[0] : old_map.pos[1]][::-1]:
                if end_map is not None:
                    break

            if start_map is not None and end_map is not None:
                merged_mappings[idx] = MappingPos(
                    pos=(start_map.pos[0], end_map.pos[1])
                )
            elif start_map is not None:
                merged_mappings[idx] = MappingPos(pos=start_map.pos)
            elif end_map is not None:
                merged_mappings[idx] = MappingPos(pos=end_map.pos)

    return merged_mappings


def get_mappings(
    text: str,
    new_text: str,
    mappings: MappingListType | None = None,
    tajweed_rule: TajweedRule | None = None,
) -> MappingListType:
    # TODO: need to write docstring
    """
    Examples:

        pattern: r"(a)"
        repl: r"\1\1\1"
        text: "abcd"
        tajweed_rule = NormalMadd()

        Output:
    (
        "aaabcd",
        [
            MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
            MappingPos(pos=(3, 4)),
            MappingPos(pos=(4, 5)),
            MappingPos(pos=(5, 6)),
        ],
    )


    ----------------
        pattern: r"d$"
        repl: r""
        text: "aaabcd"
        mappings:
            [
                MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
                MappingPos(pos=(3, 4)),
                MappingPos(pos=(4, 5)),
                MappingPos(pos=(5, 6)),
            ]

        Output:
    (
        "aaabc",
        [
            MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
            MappingPos(pos=(3, 4)),
            MappingPos(pos=(4, 5)),
            None,
        ],
    )
    ----------------

    """
    if text == "":
        return []

    # rev_mapings = {}
    # if mappings:
    #     for m_idx, map_pos in enumerate(mappings):
    #         if map_pos is not None:
    #             for idx in range(map_pos.pos[0], map_pos.pos[1]):
    #                 rev_mapings[idx] = m_idx

    # NOTE: Opcoes operation order is: equal, insert, replace
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
                            new_mappings[old_idx] = None
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
                            new_mappings[old_idx] = None
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
                    new_map_pos = MappingPos(pos=(new_idx, new_idx + 1))
                    new_map_pos.add_tajweed_rule(tajweed_rule)
                    new_mappings[old_idx] = new_map_pos

        elif curr_op[0] == "equal":
            for old_idx, new_idx in zip(
                range(curr_op[1], curr_op[2]), range(curr_op[3], curr_op[4])
            ):
                if new_mappings[old_idx] is None:
                    new_mappings[old_idx] = MappingPos(pos=(new_idx, new_idx + 1))
        elif curr_op[0] == "delete":
            ...

        # This not optimal but in case of noon or meem we want to delete the first letter and leave the next one
        # for example:
        # لكم ما
        # becomes
        # لكمَّا
        # We want to delete the first letter and keep the later
        for idx in range(1, len(text) - 1):
            if (
                (text[idx - 1] == text[idx + 1])
                and (text[idx] == " ")
                and (
                    new_mappings[idx - 1] is not None and new_mappings[idx + 1] is None
                )
            ):
                # swaping
                new_mappings[idx + 1] = new_mappings[idx - 1]
                new_mappings[idx - 1] = None

        last_op = curr_op
        curr_op = next_op

    new_mappings = merge_mappings(mappings, new_mappings)

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


def sub_with_mapping(
    pattern: str,
    repl,
    text: str,
    mappings: MappingListType | None = None,
    tajweed_rule: TajweedRule | None = None,
) -> tuple[str, MappingListType]:
    """
    Examples:

        pattern: r"(a)"
        repl: r"\1\1\1"
        text: "abcd"
        tajweed_rule = NormalMadd()

        Output:
    (
        "aaabcd",
        [
            MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
            MappingPos(pos=(3, 4)),
            MappingPos(pos=(4, 5)),
            MappingPos(pos=(5, 6)),
        ],
    )


    ----------------
        pattern: r"d$"
        repl: r""
        text: "aaabcd"
        mappings:
            [
                MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
                MappingPos(pos=(3, 4)),
                MappingPos(pos=(4, 5)),
                MappingPos(pos=(5, 6)),
            ]

        Output:
    (
        "aaabc",
        [
            MappingPos(pos=(0, 3), tajweed_rules=[NormalMadd()]),
            MappingPos(pos=(3, 4)),
            MappingPos(pos=(4, 5)),
            None,
        ],
    )
    ----------------

    """
    if text == "":
        return "", []

    # Apply the regex substitution
    new_text = re.sub(pattern, repl, text)
    new_mappings = get_mappings(text, new_text, mappings)
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
    regs: list[tuple[str, str]] | tuple[str, str]
    arabic_name: str
    ops_before: list["ConversionOperation"] | None = None

    def __post_init__(self):
        if isinstance(self.regs, tuple):
            self.regs = [self.regs]

        if self.ops_before is None:
            self.ops_before = []

    def forward(
        self,
        text,
        moshaf: MoshafAttributes,
        mappings: MappingListType | None = None,
    ) -> tuple[str, MappingListType]:
        for input_reg, out_reg in self.regs:
            text, mappings = sub_with_mapping(input_reg, out_reg, text, mappings)
        return text, mappings

    def apply(
        self,
        text: str,
        moshaf: MoshafAttributes,
        mappings: MappingListType | None,
        discard_ops: list["ConversionOperation"] = [],
        mode: Literal["inference", "test"] = "inference",
    ) -> tuple[str, MappingListType]:
        if mode == "test":
            discard_ops_names = {o.arabic_name for o in discard_ops}
            for op in self.ops_before:
                if op.arabic_name not in discard_ops_names:
                    print(f"Applying: {type(op)}")
                    text, mappings = op.apply(
                        text, moshaf, mappings, mode="test", discard_ops=discard_ops
                    )

        if mode in {"inference", "test"}:
            # TODO: Add real mapping
            new_text, new_mappings = self.forward(text, moshaf, mappings)
            return new_text, new_mappings
        else:
            raise ValueError(f"Invalid Model got: `{mode}`")
