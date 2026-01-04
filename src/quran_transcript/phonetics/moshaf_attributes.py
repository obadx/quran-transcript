from dataclasses import dataclass
from typing import Any, Literal, get_origin, get_args
import sys

# Sllving import Self from python 3.10
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)
from pydantic.fields import PydanticUndefined, FieldInfo


@dataclass
class MoshafFieldDocs:
    english_name: str
    arabic_name: str
    english2arabic_map: dict[Any, Any]
    more_info: str = ""


def get_moshaf_field_docs(fieldname: str, fieldinfo: FieldInfo) -> MoshafFieldDocs:
    """Retuns the Moshaf Field docs as a `MoshafFieldDocs`

    If the attribute is not Quran specifc will return None

    Returns:
        MoshafFieldDocs
    """
    if get_origin(fieldinfo.annotation) != Literal:
        return None
    docs = fieldinfo.description
    if docs == PydanticUndefined or not docs:
        return None

    arabic_name = get_arabic_name(fieldinfo)
    # Filterout None Quranic Attributes
    if arabic_name is None:
        return None

    english2arabic_map = get_arabic_attributes(fieldinfo)
    if english2arabic_map is None:
        choices = list(get_args(fieldinfo.annotation))
        english2arabic_map = {c: c for c in choices}

    return MoshafFieldDocs(
        arabic_name=arabic_name,
        english_name=fieldname,
        english2arabic_map=english2arabic_map,
        more_info=docs,
    )


def get_arabic_attributes(field_info: FieldInfo) -> dict[str, str] | None:
    """get the Arabic attributes maping from English for `Literal` type fields

    Returns:
        * the Arabic Attributes as {"English vlaue": "Arabie Value"}
        * None: if there is no Arabic Name
    """
    if field_info.json_schema_extra:
        if "field_arabic_attrs_map" in field_info.json_schema_extra:
            return field_info.json_schema_extra["field_arabic_attrs_map"]
    return None


def get_arabic_name(field_info: FieldInfo) -> str | None:
    """get the Arabic name out of the field description

    Retusns:
        * the Arabic Name, rest of the docs
        * None: if there is no Arabic Name

    """
    if field_info.json_schema_extra:
        if "field_arabic_name" in field_info.json_schema_extra:
            return field_info.json_schema_extra["field_arabic_name"]

    return None


