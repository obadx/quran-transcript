import pytest

from quran_transcript import alphabet as alph
from quran_transcript.phonetics.error_pat import (
    PhonemesGroupsAligment,
    ReciterErrPatern,
    ReciterErrPatParsingError,
    _encode_alignments,
)
from quran_transcript.phonetics.tajweed_rulses import (
    TajweedRuleMetadata,
    TajweedRuleType,
)

PH = alph.phonetics
QAF = PH.qaf
KAF = PH.kaf
FATHA = PH.fatha
ALIF = PH.alif
MEEM = PH.meem


def align(op_type, ref_idx, pred_idx) -> PhonemesGroupsAligment:
    return PhonemesGroupsAligment(
        op_type=op_type,
        ref_idx=ref_idx,
        pred_idx=pred_idx,
    )


def meta(
    rule_type: TajweedRuleType,
    pivot: tuple[int, int] = (0, 1),
) -> TajweedRuleMetadata:
    return TajweedRuleMetadata(
        pivot=pivot,
        deps=[],
        tag="tag",
        rule_type=rule_type,
    )


# ---------------------------------------------------------------- Parser


@pytest.mark.parametrize(
    "pat,rules",
    [
        (r"R:<e:ABC>", {}),
        (r"R:<e,t0:ABC>", {"t0": TajweedRuleType.NORMAL_MADD}),
        (r"R:<e,t0:ABC><i:D>", {"t0": TajweedRuleType.NORMAL_MADD}),
        (r"R:<d,t2:E>", {"t2": TajweedRuleType.QALQALAH}),
        (r"R:<r,t3:X>", {"t3": TajweedRuleType.QALQALAH}),
        (r"R:<e,t0:A><e,t1:B>", {"t0": TajweedRuleType.NORMAL_MADD}),
    ],
)
def test_parser_valid_patterns(pat, rules):
    err_pat = ReciterErrPatern(pat, rules)
    assert err_pat.re_pat.pattern


def test_parser_rejects_repeated_tag_name():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(
            r"R:<e,t0:A><e,t0:B>",
            {"t0": TajweedRuleType.NORMAL_MADD},
        )


def test_parser_rejects_named_insert():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(r"R:<i,t0:A>", {"t0": TajweedRuleType.NORMAL_MADD})


@pytest.mark.parametrize(
    "pat",
    [
        r"R:abc<e:A>",
        r"R:<e:A>abc",
        r"R:<e:A>abc<e:B>",
        r"R:<e:A>>",
        r"R:",
    ],
)
def test_parser_rejects_disconnected_or_empty_patterns(pat):
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(pat, {})


def test_parser_requires_r_prefix():
    with pytest.raises(AssertionError):
        ReciterErrPatern(r"<e:A>", {})


def test_parser_rejects_empty_tag_pattern():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(r"R:<e:>", {})


def test_parser_rejects_empty_matching_tag_pattern():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(rf"R:<e:{ALIF}*>", {})


def test_parser_rejects_invalid_tag_regex():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(r"R:<e:[ا>", {})


def test_parser_rejects_rules_tag_absent_from_pattern():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(
            r"R:<e:A>",
            {"t0": TajweedRuleType.NORMAL_MADD},
        )


def test_parser_rejects_unknown_err_tag():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(
            r"R:<e,t0:A>",
            {"t0": TajweedRuleType.NORMAL_MADD},
            err_tag="t1",
        )


def test_parser_rejects_non_tajweed_rule_value():
    with pytest.raises(ReciterErrPatParsingError):
        ReciterErrPatern(
            r"R:<e,t0:A>",
            {"t0": "NORMAL_MADD"},
        )


# ------------------------------------------------------- Pattern compilation


