from quran_transcript.phonetics.sifa import chunck_phonemes, process_sifat
from quran_transcript import quran_phonetizer, MoshafAttributes, Aya

from pydantic import BaseModel
from typing import Any


def format_pydantic(instance: BaseModel) -> str:
    def format_value(v: Any) -> str:
        if isinstance(v, BaseModel):
            return format_pydantic(v)
        elif isinstance(v, list):
            return "[" + ", ".join(format_value(item) for item in v) + "]"
        elif isinstance(v, dict):
            return (
                "{"
                + ", ".join(f"{k}: {format_value(val)}" for k, val in v.items())
                + "}"
            )
        else:
            return str(v)

    class_name = instance.__class__.__name__
    fields = []

    # Get field names in declaration order (works for both Pydantic v1 and v2)
    if hasattr(instance, "__fields__"):  # Pydantic v1
        field_names = list(instance.__fields__.keys())
    else:  # Pydantic v2
        field_names = list(instance.model_fields.keys())

    for field_name in field_names:
        value = getattr(instance, field_name)
        formatted_value = format_value(value)
        fields.append(f"{field_name}='{formatted_value}'")

    return f"{class_name}({', '.join(fields)})"


if __name__ == "__main__":
    aya = Aya(75, 27)
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
        tasheel_or_madd="madd",
    )

    uthmani_script = aya.get().uthmani
    phonetic_script = quran_phonetizer(uthmani_script, moshaf).phonemes
    chunks = chunck_phonemes(phonetic_script)
    sifa_outs = process_sifat(uthmani_script, phonetic_script, moshaf)

    for o in sifa_outs:
        print(f"{format_pydantic(o)},")
