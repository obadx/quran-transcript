import py
import pytest
import sys
import os


from quran_transcript import MoshafAttributes, quran_phonetizer, Aya
from quran_transcript.phonetics.conv_base_operation import (
    MappingPos,
    sub_with_mapping,
    merge_mappings,
    get_mappings,
    MappingListType,
)
from quran_transcript.phonetics.search import (
    get_uth_word_boundaries_in_ph,
    clean_uthmani_spaces,
)

from quran_transcript.phonetics.tajweed_rulses import NormalMaddRule, Qalqalah
# Import the sub_with_mapping function from the existing test file


@pytest.mark.parametrize(
    "pattern,repl,input_text,expected_output,expected_mappings",
    [
        # Test case 1: Identity mapping (no change)
        (
            "",
            "",
            "abcd",
            "abcd",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
            ],
        ),
        # Test case 2: equal + insert
        (
            "a",
            "aaaa",
            "abcd",
            "aaaabcd",
            [
                MappingPos(pos=(0, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
                MappingPos(pos=(6, 7), tajweed_rules=None),
            ],
        ),
        # Test case 3: equal + insert + replace
        (
            "ab",
            "aaaa",
            "abcd",
            "aaaacd",
            [
                MappingPos(pos=(0, 4), tajweed_rules=None),
                MappingPos(pos=(4, 4), deleted=True),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
            ],
        ),
        # Test case 4: insert + replace
        (
            "ab",
            "mmmm",
            "abcd",
            "mmmmcd",
            [
                MappingPos(pos=(0, 4), tajweed_rules=None),
                MappingPos(pos=(4, 4), deleted=True),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
            ],
        ),
        # Test case 5: delete
        (
            "b",
            "",
            "abcd",
            "acd",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 1), deleted=True),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
            ],
        ),
        # Test case 6: replace
        (
            "bc",
            "mn",
            "abcd",
            "amnd",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
            ],
        ),
        # Test case 7: insert + replace + delete
        (
            "bcd",
            "amn",
            "abcd",
            "aamn",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
            ],
        ),
        # Test case 8: equal + insert + replace + delete
        (
            "ab(.)d$",
            r"aaaa\1",
            "abcd",
            "aaaac",
            [
                MappingPos(pos=(0, 4), tajweed_rules=None),
                MappingPos(pos=(4, 4), deleted=True),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 5), deleted=True),
            ],
        ),
        # Test case 9: equal + insert + equal
        (
            "abcd",
            r"abmcd",
            "abcd",
            "abmcd",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
            ],
        ),
        # Test case 10: insert + equal
        (
            "abcd",
            "mmmabcd",
            "abcd",
            "mmmabcd",
            [
                MappingPos(pos=(0, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
                MappingPos(pos=(6, 7), tajweed_rules=None),
            ],
        ),
        # Test case 9: equal + insert + equal
        (
            "abcd",
            "abccd",
            "abcd",
            "abccd",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
            ],
        ),
    ],
)
def test_sub_with_mapping_operations(
    pattern, repl, input_text, expected_output, expected_mappings
):
    """Test sub_with_mapping function with various regex operations."""

    result_text, result_mappings = sub_with_mapping(pattern, repl, input_text)

    # Assert output text matches expected
    assert result_text == expected_output, (
        f"Expected '{expected_output}', got '{result_text}'"
    )

    # Assert number of mappings matches
    assert len(result_mappings) == len(expected_mappings), (
        f"Expected {len(expected_mappings)} mappings, got {len(result_mappings)}"
    )

    # Assert each mapping matches expected
    print(f"OUT: {result_mappings}")
    print(f"EXP: {expected_mappings}")
    assert result_mappings == expected_mappings


