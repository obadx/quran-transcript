import re

import pytest

from quran_transcript.phonetics.conv_base_operation import (
    MappedTagPrasingCardinalityError,
    MappedTagPrasingError,
    PhonetizerMappings,
    RepPart,
    add_tajweed_rule_with_tagged_pat,
    expand_replacement,
    init_mappings,
    parse_replacement,
    parse_tags,
    sub_with_tagged_mapping,
)
from quran_transcript.phonetics.tajweed_rulses import (
    TajweedRuleMetadata,
    TajweedRuleType,
)
from tests.conftest import _check_mapping_continuty


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _assert_mappings(
    out_mappings: PhonetizerMappings,
    expected_pos: list[tuple[int, int]],
    deleted_idx: set[int] | None = None,
):
    deleted_idx = deleted_idx or set()
    assert len(out_mappings.uth_to_ph) == len(expected_pos)
    for i, exp in enumerate(expected_pos):
        assert out_mappings[i].pos == exp
        assert out_mappings[i].deleted == (i in deleted_idx)


def _assert_tajweed_rules(
    out_mappings: PhonetizerMappings,
    expected: dict[int, list[TajweedRuleMetadata]],
):
    actual = {
        idx: rules
        for idx, rules in enumerate(out_mappings.ph_to_taj_rules)
        if rules
    }
    assert actual == expected


def _render(mappings: PhonetizerMappings, out_text: str) -> list[str]:
    return [out_text[m.pos[0] : m.pos[1]] for m in mappings.uth_to_ph]


def _prety_print(
    pat: str, rep: str, in_text: str, out_text: str, out_mappings: PhonetizerMappings
):
    print(f"pat: `{pat}`")
    print(f"rep: `{rep}`")
    print(f"IN  text: `{in_text}`")
    print(f"Out text: `{out_text}`")
    print("*" * 40)

    for idx, uth_c in enumerate(in_text):
        print(f"IN_IDX: `{idx}`, SPAN: `{out_mappings[idx]}`")
        mapping = out_mappings[idx]
        ph_c = out_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")
        print("-" * 40)


# ----------------------------------------------------------------------
# _expand_replacement
# ----------------------------------------------------------------------
class TestExpandReplacement:
    def test_plain(self):
        m = re.match(r"(a)", "a")
        assert expand_replacement(parse_replacement("xyz"), m) == "xyz"

    def test_numbered_backref(self):
        m = re.match(r"(a)(b)", "ab")
        assert expand_replacement(parse_replacement(r"\1\2"), m) == "ab"
        assert expand_replacement(parse_replacement(r"\2\1"), m) == "ba"

    def test_named_backref(self):
        m = re.match(r"(?P<first>a)(?P<second>b)", "ab")
        assert expand_replacement(parse_replacement(r"\g<first>\g<second>"), m) == "ab"
        assert expand_replacement(parse_replacement(r"\g<second>\g<first>"), m) == "ba"

    def test_g_numbered(self):
        m = re.match(r"(a)", "a")
        assert expand_replacement(parse_replacement(r"\g<1>"), m) == "a"

    def test_escaped_backslash(self):
        m = re.match(r"(a)", "a")
        assert expand_replacement(parse_replacement(r"\\"), m) == "\\"

    def test_mixed(self):
        m = re.match(r"(a)(b)", "ab")
        assert expand_replacement(parse_replacement(r"X\1Y\2Z"), m) == "XaYbZ"

    def test_no_backrefs_only_literal(self):
        m = re.match(r"(a)", "a")
        assert expand_replacement(parse_replacement("hello world"), m) == "hello world"


# ----------------------------------------------------------------------
# parse_tags
# ----------------------------------------------------------------------
class TestParseTags:
    def test_valid(self):
        pat = r"<x:a><y:b>"
        rep = r"<x:A><y:B>"
        tags = parse_tags(pat, rep)
        assert len(tags) == 2
        assert tags[0].tag == "x"
        assert tags[0].pat == "a"
        assert tags[0].rep_parts == [RepPart(t="STR", grp_id=-1, grp_name="", text="A")]
        assert tags[1].tag == "y"
        assert tags[1].pat == "b"
        assert tags[1].rep_parts == [RepPart(t="STR", grp_id=-1, grp_name="", text="B")]

    def test_non_connected_rep(self):
        pat = r"<x:a>"
        rep = r"<x:A>N"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_leading_garbage_in_rep(self):
        pat = r"<x:a>"
        rep = r"N<x:A>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_non_tag_segments(self):
        pat = r"abc<x:d>ef"
        rep = r"<x:D>"
        tags = parse_tags(pat, rep)
        assert len(tags) == 3
        assert tags[0].tag == "" and tags[0].pat == "abc" and tags[0].rep_parts == []
        assert (
            tags[1].tag == "x"
            and tags[1].pat == "d"
            and tags[1].rep_parts
            == [RepPart(t="STR", grp_id=-1, grp_name="", text="D")]
        )
        assert tags[2].tag == "" and tags[2].pat == "ef" and tags[2].rep_parts == []

    def test_tag_with_digit(self):
        pat = r"<x1:a>"
        rep = r"<x1:A>"
        tags = parse_tags(pat, rep)
        assert len(tags) == 1
        assert tags[0].tag == "x1"

    def test_extra_tag_in_rep_error(self):
        pat = r"<x:a>"
        rep = r"<x:A><y:B>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_repeated_tag_in_rep_error(self):
        pat = r"<x:a><y:b>"
        rep = r"<x:a><x:c>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_repeated_tag_in_pat_error(self):
        pat = r"<x:a><x:b>"
        rep = r"<x:a>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_compiled_pat_present(self):
        pat = r"<x:a>"
        rep = r"<x:A>"
        tags = parse_tags(pat, rep)
        assert tags[0].compiled_pat is not None
        assert tags[0].compiled_pat.pattern == "a"


