import re

from quran_transcript import Aya
import quran_transcript.alphabet as alph
from quran_transcript.alphabet import uthmani as uth
from quran_transcript.alphabet import phonetics as ph
from quran_transcript.alphabet import phonetic_groups as phg
from quran_transcript.phonetics.operations import (
    ConvertAlifMaksora,
    ConversionOperation,
    BeginWithHamzatWasl,
    NormalizeHmazat,
    DeleteShaddaAtBeginning,
    CleanEnd,
    EnlargeSmallLetters,
    RemoveKasheeda,
    DisassembleHrofMoqatta,
    SpecialCases,
    IthbatYaaYohie,
    RemoveHmzatWaslMiddle,
    RemoveSkoonMostadeer,
    SkoonMostateel,
    MaddAlewad,
    WawAlsalah,
    NormalizeTaa,
    AddAlifIsmAllah,
    PrepareGhonnaIdghamIqlab,
    IltiqaaAlsaknan,
    Ghonna,
    Tasheel,
    Imala,
)
from quran_transcript.phonetics.operations import QuranPhonemesPhonetizer
from quran_transcript.phonetics.moshaf_attributes import MoshafAttributes


def get_occurance(
    char: str,
    operations: list[ConversionOperation] = [],
    context=4,
    limit: int | None = None,
    specific_aya: Aya | None = None,
):
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    if specific_aya is None:
        start_aya = Aya()
        max_loop = None
    else:
        start_aya = specific_aya
        max_loop = 1
    counter = 0
    for aya in start_aya.get_ayat_after(num_ayat=max_loop):
        txt = aya.get().uthmani
        for op in operations:
            txt = op.apply(txt, moshaf, mode="inference")
        outs = re.finditer(char, txt)
        first = True
        for out in outs:
            if first:
                print(aya)
                first = False
            counter += 1
            print(f"Case: `{counter}`")
            print(out)
            print(f"'{aya.get().uthmani[: out.start() + context]}'")
            print(f"'{txt[: out.start() + context]}'")

            print("-" * 30)
            print()
            print()

        if limit is not None:
            if counter >= limit:
                break


def get_missing_cases(
    char: str, regs: list[str], operations: list[ConversionOperation] = []
):
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    start_aya = Aya()
    for aya in start_aya.get_ayat_after(114):
        txt = aya.get().uthmani
        for op in operations:
            txt = op.apply(txt, moshaf)
        if char in txt:
            main_outs = re.finditer(char, txt)
            found = False
            for main_out in main_outs:
                txt_part = txt[: main_out.start() + len(char) + 5]
                for reg in regs:
                    re_out = re.search(reg, txt_part)
                    if re_out:
                        found = True
                        break
                if not found:
                    print(aya)
                    print(txt_part)
                    print("-" * 30)
                    print()
                    print()