@pytest.mark.parametrize(
    "input_text,out_text,in_mappings, exp_mappings",
    [
        (
            "بِسْمِ لَّاهِ رَّحْمَانِ رَّحِۦۦۦۦم",
            "بِسْمِ لَّااهِ رَّحْمَاانِ رَّحِۦۦۦۦم",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 7), deleted=True),
                MappingPos(pos=(7, 8), tajweed_rules=None),
                MappingPos(pos=(8, 8), deleted=True),
                MappingPos(pos=(8, 9), tajweed_rules=None),
                MappingPos(pos=(9, 11), tajweed_rules=[NormalMaddRule(tag="alif")]),
                MappingPos(pos=(11, 12), tajweed_rules=None),
                MappingPos(pos=(12, 13), tajweed_rules=None),
                MappingPos(pos=(13, 14), tajweed_rules=None),
                MappingPos(pos=(14, 14), deleted=True),
                MappingPos(pos=(14, 14), deleted=True),
                MappingPos(pos=(14, 15), tajweed_rules=None),
                MappingPos(pos=(15, 16), tajweed_rules=None),
                MappingPos(pos=(16, 17), tajweed_rules=None),
                MappingPos(pos=(17, 18), tajweed_rules=None),
                MappingPos(pos=(18, 19), tajweed_rules=None),
                MappingPos(pos=(19, 20), tajweed_rules=None),
                MappingPos(pos=(20, 21), tajweed_rules=None),
                MappingPos(pos=(21, 21), deleted=True),
                MappingPos(pos=(21, 22), tajweed_rules=None),
                MappingPos(pos=(22, 23), tajweed_rules=None),
                MappingPos(pos=(23, 24), tajweed_rules=None),
                MappingPos(pos=(24, 25), tajweed_rules=None),
                MappingPos(pos=(25, 25), deleted=True),
                MappingPos(pos=(25, 25), deleted=True),
                MappingPos(pos=(25, 26), tajweed_rules=None),
                MappingPos(pos=(26, 27), tajweed_rules=None),
                MappingPos(pos=(27, 28), tajweed_rules=None),
                MappingPos(pos=(28, 29), tajweed_rules=None),
                MappingPos(pos=(29, 30), tajweed_rules=None),
                MappingPos(pos=(30, 34), tajweed_rules=None),
                MappingPos(pos=(34, 35), tajweed_rules=None),
                MappingPos(pos=(35, 35), deleted=True),
            ],
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 7), deleted=True),
                MappingPos(pos=(7, 8), tajweed_rules=None),
                MappingPos(pos=(8, 8), deleted=True),
                MappingPos(pos=(8, 9), tajweed_rules=None),
                MappingPos(pos=(9, 12), tajweed_rules=[NormalMaddRule(tag="alif")]),
                MappingPos(pos=(12, 13), tajweed_rules=None),
                MappingPos(pos=(13, 14), tajweed_rules=None),
                MappingPos(pos=(14, 15), tajweed_rules=None),
                MappingPos(pos=(15, 15), deleted=True),
                MappingPos(pos=(15, 15), deleted=True),
                MappingPos(pos=(15, 16), tajweed_rules=None),
                MappingPos(pos=(16, 17), tajweed_rules=None),
                MappingPos(pos=(17, 18), tajweed_rules=None),
                MappingPos(pos=(18, 19), tajweed_rules=None),
                MappingPos(pos=(19, 20), tajweed_rules=None),
                MappingPos(pos=(20, 21), tajweed_rules=None),
                MappingPos(pos=(21, 22), tajweed_rules=None),
                MappingPos(pos=(22, 22), deleted=True),
                MappingPos(pos=(22, 24), tajweed_rules=None),
                MappingPos(pos=(24, 25), tajweed_rules=None),
                MappingPos(pos=(25, 26), tajweed_rules=None),
                MappingPos(pos=(26, 27), tajweed_rules=None),
                MappingPos(pos=(27, 27), deleted=True),
                MappingPos(pos=(27, 27), deleted=True),
                MappingPos(pos=(27, 28), tajweed_rules=None),
                MappingPos(pos=(28, 29), tajweed_rules=None),
                MappingPos(pos=(29, 30), tajweed_rules=None),
                MappingPos(pos=(30, 31), tajweed_rules=None),
                MappingPos(pos=(31, 32), tajweed_rules=None),
                MappingPos(pos=(32, 36), tajweed_rules=None),
                MappingPos(pos=(36, 37), tajweed_rules=None),
                MappingPos(pos=(37, 37), deleted=True),
            ],
        ),
        (
            "وَقِۦۦلَ مَنْۜ رَااااق",
            "وَقِۦۦلَ مَنْۜ رَااااقڇ",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 6), tajweed_rules=None),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 8), tajweed_rules=None),
                MappingPos(pos=(8, 9), tajweed_rules=None),
                MappingPos(pos=(9, 10), tajweed_rules=None),
                MappingPos(pos=(10, 11), tajweed_rules=None),
                MappingPos(pos=(11, 12), tajweed_rules=None),
                MappingPos(pos=(12, 14), tajweed_rules=None),
                MappingPos(pos=(14, 15), tajweed_rules=None),
                MappingPos(pos=(15, 16), tajweed_rules=None),
                MappingPos(pos=(16, 17), tajweed_rules=None),
                MappingPos(pos=(17, 21), tajweed_rules=None),
                MappingPos(pos=(21, 22), tajweed_rules=None),
                MappingPos(pos=(22, 22), deleted=True),
                MappingPos(pos=(22, 22), deleted=True),
            ],
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 6), tajweed_rules=None),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 8), tajweed_rules=None),
                MappingPos(pos=(8, 9), tajweed_rules=None),
                MappingPos(pos=(9, 10), tajweed_rules=None),
                MappingPos(pos=(10, 11), tajweed_rules=None),
                MappingPos(pos=(11, 12), tajweed_rules=None),
                MappingPos(pos=(12, 14), tajweed_rules=None),
                MappingPos(pos=(14, 15), tajweed_rules=None),
                MappingPos(pos=(15, 16), tajweed_rules=None),
                MappingPos(pos=(16, 17), tajweed_rules=None),
                MappingPos(pos=(17, 21), tajweed_rules=None),
                MappingPos(pos=(21, 23), tajweed_rules=None),
                MappingPos(pos=(23, 23), deleted=True),
                MappingPos(pos=(23, 23), deleted=True),
            ],
        ),
    ],
)
def test_get_mappings(
    input_text: str,
    out_text: str,
    in_mappings: MappingListType | None,
    exp_mappings: MappingListType,
):
    """Test Get Mappings"""

    out_mappings = get_mappings(input_text, out_text, in_mappings)

    # Assert each mapping matches expected
    print(f"OUT: {out_mappings}")
    print(f"EXP: {exp_mappings}")
    assert out_mappings == exp_mappings


