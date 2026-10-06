import re

import pytest

from quran_transcript.phonetics.conv_base_operation import (
    MappedTagPrasingCardinalityError,
    MappedTagPrasingError,
    PhonetizerMappings,
    RepPart,
    expand_replacement,
    init_mappings,
    parse_replacement,
    parse_tags,
    sub_with_tagged_mapping,
)


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


def _render(mappings: PhonetizerMappings, out_text: str) -> list[str]:
    return [out_text[m.pos[0] : m.pos[1]] for m in mappings.uth_to_ph]


def _check_mapping_continuty(mappings: PhonetizerMappings):
    if mappings.uth_to_ph:
        last_end = mappings.uth_to_ph[0].pos[1]
    for idx in range(1, len(mappings.uth_to_ph)):
        if last_end != mappings.uth_to_ph[idx].pos[0]:
            raise ValueError(f"Breaking mappings continutiy at idx: {idx}")
        last_end = mappings.uth_to_ph[idx].pos[1]


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

    def test_extra_tag_in_rep_ignored(self):
        pat = r"<x:a>"
        rep = r"<x:A><y:B>"
        tags = parse_tags(pat, rep)
        assert len(tags) == 1
        assert tags[0].tag == "x"

    def test_compiled_pat_present(self):
        pat = r"<x:a>"
        rep = r"<x:A>"
        tags = parse_tags(pat, rep)
        assert tags[0].compiled_pat is not None
        assert tags[0].compiled_pat.pattern == "a"


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
