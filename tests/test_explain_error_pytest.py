import pytest

from quran_transcript import MoshafAttributes, quran_phonetizer, explain_error


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
