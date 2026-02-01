import re
import diff_match_patch as dmp_module
from typing import List, Tuple, Optional, Union, Callable


def apply_regex_with_mapping(
    pattern: Union[str, re.Pattern],
    repl: Union[str, Callable[[re.Match], str]],
    text: str,
    prev_mapping: Optional[List[List[int]]] = None,
) -> Tuple[str, List[List[int]]]:
    """
    Apply a regex substitution and return character-level mapping from INPUT to OUTPUT indices.

    This function applies a single regex pattern to the input text and returns:
    1. The transformed text after substitution
    2. A mapping that shows which positions in the INPUT text contribute to each position in the OUTPUT text

    Args:
        pattern: Regex pattern (string or compiled pattern)
        repl: Replacement string or callable. If string, can contain backreferences like \\1.
              If callable, should accept a match object and return replacement string.
        text: Input text to apply regex to
        prev_mapping: Optional mapping from PREVIOUS operations. This allows chaining multiple
                     regex operations while maintaining mapping back to ORIGINAL input.
                     prev_mapping[i] = list of positions in the ORIGINAL input that
                     contribute to character i in the current input text.

    Returns:
        Tuple of (new_text, new_mapping) where:
        - new_text: The text after applying the regex substitution
        - new_mapping: A list where new_mapping[i] = list of positions in the ORIGINAL input text
                      that contribute to character i in new_text.

        If prev_mapping is None, new_mapping maps from the input text to itself.
        If prev_mapping is provided, new_mapping maps from the ORIGINAL input (before any
        previous operations) to the new output.

    Example:
        # Simple usage without chaining:
        text = "Hello 123 world"
        new_text, mapping = apply_regex_with_mapping(r"\d+", "NUM", text)
        # mapping[i] shows which characters in "Hello 123 world" contribute to character i in new_text

        # Chaining operations:
        text = "Hello 123 world"
        result1, map1 = apply_regex_with_mapping(r"\d+", "NUM", text)
        result2, map2 = apply_regex_with_mapping(r"world", "earth", result1, map1)
        # map2[i] shows which characters in ORIGINAL "Hello 123 world" contribute to character i in result2
    """

    # Apply the regex substitution
    new_text = re.sub(pattern, repl, text)

    # Initialize diff-match-patch
    dmp = dmp_module.diff_match_patch()

    # Compute differences between input and output
    diffs = dmp.diff_main(text, new_text)
    dmp.diff_cleanupSemantic(diffs)  # Clean up for better grouping

    # If no previous mapping provided, assume identity mapping
    # (each character in input maps to itself)
    if prev_mapping is None:
        # Create identity mapping: input position i contributes to output position i
        input_to_output = [[i] for i in range(len(text))]
    else:
        # We have mapping from ORIGINAL to CURRENT input
        # We need to invert it to get from CURRENT input to ORIGINAL
        current_to_original = [[] for _ in range(len(text))]
        for orig_pos, current_positions in enumerate(prev_mapping):
            for current_pos in current_positions:
                if current_pos < len(current_to_original):
                    current_to_original[current_pos].append(orig_pos)
        input_to_output = current_to_original

    # Process diffs to build output mapping
    # We'll build output_to_original: for each position in output, which original positions?
    output_to_original = []

    # Track position in input text
    input_pos = 0

    for op, content in diffs:
        content_len = len(content)

        if op == 0:  # EQUAL - content unchanged
            # Copy mapping from input to output
            for i in range(content_len):
                if input_pos + i < len(input_to_output):
                    output_to_original.append(input_to_output[input_pos + i].copy())
                else:
                    output_to_original.append([])
            input_pos += content_len

        elif op == 1:  # INSERT - new content added
            # New content has no corresponding input characters
            for _ in range(content_len):
                output_to_original.append([])
            # input_pos doesn't change

        elif op == -1:  # DELETE - content removed
            # Content removed: propagate its source positions to surrounding context
            # Collect all original positions from the deleted segment
            deleted_sources = set()
            for i in range(content_len):
                if input_pos + i < len(input_to_output):
                    deleted_sources.update(input_to_output[input_pos + i])

            # Add deleted sources to the previous character in output (if any)
            if output_to_original and deleted_sources:
                output_to_original[-1].extend(deleted_sources)

            input_pos += content_len

    # Now invert to get the final mapping: ORIGINAL -> OUTPUT positions
    # If prev_mapping was provided, we're mapping ORIGINAL -> FINAL
    # If prev_mapping was None, we're mapping INPUT -> OUTPUT
    if prev_mapping is None:
        original_length = len(text)
    else:
        original_length = len(prev_mapping)

    final_mapping = [[] for _ in range(original_length)]

    for output_pos, original_positions in enumerate(output_to_original):
        for orig_pos in original_positions:
            if orig_pos < len(final_mapping):
                final_mapping[orig_pos].append(output_pos)

    return new_text, final_mapping


