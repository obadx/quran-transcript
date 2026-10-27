import json
import re
from dataclasses import asdict
from hashlib import new
from pathlib import Path

from quran_transcript import Aya
from quran_transcript import alphabet as alph
from quran_transcript.alphabet import BeginHamzatWasl, SpecialPattern, UthmaniAlphabet
from quran_transcript.alphabet import phonetics as ph
from quran_transcript.alphabet import uthmani as uth
from quran_transcript.phonetics.conv_base_operation import (
    init_mappings,
    sub_with_tagged_mapping,
)


def get_uthmani_alpabet() -> list[str]:
    aya = Aya(1, 1)
    alphabet = set()
    for aya in aya.get_ayat_after(114):
        alphabet |= set(aya.get().uthmani)
    return sorted(alphabet)


def process_hrofp_moqtta_tagged_mapping(
    key_to_expand: dict[str, str],
) -> dict[str, str]:
    new_key_to_expand = {}
    for key, expand in key_to_expand.items():
        key_words = key.split(alph.uthmani.space)
        expand_words = expand.split(alph.uthmani.space)
        if len(key_words) == 2:
            word = key_words[0]
            residual = alph.uthmani.space + key_words[1]
            expand_words = expand_words[:-1]
        else:
            word = key
            residual = ""

        chars = re.findall(f".{alph.uthmani.madd}?", word)

        # Starting condition
        new_key = f"M:<s:(^|{alph.uthmani.space})>"
        new_expand = r"<s:\1>"
        for idx, (char, w_expand) in enumerate(zip(chars, expand_words)):
            new_expand += f"<p{idx}:{w_expand}"
            if len(char) == 1:
                new_key += f"<p{idx}:{char}>"
            elif len(char) == 2:
                new_key += f"<p{idx}:{char[0]}>{char[1]}"
            else:
                raise ValueError()

            if idx != (len(chars) - 1):
                # add space (for non last iteration)
                new_expand += alph.uthmani.space
            new_expand += ">"  # closing the exapnd

        if residual:
            new_key += f"<r:{residual}>"
            new_expand += f"<r:{residual}>"

        # end
        new_key += f"<e:({alph.uthmani.space}|$)>"
        new_expand += r"<e:\2>"

        new_key_to_expand[new_key] = new_expand
    return new_key_to_expand


