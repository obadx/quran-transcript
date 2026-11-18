import pprint
from time import perf_counter_ns

from pyinstrument import Profiler

from quran_transcript import Aya, MoshafAttributes
from quran_transcript.phonetics.phonetizer import quran_phonetizer

if __name__ == "__main__":
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
        madd_alleen_len=2,
        madd_yaa_alayn_alharfy=6,
    )
    aya = Aya()
    aya = Aya(1, 1)
    # aya = Aya(12, 1)
    # aya = Aya(2, 1)
    # aya = Aya(36, 1)
    # aya = Aya(26, 1)
    # aya = Aya(2, 286)
    # aya = Aya(2, 282)
    # aya = Aya(19, 1)
    # aya = Aya(75, 27)
    # aya = Aya(28, 4)
    # aya = Aya(2, 6)
    # aya = Aya(2, 7)
    # aya = Aya(27, 62)
    # aya = Aya(112, 3)
    # aya = Aya(3, 1)
    # aya = Aya(30, 28)
    # aya = Aya(2, 9)
    # aya = Aya(106, 1)
    aya = Aya(111, 1)
    uth_text = aya.get().uthmani

    # uth_text = aya.get_by_imlaey_words(start=7, window=2).uthmani
    # uth_text = "لَكُم مَّا"
    # uth_text = "غِشَـٰوَةٌۭ وَلَهُمْ"
    # uth_text = "قَلِيلًۭا مِّمَّا"
    # uth_text = "أَمَّن يُجِيبُ"
    # uth_text = "قَرِيبٌ"
    # uth_text = "ٱلْحَقُّ"
    # uth_text = "حمٓ عٓسٓقٓ"
    # uth_text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ حمٓ عٓسٓقٓ"
    # uth_text = "ٱلسَّوْءِ"
    # uth_text = "قُرَيْشٍ"
    # uth_text = "لِّلْمُتَّقِينَ"

    # الإقلاب
    # uth_text = "مِنۢ بَعْدِ"
    # uth_text = "سَمِيعٌۢ بَصِيرٌۭ"

    # مد العوض
    # uth_text = "قَرِيبًا"
    # uth_text = "مَسْطُورًۭا"

    # uth_text = "أَنْعَمْتَ"
    # uth_text = "ٱللَّهُ"

    uth_text = "لَّٰكِنَّا۠ هُوَ"
    uth_text = "أَحَدٌ ٱللَّهُ"

    # uth_text = "ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ طسٓمٓ"

    # profiler = Profiler()
    # profiler.start()
    start = perf_counter_ns()
    for _ in range(1):
        ph_out = quran_phonetizer(uth_text, moshaf)
    end = perf_counter_ns()
    # profiler.stop()
    ph_text = ph_out.phonemes
    print(uth_text)
    print(ph_out.phonemes)
    print(ph_out.mappings)
    print("*" * 40)
    for idx, uth_c in enumerate(uth_text):
        print(f"UTH_IDX: `{idx}`, SPAN: `{ph_out.mappings[idx].pos}`")
        ph_c = ""
        mapping = ph_out.mappings[idx]
        ph_c = ph_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")
        ph_start, ph_end = ph_out.mappings[idx].pos
        pprint.pp(ph_out.mappings.ph_to_taj_rule_metas[ph_start:ph_end])

        print("-" * 40)

    # print(profiler.output_text(unicode=True, color=True, show_all=True))

    print(f"Total Time (ns): {end - start}")
    print(f"Total Time (s): {(end - start) / 1e9}")
    """
    * meem moshaddah
    * Lam Ism Allah should be deleted at [8] [Not the best thing but works]
    * No addision for Alif of Ism Allah pos(9, 11) [DONE]
    * Normal Madd [25] pos(20, 21) [DONE]
    """
