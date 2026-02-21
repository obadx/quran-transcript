from quran_transcript import (
    quran_phonetizer,
    MoshafAttributes,
    ReciterError,
    explain_error,
)


if __name__ == "__main__":
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    uthmani_text = "قَالُوٓا۟"
    predicted_text = "كالۥۥ"
    predicted_text = "فكالۥۥ"
    predicted_text = "فكۥۥلۥۥ"

    # uthmani_text = "ٱلْحَقُّ"
    # predicted_text = "ءَلحَقق"
    # predicted_text = "ءَلحقق"
    # predicted_text = "ءَلحُقق"

    # uthmani_text = "الٓمٓ"
    # predicted_text = "ءَلِف لَااااااممممِۦۦۦۦۦۦم"
    # predicted_text = "ءَلِف لَاااااممممِۦۦۦۦۦۦم"

    uthmani_text = "لَكَ"
    predicted_text = "لَكَا"

    ref_ph_out = quran_phonetizer(uthmani_text, moshaf)
    print(ref_ph_out.phonemes)
    print(predicted_text)
    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ref_ph_out.phonemes,
        predicted_ph_text=predicted_text,
        mappings=ref_ph_out.mappings,
    )
    for err in errors:
        print(
            f"UTH: `{uthmani_text[err.uthmani_pos[0] : err.uthmani_pos[1]]}`, {err.uthmani_pos}"
        )
        print(
            f"PH: `{ref_ph_out.phonemes[err.ph_pos[0] : err.ph_pos[1]]}`, {err.ph_pos}"
        )
        print(err)
        print("-" * 50)