def test_sub_with_mapping_edge_cases():
    """Test edge cases for sub_with_mapping function."""

    # Test with empty input
    result_text, result_mappings = sub_with_mapping("", "", "")
    assert result_text == ""
    assert result_mappings == []

    # Test with pattern that doesn't match
    result_text, result_mappings = sub_with_mapping("z", "x", "abcd")
    assert result_text == "abcd"
    assert len(result_mappings) == 4
    for i, mapping in enumerate(result_mappings):
        assert mapping.pos == (i, i + 1)


def test_mapping_pos_consistency():
    """Test that MappingPos objects maintain consistency."""
    # Test basic MappingPos creation
    pos = MappingPos(pos=(0, 3))
    assert pos.pos == (0, 3)
    assert pos.tajweed_rules is None

    # Test with tajweed_rules
    pos_with_rules = MappingPos(pos=(1, 4), tajweed_rules=[])
    assert pos_with_rules.pos == (1, 4)
    assert pos_with_rules.tajweed_rules == []


class TestMergeMappings:
    """Test cases for merge_mappings function."""

    def test_merge_mappings_none_input(self):
        """Test when first parameter is None - should return new_mappings."""
        new_mappings: MappingListType = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        result = merge_mappings(None, new_mappings)
        assert result == new_mappings

    def test_merge_mappings_identity(self):
        """Test simple identity mapping - should preserve positions."""
        mappings: MappingListType = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        new_mappings: MappingListType = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        expected: MappingListType = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        result = merge_mappings(mappings, new_mappings)
        assert result == expected

    def test_merge_mappings_expansion(self):
        """Test when new mappings expand the range."""
        mappings = [
            MappingPos(pos=(0, 1)),  # Single position
            MappingPos(pos=(1, 2)),
        ]

        new_mappings = [
            MappingPos(pos=(0, 3)),  # Expanded range
            MappingPos(pos=(3, 4)),
            MappingPos(pos=(4, 5)),
        ]

        expected = [
            MappingPos(pos=(0, 3)),  # First mapping gets expanded range
            MappingPos(
                pos=(3, 4)
            ),  # Second mapping maps to first position in its range
        ]

        result = merge_mappings(mappings, new_mappings)
        assert result == expected

    def test_merge_mappings_contraction(self):
        """Test when new mappings contract the range."""
        mappings = [
            MappingPos(pos=(0, 3)),  # Wide range
            MappingPos(pos=(3, 4)),
        ]

        new_mappings = [
            MappingPos(pos=(0, 1)),  # Contracted range
            MappingPos(pos=(1, 1), deleted=True),  # Missing position
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 2), deleted=True),
        ]

        expected = [
            MappingPos(pos=(0, 2)),  # Should span from first to last non-None
            MappingPos(pos=(2, 2), deleted=True),
        ]

        result = merge_mappings(mappings, new_mappings)
        print(f"OUT: {result}")
        print(f"EXP: {expected}")

        assert result == expected

    @pytest.mark.parametrize(
        "mappings,new_mappings,expected",
        [
            # Test start and eend in between
            (
                [
                    MappingPos(pos=(0, 3)),
                    MappingPos(pos=(3, 5)),
                    MappingPos(pos=(5, 6)),
                ],
                [
                    MappingPos(pos=(0, 0), deleted=True),
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 1), deleted=True),
                    MappingPos(pos=(1, 3)),
                    MappingPos(pos=(3, 6)),
                    MappingPos(pos=(6, 6), deleted=True),
                ],
                [
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 6)),
                    MappingPos(pos=(6, 6), deleted=True),
                ],  # Should span first to last non-None
            ),
            # Test start and eend in between + tajweed rules (input)
            (
                [
                    MappingPos(pos=(0, 3), tajweed_rules=[NormalMaddRule(tag="alif")]),
                    MappingPos(pos=(3, 5)),
                    MappingPos(pos=(5, 6)),
                ],
                [
                    MappingPos(pos=(0, 0), deleted=True),
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 1), deleted=True),
                    MappingPos(pos=(1, 3)),
                    MappingPos(pos=(3, 6)),
                    MappingPos(pos=(6, 6), deleted=True),
                ],
                [
                    MappingPos(pos=(0, 1), tajweed_rules=[NormalMaddRule(tag="alif")]),
                    MappingPos(pos=(1, 6)),
                    MappingPos(pos=(6, 6), deleted=True),
                ],  # Should span first to last non-None
            ),
            # Test start and eend in between + tajweed rules (output)
            (
                [
                    MappingPos(pos=(0, 3)),
                    MappingPos(pos=(3, 5)),
                    MappingPos(pos=(5, 6)),
                ],
                [
                    MappingPos(pos=(0, 0), deleted=True),
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 1), deleted=True),
                    MappingPos(pos=(1, 3), tajweed_rules=[NormalMaddRule(tag="alif")]),
                    MappingPos(pos=(3, 6)),
                    MappingPos(pos=(6, 6), deleted=True),
                ],
                [
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 6), tajweed_rules=[NormalMaddRule(tag="alif")]),
                    MappingPos(pos=(6, 6), deleted=True),
                ],  # Should span first to last non-None
            ),
            # Test start and eend in between + tajweed rules (both)
            (
                [
                    MappingPos(pos=(0, 3)),
                    MappingPos(pos=(3, 5), tajweed_rules=[Qalqalah()]),
                    MappingPos(pos=(5, 6)),
                ],
                [
                    MappingPos(pos=(0, 0), deleted=True),
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 1), deleted=True),
                    MappingPos(pos=(1, 3), tajweed_rules=[NormalMaddRule(tag="alif")]),
                    MappingPos(pos=(3, 6)),
                    MappingPos(pos=(6, 6), deleted=True),
                ],
                [
                    MappingPos(pos=(0, 1)),
                    MappingPos(
                        pos=(1, 6),
                        tajweed_rules=[Qalqalah(), NormalMaddRule(tag="alif")],
                    ),
                    MappingPos(pos=(6, 6), deleted=True),
                ],  # Should span first to last non-None
            ),
            # Test partial None mappings - some positions in range are None
            (
                [MappingPos(pos=(0, 3))],
                [
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(1, 1), deleted=True),
                    MappingPos(pos=(2, 3)),
                ],
                [MappingPos(pos=(0, 3))],  # Should span first to last non-None
            ),
            # Test single mapping to multiple new mappings
            (
                [MappingPos(pos=(1, 2))],
                [MappingPos(pos=(0, 0), deleted=True), MappingPos(pos=(0, 2))],
                [MappingPos(pos=(0, 2))],  # Should get the non-None range
            ),
            # Test edge case with only start mapping
            (
                [MappingPos(pos=(0, 1))],
                [MappingPos(pos=(0, 1))],
                [MappingPos(pos=(0, 1))],  # Should use start position only
            ),
            # Test edge case with only end mapping
            (
                [MappingPos(pos=(0, 1))],
                [MappingPos(pos=(0, 0), deleted=True)],
                [MappingPos(pos=(0, 0), deleted=True)],  # Should use end position only
            ),
        ],
    )
    def test_merge_mappings_partial_none(self, mappings, new_mappings, expected):
        """Test various scenarios with None values in new_mappings."""
        result = merge_mappings(mappings, new_mappings)
        print(f"MAP: {mappings}")
        print(f"NEW: {new_mappings}")
        print(f"OUT: {result}")
        print(f"EXP: {expected}")
        assert result == expected

    def test_merge_mappings_empty_lists(self):
        """Test edge cases with empty lists."""
        # Both empty
        with pytest.raises(ValueError):
            result = merge_mappings([], [])

        # Empty mappings, non-empty new_mappings
        new_mappings = [MappingPos(pos=(0, 1))]
        result = merge_mappings([], new_mappings)
        assert result == []

        # Non-empty mappings, empty new_mappings
        with pytest.raises(ValueError):
            mappings = [MappingPos(pos=(0, 1))]
            result = merge_mappings(mappings, [])

    def test_merge_mappings_complex_range(self):
        """Test complex scenario with multiple overlapping ranges."""
        mappings = [
            MappingPos(pos=(0, 3)),  # Maps to first 3 positions
            MappingPos(pos=(3, 5)),  # Maps to next 2 positions
            MappingPos(pos=(5, 6)),  # Maps to last position
        ]

        new_mappings = [
            MappingPos(pos=(0, 2)),  # Expanded first range
            MappingPos(pos=(2, 4)),
            MappingPos(pos=(4, 4), deleted=True),  # Gap
            MappingPos(pos=(4, 7)),  # Expanded second range
            MappingPos(pos=(7, 8)),
            MappingPos(pos=(8, 9)),  # Expanded third range
        ]

        expected = [
            MappingPos(pos=(0, 4)),  # First mapping spans first non-None range
            MappingPos(pos=(4, 8)),  # Second mapping spans its range
            MappingPos(pos=(8, 9)),  # Third mapping gets its position
        ]

        result = merge_mappings(mappings, new_mappings)
        assert result == expected