def test_pattern_compilation_equal_then_insert():
    err_pat = ReciterErrPatern(
        r"R:<e,t0:ABC><i:D>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )
    assert err_pat.re_pat.pattern == r"e(?:ABC)i(?:D)"


def test_pattern_compilation_shares_op_prefix_for_same_op_run():
    err_pat = ReciterErrPatern(r"R:<e,t0:A><e,t1:B>", {})
    assert err_pat.re_pat.pattern == r"e(?:A)(?:B)"
    assert err_pat.re_pat.fullmatch("eAB") is not None


def test_pattern_compilation_preserves_alternation():
    err_pat = ReciterErrPatern(r"R:<e,t0:A|B>", {})
    assert err_pat.re_pat.pattern == r"e(?:A|B)"
    assert err_pat.re_pat.fullmatch("eA") is not None
    assert err_pat.re_pat.fullmatch("eB") is not None
    assert err_pat.re_pat.fullmatch("eAB") is None


def test_pattern_compilation_preserves_user_group_numbering():
    err_pat = ReciterErrPatern(r"R:<e,t0:(A)\1>", {})
    assert err_pat.re_pat.pattern == r"e(?:(A)\1)"
    match = err_pat.re_pat.fullmatch("eAA")
    assert match is not None
    assert match.group(1) == "A"
    assert err_pat.re_pat.groups == 1


def test_pattern_compilation_tag_names_do_not_add_groups():
    err_pat = ReciterErrPatern(r"R:<e,t0:ABC>", {})
    assert err_pat.re_pat.pattern == r"e(?:ABC)"
    assert err_pat.re_pat.groups == 0


# ---------------------------------------------------------------- Encoding


def test_encode_alignments():
    ref_ph_groups = ["A", "B", "C", "E"]
    pred_ph_groups = ["A", "B", "C", "D"]
    alignments = [
        align("equal", 0, 0),
        align("equal", 1, 1),
        align("equal", 2, 2),
        align("insert", 3, 3),
        align("delete", 3, 4),
    ]

    encoded, enc_to_align = _encode_alignments(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
    )

    assert encoded == "eABCiDdE"
    assert enc_to_align == [0, 0, 1, 2, 3, 3, 4, 4, 5]


def test_encode_alignments_uses_reference_for_delete_and_predicted_for_replace():
    ref_ph_groups = ["A"]
    pred_ph_groups = ["B"]
    alignments = [align("replace", 0, 0)]

    encoded, enc_to_align = _encode_alignments(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
    )

    assert encoded == "rB"
    assert enc_to_align == [0, 0, 1]


# ---------------------------------------------------------------- Matching


def test_find_all_equal_then_insert():
    ref_ph_groups = ["A", "B", "C", "E"]
    pred_ph_groups = ["A", "B", "C", "D"]
    alignments = [
        align("equal", 0, 0),
        align("equal", 1, 1),
        align("equal", 2, 2),
        align("insert", 3, 3),
        align("delete", 3, 4),
    ]
    ref_group_rules = [
        [meta(TajweedRuleType.NORMAL_MADD, pivot=(0, 2))],
        [],
        [],
        [],
    ]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:ABC><i:D>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules,
        ref_ph_to_uthmani=[0, 1, 2, 3, 4],
    )

    assert len(errors) == 1
    err = errors[0]
    assert err.expected_ph == "ABC"
    assert err.preditected_ph == "ABCD"
    assert err.ph_pos == (0, 3)
    assert err.uthmani_pos == (0, 3)
    assert err.error_type == "tajweed"
    assert err.speech_error_type == "insert"
    assert err.expected_len == 2
    assert err.predicted_len == 4
    assert [rule.rule_type for rule in err.ref_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD
    ]


def test_find_all_replace_matches_predicted_side():
    ref_ph_groups = [QAF + FATHA]
    pred_ph_groups = [KAF]
    alignments = [align("replace", 0, 0)]

    errors = ReciterErrPatern(rf"R:<r:{KAF}>", {}).find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 0, 1],
    )
    assert len(errors) == 1
    err = errors[0]
    assert err.expected_ph == QAF + FATHA
    assert err.preditected_ph == KAF
    assert err.error_type == "normal"
    assert err.speech_error_type == "replace"
    assert err.ph_pos == (0, 2)
    assert err.uthmani_pos == (0, 1)

    errors = ReciterErrPatern(rf"R:<r:{QAF}>", {}).find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 0, 1],
    )
    assert errors == []


def test_find_all_delete_matches_reference_side():
    ref_ph_groups = [QAF + FATHA]
    pred_ph_groups: list[str] = []
    alignments = [align("delete", 0, 0)]

    errors = ReciterErrPatern(rf"R:<d:{QAF}>", {}).find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 0, 1],
    )
    assert len(errors) == 1
    err = errors[0]
    assert err.expected_ph == QAF + FATHA
    assert err.preditected_ph == ""
    assert err.speech_error_type == "delete"
    assert err.ph_pos == (0, 2)
    assert err.uthmani_pos == (0, 1)

    errors = ReciterErrPatern(rf"R:<d:{KAF}>", {}).find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 0, 1],
    )
    assert errors == []