class MoshafAttributes(BaseModel):
    # Quran Specific Attributes
    # Core Attributes (كليات)
    rewaya: Literal["hafs"] = Field(
        json_schema_extra={
            "field_arabic_name": "الرواية",
            "field_arabic_attrs_map": {"hafs": "حفص"},
        },
        description="The type of the quran Rewaya.",
    )
    recitation_speed: Literal["mujawad", "above_murattal", "murattal", "hadr"] = Field(
        default="murattal",
        json_schema_extra={
            "field_arabic_name": "سرعة التلاوة",
            "field_arabic_attrs_map": {
                "mujawad": "مجود",
                "above_murattal": "فويق المرتل",
                "murattal": "مرتل",
                "hadr": "حدر",
            },
        },
        description="The recitation speed sorted from slowest to the fastest سرعة التلاوة مرتبة من الأبطأ إلي الأسرع",
    )

    takbeer: Literal[
        "no_takbeer", "beginning_of_sharh", "end_of_doha", "general_takbeer"
    ] = Field(
        default="no_takbeer",
        json_schema_extra={
            "field_arabic_name": "التكبير",
            "field_arabic_attrs_map": {
                "no_takbeer": "لا تكبير",
                "beginning_of_sharh": "التكبير من أول الشرح لأول الناس",
                "end_of_doha": "التكبير من آخر الضحى لآخر الناس",
                "general_takbeer": "التكبير أول كل سورة إلا التوبة",
            },
        },
        description="The ways to add takbeer (الله أكبر) after Istiaatha"
        " (استعاذة) and between end of the surah and beginning of the surah."
        ' `no_takbeer`: "لا تكبير" — No Takbeer (No proclamation of greatness, i.e., there is no Takbeer recitation)'
        ' `beginning_of_sharh`: "التكبير من أول الشرح لأول الناس" — Takbeer from the beginning of Surah Ash-Sharh to the beginning of Surah An-Nas'
        ' `end_of_dohaf`: "التكبير من آخر الضحى لآخر الناس" — Takbeer from the end of Surah Ad-Duha to the end of Surah An-Nas'
        ' `general_takbeer`: "التكبير أول كل سورة إلا التوبة" — Takbeer at the beginning of every Surah except Surah At-Tawbah',
    )

    madd_monfasel_len: Literal[2, 3, 4, 5] = Field(
        json_schema_extra={
            "field_arabic_name": "مد المنفصل",
        },
        description=' The length of Mad Al Monfasel "مد النفصل" for Hafs Rewaya.',
    )
    madd_mottasel_len: Literal[4, 5, 6] = Field(
        json_schema_extra={
            "field_arabic_name": "مقدار المد المتصل",
        },
        description=' The length of Mad Al Motasel "مد المتصل" for Hafs.',
    )
    madd_mottasel_waqf: Literal[4, 5, 6] = Field(
        json_schema_extra={
            "field_arabic_name": "مقدار المد المتصل وقفا",
        },
        description=" The length of Madd Almotasel at pause for Hafs."
        '. Example "السماء".',
    )
    madd_aared_len: Literal[2, 4, 6] = Field(
        json_schema_extra={
            "field_arabic_name": "مقدار المد العارض",
        },
        description=' The length of Mad Al Aared "مد العارض للسكون".',
    )
    madd_alleen_len: Literal[2, 4, 6] = Field(
        default=None,
        json_schema_extra={
            "field_arabic_name": "مقدار مد اللين",
        },
        description="The length of the Madd al-Leen when stopping at the end of a word"
        " (for a sakin waw or ya preceded by a letter with a fatha) should be"
        " less than or equal to the length of Madd al-'Arid (the temporary stretch due to stopping)."
        " **Default Value is equal to `madd_aared_len`**."
        " مقدرا مع اللين عن القوف (للواو الساكنة والياء الساكنة وقبلها حرف مفتوح) ويجب أن يكون مقدار مد اللين أقل من أو يساوي مع العارض",
    )
    ghonna_lam_and_raa: Literal["ghonna", "no_ghonna"] = Field(
        default="no_ghonna",
        json_schema_extra={
            "field_arabic_name": "غنة اللام و الراء",
            "field_arabic_attrs_map": {"ghonna": "غنة", "no_ghonna": "لا غنة"},
        },
        description="The ghonna for merging (Idghaam) noon with Lam and Raa for Hafs.",
    )

    # (الجزئيات)
    meem_aal_imran: Literal["waqf", "wasl_2", "wasl_6"] = Field(
        default="waqf",
        json_schema_extra={
            "field_arabic_name": "ميم آل عمران في قوله تعالى: {الم الله} وصلا",
            "field_arabic_attrs_map": {
                "waqf": "وقف",
                "wasl_2": "فتح الميم ومدها حركتين",
                "wasl_6": "فتح الميم ومدها ستة حركات",
            },
        },
        description="The ways to recite the word meem Aal Imran (الم الله)"
        " at connected recitation."
        " `waqf`: Pause with a prolonged madd (elongation) of 6 harakat (beats)."
        ' `wasl_2` Pronounce "meem" with fathah (a short "a" sound) and stretch it for 2 harakat.'
        ' `wasl_6` Pronounce "meem" with fathah and stretch it for 6 harakat.',
    )
    madd_yaa_alayn_alharfy: Literal[2, 4, 6] = Field(
        default=6,
        json_schema_extra={
            "field_arabic_name": "مقدار   المد اللازم الحرفي للعين",
        },
        description=" The length of Lzem Harfy of Yaa in letter Al-Ayen Madd"
        ' "المد الحرفي اللازم لحرف العين" in'
        ' surar: Maryam "مريم", AlShura "الشورى".',
    )
    saken_before_hamz: Literal["tahqeek", "general_sakt", "local_sakt"] = Field(
        default="tahqeek",
        json_schema_extra={
            "field_arabic_name": "الساكن قبل الهمز",
            "field_arabic_attrs_map": {
                "tahqeek": "تحقيق",
                "general_sakt": "سكت عام",
                "local_sakt": "سكت خاص",
            },
        },
        description="The ways of Hafs for saken before hamz. "
        '"The letter with sukoon before the hamzah (ء)".'
        "And it has three forms: full articulation (`tahqeeq`),"
        " general pause (`general_sakt`), and specific pause (`local_skat`).",
    )
    sakt_iwaja: Literal["sakt", "waqf", "idraj"] = Field(
        default="waqf",
        json_schema_extra={
            "field_arabic_name": "السكت عند عوجا في الكهف",
            "field_arabic_attrs_map": {"sakt": "سكت", "waqf": "وقف", "idraj": "إدراج"},
        },
        description='The ways to recite the word "عوجا" (Iwaja).'
        " `sakt` means slight pause."
        " `idraj` means not `sakt`."
        " `waqf`:  means full pause, so we can not determine weither"
        " the reciter uses `sakt` or `idraj` (no sakt).",
    )
    sakt_marqdena: Literal["sakt", "waqf", "idraj"] = Field(
        default="waqf",
        json_schema_extra={
            "field_arabic_name": "السكت عند مرقدنا  في يس",
            "field_arabic_attrs_map": {"sakt": "سكت", "waqf": "وقف", "idraj": "إدراج"},
        },
        description='The ways to recite the word "مرقدنا" (Marqadena) in Surat Yassen.'
        " `sakt` means slight pause."
        " `idraj` means not `sakt`."
        " `waqf`:  means full pause, so we can not determine weither"
        " the reciter uses `sakt` or `idraj` (no sakt).",
    )
    sakt_man_raq: Literal["sakt", "waqf", "idraj"] = Field(
        default="sakt",
        json_schema_extra={
            "field_arabic_name": "السكت عند  من راق في القيامة",
            "field_arabic_attrs_map": {"sakt": "سكت", "waqf": "وقف", "idraj": "إدراج"},
        },
        description='The ways to recite the word "من راق" (Man Raq) in Surat Al Qiyama.'
        " `sakt` means slight pause."
        " `idraj` means not `sakt`."
        " `waqf`:  means full pause, so we can not determine weither"
        " the reciter uses `sakt` or `idraj` (no sakt).",
    )
    sakt_bal_ran: Literal["sakt", "waqf", "idraj"] = Field(
        default="sakt",
        json_schema_extra={
            "field_arabic_name": "السكت عند  بل ران في  المطففين",
            "field_arabic_attrs_map": {"sakt": "سكت", "waqf": "وقف", "idraj": "إدراج"},
        },
        description='The ways to recite the word "بل ران" (Bal Ran) in Surat Al Motaffin.'
        " `sakt` means slight pause."
        " `idraj` means not `sakt`."
        " `waqf`:  means full pause, so we can not determine weither"
        " the reciter uses `sakt` or `idraj` (no sakt).",
    )
    sakt_maleeyah: Literal["sakt", "waqf", "idgham"] = Field(
        default="waqf",
        json_schema_extra={
            "field_arabic_name": "وجه  قوله تعالى {ماليه هلك} بالحاقة",
            "field_arabic_attrs_map": {"sakt": "سكت", "waqf": "وقف", "idgham": "إدغام"},
        },
        description="The ways to recite the word {ماليه هلك} in Surah Al-Ahqaf."
        " `sakt` means slight pause."
        " `idgham` Assimilation of the letter 'Ha' (ه) into the letter 'Ha' (ه) with complete assimilation."
        "`waqf`:  means full pause, so we can not determine weither"
        " the reciter uses `sakt` or `idgham`.",
    )
    between_anfal_and_tawba: Literal["waqf", "sakt", "wasl"] = Field(
        default="waqf",
        json_schema_extra={
            "field_arabic_name": "وجه بين الأنفال والتوبة",
            "field_arabic_attrs_map": {"waqf": "وقف", "sakt": "سكت", "wasl": "وصل"},
        },
        description="The ways to recite end of Surah Al-Anfal and beginning of Surah At-Tawbah.",
    )
    noon_and_yaseen: Literal["izhar", "idgham"] = Field(
        json_schema_extra={
            "field_arabic_name": "الإدغام والإظهار في النون عند الواو من قوله تعالى: {يس والقرآن}و {ن والقلم}",
            "field_arabic_attrs_map": {"izhar": "إظهار", "idgham": "إدغام"},
        },
        default="izhar",
        description='Weither to merge noon of both: {يس} and {ن} with (و) "`idgham`" or not "`izhar`".',
    )
    yaa_ataan: Literal["wasl", "hadhf", "ithbat"] = Field(
        default="wasl",
        json_schema_extra={
            "field_arabic_name": " إثبات الياء وحذفها وقفا في قوله تعالى {آتان} بالنمل",
            "field_arabic_attrs_map": {
                "wasl": "وصل",
                "hadhf": "حذف",
                "ithbat": "إثبات",
            },
        },
        description="The affirmation and omission of the letter 'Yaa' in the pause of the verse {آتاني} in Surah An-Naml."
        "`wasl`: means connected recitation without pasuding as (آتانيَ)."
        "`hadhf`: means deletion of letter (ي) at puase so recited as (آتان)."
        "`ithbat`: means confirmation reciting letter (ي) at puase as (آتاني).",
    )
    start_with_ism: Literal["wasl", "lism", "alism"] = Field(
        default="wasl",
        json_schema_extra={
            "field_arabic_name": "وجه البدأ بكلمة {الاسم} في سورة الحجرات",
            "field_arabic_attrs_map": {"wasl": "وصل", "lism": "لسم", "alism": "ألسم"},
        },
        description="The ruling on starting with the word {الاسم} in Surah Al-Hujurat."
        "`lism` Recited as (لسم) at the beginning. "
        "`alism` Recited as (ألسم). ath the beginning"
        "`wasl`: means completing recitaion without paussing as normal, "
        "So Reciting is as (بئس لسم).",
    )
    yabsut: Literal["seen", "saad"] = Field(
        json_schema_extra={
            "field_arabic_name": "السين والصاد في قوله تعالى: {والله يقبض ويبسط} بالبقرة",
            "field_arabic_attrs_map": {"seen": "سين", "saad": "صاد"},
        },
        default="seen",
        description="The ruling on pronouncing `seen` (س) or `saad` (ص) in the verse {والله يقبض ويبسط} in Surah Al-Baqarah.",
    )
    bastah: Literal["seen", "saad"] = Field(
        default="seen",
        json_schema_extra={
            "field_arabic_name": "السين والصاد في قوله تعالى:  {وزادكم في الخلق بسطة} بالأعراف",
            "field_arabic_attrs_map": {"seen": "سين", "saad": "صاد"},
        },
        description="The ruling on pronouncing `seen` (س) or `saad` (ص ) in the verse {وزادكم في الخلق بسطة} in Surah Al-A'raf.",
    )
    almusaytirun: Literal["seen", "saad"] = Field(
        default="saad",
        json_schema_extra={
            "field_arabic_name": "السين والصاد في قوله تعالى {أم هم المصيطرون} بالطور",
            "field_arabic_attrs_map": {"seen": "سين", "saad": "صاد"},
        },
        description="The pronunciation of `seen` (س) or `saad` (ص ) in the verse {أم هم المصيطرون} in Surah At-Tur.",
    )
    bimusaytir: Literal["seen", "saad"] = Field(
        default="saad",
        json_schema_extra={
            "field_arabic_name": "السين والصاد في قوله تعالى:  {لست عليهم بمصيطر} بالغاشية",
            "field_arabic_attrs_map": {"seen": "سين", "saad": "صاد"},
        },
        description="The pronunciation of `seen` (س) or `saad` (ص ) in the verse {لست عليهم بمصيطر} in Surah Al-Ghashiyah.",
    )
    tasheel_or_madd: Literal["tasheel", "madd"] = Field(
        default="madd",
        json_schema_extra={
            "field_arabic_name": "همزة الوصل في قوله تعالى: {آلذكرين} بموضعي الأنعام و{آلآن} موضعي يونس و{آلله} بيونس والنمل",
            "field_arabic_attrs_map": {"tasheel": "تسهيل", "madd": "مد"},
        },
        description=" Tasheel of Madd"
        ' "وجع التسهيل أو المد" for 6 words in The Holy Quran:'
        ' "ءالذكرين", "ءالله", "ءائن".',
    )
    yalhath_dhalik: Literal["izhar", "idgham", "waqf"] = Field(
        default="idgham",
        json_schema_extra={
            "field_arabic_name": "الإدغام وعدمه في قوله تعالى: {يلهث ذلك} بالأعراف",
            "field_arabic_attrs_map": {
                "izhar": "إظهار",
                "idgham": "إدغام",
                "waqf": "وقف",
            },
        },
        description="The assimilation (`idgham`) and non-assimilation (`izhar`) in the verse {يلهث ذلك} in Surah Al-A'raf."
        " `waqf`: means the rectier has paused on (يلهث)",
    )
    irkab_maana: Literal["izhar", "idgham", "waqf"] = Field(
        default="idgham",
        json_schema_extra={
            "field_arabic_name": "الإدغام والإظهار في قوله تعالى: {اركب معنا} بهود",
            "field_arabic_attrs_map": {
                "izhar": "إظهار",
                "idgham": "إدغام",
                "waqf": "وقف",
            },
        },
        description="The assimilation and clear pronunciation in the verse {اركب معنا} in Surah Hud."
        "This refers to the recitation rules concerning whether the letter"
        ' "Noon" (ن) is assimilated into the following letter or pronounced'
        " clearly when reciting this specific verse."
        " `waqf`: means the rectier has paused on (اركب)",
    )
    noon_tamnna: Literal["ishmam", "rawm"] = Field(
        default="ishmam",
        json_schema_extra={
            "field_arabic_name": " الإشمام والروم (الاختلاس) في قوله تعالى {لا تأمنا على يوسف}",
            "field_arabic_attrs_map": {"ishmam": "إشمام", "rawm": "روم"},
        },
        description="The nasalization (`ishmam`) or the slight drawing (`rawm`) in the verse {لا تأمنا على يوسف}",
    )
    harakat_daaf: Literal["fath", "dam"] = Field(
        default="fath",
        json_schema_extra={
            "field_arabic_name": "حركة الضاد (فتح أو ضم) في قوله تعالى {ضعف} بالروم",
            "field_arabic_attrs_map": {"fath": "فتح", "dam": "ضم"},
        },
        description="The vowel movement of the letter 'Dhad' (ض) (whether with `fath` or `dam`) in the word {ضعف} in Surah Ar-Rum.",
    )
    alif_salasila: Literal["hadhf", "ithbat", "wasl"] = Field(
        default="wasl",
        json_schema_extra={
            "field_arabic_name": "إثبات الألف وحذفها وقفا في قوله تعالى: {سلاسلا} بسورة الإنسان",
            "field_arabic_attrs_map": {
                "hadhf": "حذف",
                "ithbat": "إثبات",
                "wasl": "وصل",
            },
        },
        description="Affirmation and omission of the 'Alif' when pausing in the verse {سلاسلا} in Surah Al-Insan."
        "This refers to the recitation rule regarding whether the final"
        ' "Alif" in the word "سلاسلا" is pronounced (affirmed) or omitted'
        " when pausing (waqf) at this word during recitation in the specific"
        " verse from Surah Al-Insan."
        " `hadhf`: means to remove alif (ا) during puase as (سلاسل)"
        " `ithbat`: means to recite alif (ا) during puase as (سلاسلا)"
        " `wasl` means completing the recitation as normal without pausing"
        ", so recite it as (سلاسلَ وأغلالا)",
    )
    idgham_nakhluqkum: Literal["idgham_naqis", "idgham_kamil"] = Field(
        default="idgham_kamil",
        json_schema_extra={
            "field_arabic_name": "إدغام القاف في الكاف إدغاما ناقصا أو كاملا {نخلقكم} بالمرسلات",
            "field_arabic_attrs_map": {
                "idgham_kamil": "إدغام كامل",
                "idgham_naqis": "إدغام ناقص",
            },
        },
        description="Assimilation of the letter 'Qaf' into the letter 'Kaf,' whether incomplete (`idgham_naqis`) or complete (`idgham_kamil`), in the verse {نخلقكم} in Surah Al-Mursalat.",
    )
    raa_firq: Literal["waqf", "tafkheem", "tarqeeq"] = Field(
        default="tafkheem",
        json_schema_extra={
            "field_arabic_name": "التفخيم والترقيق في راء {فرق} في الشعراء وصلا",
            "field_arabic_attrs_map": {
                "waqf": "وقف",
                "tafkheem": "تفخيم",
                "tarqeeq": "ترقيق",
            },
        },
        description="Emphasis and softening of the letter 'Ra' in the word {فرق} in Surah Ash-Shu'ara' when connected (wasl)."
        "This refers to the recitation rules concerning whether the"
        ' letter "Ra" (ر) in the word "فرق"  is pronounced with'
        " emphasis (`tafkheem`) or softening (`tarqeeq`) when reciting the"
        " specific verse from Surah Ash-Shu'ara' in connected speech."
        " `waqf`: means pasuing so we only have one way (tafkheem of Raa)",
    )
    raa_alqitr: Literal["wasl", "tafkheem", "tarqeeq"] = Field(
        default="wasl",
        json_schema_extra={
            "field_arabic_name": "التفخيم والترقيق في راء {القطر} في سبأ وقفا",
            "field_arabic_attrs_map": {
                "wasl": "وصل",
                "tafkheem": "تفخيم",
                "tarqeeq": "ترقيق",
            },
        },
        description="Emphasis and softening of the letter 'Ra' in the word {القطر} in Surah Saba' when pausing (waqf)."
        'This refers to the recitation rules regarding whether the letter "Ra"'
        ' (ر) in the word "القطر" is pronounced with emphasis'
        " (`tafkheem`) or softening (`tarqeeq`) when pausing at this word in Surah Saba'."
        " `wasl`: means not pasuing so we only have one way (tarqeeq of Raa)",
    )
    raa_misr: Literal["wasl", "tafkheem", "tarqeeq"] = Field(
        default="wasl",
        json_schema_extra={
            "field_arabic_name": "التفخيم والترقيق في راء {مصر} في يونس وموضعي يوسف والزخرف  وقفا",
            "field_arabic_attrs_map": {
                "wasl": "وصل",
                "tafkheem": "تفخيم",
                "tarqeeq": "ترقيق",
            },
        },
        description="Emphasis and softening of the letter 'Ra' in the word {مصر} in Surah Yunus, and in the locations of Surah Yusuf and Surah Az-Zukhruf when pausing (waqf)."
        'This refers to the recitation rules regarding whether the letter "Ra"'
        ' (ر) in the word "مصر" is pronounced with emphasis (`tafkheem`)'
        " or softening (`tarqeeq`) at the specific pauses in these Surahs."
        " `wasl`: means not pasuing so we only have one way (tafkheem of Raa)",
    )
    raa_nudhur: Literal["wasl", "tafkheem", "tarqeeq"] = Field(
        default="tafkheem",
        json_schema_extra={
            "field_arabic_name": "التفخيم والترقيق  في راء {نذر} بالقمر وقفا",
            "field_arabic_attrs_map": {
                "wasl": "وصل",
                "tafkheem": "تفخيم",
                "tarqeeq": "ترقيق",
            },
        },
        description="Emphasis and softening of the letter 'Ra' in the word {نذر} in Surah Al-Qamar when pausing (waqf)."
        'This refers to the recitation rules regarding whether the letter "Ra"'
        ' (ر) in the word "نذر" is pronounced with emphasis (`tafkheem`)'
        " or softening (`tarqeeq`) when pausing at this word in Surah Al-Qamar."
        " `wasl`: means not pasuing so we only have one way (tarqeeq of Raa)",
    )
    raa_yasr: Literal["wasl", "tafkheem", "tarqeeq"] = Field(
        default="tarqeeq",
        json_schema_extra={
            "field_arabic_name": "التفخيم والترقيق في راء {يسر} بالفجر و{أن أسر} بطه والشعراء و{فأسر} بهود والحجر والدخان  وقفا",
            "field_arabic_attrs_map": {
                "wasl": "وصل",
                "tafkheem": "تفخيم",
                "tarqeeq": "ترقيق",
            },
        },
        description="Emphasis and softening of the letter 'Ra' in the word {يسر} in Surah Al-Fajr when pausing (waqf)."
        'This refers to the recitation rules regarding whether the letter "Ra"'
        ' (ر) in the word "يسر" is pronounced with emphasis (`tafkheem`)'
        " or softening (`tarqeeq`) when pausing at this word in Surah Al-Fajr."
        " `wasl`: means not pasuing so we only have one way (tarqeeq of Raa)",
    )
    meem_mokhfah: Literal["meem", "ikhfaa"] = Field(
        default="ikhfaa",
        json_schema_extra={
            "field_arabic_name": "هل الميم مخفاة أو مدغمة",
            "field_arabic_attrs_map": {
                "meem": "ميم",
                "ikhfaa": "إخفاء",
            },
        },
        description="This is not a standrad Hafs way but a disagreement between schoolars in our century how to pronounc Ikhfaa for meem. Some schoolars do full merging `إدام` and the other open the leaps a little bit `إخفاء`. We did not want to add this but some of the best reciters disagree about this",
    )

    @model_validator(mode="after")
    def check_madd_alleen(self) -> Self:
        if self.madd_alleen_len > self.madd_aared_len:
            raise ValueError(
                f"مد  اللين يجب أن يكون أقل من أو يساوي مد العارض للسكون. مد العارض ({self.madd_aared_len})و مد اللين ({self.madd_alleen_len})."
            )
        return self

    def model_post_init(self, *args, **kwargs):
        if self.madd_alleen_len is None:
            self.madd_alleen_len = self.madd_aared_len

    @classmethod
    def generate_docs(cls) -> str:
        """Generates documentations for the Qura'anic Fields"""
        md_table = "|Attribute Name|Arabic Name|Values|Default Value|More Info|"
        md_table += "\n" + "|-" * 5 + "|" + "\n"

        for fieldname, fieldinfo in cls.model_fields.items():
            docs = get_moshaf_field_docs(fieldname, fieldinfo)
            if not docs:
                continue
            md_table += "|"
            md_table += docs.english_name + "|"
            md_table += docs.arabic_name + "|"

            # Values
            for en, ar in docs.english2arabic_map.items():
                if en == ar:
                    md_table += f"- `{en}`<br>"
                else:
                    md_table += f"- `{en}` (`{ar}`)<br>"
            md_table += "|"

            # Default Value
            if fieldinfo.default == PydanticUndefined:
                md_table += "|"
            else:
                if fieldinfo.default is None:
                    md_table += "`None`|"
                else:
                    ar_val = docs.english2arabic_map[fieldinfo.default]
                    if ar_val == fieldinfo.default:
                        md_table += f"`{ar_val}`|"
                    else:
                        md_table += f"`{fieldinfo.default}` (`{ar_val}`)|"

            md_table += docs.more_info + "|"

            md_table += "\n"

        return md_table
