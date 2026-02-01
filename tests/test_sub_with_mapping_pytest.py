import pytest
import sys
import os


from quran_transcript.phonetics.conv_base_operation import (
    MappingPos,
    sub_with_mapping,
    merge_mappings,
)

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
                None,
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
                None,
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
                None,
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
                None,
                MappingPos(pos=(4, 5), tajweed_rules=None),
                None,
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
        if mapping is not None:
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
        new_mappings: list[MappingPos | None] = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        result = merge_mappings(None, new_mappings)
        assert result == new_mappings

    def test_merge_mappings_identity(self):
        """Test simple identity mapping - should preserve positions."""
        mappings: list[MappingPos | None] = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        new_mappings: list[MappingPos | None] = [
            MappingPos(pos=(0, 1)),
            MappingPos(pos=(1, 2)),
            MappingPos(pos=(2, 3)),
        ]

        expected: list[MappingPos | None] = [
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
            None,  # Missing position
            MappingPos(pos=(1, 2)),
            None,
        ]

        expected = [
            MappingPos(pos=(0, 2)),  # Should span from first to last non-None
            None,
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
                    None,
                    MappingPos(pos=(0, 1)),
                    None,
                    MappingPos(pos=(2, 3)),
                    MappingPos(pos=(3, 6)),
                    None,
                ],
                [
                    MappingPos(pos=(0, 1)),
                    MappingPos(pos=(2, 6)),
                    None,
                ],  # Should span first to last non-None
            ),
            # Test partial None mappings - some positions in range are None
            (
                [MappingPos(pos=(0, 3))],
                [MappingPos(pos=(0, 1)), None, MappingPos(pos=(2, 3))],
                [MappingPos(pos=(0, 3))],  # Should span first to last non-None
            ),
            # Test single mapping to multiple new mappings
            (
                [MappingPos(pos=(1, 2))],
                [None, MappingPos(pos=(1, 2))],
                [MappingPos(pos=(1, 2))],  # Should get the non-None range
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
                [None],
                [None],  # Should use end position only
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
        result = merge_mappings([], [])
        assert result == []

        # Empty mappings, non-empty new_mappings
        new_mappings = [MappingPos(pos=(0, 1))]
        result = merge_mappings([], new_mappings)
        assert result == []

        # Non-empty mappings, empty new_mappings
        mappings = [MappingPos(pos=(0, 1))]
        result = merge_mappings(mappings, [])
        assert result == [None]

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
            None,  # Gap
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