# ----------------------------------------------------------------------
# parse_tags: Tajweed tags (T / D) rules
# ----------------------------------------------------------------------
class TestParseTagsTajweed:
    def test_plain_tags_are_classified_as_tag(self):
        pat = r"<x:a><y1:b>"
        rep = r"<x:A><y1:B>"
        tags = parse_tags(pat, rep)
        assert all(t.tag_tp == "TAG" for t in tags)
        assert all(t.taj_tag == "" and t.taj_deps == [] for t in tags)

    def test_tajweed_pivot_with_single_digit_deps(self):
        pat = r"<D0:ab><T:cd><D1:ef>"
        rep = r"<D0:ab><T:CD><D1:ef>"
        tags = parse_tags(pat, rep)
        assert [t.tag_tp for t in tags] == ["TAJWEED_DEP", "TAJWEED", "TAJWEED_DEP"]
        # deps may come before or after the pivot both belong to `T`
        assert tags[0].taj_tag == "T"
        assert tags[2].taj_tag == "T"
        assert tags[1].taj_tag == "T"
        assert tags[1].taj_deps == ["D0", "D1"]
        assert tags[0].taj_deps == [] and tags[2].taj_deps == []
        # dep_idx & num_deps
        assert tags[1].dep_idx == -1 and tags[1].num_deps == 2
        assert tags[0].dep_idx == 0 and tags[0].num_deps == 2
        assert tags[2].dep_idx == 1 and tags[2].num_deps == 2

    def test_numbered_tajweed_pivots_with_two_digit_deps(self):
        pat = r"<T0:ab><D00:cd><T1:ef><D10:gh>"
        rep = r"<T0:AB><D00:cd><T1:EF><D10:gh>"
        tags = parse_tags(pat, rep)
        assert [t.tag_tp for t in tags] == [
            "TAJWEED",
            "TAJWEED_DEP",
            "TAJWEED",
            "TAJWEED_DEP",
        ]
        assert tags[0].taj_tag == "T0" and tags[0].taj_deps == ["D00"]
        assert tags[1].taj_tag == "T0"
        assert tags[2].taj_tag == "T1" and tags[2].taj_deps == ["D10"]
        assert tags[3].taj_tag == "T1"
        # dep_idx & num_deps
        assert tags[0].dep_idx == -1 and tags[0].num_deps == 1
        assert tags[1].dep_idx == 0 and tags[1].num_deps == 1
        assert tags[2].dep_idx == -1 and tags[2].num_deps == 1
        assert tags[3].dep_idx == 0 and tags[3].num_deps == 1

    def test_tajweed_tag_with_no_deps(self):
        pat = r"<x:a><T:cd>"
        rep = r"<x:A><T:CD>"
        tags = parse_tags(pat, rep)
        assert tags[1].tag_tp == "TAJWEED"
        assert tags[1].taj_deps == []

    # ------------------------------------------------------------------
    # Not allowed usages
    # ------------------------------------------------------------------
    def test_single_digit_dep_with_numbered_tajweed_error(self):
        pat = r"<T1:ab><D0:cd>"
        rep = r"<T1:AB><D0:cd>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_two_digit_dep_with_plain_tajweed_error(self):
        pat = r"<T:ab><D12:cd>"
        rep = r"<T:AB><D12:cd>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_dep_with_no_tajweed_tag_error(self):
        pat = r"<D0:ab>"
        rep = r"<D0:ab>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_non_indexed_tajweed_dep_error(self):
        pat = r"<T:c><D:d>"
        rep = r"<T:C><D:d>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_out_of_order_deps_error(self):
        pat = r"<D5:ab><T:cd><D3:ef>"
        rep = r"<D5:ab><T:CD><D3:ef>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_gap_in_deps_error(self):
        pat = r"<D2:ab><T:cd><D4:ef>"
        rep = r"<D2:ab><T:CD><D4:ef>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_non_zero_start_deps_error(self):
        pat = r"<D2:ab><T:cd><D3:ef>"
        rep = r"<D2:ab><T:CD><D3:ef>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_duplicated_plain_tajweed_error(self):
        pat = r"<T:ab><T:cd>"
        rep = r"<T:AB><T:CD>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_duplicated_numbered_tajweed_error(self):
        pat = r"<T1:ab><D10:cd><T1:ef><D11:gh>"
        rep = r"<T1:AB><D10:cd><T1:EF><D11:gh>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)

    def test_rep_tag_not_in_pat_error(self):
        # `D1` exists in the `rep` but the `pat` only defines `D0`
        pat = r"<T:ab><D0:(cd)>"
        rep = r"<T:AB><D1:\1>"
        with pytest.raises(MappedTagPrasingError):
            parse_tags(pat, rep)