if __name__ == "__main__":
    # get_occurance(alph.uthmani.alif_maksora)
    get_missing_cases(
        alph.uthmani.alif_maksora,
        [
            f"{alph.uthmani.fatha}{alph.uthmani.alif_maksora}({alph.uthmani.space}|$)",
            f"{alph.uthmani.alif_maksora}{alph.uthmani.alif_khnjaria}",
            f"{alph.uthmani.kasra}{alph.uthmani.alif_maksora}",
            f"{alph.uthmani.alif_maksora}([{alph.uthmani.harakat_group}{alph.uthmani.ras_haaa}{alph.uthmani.shadda}{alph.uthmani.tanween_dam}{alph.uthmani.madd}])",
            f"({alph.uthmani.tanween_fath_mothhar}|{alph.uthmani.tanween_fath_modgham}){alph.uthmani.alif_maksora}",
        ],
    )

    # # yass + kasra at the end of the word
    # get_occurance(
    #     alph.uthmani.yaa + alph.uthmani.kasra + "(\s|$)",
    #     operations=[ConvertAlifMaksora()],
    #     context=10,
    # )

    # يحي
    # get_occurance(
    #     f"[{alph.uthmani.hamza}{alph.uthmani.noon}{alph.uthmani.yaa}{alph.uthmani.taa_mabsoota}]{alph.uthmani.dama}{alph.uthmani.haa_mohmala}{alph.uthmani.ras_haaa}{alph.uthmani.yaa}{alph.uthmani.kasra}({alph.uthmani.space}|$)",
    #     operations=[ConvertAlifMaksora(), NormalizeHmazat()],
    #     context=10,
    # )

    # # واو الصلاة
    # get_occurance(
    #     f"{alph.uthmani.waw}{alph.uthmani.alif_khnjaria}",
    #     operations=[ConvertAlifMaksora()],
    #     context=10,
    # )

    # ياء الصلة
    # get_occurance(
    #     alph.uthmani.small_yaa_sila,
    #     context=10,
    # )

    # # ياء الصلة
    # get_occurance(
    #     f"({alph.uthmani.tanween_fath_modgham}|{alph.uthmani.tanween_fath_mothhar})",
    #     context=10,
    # )

    # ت
    # get_occurance(
    #     # f"{alph.uthmani.taa_marboota}({alph.uthmani.shadda}|{alph.uthmani.ras_haaa})?$",
    #     f"{alph.uthmani.taa_marboota}$",
    #     context=10,
    #     operations=[CleanEnd()],
    # )

    # مد الفرق
    # get_occurance(
    #     f"{alph.uthmani.hamza}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.madd}{alph.uthmani.lam}",
    #     context=500,
    #     operations=[CleanEnd()],
    # )

    # # ضعف
    # get_occurance(
    #     f"(?<!\\b{alph.uthmani.ras_haaa}{alph.uthmani.space})" + "ضَعْف" + r"\b",
    #     context=10,
    # )

    # # سلاسلا
    # get_occurance(
    #     "سَلَـٰسِلَا۟",
    #     context=10,
    # )

    # #  اسم الله
    # get_occurance(
    #     f"({alph.uthmani.lam}{alph.uthmani.kasra}?{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha})({alph.uthmani.haa}(?:[{alph.uthmani.harakat_group}]{alph.uthmani.meem}|[{alph.uthmani.harakat_group}]|$))",
    #     context=10,
    #     limit=None,
    # )

    # print("Special case")
    # pattern = f"{alph.uthmani.lam}({alph.uthmani.kasra})?{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha}{alph.uthmani.haa}"
    # target_pattern = f"{alph.uthmani.lam}\\1{alph.uthmani.lam}{alph.uthmani.shadda}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.haa}"
    # out = re.sub(pattern, target_pattern, Aya(27, 59).get().uthmani)
    # print(out)

    # ها ويا للتنبيه
    # get_occurance(
    #     f"(^|{alph.uthmani.space}|((^|{alph.uthmani.space})[{alph.uthmani.faa}{alph.uthmani.waw}{alph.uthmani.hamza}]{alph.uthmani.fatha})){alph.uthmani.yaa}{alph.uthmani.fatha}{alph.uthmani.alif}{alph.uthmani.madd}{alph.uthmani.hamza}.(?!{alph.uthmani.space})",
    #     context=15,
    #     operations=[
    #         DisassembleHrofMoqatta(),
    #         SpecialCases(),
    #         ConvertAlifMaksora(),
    #         NormalizeHmazat(),
    #         IthbatYaaYohie(),
    #         RemoveKasheeda(),
    #         RemoveHmzatWaslMiddle(),
    #         RemoveSkoonMostadeer(),
    #         SkoonMostateel(),
    #         MaddAlewad(),
    #         WawAlsalah(),
    #         EnlargeSmallLetters(),
    #         CleanEnd(),
    #         NormalizeTaa(),
    #         AddAlifIsmAllah(),
    #         PrepareGhonnaIdghamIqlab(),
    #         IltiqaaAlsaknan(),
    #         Ghonna(),
    #         Tasheel(),
    #         Imala(),
    #     ],
    # )

    # حذف الحرف الأول
    # get_occurance(
    #     f"([{alph.uthmani.fatha}{alph.uthmani.dama}]{alph.uthmani.yaa}|[{alph.uthmani.fatha}{alph.uthmani.kasra}]{alph.uthmani.waw}|[{alph.uthmani.pure_letters_without_yaa_and_waw_group}]){alph.uthmani.space}?([{alph.uthmani.pure_letters_group}]{alph.uthmani.shadda})",
    #     context=10,
    #     specific_aya=Aya(22, 61),
    #     operations=[
    #         DisassembleHrofMoqatta(),
    #         SpecialCases(),
    #         ConvertAlifMaksora(),
    #         NormalizeHmazat(),
    #         IthbatYaaYohie(),
    #         RemoveKasheeda(),
    #         RemoveHmzatWaslMiddle(),
    #         RemoveSkoonMostadeer(),
    #         SkoonMostateel(),
    #         MaddAlewad(),
    #         WawAlsalah(),
    #         EnlargeSmallLetters(),
    #         CleanEnd(),
    #         NormalizeTaa(),
    #         AddAlifIsmAllah(),
    #     ],
    # )

    # # كسر التنوين
    # get_occurance(
    #     f"({alph.uthmani.noon}){alph.uthmani.ras_haaa}({alph.uthmani.space}.[{alph.uthmani.ras_haaa}{alph.uthmani.shadda}])",
    #     context=10,
    #     operations=[
    #         DisassembleHrofMoqatta(),
    #         SpecialCases(),
    #         ConvertAlifMaksora(),
    #         NormalizeHmazat(),
    #         IthbatYaaYohie(),
    #         RemoveKasheeda(),
    #         RemoveHmzatWaslMiddle(),
    #         RemoveSkoonMostadeer(),
    #         SkoonMostateel(),
    #         MaddAlewad(),
    #         WawAlsalah(),
    #         EnlargeSmallLetters(),
    #         CleanEnd(),
    #         NormalizeTaa(),
    #         AddAlifIsmAllah(),
    #         PrepareGhonnaIdghamIqlab(),
    #     ],
    # )

    # # التقاء السكنان والأول منها حرف مد
    # get_occurance(
    #     f"({alph.uthmani.madd_alif}|{alph.uthmani.madd_yaa}|{alph.uthmani.madd_yaa})({alph.uthmani.space}.[{alph.uthmani.ras_haaa}{alph.uthmani.shadda}])",
    #     context=10,
    #     operations=[
    #         DisassembleHrofMoqatta(),
    #         SpecialCases(),
    #         ConvertAlifMaksora(),
    #         NormalizeHmazat(),
    #         IthbatYaaYohie(),
    #         RemoveKasheeda(),
    #         RemoveHmzatWaslMiddle(),
    #         RemoveSkoonMostadeer(),
    #         SkoonMostateel(),
    #         MaddAlewad(),
    #         WawAlsalah(),
    #         EnlargeSmallLetters(),
    #         CleanEnd(),
    #         NormalizeTaa(),
    #         AddAlifIsmAllah(),
    #         PrepareGhonnaIdghamIqlab(),
    #     ],
    # )

    # كشف أخظاء التنوين المدغم;w
    # get_occurance(
    #     f"[{alph.uthmani.tanween_fath}{alph.uthmani.tanween_dam}{alph.uthmani.tanween_kasr}]{alph.uthmani.meem_iqlab}{alph.uthmani.space}[{alph.uthmani.noon_ikhfaa_group}{alph.uthmani.yaa}{alph.uthmani.waw}]",
    #     # f"[{alph.uthmani.tanween_fath}{alph.uthmani.tanween_dam}{alph.uthmani.tanween_kasr}]{alph.uthmani.tanween_idhaam_dterminer}{alph.uthmani.space}[{alph.uthmani.noon_ikhfaa_group}{alph.uthmani.yaa}{alph.uthmani.waw}]",
    #     context=10,
    # )
    # get_occurance(
    #     # f"[{alph.uthmani.tanween_fath}{alph.uthmani.tanween_dam}{alph.uthmani.tanween_kasr}]{alph.uthmani.meem_iqlab}{alph.uthmani.space}{alph.uthmani.baa}",
    #     f"[{alph.uthmani.tanween_fath}{alph.uthmani.tanween_dam}{alph.uthmani.tanween_kasr}]{alph.uthmani.tanween_idhaam_dterminer}{alph.uthmani.space}{alph.uthmani.baa}",
    #     context=10,
    # )
    # get_occurance(
    #     f"{alph.uthmani.noon}{alph.uthmani.tanween_idhaam_dterminer}",
    #     context=10,
    # )

    #  مد اللين
    # get_occurance(
    #     f"({alph.uthmani.fatha})([{alph.uthmani.yaa}{alph.uthmani.waw}]){alph.uthmani.ras_haaa}?(.{alph.uthmani.ras_haaa}?$)",
    #     specific_aya=Aya(106, 1),
    #     operations=[
    #         DisassembleHrofMoqatta(),
    #         SpecialCases(),
    #         ConvertAlifMaksora(),
    #         NormalizeHmazat(),
    #         IthbatYaaYohie(),
    #         RemoveKasheeda(),
    #         RemoveHmzatWaslMiddle(),
    #         RemoveSkoonMostadeer(),
    #         SkoonMostateel(),
    #         MaddAlewad(),
    #         WawAlsalah(),
    #         EnlargeSmallLetters(),
    #         CleanEnd(),
    #         NormalizeTaa(),
    #         AddAlifIsmAllah(),
    #         PrepareGhonnaIdghamIqlab(),
    #         IltiqaaAlsaknan(),
    #         Ghonna(),
    #         Tasheel(),
    #         Imala(),
    #     ],
    # )

    # # اسم الله بعد إجراء كل العمليات
    # get_occurance(
    #     f"{alph.phonetics.lam}{{2}}{alph.phonetics.fatha}{alph.phonetics.alif}{{2}}{alph.phonetics.haa}",
    #     operations=QuranPhonemesPhonetizer().ops,
    # )

    # المد الطبيعي
    # get_occurance(
    #     f"{alph.uthmani.dama}{alph.uthmani.waw}{alph.uthmani.yaa}",
    #     # f"{alph.uthmani.kasra}{alph.uthmani.yaa}(?![{alph.uthmani.alif}{alph.uthmani.yaa}{alph.uthmani.waw}{alph.uthmani.ras_haaa}{alph.uthmani.shadda}{alph.uthmani.harakat_group}])",
    #     operations=[
    #         DisassembleHrofMoqatta(),
    #         SpecialCases(),
    #         BeginWithHamzatWasl(),
    #         ConvertAlifMaksora(),
    #         NormalizeHmazat(),
    #         IthbatYaaYohie(),
    #         RemoveKasheeda(),
    #         RemoveHmzatWaslMiddle(),
    #         RemoveSkoonMostadeer(),
    #         SkoonMostateel(),
    #         MaddAlewad(),
    #         WawAlsalah(),
    #         EnlargeSmallLetters(),
    #         CleanEnd(),
    #         NormalizeTaa(),
    #         AddAlifIsmAllah(),
    #         PrepareGhonnaIdghamIqlab(),
    #         IltiqaaAlsaknan(),
    #         DeleteShaddaAtBeginning(),
    #         Ghonna(),
    #         Tasheel(),
    #         Imala(),
    #     ],
    # )

    # # اسم الله بعد إجراء كل العمليات
    # get_occurance(
    #     f"(?<!{ph.jeem})(?<!{ph.daal})(?<!{ph.taa}{ph.fatha}{ph.waw})(.){uth.space}?{ph.lam}{{2}}{ph.fatha}{ph.alif}{{2,6}}{ph.haa}(?!{ph.dama}{ph.meem}(?!{ph.meem}))",
    #     operations=QuranPhonemesPhonetizer().ops,
    # )

    # حرف الراء
    get_occurance(
        f"{uth.raa}{uth.space}{uth.raa}{uth.shadda}"
        # operations=QuranPhonemesPhonetizer().ops,
    )
