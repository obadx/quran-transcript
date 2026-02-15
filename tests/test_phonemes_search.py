from pyinstrument import Profiler

from quran_transcript import MoshafAttributes, quran_phonetizer, Aya
from quran_transcript.phonetics.search import PhoneticSearch


if __name__ == "__main__":
    profiler = Profiler()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    uth_text = "قَلِيلًۭا مِّمَّا"
    uth_text = "قَلِيلًۭا مَّا"
    uth_text = "يُجِيبُ"
    uth_text = "ءَممممَن"  # very edge case
    ph_text = quran_phonetizer(uth_text, moshaf, remove_spaces=True).phonemes
    print(ph_text)

    ph_search = PhoneticSearch()
    profiler.start()
    # ph_search.search("ءَلحَمدُلِللَااهِللَذِۦۦۦۦءَںںںزَلَعَلَااعَبڇدِهِلكِتَاابَوَلَميَجڇعَللَهُۥۥعِوَجَاا")
    # ph_search.search("ءَلحَمدُلِللَااهِللَذِۦۦۦۦءَںںںزَلَلَاعَبڇدِهِلكِتَااوَلَميَجڇعَللَهُۥۥعِوَجَاا")
    # results = ph_search.search(
    #     "ءَلحَمدُلِللَااهِلذِۦۦۦۦءَںںںزَلَاعَبڇدِهِلكِتَاالَميَجڇعَللَهُۥۥعِوَجَاا", error_ratio=0.2
    # )
    results = ph_search.search(ph_text, error_ratio=0.4)
    profiler.stop()
    # print(results)
    print("-" * 40)

    for r in results:
        if r.start.sura_idx == 27 and r.start.aya_idx == 62:
            print(r)
            print(ph_search.get_uthmani_from_result(r))

            print("*" * 50)
    print(profiler.output_text(unicode=True, color=True, show_all=True))