def test_find_all_insert_matches_predicted_side():
    ref_ph_groups: list[str] = []
    pred_ph_groups = [MEEM]
    alignments = [align("insert", 0, 0)]

    errors = ReciterErrPatern(rf"R:<i:{MEEM}>", {}).find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[],
        ref_ph_to_uthmani=[0],
    )
    assert len(errors) == 1
    err = errors[0]
    assert err.expected_ph == ""
    assert err.preditected_ph == MEEM
    assert err.speech_error_type == "insert"
    assert err.ph_pos == (0, 0)
    assert err.uthmani_pos == (0, 0)

    errors = ReciterErrPatern(rf"R:<i:{KAF}>", {}).find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[],
        ref_ph_to_uthmani=[0],
    )
    assert errors == []


def test_find_all_with_user_backreference():
    ref_ph_groups = ["A", "A"]
    pred_ph_groups = ["A", "A", "B"]
    alignments = [
        align("equal", 0, 0),
        align("equal", 1, 1),
        align("insert", 2, 2),
    ]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:(A)\1><i:B>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)], []],
        ref_ph_to_uthmani=[0, 1, 2, 3],
    )
    assert len(errors) == 1
    assert errors[0].expected_ph == "AA"
    assert errors[0].preditected_ph == "AAB"
    assert errors[0].speech_error_type == "insert"