def apply_sequential_regex_mappings(
    text: str,
    patterns: List[
        Tuple[Union[str, re.Pattern], Union[str, Callable[[re.Match], str]]]
    ],
) -> Tuple[str, List[List[int]]]:
    """
    Apply multiple regex patterns sequentially while maintaining mapping back to original input.

    Args:
        text: Original input text
        patterns: List of (pattern, replacement) tuples to apply in order

    Returns:
        Tuple of (final_text, mapping) where:
        - final_text: Text after applying all regex patterns
        - mapping: A list where mapping[i] = list of positions in final_text that
                  the i-th character of the ORIGINAL text contributes to.

    Example:
        text = "Hello 123 world!"
        patterns = [
            (r"\\d+", "NUM"),
            (r"world", "earth"),
            (r"\\s+", " "),
        ]
        final, mapping = apply_sequential_regex_mappings(text, patterns)
        # mapping[6] might be [6, 7, 8] showing that original '1' at position 6
        # contributes to output positions 6, 7, and 8 (in "NUM")
    """
    current_text = text
    current_mapping = None  # Start with no mapping (identity will be created)

    for pattern, repl in patterns:
        current_text, current_mapping = apply_regex_with_mapping(
            pattern, repl, current_text, current_mapping
        )

    return current_text, current_mapping


# Example usage and demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("EXAMPLE 1: Single regex without previous mapping")
    print("=" * 60)

    text = "Hello 123 world!"
    pattern = r"(\d+)"
    replacement = r"NUM\1"

    result, mapping = apply_regex_with_mapping(pattern, replacement, text)
    print(mapping)

    print(f"Input text:    '{text}'")
    print(f"Pattern:       {pattern}")
    print(f"Replacement:   {replacement}")
    print(f"Output text:   '{result}'")
    print()
    print("Mapping (INPUT -> OUTPUT indices):")
    print("Format: input_position -> list of output_positions")
    print()

    for i, char in enumerate(text):
        output_positions = mapping[i]
        output_chars = (
            [result[pos] for pos in output_positions] if output_positions else []
        )
        print(
            f"  Input position {i:2} ('{char}'): → Output positions {output_positions} (chars: {output_chars})"
        )

    print("\n" + "=" * 60)
    print("EXAMPLE 2: Chaining multiple regex operations")
    print("=" * 60)

    text = "The price is $99.99 today"
    patterns = [
        (r"\$(\d+)", r"USD\1"),
        (r"(\d+)\.(\d+)", r"\1.\2 dollars"),
        (r"\s+", " "),  # Normalize spaces
    ]

    final, final_mapping = apply_sequential_regex_mappings(text, patterns)

    print(f"Original text: '{text}'")
    for i, (pat, repl) in enumerate(patterns, 1):
        print(f"  Step {i}: {pat} -> {repl}")
    print(f"Final text:    '{final}'")
    print()

    # Show mapping for specific interesting characters
    print("Character mapping (ORIGINAL -> FINAL):")
    print()

    # Find interesting positions in original text
    interesting_positions = []
    for i, char in enumerate(text):
        if char.isdigit() or char == "$" or char == ".":
            interesting_positions.append(i)

    for pos in interesting_positions:
        output_positions = final_mapping[pos]
        output_chars = [final[p] for p in output_positions] if output_positions else []
        print(
            f"  Original position {pos:2} ('{text[pos]}'): → Final positions {output_positions} (chars: {output_chars})"
        )

    print("\n" + "=" * 60)
    print("EXAMPLE 3: Deletion and insertion")
    print("=" * 60)

    text = "Remove 123 and 456 numbers"
    patterns = [
        (r"\d+", ""),  # Delete all numbers
        (r"\s+", " "),  # Normalize spaces
    ]

    final, mapping = apply_sequential_regex_mappings(text, patterns)

    print(f"Original: '{text}'")
    print(f"Final:    '{final}'")
    print()
    print("Mapping for deleted characters (should be empty):")

    for i, char in enumerate(text):
        if char.isdigit():
            output_positions = mapping[i]
            print(
                f"  Original digit '{char}' at position {i}: → Output positions {output_positions}"
            )

    print("\n" + "=" * 60)
    print("Querying the mapping:")
    print("=" * 60)

    # Helper function to query mapping
    def query_mapping(
        original_text: str,
        final_text: str,
        mapping: List[List[int]],
        query_positions: List[int],
    ) -> None:
        """Query the mapping for specific positions"""
        for pos in query_positions:
            if pos < len(mapping):
                output_positions = mapping[pos]
                if output_positions:
                    chars_in_final = [final_text[p] for p in output_positions]
                    print(
                        f"Original position {pos} ('{original_text[pos]}') → "
                        f"Final positions {output_positions} (chars: {chars_in_final})"
                    )
                else:
                    print(
                        f"Original position {pos} ('{original_text[pos]}') → "
                        f"DELETED (no positions in final text)"
                    )

    # Query specific positions
    query_positions = [6, 7, 8, 9]  # Positions of "123 " in original
    query_mapping(text, final, mapping, query_positions)