@pytest.mark.parametrize(
    "uth_text, ph_text, exp_mappings",
    [
        (
            "الٓر تِلْكَ ءَايَـٰتُ ٱلْكِتَـٰبِ ٱلْمُبِينِ",
            "ءَلِف لَاااااام رَاا تِلكَ ءَاايَااتُ لكِتَاابِ لمُبِۦۦۦۦن",
            [
                MappingPos(pos=(0, 6), tajweed_rules=None),
                MappingPos(pos=(6, 16), tajweed_rules=None),
                MappingPos(pos=(16, 16), deleted=True),
                MappingPos(
                    pos=(16, 20),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="alif",
                        )
                    ],
                ),
                MappingPos(pos=(20, 21), tajweed_rules=None),
                MappingPos(pos=(21, 22), tajweed_rules=None),
                MappingPos(pos=(22, 23), tajweed_rules=None),
                MappingPos(pos=(23, 24), tajweed_rules=None),
                MappingPos(pos=(24, 24), deleted=True),
                MappingPos(pos=(24, 25), tajweed_rules=None),
                MappingPos(pos=(25, 26), tajweed_rules=None),
                MappingPos(pos=(26, 27), tajweed_rules=None),
                MappingPos(pos=(27, 28), tajweed_rules=None),
                MappingPos(pos=(28, 29), tajweed_rules=None),
                MappingPos(
                    pos=(29, 31),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="alif",
                        )
                    ],
                ),
                MappingPos(pos=(31, 32), tajweed_rules=None),
                MappingPos(pos=(32, 33), tajweed_rules=None),
                MappingPos(pos=(33, 33), deleted=True),
                MappingPos(
                    pos=(33, 35),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="alif",
                        )
                    ],
                ),
                MappingPos(pos=(35, 36), tajweed_rules=None),
                MappingPos(pos=(36, 37), tajweed_rules=None),
                MappingPos(pos=(37, 38), tajweed_rules=None),
                MappingPos(pos=(38, 38), deleted=True),
                MappingPos(pos=(38, 39), tajweed_rules=None),
                MappingPos(pos=(39, 39), deleted=True),
                MappingPos(pos=(39, 40), tajweed_rules=None),
                MappingPos(pos=(40, 41), tajweed_rules=None),
                MappingPos(pos=(41, 42), tajweed_rules=None),
                MappingPos(pos=(42, 43), tajweed_rules=None),
                MappingPos(pos=(43, 43), deleted=True),
                MappingPos(
                    pos=(43, 45),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="alif",
                        )
                    ],
                ),
                MappingPos(pos=(45, 46), tajweed_rules=None),
                MappingPos(pos=(46, 47), tajweed_rules=None),
                MappingPos(pos=(47, 48), tajweed_rules=None),
                MappingPos(pos=(48, 48), deleted=True),
                MappingPos(pos=(48, 49), tajweed_rules=None),
                MappingPos(pos=(49, 49), deleted=True),
                MappingPos(pos=(49, 50), tajweed_rules=None),
                MappingPos(pos=(50, 51), tajweed_rules=None),
                MappingPos(pos=(51, 52), tajweed_rules=None),
                MappingPos(pos=(52, 53), tajweed_rules=None),
                MappingPos(pos=(53, 57), tajweed_rules=None),
                MappingPos(pos=(57, 58), tajweed_rules=None),
                MappingPos(pos=(58, 58), deleted=True),
            ],
        ),
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
            "بِسمِ للَااهِ ررَحمَاانِ ررَحِۦۦۦۦم",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 3), deleted=True),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 5), tajweed_rules=None),
                MappingPos(pos=(5, 6), tajweed_rules=None),
                MappingPos(pos=(6, 6), deleted=True),
                MappingPos(pos=(6, 6), deleted=True),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 8), tajweed_rules=None),
                MappingPos(pos=(8, 11), tajweed_rules=[NormalMaddRule(tag="alif")]),
                MappingPos(pos=(11, 12), tajweed_rules=None),
                MappingPos(pos=(12, 13), tajweed_rules=None),
                MappingPos(pos=(13, 14), tajweed_rules=None),
                MappingPos(pos=(14, 14), deleted=True),
                MappingPos(pos=(14, 14), deleted=True),
                MappingPos(pos=(14, 15), tajweed_rules=None),
                MappingPos(pos=(15, 16), tajweed_rules=None),
                MappingPos(pos=(16, 17), tajweed_rules=None),
                MappingPos(pos=(17, 18), tajweed_rules=None),
                MappingPos(pos=(18, 18), deleted=True),
                MappingPos(pos=(18, 19), tajweed_rules=None),
                MappingPos(pos=(19, 20), tajweed_rules=None),
                MappingPos(pos=(20, 20), deleted=True),
                MappingPos(pos=(20, 22), tajweed_rules=[NormalMaddRule(tag="alif")]),
                MappingPos(pos=(22, 23), tajweed_rules=None),
                MappingPos(pos=(23, 24), tajweed_rules=None),
                MappingPos(pos=(24, 25), tajweed_rules=None),
                MappingPos(pos=(25, 25), deleted=True),
                MappingPos(pos=(25, 25), deleted=True),
                MappingPos(pos=(25, 26), tajweed_rules=None),
                MappingPos(pos=(26, 27), tajweed_rules=None),
                MappingPos(pos=(27, 28), tajweed_rules=None),
                MappingPos(pos=(28, 29), tajweed_rules=None),
                MappingPos(pos=(29, 30), tajweed_rules=None),
                MappingPos(pos=(30, 34), tajweed_rules=None),
                MappingPos(pos=(34, 35), tajweed_rules=None),
                MappingPos(pos=(35, 35), deleted=True),
            ],
        ),
        (
            "إِنَّ ٱلَّذِينَ كَفَرُوا۟ سَوَآءٌ عَلَيْهِمْ ءَأَنذَرْتَهُمْ أَمْ لَمْ تُنذِرْهُمْ لَا يُؤْمِنُونَ",
            "ءِننننَ للَذِۦۦنَ كَفَرُۥۥ سَوَااااءُن عَلَيهِم ءَءَںںںذَرتَهُم ءَم لَم تُںںںذِرهُم لَاا يُءمِنُۥۥۥۥن",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 6), tajweed_rules=None),
                MappingPos(pos=(6, 6), deleted=True),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 8), tajweed_rules=None),
                MappingPos(pos=(8, 8), deleted=True),
                MappingPos(pos=(8, 9), tajweed_rules=None),
                MappingPos(pos=(9, 10), tajweed_rules=None),
                MappingPos(pos=(10, 11), tajweed_rules=None),
                MappingPos(pos=(11, 12), tajweed_rules=None),
                MappingPos(pos=(12, 13), tajweed_rules=None),
                MappingPos(
                    pos=(13, 15),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="yaa",
                        )
                    ],
                ),
                MappingPos(pos=(15, 16), tajweed_rules=None),
                MappingPos(pos=(16, 17), tajweed_rules=None),
                MappingPos(pos=(17, 18), tajweed_rules=None),
                MappingPos(pos=(18, 19), tajweed_rules=None),
                MappingPos(pos=(19, 20), tajweed_rules=None),
                MappingPos(pos=(20, 21), tajweed_rules=None),
                MappingPos(pos=(21, 22), tajweed_rules=None),
                MappingPos(pos=(22, 23), tajweed_rules=None),
                MappingPos(pos=(23, 24), tajweed_rules=None),
                MappingPos(
                    pos=(24, 26),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="waw",
                        )
                    ],
                ),
                MappingPos(pos=(26, 26), deleted=True),
                MappingPos(pos=(26, 26), deleted=True),
                MappingPos(pos=(26, 27), tajweed_rules=None),
                MappingPos(pos=(27, 28), tajweed_rules=None),
                MappingPos(pos=(28, 29), tajweed_rules=None),
                MappingPos(pos=(29, 30), tajweed_rules=None),
                MappingPos(pos=(30, 31), tajweed_rules=None),
                MappingPos(pos=(31, 35), tajweed_rules=None),
                MappingPos(pos=(35, 35), deleted=True),
                MappingPos(pos=(35, 36), tajweed_rules=None),
                MappingPos(pos=(36, 38), tajweed_rules=None),
                MappingPos(pos=(38, 39), tajweed_rules=None),
                MappingPos(pos=(39, 40), tajweed_rules=None),
                MappingPos(pos=(40, 41), tajweed_rules=None),
                MappingPos(pos=(41, 42), tajweed_rules=None),
                MappingPos(pos=(42, 43), tajweed_rules=None),
                MappingPos(pos=(43, 44), tajweed_rules=None),
                MappingPos(pos=(44, 44), deleted=True),
                MappingPos(pos=(44, 45), tajweed_rules=None),
                MappingPos(pos=(45, 46), tajweed_rules=None),
                MappingPos(pos=(46, 47), tajweed_rules=None),
                MappingPos(pos=(47, 47), deleted=True),
                MappingPos(pos=(47, 48), tajweed_rules=None),
                MappingPos(pos=(48, 49), tajweed_rules=None),
                MappingPos(pos=(49, 50), tajweed_rules=None),
                MappingPos(pos=(50, 51), tajweed_rules=None),
                MappingPos(pos=(51, 52), tajweed_rules=None),
                MappingPos(pos=(52, 55), tajweed_rules=None),
                MappingPos(pos=(55, 56), tajweed_rules=None),
                MappingPos(pos=(56, 57), tajweed_rules=None),
                MappingPos(pos=(57, 58), tajweed_rules=None),
                MappingPos(pos=(58, 58), deleted=True),
                MappingPos(pos=(58, 59), tajweed_rules=None),
                MappingPos(pos=(59, 60), tajweed_rules=None),
                MappingPos(pos=(60, 61), tajweed_rules=None),
                MappingPos(pos=(61, 62), tajweed_rules=None),
                MappingPos(pos=(62, 63), tajweed_rules=None),
                MappingPos(pos=(63, 63), deleted=True),
                MappingPos(pos=(63, 64), tajweed_rules=None),
                MappingPos(pos=(64, 65), tajweed_rules=None),
                MappingPos(pos=(65, 66), tajweed_rules=None),
                MappingPos(pos=(66, 67), tajweed_rules=None),
                MappingPos(pos=(67, 67), deleted=True),
                MappingPos(pos=(67, 68), tajweed_rules=None),
                MappingPos(pos=(68, 69), tajweed_rules=None),
                MappingPos(pos=(69, 70), tajweed_rules=None),
                MappingPos(pos=(70, 71), tajweed_rules=None),
                MappingPos(pos=(71, 71), deleted=True),
                MappingPos(pos=(71, 72), tajweed_rules=None),
                MappingPos(pos=(72, 73), tajweed_rules=None),
                MappingPos(pos=(73, 74), tajweed_rules=None),
                MappingPos(pos=(74, 77), tajweed_rules=None),
                MappingPos(pos=(77, 78), tajweed_rules=None),
                MappingPos(pos=(78, 79), tajweed_rules=None),
                MappingPos(pos=(79, 80), tajweed_rules=None),
                MappingPos(pos=(80, 80), deleted=True),
                MappingPos(pos=(80, 81), tajweed_rules=None),
                MappingPos(pos=(81, 82), tajweed_rules=None),
                MappingPos(pos=(82, 83), tajweed_rules=None),
                MappingPos(pos=(83, 83), deleted=True),
                MappingPos(pos=(83, 84), tajweed_rules=None),
                MappingPos(pos=(84, 85), tajweed_rules=None),
                MappingPos(pos=(85, 86), tajweed_rules=None),
                MappingPos(
                    pos=(86, 88),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="alif",
                        )
                    ],
                ),
                MappingPos(pos=(88, 89), tajweed_rules=None),
                MappingPos(pos=(89, 90), tajweed_rules=None),
                MappingPos(pos=(90, 91), tajweed_rules=None),
                MappingPos(pos=(91, 92), tajweed_rules=None),
                MappingPos(pos=(92, 92), deleted=True),
                MappingPos(pos=(92, 93), tajweed_rules=None),
                MappingPos(pos=(93, 94), tajweed_rules=None),
                MappingPos(pos=(94, 95), tajweed_rules=None),
                MappingPos(pos=(95, 96), tajweed_rules=None),
                MappingPos(pos=(96, 100), tajweed_rules=None),
                MappingPos(pos=(100, 101), tajweed_rules=None),
                MappingPos(pos=(101, 101), deleted=True),
            ],
        ),
        (
            "مِّن مَّا",
            "مِممممَاا",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 1), deleted=True),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 2), deleted=True),
                MappingPos(pos=(2, 2), deleted=True),
                MappingPos(pos=(2, 6), tajweed_rules=None),
                MappingPos(pos=(6, 6), deleted=True),
                MappingPos(pos=(6, 7), tajweed_rules=None),
                MappingPos(pos=(7, 9), tajweed_rules=[NormalMaddRule(tag="alif")]),
            ],
        ),
        (
            "لَكُم مَّا",
            "لَكُممممَاا",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None),
                MappingPos(pos=(1, 2), tajweed_rules=None),
                MappingPos(pos=(2, 3), tajweed_rules=None),
                MappingPos(pos=(3, 4), tajweed_rules=None),
                MappingPos(pos=(4, 4), deleted=True),
                MappingPos(pos=(4, 4), deleted=True),
                MappingPos(pos=(4, 8), tajweed_rules=None),
                MappingPos(pos=(8, 8), deleted=True),
                MappingPos(pos=(8, 9), tajweed_rules=None),
                MappingPos(pos=(9, 11), tajweed_rules=[NormalMaddRule(tag="alif")]),
            ],
        ),
        (
            "الٓمٓ",
            "ءَلِف لَااااااممممِۦۦۦۦۦۦم",
            [
                MappingPos(pos=(0, 6), tajweed_rules=None, deleted=False),
                MappingPos(pos=(6, 14), tajweed_rules=None, deleted=False),
                MappingPos(pos=(14, 14), tajweed_rules=None, deleted=True),
                MappingPos(pos=(14, 26), tajweed_rules=None, deleted=False),
                MappingPos(pos=(26, 26), tajweed_rules=None, deleted=True),
            ],
        ),
        (
            "غِشَـٰوَةٌۭ وَلَهُمْ",
            "غِشَااوَتُوووَلَهُم",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None, deleted=False),
                MappingPos(pos=(1, 2), tajweed_rules=None, deleted=False),
                MappingPos(pos=(2, 3), tajweed_rules=None, deleted=False),
                MappingPos(pos=(3, 4), tajweed_rules=None, deleted=False),
                MappingPos(pos=(4, 4), tajweed_rules=None, deleted=True),
                MappingPos(
                    pos=(4, 6),
                    tajweed_rules=[NormalMaddRule(tag="alif")],
                ),
                MappingPos(pos=(6, 7), tajweed_rules=None, deleted=False),
                MappingPos(pos=(7, 8), tajweed_rules=None, deleted=False),
                MappingPos(pos=(8, 9), tajweed_rules=None, deleted=False),
                MappingPos(pos=(9, 12), tajweed_rules=None, deleted=False),
                MappingPos(
                    pos=(12, 12), tajweed_rules=None, deleted=True
                ),  # determiner
                MappingPos(pos=(12, 12), tajweed_rules=None, deleted=True),  # space
                MappingPos(pos=(12, 13), tajweed_rules=None, deleted=False),
                MappingPos(pos=(13, 14), tajweed_rules=None, deleted=False),
                MappingPos(pos=(14, 15), tajweed_rules=None, deleted=False),
                MappingPos(pos=(15, 16), tajweed_rules=None, deleted=False),
                MappingPos(pos=(16, 17), tajweed_rules=None, deleted=False),
                MappingPos(pos=(17, 18), tajweed_rules=None, deleted=False),
                MappingPos(pos=(18, 19), tajweed_rules=None, deleted=False),
                MappingPos(pos=(19, 19), tajweed_rules=None, deleted=True),
            ],
        ),
        (
            "قَلِيلًۭا مِّمَّا",
            "قَلِۦۦلَممممِممممَاا",
            [
                MappingPos(pos=(0, 1), tajweed_rules=None, deleted=False),
                MappingPos(pos=(1, 2), tajweed_rules=None, deleted=False),
                MappingPos(pos=(2, 3), tajweed_rules=None, deleted=False),
                MappingPos(pos=(3, 4), tajweed_rules=None, deleted=False),
                MappingPos(
                    pos=(4, 6),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="yaa",
                        )
                    ],
                ),
                MappingPos(pos=(6, 7), tajweed_rules=None, deleted=False),
                MappingPos(pos=(7, 8), tajweed_rules=None, deleted=False),
                MappingPos(pos=(8, 8), tajweed_rules=None, deleted=True),
                MappingPos(pos=(8, 8), tajweed_rules=None, deleted=True),
                MappingPos(pos=(8, 8), tajweed_rules=None, deleted=True),
                MappingPos(pos=(8, 12), tajweed_rules=None, deleted=False),
                MappingPos(pos=(12, 12), tajweed_rules=None, deleted=True),
                MappingPos(pos=(12, 13), tajweed_rules=None, deleted=False),
                MappingPos(pos=(13, 17), tajweed_rules=None, deleted=False),
                MappingPos(pos=(17, 17), tajweed_rules=None, deleted=True),
                MappingPos(pos=(17, 18), tajweed_rules=None, deleted=False),
                MappingPos(
                    pos=(18, 20),
                    tajweed_rules=[
                        NormalMaddRule(
                            tag="alif",
                        )
                    ],
                    deleted=False,
                ),
            ],
        ),
    ],
)
def test_phonetizer_with_mappings(
    uth_text: str, ph_text, exp_mappings: MappingListType
):
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    ph_out = quran_phonetizer(uth_text, moshaf)
    print(uth_text)
    print(ph_out.phonemes)
    print(ph_out.mappings)

    assert ph_out.phonemes == ph_text
    assert exp_mappings == ph_out.mappings
    for idx, uth_c in enumerate(uth_text):
        print(f"UTH_IDX: `{idx}`, SPAN: `{ph_out.mappings[idx]}`")
        ph_c = ""
        mapping = ph_out.mappings[idx]
        if mapping is not None:
            ph_c = ph_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")

        print("-" * 40)


def test_sub_with_mapping_stress_test():
    start_aya = Aya()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    for aya in start_aya.get_ayat_after():
        uthmani_text = aya.get().uthmani
        print(f"UTH:\n{uthmani_text}")
        ph_out = quran_phonetizer(uthmani_text, moshaf, remove_spaces=True)
        # Ensuring that space is not assigned to any mapping
        get_uth_word_boundaries_in_ph(uthmani_text, ph_out.mappings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