# ----------------------------------------------------------------------
# sub_with_tagged_mapping
# ----------------------------------------------------------------------
class TestSubWithTaggedMapping:
    def test_simple(self):
        in_text = "a"
        pat = r"M:<x:a>"
        rep = r"<x:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "A"
        _assert_mappings(out_mappings, [(0, 1)])

    def test_multiple_tags(self):
        in_text = "ab"
        pat = r"M:<x:a><y:b>"
        rep = r"<x:A><y:B>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AB"
        _assert_mappings(out_mappings, [(0, 1), (1, 2)])

    def test_backreference(self):
        in_text = "ab"
        pat = r"M:<x:(a)><y:(b)>"
        rep = r"<x:\1><y:\2>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ab"
        _assert_mappings(out_mappings, [(0, 1), (1, 2)])

    def test_deletion(self):
        in_text = "aN"
        pat = r"M:<x:a>."
        rep = r"<x:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "A"
        _assert_mappings(out_mappings, [(0, 1), (1, 1)], deleted_idx={1})

    def test_one_to_many(self):
        in_text = "a"
        pat = r"M:<x:a>"
        rep = r"<x:ABC>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABC"
        _assert_mappings(out_mappings, [(0, 3)])

    def test_multiple_matches(self):
        in_text = "a a"
        pat = r"M:<x:a>"
        rep = r"<x:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "A A"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 3)])

    def test_unmapped_prefix_suffix(self):
        in_text = "za"
        pat = r"M:<x:a>"
        rep = r"<x:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "zA"
        _assert_mappings(out_mappings, [(0, 1), (1, 2)])

    def test_many_to_many_error(self):
        in_text = "ac"
        pat = r"M:<x:[ab]c>"
        rep = r"<x:ABC>"
        mappings = init_mappings(in_text)
        with pytest.raises(MappedTagPrasingCardinalityError):
            sub_with_tagged_mapping(pat, rep, in_text, mappings)

    def test_many_to_one_error(self):
        in_text = "ac"
        pat = r"M:<x:[ab]c>"
        rep = r"<x:A>"
        mappings = init_mappings(in_text)
        with pytest.raises(MappedTagPrasingCardinalityError):
            sub_with_tagged_mapping(pat, rep, in_text, mappings)

    def test_missing_m_prefix(self):
        with pytest.raises(AssertionError):
            sub_with_tagged_mapping(r"<x:a>", r"<x:A>", "a", init_mappings("a"))

    def test_named_group_backref(self):
        in_text = "a"
        pat = r"M:<x:(a)>"
        rep = r"<x:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "a"
        _assert_mappings(out_mappings, [(0, 1)])

    def test_escaped_backslash(self):
        in_text = "a"
        pat = r"M:<x:a>"
        rep = r"<x:\\>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "\\"
        _assert_mappings(out_mappings, [(0, 1)])

    def test_many_to_many_equal_length(self):
        in_text = "ab"
        pat = r"M:<x:(a)(b)>"
        rep = r"<x:\2\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ba"
        _assert_mappings(out_mappings, [(0, 1), (1, 2)])

    def test_no_tags(self):
        in_text = "abc"
        pat = r"M:abc"
        rep = r""
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == ""
        _assert_mappings(out_mappings, [(0, 0), (0, 0), (0, 0)], deleted_idx={0, 1, 2})

    def test_complex_literals_and_tags(self):
        in_text = "aXbYc"
        pat = r"M:a<x:X>b<y:Y>c"
        rep = r"<x:A><y:B>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AB"
        _assert_mappings(
            out_mappings,
            [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
            deleted_idx={0, 2, 4},
        )

    def test_pattern_with_brackets_and_group(self):
        in_text = "a123"
        pat = r"M:<x:([a-z])><y:(\d+)>"
        rep = r"<x:\1><y:\2>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "a123"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 3), (3, 4)])

    # ------------------------------------------------------------------
    # New cases derived from the "Ahmed aNdef Mahmoud" example
    # ------------------------------------------------------------------
    def test_ahmed_aNdef_mahmoud(self):
        in_text = "Ahmed aNdef Mahmoud"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = init_mappings(in_text)

        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "Ahmed Adef Mahmoud"

        _assert_mappings(
            out_mappings,
            [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
                (15, 16),
                (16, 17),
                (17, 18),
            ],
            deleted_idx={7},
        )

        # Rendered characters
        rendered = _render(out_mappings, out_text)
        assert rendered[6] == "A"
        assert rendered[7] == ""
        assert rendered[8:11] == ["d", "e", "f"]

    def test_ahmed_only_first_occurrence_matches(self):
        """Uppercase 'A' at start must NOT match `[ab]` (lowercase only)."""
        in_text = "Ahmed"
        pat = r"M:<x:[ab]>."
        rep = r"<x:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        # no match at all
        assert out_text == "Ahmed"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])

    def test_match_at_very_start_and_end(self):
        in_text = "aNdefX"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AdefX"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
            deleted_idx={1},
        )

    def test_multiple_occurrences_in_one_text(self):
        in_text = "aNb aNc"
        # matches 'aNb' and 'aNc'
        pat = r"M:<x:[ab]>.<r:([bc])>"
        rep = r"<x:X><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        # 'aNb' -> 'Xb', 'aNc' -> 'Xc'
        assert out_text == "Xb Xc"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 1), (1, 2), (2, 3), (3, 4), (4, 4), (4, 5)],
            deleted_idx={1, 5},
        )

    def test_no_match_returns_identical_text_and_mappings(self):
        in_text = "hello world"
        pat = r"M:<x:[0-9]>"
        rep = r"<x:D>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == in_text
        _assert_mappings(
            out_mappings,
            [(i, i + 1) for i in range(len(in_text))],
        )

    def test_one_to_many_shifts_following_indices(self):
        in_text = "aXY"
        pat = r"M:<x:a>"
        rep = r"<x:AAA>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        assert out_text == "AAAXY"
        _assert_mappings(out_mappings, [(0, 3), (3, 4), (4, 5)])

    # ------------------------------------------------------------------
    # Cases from play_with_tagged_mapping.py
    # ------------------------------------------------------------------
    def test_single_match_at_start(self):
        in_text = "aNdef"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "Adef"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 1), (1, 2), (2, 3), (3, 4)],
            deleted_idx={1},
        )

    def test_two_matches_with_tail(self):
        in_text = "Ahmed aNdef Mahmoud aNdef Hello"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "Ahmed Adef Mahmoud Adef Hello"
        _assert_mappings(
            out_mappings,
            [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
                (15, 16),
                (16, 17),
                (17, 18),
                (18, 19),
                (19, 20),
                (20, 20),
                (20, 21),
                (21, 22),
                (22, 23),
                (23, 24),
                (24, 25),
                (25, 26),
                (26, 27),
                (27, 28),
                (28, 29),
            ],
            deleted_idx={7, 21},
        )

    def test_two_matches_at_end(self):
        in_text = "Ahmed aNdef Mahmoud aNdef"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "Ahmed Adef Mahmoud Adef"
        _assert_mappings(
            out_mappings,
            [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
                (15, 16),
                (16, 17),
                (17, 18),
                (18, 19),
                (19, 20),
                (20, 20),
                (20, 21),
                (21, 22),
                (22, 23),
            ],
            deleted_idx={7, 21},
        )

    # ------------------------------------------------------------------
    # One-to-many expansion cases from play_with_tagged_mapping.py
    # ------------------------------------------------------------------
    def test_no_mapping_change(self):
        in_text = "adef"
        pat = r"M:<x:[ab]><r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "Adef"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 3), (3, 4)])

    def test_one_to_many_shifting(self):
        in_text = "adef"
        pat = r"M:<x:[ab]><r:(def)>"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAdef"
        _assert_mappings(out_mappings, [(0, 4), (4, 5), (5, 6), (6, 7)])

    def test_one_to_many_with_trailing_text(self):
        in_text = "adef Hello"
        pat = r"M:<x:[ab]><r:(def)>"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAdef Hello"
        _assert_mappings(
            out_mappings,
            [
                (0, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
            ],
        )

    def test_two_one_to_many_with_trailing_text(self):
        in_text = "adefn Hello"
        pat = r"M:<x:[ab]><r:(def)><y:n>"
        rep = r"<x:AAAA><r:\1><y:NNN>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAdefNNN Hello"
        _assert_mappings(
            out_mappings,
            [
                (0, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
                (15, 16),
            ],
        )

    # ------------------------------------------------------------------
    # Word boundary cases from play_with_tagged_mapping.py
    # ------------------------------------------------------------------
    def test_word_boundary(self):
        in_text = "word"
        pat = r"M:<x:(word\b)>"
        rep = r"<x:WORD>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "WORD"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])

    def test_word_boundary_no_match(self):
        in_text = "wordF"
        pat = r"M:<x:(word\b)>"
        rep = r"<x:WORD>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "wordF"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])

    # ------------------------------------------------------------------
    # Multiple groups case from play_with_tagged_mapping.py
    # ------------------------------------------------------------------
    def test_multiple_groups(self):
        in_text = "a123"
        pat = r"M:<x:(a)><r:(\d+)>"
        rep = r"<x:\1><r:\2>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "a123"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])

    # ------------------------------------------------------------------
    # Anchor cases from play_with_tagged_mapping.py
    # ------------------------------------------------------------------
    def test_end_of_string_anchor(self):
        in_text = "END"
        pat = r"M:<x:END><r:($)>"
        rep = r"<x:end><r:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "end"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 3)])

    def test_beginning_of_string_anchor(self):
        in_text = "START"
        pat = r"M:<x:(^)><r:START>"
        rep = r"<x:\1><r:start>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "start"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])

    # ------------------------------------------------------------------
    # Zero-width optional characters between tags
    # ------------------------------------------------------------------
    def test_zero_width_optional_char_present(self):
        in_text = "abc"
        pat = r"M:<x:ab>c?<y:($)>"
        rep = r"<x:AB><y:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AB"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 2)],
            deleted_idx={2},
        )

    def test_zero_width_optional_char_absent(self):
        in_text = "ab"
        pat = r"M:<x:ab>c?<y:($)>"
        rep = r"<x:AB><y:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AB"
        _assert_mappings(out_mappings, [(0, 1), (1, 2)])

    def test_zero_width_optional_char_absent_one_to_many(self):
        in_text = "a"
        pat = r"M:<x:a>b?<y:($)>"
        rep = r"<x:AAAA><y:\1>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAA"
        _assert_mappings(out_mappings, [(0, 4)])


