from quran_transcript.phonetics.phonetizer import quran_phonetizer
from quran_transcript import Aya, MoshafAttributes


if __name__ == "__main__":
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    aya = Aya()
    uth_text = aya.get().uthmani
    ph_out = quran_phonetizer(uth_text, moshaf)
    ph_text = ph_out.phonemes
    print(uth_text[24:27])
    for idx, uth_c in enumerate(uth_text):
        print(f"UTH_IDX: `{idx}`, SPAN: `{ph_out.mappings[idx]}`")
        ph_c = ""
        mapping = ph_out.mappings[idx]
        if mapping is not None:
            ph_c = ph_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")

        print("-" * 40)

    """
    * Lam Ism Allah should be deleted at [8] [Not the best thing but works]
    * No addision for Alif of Ism Allah pos(9, 11) [DONE]
    * Normal Madd [25] pos(20, 21) [DONE]
    """