if __name__ == "__main__":
    alphabet_path = "./quran-script/quran-alphabet.json"
    uth_alph = get_uthmani_alpabet()
    daaf = "ضَعْف"

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
    hrof_moqtta_disassemble = process_hrofp_moqtta_tagged_mapping(
        hrof_moqtta_disassemble
    )
    for key, val in hrof_moqtta_disassemble.items():
        print(key)
        print(val)
        sub_with_tagged_mapping(key, val, "", init_mappings(key))
        print("-" * 40)

    # الأيكمة
    lykah = "لْـَٔيْكَةِ"
    alykah = "ٱلْأَيْكَةِ"
    kasheeda_idx = lykah.find(uth.kasheeda)

    # عوجا قيما
    iwaja = "عِوَجَا"
    qymaa = "قَيِّمًۭا"

    # مرقدنا هذا
    marqdna = "مَّرْقَدِنَا"
    hatha = "هَـٰذَا"

    # من راق
    man = "مَنْ"
    raq = "رَاقٍۢ"

    # بل ران
    bal = "بَلْ"
    ran = "رَانَ"

    # ماليه هلك
    maliyah = "مَالِيَهْ"
    halaka = "هَلَكَ"

    # عليم براءة
    aliem = "عَلِيمٌۢ"
    braah = "بَرَآءَةٌۭ"

    # يس والقرآن
    yassen = "يَا سِيٓنْ"
    walqraan = "وَٱلْقُرْءَانِ"

    # ن والقلم
    noon = "نُوٓنْ"
    walqlam = "وَٱلْقَلَمِ"

    # آتاني
    atanee = "ءَاتَىٰنِۦَ"

    # السم
    sim = "سْمُ"

    # يبصط
    yabsoot = "وَيَبْصُۜطُ"
    yabsoot_saad = "وَيَبْصُطُ"
    yabsoot_seen = "وَيَبْسُطُ"
    special_patterns = [
        # SpecialPattern(
        #     pattern=f"{alph.uthmani.lam}({alph.uthmani.kasra})?{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha}{alph.uthmani.haa}",
        #     target_pattern=f"{alph.uthmani.lam}\\1{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.haa}",
        # ),
        # الأيكمة
        SpecialPattern(
            pattern=f"M:<r0:{uth.lam}><r1:({uth.ras_haaa})>{lykah[kasheeda_idx]}<r2:{lykah[kasheeda_idx + 1 :]}>",
            target_pattern=f"<r0:{uth.hamzat_wasl}{uth.lam}><r1:\\1><r2:{alykah[3:]}>",
            pos="start",
        ),
        # عوجا قيما
        SpecialPattern(
            pattern=f"M:<r0:({iwaja[:-2]})><r1:({iwaja[-2]})><r2:({iwaja[-1]})><r3:({uth.space}{qymaa})>",
            attr_name="sakt_iwaja",
            opts={
                "waqf": r"<r0:\\1><r1:\\2><r2:\\3><r3:\\4>",
                "sakt": f"<r0:\\1><r1:\\2><r2:\\3{ph.sakt}><r3:\\4>",
                "idraj": f"<r0:\\1><r1:{uth.tanween_fath_modgham}><r2:\\3><r3:\\4>",
            },
        ),
        # مرقدنا هذا
        SpecialPattern(
            pattern=f"M:<r0:({marqdna})><r1:({uth.space})><r2:({hatha})>",
            attr_name="sakt_marqdena",
            opts={
                "sakt": f"<r0:\\1{ph.sakt}><r1:\\2><r2:\\3>",
                "idraj": r"<r0:\1><r1:\2><r2:\3>",
                "waqf": r"<r0:\1><r1:\2><r2:\3>",
            },
        ),
        # من راق
        SpecialPattern(
            pattern=f"M:<r0:({man})><r1:({uth.space})><r2:({raq[0]})><r3:({raq[1]})><r4:({raq[2:]})>",
            attr_name="sakt_man_raq",
            opts={
                "sakt": f"<r0:\\1{ph.sakt}><r1:\\2><r2:\\3><r3:\\4><r4:\\5>",
                "idraj": f"<r0:{man[:-1]}><r1:\\2><r2:\\3><r3:{uth.shadda}\\4><r4:\\5>",
                "waqf": r"<r0:\1><r1:\2><r2:\3><r3:\4><r4:\5>",
            },
        ),
        # بل ران
        SpecialPattern(
            pattern=f"M:<r0:({bal})><r1:({uth.space})><r2:({ran[0]})><r3:({ran[1]})><r4:({ran[2:]})>",
            attr_name="sakt_bal_ran",
            opts={
                "sakt": f"<r0:\\1{ph.sakt}><r1:\\2><r2:\\3><r3:\\4><r4:\\5>",
                "idraj": f"<r0:{bal[:-1]}><r1:\\2><r2:\\3><r3:{uth.shadda}\\4><r4:\\5>",
                "waqf": r"<r0:\1><r1:\2><r2:\3><r3:\4><r4:\5>",
            },
        ),
        # ماليه هلك
        SpecialPattern(
            pattern=f"M:<r0:({maliyah})><r1:({uth.space})><r2:({halaka[0]})><r3:({halaka[1]})><r4:({halaka[2:]})>",
            attr_name="sakt_maleeyah",
            opts={
                "sakt": f"<r0:\\1{ph.sakt}><r1:\\2><r2:\\3><r3:\\4><r4:\\5>",
                "idgham": f"<r0:{maliyah[:-1]}><r1:\\2><r2:\\3><r3:{uth.shadda}\\4><r4:\\5>",
                "waqf": r"<r0:\1><r1:\2><r2:\3><r3:\4><r4:\5>",
            },
        ),
        # عليم براءة
        SpecialPattern(
            pattern=f"M:<r0:({aliem[:-3]})><r1:({aliem[-3]})><r2:({aliem[-2:]})><r3:({uth.space})><r4:({braah})>",
            attr_name="between_anfal_and_tawba",
            opts={
                "sakt": f"<r0:\\1><r1:\\2{ph.sakt}><r3:\\4><r4:\\5>",
                "wasl": r"<r0:\1><r1:\2><r2:\3><r3:\4><r4:\5>",
                "waqf": r"<r0:\1><r1:\2><r2:\3><r3:\4><r4:\5>",
            },
        ),
        # يس والقرآن
        SpecialPattern(
            pattern=f"M:<r0:({yassen})><s:({uth.space})><r1:({walqraan})>",
            attr_name="noon_and_yaseen",
            opts={
                "idgham": f"<r0:{yassen[:-1]}><s:\\2><r1:\\3>",
                "izhar": r"<r0:\1><s:\2><r1:\3>",
            },
        ),
        # ن والقلم
        SpecialPattern(
            pattern=f"M:<r0:({noon})><s:({uth.space})><r1:({walqlam})>",
            attr_name="noon_and_yaseen",
            opts={
                "idgham": f"<r0:{noon[:-1]}><s:\\2><r1:\\3>",
                "izhar": r"<r0:\1><s:\2><r1:\3>",
            },
        ),
        # آتاني
        SpecialPattern(
            pattern=f"M:<r:({atanee[:-2]})><y:({atanee[-2]})><f:({atanee[-1]})>",
            attr_name="yaa_ataan",
            pos="end",
            opts={
                "hadhf": r"<r:\1>",
                "ithbat": f"<r:\\1><y:{uth.yaa}>",
                "wasl": r"<r:\1><y:\2><f:\3>",
            },
        ),
        # الاسم
        SpecialPattern(
            pattern=f"M:<w0:{uth.hamzat_wasl}><l:({uth.lam}{uth.kasra})><w1:{uth.hamzat_wasl}><s:({sim})>",
            attr_name="start_with_ism",
            pos="start",
            opts={
                "lism": r"<l:\1><s:\2>",
                "alism": f"<w0:{uth.hamza_above_alif}{uth.fatha}><l:\\1><s:\\2>",
                "wasl": f"<w0:{uth.hamzat_wasl}><l:\\1><w1:{uth.hamzat_wasl}><s:\\2>",
            },
        ),
        # يبصط
        SpecialPattern(
            pattern=f"{yabsoot}",
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
        # وردت  ضَعْف في القرآن ف 4 مواضع: في الإنفل وثلاث في الروم فهنا نستثني موضع الأنفال
        # NOTE: if on starts with workضَعْفا we will inforce using suraah Alrom analogy
        # NOTE: Tanzil mixed up alph.uthmani.tanween_idhaam_dterminer with alph.uthmani.meem_iqlab so for surah Alroom
        # Tanweed with Idgham with written witn tanween_kasr + meem_iqlab
        SpecialPattern(
            pattern=f"(?:([^{alph.uthmani.ras_haaa}].){daaf})|(?:{daaf}({alph.uthmani.tanween_kasr}{alph.uthmani.meem_iqlab}))",
            attr_name="harakat_daaf",
            opts={
                "fath": r"\1" + "ضَعْف" + r"\2",
                "dam": r"\1" + "ضُعْف" + r"\2",
            },
        ),
        SpecialPattern(
            pattern="ضَعْف",
            attr_name="harakat_daaf",
            opts={
                "fath": "ضَعْف",
                "dam": "ضُعْف",
            },
            pos="start",
            sura_idx=30,
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
