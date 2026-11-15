from abc import ABC
from dataclasses import dataclass, field, replace
from enum import IntEnum, auto
from typing import Literal, TypeAlias

from ..alphabet import MultiLangText
from ..alphabet import phonetics as ph


class TajweedRuleType(IntEnum):
    NORMAL_MADD = auto()
    LAZIM_MADD = auto()
    ELEWAD_MADD = auto()
    MONFASEL_MADD = auto()
    MOTTASEL_MADD = auto()
    LEEN_MADD = auto()
    AARED_MADD = auto()

    SKOON_MOSTADEER_DELETE = auto()
    SKOON_MOSTATEEL_MID_DELETE = auto()
    SKOON_MOSTATEEL_END_ADD = auto()

    TANWEEN_FATH_MID_DELETE = auto()
    TANWEEN_FATAH_FOR_HAA_TANEETH_PAUSE = auto()

    # النون الساكنة والتنوين
    IZHAR_NOON = auto()
    IDGHAM_GONNAH_NOON = auto()
    IQLAB_NOON = auto()
    IKHFAA_NOON = auto()

    # الميم الساكنة
    IZHAR_MEEM = auto()
    IDGHAM_MEEM = auto()
    IKHFAA_MEEM = auto()

    # النون والميم المشددتين
    MOSHADAD_NOON = auto()
    MOSHADAD_MEEM = auto()

    IDGHAM_KAMEL = auto()

    # التقاء الساكنين
    KASR_TANWEEN_ILTIQAA_SAKENAYN = auto()
    DELETE_FIRST_ILTIQAA_SAKENAYN = auto()

    TASHEEL = auto()

    QALQALAH = auto()

    HAMZAT_WASL_DELETE = auto()
    KASR_NOUNS_HAMZAT_WASL = auto()
    KASR_VERB_HAMZAT_WASL = auto()
    DAM_VERB_HAMZAT_WASL = auto()
    FATH_ALL_HAMZAT_WASL = auto()
    ILTIQAA_HAMZATAN_SECOND_MADD_YAA = auto()
    ILTIQAA_HAMZATAN_SECOND_MADD_WAW = auto()


def _ph_span_to_uth(ph_to_uth: list[int], start: int, end: int) -> tuple[int, int]:
    """Convert a half-open phonetic span to a half-open Uthmani span."""
    if start == end:
        idx = ph_to_uth[start]
        return (idx, idx)
    return (ph_to_uth[start], ph_to_uth[end - 1] + 1)


@dataclass
class TajweedRuleMetadata:
    """The Tajweed rule poition in phonetic script space (not uthmani space)"""

    pivot: tuple[int, int]
    deps: list[tuple[int, int]]
    tag: str
    rule_type: TajweedRuleType
    uth_pivot: tuple[int, int] = (-1, -1)
    uth_deps: list[tuple[int, int]] = field(default_factory=list)
    golden_len: float = -1

    def update_pivot_start(self, x: int) -> None:
        self.pivot = (x, self.pivot[1])

    def update_pivot_end(self, x: int) -> None:
        self.pivot = (self.pivot[0], x)

    def update_dep_start(self, dep_idx, x: int) -> None:
        self.deps[dep_idx] = (x, self.deps[dep_idx][1])

    def update_dep_end(self, dep_idx, x: int) -> None:
        self.deps[dep_idx] = (self.deps[dep_idx][0], x)

    def fill_uth(self, ph_to_uth: list[int]) -> None:
        """thie method is expected be called after finishing all operations
        it fills the uth_pivot and uth_deps"""

        # TODO: check delete ids
        # self.uth_pivot = _ph_span_to_uth(ph_to_uth, *self.pivot)
        self.uth_pivot = _ph_span_to_uth(ph_to_uth, *self.pivot)
        uth_deps = []
        for ph_start, ph_end in self.deps:
            # TODO: check delete ids
            # uth_deps.append(_ph_span_to_uth(ph_to_uth, ph_start, ph_end))
            uth_deps.append(_ph_span_to_uth(ph_to_uth, ph_start, ph_end))
        self.uth_deps = uth_deps

    def set_golden_len(self, val: float) -> None:
        self.golden_len = val

    def set_tag(self, tag: str) -> None:
        """Set the tag of the Tajweed rule"""
        self.tag = tag


