import numpy as np
import re
import importlib.resources as pkg_resources
from pathlib import Path

from ..utils import Aya
from .phonetizer import quran_phonetizer
from .sifa import chunck_phonemes
from .moshaf_attributes import MoshafAttributes
from .conv_base_operation import MappingListType
from .. import alphabet as alph


def clean_uthmani_spaces(uth_text: str):
    """remove residual spaces from the uthmani text"""
    uth_text = re.sub(r"\s+", f"{alph.uthmani.space}", uth_text)
    uth_text = re.sub(r"(\s$|^\s)", r"", uth_text)
    return uth_text


def normalize_phonetic_groups(ph_groups: list[str]):
    """Normalizing phonetic group level by selecting first index of evey phoneme group"""
    out = ""
    for g in ph_groups:
        out += g[0]
    return out


def get_uth_word_boundaries_in_ph(uth_text: str, mappings: MappingListType) -> set[int]:
    """gets the uthmani word boundary indices in the phonetic script using mappings from uthmani to phonetic script"""
    boundries = set()
    for idx in range(len(uth_text)):
        if uth_text[idx] == alph.uthmani.space:
            assert mappings[idx].deleted, (
                f"`{uth_text}`, `{len(uth_text)}`, `IDX={idx}`, `{uth_text[idx]}`, `{uth_text[idx + 1 :]}`, `{mappings[idx]}`"
            )
            boundries.add(mappings[idx].pos[0])
    return boundries


def get_phonetic_to_char_uthmani(mappings: MappingListType) -> dict[int, int]:
    ph_to_uth = {}
    for uth_idx, m in enumerate(mappings):
        for ph_idx in range(m.pos[0], m.pos[1]):
            ph_to_uth[ph_idx] = uth_idx
    return ph_to_uth


def create_phonemes_index(output_dir: Path | None = None):
    """Creates Phonemes index as a 5d numpay array

    every element in the arrya is
    [sura_idx][aya_idx][uth_word_start_idx][char_idx_within the uth aya][ph_idx_start]

    The last row contains the next phoneitc index to be complete
    [sura_idx][aya_idx][uth_word_start_idx of last word][last char uth idx][ph_idx_start last index + 1]
    """
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    start_aya = Aya()
    ph_grp_to_index = []
    ref_ph = ""
    for aya in start_aya.get_ayat_after():
        uth_text = aya.get().uthmani
        uth_text = clean_uthmani_spaces(uth_text)
        ph_out = quran_phonetizer(uth_text, moshaf, remove_spaces=True)
        ph_text = ph_out.phonemes
        ph_groups = chunck_phonemes(ph_text)
        ph_norm = normalize_phonetic_groups(ph_groups)
        ref_ph += ph_norm
        uth_word_bound = get_uth_word_boundaries_in_ph(uth_text, ph_out.mappings)
        ph_to_uth_idx = get_phonetic_to_char_uthmani(ph_out.mappings)

        ph_start_idx = 0
        uth_word_idx = 0
        for ph_g in ph_groups:
            ph_end_idx = ph_start_idx + len(ph_g)
            ph_grp_to_index.append(
                [
                    aya.get().sura_idx,
                    aya.get().aya_idx,
                    uth_word_idx,
                    ph_to_uth_idx[ph_start_idx],
                    ph_start_idx,
                ]
            )

            # Adjusting Values for the following steps
            if ph_end_idx in uth_word_bound:
                uth_word_idx += 1
            ph_start_idx = ph_end_idx

    # TODO: Add last row

    # Convert to numpy array of uint16
    index_array = np.array(ph_grp_to_index, dtype=np.uint16)

    # Determine output directory
    if output_dir is None:
        # Default to package's quran-script folder
        output_dir = Path(pkg_resources.files("quran_transcript")) / "quran-script"
    else:
        output_dir = Path(output_dir)

    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save index as .npy
    index_path = output_dir / "ph_index.npy"
    np.save(index_path, index_array)
    print(f"Phoneme index saved to {index_path}")

    # Save reference phonemes as text
    ref_ph_path = output_dir / "ref_norm_ph.txt"
    with open(ref_ph_path, "w", encoding="utf-8") as f:
        f.write(ref_ph)
    print(f"Reference phonemes saved to {ref_ph_path}")
