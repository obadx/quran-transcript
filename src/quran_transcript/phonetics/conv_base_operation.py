from dataclasses import dataclass, field
import re
from typing import Literal
from enum import StrEnum

from .moshaf_attributes import MoshafAttributes
from .tajweed_rulses import TajweedRule


@dataclass
class MappingPos:
    pos: tuple[int, int]
    tajweed_rules: list[TajweedRule] | None = None


class FilterTages(StrEnum):
    # المدود
    MADD = "مد"
    MADD_NORMAL = "مد طبيعي"
    MADD_EWAD = ""
    MADD_MONFASel = ""
    MADD_MOTTASel = ""
    MADD_LAZEM = ""
    MADD_MOTTASEL_PUASE = ""
    MADD_ARRED = ""


@dataclass
class SubOperation:
    tags: list[FilterTages] = field(default_factory=lambda: [])


@dataclass
class ConversionOperation:
    regs: list[tuple[str, str]] | tuple[str, str]
    arabic_name: str
    ops_before: list["ConversionOperation"] | None = None

    def __post_init__(self):
        if isinstance(self.regs, tuple):
            self.regs = [self.regs]

        if self.ops_before is None:
            self.ops_before = []

    def forward(self, text, moshaf: MoshafAttributes) -> str:
        for input_reg, out_reg in self.regs:
            text = re.sub(input_reg, out_reg, text)
        return text

    def apply(
        self,
        text: str,
        moshaf: MoshafAttributes,
        mappings: list[MappingPos | None] | None,
        discard_ops: list["ConversionOperation"] = [],
        mode: Literal["inference", "test"] = "inference",
    ) -> tuple[str, list[MappingPos | None]]:
        if mode == "test":
            discard_ops_names = {o.arabic_name for o in discard_ops}
            for op in self.ops_before:
                if op.arabic_name not in discard_ops_names:
                    print(f"Applying: {type(op)}")
                    text, mappings = op.apply(
                        text, moshaf, mappings, mode="test", discard_ops=discard_ops
                    )

        if mode in {"inference", "test"}:
            # TODO: Add real mapping
            return self.forward(text, moshaf), mappings
        else:
            raise ValueError(f"Invalid Model got: `{mode}`")
