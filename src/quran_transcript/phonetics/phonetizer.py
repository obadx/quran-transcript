import re
from dataclasses import dataclass

from .conv_base_operation import MappingPos, sub_with_mapping, MappingListType
from .operations import OPERATION_ORDER
from .moshaf_attributes import MoshafAttributes
from .sifa import process_sifat, SifaOutput
from .. import alphabet as alph


@dataclass
class QuranPhoneticScriptOutput:
    phonemes: str
    sifat: list[SifaOutput]
    mappings: MappingListType  # `None` for deletion
    # TODO: Add mappings with sifat


def quran_phonetizer(
    uhtmani_text: str, moshaf: MoshafAttributes, remove_spaces=False
) -> QuranPhoneticScriptOutput:
    """الرسم الصوتي للقآن الكريم على طبقتين: طبقة الأحرف وطبقة الصفات"""
    text = uhtmani_text

    # cleaning extra scpace
    text, mappings = sub_with_mapping(r"\s+", rf"{alph.uthmani.space}", text)
    text, mappings = sub_with_mapping(r"(\s$|^\s)", r"", text, mappings=mappings)

    for op in OPERATION_ORDER:
        text, mappings = op.apply(text, moshaf, mappings)

    sifat = process_sifat(
        uthmani_script=uhtmani_text,
        phonetic_script=text,
        moshaf=moshaf,
    )

    if remove_spaces:
        text, mappings = sub_with_mapping(
            alph.uthmani.space, r"", text, mappings=mappings
        )

    return QuranPhoneticScriptOutput(phonemes=text, sifat=sifat, mappings=mappings)
