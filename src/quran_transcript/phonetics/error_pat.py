from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from quran_transcript.phonetics.tajweed_rulses import (
    FullTajweedRuleType,
    TajweedRuleType,
)

from .tajweed_rulses import ExplainedTajweedRule

TashkeelErrorType: TypeAlias = Literal["fatha", "dama", "kasra", "skoon"]


@dataclass(frozen=True)
class PhonemesGroupsAligment:
    op_type: Literal["insert", "replace", "delete", "equal"]
    ref_idx: int
    pred_idx: int


@dataclass(frozen=True)
class ReciterError:
    """A single recitation error.

    Tajweed rule fields contain :class:`ExplainedTajweedRule` snapshots, ready
    for display or serialization.
    """

    uthmani_pos: tuple[int, int]  # start, end
    ph_pos: tuple[int, int]  # start, end
    error_type: Literal["tajweed", "normal", "tashkeel"]
    speech_error_type: Literal["insert", "delete", "replace"]
    expected_ph: str
    preditected_ph: str
    expected_len: int = -1
    predicted_len: int = -1
    expected_tashkeel: TashkeelErrorType | None = None
    predicted_tashkeel: TashkeelErrorType | None = None
    ref_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)
    inserted_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)
    replaced_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)
    missing_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)


class ReciterErrPatern:
    def __init__(self, pat: str, rules: dict[str, TajweedRuleType]) -> None:
        """A minimal layer over re to detect reciters errors and return coreespoding
        human readable output to the user

        Rules:
        * This a minimal layer on top of re to cature error patterns in predicted phonemes groups by the [R]eciter
        * The Reciter Error pattern is trying to match the predicted phonemes by a reciter to detect error pattern to
          return human readable reciter error
        * `pat` should start with `R:` [R]eciter
        * EX: pat = r"<e,t0:abc><i:d>"
        <e,t0:abc>
        ^^ ^     ^
        -^-^------  This is called a `tag` These brackets `<..>` holds the pattern and is not related to re gropus.
         ^ ^
         ^ - > `e` is called **operation type** and can be out of 4 valude: `e`: equal, `i`: insert, `r`: replace, or `d`: delete
           ^ - > `t0` is called  the **tag name** and composed only of a single charcter and it can followed by a number like `x`, `y3` and it is optional
         `abc` is called `tag pattern`; every character in the tag pattern represents the first chacter of each phonemes group

        * pat patterns Have to be connected like r"<d,t0:ABC><r:m>" but not r"<d,t0:ABC>N<r:m>" ->  ParserError `N` should be included in a tag
        * tag names have to be unique; repeating a tag raises

        * for `e` equal, `d`: delete, `r`: replace operations it is optinal to add **tag name** like r"R:<e:abc>" or r"R:<e,x:abc>",
          ,r"R:<d:abc>" or r"R:<d,x:abc>", r"R:<r:abc>" or r"R:<r,x:abc>"
        * for `insert` operation it is not allowed to add **tag name** you will get parser error like: r"R:<i,x:abc>"

        * **tag names** should b compose of a single small case character followed by a single digit like `m0`, `m` not `x11` or `M`
        * if a **tag name** is found in the rules but not in the pat you will get a tag not found error


        Limitation:
        * not supporting named group followed by the end of tag brackets in `rep` like this: `r"<x:X><r:\\g<c>>"`
                                               -------------------------------------------------------------^
        Because the parser will think that the end of named group is the group name closing

        """
        assert pat.startswith("R:")

    def match(
        self,
        ref_ph_gropuhs: list[str],
        pred_ph_gropus: list[str],
        ph_groups_align: list[PhonemesGroupsAligment],
        ref_ph_groupt_rule_types: list[list[FullTajweedRuleType]],
    ) -> ReciterError:
        """

        # thinking with you opencode:
        * I'm thinkig for gropus take the first char and at:  i, e, r, d at the begnning
        * for the the pat we will append i, e, r, d in the pat also like <e,t1:abc> tag text become in the parser eabc
        * we all have arabic letters so no problem about this implementation

        What do you think opencode about this implementation
        * use ideas and code quality same as conv_base_operation QuranReWithMapping but do not resue the code unless no conflicts no problems
        """
        ...
