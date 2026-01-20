import pytest
import re
from dataclasses import asdict
from typing import Literal

from quran_transcript.phonetics.moshaf_attributes import MoshafAttributes
from quran_transcript.phonetics.operations import (
    DisassembleHrofMoqatta,
    SpecialCases,
    BeginWithHamzatWasl,
    ConvertAlifMaksora,
    NormalizeHmazat,
    IthbatYaaYohie,
    RemoveKasheeda,
    RemoveHmzatWaslMiddle,
    RemoveSkoonMostadeer,
    SkoonMostateel,
    MaddAlewad,
    WawAlsalah,
    EnlargeSmallLetters,
    CleanEnd,
    NormalizeTaa,
    AddAlifIsmAllah,
    PrepareGhonnaIdghamIqlab,
    IltiqaaAlsaknan,
    Ghonna,
    Tasheel,
    Imala,
    Madd,
    Qalqla,
)
from quran_transcript.phonetics.phonetizer import quran_phonetizer
from quran_transcript.phonetics.sifa import (
    process_sifat,
    SifaOutput,
    lam_tafkheem_tarqeeq_finder,
    alif_tafkheem_tarqeeq_finder,
    raa_tafkheem_tarqeeq_finder,
)
from quran_transcript import Aya
from quran_transcript import alphabet as alph


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ فِيهِ هُدًۭى لِّلْمُتَّقِينَ",
            "ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ فِيهِ هُدًۭ لِّلْمُتَّقِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # alif khnjaria
        (
            "أُو۟لَـٰٓئِكَ ٱلَّذِينَ ٱشْتَرَوُا۟ ٱلضَّلَـٰلَةَ بِٱلْهُدَىٰ فَمَا رَبِحَت تِّجَـٰرَتُهُمْ وَمَا كَانُوا۟ مُهْتَدِينَ",
            "أُو۟لَـٰٓئِكَ ٱلَّذِينَ ٱشْتَرَوُا۟ ٱلضَّلَـٰلَةَ بِٱلْهُدَا فَمَا رَبِحَت تِّجَـٰرَتُهُمْ وَمَا كَانُوا۟ مُهْتَدِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # alif middle
        (
            "إِذْ هَمَّت طَّآئِفَتَانِ مِنكُمْ أَن تَفْشَلَا وَٱللَّهُ وَلِيُّهُمَا وَعَلَى ٱللَّهِ فَلْيَتَوَكَّلِ ٱلْمُؤْمِنُونَ",
            "إِذْ هَمَّت طَّآئِفَتَانِ مِنكُمْ أَن تَفْشَلَا وَٱللَّهُ وَلِيُّهُمَا وَعَلَا ٱللَّهِ فَلْيَتَوَكَّلِ ٱلْمُؤْمِنُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # alif end
        (
            "إِذْ هَمَّت طَّآئِفَتَانِ مِنكُمْ أَن تَفْشَلَا وَٱللَّهُ وَلِيُّهُمَا وَعَلَى",
            "إِذْ هَمَّت طَّآئِفَتَانِ مِنكُمْ أَن تَفْشَلَا وَٱللَّهُ وَلِيُّهُمَا وَعَلَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa (kasra before)
        (
            "أَوْ كَصَيِّبٍۢ مِّنَ ٱلسَّمَآءِ فِيهِ ظُلُمَـٰتٌۭ وَرَعْدٌۭ وَبَرْقٌۭ يَجْعَلُونَ أَصَـٰبِعَهُمْ فِىٓ ءَاذَانِهِم مِّنَ ٱلصَّوَٰعِقِ حَذَرَ ٱلْمَوْتِ وَٱللَّهُ مُحِيطٌۢ بِٱلْكَـٰفِرِينَ",
            "أَوْ كَصَيِّبٍۢ مِّنَ ٱلسَّمَآءِ فِيهِ ظُلُمَـٰتٌۭ وَرَعْدٌۭ وَبَرْقٌۭ يَجْعَلُونَ أَصَـٰبِعَهُمْ فِيٓ ءَاذَانِهِم مِّنَ ٱلصَّوَٰعِقِ حَذَرَ ٱلْمَوْتِ وَٱللَّهُ مُحِيطٌۢ بِٱلْكَـٰفِرِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa multiples
        (
            "وَلَمَّا جَهَّزَهُم بِجَهَازِهِمْ قَالَ ٱئْتُونِى بِأَخٍۢ لَّكُم مِّنْ أَبِيكُمْ أَلَا تَرَوْنَ أَنِّىٓ أُوفِى ٱلْكَيْلَ وَأَنَا۠ خَيْرُ ٱلْمُنزِلِينَ",
            "وَلَمَّا جَهَّزَهُم بِجَهَازِهِمْ قَالَ ٱئْتُونِي بِأَخٍۢ لَّكُم مِّنْ أَبِيكُمْ أَلَا تَرَوْنَ أَنِّيٓ أُوفِي ٱلْكَيْلَ وَأَنَا۠ خَيْرُ ٱلْمُنزِلِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + kasra
        (
            "وَقَالَ ٱللَّهُ لَا تَتَّخِذُوٓا۟ إِلَـٰهَيْنِ ٱثْنَيْنِ إِنَّمَا هُوَ إِلَـٰهٌۭ وَٰحِدٌۭ فَإِيَّـٰىَ فَٱرْهَبُونِ",
            "وَقَالَ ٱللَّهُ لَا تَتَّخِذُوٓا۟ إِلَـٰهَيْنِ ٱثْنَيْنِ إِنَّمَا هُوَ إِلَـٰهٌۭ وَٰحِدٌۭ فَإِيَّـٰيَ فَٱرْهَبُونِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + tanween dam
        (
            "صُمٌّۢ بُكْمٌ عُمْىٌۭ فَهُمْ لَا يَرْجِعُونَ",
            "صُمٌّۢ بُكْمٌ عُمْيٌۭ فَهُمْ لَا يَرْجِعُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + damma
        (
            "أَلَمْ يَعْلَمُوٓا۟ أَنَّهُۥ مَن يُحَادِدِ ٱللَّهَ وَرَسُولَهُۥ فَأَنَّ لَهُۥ نَارَ جَهَنَّمَ خَـٰلِدًۭا فِيهَا ذَٰلِكَ ٱلْخِزْىُ ٱلْعَظِيمُ",
            "أَلَمْ يَعْلَمُوٓا۟ أَنَّهُۥ مَن يُحَادِدِ ٱللَّهَ وَرَسُولَهُۥ فَأَنَّ لَهُۥ نَارَ جَهَنَّمَ خَـٰلِدًۭا فِيهَا ذَٰلِكَ ٱلْخِزْيُ ٱلْعَظِيمُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + ksara
        (
            "قُلْ إِنَّمَآ أُنذِرُكُم بِٱلْوَحْىِ وَلَا يَسْمَعُ ٱلصُّمُّ ٱلدُّعَآءَ إِذَا مَا يُنذَرُونَ",
            "قُلْ إِنَّمَآ أُنذِرُكُم بِٱلْوَحْيِ وَلَا يَسْمَعُ ٱلصُّمُّ ٱلدُّعَآءَ إِذَا مَا يُنذَرُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + raas_haa
        (
            "وَءَاتُوا۟ ٱلنِّسَآءَ صَدُقَـٰتِهِنَّ نِحْلَةًۭ فَإِن طِبْنَ لَكُمْ عَن شَىْءٍۢ مِّنْهُ نَفْسًۭا فَكُلُوهُ هَنِيٓـًۭٔا مَّرِيٓـًۭٔا",
            "وَءَاتُوا۟ ٱلنِّسَآءَ صَدُقَـٰتِهِنَّ نِحْلَةًۭ فَإِن طِبْنَ لَكُمْ عَن شَيْءٍۢ مِّنْهُ نَفْسًۭا فَكُلُوهُ هَنِيٓـًۭٔا مَّرِيٓـًۭٔا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + shadda
        (
            "بِأَىِّ ذَنۢبٍۢ قُتِلَتْ",
            "بِأَيِّ ذَنۢبٍۢ قُتِلَتْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa + madd
        (
            "وَأَشْرَقَتِ ٱلْأَرْضُ بِنُورِ رَبِّهَا وَوُضِعَ ٱلْكِتَـٰبُ وَجِا۟ىٓءَ بِٱلنَّبِيِّـۧنَ وَٱلشُّهَدَآءِ وَقُضِىَ بَيْنَهُم بِٱلْحَقِّ وَهُمْ لَا يُظْلَمُونَ",
            "وَأَشْرَقَتِ ٱلْأَرْضُ بِنُورِ رَبِّهَا وَوُضِعَ ٱلْكِتَـٰبُ وَجِا۟يٓءَ بِٱلنَّبِيِّـۧنَ وَٱلشُّهَدَآءِ وَقُضِيَ بَيْنَهُم بِٱلْحَقِّ وَهُمْ لَا يُظْلَمُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_convert_alif_maksora(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = ConvertAlifMaksora()
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


def test_convert_alif_maksora_stress_test():
    start_aya = Aya()
    op = ConvertAlifMaksora()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    for aya in start_aya.get_ayat_after(114):
        txt = aya.get().uthmani
        out_text, _ = op.apply(txt, moshaf, None, mode="test")
        if alph.uthmani.alif_maksora in out_text:
            print(aya)
            print(out_text)
            raise ValueError()


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "وَمَن يَرْغَبُ عَن مِّلَّةِ إِبْرَٰهِـۧمَ إِلَّا مَن سَفِهَ نَفْسَهُۥ وَلَقَدِ ٱصْطَفَيْنَـٰهُ فِى ٱلدُّنْيَا وَإِنَّهُۥ فِى ٱلْـَٔاخِرَةِ لَمِنَ ٱلصَّـٰلِحِينَ",
            "وَمَن يَرْغَبُ عَن مِّلَّةِ ءِبْرَٰهِـۧمَ ءِلَّا مَن سَفِهَ نَفْسَهُۥ وَلَقَدِ ٱصْطَفَيْنَـٰهُ فِى ٱلدُّنْيَا وَءِنَّهُۥ فِى ٱلْـءَاخِرَةِ لَمِنَ ٱلصَّـٰلِحِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_normalize_hamazat(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = NormalizeHmazat()
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


def test_normalize_hamazat_stress_test():
    start_aya = Aya()
    op = NormalizeHmazat()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    hamazat = re.sub(alph.uthmani.hamza, "", alph.uthmani.hamazat_group)
    for aya in start_aya.get_ayat_after(114):
        txt = aya.get().uthmani
        out_text, _ = op.apply(txt, moshaf, None, mode="test")
        if re.search(f"[{hamazat}]", out_text):
            print(aya)
            print(out_text)
            raise ValueError()


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "أَلَمْ تَرَ إِلَى ٱلَّذِى حَآجَّ إِبْرَٰهِـۧمَ فِى رَبِّهِۦٓ أَنْ ءَاتَىٰهُ ٱللَّهُ ٱلْمُلْكَ إِذْ قَالَ إِبْرَٰهِـۧمُ رَبِّىَ ٱلَّذِى يُحْىِۦ وَيُمِيتُ قَالَ أَنَا۠ أُحْىِۦ وَأُمِيتُ قَالَ إِبْرَٰهِـۧمُ فَإِنَّ ٱللَّهَ يَأْتِى بِٱلشَّمْسِ مِنَ ٱلْمَشْرِقِ فَأْتِ بِهَا مِنَ ٱلْمَغْرِبِ فَبُهِتَ ٱلَّذِى كَفَرَ وَٱللَّهُ لَا يَهْدِى ٱلْقَوْمَ ٱلظَّـٰلِمِينَ",
            "أَلَمْ تَرَ إِلَى ٱلَّذِى حَآجَّ إِبْرَٰهِـۧمَ فِى رَبِّهِۦٓ أَنْ ءَاتَىٰهُ ٱللَّهُ ٱلْمُلْكَ إِذْ قَالَ إِبْرَٰهِـۧمُ رَبِّىَ ٱلَّذِى يُحْىِۦ وَيُمِيتُ قَالَ أَنَا۠ أُحْىِۦ وَأُمِيتُ قَالَ إِبْرَٰهِـۧمُ فَإِنَّ ٱللَّهَ يَأْتِى بِٱلشَّمْسِ مِنَ ٱلْمَشْرِقِ فَأْتِ بِهَا مِنَ ٱلْمَغْرِبِ فَبُهِتَ ٱلَّذِى كَفَرَ وَٱللَّهُ لَا يَهْدِى ٱلْقَوْمَ ٱلظَّـٰلِمِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَإِذْ قَالَ إِبْرَٰهِـۧمُ رَبِّ أَرِنِى كَيْفَ تُحْىِ ٱلْمَوْتَىٰ قَالَ أَوَلَمْ تُؤْمِن قَالَ بَلَىٰ وَلَـٰكِن لِّيَطْمَئِنَّ قَلْبِى قَالَ فَخُذْ أَرْبَعَةًۭ مِّنَ ٱلطَّيْرِ فَصُرْهُنَّ إِلَيْكَ ثُمَّ ٱجْعَلْ عَلَىٰ كُلِّ جَبَلٍۢ مِّنْهُنَّ جُزْءًۭا ثُمَّ ٱدْعُهُنَّ يَأْتِينَكَ سَعْيًۭا وَٱعْلَمْ أَنَّ ٱللَّهَ عَزِيزٌ حَكِيمٌۭ",
            "وَإِذْ قَالَ إِبْرَٰهِـۧمُ رَبِّ أَرِنِى كَيْفَ تُحْيِي ٱلْمَوْتَىٰ قَالَ أَوَلَمْ تُؤْمِن قَالَ بَلَىٰ وَلَـٰكِن لِّيَطْمَئِنَّ قَلْبِى قَالَ فَخُذْ أَرْبَعَةًۭ مِّنَ ٱلطَّيْرِ فَصُرْهُنَّ إِلَيْكَ ثُمَّ ٱجْعَلْ عَلَىٰ كُلِّ جَبَلٍۢ مِّنْهُنَّ جُزْءًۭا ثُمَّ ٱدْعُهُنَّ يَأْتِينَكَ سَعْيًۭا وَٱعْلَمْ أَنَّ ٱللَّهَ عَزِيزٌ حَكِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_ithbat_yaa_yohie(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = IthbatYaaYohie()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "وَٱلَّذِينَ يُؤْمِنُونَ بِمَآ أُنزِلَ إِلَيْكَ وَمَآ أُنزِلَ مِن قَبْلِكَ وَبِٱلْـَٔاخِرَةِ هُمْ يُوقِنُونَ",
            "وَٱلَّذِينَ يُؤْمِنُونَ بِمَآ أُنزِلَ إِلَيْكَ وَمَآ أُنزِلَ مِن قَبْلِكَ وَبِٱلَْٔاخِرَةِ هُمْ يُوقِنُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_remove_kasheeda(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = RemoveKasheeda()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ٱسْتِكْبَارًۭا فِى ٱلْأَرْضِ وَمَكْرَ ٱلسَّيِّئِ وَلَا يَحِيقُ ٱلْمَكْرُ ٱلسَّيِّئُ إِلَّا بِأَهْلِهِۦ فَهَلْ يَنظُرُونَ إِلَّا سُنَّتَ ٱلْأَوَّلِينَ فَلَن تَجِدَ لِسُنَّتِ ٱللَّهِ تَبْدِيلًۭا وَلَن تَجِدَ لِسُنَّتِ ٱللَّهِ تَحْوِيلًا",
            "ٱسْتِكْبَارًۭا فِى لْأَرْضِ وَمَكْرَ لسَّيِّئِ وَلَا يَحِيقُ لْمَكْرُ لسَّيِّئُ إِلَّا بِأَهْلِهِۦ فَهَلْ يَنظُرُونَ إِلَّا سُنَّتَ لْأَوَّلِينَ فَلَن تَجِدَ لِسُنَّتِ للَّهِ تَبْدِيلًۭا وَلَن تَجِدَ لِسُنَّتِ للَّهِ تَحْوِيلًا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قَالَ رَبُّ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَمَا بَيْنَهُمَآ إِن كُنتُم مُّوقِنِينَ",
            "قَالَ رَبُّ لسَّمَـٰوَٰتِ وَلْأَرْضِ وَمَا بَيْنَهُمَآ إِن كُنتُم مُّوقِنِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_remove_kasheeda(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = RemoveHmzatWaslMiddle()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "وَجِا۟ىٓءَ يَوْمَئِذٍۭ بِجَهَنَّمَ يَوْمَئِذٍۢ يَتَذَكَّرُ ٱلْإِنسَـٰنُ وَأَنَّىٰ لَهُ ٱلذِّكْرَىٰ",
            "وَجِىٓءَ يَوْمَئِذٍۭ بِجَهَنَّمَ يَوْمَئِذٍۢ يَتَذَكَّرُ ٱلْإِنسَـٰنُ وَأَنَّىٰ لَهُ ٱلذِّكْرَىٰ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَٱنطَلَقَ ٱلْمَلَأُ مِنْهُمْ أَنِ ٱمْشُوا۟ وَٱصْبِرُوا۟ عَلَىٰٓ ءَالِهَتِكُمْ إِنَّ هَـٰذَا لَشَىْءٌۭ يُرَادُ",
            "وَٱنطَلَقَ ٱلْمَلَأُ مِنْهُمْ أَنِ ٱمْشُو وَٱصْبِرُو عَلَىٰٓ ءَالِهَتِكُمْ إِنَّ هَـٰذَا لَشَىْءٌۭ يُرَادُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_remove_skoon_mostadeer(
    in_text: str, target_text: str, moshaf: MoshafAttributes
):
    op = RemoveSkoonMostadeer()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "فَقَالَ أَنَا۠ رَبُّكُمُ ٱلْأَعْلَىٰ",
            "فَقَالَ أَنَ رَبُّكُمُ ٱلْأَعْلَىٰ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَيُطَافُ عَلَيْهِم بِـَٔانِيَةٍۢ مِّن فِضَّةٍۢ وَأَكْوَابٍۢ كَانَتْ قَوَارِيرَا۠",
            "وَيُطَافُ عَلَيْهِم بِـَٔانِيَةٍۢ مِّن فِضَّةٍۢ وَأَكْوَابٍۢ كَانَتْ قَوَارِيرَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_skoon_mostateel(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = SkoonMostateel()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


def test_skoon_mostateel_stree_test():
    start_aya = Aya()
    op = SkoonMostateel()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    for aya in start_aya.get_ayat_after(114):
        txt = aya.get().uthmani
        out_text, _ = op.apply(txt, moshaf, None, mode="test")
        if alph.uthmani.skoon_mostateel in out_text:
            print(aya)
            print(out_text)
            raise ValueError()


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "وَإِن مِّن قَرْيَةٍ إِلَّا نَحْنُ مُهْلِكُوهَا قَبْلَ يَوْمِ ٱلْقِيَـٰمَةِ أَوْ مُعَذِّبُوهَا عَذَابًۭا شَدِيدًۭا كَانَ ذَٰلِكَ فِى ٱلْكِتَـٰبِ مَسْطُورًۭا",
            "وَإِن مِّن قَرْيَةٍ إِلَّا نَحْنُ مُهْلِكُوهَا قَبْلَ يَوْمِ ٱلْقِيَـٰمَةِ أَوْ مُعَذِّبُوهَا عَذَابًۭ شَدِيدًۭ كَانَ ذَٰلِكَ فِى ٱلْكِتَـٰبِ مَسْطُورَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلَّذِى جَعَلَ لَكُمُ ٱلْأَرْضَ فِرَٰشًۭا وَٱلسَّمَآءَ بِنَآءًۭ وَأَنزَلَ مِنَ ٱلسَّمَآءِ مَآءًۭ فَأَخْرَجَ بِهِۦ مِنَ ٱلثَّمَرَٰتِ رِزْقًۭا لَّكُمْ فَلَا تَجْعَلُوا۟ لِلَّهِ أَندَادًۭا وَأَنتُمْ تَعْلَمُونَ",
            "ٱلَّذِى جَعَلَ لَكُمُ ٱلْأَرْضَ فِرَٰشًۭ وَٱلسَّمَآءَ بِنَآءًۭ وَأَنزَلَ مِنَ ٱلسَّمَآءِ مَآءًۭ فَأَخْرَجَ بِهِۦ مِنَ ٱلثَّمَرَٰتِ رِزْقًۭ لَّكُمْ فَلَا تَجْعَلُوا۟ لِلَّهِ أَندَادًۭ وَأَنتُمْ تَعْلَمُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلَّذِى جَعَلَ لَكُمُ ٱلْأَرْضَ فِرَٰشًۭا وَٱلسَّمَآءَ بِنَآءًۭ وَأَنزَلَ مِنَ ٱلسَّمَآءِ مَآءًۭ",
            "ٱلَّذِى جَعَلَ لَكُمُ ٱلْأَرْضَ فِرَٰشًۭ وَٱلسَّمَآءَ بِنَآءًۭ وَأَنزَلَ مِنَ ٱلسَّمَآءِ مَآءَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَٱلسَّارِقُ وَٱلسَّارِقَةُ فَٱقْطَعُوٓا۟ أَيْدِيَهُمَا جَزَآءًۢ بِمَا كَسَبَا نَكَـٰلًۭا مِّنَ ٱللَّهِ وَٱللَّهُ عَزِيزٌ حَكِيمٌۭ",
            "وَٱلسَّارِقُ وَٱلسَّارِقَةُ فَٱقْطَعُوٓا۟ أَيْدِيَهُمَا جَزَآءًۢ بِمَا كَسَبَا نَكَـٰلًۭ مِّنَ ٱللَّهِ وَٱللَّهُ عَزِيزٌ حَكِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَٱلسَّارِقُ وَٱلسَّارِقَةُ فَٱقْطَعُوٓا۟ أَيْدِيَهُمَا جَزَآءًۢ",
            "وَٱلسَّارِقُ وَٱلسَّارِقَةُ فَٱقْطَعُوٓا۟ أَيْدِيَهُمَا جَزَآءَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_madd_alewad(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = MaddAlewad()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "إِنَّمَا يَعْمُرُ مَسَـٰجِدَ ٱللَّهِ مَنْ ءَامَنَ بِٱللَّهِ وَٱلْيَوْمِ ٱلْـَٔاخِرِ وَأَقَامَ ٱلصَّلَوٰةَ وَءَاتَى ٱلزَّكَوٰةَ وَلَمْ يَخْشَ إِلَّا ٱللَّهَ فَعَسَىٰٓ أُو۟لَـٰٓئِكَ أَن يَكُونُوا۟ مِنَ ٱلْمُهْتَدِينَ",
            "إِنَّمَا يَعْمُرُ مَسَـٰجِدَ ٱللَّهِ مَنْ ءَامَنَ بِٱللَّهِ وَٱلْيَوْمِ ٱلْـَٔاخِرِ وَأَقَامَ ٱلصَّلَاةَ وَءَاتَى ٱلزَّكَاةَ وَلَمْ يَخْشَ إِلَّا ٱللَّهَ فَعَسَىٰٓ أُو۟لَـٰٓئِكَ أَن يَكُونُوا۟ مِنَ ٱلْمُهْتَدِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلَّذِينَ يَأْكُلُونَ ٱلرِّبَوٰا۟ لَا يَقُومُونَ إِلَّا كَمَا يَقُومُ ٱلَّذِى يَتَخَبَّطُهُ ٱلشَّيْطَـٰنُ مِنَ ٱلْمَسِّ ذَٰلِكَ بِأَنَّهُمْ قَالُوٓا۟ إِنَّمَا ٱلْبَيْعُ مِثْلُ ٱلرِّبَوٰا۟ وَأَحَلَّ ٱللَّهُ ٱلْبَيْعَ وَحَرَّمَ ٱلرِّبَوٰا۟ فَمَن جَآءَهُۥ مَوْعِظَةٌۭ مِّن رَّبِّهِۦ فَٱنتَهَىٰ فَلَهُۥ مَا سَلَفَ وَأَمْرُهُۥٓ إِلَى ٱللَّهِ وَمَنْ عَادَ فَأُو۟لَـٰٓئِكَ أَصْحَـٰبُ ٱلنَّارِ هُمْ فِيهَا خَـٰلِدُونَ",
            "ٱلَّذِينَ يَأْكُلُونَ ٱلرِّبَاا۟ لَا يَقُومُونَ إِلَّا كَمَا يَقُومُ ٱلَّذِى يَتَخَبَّطُهُ ٱلشَّيْطَـٰنُ مِنَ ٱلْمَسِّ ذَٰلِكَ بِأَنَّهُمْ قَالُوٓا۟ إِنَّمَا ٱلْبَيْعُ مِثْلُ ٱلرِّبَاا۟ وَأَحَلَّ ٱللَّهُ ٱلْبَيْعَ وَحَرَّمَ ٱلرِّبَاا۟ فَمَن جَآءَهُۥ مَوْعِظَةٌۭ مِّن رَّبِّهِۦ فَٱنتَهَىٰ فَلَهُۥ مَا سَلَفَ وَأَمْرُهُۥٓ إِلَى ٱللَّهِ وَمَنْ عَادَ فَأُو۟لَـٰٓئِكَ أَصْحَـٰبُ ٱلنَّارِ هُمْ فِيهَا خَـٰلِدُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "",
            "",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_waw_alslah(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = WawAlsalah()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ فِيهِ هُدًۭى لِّلْمُتَّقِينَ",
            "ذَالِكَ ٱلْكِتَـابُ لَا رَيْبَ فِيهِ هُدًۭى لِّلْمُتَّقِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَٱسْتَجَبْنَا لَهُۥ وَنَجَّيْنَـٰهُ مِنَ ٱلْغَمِّ وَكَذَٰلِكَ نُـۨجِى ٱلْمُؤْمِنِينَ",
            "فَٱسْتَجَبْنَا لَهُو وَنَجَّيْنَـاهُ مِنَ ٱلْغَمِّ وَكَذَالِكَ نُـنجِى ٱلْمُؤْمِنِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَيَخْلُدْ فِيهِۦ",
            "وَيَخْلُدْ فِيهِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "يَحْسَبُ أَنَّ مَالَهُۥٓ",
            "يَحْسَبُ أَنَّ مَالَهُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَلْيَنظُرِ ٱلْإِنسَـٰنُ إِلَىٰ طَعَامِهِۦٓ",
            "فَلْيَنظُرِ ٱلْإِنسَـانُ إِلَىا طَعَامِهِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_enlarge_small_letters(
    in_text: str, target_text: str, moshaf: MoshafAttributes
):
    op = EnlargeSmallLetters()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ فِيهِ هُدًۭى لِّلْمُتَّقِينَ",
            "ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ فِيهِ هُدًۭى لِّلْمُتَّقِين",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "لَّهُۥ مَا فِى ٱلسَّمَـٰوَٰتِ وَمَا فِى ٱلْأَرْضِ وَإِنَّ ٱللَّهَ لَهُوَ ٱلْغَنِىُّ ٱلْحَمِيدُ",
            "لَّهُۥ مَا فِى ٱلسَّمَـٰوَٰتِ وَمَا فِى ٱلْأَرْضِ وَإِنَّ ٱللَّهَ لَهُوَ ٱلْغَنِىُّ ٱلْحَمِيد",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "لَّهُۥ مَا فِى ٱلسَّمَـٰوَٰتِ وَمَا فِى ٱلْأَرْضِ وَإِنَّ ٱللَّهَ لَهُوَ ٱلْغَنِىُّ",
            "لَّهُۥ مَا فِى ٱلسَّمَـٰوَٰتِ وَمَا فِى ٱلْأَرْضِ وَإِنَّ ٱللَّهَ لَهُوَ ٱلْغَنِىّ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَٱلَّذِينَ يُؤْمِنُونَ بِمَآ أُنزِلَ إِلَيْكَ وَمَآ",
            "وَٱلَّذِينَ يُؤْمِنُونَ بِمَآ أُنزِلَ إِلَيْكَ وَمَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "لِيُوَفِّيَهُمْ أُجُورَهُمْ وَيَزِيدَهُم مِّن فَضْلِهِۦٓ إِنَّهُۥ غَفُورٌۭ شَكُورٌۭ",
            "لِيُوَفِّيَهُمْ أُجُورَهُمْ وَيَزِيدَهُم مِّن فَضْلِهِۦٓ إِنَّهُۥ غَفُورٌۭ شَكُور",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "إِنَّ ٱلَّذِينَ كَفَرُوا۟ سَوَآءٌ",
            "إِنَّ ٱلَّذِينَ كَفَرُوا۟ سَوَآء",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "يَمْحَقُ ٱللَّهُ ٱلرِّبَوٰا۟ وَيُرْبِى ٱلصَّدَقَـٰتِ وَٱللَّهُ لَا يُحِبُّ كُلَّ كَفَّارٍ",
            "يَمْحَقُ ٱللَّهُ ٱلرِّبَوٰا۟ وَيُرْبِى ٱلصَّدَقَـٰتِ وَٱللَّهُ لَا يُحِبُّ كُلَّ كَفَّار",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَتَوَلَّ عَنْهُمْ يَوْمَ يَدْعُ ٱلدَّاعِ إِلَىٰ شَىْءٍۢ نُّكُرٍ",
            "فَتَوَلَّ عَنْهُمْ يَوْمَ يَدْعُ ٱلدَّاعِ إِلَىٰ شَىْءٍۢ نُّكُر",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ",
            "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَد",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_clean_end(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = CleanEnd()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


def test_clean_end_stree_test():
    start_aya = Aya()
    op = CleanEnd()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    is_error = False
    for aya in start_aya.get_ayat_after(114):
        txt = aya.get().uthmani
        out_text, _ = op.apply(txt, moshaf, None, mode="test")
        if out_text[-1] not in (
            alph.uthmani.letters_group + alph.uthmani.ras_haaa + alph.uthmani.shadda
        ):
            is_error = True
            print(aya)
            print(out_text)
            print("\n" * 2)
    if is_error:
        raise ValueError()


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "لَّا مَقْطُوعَةٍۢ وَلَا مَمْنُوعَةٍۢ",
            "لَّا مَقْطُوعَتٍۢ وَلَا مَمْنُوعَه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_normalize_taa(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = NormalizeTaa()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ الٓمٓ ٱللَّهُ لَآ إِلَـٰهَ",
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ أَلِفْ لَآم مِّيٓمَ ٱللَّهُ لَآ إِلَـٰهَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "الٓمٓ",
            "أَلِفْ لَآم مِّيٓمْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "الٓمٓ ذَٰلِكَ ٱلْكِتَـٰبُ لَا",
            "أَلِفْ لَآم مِّيٓمْ ذَٰلِكَ ٱلْكِتَـٰبُ لَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ الٓمٓ ذَٰلِكَ ٱلْكِتَـٰبُ لَا",
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ أَلِفْ لَآم مِّيٓمْ ذَٰلِكَ ٱلْكِتَـٰبُ لَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَبَشِّرِ ٱلَّذِينَ ءَامَنُوا۟ وَعَمِلُوا۟ ٱلصَّـٰلِحَـٰتِ أَنَّ لَهُمْ جَنَّـٰتٍۢ تَجْرِى مِن تَحْتِهَا ٱلْأَنْهَـٰرُ كُلَّمَا رُزِقُوا۟ مِنْهَا مِن ثَمَرَةٍۢ رِّزْقًۭا قَالُوا۟ هَـٰذَا ٱلَّذِى رُزِقْنَا مِن قَبْلُ وَأُتُوا۟ بِهِۦ مُتَشَـٰبِهًۭا وَلَهُمْ فِيهَآ أَزْوَٰجٌۭ مُّطَهَّرَةٌۭ وَهُمْ فِيهَا خَـٰلِدُونَ",
            "وَبَشِّرِ ٱلَّذِينَ ءَامَنُوا۟ وَعَمِلُوا۟ ٱلصَّـٰلِحَـٰتِ أَنَّ لَهُمْ جَنَّـٰتٍۢ تَجْرِى مِن تَحْتِهَا ٱلْأَنْهَـٰرُ كُلَّمَا رُزِقُوا۟ مِنْهَا مِن ثَمَرَةٍۢ رِّزْقًۭا قَالُوا۟ هَـٰذَا ٱلَّذِى رُزِقْنَا مِن قَبْلُ وَأُتُوا۟ بِهِۦ مُتَشَـٰبِهًۭا وَلَهُمْ فِيهَآ أَزْوَٰجٌۭ مُّطَهَّرَةٌۭ وَهُمْ فِيهَا خَـٰلِدُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ حمٓ عٓسٓقٓ كَذَٰلِكَ يُوحِىٓ",
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ حَا مِيٓمْ عَيٓن سِيٓن قَآفْ كَذَٰلِكَ يُوحِىٓ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_disassemble_hrof_moqatta(
    in_text: str, target_text: str, moshaf: MoshafAttributes
):
    op = DisassembleHrofMoqatta()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ٱلْحَمْدُ لِلَّهِ ٱلَّذِىٓ أَنزَلَ عَلَىٰ عَبْدِهِ ٱلْكِتَـٰبَ وَلَمْ يَجْعَل لَّهُۥ عِوَجَا قَيِّمًۭا لِّيُنذِرَ بَأْسًۭا شَدِيدًۭا",
            "ٱلْحَمْدُ لِلَّهِ ٱلَّذِىٓ أَنزَلَ عَلَىٰ عَبْدِهِ ٱلْكِتَـٰبَ وَلَمْ يَجْعَل لَّهُۥ عِوَجَاۜ قَيِّمًۭا لِّيُنذِرَ بَأْسًۭا شَدِيدًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_iwaja="sakt",
            ),
        ),
        (
            "ٱلْحَمْدُ لِلَّهِ ٱلَّذِىٓ أَنزَلَ عَلَىٰ عَبْدِهِ ٱلْكِتَـٰبَ وَلَمْ يَجْعَل لَّهُۥ عِوَجَا قَيِّمًۭا لِّيُنذِرَ بَأْسًۭا شَدِيدًۭا",
            "ٱلْحَمْدُ لِلَّهِ ٱلَّذِىٓ أَنزَلَ عَلَىٰ عَبْدِهِ ٱلْكِتَـٰبَ وَلَمْ يَجْعَل لَّهُۥ عِوَجًۭا قَيِّمًۭا لِّيُنذِرَ بَأْسًۭا شَدِيدًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_iwaja="idraj",
            ),
        ),
        (
            "قَالُوا۟ يَـٰوَيْلَنَا مَنۢ بَعَثَنَا مِن مَّرْقَدِنَا هَـٰذَا مَا وَعَدَ ٱلرَّحْمَـٰنُ وَصَدَقَ ٱلْمُرْسَلُونَ",
            "قَالُوا۟ يَـٰوَيْلَنَا مَنۢ بَعَثَنَا مِن مَّرْقَدِنَاۜ هَـٰذَا مَا وَعَدَ ٱلرَّحْمَـٰنُ وَصَدَقَ ٱلْمُرْسَلُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_marqdena="sakt",
            ),
        ),
        (
            "قَالُوا۟ يَـٰوَيْلَنَا مَنۢ بَعَثَنَا مِن مَّرْقَدِنَا هَـٰذَا مَا وَعَدَ ٱلرَّحْمَـٰنُ وَصَدَقَ ٱلْمُرْسَلُونَ",
            "قَالُوا۟ يَـٰوَيْلَنَا مَنۢ بَعَثَنَا مِن مَّرْقَدِنَا هَـٰذَا مَا وَعَدَ ٱلرَّحْمَـٰنُ وَصَدَقَ ٱلْمُرْسَلُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_marqdena="idraj",
            ),
        ),
        (
            "وَقِيلَ مَنْ رَاقٍۢ",
            "وَقِيلَ مَنْۜ رَاقٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_man_raq="sakt",
            ),
        ),
        (
            "وَقِيلَ مَنْ رَاقٍۢ",
            "وَقِيلَ مَن رَّاقٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_man_raq="idraj",
            ),
        ),
        (
            "كَلَّا بَلْ رَانَ عَلَىٰ قُلُوبِهِم",
            "كَلَّا بَلْۜ رَانَ عَلَىٰ قُلُوبِهِم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_bal_ran="sakt",
            ),
        ),
        (
            "كَلَّا بَلْ رَانَ عَلَىٰ قُلُوبِهِم",
            "كَلَّا بَل رَّانَ عَلَىٰ قُلُوبِهِم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_bal_ran="idraj",
            ),
        ),
        (
            "مَآ أَغْنَىٰ عَنِّى مَالِيَهْ هَلَكَ عَنِّى سُلْطَـٰنِيَهْ",
            "مَآ أَغْنَىٰ عَنِّى مَالِيَهْۜ هَلَكَ عَنِّى سُلْطَـٰنِيَهْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_maleeyah="sakt",
            ),
        ),
        (
            "مَآ أَغْنَىٰ عَنِّى مَالِيَهْ هَلَكَ عَنِّى سُلْطَـٰنِيَهْ",
            "مَآ أَغْنَىٰ عَنِّى مَالِيَه هَّلَكَ عَنِّى سُلْطَـٰنِيَهْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                sakt_maleeyah="idgham",
            ),
        ),
        (
            "إِنَّ ٱللَّهَ بِكُلِّ شَىْءٍ عَلِيمٌۢ بَرَآءَةٌۭ مِّنَ ٱللَّهِ وَرَسُولِهِۦٓ",
            "إِنَّ ٱللَّهَ بِكُلِّ شَىْءٍ عَلِيمۜ بَرَآءَةٌۭ مِّنَ ٱللَّهِ وَرَسُولِهِۦٓ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "إِنَّ ٱللَّهَ بِكُلِّ شَىْءٍ عَلِيمٌۢ بَرَآءَةٌۭ مِّنَ ٱللَّهِ وَرَسُولِهِۦٓ",
            "إِنَّ ٱللَّهَ بِكُلِّ شَىْءٍ عَلِيمٌۢ بَرَآءَةٌۭ مِّنَ ٱللَّهِ وَرَسُولِهِۦٓ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="wasl",
            ),
        ),
        (
            "يسٓ",
            "يسٓ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_and_yaseen="izhar",
            ),
        ),
        (
            "يسٓ وَٱلْقُرْءَانِ ٱلْحَكِيمِ",
            "يَا سِيٓنْ وَٱلْقُرْءَانِ ٱلْحَكِيمِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_and_yaseen="izhar",
            ),
        ),
        (
            "يسٓ وَٱلْقُرْءَانِ ٱلْحَكِيمِ",
            "يَا سِيٓن وَٱلْقُرْءَانِ ٱلْحَكِيمِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_and_yaseen="idgham",
            ),
        ),
        (
            "نٓ وَٱلْقَلَمِ",
            "نُوٓنْ وَٱلْقَلَمِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_and_yaseen="izhar",
            ),
        ),
        (
            "نٓ وَٱلْقَلَمِ",
            "نُوٓن وَٱلْقَلَمِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_and_yaseen="idgham",
            ),
        ),
        (
            "فَلَمَّا جَآءَ سُلَيْمَـٰنَ قَالَ أَتُمِدُّونَنِ بِمَالٍۢ فَمَآ ءَاتَىٰنِۦَ ٱللَّهُ خَيْرٌۭ مِّمَّآ ءَاتَىٰكُم بَلْ أَنتُم بِهَدِيَّتِكُمْ تَفْرَحُونَ",
            "فَلَمَّا جَآءَ سُلَيْمَـٰنَ قَالَ أَتُمِدُّونَنِ بِمَالٍۢ فَمَآ ءَاتَىٰنِۦَ ٱللَّهُ خَيْرٌۭ مِّمَّآ ءَاتَىٰكُم بَلْ أَنتُم بِهَدِيَّتِكُمْ تَفْرَحُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yaa_ataan="wasl",
            ),
        ),
        (
            "فَلَمَّا جَآءَ سُلَيْمَـٰنَ قَالَ أَتُمِدُّونَنِ بِمَالٍۢ فَمَآ ءَاتَىٰنِۦَ",
            "فَلَمَّا جَآءَ سُلَيْمَـٰنَ قَالَ أَتُمِدُّونَنِ بِمَالٍۢ فَمَآ ءَاتَىٰنِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yaa_ataan="hadhf",
            ),
        ),
        (
            "فَلَمَّا جَآءَ سُلَيْمَـٰنَ قَالَ أَتُمِدُّونَنِ بِمَالٍۢ فَمَآ ءَاتَىٰنِۦَ",
            "فَلَمَّا جَآءَ سُلَيْمَـٰنَ قَالَ أَتُمِدُّونَنِ بِمَالٍۢ فَمَآ ءَاتَىٰنِي",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yaa_ataan="ithbat",
            ),
        ),
        (
            "يَـٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ لَا يَسْخَرْ قَوْمٌۭ مِّن قَوْمٍ عَسَىٰٓ أَن يَكُونُوا۟ خَيْرًۭا مِّنْهُمْ وَلَا نِسَآءٌۭ مِّن نِّسَآءٍ عَسَىٰٓ أَن يَكُنَّ خَيْرًۭا مِّنْهُنَّ وَلَا تَلْمِزُوٓا۟ أَنفُسَكُمْ وَلَا تَنَابَزُوا۟ بِٱلْأَلْقَـٰبِ بِئْسَ ٱلِٱسْمُ ٱلْفُسُوقُ بَعْدَ ٱلْإِيمَـٰنِ وَمَن لَّمْ يَتُبْ فَأُو۟لَـٰٓئِكَ هُمُ ٱلظَّـٰلِمُونَ",
            "يَـٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ لَا يَسْخَرْ قَوْمٌۭ مِّن قَوْمٍ عَسَىٰٓ أَن يَكُونُوا۟ خَيْرًۭا مِّنْهُمْ وَلَا نِسَآءٌۭ مِّن نِّسَآءٍ عَسَىٰٓ أَن يَكُنَّ خَيْرًۭا مِّنْهُنَّ وَلَا تَلْمِزُوٓا۟ أَنفُسَكُمْ وَلَا تَنَابَزُوا۟ بِٱلْأَلْقَـٰبِ بِئْسَ ٱلِٱسْمُ ٱلْفُسُوقُ بَعْدَ ٱلْإِيمَـٰنِ وَمَن لَّمْ يَتُبْ فَأُو۟لَـٰٓئِكَ هُمُ ٱلظَّـٰلِمُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                start_with_ism="wasl",
            ),
        ),
        (
            "ٱلِٱسْمُ ٱلْفُسُوقُ بَعْدَ ٱلْإِيمَـٰنِ وَمَن لَّمْ يَتُبْ فَأُو۟لَـٰٓئِكَ",
            "لِسْمُ ٱلْفُسُوقُ بَعْدَ ٱلْإِيمَـٰنِ وَمَن لَّمْ يَتُبْ فَأُو۟لَـٰٓئِكَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                start_with_ism="lism",
            ),
        ),
        (
            "ٱلِٱسْمُ ٱلْفُسُوقُ بَعْدَ ٱلْإِيمَـٰنِ وَمَن لَّمْ يَتُبْ فَأُو۟لَـٰٓئِكَ",
            "أَلِسْمُ ٱلْفُسُوقُ بَعْدَ ٱلْإِيمَـٰنِ وَمَن لَّمْ يَتُبْ فَأُو۟لَـٰٓئِكَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                start_with_ism="alism",
            ),
        ),
        (
            "مَّن ذَا ٱلَّذِى يُقْرِضُ ٱللَّهَ قَرْضًا حَسَنًۭا فَيُضَـٰعِفَهُۥ لَهُۥٓ أَضْعَافًۭا كَثِيرَةًۭ وَٱللَّهُ يَقْبِضُ وَيَبْصُۜطُ وَإِلَيْهِ تُرْجَعُونَ",
            "مَّن ذَا ٱلَّذِى يُقْرِضُ ٱللَّهَ قَرْضًا حَسَنًۭا فَيُضَـٰعِفَهُۥ لَهُۥٓ أَضْعَافًۭا كَثِيرَةًۭ وَٱللَّهُ يَقْبِضُ وَيَبْسُطُ وَإِلَيْهِ تُرْجَعُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yabsut="seen",
            ),
        ),
        (
            "مَّن ذَا ٱلَّذِى يُقْرِضُ ٱللَّهَ قَرْضًا حَسَنًۭا فَيُضَـٰعِفَهُۥ لَهُۥٓ أَضْعَافًۭا كَثِيرَةًۭ وَٱللَّهُ يَقْبِضُ وَيَبْصُۜطُ وَإِلَيْهِ تُرْجَعُونَ",
            "مَّن ذَا ٱلَّذِى يُقْرِضُ ٱللَّهَ قَرْضًا حَسَنًۭا فَيُضَـٰعِفَهُۥ لَهُۥٓ أَضْعَافًۭا كَثِيرَةًۭ وَٱللَّهُ يَقْبِضُ وَيَبْصُطُ وَإِلَيْهِ تُرْجَعُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yabsut="saad",
            ),
        ),
        (
            "أَوَعَجِبْتُمْ أَن جَآءَكُمْ ذِكْرٌۭ مِّن رَّبِّكُمْ عَلَىٰ رَجُلٍۢ مِّنكُمْ لِيُنذِرَكُمْ وَٱذْكُرُوٓا۟ إِذْ جَعَلَكُمْ خُلَفَآءَ مِنۢ بَعْدِ قَوْمِ نُوحٍۢ وَزَادَكُمْ فِى ٱلْخَلْقِ بَصْۜطَةًۭ فَٱذْكُرُوٓا۟ ءَالَآءَ ٱللَّهِ لَعَلَّكُمْ تُفْلِحُونَ",
            "أَوَعَجِبْتُمْ أَن جَآءَكُمْ ذِكْرٌۭ مِّن رَّبِّكُمْ عَلَىٰ رَجُلٍۢ مِّنكُمْ لِيُنذِرَكُمْ وَٱذْكُرُوٓا۟ إِذْ جَعَلَكُمْ خُلَفَآءَ مِنۢ بَعْدِ قَوْمِ نُوحٍۢ وَزَادَكُمْ فِى ٱلْخَلْقِ بَسْطَةًۭ فَٱذْكُرُوٓا۟ ءَالَآءَ ٱللَّهِ لَعَلَّكُمْ تُفْلِحُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                bastah="seen",
            ),
        ),
        (
            "أَوَعَجِبْتُمْ أَن جَآءَكُمْ ذِكْرٌۭ مِّن رَّبِّكُمْ عَلَىٰ رَجُلٍۢ مِّنكُمْ لِيُنذِرَكُمْ وَٱذْكُرُوٓا۟ إِذْ جَعَلَكُمْ خُلَفَآءَ مِنۢ بَعْدِ قَوْمِ نُوحٍۢ وَزَادَكُمْ فِى ٱلْخَلْقِ بَصْۜطَةًۭ فَٱذْكُرُوٓا۟ ءَالَآءَ ٱللَّهِ لَعَلَّكُمْ تُفْلِحُونَ",
            "أَوَعَجِبْتُمْ أَن جَآءَكُمْ ذِكْرٌۭ مِّن رَّبِّكُمْ عَلَىٰ رَجُلٍۢ مِّنكُمْ لِيُنذِرَكُمْ وَٱذْكُرُوٓا۟ إِذْ جَعَلَكُمْ خُلَفَآءَ مِنۢ بَعْدِ قَوْمِ نُوحٍۢ وَزَادَكُمْ فِى ٱلْخَلْقِ بَصْطَةًۭ فَٱذْكُرُوٓا۟ ءَالَآءَ ٱللَّهِ لَعَلَّكُمْ تُفْلِحُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                bastah="saad",
            ),
        ),
        (
            "أَمْ عِندَهُمْ خَزَآئِنُ رَبِّكَ أَمْ هُمُ ٱلْمُصَۣيْطِرُونَ",
            "أَمْ عِندَهُمْ خَزَآئِنُ رَبِّكَ أَمْ هُمُ ٱلْمُسَيْطِرُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                almusaytirun="seen",
            ),
        ),
        (
            "أَمْ عِندَهُمْ خَزَآئِنُ رَبِّكَ أَمْ هُمُ ٱلْمُصَۣيْطِرُونَ",
            "أَمْ عِندَهُمْ خَزَآئِنُ رَبِّكَ أَمْ هُمُ ٱلْمُصَيْطِرُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                almusaytirun="saad",
            ),
        ),
        (
            "لَّسْتَ عَلَيْهِم بِمُصَيْطِرٍ",
            "لَّسْتَ عَلَيْهِم بِمُسَيْطِرٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                bimusaytir="seen",
            ),
        ),
        (
            "لَّسْتَ عَلَيْهِم بِمُصَيْطِرٍ",
            "لَّسْتَ عَلَيْهِم بِمُصَيْطِرٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                bimusaytir="saad",
            ),
        ),
        (
            "يَـٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ لَا تُحِلُّوا۟ شَعَـٰٓئِرَ ٱللَّهِ وَلَا ٱلشَّهْرَ ٱلْحَرَامَ وَلَا ٱلْهَدْىَ وَلَا ٱلْقَلَـٰٓئِدَ وَلَآ ءَآمِّينَ ٱلْبَيْتَ ٱلْحَرَامَ يَبْتَغُونَ فَضْلًۭا مِّن رَّبِّهِمْ وَرِضْوَٰنًۭا وَإِذَا حَلَلْتُمْ فَٱصْطَادُوا۟ وَلَا يَجْرِمَنَّكُمْ شَنَـَٔانُ قَوْمٍ أَن صَدُّوكُمْ عَنِ ٱلْمَسْجِدِ ٱلْحَرَامِ أَن تَعْتَدُوا۟ وَتَعَاوَنُوا۟ عَلَى ٱلْبِرِّ وَٱلتَّقْوَىٰ وَلَا تَعَاوَنُوا۟ عَلَى ٱلْإِثْمِ وَٱلْعُدْوَٰنِ وَٱتَّقُوا۟ ٱللَّهَ إِنَّ ٱللَّهَ شَدِيدُ ٱلْعِقَابِ",
            "يَـٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ لَا تُحِلُّوا۟ شَعَـٰٓئِرَ ٱللَّهِ وَلَا ٱلشَّهْرَ ٱلْحَرَامَ وَلَا ٱلْهَدْىَ وَلَا ٱلْقَلَـٰٓئِدَ وَلَآ ءَآمِّينَ ٱلْبَيْتَ ٱلْحَرَامَ يَبْتَغُونَ فَضْلًۭا مِّن رَّبِّهِمْ وَرِضْوَٰنًۭا وَإِذَا حَلَلْتُمْ فَٱصْطَادُوا۟ وَلَا يَجْرِمَنَّكُمْ شَنَـَٔانُ قَوْمٍ أَن صَدُّوكُمْ عَنِ ٱلْمَسْجِدِ ٱلْحَرَامِ أَن تَعْتَدُوا۟ وَتَعَاوَنُوا۟ عَلَى ٱلْبِرِّ وَٱلتَّقْوَىٰ وَلَا تَعَاوَنُوا۟ عَلَى ٱلْإِثْمِ وَٱلْعُدْوَٰنِ وَٱتَّقُوا۟ ٱللَّهَ إِنَّ ٱللَّهَ شَدِيدُ ٱلْعِقَابِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "ثَمَـٰنِيَةَ أَزْوَٰجٍۢ مِّنَ ٱلضَّأْنِ ٱثْنَيْنِ وَمِنَ ٱلْمَعْزِ ٱثْنَيْنِ قُلْ ءَآلذَّكَرَيْنِ حَرَّمَ أَمِ ٱلْأُنثَيَيْنِ أَمَّا ٱشْتَمَلَتْ عَلَيْهِ أَرْحَامُ ٱلْأُنثَيَيْنِ نَبِّـُٔونِى بِعِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            "ثَمَـٰنِيَةَ أَزْوَٰجٍۢ مِّنَ ٱلضَّأْنِ ٱثْنَيْنِ وَمِنَ ٱلْمَعْزِ ٱثْنَيْنِ قُلْ ءَا۬لذَّكَرَيْنِ حَرَّمَ أَمِ ٱلْأُنثَيَيْنِ أَمَّا ٱشْتَمَلَتْ عَلَيْهِ أَرْحَامُ ٱلْأُنثَيَيْنِ نَبِّـُٔونِى بِعِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "ثَمَـٰنِيَةَ أَزْوَٰجٍۢ مِّنَ ٱلضَّأْنِ ٱثْنَيْنِ وَمِنَ ٱلْمَعْزِ ٱثْنَيْنِ قُلْ ءَآلذَّكَرَيْنِ حَرَّمَ أَمِ ٱلْأُنثَيَيْنِ أَمَّا ٱشْتَمَلَتْ عَلَيْهِ أَرْحَامُ ٱلْأُنثَيَيْنِ نَبِّـُٔونِى بِعِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            "ثَمَـٰنِيَةَ أَزْوَٰجٍۢ مِّنَ ٱلضَّأْنِ ٱثْنَيْنِ وَمِنَ ٱلْمَعْزِ ٱثْنَيْنِ قُلْ ءَآلذَّكَرَيْنِ حَرَّمَ أَمِ ٱلْأُنثَيَيْنِ أَمَّا ٱشْتَمَلَتْ عَلَيْهِ أَرْحَامُ ٱلْأُنثَيَيْنِ نَبِّـُٔونِى بِعِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="madd",
            ),
        ),
        (
            "قُلِ ٱلْحَمْدُ لِلَّهِ وَسَلَـٰمٌ عَلَىٰ عِبَادِهِ ٱلَّذِينَ ٱصْطَفَىٰٓ ءَآللَّهُ خَيْرٌ أَمَّا يُشْرِكُونَ",
            "قُلِ ٱلْحَمْدُ لِلَّهِ وَسَلَـٰمٌ عَلَىٰ عِبَادِهِ ٱلَّذِينَ ٱصْطَفَىٰٓ ءَا۬للَّهُ خَيْرٌ أَمَّا يُشْرِكُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "قُلِ ٱلْحَمْدُ لِلَّهِ وَسَلَـٰمٌ عَلَىٰ عِبَادِهِ ٱلَّذِينَ ٱصْطَفَىٰٓ ءَآللَّهُ خَيْرٌ أَمَّا يُشْرِكُونَ",
            "قُلِ ٱلْحَمْدُ لِلَّهِ وَسَلَـٰمٌ عَلَىٰ عِبَادِهِ ٱلَّذِينَ ٱصْطَفَىٰٓ ءَآللَّهُ خَيْرٌ أَمَّا يُشْرِكُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="madd",
            ),
        ),
        (
            "ءَآلْـَٔـٰنَ وَقَدْ عَصَيْتَ قَبْلُ وَكُنتَ مِنَ ٱلْمُفْسِدِينَ",
            "ءَا۬لْـَٔـٰنَ وَقَدْ عَصَيْتَ قَبْلُ وَكُنتَ مِنَ ٱلْمُفْسِدِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث ذَّٰلِكَ مَثَلُ ٱلْقَوْمِ ٱلَّذِينَ كَذَّبُوا۟ بِـَٔايَـٰتِنَا فَٱقْصُصِ ٱلْقَصَصَ لَعَلَّهُمْ يَتَفَكَّرُونَ",
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَثْ ذَٰلِكَ مَثَلُ ٱلْقَوْمِ ٱلَّذِينَ كَذَّبُوا۟ بِـَٔايَـٰتِنَا فَٱقْصُصِ ٱلْقَصَصَ لَعَلَّهُمْ يَتَفَكَّرُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yalhath_dhalik="izhar",
            ),
        ),
        (
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث",
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yalhath_dhalik="izhar",
            ),
        ),
        (
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث",
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yalhath_dhalik="waqf",
            ),
        ),
        (
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث ذَّٰلِكَ مَثَلُ ٱلْقَوْمِ ٱلَّذِينَ كَذَّبُوا۟ بِـَٔايَـٰتِنَا فَٱقْصُصِ ٱلْقَصَصَ لَعَلَّهُمْ يَتَفَكَّرُونَ",
            "وَلَوْ شِئْنَا لَرَفَعْنَـٰهُ بِهَا وَلَـٰكِنَّهُۥٓ أَخْلَدَ إِلَى ٱلْأَرْضِ وَٱتَّبَعَ هَوَىٰهُ فَمَثَلُهُۥ كَمَثَلِ ٱلْكَلْبِ إِن تَحْمِلْ عَلَيْهِ يَلْهَثْ أَوْ تَتْرُكْهُ يَلْهَث ذَّٰلِكَ مَثَلُ ٱلْقَوْمِ ٱلَّذِينَ كَذَّبُوا۟ بِـَٔايَـٰتِنَا فَٱقْصُصِ ٱلْقَصَصَ لَعَلَّهُمْ يَتَفَكَّرُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                yalhath_dhalik="idgham",
            ),
        ),
        (
            "وَهِىَ تَجْرِى بِهِمْ فِى مَوْجٍۢ كَٱلْجِبَالِ وَنَادَىٰ نُوحٌ ٱبْنَهُۥ وَكَانَ فِى مَعْزِلٍۢ يَـٰبُنَىَّ ٱرْكَب مَّعَنَا وَلَا تَكُن مَّعَ ٱلْكَـٰفِرِينَ",
            "وَهِىَ تَجْرِى بِهِمْ فِى مَوْجٍۢ كَٱلْجِبَالِ وَنَادَىٰ نُوحٌ ٱبْنَهُۥ وَكَانَ فِى مَعْزِلٍۢ يَـٰبُنَىَّ ٱرْكَبْ مَعَنَا وَلَا تَكُن مَّعَ ٱلْكَـٰفِرِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                irkab_maana="izhar",
            ),
        ),
        (
            "وَهِىَ تَجْرِى بِهِمْ فِى مَوْجٍۢ كَٱلْجِبَالِ وَنَادَىٰ نُوحٌ ٱبْنَهُۥ وَكَانَ فِى مَعْزِلٍۢ يَـٰبُنَىَّ ٱرْكَب مَّعَنَا وَلَا تَكُن مَّعَ ٱلْكَـٰفِرِينَ",
            "وَهِىَ تَجْرِى بِهِمْ فِى مَوْجٍۢ كَٱلْجِبَالِ وَنَادَىٰ نُوحٌ ٱبْنَهُۥ وَكَانَ فِى مَعْزِلٍۢ يَـٰبُنَىَّ ٱرْكَب مَّعَنَا وَلَا تَكُن مَّعَ ٱلْكَـٰفِرِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                irkab_maana="idgham",
            ),
        ),
        (
            "قَالُوا۟ يَـٰٓأَبَانَا مَا لَكَ لَا تَأْمَ۫نَّا عَلَىٰ يُوسُفَ وَإِنَّا لَهُۥ لَنَـٰصِحُونَ",
            "قَالُوا۟ يَـٰٓأَبَانَا مَا لَكَ لَا تَأْمَنَّا عَلَىٰ يُوسُفَ وَإِنَّا لَهُۥ لَنَـٰصِحُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_tamnna="ishmam",
            ),
        ),
        (
            "قَالُوا۟ يَـٰٓأَبَانَا مَا لَكَ لَا تَأْمَ۫نَّا عَلَىٰ يُوسُفَ وَإِنَّا لَهُۥ لَنَـٰصِحُونَ",
            "قَالُوا۟ يَـٰٓأَبَانَا مَا لَكَ لَا تَأْمَنؙنَا عَلَىٰ يُوسُفَ وَإِنَّا لَهُۥ لَنَـٰصِحُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                noon_tamnna="rawm",
            ),
        ),
        (
            "ٱلْـَٔـٰنَ خَفَّفَ ٱللَّهُ عَنكُمْ وَعَلِمَ أَنَّ فِيكُمْ ضَعْفًۭا فَإِن يَكُن مِّنكُم مِّا۟ئَةٌۭ صَابِرَةٌۭ يَغْلِبُوا۟ مِا۟ئَتَيْنِ وَإِن يَكُن مِّنكُمْ أَلْفٌۭ يَغْلِبُوٓا۟ أَلْفَيْنِ بِإِذْنِ ٱللَّهِ وَٱللَّهُ مَعَ ٱلصَّـٰبِرِينَ",
            "ٱلْـَٔـٰنَ خَفَّفَ ٱللَّهُ عَنكُمْ وَعَلِمَ أَنَّ فِيكُمْ ضَعْفًۭا فَإِن يَكُن مِّنكُم مِّا۟ئَةٌۭ صَابِرَةٌۭ يَغْلِبُوا۟ مِا۟ئَتَيْنِ وَإِن يَكُن مِّنكُمْ أَلْفٌۭ يَغْلِبُوٓا۟ أَلْفَيْنِ بِإِذْنِ ٱللَّهِ وَٱللَّهُ مَعَ ٱلصَّـٰبِرِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                harakat_daaf="dam",
            ),
        ),
        (
            "ٱللَّهُ ٱلَّذِى خَلَقَكُم مِّن ضَعْفٍۢ ثُمَّ جَعَلَ مِنۢ بَعْدِ ضَعْفٍۢ قُوَّةًۭ ثُمَّ جَعَلَ مِنۢ بَعْدِ قُوَّةٍۢ ضَعْفًۭا وَشَيْبَةًۭ يَخْلُقُ مَا يَشَآءُ وَهُوَ ٱلْعَلِيمُ ٱلْقَدِيرُ",
            "ٱللَّهُ ٱلَّذِى خَلَقَكُم مِّن ضُعْفٍۢ ثُمَّ جَعَلَ مِنۢ بَعْدِ ضُعْفٍۢ قُوَّةًۭ ثُمَّ جَعَلَ مِنۢ بَعْدِ قُوَّةٍۢ ضُعْفًۭا وَشَيْبَةًۭ يَخْلُقُ مَا يَشَآءُ وَهُوَ ٱلْعَلِيمُ ٱلْقَدِيرُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                harakat_daaf="dam",
            ),
        ),
        (
            "ٱللَّهُ ٱلَّذِى خَلَقَكُم مِّن ضَعْفٍۢ ثُمَّ جَعَلَ مِنۢ بَعْدِ ضَعْفٍۢ قُوَّةًۭ ثُمَّ جَعَلَ مِنۢ بَعْدِ قُوَّةٍۢ ضَعْفًۭا وَشَيْبَةًۭ يَخْلُقُ مَا يَشَآءُ وَهُوَ ٱلْعَلِيمُ ٱلْقَدِيرُ",
            "ٱللَّهُ ٱلَّذِى خَلَقَكُم مِّن ضَعْفٍۢ ثُمَّ جَعَلَ مِنۢ بَعْدِ ضَعْفٍۢ قُوَّةًۭ ثُمَّ جَعَلَ مِنۢ بَعْدِ قُوَّةٍۢ ضَعْفًۭا وَشَيْبَةًۭ يَخْلُقُ مَا يَشَآءُ وَهُوَ ٱلْعَلِيمُ ٱلْقَدِيرُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                harakat_daaf="fath",
            ),
        ),
        (
            "إِنَّآ أَعْتَدْنَا لِلْكَـٰفِرِينَ سَلَـٰسِلَا۟ وَأَغْلَـٰلًۭا وَسَعِيرًا",
            "إِنَّآ أَعْتَدْنَا لِلْكَـٰفِرِينَ سَلَـٰسِلَا۟ وَأَغْلَـٰلًۭا وَسَعِيرًا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                alif_salasila="ithbat",
            ),
        ),
        (
            "إِنَّآ أَعْتَدْنَا لِلْكَـٰفِرِينَ سَلَـٰسِلَا۟",
            "إِنَّآ أَعْتَدْنَا لِلْكَـٰفِرِينَ سَلَـٰسِلَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                alif_salasila="ithbat",
            ),
        ),
        (
            "إِنَّآ أَعْتَدْنَا لِلْكَـٰفِرِينَ سَلَـٰسِلَا۟",
            "إِنَّآ أَعْتَدْنَا لِلْكَـٰفِرِينَ سَلَـٰسِلَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                alif_salasila="hadhf",
            ),
        ),
        (
            "أَلَمْ نَخْلُقكُّم مِّن مَّآءٍۢ مَّهِينٍۢ",
            "أَلَمْ نَخْلُقكُّم مِّن مَّآءٍۢ مَّهِينٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                idgham_nakhluqkum="idgham_kamil",
            ),
        ),
        (
            "أَلَمْ نَخْلُقكُّم مِّن مَّآءٍۢ مَّهِينٍۢ",
            "أَلَمْ نَخْلُقكُم مِّن مَّآءٍۢ مَّهِينٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                idgham_nakhluqkum="idgham_naqis",
            ),
        ),
        (
            "وَإِن كَانَ أَصْحَـٰبُ ٱلْأَيْكَةِ لَظَـٰلِمِينَ",
            "وَإِن كَانَ أَصْحَـٰبُ ٱلْأَيْكَةِ لَظَـٰلِمِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "كَذَّبَ أَصْحَـٰبُ لْـَٔيْكَةِ ٱلْمُرْسَلِينَ",
            "كَذَّبَ أَصْحَـٰبُ لْـَٔيْكَةِ ٱلْمُرْسَلِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "لْـَٔيْكَةِ ٱلْمُرْسَلِينَ",
            "ٱلْأَيْكَةِ ٱلْمُرْسَلِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_special_cases(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = SpecialCases()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None)
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(out_text)
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ٱللَّهُ ٱلَّذِى خَلَقَكُم مِّن ضَعْفٍۢ ثُمَّ جَعَلَ مِنۢ بَعْدِ ضَعْفٍۢ قُوَّةًۭ ثُمَّ جَعَلَ مِنۢ بَعْدِ قُوَّةٍۢ ضَعْفًۭا وَشَيْبَةًۭ يَخْلُقُ مَا يَشَآءُ وَهُوَ ٱلْعَلِيمُ ٱلْقَدِيرُ",
            "ٱللَّاهُ ٱلَّذِى خَلَقَكُم مِّن ضَعْفٍۢ ثُمَّ جَعَلَ مِنۢ بَعْدِ ضَعْفٍۢ قُوَّةًۭ ثُمَّ جَعَلَ مِنۢ بَعْدِ قُوَّةٍۢ ضَعْفًۭا وَشَيْبَةًۭ يَخْلُقُ مَا يَشَآءُ وَهُوَ ٱلْعَلِيمُ ٱلْقَدِيرُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قُلِ ٱللَّهُمَّ مَـٰلِكَ ٱلْمُلْكِ تُؤْتِى ٱلْمُلْكَ مَن تَشَآءُ وَتَنزِعُ ٱلْمُلْكَ مِمَّن تَشَآءُ وَتُعِزُّ مَن تَشَآءُ وَتُذِلُّ مَن تَشَآءُ بِيَدِكَ ٱلْخَيْرُ إِنَّكَ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌۭ",
            "قُلِ ٱللَّاهُمَّ مَـٰلِكَ ٱلْمُلْكِ تُؤْتِى ٱلْمُلْكَ مَن تَشَآءُ وَتَنزِعُ ٱلْمُلْكَ مِمَّن تَشَآءُ وَتُعِزُّ مَن تَشَآءُ وَتُذِلُّ مَن تَشَآءُ بِيَدِكَ ٱلْخَيْرُ إِنَّكَ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قُلِ ٱلْحَمْدُ لِلَّهِ وَسَلَـٰمٌ عَلَىٰ عِبَادِهِ ٱلَّذِينَ ٱصْطَفَىٰٓ ءَآللَّهُ خَيْرٌ أَمَّا يُشْرِكُونَ",
            "قُلِ ٱلْحَمْدُ لِلَّاهِ وَسَلَـٰمٌ عَلَىٰ عِبَادِهِ ٱلَّذِينَ ٱصْطَفَىٰٓ ءَآللَّاهُ خَيْرٌ أَمَّا يُشْرِكُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "لَّا ظَلِيلٍۢ وَلَا يُغْنِى مِنَ ٱللَّهَبِ",
            "لَّا ظَلِيلٍۢ وَلَا يُغْنِى مِنَ ٱللَّهَبِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَإِذَا رَأَوْا۟ تِجَـٰرَةً أَوْ لَهْوًا ٱنفَضُّوٓا۟ إِلَيْهَا وَتَرَكُوكَ قَآئِمًۭا قُلْ مَا عِندَ ٱللَّهِ خَيْرٌۭ مِّنَ ٱللَّهْوِ وَمِنَ ٱلتِّجَـٰرَةِ وَٱللَّهُ خَيْرُ ٱلرَّٰزِقِينَ",
            "وَإِذَا رَأَوْا۟ تِجَـٰرَةً أَوْ لَهْوًا ٱنفَضُّوٓا۟ إِلَيْهَا وَتَرَكُوكَ قَآئِمًۭا قُلْ مَا عِندَ ٱللَّاهِ خَيْرٌۭ مِّنَ ٱللَّهْوِ وَمِنَ ٱلتِّجَـٰرَةِ وَٱللَّاهُ خَيْرُ ٱلرَّٰزِقِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَسَيَكْفِيكَهُمُ ٱللَّهُ",
            "فَسَيَكْفِيكَهُمُ ٱللَّاهُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_alif_ism_Allah(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = AddAlifIsmAllah()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(
            target_text,
            moshaf,
            None,
            mode="test",
        )
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "وَإِذْ وَٰعَدْنَا مُوسَىٰٓ أَرْبَعِينَ لَيْلَةًۭ ثُمَّ ٱتَّخَذْتُمُ ٱلْعِجْلَ مِنۢ بَعْدِهِۦ وَأَنتُمْ ظَـٰلِمُونَ",
            "وَإِذْ وَٰعَدْنَا مُوسَىٰٓ أَرْبَعِينَ لَيْلَتَن ثُمَّ ٱتَّخَذْتُمُ ٱلْعِجْلَ مِم بَعْدِهِۦ وَأَنتُمْ ظَـٰلِمُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قَالَ يَـٰٓـَٔادَمُ أَنۢبِئْهُم بِأَسْمَآئِهِمْ فَلَمَّآ أَنۢبَأَهُم بِأَسْمَآئِهِمْ قَالَ أَلَمْ أَقُل لَّكُمْ إِنِّىٓ أَعْلَمُ غَيْبَ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَأَعْلَمُ مَا تُبْدُونَ وَمَا كُنتُمْ تَكْتُمُونَ",
            "قَالَ يَـٰٓـَٔادَمُ أَمبِئْهُم بِأَسْمَآئِهِمْ فَلَمَّآ أَمبَأَهُم بِأَسْمَآئِهِمْ قَالَ أَلَمْ أَقُلَّكُمْ إِنِّىٓ أَعْلَمُ غَيْبَ سَّمَـٰوَٰتِ وَٱلْأَرْضِ وَأَعْلَمُ مَا تُبْدُونَ وَمَا كُنتُمْ تَكْتُمُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ذَٰلِكَ بِأَنَّ ٱللَّهَ يُولِجُ ٱلَّيْلَ فِى ٱلنَّهَارِ وَيُولِجُ ٱلنَّهَارَ فِى ٱلَّيْلِ وَأَنَّ ٱللَّهَ سَمِيعٌۢ بَصِيرٌۭ",
            "ذَٰلِكَ بِأَنَّ لَّاهَ يُولِجُ لَّيْلَ فِى نَّهَارِ وَيُولِجُ نَّهَارَ فِى لَّيْلِ وَأَنَّ لَّاهَ سَمِيعُم بَصِيرٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَٱلسَّارِقُ وَٱلسَّارِقَةُ فَٱقْطَعُوٓا۟ أَيْدِيَهُمَا جَزَآءًۢ بِمَا كَسَبَا نَكَـٰلًۭا مِّنَ ٱللَّهِ وَٱللَّهُ عَزِيزٌ حَكِيمٌۭ",
            "وَسَّارِقُ وَسَّارِقَةُ فَقْطَعُوٓا۟ أَيْدِيَهُمَا جَزَآءَم بِمَا كَسَبَا نَكَـٰلَمِّنَ لَّاهِ وَلَّاهُ عَزِيزُنْ حَكِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "أَوَلَمْ يَرَوْا۟ إِلَى ٱلطَّيْرِ فَوْقَهُمْ صَـٰٓفَّـٰتٍۢ وَيَقْبِضْنَ مَا يُمْسِكُهُنَّ إِلَّا ٱلرَّحْمَـٰنُ إِنَّهُۥ بِكُلِّ شَىْءٍۭ بَصِيرٌ",
            "أَوَلَمْ يَرَوْا۟ إِلَى طَّيْرِ فَوْقَهُمْ صَـٰٓفَّـٰتِن وَيَقْبِضْنَ مَا يُمْسِكُهُنَّ إِلَّا رَّحْمَـٰنُ إِنَّهُۥ بِكُلِّ شَىْءِم بَصِيرٌ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "يَمْحَقُ ٱللَّهُ ٱلرِّبَوٰا۟ وَيُرْبِى ٱلصَّدَقَـٰتِ وَٱللَّهُ لَا يُحِبُّ كُلَّ كَفَّارٍ أَثِيمٍ",
            "يَمْحَقُ لَّاهُ رِّبَوٰا۟ وَيُرْبِى صَّدَقَـٰتِ وَلَّاهُ لَا يُحِبُّ كُلَّ كَفَّارِنْ أَثِيمٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَيَقُولُ ٱلَّذِينَ كَفَرُوا۟ لَوْلَآ أُنزِلَ عَلَيْهِ ءَايَةٌۭ مِّن رَّبِّهِۦٓ إِنَّمَآ أَنتَ مُنذِرٌۭ وَلِكُلِّ قَوْمٍ هَادٍ",
            "وَيَقُولُ لَّذِينَ كَفَرُوا۟ لَوْلَآ أُنزِلَ عَلَيْهِ ءَايَتُمِّرَّبِّهِۦٓ إِنَّمَآ أَنتَ مُنذِرُن وَلِكُلِّ قَوْمِنْ هَادٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَإِنْ عَزَمُوا۟ ٱلطَّلَـٰقَ فَإِنَّ ٱللَّهَ سَمِيعٌ عَلِيمٌۭ",
            "وَإِنْ عَزَمُوا۟ طَّلَـٰقَ فَإِنَّ لَّاهَ سَمِيعُنْ عَلِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَأَلَّوِ ٱسْتَقَـٰمُوا۟ عَلَى ٱلطَّرِيقَةِ لَأَسْقَيْنَـٰهُم مَّآءً غَدَقًۭا",
            "وَأَلَّوِ ٱسْتَقَـٰمُوا۟ عَلَى طَّرِيقَةِ لَأَسْقَيْنَـٰهُمَّآءَنْ غَدَقًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قَالُوا۟ تِلْكَ إِذًۭا كَرَّةٌ خَاسِرَةٌۭ",
            "قَالُوا۟ تِلْكَ إِذَن كَرَّتُنْ خَاسِرَةٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًۭا يَرَهُۥ",
            "فَمَن يَعْمَلْ مِثْقَالَ ذَرَّتِنْ خَيْرَن يَرَهُۥ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱللَّهُ خَـٰلِقُ كُلِّ شَىْءٍۢ وَهُوَ عَلَىٰ كُلِّ شَىْءٍۢ وَكِيلٌۭ",
            "ٱلَّاهُ خَـٰلِقُ كُلِّ شَىْءِن وَهُوَ عَلَىٰ كُلِّ شَىْءِن وَكِيلٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قَوْلٌۭ مَّعْرُوفٌۭ وَمَغْفِرَةٌ خَيْرٌۭ مِّن صَدَقَةٍۢ يَتْبَعُهَآ أَذًۭى وَٱللَّهُ غَنِىٌّ حَلِيمٌۭ",
            "قَوْلُمَّعْرُوفُن وَمَغْفِرَتُنْ خَيْرُمِّن صَدَقَتِن يَتْبَعُهَآ أَذَن وَٱلَّاهُ غَنِيُّنْ حَلِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَتَوَلَّ عَنْهُمْ يَوْمَ يَدْعُ ٱلدَّاعِ إِلَىٰ شَىْءٍۢ نُّكُرٍ",
            "فَتَوَلَّ عَنْهُمْ يَوْمَ يَدْعُ ٱدَّاعِ إِلَىٰ شَيْءِنُّكُرٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "إِنَّا مُرْسِلُوا۟ ٱلنَّاقَةِ فِتْنَةًۭ لَّهُمْ فَٱرْتَقِبْهُمْ وَٱصْطَبِرْ",
            "إِنَّا مُرْسِلُوا۟ ٱنَّاقَةِ فِتْنَتَلَّهُمْ فَٱرْتَقِبْهُمْ وَٱصْطَبِرْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَإِنِ ٱنتَهَوْا۟ فَإِنَّ ٱللَّهَ غَفُورٌۭ رَّحِيمٌۭ",
            "فَإِنِ ٱنتَهَوْا۟ فَإِنَّ ٱلَّاهَ غَفُورُرَّحِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَأَمَّا عَادٌۭ فَأُهْلِكُوا۟ بِرِيحٍۢ صَرْصَرٍ عَاتِيَةٍۢ",
            "وَأَمَّا عَادُن فَأُهْلِكُوا۟ بِرِيحِن صَرْصَرِنْ عَاتِيَةٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَلَا تَحْسَبَنَّ ٱللَّهَ مُخْلِفَ وَعْدِهِۦ رُسُلَهُۥٓ إِنَّ ٱللَّهَ عَزِيزٌۭ ذُو ٱنتِقَامٍۢ",
            "فَلَا تَحْسَبَنَّ ٱلَّاهَ مُخْلِفَ وَعْدِهِۦ رُسُلَهُۥٓ إِنَّ ٱلَّاهَ عَزِيزُن ذُو ٱنتِقَامٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَأَنزَلْنَا مِنَ ٱلْمُعْصِرَٰتِ مَآءًۭ ثَجَّاجًۭا",
            "وَأَنزَلْنَا مِنَ ٱلْمُعْصِرَٰتِ مَآءَن ثَجَّاجًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "كِرَامًۭا كَـٰتِبِينَ",
            "كِرَامَن كَـٰتِبِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فِيهَا عَيْنٌۭ جَارِيَةٌۭ",
            "فِيهَا عَيْنُن جَارِيَةٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلَّذِى لَهُۥ مُلْكُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَٱللَّهُ عَلَىٰ كُلِّ شَىْءٍۢ شَهِيدٌ",
            "ٱلَّذِى لَهُۥ مُلْكُ ٱسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَٱلَّاهُ عَلَىٰ كُلِّ شَيْءِن شَهِيدٌ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "تَبَـٰرَكَ ٱلَّذِى بِيَدِهِ ٱلْمُلْكُ وَهُوَ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌ",
            "تَبَـٰرَكَ ٱلَّذِى بِيَدِهِ ٱلْمُلْكُ وَهُوَ عَلَىٰ كُلِّ شَيْءِن قَدِيرٌ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "سَيَقُولُونَ ثَلَـٰثَةٌۭ رَّابِعُهُمْ كَلْبُهُمْ وَيَقُولُونَ خَمْسَةٌۭ سَادِسُهُمْ كَلْبُهُمْ رَجْمًۢا بِٱلْغَيْبِ وَيَقُولُونَ سَبْعَةٌۭ وَثَامِنُهُمْ كَلْبُهُمْ قُل رَّبِّىٓ أَعْلَمُ بِعِدَّتِهِم مَّا يَعْلَمُهُمْ إِلَّا قَلِيلٌۭ فَلَا تُمَارِ فِيهِمْ إِلَّا مِرَآءًۭ ظَـٰهِرًۭا وَلَا تَسْتَفْتِ فِيهِم مِّنْهُمْ أَحَدًۭا",
            "سَيَقُولُونَ ثَلَـٰثَتُرَّابِعُهُمْ كَلْبُهُمْ وَيَقُولُونَ خَمْسَتُن سَادِسُهُمْ كَلْبُهُمْ رَجْمَم بِٱلْغَيْبِ وَيَقُولُونَ سَبْعَتُن وَثَامِنُهُمْ كَلْبُهُمْ قُرَّبِّىٓ أَعْلَمُ بِعِدَّتِهِمَّا يَعْلَمُهُمْ إِلَّا قَلِيلُن فَلَا تُمَارِ فِيهِمْ إِلَّا مِرَآءَن ظَـٰهِرَن وَلَا تَسْتَفْتِ فِيهِمِّنْهُمْ أَحَدًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَكَأْسًۭا دِهَاقًۭا",
            "وَكَأْسَن دِهَاقًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "أَلَمْ تَرَ كَيْفَ ضَرَبَ ٱللَّهُ مَثَلًۭا كَلِمَةًۭ طَيِّبَةًۭ كَشَجَرَةٍۢ طَيِّبَةٍ أَصْلُهَا ثَابِتٌۭ وَفَرْعُهَا فِى ٱلسَّمَآءِ",
            "أَلَمْ تَرَ كَيْفَ ضَرَبَ ٱلَّاهُ مَثَلَن كَلِمَتَن طَيِّبَتَن كَشَجَرَتِن طَيِّبَتِنْ أَصْلُهَا ثَابِتُن وَفَرْعُهَا فِى ٱسَّمَآءِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فَٱنطَلَقَا حَتَّىٰٓ إِذَا لَقِيَا غُلَـٰمًۭا فَقَتَلَهُۥ قَالَ أَقَتَلْتَ نَفْسًۭا زَكِيَّةًۢ بِغَيْرِ نَفْسٍۢ لَّقَدْ جِئْتَ شَيْـًۭٔا نُّكْرًۭا",
            "فَٱنطَلَقَا حَتَّىٰٓ إِذَا لَقِيَا غُلَـٰمَن فَقَتَلَهُۥ قَالَ أَقَتَلْتَ نَفْسَن زَكِيَّتَم بِغَيْرِ نَفْسِلَّقَدْ جِئْتَ شَيْءَنُّكْرًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَهُوَ ٱلَّذِى سَخَّرَ ٱلْبَحْرَ لِتَأْكُلُوا۟ مِنْهُ لَحْمًۭا طَرِيًّۭا وَتَسْتَخْرِجُوا۟ مِنْهُ حِلْيَةًۭ تَلْبَسُونَهَا وَتَرَى ٱلْفُلْكَ مَوَاخِرَ فِيهِ وَلِتَبْتَغُوا۟ مِن فَضْلِهِۦ وَلَعَلَّكُمْ تَشْكُرُونَ",
            "وَهُوَ ٱلَّذِى سَخَّرَ ٱلْبَحْرَ لِتَأْكُلُوا۟ مِنْهُ لَحْمَن طَرِيَّن وَتَسْتَخْرِجُوا۟ مِنْهُ حِلْيَتَن تَلْبَسُونَهَا وَتَرَى ٱلْفُلْكَ مَوَاخِرَ فِيهِ وَلِتَبْتَغُوا۟ مِن فَضْلِهِۦ وَلَعَلَّكُمْ تَشْكُرُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "تِلْكَ إِذًۭا قِسْمَةٌۭ ضِيزَىٰٓ",
            "تِلْكَ إِذَن قِسْمَتُن ضِيزَىٰٓ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_Prepare_ghonna_tanween_idgham(
    in_text: str, target_text: str, moshaf: MoshafAttributes
):
    op = PrepareGhonnaIdghamIqlab()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None, mode="test")
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        # alif
        (
            "وَلَقَدْ ءَاتَيْنَا دَاوُۥدَ وَسُلَيْمَـٰنَ عِلْمًۭا وَقَالَا ٱلْحَمْدُ لِلَّهِ ٱلَّذِى فَضَّلَنَا عَلَىٰ كَثِيرٍۢ مِّنْ عِبَادِهِ ٱلْمُؤْمِنِينَ",
            "وَلَقَدْ ءَاتَيْنَا دَاوُۥدَ وَسُلَيْمَـٰنَ عِلْمًۭا وَقَالَ ٱلْحَمْدُ لِلَّهِ ٱلَّذِى فَضَّلَنَا عَلَىٰ كَثِيرٍۢ مِّنْ عِبَادِهِ ٱلْمُؤْمِنِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # waw
        (
            "وَإِذْ قَالُوا۟ ٱللَّهُمَّ إِن كَانَ هَـٰذَا هُوَ ٱلْحَقَّ مِنْ عِندِكَ فَأَمْطِرْ عَلَيْنَا حِجَارَةًۭ مِّنَ ٱلسَّمَآءِ أَوِ ٱئْتِنَا بِعَذَابٍ أَلِيمٍۢ",
            "وَإِذْ قَالُا۟ ٱللَّهُمَّ إِن كَانَ هَـٰذَا هُوَ ٱلْحَقَّ مِنْ عِندِكَ فَأَمْطِرْ عَلَيْنَا حِجَارَةًۭ مِّنَ ٱلسَّمَآءِ أَوِ ٱئْتِنَا بِعَذَابٍ أَلِيمٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # yaa
        (
            "قَالَتْ رُسُلُهُمْ أَفِى ٱللَّهِ شَكٌّۭ فَاطِرِ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ يَدْعُوكُمْ لِيَغْفِرَ لَكُم مِّن ذُنُوبِكُمْ وَيُؤَخِّرَكُمْ إِلَىٰٓ أَجَلٍۢ مُّسَمًّۭى قَالُوٓا۟ إِنْ أَنتُمْ إِلَّا بَشَرٌۭ مِّثْلُنَا تُرِيدُونَ أَن تَصُدُّونَا عَمَّا كَانَ يَعْبُدُ ءَابَآؤُنَا فَأْتُونَا بِسُلْطَـٰنٍۢ مُّبِينٍۢ",
            "قَالَتْ رُسُلُهُمْ أَفِ ٱللَّهِ شَكٌّۭ فَاطِرِ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ يَدْعُوكُمْ لِيَغْفِرَ لَكُم مِّن ذُنُوبِكُمْ وَيُؤَخِّرَكُمْ إِلَىٰٓ أَجَلٍۢ مُّسَمًّۭى قَالُوٓا۟ إِنْ أَنتُمْ إِلَّا بَشَرٌۭ مِّثْلُنَا تُرِيدُونَ أَن تَصُدُّونَا عَمَّا كَانَ يَعْبُدُ ءَابَآؤُنَا فَأْتُونَا بِسُلْطَـٰنٍۢ مُّبِينٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # tanween dam
        (
            "وَهِىَ تَجْرِى بِهِمْ فِى مَوْجٍۢ كَٱلْجِبَالِ وَنَادَىٰ نُوحٌ ٱبْنَهُۥ وَكَانَ فِى مَعْزِلٍۢ يَـٰبُنَىَّ ٱرْكَب مَّعَنَا وَلَا تَكُن مَّعَ ٱلْكَـٰفِرِينَ",
            "وَهِىَ تَجْرِى بِهِمْ فِى مَوْجٍۢ كَٱلْجِبَالِ وَنَادَىٰ نُوحُنِ ٱبْنَهُۥ وَكَانَ فِى مَعْزِلٍۢ يَـٰبُنَىَّ ٱرْكَب مَّعَنَا وَلَا تَكُن مَّعَ ٱلْكَـٰفِرِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # tanween fath
        (
            "إِذْ نَادَىٰهُ رَبُّهُۥ بِٱلْوَادِ ٱلْمُقَدَّسِ طُوًى ٱذْهَبْ إِلَىٰ فِرْعَوْنَ إِنَّهُۥ طَغَىٰ",
            "إِذْ نَادَىٰهُ رَبُّهُۥ بِٱلْوَادِ ٱلْمُقَدَّسِ طُوَنِ ٱذْهَبْ إِلَىٰ فِرْعَوْنَ إِنَّهُۥ طَغَىٰ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_iltiqaa_alsaknana(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = IltiqaaAlsaknan()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None, mode="test")
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        # إدغم النون في الياء
        (
            "فَمَن يَعْمَلْ",
            "فَمَيييَعْمَلْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "خَيْرًۭا يَرَهُۥ",
            "خَيْرَيييَرَهُۥ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مِن وَلِىٍّۢ وَلَا نَصِيرٍ",
            "مِوووَلِيِّوووَلَا نَصِيرٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # إخفاء النون
        (
            "مِنكُمْ",
            "مِںںںكُمْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مِن قَبْلِكَ",
            "مِںںںقَبْلِكَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "خَمْسَةٌۭ سَادِسُهُمْ",
            "خَمْسَتُںںںسَادِسُهُمْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # الميم المخفاة
        (
            "مِنۢ بَعْدِ",
            "مِ۾۾۾بَعْدِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "أَنۢبِئْهُم",
            "أَ۾۾۾بِئْهُم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "سَمِيعٌۢ بَصِيرٌ",
            "سَمِيعُ۾۾۾بَصِيرٌ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "تَرْمِيهِم بِحِجَارَةٍۢ",
            "تَرْمِيهِ۾۾۾بِحِجَارَةٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "تَرْمِيهِم بِحِجَارَةٍۢ",
            "تَرْمِيهِمممبِحِجَارَةٍۢ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                meem_mokhfah="meem",
            ),
        ),
        (
            "سَمِيعٌۢ بَصِيرٌ",
            "سَمِيعُمممبَصِيرٌ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                meem_mokhfah="meem",
            ),
        ),
        # النون المشددة
        (
            "إِنَّمَا",
            "إِننننَمَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَلَن نُّشْرِكَ",
            "وَلَننننُشْرِكَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ",
            "مِنَ لْجِننننَةِ وَننننَاسِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَلَٰكِنَّ ٱلْبِرَّ",
            "وَلَٰكِننننَ لْبِرَّ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "حَمَّالَةَ ٱلْحَطَبِ",
            "حَممممَالَةَ ٱلْحَطَبِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "",
            "",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلْيَمِّ وَلَا تَخَافِى",
            "ٱلْيَممممِ وَلَا تَخَافِى",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "لَكُم مَّا",
            "لَكُممممَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مِن مَّالٍ",
            "مِممممَالٍ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "خَيْرٌۭ مِّن",
            "خَيْرُممممِن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مِّنْ خَوْفٍۭ",
            "مِّنْ خَوْفٍۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_ghonna(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = Ghonna()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None, mode="test")
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        # إدغم النون في الياء
        (
            "ءَا۬عْجَمِىٌّۭ",
            "ءَٲعْجَمِىٌّۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ءَآلذَّكَرَيْنِ",
            "ءَٲلذَّكَرَيْنِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
    ],
)
def test_tasheel(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = Tasheel()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None, mode="test")
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        # إدغم النون في الياء
        (
            "مَجْر۪ىٰهَا",
            "مَجْر۪ــهَا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_imala(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = Imala()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(target_text, moshaf, None, mode="test")
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        # المد المنفصل
        (
            "يَـٰٓأَيُّهَا ٱلَّذِينَ",
            "يَااااءَيُّهَا لَّذِۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
            ),
        ),
        (
            "يَـٰٓأَيُّهَا ٱلَّذِينَ",
            "يَااءَيُّهَا لَّذِۦۦۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=6,
            ),
        ),
        (
            "أَهَـٰٓؤُلَآءِ",
            "أَهَااؤُلَاااااء",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=5,
                madd_aared_len=4,
            ),
        ),
        (
            "بِمَآ أُنزِلَ",
            "بِمَااااا أُنزِلَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=5,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قَالُوٓا۟ ءَامَنَّا",
            "قَاالُۥۥۥۥ ءَاامَنَّاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=5,
                madd_mottasel_waqf=5,
                madd_aared_len=4,
            ),
        ),
        (
            "وَفِىٓ أَنفُسِكُمْ",
            "وَفِۦۦ أَنفُسِكُمْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مَالَهُۥٓ أَخْلَدَهُۥ",
            "مَاالَهُۥۥۥۥۥ أَخْلَدَه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=5,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "طَعَامِهِۦٓ أَنَّا",
            "طَعَاامِهِۦۦۦۦ أَنَّاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=5,
                madd_mottasel_waqf=5,
                madd_aared_len=6,
            ),
        ),
        (
            "أَوْ كَصَيِّبٍۢ مِّنَ ٱلسَّمَآءِ",
            "أَوْ كَصَيِّبِممممِنَ سَّمَااااااء",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=6,
            ),
        ),
        # المد المتصل
        (
            "وَٱلسَّمَآءَ بِنَآءًۭ وَأَنزَلَ مِنَ ٱلسَّمَآءِ مَآءًۭ",
            "وَسَّمَااااءَ بِنَااااءَوووَأَںںںزَلَ مِنَ سَّمَااااءِ مَااااءَاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=5,
                madd_aared_len=4,
            ),
        ),
        (
            "سُوٓءَ ٱلْعَذَابِ",
            "سُۥۥۥۥۥءَ لْعَذَااااب",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=5,
                madd_mottasel_waqf=5,
                madd_aared_len=4,
            ),
        ),
        (
            "سِىٓءَ بِهِمْ",
            "سِۦۦۦۦۦۦءَ بِهِمْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=6,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # combined متصل ومنفصل
        (
            "أَسَـٰٓـُٔوا۟ ٱلسُّوٓأَىٰٓ أَن",
            "أَسَااااءُ سُّۥۥۥۥءَاا أَن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        # المد اللازم
        (
            "ءَآلْـَٔـٰنَ وَقَدْ عَصَيْتَ",
            "ءَاااااالْءَاانَ وَقَدْ عَصَيييت",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلصَّآخَّةُ",
            "ٱصَّااااااخَّةُ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "أَتُحَـٰٓجُّوٓنِّى",
            "أَتُحَااااااجُّۥۥۥۥۥۥننننِۦۦ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "جَآنٌّۭ",
            "جَااااااننن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "كٓهيعٓصٓ",
            "كَاااااافْ هَاا يَاا عَيںںںصَاااااادْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                madd_yaa_alayn_alharfy=2,
            ),
        ),
        (
            "عٓسٓقٓ",
            "عَيييييںںںسِۦۦۦۦۦۦںںںقَاااااافْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                madd_yaa_alayn_alharfy=6,
            ),
        ),
        (
            "الٓمٓ",
            "ءَلِفْ لَااااااممممِۦۦۦۦۦۦمْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "الٓمٓ ٱللَّهُ",
            "ءَلِفْ لَااااااممممِۦۦۦۦۦۦمَ لَّااااه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                meem_aal_imran="wasl_6",
            ),
        ),
        (
            "الٓمٓ ٱللَّهُ",
            "ءَلِفْ لَااااااممممِۦۦمَ لَّااه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                meem_aal_imran="wasl_2",
            ),
        ),
        # مد طبيعي
        (
            "قَرِيبًۭا",
            "قَرِۦۦبَاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                meem_aal_imran="wasl_2",
            ),
        ),
        # مد اللين
        (
            "مِّنْ خَوْفٍۭ",
            "مِنْ خَوووووف",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=6,
            ),
        ),
        # compos tests
        (
            "قَالُوا۟ هَـٰذَا ٱلَّذِى رُزِقْنَا مِن قَبْلُ وَأُتُوا۟ بِهِۦ مُتَشَـٰبِهًۭا وَلَهُمْ فِيهَآ أَزْوَٰجٌۭ مُّطَهَّرَةٌۭ وَهُمْ فِيهَا خَـٰلِدُونَ",
            "قَاالُۥۥ هَااذَ لَّذِۦۦ رُزِقْنَاا مِںںںقَبْلُ وَأُتُۥۥ بِهِۦۦ مُتَشَاابِهَوووَلَهُمْ فِۦۦهَاااا أَزْوَااجُممممُطَهَّرَتُوووَهُمْ فِۦۦهَاا خَاالِدُۥۥن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
            ),
        ),
        (
            "عَلِيمٌۢ بَرَآءَةٌۭ",
            "عَلِۦۦۦۦمۜ بَرَااااءَه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "فَسَيَكْفِيكَهُمُ ٱللَّهُ",
            "فَسَيَكْفِۦۦكَهُمُ لَّااااه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
            "ءِيَّااكَ نَعْبُدُ وَءِيَّااكَ نَسْتَعِۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_madd(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = Madd()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(
            target_text,
            moshaf,
            None,
            mode="test",
            discard_ops=[EnlargeSmallLetters()],
        )
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "ٱلْحَقُّ",
            "ٱلْحَقّڇ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            f"أَنَّهُ ٱلْحَقُّ مِن",
            f"أَنَّهُ ٱلْحَقُّ مِن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "أَلَآ إِنَّهُمْ فِى مِرْيَةٍۢ مِّن لِّقَآءِ رَبِّهِمْ أَلَآ إِنَّهُۥ بِكُلِّ شَىْءٍۢ مُّحِيطٌۢ",
            "أَلَآ إِنَّهُمْ فِى مِرْيَةٍۢ مِّن لِّقَآءِ رَبِّهِمْ أَلَآ إِنَّهُۥ بِكُلِّ شَىْءٍۢ مُّحِيطڇ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "تَبَّتْ يَدَآ أَبِى لَهَبٍۢ وَتَبَّ",
            "تَبَّتْ يَدَآ أَبِى لَهَبٍۢ وَتَبّڇ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "قُلْ أَئِنَّكُمْ لَتَكْفُرُونَ بِٱلَّذِى خَلَقَ ٱلْأَرْضَ فِى يَوْمَيْنِ وَتَجْعَلُونَ لَهُۥٓ أَندَادًۭا ذَٰلِكَ رَبُّ ٱلْعَـٰلَمِينَ",
            "قُلْ أَئِنَّكُمْ لَتَكْفُرُونَ بِٱلَّذِى خَلَقَ ٱلْأَرْضَ فِى يَوْمَيْنِ وَتَجْڇعَلُونَ لَهُۥٓ أَندَادًۭا ذَٰلِكَ رَبُّ ٱلْعَـٰلَمِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَمَن يَعْمَلْ مِنَ ٱلصَّـٰلِحَـٰتِ مِن ذَكَرٍ أَوْ أُنثَىٰ وَهُوَ مُؤْمِنٌۭ فَأُو۟لَـٰٓئِكَ يَدْخُلُونَ ٱلْجَنَّةَ وَلَا يُظْلَمُونَ نَقِيرًۭا",
            "وَمَن يَعْمَلْ مِنَ ٱلصَّـٰلِحَـٰتِ مِن ذَكَرٍ أَوْ أُنثَىٰ وَهُوَ مُؤْمِنٌۭ فَأُو۟لَـٰٓئِكَ يَدْڇخُلُونَ ٱلْجَنَّةَ وَلَا يُظْلَمُونَ نَقِيرًۭا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
    ],
)
def test_qlqla(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = Qalqla()
    for b_op in op.ops_before:
        target_text = b_op.apply(
            target_text,
            moshaf,
            mode="test",
        )
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "وَقَالَ فِرْعَوْنُ يَـٰهَـٰمَـٰنُ ٱبْنِ لِى صَرْحًۭا لَّعَلِّىٓ أَبْلُغُ ٱلْأَسْبَـٰبَ",
            "وَقَالَ فِرْعَوْنُ يَـٰهَـٰمَـٰنُ ٱبْنِ لِى صَرْحًۭا لَّعَلِّىٓ أَبْلُغُ ٱلْأَسْبَـٰبَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱبْنِ لِى صَرْحًۭا لَّعَلِّىٓ أَبْلُغُ ٱلْأَسْبَـٰبَ",
            "ءِبْنِ لِى صَرْحًۭا لَّعَلِّىٓ أَبْلُغُ ٱلْأَسْبَـٰبَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱقْرَأْ",
            "ءِقْرَأْ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱتَّسَقَ",
            "ءِتَّسَقَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱئْتُوا۟",
            "ءِيتُوا۟",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱئْتُونِى بِكِتَـٰبٍۢ مِّن قَبْلِ هَـٰذَآ أَوْ أَثَـٰرَةٍۢ مِّنْ عِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            "ءِيتُونِى بِكِتَـٰبٍۢ مِّن قَبْلِ هَـٰذَآ أَوْ أَثَـٰرَةٍۢ مِّنْ عِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱئْتُونِى",
            "ءِيتُونِى",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱؤْتُمِنَ أَمَـٰنَتَهُۥ وَلْيَتَّقِ ٱللَّهَ رَبَّهُۥ",
            "ءُوتُمِنَ أَمَـٰنَتَهُۥ وَلْيَتَّقِ ٱللَّهَ رَبَّهُۥ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱسْتِكْبَارًۭا فِى ٱلْأَرْضِ وَمَكْرَ ٱلسَّيِّئِ وَلَا يَحِيقُ ٱلْمَكْرُ ٱلسَّيِّئُ إِلَّا بِأَهْلِهِۦ فَهَلْ يَنظُرُونَ إِلَّا سُنَّتَ ٱلْأَوَّلِينَ فَلَن تَجِدَ لِسُنَّتِ ٱللَّهِ تَبْدِيلًۭا وَلَن تَجِدَ لِسُنَّتِ ٱللَّهِ تَحْوِيلًا",
            "ءِسْتِكْبَارًۭا فِى ٱلْأَرْضِ وَمَكْرَ ٱلسَّيِّئِ وَلَا يَحِيقُ ٱلْمَكْرُ ٱلسَّيِّئُ إِلَّا بِأَهْلِهِۦ فَهَلْ يَنظُرُونَ إِلَّا سُنَّتَ ٱلْأَوَّلِينَ فَلَن تَجِدَ لِسُنَّتِ ٱللَّهِ تَبْدِيلًۭا وَلَن تَجِدَ لِسُنَّتِ ٱللَّهِ تَحْوِيلًا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلَّذِينَ ءَامَنُوا۟ وَلَمْ يَلْبِسُوٓا۟ إِيمَـٰنَهُم بِظُلْمٍ أُو۟لَـٰٓئِكَ لَهُمُ ٱلْأَمْنُ وَهُم مُّهْتَدُونَ",
            "ءَلَّذِينَ ءَامَنُوا۟ وَلَمْ يَلْبِسُوٓا۟ إِيمَـٰنَهُم بِظُلْمٍ أُو۟لَـٰٓئِكَ لَهُمُ ٱلْأَمْنُ وَهُم مُّهْتَدُونَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلَّـٰٓـِٔى وَلَدْنَهُمْ وَإِنَّهُمْ لَيَقُولُونَ مُنكَرًۭا مِّنَ ٱلْقَوْلِ وَزُورًۭا وَإِنَّ ٱللَّهَ لَعَفُوٌّ غَفُورٌۭ",
            "ءَلَّـٰٓـِٔى وَلَدْنَهُمْ وَإِنَّهُمْ لَيَقُولُونَ مُنكَرًۭا مِّنَ ٱلْقَوْلِ وَزُورًۭا وَإِنَّ ٱللَّهَ لَعَفُوٌّ غَفُورٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلَّذِينَ يَنقُضُونَ عَهْدَ ٱللَّهِ مِنۢ بَعْدِ مِيثَـٰقِهِۦ وَيَقْطَعُونَ مَآ أَمَرَ ٱللَّهُ بِهِۦٓ أَن يُوصَلَ وَيُفْسِدُونَ فِى ٱلْأَرْضِ",
            "ءَلَّذِينَ يَنقُضُونَ عَهْدَ ٱللَّهِ مِنۢ بَعْدِ مِيثَـٰقِهِۦ وَيَقْطَعُونَ مَآ أَمَرَ ٱللَّهُ بِهِۦٓ أَن يُوصَلَ وَيُفْسِدُونَ فِى ٱلْأَرْضِ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱللَّهُمَّ وَتَحِيَّتُهُمْ فِيهَا سَلَـٰمٌۭ وَءَاخِرُ دَعْوَىٰهُمْ أَنِ ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
            "ءَللَّهُمَّ وَتَحِيَّتُهُمْ فِيهَا سَلَـٰمٌۭ وَءَاخِرُ دَعْوَىٰهُمْ أَنِ ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلْخَبِيثَـٰتُ لِلْخَبِيثِينَ وَٱلْخَبِيثُونَ لِلْخَبِيثَـٰتِ وَٱلطَّيِّبَـٰتُ لِلطَّيِّبِينَ وَٱلطَّيِّبُونَ لِلطَّيِّبَـٰتِ أُو۟لَـٰٓئِكَ مُبَرَّءُونَ مِمَّا يَقُولُونَ لَهُم مَّغْفِرَةٌۭ وَرِزْقٌۭ كَرِيمٌۭ",
            "ءَلْخَبِيثَـٰتُ لِلْخَبِيثِينَ وَٱلْخَبِيثُونَ لِلْخَبِيثَـٰتِ وَٱلطَّيِّبَـٰتُ لِلطَّيِّبِينَ وَٱلطَّيِّبُونَ لِلطَّيِّبَـٰتِ أُو۟لَـٰٓئِكَ مُبَرَّءُونَ مِمَّا يَقُولُونَ لَهُم مَّغْفِرَةٌۭ وَرِزْقٌۭ كَرِيمٌۭ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
    ],
)
def test_qlqla(in_text: str, target_text: str, moshaf: MoshafAttributes):
    op = BeginWithHamzatWasl()
    for b_op in op.ops_before:
        target_text, _ = b_op.apply(
            target_text,
            moshaf,
            None,
            mode="test",
        )
    out_text, _ = op.apply(in_text, moshaf, None, mode="test")
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