# ----------------------------------------------------------------------
# Many-to-many mappings with a shared prefix (insert/delete)
# ----------------------------------------------------------------------
class TestManyToManyWithPrefixInsertDelete:
    def test_insert(self):
        in_text = "abc"
        pat = r"M:<T:abc>"
        rep = r"<T:abcd>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "abcd"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 4)])

    def test_insert_with_deleted_prefix(self):
        in_text = "ABCabc"
        pat = r"M:C<T:abc>"
        rep = r"<T:abcd>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABabcd"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 2), (2, 3), (3, 4), (4, 6)],
            deleted_idx={2},
        )

    def test_insert_with_deleted_prefix_and_suffix(self):
        in_text = "ABCabcDEF"
        pat = r"M:C<T:abc>D"
        rep = r"<T:abcd>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABabcdEF"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 2), (2, 3), (3, 4), (4, 6), (6, 6), (6, 7), (7, 8)],
            deleted_idx={2, 6},
        )

    def test_insert_after_one_to_many(self):
        in_text = "AabcDEF"
        pat = r"M:<x:A><T:abc>D"
        rep = r"<x:AAAC><T:abcd>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAACabcdEF"
        _assert_mappings(
            out_mappings,
            [(0, 4), (4, 5), (5, 6), (6, 8), (8, 8), (8, 9), (9, 10)],
            deleted_idx={4},
        )

    def test_delete(self):
        in_text = "abc"
        pat = r"M:<T:abc>"
        rep = r"<T:ab>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ab"
        _assert_mappings(out_mappings, [(0, 1), (1, 2), (2, 2)], deleted_idx={2})

    def test_delete_with_deleted_prefix(self):
        in_text = "ABCabc"
        pat = r"M:C<T:abc>"
        rep = r"<T:ab>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABab"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 2), (2, 3), (3, 4), (4, 4)],
            deleted_idx={2, 5},
        )

    def test_delete_with_deleted_prefix_and_suffix(self):
        in_text = "ABCabcDEF"
        pat = r"M:C<T:abc>D"
        rep = r"<T:ab>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABabEF"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 2), (2, 3), (3, 4), (4, 4), (4, 4), (4, 5), (5, 6)],
            deleted_idx={2, 5, 6},
        )

    def test_insert_and_delete_with_shifts(self):
        in_text = "ABabcDEF"
        pat = r"M:<x:A>B<T:abc>D"
        rep = r"<x:AAAA><T:ab>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAabEF"
        _assert_mappings(
            out_mappings,
            [(0, 4), (4, 4), (4, 5), (5, 6), (6, 6), (6, 6), (6, 7), (7, 8)],
            deleted_idx={1, 4, 5},
        )

    def test_unequal_lengths_without_prefix_error(self):
        in_text = "abc"
        pat = r"M:<x:abc>"
        rep = r"<x:ax>"
        mappings = init_mappings(in_text)
        with pytest.raises(MappedTagPrasingCardinalityError):
            sub_with_tagged_mapping(pat, rep, in_text, mappings)


