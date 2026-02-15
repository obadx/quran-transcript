from quran_transcript.phonetics.phonetizer import quran_phonetizer
from quran_transcript import Aya, MoshafAttributes
from pyinstrument import Profiler


if __name__ == "__main__":
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    aya = Aya()
    aya = Aya(1, 1)
    # aya = Aya(12, 1)
    aya = Aya(2, 1)
    aya = Aya(19, 1)
    # aya = Aya(75, 27)
    aya = Aya(2, 6)
    aya = Aya(2, 7)
    aya = Aya(27, 62)
    # aya = Aya(3, 1)
    # aya = Aya(30, 28)
    # aya = Aya(2, 9)
    uth_text = aya.get().uthmani

    # uth_text = aya.get_by_imlaey_words(start=7, window=2).uthmani
    # uth_text = "لَكُم مَّا"
    # uth_text = "غِشَـٰوَةٌۭ وَلَهُمْ"
    # uth_text = "قَلِيلًۭا مِّمَّا"
    # uth_text = "أَمَّن يُجِيبُ"

    profiler = Profiler()
    profiler.start()
    ph_out = quran_phonetizer(uth_text, moshaf, remove_spaces=True)
    profiler.stop()
    ph_text = ph_out.phonemes
    print(uth_text)
    print(ph_out.phonemes)
    print(ph_out.mappings)
    for idx, uth_c in enumerate(uth_text):
        print(f"UTH_IDX: `{idx}`, SPAN: `{ph_out.mappings[idx]}`")
        ph_c = ""
        mapping = ph_out.mappings[idx]
        if mapping is not None:
            ph_c = ph_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")

        print("-" * 40)

    print(profiler.output_text(unicode=True, color=True, show_all=True))
    """
    * meem moshaddah
    * Lam Ism Allah should be deleted at [8] [Not the best thing but works]
    * No addision for Alif of Ism Allah pos(9, 11) [DONE]
    * Normal Madd [25] pos(20, 21) [DONE]
    """
