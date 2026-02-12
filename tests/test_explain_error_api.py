from quran_transcript.phonetics.error_explainer import ReciterError, explain_error

from quran_transcript import quran_phonetizer, MoshafAttributes


if __name__ == "__main__":
    uthmani_text = "قَالُوٓا۟"

    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    ref_ph_out = quran_phonetizer(uthmani_text, moshaf)

    predicted_text = "كالۥۥ"
    predicted_text = "فكالۥۥ"
    predicted_text = "فكۥۥلۥۥ"

    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ref_ph_out.phonemes,
        predicted_ph_text=predicted_text,
        mappings=ref_ph_out.mappings,
    )
    for err in errors:
        print(err)