CorrectnessType: TypeAlias = Literal["match", "count", "descriptive"]


@dataclass
class TajweedRule(ABC):
    """
    to_overwrite_tajweed_rules: if a rule in the future occpy in the same span ignore the new rule in the `to_overwrite_tajweed_rules` and keep the old rule
    Attributes:

    pivot_uth_idx (int): the int idx of the uthmani charcahter that corresponds to the Tajweed Rule
    dep_uth_ids (list[tuple[int, int]]): A list of uthmani text positon that affects the Tajweed rule each item is
    a tuple of (start, end). If start == end then the Tajweed rule depends on Pause (Waqf) or (وقف) in Arabic
    """

    # fixed fields
    name: MultiLangText
    description: MultiLangText
    rule_type: TajweedRuleType
    correctness: CorrectnessType

    def count(self, ref_text: str, pred_text: str) -> int | float:
        return 0

    def match(self, ref_text: str, pred_text: str) -> bool:
        return ref_text == pred_text


FullTajweedRuleType: TypeAlias = tuple[TajweedRule, TajweedRuleMetadata]


@dataclass(frozen=True)
class ExplainedTajweedRule:
    """A pure, serializable snapshot of a Tajweed rule and its metadata.

    This is intentionally a plain data struct used in the final error output.
    The original :class:`TajweedRule` keeps all behavior (``count``/``match``);
    this class only carries the fields needed to display or serialize a rule.
    """

    name: MultiLangText
    description: MultiLangText
    rule_type: TajweedRuleType
    correctness: CorrectnessType
    ph_pivot: tuple[int, int]
    ph_deps: list[tuple[int, int]]
    tag: str
    uth_pivot: tuple[int, int]
    uth_deps: list[tuple[int, int]]
    golden_len: int

    @classmethod
    def from_(
        cls,
        rule: TajweedRule,
        meta: TajweedRuleMetadata,
    ) -> "ExplainedTajweedRule":
        """Build a plain snapshot from a rule and its metadata."""
        return cls(
            name=replace(rule.name),
            description=replace(rule.description),
            rule_type=rule.rule_type,
            correctness=rule.correctness,
            ph_pivot=meta.pivot,
            ph_deps=list(meta.deps),
            tag=meta.tag,
            uth_pivot=meta.uth_pivot,
            uth_deps=list(meta.uth_deps),
            golden_len=meta.golden_len,
        )


# @dataclass
# class Qalqalah(TajweedRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="قلقة", en="Qalqalah")
#     )
#     golden_len: int = 0
#     correctness_type: Literal["match", "count"] = "match"
#
#     def match(self, ref_text, pred_text) -> bool:
#         return ref_text == pred_text
#
#     def is_ph_str_in(self, ph_str: str) -> bool:
#         """Whether the phonetic script is assoicated with this Tajweed rule or not"""
#         return True
#
#     def get_relvant_rule(self, ph_str: str) -> Optional["TajweedRule"]:
#         """Returs a Tajweed rule that is assocaited with the input ph_str"""
#         if not ph_str:
#             return None
#         elif ph_str[-1] == alph.phonetics.qlqla:
#             return self
#         else:
#             return None
#
#
@dataclass
class MaddRule(TajweedRule):
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> int:
        assert ref_text[0] == pred_text[0]
        return len(pred_text)


@dataclass
class DescriptiveTajweedRule(TajweedRule):
    """Base for rules that are tagged but do not have correction behavior yet."""

    correctness: CorrectnessType = "descriptive"


@dataclass
class NormalMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="المد الطبيعي",
        en="Normal Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.NORMAL_MADD


@dataclass
class LazimMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="المد اللازم",
        en="Lazem Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.LAZIM_MADD


@dataclass
class ElewadMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="مد العوض",
        en="Iwad Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.ELEWAD_MADD