# ----------------------------------------------------------------------
# sub_with_tagged_mapping: Tajweed rules
# ----------------------------------------------------------------------
class TestSubWithTaggedMappingTajweed:
    def test_tajweed_rule_only(self):
        in_text = "abcdef"
        pat = r"M:<T:ab>"
        rep = r"<T:AB>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABcdef"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_many_matches(self):
        in_text = "aba aba"
        pat = r"M:<T:a>"
        rep = r"<T:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "AbA AbA"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 1),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                2: [
                    TajweedRuleMetadata(
                        pivot=(2, 3),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                4: [
                    TajweedRuleMetadata(
                        pivot=(4, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                6: [
                    TajweedRuleMetadata(
                        pivot=(6, 7),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_many_matches_multiple_tags(self):
        in_text = "abac abac"
        pat = r"M:<T:ab><T0:a>"
        rep = r"<T:AB><T0:A>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABAc ABAc"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                2: [
                    TajweedRuleMetadata(
                        pivot=(2, 3),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                5: [
                    TajweedRuleMetadata(
                        pivot=(5, 7),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 8),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_many_matches_with_dep_after(self):
        in_text = "aba aba"
        pat = r"M:<T:ab><D0:a>"
        rep = r"<T:AB><D0:a>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "ABa ABa"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[(2, 3)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                4: [
                    TajweedRuleMetadata(
                        pivot=(4, 6),
                        deps=[(6, 7)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_many_matches_with_dep_before(self):
        in_text = "aba aba"
        pat = r"M:<D0:a><T:ba>"
        rep = r"<D0:a><T:BA>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "aBA aBA"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 3),
                        deps=[(0, 1)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                5: [
                    TajweedRuleMetadata(
                        pivot=(5, 7),
                        deps=[(4, 5)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_on_deletion(self):
        in_text = "abcdef"
        pat = r"M:<T:ef>"
        rep = r""
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "abcd"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 3), (3, 4), (4, 4), (4, 4)],
            deleted_idx={4, 5},
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                4: [
                    TajweedRuleMetadata(
                        pivot=(4, 4),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_one_to_many(self):
        in_text = "abcdef"
        pat = r"M:<T:a>"
        rep = r"<T:AAAA>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAbcdef"
        _assert_mappings(
            out_mappings,
            [(0, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 4),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_one_to_many_with_tag(self):
        in_text = "abcdef"
        pat = r"M:<T:a><r:.>"
        rep = r"<T:AAAA><r:b>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAbcdef"
        _assert_mappings(
            out_mappings,
            [(0, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 4),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_one_to_many_with_tag_and_dep(self):
        in_text = "abcdef"
        pat = r"M:<T:a><r:.><D0:c>"
        rep = r"<T:AAAA><r:b><D0:c>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAbcdef"
        _assert_mappings(
            out_mappings,
            [(0, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 4),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_one_to_many_with_deletion_and_dep(self):
        in_text = "abcdef"
        pat = r"M:<T:a>.<D0:c>"
        rep = r"<T:AAAA><D0:c>"
        mappings = init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(out_mappings)
        assert out_text == "AAAAcdef"
        _assert_mappings(
            out_mappings,
            [(0, 4), (4, 4), (4, 5), (5, 6), (6, 7), (7, 8)],
            deleted_idx={1},
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 4),
                        deps=[(4, 5)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )


# ----------------------------------------------------------------------
# add_tajweed_rule_with_tagged_pat
# ----------------------------------------------------------------------
class TestAddTajweedRuleWithTaggedPat:
    def test_add_tajweed_rule_only(self):
        in_text = "abcdef"
        mappings = init_mappings(in_text)
        mid_text, mappings = sub_with_tagged_mapping(
            r"M:<T:ab>",
            r"<T:AB>",
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        assert mid_text == "ABcdef"

        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                5: [
                    TajweedRuleMetadata(
                        pivot=(5, 6),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_tajweed_rule_with_dep_after(self):
        in_text = "abcdef"
        mappings = init_mappings(in_text)
        mid_text, mappings = sub_with_tagged_mapping(
            r"M:<T:ab>",
            r"<T:AB>",
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        assert mid_text == "ABcdef"

        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:e><D0:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                4: [
                    TajweedRuleMetadata(
                        pivot=(4, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_tajweed_rule_with_dep_before(self):
        in_text = "abcdef"
        mappings = init_mappings(in_text)
        mid_text, mappings = sub_with_tagged_mapping(
            r"M:<T:ab>",
            r"<T:AB>",
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        assert mid_text == "ABcdef"

        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<D0:e><T:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                5: [
                    TajweedRuleMetadata(
                        pivot=(5, 6),
                        deps=[(4, 5)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_tajweed_rule_with_dep_after_multiple_matches(self):
        in_text = "abcdef ef mn ef"
        mappings = init_mappings(in_text)
        mid_text, mappings = sub_with_tagged_mapping(
            r"M:<T:ab>",
            r"<T:AB>",
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        assert mid_text == "ABcdef ef mn ef"

        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:e><D0:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                4: [
                    TajweedRuleMetadata(
                        pivot=(4, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 8),
                        deps=[(8, 9)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                13: [
                    TajweedRuleMetadata(
                        pivot=(13, 14),
                        deps=[(14, 15)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_tajweed_rule_with_dep_before_multiple_matches(self):
        in_text = "abcdef ef mn ef"
        mappings = init_mappings(in_text)
        mid_text, mappings = sub_with_tagged_mapping(
            r"M:<T:ab>",
            r"<T:AB>",
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        assert mid_text == "ABcdef ef mn ef"

        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<D0:e><T:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                5: [
                    TajweedRuleMetadata(
                        pivot=(5, 6),
                        deps=[(4, 5)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                8: [
                    TajweedRuleMetadata(
                        pivot=(8, 9),
                        deps=[(7, 8)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                14: [
                    TajweedRuleMetadata(
                        pivot=(14, 15),
                        deps=[(13, 14)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_tajweed_rule_non_indexed_dep_error(self):
        mappings = init_mappings("abcdefgh")
        with pytest.raises(MappedTagPrasingError):
            add_tajweed_rule_with_tagged_pat(
                r"M:<T:e><D:f>",
                "abcdefgh",
                mappings,
                TajweedRuleType.NORMAL_MADD,
            )


# ----------------------------------------------------------------------
# Cascaded (two-stage) cases from play_with_tagged_mapping.py
# ----------------------------------------------------------------------
class TestCascadedSubWithTaggedMapping:
    def test_cascade_one_to_many_delete_shifting_normal_text(self):
        in_text = "aNdef Hello"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)
        assert mid_text == "AAAAdef Hello"

        mid_pat = r"M:<x:A><r:d>"
        mid_rep = r"<x:FFF><r:d>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "AAAFFFdef Hello"
        _assert_mappings(
            out_mappings,
            [
                (0, 6),
                (6, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
            ],
            deleted_idx={1},
        )

    def test_cascade_one_to_many_delete_zero_width_noop_shift(self):
        in_text = "abc"
        pat = r"M:<x:ab>c"
        rep = r"<x:ab>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)

        assert mid_text == "ab"
        _assert_mappings(
            mappings,
            [(0, 1), (1, 2), (2, 2)],
            deleted_idx={2},
        )

        mid_pat = r"M:<x:a>b<y:($)>"
        mid_rep = r"<x:BB><y:\1>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "BB"
        _assert_mappings(
            out_mappings,
            [(0, 2), (2, 2), (2, 2)],
            deleted_idx={1, 2},
        )

    def test_cascade_one_to_many_then_replace_with_fff(self):
        in_text = "aNdef Hello"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)
        assert mid_text == "AAAAdef Hello"

        mid_pat = r"M:<x:A>.<r:(ef)>"
        mid_rep = r"<x:FFF><r:\1>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "AAAFFFef Hello"
        _assert_mappings(
            out_mappings,
            [
                (0, 6),
                (6, 6),
                (6, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
            ],
            deleted_idx={1, 2},
        )

    def test_cascade_one_to_many_then_replace_dropping_prefix(self):
        in_text = "aNdef Hello"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)
        assert mid_text == "AAAAdef Hello"

        mid_pat = r"M:<x:A>.<r:(ef)>"
        mid_rep = r"<r:\1>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "AAAef Hello"
        _assert_mappings(
            out_mappings,
            [
                (0, 3),
                (3, 3),
                (3, 3),
                (3, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
            ],
            deleted_idx={1, 2},
        )

    def test_cascade_delete_at_end(self):
        in_text = "aNdef Hello"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)
        assert mid_text == "AAAAdef Hello"

        mid_pat = r"M:<x:o$>"
        mid_rep = r""
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "AAAAdef Hell"
        _assert_mappings(
            out_mappings,
            [
                (0, 4),
                (4, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 12),
            ],
            deleted_idx={1, 10},
        )

    def test_cascade_delete_tail_in_first_stage(self):
        in_text = "aNdef Hello"
        pat = r"M:<x:[ab]>.<r:(def)> Hello"
        rep = r"<x:AAAA><r:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)
        assert mid_text == "AAAAdef"

        mid_pat = r"M:<x:A>.<r:(ef)>"
        mid_rep = r"<x:FFF><r:\1>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "AAAFFFef"
        _assert_mappings(
            out_mappings,
            [
                (0, 6),
                (6, 6),
                (6, 6),
                (6, 7),
                (7, 8),
                (8, 8),
                (8, 8),
                (8, 8),
                (8, 8),
                (8, 8),
                (8, 8),
            ],
            deleted_idx={1, 2, 5, 6, 7, 8, 9, 10},
        )

    def test_cascade_delete_tail_then_one_to_many_at_end(self):
        in_text = "aNdef Hello"
        pat = r"M:<x: Hello>"
        rep = r""
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, mid_text, mappings)
        _check_mapping_continuty(mappings)
        assert mid_text == "aNdef"

        mid_pat = r"M:<x:f$>"
        mid_rep = r"<x:FFFF>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _prety_print(mid_pat, mid_rep, in_text, out_text, out_mappings)
        _check_mapping_continuty(out_mappings)

        assert out_text == "aNdeFFFF"
        _assert_mappings(
            out_mappings,
            [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (4, 8),
                (8, 8),
                (8, 8),
                (8, 8),
                (8, 8),
                (8, 8),
                (8, 8),
            ],
            deleted_idx={5, 6, 7, 8, 9, 10},
        )


# ----------------------------------------------------------------------
# Cascaded (two-stage) Tajweed rule cases from play_with_tagged_mapping.py
# ----------------------------------------------------------------------
class TestCascadedSubWithTaggedMappingTajweed:
    def test_tajweed_rule_with_dep_then_reorder_prefix(self):
        in_text = "abcdef"
        pat = r"M:<T:ab><D0:(cd)>"
        rep = r"<T:AB><D0:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdef"

        mid_pat = r"M:<x:AB>"
        mid_rep = r"<x:BA>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "BAcdef"
        _assert_mappings(out_mappings, [(i, i + 1) for i in range(len(in_text))])
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 2),
                        deps=[(2, 4)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rule_with_dep_then_delete_prefix(self):
        in_text = "abcdef"
        pat = r"M:<T:ab><D0:(cd)>"
        rep = r"<T:AB><D0:\1>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdef"

        mid_pat = r"M:<x:AB>"
        mid_rep = r""
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat, mid_rep, mid_text, mappings
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "cdef"
        _assert_mappings(
            out_mappings,
            [(0, 0), (0, 0), (0, 1), (1, 2), (2, 3), (3, 4)],
            deleted_idx={0, 1},
        )
        # The tajweed pivot is collapsed to zero width but is not removed.
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 0),
                        deps=[(0, 2)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_second_tajweed_rule_added(self):
        in_text = "abcdef"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdef"

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdef"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_second_tajweed_rule_added_with_allowing_condition(self):
        in_text = "abcdef"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdef"

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
            insert_tajweed_cond=lambda types, rule_type: (
                TajweedRuleType.LAZIM_MADD not in types
            ),
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdef"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_tajweed_rules_deleted_at_end(self):
        in_text = "abcdef"
        pat = r"M:<T:ef><D0:($)>"
        rep = r""
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "abcd"

        mid_pat = r"M:<T:cd><D0:($)>"
        mid_rep = r""
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ab"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 2), (2, 2), (2, 2), (2, 2), (2, 2)],
            deleted_idx={2, 3, 4, 5},
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                2: [
                    TajweedRuleMetadata(
                        pivot=(2, 2),
                        deps=[(2, 2)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    ),
                    TajweedRuleMetadata(
                        pivot=(2, 2),
                        deps=[(2, 2)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    ),
                ],
            },
        )

    def test_tajweed_rules_deleted_at_end_with_surrounding_text(self):
        in_text = "Ahmed Mahmoud abcdef"
        pat = r"M:<T:ef><D0:($)>"
        rep = r""
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "Ahmed Mahmoud abcd"

        mid_pat = r"M:<T:cd><D0:($)>"
        mid_rep = r""
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "Ahmed Mahmoud ab"
        _assert_mappings(
            out_mappings,
            [(i, i + 1) for i in range(16)] + [(16, 16)] * 4,
            deleted_idx={16, 17, 18, 19},
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                16: [
                    TajweedRuleMetadata(
                        pivot=(16, 16),
                        deps=[(16, 16)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    ),
                    TajweedRuleMetadata(
                        pivot=(16, 16),
                        deps=[(16, 16)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    ),
                ],
            },
        )

    def test_second_tajweed_rule_added_with_surrounding_text(self):
        in_text = "Hello How are you: abcdef Good "
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "Hello How are you: ABcdef Good "

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "Hello How are you: ABBBBcdef Good "
        _assert_mappings(
            out_mappings,
            [(i, i + 1) for i in range(19)]
            + [(19, 20), (20, 24)]
            + [(i + 3, i + 4) for i in range(21, 31)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                19: [
                    TajweedRuleMetadata(
                        pivot=(19, 24),
                        deps=[(24, 25)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                20: [
                    TajweedRuleMetadata(
                        pivot=(20, 24),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_second_tajweed_rule_blocked_by_condition(self):
        in_text = "Hello How are you: abcdef Good "
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "Hello How are you: ABcdef Good "

        mid_pat = r"M:<T:A>"
        mid_rep = r"<T:aaaa>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
            insert_tajweed_cond=lambda types, rule_type: (
                TajweedRuleType.LAZIM_MADD not in types
            ),
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "Hello How are you: aaaaBcdef Good "
        _assert_mappings(
            out_mappings,
            [(i, i + 1) for i in range(19)]
            + [(19, 23), (23, 24)]
            + [(i + 3, i + 4) for i in range(21, 31)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                19: [
                    TajweedRuleMetadata(
                        pivot=(19, 24),
                        deps=[(24, 25)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
            },
        )

    def test_add_first_tajweed_rule_after_sub(self):
        in_text = "abcdefgh"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdefgh"

        mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:ef>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdefgh"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 9),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_first_tajweed_rule_with_dep_after_sub(self):
        in_text = "abcdefgh"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdefgh"

        mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:e><D0:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdefgh"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 8),
                        deps=[(8, 9)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_first_and_mid_tajweed_rules(self):
        in_text = "abcdefgh"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdefgh"

        mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:e><D0:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:g>",
            out_text,
            out_mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdefgh"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 8),
                        deps=[(8, 9)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                9: [
                    TajweedRuleMetadata(
                        pivot=(9, 10),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_first_and_mid_tajweed_rules_with_deps(self):
        in_text = "abcdefgh"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdefgh"

        mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:e><D0:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:g><D0:h>",
            out_text,
            out_mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdefgh"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 8),
                        deps=[(8, 9)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                9: [
                    TajweedRuleMetadata(
                        pivot=(9, 10),
                        deps=[(10, 11)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )

    def test_add_first_and_mid_tajweed_rules_with_dep_before(self):
        in_text = "abcdefgh"
        pat = r"M:<T:ab><D0:c>"
        rep = r"<T:AB><D0:c>"
        mappings = init_mappings(in_text)

        mid_text, mappings = sub_with_tagged_mapping(
            pat,
            rep,
            in_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.LAZIM_MADD,
        )
        _check_mapping_continuty(mappings)
        assert mid_text == "ABcdefgh"

        mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<T:e><D0:f>",
            mid_text,
            mappings,
            TajweedRuleType.NORMAL_MADD,
        )

        mid_pat = r"M:<T:B>"
        mid_rep = r"<T:BBBB>"
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=TajweedRuleType.NORMAL_MADD,
        )
        out_mappings = add_tajweed_rule_with_tagged_pat(
            r"M:<D0:g><T:h>",
            out_text,
            out_mappings,
            TajweedRuleType.NORMAL_MADD,
        )
        _check_mapping_continuty(out_mappings)

        assert out_text == "ABBBBcdefgh"
        _assert_mappings(
            out_mappings,
            [(0, 1), (1, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11)],
        )
        _assert_tajweed_rules(
            out_mappings,
            {
                0: [
                    TajweedRuleMetadata(
                        pivot=(0, 5),
                        deps=[(5, 6)],
                        tag="",
                        rule_type=TajweedRuleType.LAZIM_MADD,
                    )
                ],
                1: [
                    TajweedRuleMetadata(
                        pivot=(1, 5),
                        deps=[],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                7: [
                    TajweedRuleMetadata(
                        pivot=(7, 8),
                        deps=[(8, 9)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
                10: [
                    TajweedRuleMetadata(
                        pivot=(10, 11),
                        deps=[(9, 10)],
                        tag="",
                        rule_type=TajweedRuleType.NORMAL_MADD,
                    )
                ],
            },
        )
