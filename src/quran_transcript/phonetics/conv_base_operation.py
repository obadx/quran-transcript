from dataclasses import dataclass, field
import re
from typing import Literal, TypeAlias
from Levenshtein import opcodes

from .moshaf_attributes import MoshafAttributes
from .tajweed_rulses import TajweedRule
from .. import alphabet as alph


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

    # Special Case where we want to assgin the tag for Leen Madd
    for m_idx in range(len(new_mappings)):
        if new_mappings[m_idx].tajweed_rules:
            for taj_idx in range(len(new_mappings[m_idx].tajweed_rules)):
                if (
                    new_mappings[m_idx].tajweed_rules[taj_idx].name.en == "Leen Madd"
                    and new_mappings[m_idx].tajweed_rules[taj_idx].tag is None
                ):
                    tag = (
                        new_mappings[m_idx]
                        .tajweed_rules[taj_idx]
                        ._madd_to_tag[new_text[new_mappings[m_idx].pos[0]]]
                    )
                    new_mappings[m_idx].tajweed_rules[taj_idx].tag = tag

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
            print("here")
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
    regs: list[tuple[str, str]] | tuple[str, str]
    arabic_name: str
    tajweed_rules: list[TajweedRule | None] | TajweedRule | None = None
    ops_before: list["ConversionOperation"] | None = None

    def __post_init__(self):
        if isinstance(self.regs, tuple):
            self.regs = [self.regs]

        if self.ops_before is None:
            self.ops_before = []

        if self.tajweed_rules:
            if not isinstance(self.tajweed_rules, list):
                self.tajweed_rules = [self.tajweed_rules]
        else:
            self.tajweed_rules = [None for _ in range(len(self.regs))]

    def forward(
        self,
        text,
        moshaf: MoshafAttributes,
        mappings: MappingListType | None = None,
    ) -> tuple[str, MappingListType]:
        for (input_reg, out_reg), taj_rule in zip(self.regs, self.tajweed_rules):
            text, mappings = sub_with_mapping(
                input_reg, out_reg, text, mappings, tajweed_rule=taj_rule
            )
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
