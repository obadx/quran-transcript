from dataclasses import dataclass

from .conv_base_operation import PhonetizerMappings
from .moshaf_attributes import MoshafAttributes
from .operations import QuranPhonemesPhonetizer
from .sifa import SifaOutput, process_sifat


@dataclass
class QuranPhoneticScriptOutput:
    phonemes: str
    sifat: list[SifaOutput]
    mappings: PhonetizerMappings
    # TODO: Add mappings with sifat


_QURAN_PHONEMES_PHONETIZER = QuranPhonemesPhonetizer()


def quran_phonetizer(
    uthmani_text: str,
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
    text, mappings = _QURAN_PHONEMES_PHONETIZER.process(
        uthmani_text, moshaf, sura_idx=sura_idx
    )

    sifat = process_sifat(
        uthmani_script=uthmani_text,
        phonetic_script=text,
        moshaf=moshaf,
    )

    if remove_spaces:
        text, mappings = _QURAN_PHONEMES_PHONETIZER.remove_spaces(text, mappings)

    return QuranPhoneticScriptOutput(phonemes=text, sifat=sifat, mappings=mappings)
