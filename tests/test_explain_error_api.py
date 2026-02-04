from quran_transcript.phonetics.tajweed_rulses import NormalMaddRule
from quran_transcript.phonetics.error_explainer import ReciterError, explain_error
from quran_transcript.phonetics.conv_base_operation import MappingPos


if __name__ == "__main__":
    normal_madd_alif = NormalMaddRule(tag="alif")
    normal_madd_waw = NormalMaddRule(tag="waw")
    uthmani_text = "قالوا"
    ref_mapping = [
        MappingPos(pos=(0, 1)),
        MappingPos(pos=(1, 3), tajweed_rules=[normal_madd_alif]),
        MappingPos(pos=(3, 4)),
        MappingPos(pos=(4, 6), tajweed_rules=[normal_madd_waw]),
        None,
    ]
    ref_ph_text = "قاالۥۥ"

    predicted_text = "كالۥۥ"
    predicted_text = "فكالۥۥ"
    predicted_text = "فكۥۥلۥۥ"

    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ref_ph_text,
        predicted_ph_text=predicted_text,
        mappings=ref_mapping,
    )
    for err in errors:
        print(err)
