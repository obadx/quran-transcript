from dataclasses import dataclass

from .. import alphabet as alph
from .conv_base_operation import MappingListType, MappingPos, sub_with_mapping
from .moshaf_attributes import MoshafAttributes
from .operations import OPERATION_ORDER
from .sifa import SifaOutput, process_sifat


@dataclass
class QuranPhoneticScriptOutput:
    phonemes: str
    sifat: list[SifaOutput]
    mappings: MappingListType  # `None` for deletion
    # TODO: Add mappings with sifat


def quran_phonetizer(
    uhtmani_text: str,
    moshaf: MoshafAttributes,
    remove_spaces=False,
    sura_idx: int = 0,
) -> QuranPhoneticScriptOutput:
    """الرسم الصوتي للقآن الكريم على طبقتين: طبقة الأحرف وطبقة الصفات
    Args:
        sura_idx (int): the sura index from 1 to 114. If zero then there is no sura set.
            Used when a specific rule is tied to a specific sura.
            This is used particularly if the user pronounced ONLY `ضَعْفًا` so we cannot infer whether this
            is from surah Alroom so we have two ways with damma or fatha; or from surah AlAnfal so we only
            pronounce it with fatha.

    """
    text = uhtmani_text

    # cleaning extra scpace
    text, mappings = sub_with_mapping(r"\s+", rf"{alph.uthmani.space}", text)
    text, mappings = sub_with_mapping(r"(\s$|^\s)", r"", text, mappings=mappings)

    for op in OPERATION_ORDER:
        text, mappings = op.apply(text, moshaf, mappings, sura_idx=sura_idx)

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
