import pytest

from quran_transcript import (
    MoshafAttributes,
    chunck_phonemes,
    explain_error,
    quran_phonetizer,
)
from quran_transcript.phonetics.error_explainer import (
    get_ref_phonetic_groups_tajweed_rules,
)
from quran_transcript.phonetics.tajweed_rulses import TajweedRuleType


@pytest.fixture(scope="module")
def moshaf():
    return MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )


@pytest.mark.parametrize(
    "uthmani_text,predicted_text",
    [
        # test 1
        ("أَنْعَمْتَ", "ءَنعَمتُ"),
        # test 2
        ("ٱلْجِنَّةِ", "ءَلجِننننه"),
        # test 3
        ("لَكَ", "لَكَا"),
        # test 4
        ("لَفِى", "لَفِ"),
    ],
)
def test_explain_error_cases(uthmani_text, predicted_text, moshaf):
    ref_ph_out = quran_phonetizer(uthmani_text, moshaf)
    print(uthmani_text)
    print(predicted_text)
    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ref_ph_out.phonemes,
        predicted_ph_text=predicted_text,
        mappings=ref_ph_out.mappings,
    )

    assert errors, "Expected at least one ReciterError for the notebook cases."

    # Basic sanity checks on error positions
    for err in errors:
        assert 0 <= err.uthmani_pos[0] <= err.uthmani_pos[1] <= len(uthmani_text)
        assert 0 <= err.ph_pos[0] <= err.ph_pos[1] <= len(ref_ph_out.phonemes)


def test_normal_madd_rule_is_attached_to_the_last_phoneme_group(moshaf):
    uthmani_text = "قَالُوٓا۟"
    predicted_text = "قَاالُۥ"

    ref_ph_out = quran_phonetizer(uthmani_text, moshaf)
    ref_ph_groups = chunck_phonemes(ref_ph_out.phonemes)

    rules = get_ref_phonetic_groups_tajweed_rules(
        ref_ph_out.phonemes,
        ref_ph_groups=ref_ph_groups,
        mappings=ref_ph_out.mappings,
    )

    assert len(rules) == len(ref_ph_groups)
    assert ref_ph_groups == ["قَ", "اا", "لُ", "ۥۥ"]
    assert rules[1][0][0].rule_type == TajweedRuleType.NORMAL_MADD
    assert rules[1][0][1].pivot == (2, 4)
    assert rules[3][0][0].rule_type == TajweedRuleType.NORMAL_MADD
    assert rules[3][0][1].pivot == (6, 8)
    assert rules[3][0][1].uth_pivot == (5, 6)

    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ref_ph_out.phonemes,
        predicted_ph_text=predicted_text,
        mappings=ref_ph_out.mappings,
    )

    assert len(errors) == 1
    err = errors[0]
    assert err.error_type == "tajweed"
    assert err.speech_error_type == "replace"
    assert err.expected_ph == "ۥۥ"
    assert err.preditected_ph == "ۥ"
    assert err.expected_len == 2
    assert err.predicted_len == 1
    assert err.uthmani_pos == (5, 6)
    assert err.ph_pos == (6, 8)
    assert err.ref_tajweed_rules[0].rule_type == TajweedRuleType.NORMAL_MADD
    assert err.ref_tajweed_rules[0].ph_pivot == (6, 8)
    assert err.ref_tajweed_rules[0].uth_pivot == (5, 6)
