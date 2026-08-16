import json
import re
from dataclasses import asdict
from pathlib import Path

from quran_transcript import Aya
from quran_transcript import alphabet as alph
from quran_transcript.alphabet import BeginHamzatWasl, SpecialPattern, UthmaniAlphabet


def get_uthmani_alpabet() -> list[str]:
    aya = Aya(1, 1)
    alphabet = set()
    for aya in aya.get_ayat_after(114):
        alphabet |= set(aya.get().uthmani)
    return sorted(alphabet)


if __name__ == "__main__":
    alphabet_path = "./quran-script/quran-alphabet.json"
    uth_alph = get_uthmani_alpabet()

    hrof_moqtta_disassemble = {
        "الٓمٓ ٱللَّهُ": "أَلِفْ لَا~م مِّي~مَ ٱللَّهُ",
        "الٓمٓ": "أَلِفْ لَا~م مِّي~مْ",
        "الٓمٓصٓ": "أَلِفْ لَا~م مِّي~مْ صَا~دْ",
        "الٓر": "أَلِفْ لَا~مْ رَا",
        "الٓمٓر": "أَلِفْ لَا~م مِّي~مْ رَا",
        "كٓهيعٓصٓ": "كَا~فْ هَا يَا عَي~ن صَا~دْ",
        "طه": "طَا هَا",
        "طسٓمٓ": "طَا سِي~ن مِّي~مْ",
        "طسٓ": "طَا سِي~ن",
        "حمٓ": "حَا مِي~مْ",
        "عٓسٓقٓ": "عَي~ن سِي~ن قَا~فْ",
        "يسٓ": "يَا سِي~نْ",
        "صٓ": "صَا~دْ",
        "قٓ": "قَا~فْ",
        "نٓ": "نُو~نْ",
    }
    special_patterns = [
        # SpecialPattern(
        #     pattern=f"{alph.uthmani.lam}({alph.uthmani.kasra})?{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha}{alph.uthmani.haa}",
        #     target_pattern=f"{alph.uthmani.lam}\\1{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.haa}",
        # ),
        SpecialPattern(pattern="لْـَٔيْكَةِ", target_pattern="ٱلْأَيْكَةِ", pos="start"),
        SpecialPattern(
            pattern="عِوَجَا قَيِّمًۭا",
            attr_name="sakt_iwaja",
            opts={
                "sakt": "عِوَجَا" + alph.phonetics.sakt + alph.uthmani.space + "قَيِّمًۭا",
                "idraj": f"عِوَج{alph.uthmani.tanween_fath_modgham}ا"
                + alph.uthmani.space
                + "قَيِّمًۭا",
            },
        ),
        SpecialPattern(
            pattern="مَّرْقَدِنَا هَـٰذَا",
            attr_name="sakt_marqdena",
            opts={
                "sakt": "مَّرْقَدِنَا" + alph.phonetics.sakt + alph.uthmani.space + "هَـٰذَا",
                "idraj": "مَّرْقَدِنَا هَـٰذَا",
            },
        ),
        SpecialPattern(
            pattern="مَنْ رَاقٍۢ",
            attr_name="sakt_man_raq",
            opts={
                "sakt": "مَنْ" + alph.phonetics.sakt + alph.uthmani.space + "رَاقٍۢ",
                "idraj": "مَن" + alph.uthmani.space + "رَّاقٍۢ",
            },
        ),
        SpecialPattern(
            pattern="بَلْ رَانَ",
            attr_name="sakt_bal_ran",
            opts={
                "sakt": "بَلْ" + alph.phonetics.sakt + alph.uthmani.space + "رَانَ",
                "idraj": "بَل" + alph.uthmani.space + "رَّانَ",
            },
        ),
        SpecialPattern(
            pattern="مَالِيَهْ هَلَكَ",
            attr_name="sakt_maleeyah",
            opts={
                "sakt": "مَالِيَهْ" + alph.phonetics.sakt + alph.uthmani.space + "هَلَكَ",
                "idgham": "مَالِيَه" + alph.uthmani.space + "هَّلَكَ",
            },
        ),
        SpecialPattern(
            pattern="عَلِيمٌۢ بَرَآءَةٌۭ",
            attr_name="between_anfal_and_tawba",
            opts={
                "sakt": "عَلِيم" + alph.phonetics.sakt + alph.uthmani.space + "بَرَآءَةٌۭ",
                "wasl": "عَلِيمٌۢ بَرَآءَةٌۭ",
            },
        ),
        SpecialPattern(
            pattern="يَا سِيٓنْ وَٱلْقُرْءَانِ",
            attr_name="noon_and_yaseen",
            opts={
                "idgham": "يَا سِيٓن وَٱلْقُرْءَانِ",
                "izhar": "يَا سِيٓنْ وَٱلْقُرْءَانِ",
            },
        ),
        SpecialPattern(
            pattern="نُوٓنْ وَٱلْقَلَمِ",
            attr_name="noon_and_yaseen",
            opts={
                "idgham": "نُوٓن وَٱلْقَلَمِ",
                "izhar": "نُوٓنْ وَٱلْقَلَمِ",
            },
        ),
        SpecialPattern(
            pattern="ءَاتَىٰنِۦَ",
            attr_name="yaa_ataan",
            pos="end",
            opts={
                "hadhf": "ءَاتَىٰنِ",
                "ithbat": "ءَاتَىٰنِي",
            },
        ),
        SpecialPattern(
            pattern="ٱلِٱسْمُ",
            attr_name="start_with_ism",
            pos="start",
            opts={
                "lism": "لِسْمُ",
                "alism": "أَلِسْمُ",
            },
        ),
        SpecialPattern(
            pattern="وَيَبْصُۜطُ",
            attr_name="yabsut",
            opts={
                "seen": "وَيَبْسُطُ",
                "saad": "وَيَبْصُطُ",
            },
        ),
        SpecialPattern(
            pattern="بَصْۜطَةًۭ",
            attr_name="bastah",
            opts={
                "seen": "بَسْطَةًۭ",
                "saad": "بَصْطَةًۭ",
            },
        ),
        SpecialPattern(
            pattern="ٱلْمُصَۣيْطِرُونَ",
            attr_name="almusaytirun",
            opts={
                "seen": "ٱلْمُسَيْطِرُونَ",
                "saad": "ٱلْمُصَيْطِرُونَ",
            },
        ),
        SpecialPattern(
            pattern="بِمُصَيْطِرٍ",
            attr_name="bimusaytir",
            opts={
                "seen": "بِمُسَيْطِرٍ",
                "saad": "بِمُصَيْطِرٍ",
            },
        ),
        SpecialPattern(
            pattern=f"{alph.uthmani.hamza}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.madd}{alph.uthmani.lam}",
            attr_name="tasheel_or_madd",
            opts={
                "madd": f"{alph.uthmani.hamza}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.madd}{alph.uthmani.lam}",
                "tasheel": f"{alph.uthmani.hamza}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.tasheel_sign}{alph.uthmani.lam}",
            },
        ),
        SpecialPattern(
            pattern="يَلْهَث ذَّٰلِكَ",
            attr_name="yalhath_dhalik",
            opts={
                "izhar": "يَلْهَثْ ذَٰلِكَ",
                "idgham": "يَلْهَث ذَّٰلِكَ",
            },
        ),
        SpecialPattern(
            pattern="ٱرْكَب مَّعَنَا",
            attr_name="irkab_maana",
            opts={
                "izhar": "ٱرْكَبْ مَعَنَا",
                "idgham": "ٱرْكَب مَّعَنَا",
            },
        ),
        SpecialPattern(
            pattern="تَأْمَ۫نَّا",
            attr_name="noon_tamnna",
            opts={
                "ishmam": "تَأْمَنَّا",
                "rawm": re.sub(
                    alph.uthmani.dama, alph.phonetics.dama_mokhtalasa, "تَأْمَنُنَا"
                ),
            },
        ),
        SpecialPattern(
            pattern=f"(?<!\\b{alph.uthmani.ras_haaa}{alph.uthmani.space})"
            + "ضَعْف"
            + r"\b",
            attr_name="harakat_daaf",
            opts={
                "fath": "ضَعْف",
                "dam": "ضُعْف",
            },
        ),
        SpecialPattern(
            pattern="سَلَـٰسِلَا۟",
            attr_name="alif_salasila",
            pos="end",
            opts={
                "hadhf": "سَلَـٰسِلَ",
                "ithbat": "سَلَـٰسِلَا",
            },
        ),
        SpecialPattern(
            pattern="نَخْلُقكُّم",
            attr_name="idgham_nakhluqkum",
            opts={
                "idgham_kamil": "نَخْلُقكُّم",
                "idgham_naqis": "نَخْلُقكُم",
            },
        ),
        # special case where khinjaria alif is for rasm not phonetic
        SpecialPattern(
            pattern="فَٱدَّٰرَْٰٔتُمْ",
            target_pattern="فَٱدَّٰرَْٔتُمْ",
        ),
    ]
    madd = Aya(68, 1).get().uthmani[1]
    for k in hrof_moqtta_disassemble:
        hrof_moqtta_disassemble[k] = re.sub("~", madd, hrof_moqtta_disassemble[k])

    with open("./quran-script/begin_with_hamzat_wasl.json", "r", encoding="utf8") as f:
        begin_hamzat_wasl = BeginHamzatWasl(**json.load(f))

    uthmani_alphabet = UthmaniAlphabet(
        space=uth_alph[0],
        hamza=uth_alph[1],
        hamza_above_alif=uth_alph[2],
        hamza_above_waw=uth_alph[3],
        hamza_below_alif=uth_alph[4],
        hamza_above_yaa=uth_alph[5],
        alif=uth_alph[6],
        baa=uth_alph[7],
        taa_marboota=uth_alph[8],
        taa_mabsoota=uth_alph[9],
        thaa=uth_alph[10],
        jeem=uth_alph[11],
        haa_mohmala=uth_alph[12],
        khaa=uth_alph[13],
        daal=uth_alph[14],
        thaal=uth_alph[15],
        raa=uth_alph[16],
        zay=uth_alph[17],
        seen=uth_alph[18],
        sheen=uth_alph[19],
        saad=uth_alph[20],
        daad=uth_alph[21],
        taa_mofakhama=uth_alph[22],
        zaa_mofakhama=uth_alph[23],
        ayn=uth_alph[24],
        ghyn=uth_alph[25],
        kasheeda=uth_alph[26],
        faa=uth_alph[27],
        qaf=uth_alph[28],
        kaf=uth_alph[29],
        lam=uth_alph[30],
        meem=uth_alph[31],
        noon=uth_alph[32],
        haa=uth_alph[33],
        waw=uth_alph[34],
        alif_maksora=uth_alph[35],
        yaa=uth_alph[36],
        tanween_fath=uth_alph[37],
        tanween_dam=uth_alph[38],
        tanween_kasr=uth_alph[39],
        fatha=uth_alph[40],
        dama=uth_alph[41],
        kasra=uth_alph[42],
        shadda=uth_alph[43],
        ras_haaa=uth_alph[44],
        madd=uth_alph[45],
        hamza_mamdoda=uth_alph[46],
        alif_khnjaria=uth_alph[47],
        hamzat_wasl=uth_alph[48],
        small_seen_above=uth_alph[49],
        skoon_mostadeer=uth_alph[50],
        skoon_mostateel=uth_alph[51],
        meem_iqlab=uth_alph[52],
        small_seen_below=uth_alph[53],
        small_waw=uth_alph[54],
        small_yaa_sila=uth_alph[55],
        small_yaa=uth_alph[56],
        small_noon=uth_alph[57],
        imala_sign=uth_alph[58],
        ishmam_sign=uth_alph[59],
        tasheel_sign=uth_alph[60],
        tanween_idhaam_dterminer=uth_alph[61],
        hrof_moqtaa_disassemble=hrof_moqtta_disassemble,
        special_patterns=special_patterns,
        begin_hamzat_wasl=begin_hamzat_wasl,
    )

    # assert set(uth_alph) == set(asdict(uthmani_alphabet).values()), (
    #     f"{set(uth_alph) - set(asdict(uthmani_alphabet).values())}"
    # )

    with open(alphabet_path, "r", encoding="utf-8") as f:
        alphabet = json.load(f)
    alphabet["uthmani"] = asdict(uthmani_alphabet)
    del alphabet["uthmani"]["begin_hamzat_wasl"]
    with open(alphabet_path, "w+", encoding="utf-8") as f:
        json.dump(alphabet, f, indent=2, ensure_ascii=False)
