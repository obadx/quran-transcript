from abc import abstractmethod, ABC
from typing import Literal, Optional
from dataclasses import dataclass, replace, field


from .. import alphabet as alph


@dataclass
class LangName:
    ar: str
    en: str


@dataclass
class TajweedRule(ABC):
    """
    to_overwrite_tajweed_rules: if a rule in the future occpy in the same span ignore the new rule in the `to_overwrite_tajweed_rules` and keep the old rule
    """

    name: LangName
    golden_len: int
    correctness_type: Literal["match", "count"]
    tag: Optional[str] | None = None
    available_tags: Optional[set] | None = None

    def __post_init__(self):
        if self.tag is not None and self.available_tags is not None:
            if self.tag not in self.available_tags:
                raise ValueError(
                    f"Invalid tag value: `{self.tag}`. Available ones are: `{self.available_tags}`"
                )

    def count(self, ref_text, pred_text) -> int:
        return 0

    def match(self, ref_text, pred_text) -> bool:
        return True

    @abstractmethod
    def is_ph_str_in(self, ph_str: str) -> bool:
        """Whether the phonetic script is assoicated with this Tajweed rule or not"""
        return True

    @abstractmethod
    def get_relvant_rule(self, ph_str: str) -> Optional["TajweedRule"]:
        """Returs a Tajweed rule that is assocaited with the input ph_str"""
        return self


@dataclass
class Qalqalah(TajweedRule):
    name: LangName = field(default_factory=lambda: LangName(ar="قلقة", en="Qalqalah"))
    golden_len: int = 0
    correctness_type: Literal["match", "count"] = "match"

    def is_ph_str_in(self, ph_str: str) -> bool:
        """Whether the phonetic script is assoicated with this Tajweed rule or not"""
        return True

    def get_relvant_rule(self, ph_str: str) -> Optional["TajweedRule"]:
        """Returs a Tajweed rule that is assocaited with the input ph_str"""
        return self


@dataclass
class MaddRule(TajweedRule):
    name: LangName
    golden_len: int
    correctness_type: Literal["match", "count"] = "count"

    def __post_init__(self):
        self.available_tags = {"alif", "waw", "yaa"}
        super().__post_init__()
        self._madd_to_tag = {
            alph.phonetics.alif: "alif",
            alph.phonetics.waw_madd: "waw",
            alph.phonetics.yaa_madd: "yaa",
        }

    def count(self, ref_text, pred_text) -> int:
        # The case where we have Tashkeel after madd (Error from the model)
        if pred_text[-1] != pred_text[0]:
            return pred_text[:-1].count(ref_text[0])
        else:
            return pred_text.count(ref_text[0])

    def is_ph_str_in(self, ph_str: str) -> bool:
        """Whether the phonetic script is assoicated with this Tajweed rule or not"""
        if ph_str:
            return ph_str[0] in self._madd_to_tags
        else:
            return False

    def get_relvant_rule(self, ph_str: str) -> Optional["TajweedRule"]:
        """Returs a Tajweed rule that is assocaited with the input ph_str"""
        if not ph_str:
            raise ValueError("Empty String")
        elif ph_str[0] not in self._madd_to_tag:
            return None
        return replace(self, tag=self._madd_to_tag[ph_str[0]])


@dataclass
class NormalMaddRule(MaddRule):
    name: LangName = field(
        default_factory=lambda: LangName(ar="المد الطبيعي", en="Normal Madd")
    )
    golden_len: int = 2


# TODO:

"""
* Ghonna
* Madd
* Qalaqlah
* Idgham
* Tashdeed
"""