@pytest.mark.parametrize(
    "verb, target_haraka",
    [
        (
            "ٱقْرَأْ",
            alph.uthmani.kasra,
        ),
        (
            "ٱتَّسَقَ",
            alph.uthmani.kasra,
        ),
        (
            "ٱنشَقَّتْ",
            alph.uthmani.kasra,
        ),
        (
            "ٱئْتُوا۟",
            alph.uthmani.kasra,
        ),
        (
            "ٱرْكُضْ",
            alph.uthmani.dama,
        ),
        (
            "ٱنفَطَرَتْ",
            alph.uthmani.kasra,
        ),
    ],
)
def test_get_thrird_letter_in_verb_haraka(
    verb: str,
    target_haraka: str,
):
    op = BeginWithHamzatWasl()
    haraka = op._get_verb_third_letter_haraka(verb)
    print(f"'{haraka}'")
    assert haraka == target_haraka


@pytest.mark.parametrize(
    "in_text, target_text, moshaf",
    [
        (
            "أَعُوذُ بِٱللَّهِ مِنَ ٱلشَّيْطَانِ ٱلرَّجِيمِ",
            "ءَعُۥۥذُ بِللَااهِ مِنَ ششَيطَاانِ ررَجِۦۦۦۦم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
            "بِسمِ للَااهِ ررَحمَاانِ ررَحِۦۦۦۦۦۦم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=6,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
            "ءَلحَمدُ لِللَااهِ رَببِ لعَاالَمِۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
            "ءَررَحمَاانِ ررَحِۦۦۦۦم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "مَـٰلِكِ يَوْمِ ٱلدِّينِ",
            "مَاالِكِ يَومِ ددِۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
            "ءِييَااكَ نَعبُدُ وَءِييَااكَ نَستَعِۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
            "ءِهدِنَ صصِرَااطَ لمُستَقِۦۦۦۦم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ",
            "صِرَااطَ للَذِۦۦنَ ءَنعَمتَ عَلَيهِم غَيرِ لمَغضُۥۥبِ عَلَيهِم وَلَ ضضَااااااللِۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "الٓمٓ",
            "ءَلِف لَااااااممممِۦۦۦۦۦۦم",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ",
            "ذَاالِكَ لكِتَاابُ لَاا رَيييبڇ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "فِيهِ هُدًۭى لِّلْمُتَّقِينَ",
            "فِۦۦهِ هُدَللِلمُتتَقِۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱلَّذِينَ يُؤْمِنُونَ بِٱلْغَيْبِ وَيُقِيمُونَ ٱلصَّلَوٰةَ وَمِمَّا رَزَقْنَـٰهُمْ يُنفِقُونَ",
            "ءَللَذِۦۦنَ يُءمِنُۥۥنَ بِلغَيبِ وَيُقِۦۦمُۥۥنَ صصَلَااتَ وَمِممممَاا رَزَقڇنَااهُم يُںںںفِقُۥۥۥۥن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَٱلَّذِينَ يُؤْمِنُونَ بِمَآ أُنزِلَ إِلَيْكَ وَمَآ أُنزِلَ مِن قَبْلِكَ وَبِٱلْـَٔاخِرَةِ هُمْ يُوقِنُونَ",
            "وَللَذِۦۦنَ يُءمِنُۥۥنَ بِمَاااا ءُںںںزِلَ ءِلَيكَ وَمَاااا ءُںںںزِلَ مِںںںقَبڇلِكَ وَبِلءَااخِرَتِ هُم يُۥۥقِنُۥۥۥۥن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "أُو۟لَـٰٓئِكَ عَلَىٰ هُدًۭى مِّن رَّبِّهِمْ وَأُو۟لَـٰٓئِكَ هُمُ ٱلْمُفْلِحُونَ",
            "ءُلَاااااءِكَ عَلَاا هُدَممممِررَببِهِم وَءُلَاااااءِكَ هُمُ لمُفلِحُۥۥن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=5,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "إِنَّ ٱلَّذِينَ كَفَرُوا۟ سَوَآءٌ عَلَيْهِمْ ءَأَنذَرْتَهُمْ أَمْ لَمْ تُنذِرْهُمْ لَا يُؤْمِنُونَ",
            "ءِننننَ للَذِۦۦنَ كَفَرُۥۥ سَوَااااءُن عَلَيهِم ءَءَںںںذَرتَهُم ءَم لَم تُںںںذِرهُم لَاا يُءمِنُۥۥۥۥن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "إِنَّ ٱللَّهَ لَا يَسْتَحْىِۦٓ أَن يَضْرِبَ مَثَلًۭا مَّا بَعُوضَةًۭ فَمَا فَوْقَهَا",
            "ءِننننَ للَااهَ لَاا يَستَحيِۦۦۦۦ ءَيييَضرِبَ مَثَلَممممَاا بَعُۥۥضَتَںںںفَمَاا فَوقَهَاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَمَن يُطِعِ ٱللَّهَ وَٱلرَّسُولَ فَأُو۟لَـٰٓئِكَ مَعَ ٱلَّذِينَ أَنْعَمَ ٱللَّهُ عَلَيْهِم مِّنَ ٱلنَّبِيِّـۧنَ وَٱلصِّدِّيقِينَ وَٱلشُّهَدَآءِ وَٱلصَّـٰلِحِينَ وَحَسُنَ أُو۟لَـٰٓئِكَ رَفِيقًۭا",
            "وَمَيييُطِعِ للَااهَ وَررَسُۥۥلَ فَءُلَااااءِكَ مَعَ للَذِۦۦنَ ءَنعَمَ للَااهُ عَلَيهِممممِنَ ننننَبِييِۦۦنَ وَصصِددِۦۦقِۦۦنَ وَششُهَدَااااءِ وَصصَاالِحِۦۦنَ وَحَسُنَ ءُلَااااءِكَ رَفِۦۦقَاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَأَقِيمُوا۟ ٱلصَّلَوٰةَ",
            "وَءَقِۦۦمُ صصَلَااااه",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ثَمَـٰنِيَةَ أَزْوَٰجٍۢ مِّنَ ٱلضَّأْنِ ٱثْنَيْنِ وَمِنَ ٱلْمَعْزِ ٱثْنَيْنِ قُلْ ءَآلذَّكَرَيْنِ حَرَّمَ أَمِ ٱلْأُنثَيَيْنِ أَمَّا ٱشْتَمَلَتْ عَلَيْهِ أَرْحَامُ ٱلْأُنثَيَيْنِ نَبِّـُٔونِى بِعِلْمٍ إِن كُنتُمْ صَـٰدِقِينَ",
            "ثَمَاانِيَتَ ءَزوَااجِممممِنَ ضضَءنِ ثنَينِ وَمِنَ لمَعزِ ثنَينِ قُل ءَٲذذَكَرَينِ حَررَمَ ءَمِ لءُںںںثَيَينِ ءَممممَ شتَمَلَت عَلَيهِ ءَرحَاامُ لءُںںںثَيَينِ نَببِءُۥۥنِۦۦ بِعِلمِن ءِںںںكُںںںتُم صَاادِقِۦۦۦۦن",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "وَلِلَّهِ مُلْكُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَٱللَّهُ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌ",
            "وَلِللَااهِ مُلكُ سسَمَااوَااتِ وَلءَرضِ وَللَااهُ عَلَاا كُللِ شَيءِںںںقَدِۦۦۦۦر",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "لَـَٔايَـٰتٍۢ",
            "لَءَاايَاات",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "لْيَقْضُوا۟",
            "لِيَقڇضُۥۥ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "لْيَقْطَعْ",
            "لِيَقڇطَع",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "فَلَمَّآ أَتَىٰهَا نُودِىَ يَـٰمُوسَىٰٓ",
            "فَلَممممَاااا ءَتَااهَاا نُۥۥدِيَ يَاامُۥۥسَاا",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "هُوَ ٱلْحَىُّ",
            "هُوَ لحَيي",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
            ),
        ),
        (
            "كَذَٰلِكَ يُحْىِ",
            "كَذَاالِكَ يُحيِۦۦ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
            ),
        ),
        (
            "إِنَّ ٱللَّهَ لَا يَسْتَحْىِۦٓ",
            "ءِننننَ للَااهَ لَاا يَستَحيِۦۦ",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
            ),
        ),
        (
            "يَـٰٓأَيُّهَا ٱلنَّبِىُّ",
            "يَااءَييُهَ ننننَبِيي",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=2,
            ),
        ),
        (
            "ٱلْحَىِّ",
            "ءَلحَيي",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=6,
            ),
        ),
        (
            "أَحَطتُ",
            "ءَحَطت",
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=2,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=6,
            ),
        ),
    ],
)
def test_quran_phonetizer(in_text: str, target_text: str, moshaf: MoshafAttributes):
    out_text = quran_phonetizer(in_text, moshaf).phonemes
    print(f"Target Text:\n'{target_text}'")
    print(f"Out Text:\n'{out_text}'")
    assert out_text == target_text


