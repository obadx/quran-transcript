from abc import abstractmethod
from typing import Literal, Optional
from dataclasses import dataclass


from quran_transcript import chunck_phonemes
from quran_transcript import alphabet as alph
import Levenshtein as lv


@dataclass
class TajweedRule:
    name: str
    golden_len: int
    correctness_type: Literal["match", "count"]

    @abstractmethod
    def count(self, ref_text, pred_text) -> int:
        return 0

    @abstractmethod
    def match(self, ref_text, pred_text) -> bool:
        return True


@dataclass
class NormalMaddRule(TajweedRule):
    name: str = "مد طبيعي"
    golden_len: int = 2
    correctness_type: Literal["match", "count"] = "count"

    def count(self, ref_text, pred_text) -> int:
        # The case where we have Tashkeel after madd (Error from the model)
        if pred_text[-1] != pred_text[0]:
            return pred_text[:-1].count(ref_text[0])
        else:
            return pred_text.count(ref_text[0])


@dataclass
class MappingPos:
    pos: tuple[int, int]
    tajweed_rules: list[TajweedRule] | None = None


@dataclass
class ReciterError:
    uthmani_pos: tuple[int, int]  # start, end
    ph_pos: tuple[int, int]  # start, end
    error_type: Literal["tajweed", "normal", "tashkeel"]
    speech_error_type: Literal["insert", "delete", "replace"]
    expected_ph: str
    preditected_ph: str
    expected_len: Optional[int] | None = None
    predicted_len: Optional[int] | None = None
    tajweed_rules: Optional[list[TajweedRule]] | None = None


@dataclass
class PhonemesGroupsAligment:
    op_type: Literal["insert", "replace", "delete", "equal"]
    ref_idx: int
    pred_idx: int


# TODO: Testing
def align_phonemes_groups(
    ref_ph_groups: list[str], pred_ph_groups: list[str]
) -> list[PhonemesGroupsAligment]:
    ref_text = [t[0] for t in ref_ph_groups]
    pred_text = [t[0] for t in pred_ph_groups]
    out_aligments = []

    for out in lv.opcodes(ref_text, pred_text):
        # disassemble operations so every item contains a single change for a single index
        if out[0] in {"equal", "replace"}:
            for ref_start, pred_start in zip(
                range(out[1], out[2]), range(out[3], out[4])
            ):
                out_aligments.append(
                    PhonemesGroupsAligment(
                        op_type=out[0],
                        ref_idx=ref_start,
                        pred_idx=pred_start,
                    )
                )
        elif out[0] == "insert":
            for pred_start in range(out[3], out[4]):
                out_aligments.append(
                    PhonemesGroupsAligment(
                        op_type="insert",
                        ref_idx=out[1],
                        pred_idx=pred_start,
                    )
                )
        elif out[0] == "delete":
            for ref_start in range(out[1], out[2]):
                out_aligments.append(
                    PhonemesGroupsAligment(
                        op_type="delete",
                        ref_idx=ref_start,
                        pred_idx=out[3],
                    )
                )

    return out_aligments


def extract_ref_phonetic_to_uthmani(
    mappings: list[MappingPos | None],
) -> dict[int, int]:
    ref_ph_to_uthmani = {}
    for idx, map_pos in enumerate(mappings):
        if map_pos is not None:
            for ph_idx in range(*map_pos.pos):
                if ph_idx in ref_ph_to_uthmani:
                    raise ValueError(
                        f"Same phonetic scripts has multiple uthmani script. Phonetic posision: `{ph_idx}`, Uthmani Poses: `{ref_ph_to_uthmani[ph_idx]}, {idx}`"
                    )
                else:
                    ref_ph_to_uthmani[ph_idx] = idx
    return ref_ph_to_uthmani


def get_ref_phonetic_groups_tajweed_rules(
    ref_ph_groups: list[str],
    mappings: list[MappingPos | None],
    ref_ph_to_uthmani: dict[int, int],
) -> list[None | list[TajweedRule]]:
    ref_tajweed_rules = [None] * len(ref_ph_groups)
    start = 0
    end = 0
    # Computing Tajweed rules
    # TODO: O(n^2) too bad should be O(n)
    for ph_g_idx, ph_g in enumerate(ref_ph_groups):
        end += len(ph_g)
        for map_pos in mappings:
            if map_pos is not None:
                if start >= map_pos.pos[0] and end <= map_pos.pos[1]:
                    if ref_tajweed_rules[ph_g_idx] is None:
                        ref_tajweed_rules[ph_g_idx] = map_pos.tajweed_rules
                    else:
                        ref_tajweed_rules[ph_g_idx] += map_pos.tajweed_rules
        start = end
    return ref_tajweed_rules


