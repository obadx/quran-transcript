import re

import pytest

from quran_transcript.phonetics.conv_base_operation import (
    MappedTagPrasingCardinalityError,
    MappedTagPrasingError,
    MappingListType,
    MappingPos,
    _expand_replacement,
    parse_tags,
    sub_with_tagged_mapping,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _init_mappings(in_text: str) -> list[MappingPos]:
    """Identity mapping covering the whole input text."""
    return [MappingPos(pos=(i, i + 1)) for i in range(len(in_text))]


def _render(mappings: list[MappingPos], out_text: str) -> list[str]:
    return [out_text[m.pos[0] : m.pos[1]] for m in mappings]


def _prety_print(
    pat: str, rep: str, in_text: str, out_text: str, out_mappings: MappingListType
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
        assert _expand_replacement("xyz", m) == "xyz"

    def test_numbered_backref(self):
        m = re.match(r"(a)(b)", "ab")
        assert _expand_replacement(r"\1\2", m) == "ab"
        assert _expand_replacement(r"\2\1", m) == "ba"

    def test_named_backref(self):
        m = re.match(r"(?P<first>a)(?P<second>b)", "ab")
        assert _expand_replacement(r"\g<first>\g<second>", m) == "ab"
        assert _expand_replacement(r"\g<second>\g<first>", m) == "ba"

    def test_g_numbered(self):
        m = re.match(r"(a)", "a")
        assert _expand_replacement(r"\g<1>", m) == "a"

    def test_escaped_backslash(self):
        m = re.match(r"(a)", "a")
        assert _expand_replacement(r"\\", m) == "\\"

    def test_mixed(self):
        m = re.match(r"(a)(b)", "ab")
        assert _expand_replacement(r"X\1Y\2Z", m) == "XaYbZ"

    def test_no_backrefs_only_literal(self):
        m = re.match(r"(a)", "a")
        assert _expand_replacement("hello world", m) == "hello world"


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
        assert tags[0].rep == "A"
        assert tags[1].tag == "y"
        assert tags[1].pat == "b"
        assert tags[1].rep == "B"

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
        assert tags[0].tag == "" and tags[0].pat == "abc" and tags[0].rep == ""
        assert tags[1].tag == "x" and tags[1].pat == "d" and tags[1].rep == "D"
        assert tags[2].tag == "" and tags[2].pat == "ef" and tags[2].rep == ""

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
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "A"
        assert out_mappings[0].pos == (0, 1)
        assert not out_mappings[0].deleted

    def test_multiple_tags(self):
        in_text = "ab"
        pat = r"M:<x:a><y:b>"
        rep = r"<x:A><y:B>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "AB"
        assert out_mappings[0].pos == (0, 1)
        assert out_mappings[1].pos == (1, 2)
        assert not out_mappings[0].deleted
        assert not out_mappings[1].deleted

    def test_backreference(self):
        in_text = "ab"
        pat = r"M:<x:(a)><y:(b)>"
        rep = r"<x:\1><y:\2>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "ab"
        assert out_mappings[0].pos == (0, 1)
        assert out_mappings[1].pos == (1, 2)

    def test_deletion(self):
        in_text = "aN"
        pat = r"M:<x:a>."
        rep = r"<x:A>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "A"
        assert out_mappings[0].pos == (0, 1)
        assert not out_mappings[0].deleted
        assert out_mappings[1].deleted
        assert out_mappings[1].pos == (1, 1)

    def test_one_to_many(self):
        in_text = "a"
        pat = r"M:<x:a>"
        rep = r"<x:ABC>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "ABC"
        assert out_mappings[0].pos == (0, 3)
        assert not out_mappings[0].deleted

    def test_multiple_matches(self):
        in_text = "a a"
        pat = r"M:<x:a>"
        rep = r"<x:A>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "A A"
        assert out_mappings[0].pos == (0, 1)
        # space between the two matches is untouched
        assert out_mappings[1].pos == (1, 2)
        assert out_mappings[2].pos == (2, 3)

    def test_unmapped_prefix_suffix(self):
        in_text = "za"
        pat = r"M:<x:a>"
        rep = r"<x:A>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "zA"
        assert out_mappings[0].pos == (0, 1)  # z unchanged
        assert out_mappings[1].pos == (1, 2)  # a -> A

    def test_many_to_many_error(self):
        in_text = "ac"
        pat = r"M:<x:[ab]c>"
        rep = r"<x:ABC>"
        mappings = _init_mappings(in_text)
        with pytest.raises(MappedTagPrasingCardinalityError):
            sub_with_tagged_mapping(pat, rep, in_text, mappings)

    def test_many_to_one_error(self):
        in_text = "ac"
        pat = r"M:<x:[ab]c>"
        rep = r"<x:A>"
        mappings = _init_mappings(in_text)
        with pytest.raises(MappedTagPrasingCardinalityError):
            sub_with_tagged_mapping(pat, rep, in_text, mappings)

    def test_missing_m_prefix(self):
        with pytest.raises(AssertionError):
            sub_with_tagged_mapping(r"<x:a>", r"<x:A>", "a", [])

    def test_named_group_backref(self):
        in_text = "a"
        pat = r"M:<x:(a)>"
        rep = r"<x:\1>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "a"
        assert out_mappings[0].pos == (0, 1)

    def test_escaped_backslash(self):
        in_text = "a"
        pat = r"M:<x:a>"
        rep = r"<x:\\>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "\\"
        assert out_mappings[0].pos == (0, 1)

    def test_many_to_many_equal_length(self):
        in_text = "ab"
        pat = r"M:<x:(a)(b)>"
        rep = r"<x:\2\1>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "ba"
        assert out_mappings[0].pos == (0, 1)
        assert out_mappings[1].pos == (1, 2)

    def test_no_tags(self):
        in_text = "abc"
        pat = r"M:abc"
        rep = r""
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == ""
        for m in out_mappings:
            assert m.deleted
            assert m.pos == (0, 0)

    def test_complex_literals_and_tags(self):
        in_text = "aXbYc"
        pat = r"M:a<x:X>b<y:Y>c"
        rep = r"<x:A><y:B>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "AB"
        assert out_mappings[0].deleted and out_mappings[0].pos == (0, 0)
        assert not out_mappings[1].deleted and out_mappings[1].pos == (0, 1)
        assert out_mappings[2].deleted and out_mappings[2].pos == (1, 1)
        assert not out_mappings[3].deleted and out_mappings[3].pos == (1, 2)
        assert out_mappings[4].deleted and out_mappings[4].pos == (2, 2)

    def test_pattern_with_brackets_and_group(self):
        in_text = "a123"
        pat = r"M:<x:([a-z])><y:(\d+)>"
        rep = r"<x:\1><y:\2>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "a123"
        assert out_mappings[0].pos == (0, 1)
        assert out_mappings[1].pos == (1, 2)
        assert out_mappings[2].pos == (2, 3)
        assert out_mappings[3].pos == (3, 4)

    # ------------------------------------------------------------------
    # New cases derived from the "Ahmed aNdef Mahmoud" example
    # ------------------------------------------------------------------
    def test_ahmed_aNdef_mahmoud(self):
        in_text = "Ahmed aNdef Mahmoud"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = _init_mappings(in_text)

        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)

        assert out_text == "Ahmed Adef Mahmoud"

        # Unchanged prefix "Ahmed " (indices 0..5) keeps identity mapping
        for i in range(6):
            assert out_mappings[i].pos == (i, i + 1)
            assert not out_mappings[i].deleted

        # 'a' at index 6 -> 'A' at output index 6
        assert out_mappings[6].pos == (6, 7)
        assert not out_mappings[6].deleted

        # 'N' at index 7 -> deleted
        assert out_mappings[7].deleted
        assert out_mappings[7].pos == (7, 7)

        # 'd', 'e', 'f' at indices 8..10 -> output indices 7..9
        assert out_mappings[8].pos == (7, 8)
        assert out_mappings[9].pos == (8, 9)
        assert out_mappings[10].pos == (9, 10)
        for i in (8, 9, 10):
            assert not out_mappings[i].deleted

        # Space at index 11 -> output index 10
        assert out_mappings[11].pos == (10, 11)

        # Tail "Mahmoud" (indices 12..18) shifted by -1 in output
        for i in range(12, 19):
            assert out_mappings[i].pos == (i - 1, i)
            assert not out_mappings[i].deleted

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
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        # no match at all
        assert out_text == "Ahmed"
        for i in range(len(in_text)):
            assert out_mappings[i].pos == (i, i + 1)
            assert not out_mappings[i].deleted

    def test_match_at_very_start_and_end(self):
        in_text = "aNdefX"
        pat = r"M:<x:[ab]>.<r:(def)>"
        rep = r"<x:A><r:\1>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == "AdefX"
        assert out_mappings[0].pos == (0, 1)
        assert out_mappings[1].deleted and out_mappings[1].pos == (1, 1)
        # tail 'X' shifted to index 4
        assert out_mappings[5].pos == (4, 5)

    def test_multiple_occurrences_in_one_text(self):
        in_text = "aNb aNc"
        # matches 'aNb' and 'aNc'
        pat = r"M:<x:[ab]>.<r:([bc])>"
        rep = r"<x:X><r:\1>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        # 'aNb' -> 'Xb', 'aNc' -> 'Xc'
        assert out_text == "Xb Xc"
        # first match
        assert out_mappings[0].pos == (0, 1)  # a -> X
        assert out_mappings[1].deleted and out_mappings[1].pos == (1, 1)  # N deleted
        assert out_mappings[2].pos == (1, 2)  # b
        # space unchanged
        assert out_mappings[3].pos == (2, 3)
        # second match
        assert out_mappings[4].pos == (3, 4)  # a -> X
        assert out_mappings[5].deleted and out_mappings[5].pos == (4, 4)  # N deleted
        assert out_mappings[6].pos == (4, 5)  # c

    def test_no_match_returns_identical_text_and_mappings(self):
        in_text = "hello world"
        pat = r"M:<x:[0-9]>"
        rep = r"<x:D>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        assert out_text == in_text
        for i in range(len(in_text)):
            assert out_mappings[i].pos == (i, i + 1)
            assert not out_mappings[i].deleted

    def test_one_to_many_shifts_following_indices(self):
        in_text = "aXY"
        pat = r"M:<x:a>"
        rep = r"<x:AAA>"
        mappings = _init_mappings(in_text)
        out_text, out_mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
        _prety_print(pat, rep, in_text, out_text, out_mappings)
        assert out_text == "AAAXY"
        assert out_mappings[0].pos == (0, 3)
        assert out_mappings[1].pos == (3, 4)
        assert out_mappings[2].pos == (4, 5)