def test_find_all_strict_rule_lookup_failure_skips_match():
    ref_ph_groups = ["A"]
    pred_ph_groups = ["A"]
    alignments = [align("equal", 0, 0)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert errors == []


def test_find_all_strict_rule_lookup_success():
    ref_ph_groups = ["A"]
    pred_ph_groups = ["A"]
    alignments = [align("equal", 0, 0)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert len(errors) == 1
    assert errors[0].error_type == "tajweed"
    assert [rule.rule_type for rule in errors[0].ref_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD
    ]


def test_find_all_matches_err_tag_anchors_error_span():
    ref_ph_groups = ["A", "B"]
    pred_ph_groups = ["A", "B"]
    alignments = [align("equal", 0, 0), align("equal", 1, 1)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A><e,t1:B>",
        {
            "t0": TajweedRuleType.NORMAL_MADD,
            "t1": TajweedRuleType.QALQALAH,
        },
        err_tag="t1",
    )

    matches = err_pat.find_all_matches(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[
            [meta(TajweedRuleType.NORMAL_MADD)],
            [meta(TajweedRuleType.QALQALAH, pivot=(1, 2))],
        ],
        ref_ph_to_uthmani=[0, 1, 2],
    )
    assert len(matches.errors) == 1
    err = matches.errors[0]
    assert err.expected_ph == "B"
    assert err.preditected_ph == "B"
    assert err.ph_pos == (1, 2)
    assert err.uthmani_pos == (1, 2)
    assert [rule.rule_type for rule in err.ref_tajweed_rules] == [
        TajweedRuleType.QALQALAH
    ]
    assert matches.covered_alignments == frozenset(alignments)


def test_find_all_matches_empty_err_tag_uses_whole_match():
    ref_ph_groups = ["A", "B"]
    pred_ph_groups = ["A", "B"]
    alignments = [align("equal", 0, 0), align("equal", 1, 1)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A><e,t1:B>",
        {
            "t0": TajweedRuleType.NORMAL_MADD,
            "t1": TajweedRuleType.QALQALAH,
        },
    )

    matches = err_pat.find_all_matches(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[
            [meta(TajweedRuleType.NORMAL_MADD)],
            [meta(TajweedRuleType.QALQALAH, pivot=(1, 2))],
        ],
        ref_ph_to_uthmani=[0, 1, 2],
    )
    assert len(matches.errors) == 1
    err = matches.errors[0]
    assert err.expected_ph == "AB"
    assert err.preditected_ph == "AB"
    assert err.ph_pos == (0, 2)
    assert err.uthmani_pos == (0, 2)
    assert [rule.rule_type for rule in err.ref_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD,
        TajweedRuleType.QALQALAH,
    ]
    assert matches.covered_alignments == frozenset(alignments)


def test_find_all_matches_reports_covered_alignments():
    ref_ph_groups = ["A"]
    pred_ph_groups = ["B", "A"]
    alignments = [align("insert", 0, 0), align("equal", 0, 1)]
    err_pat = ReciterErrPatern(
        r"R:<i:B><e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    matches = err_pat.find_all_matches(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert len(matches.errors) == 1
    assert matches.covered_alignments == frozenset(alignments)


def test_find_all_matches_does_not_cover_rejected_match():
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    matches = err_pat.find_all_matches(
        ref_ph_groups=["A"],
        pred_ph_groups=["A"],
        ph_groups_align=[align("equal", 0, 0)],
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert matches.errors == []
    assert matches.covered_alignments == frozenset()


def test_find_all_matches_does_not_cover_match_without_error():
    err_pat = ReciterErrPatern(r"R:<e:A>", {})

    matches = err_pat.find_all_matches(
        ref_ph_groups=["A"],
        pred_ph_groups=["A"],
        ph_groups_align=[align("equal", 0, 0)],
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert matches.errors == []
    assert matches.covered_alignments == frozenset()


def test_find_all_matches_covers_only_consumed_alignments():
    ref_ph_groups = ["A", "B"]
    pred_ph_groups = ["A", "B"]
    alignments = [align("equal", 0, 0), align("equal", 1, 1)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    matches = err_pat.find_all_matches(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)], []],
        ref_ph_to_uthmani=[0, 1, 2],
    )
    assert len(matches.errors) == 1
    assert matches.covered_alignments == frozenset({alignments[0]})


def test_find_all_strict_rule_lookup_uses_union_of_reference_groups():
    ref_ph_groups = ["A", "B"]
    pred_ph_groups = ["A", "B"]
    alignments = [align("equal", 0, 0), align("equal", 1, 1)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:AB>",
        {"t0": TajweedRuleType.QALQALAH},
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[], [meta(TajweedRuleType.QALQALAH, pivot=(1, 2))]],
        ref_ph_to_uthmani=[0, 1, 2],
    )
    assert len(errors) == 1


def test_find_all_collects_all_rules_in_matched_span():
    ref_ph_groups = ["A", "B"]
    pred_ph_groups = ["A", "B"]
    alignments = [align("equal", 0, 0), align("equal", 1, 1)]
    err_pat = ReciterErrPatern(r"R:<e:AB>", {})

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[
            [meta(TajweedRuleType.NORMAL_MADD, pivot=(0, 2))],
            [meta(TajweedRuleType.QALQALAH, pivot=(1, 2))],
        ],
        ref_ph_to_uthmani=[0, 1, 2],
    )
    assert len(errors) == 1
    assert [rule.rule_type for rule in errors[0].ref_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD,
        TajweedRuleType.QALQALAH,
    ]


def test_find_all_includes_static_rule_lists_as_declared():
    ref_ph_groups = ["A"]
    pred_ph_groups = ["A"]
    alignments = [align("equal", 0, 0)]
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
        inserted_tajweed_rules=[
            TajweedRuleType.LEEN_MADD,
            TajweedRuleType.NORMAL_MADD,
        ],
        replaced_tajweed_rules=[TajweedRuleType.NORMAL_MADD],
        missing_tajweed_rules=[TajweedRuleType.LEEN_MADD],
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert len(errors) == 1
    err = errors[0]
    assert [rule.rule_type for rule in err.inserted_tajweed_rules] == [
        TajweedRuleType.LEEN_MADD,
        TajweedRuleType.NORMAL_MADD,
    ]
    assert [rule.rule_type for rule in err.replaced_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD
    ]
    assert [rule.rule_type for rule in err.missing_tajweed_rules] == [
        TajweedRuleType.LEEN_MADD
    ]

    for rule in (
        *err.inserted_tajweed_rules,
        *err.replaced_tajweed_rules,
        *err.missing_tajweed_rules,
    ):
        assert rule.ph_pivot == (-1, -1)
        assert rule.ph_deps == []
        assert rule.tag == ""
        assert rule.uth_pivot == (-1, -1)
        assert rule.uth_deps == []
        assert rule.golden_len == -1
        assert rule.name.en


def test_find_all_includes_static_replaced_rule_absent_from_reference():
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
        replaced_tajweed_rules=[TajweedRuleType.IZHAR_NOON],
    )

    errors = err_pat.find_all(
        ref_ph_groups=["A"],
        pred_ph_groups=["A"],
        ph_groups_align=[align("equal", 0, 0)],
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert len(errors) == 1
    err = errors[0]
    assert [rule.rule_type for rule in err.ref_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD
    ]
    assert [rule.rule_type for rule in err.replaced_tajweed_rules] == [
        TajweedRuleType.IZHAR_NOON
    ]
    assert err.replaced_tajweed_rules[0].ph_pivot == (-1, -1)
    assert err.replaced_tajweed_rules[0].uth_pivot == (-1, -1)
    assert err.replaced_tajweed_rules[0].golden_len == -1


def test_find_all_fills_expected_and_predicted_lengths_for_madd():
    ref_ph_groups = [QAF + FATHA, ALIF + ALIF]
    pred_ph_groups = [QAF + FATHA, ALIF]
    alignments = [align("equal", 0, 0), align("equal", 1, 1)]
    err_pat = ReciterErrPatern(
        rf"R:<e,t0:{QAF}{ALIF}>",
        {"t0": TajweedRuleType.NORMAL_MADD},
    )

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[
            [],
            [meta(TajweedRuleType.NORMAL_MADD, pivot=(2, 4))],
        ],
        ref_ph_to_uthmani=[0, 0, 1, 1, 2],
    )
    assert len(errors) == 1
    err = errors[0]
    assert err.expected_ph == QAF + FATHA + ALIF + ALIF
    assert err.preditected_ph == QAF + FATHA + ALIF
    assert err.ph_pos == (0, 4)
    assert err.uthmani_pos == (0, 2)
    assert err.expected_len == 2
    assert err.predicted_len == 3
    assert err.ref_tajweed_rules[0].golden_len == 2
    assert err.ref_tajweed_rules[0].uth_pivot == (1, 2)