@dataclass
class MonfaselMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="المد المنفصل",
        en="Monfasel Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.MONFASEL_MADD


@dataclass
class MottaselMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="المد المتصل",
        en="Mottasel Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.MOTTASEL_MADD


@dataclass
class AaredMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="المد العارض للسكون",
        en="Aared Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.AARED_MADD


@dataclass
class LeenMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="مد اللين",
        en="Leen Madd",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.LEEN_MADD

    def count(self, ref_text: str, pred_text: str) -> int:
        assert ref_text[0] == pred_text[0]
        return len(pred_text) + 1


@dataclass
class SkoonMostadeerDeleteRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="حذف السكون المستدير",
        en="Skoon Mostadeer Delete",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.SKOON_MOSTADEER_DELETE


@dataclass
class SkoonMostateelMidDeleteRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="حذف السكون المستطيل في الوسط",
        en="Skoon Mostateel Mid Delete",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.SKOON_MOSTATEEL_MID_DELETE


@dataclass
class SkoonMostateelEndAddRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إثبات الألف وقفا في الألفات السبعة",
        en="Ithbat mad alif of the seven alifs at puase",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.SKOON_MOSTATEEL_END_ADD


@dataclass
class TanweenFathMidDeleteRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="حذف تنوين الفتح في الوسط",
        en="Tanween Fath Mid Delete",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.TANWEEN_FATH_MID_DELETE


@dataclass
class TanweenFatahForHaaTaneethPauseRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="حذف تنوين الفتح لهاء التأنيث وقفاً",
        en="Delete Tanween Fatah for Haa Taneeth at Pause",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.TANWEEN_FATAH_FOR_HAA_TANEETH_PAUSE


@dataclass
class IzharNoonRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="الإظهار الحلقي",
        en="Al-Izhar Al-Halqi for Sakin Noon and Tanween",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IZHAR_NOON
    correctness: CorrectnessType = "match"


@dataclass
class IdghamGonnahNoonRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إدغام بغنة",
        en="Idgham with Ghunnah",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IDGHAM_GONNAH_NOON
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> float:
        # TODO: needs rewrite for haraka errors
        assert ref_text[0] == pred_text[0]
        if ref_text[0] in {ph.yaa, ph.waw}:
            return len(pred_text) / 2
        else:
            return (len(pred_text) - 1) / 2


@dataclass
class IqlabNoonRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إقلاب",
        en="Iqlab",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IQLAB_NOON
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> float:
        assert ref_text[0] == pred_text[0]
        if ref_text[0] == ph.meem_mokhfah:
            return (len(pred_text) + 1) / 2
        else:
            return len(pred_text) / 2


@dataclass
class IkhfaaNoonRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إخفاء حقيقي",
        en="Ikhfaa Haqiqy",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IKHFAA_NOON
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> float:
        assert ref_text[0] == pred_text[0]
        return (len(pred_text) + 1) / 2


@dataclass
class IzharMeemRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="الإظهار الشفوي",
        en="Al-Izhar Al-Shafawy for Sakin Meem",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IZHAR_MEEM
    correctness: CorrectnessType = "match"


@dataclass
class IdghamMeemRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إدغام الميم الساكنة",
        en="Idgham for Sakin Meem",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    correctness: CorrectnessType = "count"
    rule_type: TajweedRuleType = TajweedRuleType.IDGHAM_MEEM

    def count(self, ref_text: str, pred_text: str) -> float:
        assert ref_text[0] == pred_text[0]
        return len(pred_text) / 2


@dataclass
class IkhfaaMeemRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إخفاء شفوي",
        en="Ikhfaa Shafawy for Sakin Meem",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IKHFAA_MEEM
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> float:
        assert ref_text[0] == pred_text[0]
        if ref_text[0] == ph.meem_mokhfah:
            return (len(pred_text) + 1) / 2
        else:
            return len(pred_text) / 2


@dataclass
class MoshadadNoonRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="نون مشددة",
        en="Noon Mushaddadah",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.MOSHADAD_NOON
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> float:
        assert ref_text[0] == pred_text[0]
        return len(pred_text) / 2


