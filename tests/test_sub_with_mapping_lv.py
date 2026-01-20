from Levenshtein import opcodes

from quran_transcript.phonetics.conv_base_operation import MappingPos
from quran_transcript.phonetics.tajweed_rulses import NormalMaddRule, TajweedRule


"""
Taks: 
I have sequential re.sub operation I want to be able to map every char in the output string to the input string
the function takes previous mapping and returns the new mapping from the first input to the fresh new substiuted string.
Use Levenestein opcdes for this task:

The regs are complicated so try to be wise the regs are in: quran_transcript.phonetics.operations
Make your changes are here so I will plant in the code later

opcodes docs:
    Find sequence of edit operations transforming one string to another.

    opcodes(source_string, destination_string)
    opcodes(edit_operations, source_length, destination_length)

    The result is a list of 5-tuples with the same meaning as in
    SequenceMatcher's get_opcodes() output.  But since the algorithms
    differ, the actual sequences from Levenshtein and SequenceMatcher
    may differ too.

    Examples
    --------
    >>> for x in opcodes('spam', 'park'):
    ...     print(x)
    ...
    ('delete', 0, 1, 0, 0)
    ('equal', 1, 3, 0, 2)
    ('insert', 3, 3, 2, 3)
    ('replace', 3, 4, 3, 4)

    The alternate form opcodes(editops, source_string, destination_string)
    can be used for conversion from editops (triples) to opcodes (you can
    pass strings or their lengths, it doesn't matter).

"""

out = [
    MappingPos(pos=(0, 3)),
    MappingPos(pos=(3, 4)),
    MappingPos(pos=(4, 5)),
    MappingPos(pos=(5, 6)),
]


def sub_with_mapping(
    pattaern: str,
    repl,
    text: str,
    mappings: list[MappingPos | None] | None = None,
    tajweed_rule: TajweedRule | None = None,
) -> tuple[str, MappingPos]:
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
