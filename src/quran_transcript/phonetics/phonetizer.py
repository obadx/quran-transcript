import re
from dataclasses import dataclass

from .conv_base_operation import MappingPos
from .operations import OPERATION_ORDER
from .moshaf_attributes import MoshafAttributes
from .sifa import process_sifat, SifaOutput
from .. import alphabet as alph


@dataclass
class QuranPhoneticScriptOutput:
    phonemes: str
    sifat: list[SifaOutput]
    mappings: list[MappingPos | None]  # `None` for deletion


def quran_phonetizer(
    uhtmani_text: str, moshaf: MoshafAttributes, remove_spaces=False
) -> QuranPhoneticScriptOutput:
    """الرسم الصوتي للقآن الكريم على طبقتين: طبقة الأحرف وطبقة الصفات"""
    text = uhtmani_text

    # cleaning extra scpace
    # TODO: create mapping for this
    text = re.sub(r"\s+", rf"{alph.uthmani.space}", text)
    text = re.sub(r"(\s$|^\s)", r"", text)

    mappings = None
    for op in OPERATION_ORDER:
        text, mappings = op.apply(text, moshaf, mappings)

    sifat = process_sifat(
        uthmani_script=uhtmani_text,
        phonetic_script=text,
        moshaf=moshaf,
    )

    # TODO: create mapping for this
    if remove_spaces:
        text = re.sub(alph.uthmani.space, r"", text)

    return QuranPhoneticScriptOutput(phonemes=text, sifat=sifat, mappings=mappings)