def test_find_all_skips_plain_equal_match_without_rules():
    err_pat = ReciterErrPatern(r"R:<e:A>", {})

    errors = err_pat.find_all(
        ref_ph_groups=["A"],
        pred_ph_groups=["A"],
        ph_groups_align=[align("equal", 0, 0)],
        ref_group_rules=[[]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert errors == []


def test_find_all_is_non_overlapping():
    ref_ph_groups = ["A", "B", "A", "B"]
    pred_ph_groups = ["A", "B", "A", "B"]
    alignments = [
        align("equal", 0, 0),
        align("insert", 1, 1),
        align("equal", 2, 2),
        align("insert", 3, 3),
    ]
    err_pat = ReciterErrPatern(r"R:<e:A><i:B>", {})

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[], [], [], []],
        ref_ph_to_uthmani=[0, 1, 2, 3, 4],
    )
    assert len(errors) == 2
    assert errors[0].expected_ph == "A"
    assert errors[0].preditected_ph == "AB"
    assert errors[1].expected_ph == "A"
    assert errors[1].preditected_ph == "AB"


def test_find_all_rejects_tag_that_swallows_another_op_letter():
    ref_ph_groups = ["A", "B"]
    pred_ph_groups = ["A", "B", "C"]
    alignments = [
        align("equal", 0, 0),
        align("equal", 1, 1),
        align("insert", 2, 2),
    ]
    err_pat = ReciterErrPatern(r"R:<e:.*C>", {})
    assert err_pat.re_pat.fullmatch("eABiC") is not None

    errors = err_pat.find_all(
        ref_ph_groups,
        pred_ph_groups,
        alignments,
        ref_group_rules=[[], []],
        ref_ph_to_uthmani=[0, 1, 2],
    )
    assert errors == []


def test_find_all_explicit_error_and_speech_types_override_detection():
    err_pat = ReciterErrPatern(
        r"R:<e,t0:A>",
        {"t0": TajweedRuleType.NORMAL_MADD},
        error_type="tashkeel",
        speech_error_type="delete",
        missing_tajweed_rules=[TajweedRuleType.NORMAL_MADD],
    )

    errors = err_pat.find_all(
        ref_ph_groups=["A"],
        pred_ph_groups=["A"],
        ph_groups_align=[align("equal", 0, 0)],
        ref_group_rules=[[meta(TajweedRuleType.NORMAL_MADD)]],
        ref_ph_to_uthmani=[0, 1],
    )
    assert len(errors) == 1
    assert errors[0].error_type == "tashkeel"
    assert errors[0].speech_error_type == "delete"
    assert [rule.rule_type for rule in errors[0].missing_tajweed_rules] == [
        TajweedRuleType.NORMAL_MADD
    ]