@dataclass
class MoshadadMeemRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="ميم مشددة",
        en="Meem Mushaddadah",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.MOSHADAD_MEEM
    correctness: CorrectnessType = "count"

    def count(self, ref_text: str, pred_text: str) -> float:
        assert ref_text[0] == pred_text[0]
        return len(pred_text) / 2


@dataclass
class IdghamKamelRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="إدغام كامل",
        en="Full Merging",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.IDGHAM_KAMEL
    correctness: CorrectnessType = "match"


@dataclass
class KasrTanweenIltiqaaSakenaynRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="كسر التنوين لالتقاء الساكنين",
        en="Kasr Tanween for Iltiqaa Sakenayn",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.KASR_TANWEEN_ILTIQAA_SAKENAYN
    correctness: CorrectnessType = "match"


@dataclass
class DeleteFirstIltiqaaSakenaynRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="حذف الأول لالتقاء الساكنين",
        en="Delete First for Iltiqaa Sakenayn",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.DELETE_FIRST_ILTIQAA_SAKENAYN


@dataclass
class TasheelRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="تسهيل",
        en="Tasheel",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.TASHEEL
    correctness: CorrectnessType = "match"


@dataclass
class QalqalahRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="قلقلة",
        en="Qalqalah",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.QALQALAH
    correctness: CorrectnessType = "match"


@dataclass
class HamzatWaslDeleteRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="حذف همزة الوصل وصلا",
        en="Hamzat Wasl Delete on Pause",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.HAMZAT_WASL_DELETE


@dataclass
class KasrNounsHamzatWaslRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="كسر همزة الوصل في الأسماء",
        en="Kasr Hamzat Wasl in Nouns",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.KASR_NOUNS_HAMZAT_WASL


@dataclass
class KasrVerbHamzatWaslRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="كسر همزة الوصل في الأفعال",
        en="Kasr Hamzat Wasl in Verbs",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.KASR_VERB_HAMZAT_WASL


@dataclass
class DamVerbHamzatWaslRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="ضم همزة الوصل في الأفعال",
        en="Dam Hamzat Wasl in Verbs",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.DAM_VERB_HAMZAT_WASL