def explain_error(
    uthmani_text, ref_ph_text, predicted_ph_text, mappings: list[MappingPos | None]
) -> list[ReciterError]:
    """ """
    ref_ph_groups = chunck_phonemes(ref_ph_text)
    pred_ph_groups = chunck_phonemes(predicted_ph_text)

    ref_ph_to_uthmani = extract_ref_phonetic_to_uthmani(mappings)
    ref_ph_groups_tajweed_rules = get_ref_phonetic_groups_tajweed_rules(
        ref_ph_groups=ref_ph_groups,
        mappings=mappings,
        ref_ph_to_uthmani=ref_ph_to_uthmani,
    )

    # Aligning Phonemes groups using first chat of  every one
    alignmets = align_phonemes_groups(ref_ph_groups, pred_ph_groups)
    errors = []
    pred_ph_start = 0
    ref_ph_start = 0
    pred_ph_end = 0
    ref_ph_end = 0

    for align in alignmets:
        ref_ph = ref_ph_groups[align.ref_idx]
        pred_ph = pred_ph_groups[align.pred_idx]
        pred_ph_end = pred_ph_start + len(pred_ph)

        if align.op_type != "insert":
            ref_ph_end = ref_ph_start + len(ref_ph)
            uthmani_pos = (
                ref_ph_to_uthmani[ref_ph_start],
                ref_ph_to_uthmani[ref_ph_end - 1] + 1,
            )
            ph_pos = (ref_ph_start, ref_ph_end)
        else:
            uthmani_pos = (
                ref_ph_to_uthmani[ref_ph_start],
                ref_ph_to_uthmani[ref_ph_start],
            )
            ph_pos = (ref_ph_start, ref_ph_start)

        # TODO: for insert and replace try to make explanation for special phoneme like madd, ikhfaa, iqlab, ..
        if align.op_type == "insert":
            errors.append(
                ReciterError(
                    uthmani_pos=uthmani_pos,
                    ph_pos=ph_pos,
                    error_type="normal",  # TODO: try to estimate what is the Tajweed rule associated with this error type
                    speech_error_type="insert",
                    expected_ph="",
                    preditected_ph=pred_ph,
                )
            )

        elif align.op_type == "replace":
            # TODO: try to estimate the Tajweed rule
            errors.append(
                ReciterError(
                    uthmani_pos=uthmani_pos,
                    ph_pos=ph_pos,
                    error_type="normal",  # TODO: try to estimate what is the Tajweed rule associated with this error type
                    speech_error_type="replace",
                    expected_ph=ref_ph,
                    preditected_ph=pred_ph,
                )
            )

        elif align.op_type == "delete":
            errors.append(
                ReciterError(
                    uthmani_pos=uthmani_pos,
                    ph_pos=ph_pos,
                    error_type="tajweed"
                    if mappings[ref_ph_to_uthmani[ref_ph_start]].tajweed_rules
                    else "normal",
                    speech_error_type="delete",
                    expected_ph=ref_ph,
                    preditected_ph="",
                )
            )
        elif align.op_type == "equal":
            if ref_ph == pred_ph:
                ...
            # We have Tajweed rule
            elif ref_ph_groups_tajweed_rules[align.ref_idx] is not None:
                for taj_rule in ref_ph_groups_tajweed_rules[align.ref_idx]:
                    exp_len = None
                    pred_len = None
                    if taj_rule.correctness_type == "count":
                        pred_len = taj_rule.count(ref_ph, pred_ph)
                        exp_len = taj_rule.golden_len
                    elif taj_rule.correctness_type == "match":
                        ...
                    else:
                        raise ValueError(
                            f"Invalid mathing type: `{taj_rule.correctness_type}`. Available: `match`, `count`"
                        )
                    errors.append(
                        ReciterError(
                            uthmani_pos=uthmani_pos,
                            ph_pos=ph_pos,
                            error_type="tajweed",
                            speech_error_type="replace",  # TODO: make it compliant with speech typedelete
                            expected_ph=ref_ph,
                            preditected_ph=pred_ph,
                            expected_len=exp_len,
                            predicted_len=pred_len,
                            tajweed_rules=[taj_rule],
                        )
                    )

                # Tashkeel (Harakat)
                # TODO:
            elif ref_ph_groups[align.ref_idx][-1] in alph.phonetic_groups.residuals:
                ...

        pred_ph_start = pred_ph_end
        ref_ph_start = ref_ph_end

    return errors


if __name__ == "__main__":
    uthmani_text = "قالوا"
    ph_text = "قاالوو"
    # predicted_text = "كالوو"
    predicted_text = "كوولوو"
    # predicted_text = "فكالوو"

    normal_madd_rule = NormalMaddRule()

    mapping = [
        MappingPos(pos=(0, 1)),
        MappingPos(pos=(1, 3), tajweed_rules=[normal_madd_rule]),
        MappingPos(pos=(3, 4)),
        MappingPos(pos=(4, 6), tajweed_rules=[normal_madd_rule]),
        None,
    ]
    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ph_text,
        predicted_ph_text=predicted_text,
        mappings=mapping,
    )
    for err in errors:
        print(err)
