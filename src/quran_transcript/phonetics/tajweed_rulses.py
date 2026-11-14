from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from enum import IntEnum, auto
from typing import Literal, Optional, TypeAlias

from .. import alphabet as alph
from ..alphabet import MultiLangText


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


@dataclass
class TajweedRuleMetadata:
    """The Tajweed rule poition in phonetic script space (not uthmani space)"""

    pivot: tuple[int, int]
    deps: list[tuple[int, int]]
    tag: str
    rule_type: TajweedRuleType
    uth_pivot: tuple[int, int] = (-1, -1)
    uth_deps: list[tuple[int, int]] = field(default_factory=list)
    golden_len: int = -1

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

        self.uth_pivot = (ph_to_uth[self.pivot[0]], ph_to_uth[self.pivot[1]])
        uth_deps = []
        for ph_start, ph_end in self.deps:
            uth_deps.append((ph_to_uth[ph_start], ph_to_uth[ph_end]))
        self.uth_deps = uth_deps

    def set_golden_len(self, val: int) -> None:
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

    def count(self, ref_text: str, pred_text: str) -> int:
        return 0

    def match(self, ref_text: str, pred_text: str) -> bool:
        return True


FullTajweedRuleType: TypeAlias = tuple[TajweedRule, TajweedRuleMetadata]


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
class NormalMaddRule(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.NORMAL_MADD


@dataclass
class SkoonMostadeerDelete(MaddRule):
    name: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    description: MultiLangText = MultiLangText(
        ar="",
        en="",
    )
    rule_type: TajweedRuleType = TajweedRuleType.SKOON_MOSTADEER_DELETE
    correctness: CorrectnessType = "descriptive"


#
#
# @dataclass
# class MonfaselMaddRule(MaddRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="المد المنفصل", en="Monfasel Madd")
#     )
#     golden_len: int = 4
#
#
# @dataclass
# class MottaselMaddPauseRule(MaddRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="المد المتصل وقفا", en="Mottasel Madd at Pause"
#         )
#     )
#     golden_len: int = 4
#
#
# @dataclass
# class MottaselMaddRule(MaddRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="المد المتصل", en="Mottasel Madd")
#     )
#     golden_len: int = 4
#
#
# @dataclass
# class LazemMaddRule(MaddRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="المد اللازم", en="Lazem Madd")
#     )
#     golden_len: int = 6
#
#
# @dataclass
# class AaredMaddRule(MaddRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="المد العارض للسكون", en="Aared Madd")
#     )
#     golden_len: int = 4
#
#
# @dataclass
# class LeenMaddRule(MaddRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="مد اللين", en="Leen Madd")
#     )
#     golden_len: int = 4
#
#     def __post_init__(self):
#         self.available_tags = {"waw", "yaa"}
#         super().__post_init__()
#         self._madd_to_tag = {
#             alph.phonetics.waw: "waw",
#             alph.phonetics.yaa: "yaa",
#         }
#         assert self.tag in self.available_tags
#
#     def count(self, ref_text, pred_text) -> int:
#         # The case where we have Tashkeel after madd (Error from the model)
#         if pred_text[-1] != pred_text[0]:
#             return pred_text[:-1].count(ref_text[0]) + 1
#         else:
#             return pred_text.count(ref_text[0]) + 1
#
#
# @dataclass
# class IdghamKamel(TajweedRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(ar="إدغام كامل", en="Full Merging")
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
#         return None
#
#
# @dataclass
# class NoonOrMeemRuleMetadata:
#     name: MultiLangText
#     tag: str
#     offset: int = 0
#     golden_len: int = 4
#
#
# @dataclass
# class NoonOrMeemRule(TajweedRule):
#     name: MultiLangText
#     golden_len: int
#     offset: int = 0
#     correctness_type: Literal["match", "count"] = "count"
#
#     # TODO:
#     # * [ ] Add post_init that red the tag Literal and assign it to the avaialbe_tags class field
#
#     def __post_init__(self):
#         self.available_tags = {
#             "noon_izhar",
#             "noon",
#             "noon_yaa",
#             "noon_waw",
#             "noon_mokhfah",
#             "meem_izhar",
#             "meem",
#             "meem_mokhfah",
#         }
#         super().__post_init__()
#         self._ph_to_metadata: dict[str, list[NoonOrMeemRuleMetadata]] = {
#             alph.phonetics.noon: [
#                 NoonOrMeemRuleMetadata(
#                     name=field(
#                         default_factory=lambda: MultiLangText(
#                             ar="النون المشددة أو المدغمة", en="Moshadad or Modgham Noon"
#                         )
#                     ),
#                     tag="noon",
#                     offset=0,
#                 )
#             ],
#             alph.phonetics.yaa: [
#                 NoonOrMeemRuleMetadata(
#                     name=field(default_factory=lambda: MultiLangText(ar="", en="")),
#                     tag="noon_yaa",
#                     offset=1,
#                 )
#             ],
#             alph.phonetics.waw: [
#                 NoonOrMeemRuleMetadata(
#                     name=field(default_factory=lambda: MultiLangText(ar="", en="")),
#                     tag="noon_waw",
#                     offset=1,
#                 )
#             ],
#             alph.phonetics.noon_mokhfah: [
#                 NoonOrMeemRuleMetadata(
#                     name=field(default_factory=lambda: MultiLangText(ar="", en="")),
#                     tag="noon_mokhfah",
#                     offset=1,
#                 )
#             ],
#             alph.phonetics.meem: [
#                 NoonOrMeemRuleMetadata(
#                     name=field(default_factory=lambda: MultiLangText(ar="", en="")),
#                     tag="meem",
#                     offset=0,
#                 )
#             ],
#             alph.phonetics.meem_mokhfah: [
#                 NoonOrMeemRuleMetadata(
#                     name=field(default_factory=lambda: MultiLangText(ar="", en="")),
#                     tag="meem_mokhfah",
#                     offset=0,
#                 )
#             ],
#         }
#
#     def count(self, ref_text, pred_text) -> int:
#         return pred_text.count(ref_text[0]) + self.offset
#
#     def is_ph_str_in(self, ph_str: str) -> bool:
#         """Whether the phonetic script is assoicated with this Tajweed rule or not"""
#         if ph_str:
#             return ph_str[0] in self._ph_to_metadata
#         else:
#             return False
#
#     def get_relvant_rule(self, ph_str: str) -> Optional["TajweedRule"]:
#         """Returs a Tajweed rule that is assocaited with the input ph_str"""
#         if not ph_str:
#             return None
#         elif ph_str[0] not in self._ph_to_metadata:
#             return None
#         return replace(
#             self,
#             name=self._ph_to_metadata[ph_str[0]].name,
#             offset=self._ph_to_metadata[ph_str[0]].offset,
#             tag=self._ph_to_metadata[ph_str[0]].tag,
#         )
#
#
# @dataclass
# class IzharHalqy(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="الإظهار الحلقي",
#             en="Al-Izhar Al-Halqi for Sakin Noon and Tanween",
#         )
#     )
#     golden_len: int = 1
#     offset: int = 0
#     tag: str = "noon_izhar"
#
#
# @dataclass
# class IdghamWithGunnah(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="إدغام بغنة",
#             en="Idgham with Ghunnah",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 0
#     tag: Literal["yaa", "waw", "meem", "noon"] = "noon"
#
#     def __post_init__(self):
#         if self.tag in {"yaa", "waw"}:
#             self.offset = 1
#         else:
#             self.offset = 0
#
#
# @dataclass
# class Iqlab(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="إقلاب",
#             en="Iqlab",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 1
#     tag: Literal["meem", "meem_mokhfah"] = "meem_mokhfah"
#
#
# @dataclass
# class Ikhfaa(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="إخفاء",
#             en="Ikfaa",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 1
#     tag: str = "noon_mokhfah"
#
#
# @dataclass
# class NoonWithShaddah(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="نون مشددة",
#             en="Noom Mushaddadah",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 0
#     tag: str = "noon"
#
#
# @dataclass
# class MeemWithShaddah(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="ميم مشددة",
#             en="Noom Mushaddadah",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 0
#     tag: str = "meem"
#
#
# @dataclass
# class IzharShafawy(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="الإظهار شفوي",
#             en="Al-Izhar Al-Shafawy for Sakin Meem",
#         )
#     )
#     golden_len: int = 1
#     offset: int = 0
#     tag: str = "meem_izhar"
#
#
# @dataclass
# class IkhfaaShafawy(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="إخفاء شفوي",
#             en="Ikfaa Shafawy for Sakin Meem",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 1
#     tag: Literal["meem", "meem_mokhfah"] = "meem_mokhfah"
#
#
# @dataclass
# class IdghamSakinMeem(NoonOrMeemRule):
#     name: MultiLangText = field(
#         default_factory=lambda: MultiLangText(
#             ar="إدغام مثلين صغير بغنة للميم الساكنة",
#             en="Idgham for Sakin Meem",
#         )
#     )
#     golden_len: int = 4
#     offset: int = 0
#     tag: str = "meem"


TAJ_TYPE_TO_RULE = {
    TajweedRuleType.NORMAL_MADD: NormalMaddRule(),
    TajweedRuleType.SKOON_MOSTADEER_DELETE: SkoonMostadeerDelete(),
}
