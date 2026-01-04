import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .operations import OPERATION_ORDER
from .moshaf_attributes import MoshafAttributes
from .sifa import process_sifat, SifaOutput
from .. import alphabet as alph


def _distribute_mapping(segment: list[int | None], new_len: int) -> list[int | None]:
    """Spread original indices over a new segment length."""
    if new_len <= 0:
        return []
    if not segment:
        return [None] * new_len
    if len(segment) == 1:
        return [segment[0]] * new_len

    distributed: list[int | None] = []
    seg_len = len(segment)
    for k in range(new_len):
        idx = int(k * seg_len / new_len)
        if idx >= seg_len:
            idx = seg_len - 1
        distributed.append(segment[idx])
    return distributed


def _align_mapping(
    before_text: str, after_text: str, before_mapping: list[int | None]
) -> list[int | None]:
    """Align mapping list after a text transformation using sequence matching."""

    matcher = SequenceMatcher(a=before_text, b=after_text)
    new_mapping: list[int | None] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            new_mapping.extend(before_mapping[i1:i2])
        elif tag == "replace":
            segment = before_mapping[i1:i2]
            new_mapping.extend(_distribute_mapping(segment, j2 - j1))
        elif tag == "insert":
            new_mapping.extend([None] * (j2 - j1))
        elif tag == "delete":
            continue

    return new_mapping


def _substitute_with_mapping(
    text: str, mapping: list[int | None], pattern: str, replacement: str
) -> tuple[str, list[int | None]]:
    """Apply regex substitution while updating the origin mapping via alignment."""

    new_text = re.sub(pattern, replacement, text)
    if new_text == text:
        return text, mapping

    new_mapping = _align_mapping(text, new_text, mapping)
    return new_text, new_mapping


@dataclass
class QuranPhoneticScriptOutput:
    phonemes: str
    sifat: list[SifaOutput]
    char_map: list[int | None] = field(default_factory=list)


def quran_phonetizer(
    uhtmani_text: str, moshaf: MoshafAttributes, remove_spaces=False
) -> QuranPhoneticScriptOutput:
    """الرسم الصوتي للقآن الكريم على طبقتين: طبقة الأحرف وطبقة الصفات"""
    text = uhtmani_text
    mapping: list[int | None] = list(range(len(text)))

    # cleaning extra scpace
    text, mapping = _substitute_with_mapping(
        text, mapping, r"\s+", rf"{alph.uthmani.space}"
    )
    text, mapping = _substitute_with_mapping(text, mapping, r"(\s$|^\s)", r"")

    for op in OPERATION_ORDER:
        prev_text = text
        text = op.apply(text, moshaf)
        if text != prev_text:
            # print(f"Applied: {op.arabic_name}")
            # print(f"  Before: {prev_text}")
            # print(f"  After : {text}")
            mapping = _align_mapping(prev_text, text, mapping)

    sifat = process_sifat(
        uthmani_script=uhtmani_text,
        phonetic_script=text,
        moshaf=moshaf,
    )

    if remove_spaces:
        filtered_chars: list[str] = []
        filtered_map: list[int | None] = []
        for ch, idx in zip(text, mapping):
            if ch != alph.uthmani.space:
                filtered_chars.append(ch)
                filtered_map.append(idx)
        text = "".join(filtered_chars)
        mapping = filtered_map

    return QuranPhoneticScriptOutput(phonemes=text, sifat=sifat, char_map=mapping)