def test_quran_phonetizer_strees_test():
    start_aya = Aya()
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
        noon_tamnna="rawm",
    )

    for aya in start_aya.get_ayat_after(114):
        txt = aya.get().uthmani
        out_text = quran_phonetizer(txt, moshaf, remove_spaces=True).phonemes
        alphabet = set(asdict(alph.phonetics).values())
        out_alphabet = set(out_text)
        if not out_alphabet <= alphabet:
            print(f"Diff: '{out_alphabet - alphabet}'")
            print(aya)
            print(out_text)
            raise ValueError()


@pytest.mark.parametrize(
    "in_text, ex_sifa_outputs, moshaf",
    [
        (
            "ٱلْحَمْدُ",
            [
                SifaOutput(
                    phonemes="ءَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ل",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="حَ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="م",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="دڇ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "مِن قَبْلِكَ",
            [
                SifaOutput(
                    phonemes="مِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="ںںں",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="قَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="بڇ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="لِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ك",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "بِمَآ أُنزِلَ",
            [
                SifaOutput(
                    phonemes="بِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="مَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="اااا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءُ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ںںں",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="زِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ل",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَلَا ٱلضَّآلِّينَ",
            [
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="لَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ضضَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="motbaq",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اااااا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ۦۦۦۦ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ن",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَلِلَّهِ مُلْكُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَٱللَّهُ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌ",
            [
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="لِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="هِ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="مُ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="ل",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="كُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="سسَ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="مَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="تِ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ل",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ر",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ضِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="motbaq",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="هُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="عَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="لَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="كُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="شَ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ي",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ںںں",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="قَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="دِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ۦۦۦۦ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ر",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "قُلْ ءَآللَّهُ أَذِنَ",
            [
                SifaOutput(
                    phonemes="قُ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ل",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ٲ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="هُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ذِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ن",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
        (
            "قُلْ ءَآللَّهُ أَذِنَ",
            [
                SifaOutput(
                    phonemes="قُ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ل",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اااااا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="هُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ءَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ذِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ن",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="madd",
            ),
        ),
        (
            "رَّضِىَ ٱللَّهُ عَنْهُمْ وَرَضُوا۟ عَنْهُ",
            [
                SifaOutput(
                    phonemes="رَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ضِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="motbaq",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="يَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="للَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="هُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="عَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ن",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="هُ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="م",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="رَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ضُ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="motbaq",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ۥۥ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="عَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ن",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="ه",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="madd",
            ),
        ),
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
            [
                SifaOutput(
                    phonemes="بِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="س",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="مِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="للَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="هِ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ررَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ح",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="مَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="اا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="نِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="ررَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="حِ",
                    hams_or_jahr="hams",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ۦۦۦۦ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="م",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَقِيلَ مَنْ رَاقٍۢ",
            [
                SifaOutput(
                    phonemes="وَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="قِ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="low_mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="ۦۦ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="لَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="مَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="نۜ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="moraqaq",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="maghnoon",
                ),
                SifaOutput(
                    phonemes="رَ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="between",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="اااا",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="rikhw",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="not_moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
                SifaOutput(
                    phonemes="قڇ",
                    hams_or_jahr="jahr",
                    shidda_or_rakhawa="shadeed",
                    tafkheem_or_taqeeq="mofakham",
                    itbaq="monfateh",
                    safeer="no_safeer",
                    qalqla="moqalqal",
                    tikraar="not_mokarar",
                    tafashie="not_motafashie",
                    istitala="not_mostateel",
                    ghonna="not_maghnoon",
                ),
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_process_sifat(
    in_text: str, ex_sifa_outputs: list[SifaOutput], moshaf: MoshafAttributes
):
    phoneme_script = quran_phonetizer(in_text, moshaf).phonemes
    print(f"phonized text Text:\n'{phoneme_script}'")
    sifa_outputs = process_sifat(in_text, phoneme_script, moshaf)

    assert len(ex_sifa_outputs) == len(sifa_outputs)
    for out, target in zip(sifa_outputs, ex_sifa_outputs):
        print(out)
        print(target)
        assert out == target


@pytest.mark.parametrize(
    "uth_text, ex_outs, moshaf",
    [
        (
            "قُلِ ٱللَّهُمَّ مَـٰلِكَ ٱلْمُلْكِ",
            [
                "moraqaq",
                "moraqaq",
                "moraqaq",
                "moraqaq",
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَلَوْ شَآءَ ٱللَّهُ لَذَهَبَ بِسَمْعِهِمْ وَأَبْصَـٰرِهِمْ إِنَّ ٱللَّهَ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌۭ",
            [
                "moraqaq",
                "mofakham",
                "moraqaq",
                "mofakham",
                "moraqaq",
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ",
            [
                "mofakham",
                "moraqaq",
                "moraqaq",
                "moraqaq",
                "moraqaq",
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَلِلَّهِ مُلْكُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَٱللَّهُ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌ",
            [
                "moraqaq",
                "moraqaq",
                "moraqaq",
                "moraqaq",
                "mofakham",
                "moraqaq",
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
    ],
)
def test_lam_tafkheem_tarqeeq_finder(
    uth_text: str,
    ex_outs: list[Literal["mofakham", "moraqaq"]],
    moshaf: MoshafAttributes,
):
    ph_script = quran_phonetizer(uth_text, moshaf).phonemes
    outputs = lam_tafkheem_tarqeeq_finder(ph_script)
    print(uth_text)
    print(f"Ouputs: {outputs}")
    print(f"Ex Ouputs: {ex_outs}")
    assert len(outputs) == len(ex_outs)
    for o, ex_o in zip(outputs, ex_outs):
        assert o == ex_o


@pytest.mark.parametrize(
    "uth_text, ex_outs, moshaf",
    [
        (
            "قُلِ ٱللَّهُمَّ مَـٰلِكَ ٱلْمُلْكِ",
            [
                "moraqaq",
                None,
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَلَوْ شَآءَ ٱللَّهُ لَذَهَبَ بِسَمْعِهِمْ وَأَبْصَـٰرِهِمْ إِنَّ ٱللَّهَ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌۭ",
            [
                None,
                "mofakham",
                None,
                "mofakham",
                None,
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ",
            [
                "mofakham",
                None,
                None,
                None,
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "وَلِلَّهِ مُلْكُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضِ وَٱللَّهُ عَلَىٰ كُلِّ شَىْءٍۢ قَدِيرٌ",
            [
                "moraqaq",
                None,
                None,
                "mofakham",
                None,
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                between_anfal_and_tawba="sakt",
            ),
        ),
        (
            "قُلْ ءَآللَّهُ أَذِنَ",
            [
                None,
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="madd",
            ),
        ),
        (
            "قُلْ ءَآللَّهُ أَذِنَ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                tasheel_or_madd="tasheel",
            ),
        ),
    ],
)
def test_lam_tafkheem_tarqeeq_finder(
    uth_text: str,
    ex_outs: list[Literal["mofakham", "moraqaq"]],
    moshaf: MoshafAttributes,
):
    ph_script = quran_phonetizer(uth_text, moshaf).phonemes
    outputs = alif_tafkheem_tarqeeq_finder(ph_script)
    print(uth_text)
    print(ph_script)
    print(f"Ouputs: {outputs}")
    print(f"Ex Ouputs: {ex_outs}")
    assert len(outputs) == len(ex_outs)
    for o, ex_o in zip(outputs, ex_outs):
        assert o == ex_o


@pytest.mark.parametrize(
    "uth_text, ex_outs, moshaf",
    [
        (
            "كَرِيمٌۭ",
            [
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فِرْعَوْنَ",
            [
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "حِجْرٌۭ",
            [
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "خَيْرٌۭ",
            [
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قَدِيرٌۭ",
            [
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مَجْر۪ىٰهَا",
            [
                "moraqaq",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "رَمَضَانَ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "مَرْيَمَ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَٱلْعَصْرِ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "كَفَرُوا۟",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلْقُرْءَانُ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "خُسْرٍ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱرْجِعُوٓا۟",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "ٱلَّذِى ٱرْتَضَىٰ لَهُمْ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "وَإِرْصَادًۭا",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "قِرْطَاسٍۢ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فِرْقَةٍۢ",
            [
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "شَهْرُ رَمَضَانَ ٱلَّذِىٓ أُنزِلَ فِيهِ ٱلْقُرْءَانُ هُدًۭى لِّلنَّاسِ وَبَيِّنَـٰتٍۢ مِّنَ ٱلْهُدَىٰ وَٱلْفُرْقَانِ فَمَن شَهِدَ مِنكُمُ ٱلشَّهْرَ فَلْيَصُمْهُ وَمَن كَانَ مَرِيضًا أَوْ عَلَىٰ سَفَرٍۢ فَعِدَّةٌۭ مِّنْ أَيَّامٍ أُخَرَ يُرِيدُ ٱللَّهُ بِكُمُ ٱلْيُسْرَ وَلَا يُرِيدُ بِكُمُ ٱلْعُسْرَ وَلِتُكْمِلُوا۟ ٱلْعِدَّةَ وَلِتُكَبِّرُوا۟ ٱللَّهَ عَلَىٰ مَا هَدَىٰكُمْ وَلَعَلَّكُمْ تَشْكُرُونَ",
            [
                "mofakham",
                "mofakham",
                "mofakham",
                "mofakham",
                "mofakham",
                "moraqaq",
                "moraqaq",
                "mofakham",
                "moraqaq",
                "mofakham",
                "moraqaq",
                "mofakham",
                "mofakham",
                "mofakham",
            ],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
        (
            "فِرْقٍۢ كَٱلطَّوْدِ",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_firq="tafkheem",
            ),
        ),
        (
            "فِرْقٍۢ كَٱلطَّوْدِ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_firq="tarqeeq",
            ),
        ),
        (
            "فِرْقٍۢ",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_firq="tarqeeq",
            ),
        ),
        (
            "ٱلْقِطْرِ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_alqitr="tarqeeq",
            ),
        ),
        (
            "ٱلْقِطْرِ",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_alqitr="tafkheem",
            ),
        ),
        (
            "ٱلْقِطْرِ وَمِنَ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_alqitr="tafkheem",
            ),
        ),
        (
            "بِمِصْرَ",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_misr="tafkheem",
            ),
        ),
        (
            "بِمِصْرَ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_misr="tarqeeq",
            ),
        ),
        (
            "بِمِصْرَ بُيُوتًۭا",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_misr="tarqeeq",
            ),
        ),
        (
            "وَنُذُرِ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_nudhur="tarqeeq",
            ),
        ),
        (
            "وَنُذُرِ",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_nudhur="tafkheem",
            ),
        ),
        (
            "وَنُذُرِ إِنَّآ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_nudhur="tafkheem",
            ),
        ),
        (
            "يَسْرِ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_yasr="tarqeeq",
            ),
        ),
        (
            "يَسْرِ",
            ["mofakham"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_yasr="tafkheem",
            ),
        ),
        (
            "فَأَسْرِ بِأَهْلِكَ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                raa_yasr="tafkheem",
            ),
        ),
        (
            "تُصَعِّرْ خَدَّكَ",
            ["moraqaq"],
            MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
            ),
        ),
    ],
)
def test_raa_tafkheem_tarqeeq_finder(
    uth_text: str,
    ex_outs: list[Literal["mofakham", "moraqaq"]],
    moshaf: MoshafAttributes,
):
    outputs = raa_tafkheem_tarqeeq_finder(uth_text, moshaf)
    print(uth_text)
    print(f"Ouputs: {outputs}")
    print(f"Ex Ouputs: {ex_outs}")
    assert len(outputs) == len(ex_outs)
    for o, ex_o in zip(outputs, ex_outs):
        assert o == ex_o