@dataclass
class FathAllHamzatWaslRule(DescriptiveTajweedRule):
    name: MultiLangText = MultiLangText(
        ar="فتح همزة الوصل",
        en="Fath Hamzat Wasl",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.FATH_ALL_HAMZAT_WASL


@dataclass
class IltiqaaHamzatanSecondMaddYaaRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="مد الياء لالتقاء الهمزتين",
        en="Iltiqaa Hamzatan Second Madd Yaa",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.ILTIQAA_HAMZATAN_SECOND_MADD_YAA
    correctness: CorrectnessType = "match"


@dataclass
class IltiqaaHamzatanSecondMaddWawRule(TajweedRule):
    name: MultiLangText = MultiLangText(
        ar="مد الواو لالتقاء الهمزتين",
        en="Iltiqaa Hamzatan Second Madd Waw",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.ILTIQAA_HAMZATAN_SECOND_MADD_WAW
    correctness: CorrectnessType = "match"


TAJ_TYPE_TO_RULE = {
    TajweedRuleType.NORMAL_MADD: NormalMaddRule(),
    TajweedRuleType.LAZIM_MADD: LazimMaddRule(),
    TajweedRuleType.ELEWAD_MADD: ElewadMaddRule(),
    TajweedRuleType.MONFASEL_MADD: MonfaselMaddRule(),
    TajweedRuleType.MOTTASEL_MADD: MottaselMaddRule(),
    TajweedRuleType.LEEN_MADD: LeenMaddRule(),
    TajweedRuleType.AARED_MADD: AaredMaddRule(),
    TajweedRuleType.SKOON_MOSTADEER_DELETE: SkoonMostadeerDeleteRule(),
    TajweedRuleType.SKOON_MOSTATEEL_MID_DELETE: SkoonMostateelMidDeleteRule(),
    TajweedRuleType.SKOON_MOSTATEEL_END_ADD: SkoonMostateelEndAddRule(),
    TajweedRuleType.TANWEEN_FATH_MID_DELETE: TanweenFathMidDeleteRule(),
    TajweedRuleType.TANWEEN_FATAH_FOR_HAA_TANEETH_PAUSE: (
        TanweenFatahForHaaTaneethPauseRule()
    ),
    TajweedRuleType.IZHAR_NOON: IzharNoonRule(),
    TajweedRuleType.IDGHAM_GONNAH_NOON: IdghamGonnahNoonRule(),
    TajweedRuleType.IQLAB_NOON: IqlabNoonRule(),
    TajweedRuleType.IKHFAA_NOON: IkhfaaNoonRule(),
    TajweedRuleType.IZHAR_MEEM: IzharMeemRule(),
    TajweedRuleType.IDGHAM_MEEM: IdghamMeemRule(),
    TajweedRuleType.IKHFAA_MEEM: IkhfaaMeemRule(),
    TajweedRuleType.MOSHADAD_NOON: MoshadadNoonRule(),
    TajweedRuleType.MOSHADAD_MEEM: MoshadadMeemRule(),
    TajweedRuleType.IDGHAM_KAMEL: IdghamKamelRule(),
    TajweedRuleType.KASR_TANWEEN_ILTIQAA_SAKENAYN: KasrTanweenIltiqaaSakenaynRule(),
    TajweedRuleType.DELETE_FIRST_ILTIQAA_SAKENAYN: DeleteFirstIltiqaaSakenaynRule(),
    TajweedRuleType.TASHEEL: TasheelRule(),
    TajweedRuleType.QALQALAH: QalqalahRule(),
    TajweedRuleType.HAMZAT_WASL_DELETE: HamzatWaslDeleteRule(),
    TajweedRuleType.KASR_NOUNS_HAMZAT_WASL: KasrNounsHamzatWaslRule(),
    TajweedRuleType.KASR_VERB_HAMZAT_WASL: KasrVerbHamzatWaslRule(),
    TajweedRuleType.DAM_VERB_HAMZAT_WASL: DamVerbHamzatWaslRule(),
    TajweedRuleType.FATH_ALL_HAMZAT_WASL: FathAllHamzatWaslRule(),
    TajweedRuleType.ILTIQAA_HAMZATAN_SECOND_MADD_YAA: (
        IltiqaaHamzatanSecondMaddYaaRule()
    ),
    TajweedRuleType.ILTIQAA_HAMZATAN_SECOND_MADD_WAW: (
        IltiqaaHamzatanSecondMaddWawRule()
    ),
}

assert set(TAJ_TYPE_TO_RULE) == set(TajweedRuleType)


def get_full_taj_rule_type(
    taj_rule_meta: TajweedRuleMetadata,
    ph_to_uth: list[int],
) -> FullTajweedRuleType:
    """Resolve a rule metadata into its rule object and fill Uthmani positions.

    The metadata is copied before ``fill_uth`` so callers can reuse the raw
    metadata safely.
    """
    taj_rule_meta = replace(taj_rule_meta)
    taj_rule_meta.fill_uth(ph_to_uth)
    taj_rule = TAJ_TYPE_TO_RULE[taj_rule_meta.rule_type]

    if taj_rule.correctness == "count":
        # For count we have either madd or gonnah
        golden_len = taj_rule_meta.pivot[1] - taj_rule_meta.pivot[0]
        if isinstance(taj_rule, MaddRule):
            # The madd letters are what this rule is counting. Leen madd
            # counts the preceding yaa/waw in addition to the inserted ones.
            if taj_rule_meta.rule_type == TajweedRuleType.LEEN_MADD:
                golden_len += 1
            taj_rule_meta.set_golden_len(golden_len)
        else:
            # Gonnah related rules
            if golden_len == 3:
                golden_len += 1
            taj_rule_meta.set_golden_len(golden_len // 2)
    return (taj_rule, taj_rule_meta)
