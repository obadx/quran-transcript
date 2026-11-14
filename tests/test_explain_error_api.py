from quran_transcript import (
    MoshafAttributes,
    ReciterError,
    explain_error,
    quran_phonetizer,
)
from quran_transcript.phonetics.tajweed_rulses import ExplainedTajweedRule

SEPARATOR = "=" * 72
SUB_SEPARATOR = "-" * 72


def print_mappings(uthmani_text: str, mappings) -> None:
    print("Uthmani -> phonetic mappings:")
    print(f"  {'idx':>3}  {'char':<6}  phonetic span")
    for uth_idx, span in enumerate(mappings.uth_to_ph):
        char = uthmani_text[uth_idx] if uth_idx < len(uthmani_text) else ""
        deleted = " (deleted)" if span.deleted else ""
        print(f"  {uth_idx:>3}  {char!r:<6}  {span.pos}{deleted}")
    print()


def format_tajweed_rule(rule: ExplainedTajweedRule) -> list[str]:
    default_name = rule.rule_type.name.replace("_", " ").title()
    name_ar = rule.name.ar or default_name
    name_en = rule.name.en or default_name
    lines = [
        f"- {name_ar} ({name_en})",
        f"  rule_type:   {rule.rule_type.name}",
        f"  correctness: {rule.correctness}",
        f"  ph_pivot:    {rule.ph_pivot}",
        f"  uth_pivot:   {rule.uth_pivot}",
    ]
    if rule.description.ar or rule.description.en:
        lines.append(f"  description: {rule.description.ar} ({rule.description.en})")
    if rule.ph_deps:
        lines.append(f"  ph_deps:     {rule.ph_deps}")
    if rule.uth_deps:
        lines.append(f"  uth_deps:    {rule.uth_deps}")
    if rule.golden_len != -1:
        lines.append(f"  golden_len:  {rule.golden_len}")
    if rule.tag:
        lines.append(f"  tag:         {rule.tag}")
    return lines


def print_tajweed_rules(
    label: str,
    rules: list[ExplainedTajweedRule],
) -> None:
    if not rules:
        return
    print(f"  {label}:")
    for rule in rules:
        for line in format_tajweed_rule(rule):
            print(f"    {line}")


def print_error(
    index: int,
    total: int,
    err: ReciterError,
    uthmani_text: str,
    ref_ph_text: str,
) -> None:
    uth_start, uth_end = err.uthmani_pos
    ph_start, ph_end = err.ph_pos
    uth_slice = uthmani_text[uth_start:uth_end]
    ref_slice = ref_ph_text[ph_start:ph_end]

    print(SUB_SEPARATOR)
    print(f"Error {index}/{total}: {err.error_type} / {err.speech_error_type}")
    print(f"  Uthmani:   {err.uthmani_pos}\n             '{uth_slice}'")
    print(f"  Ref PH : {err.ph_pos}\n             '{ref_slice}'")
    print(f"  Expected:  {err.expected_ph!r}")
    print(f"  Predicted: {err.preditected_ph!r}")
    if err.expected_len != -1 or err.predicted_len != -1:
        print(
            f"  Length:    expected={err.expected_len}, predicted={err.predicted_len}"
        )

    print_tajweed_rules("Reference Tajweed rules", err.ref_tajweed_rules)
    print_tajweed_rules("Inserted Tajweed rules", err.inserted_tajweed_rules)
    print_tajweed_rules("Replaced Tajweed rules", err.replaced_tajweed_rules)
    print_tajweed_rules("Missing Tajweed rules", err.missing_tajweed_rules)
    print()


if __name__ == "__main__":
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )

    uthmani_text = "قَالُوٓا۟"

    # normal madd len 1 error
    predicted_text = "قَاالُۥ"

    predicted_text = "كالۥۥ"
    # predicted_text = "فكالۥۥ"
    # predicted_text = "فكۥۥلۥۥ"

    # uthmani_text = "ٱلْحَقُّ"
    # predicted_text = "ءَلحَقق"
    # predicted_text = "ءَلحقق"
    # predicted_text = "ءَلحُقق"

    # uthmani_text = "الٓمٓ"
    # predicted_text = "ءَلِف لَااااااممممِۦۦۦۦۦۦم"
    # predicted_text = "ءَلِف لَاااااممممِۦۦۦۦۦۦم"

    # uthmani_text = "لَكَ"
    # predicted_text = "لَكَا"

    ref_ph_out = quran_phonetizer(uthmani_text, moshaf)
    errors = explain_error(
        uthmani_text=uthmani_text,
        ref_ph_text=ref_ph_out.phonemes,
        predicted_ph_text=predicted_text,
        mappings=ref_ph_out.mappings,
    )

    print(SEPARATOR)
    print("Recitation error analysis")
    print(SEPARATOR)
    print(f"Uthmani text:       `{uthmani_text}`")
    print(f"Predicted text:     `{predicted_text}`")
    print(f"Reference phonemes: `{ref_ph_out.phonemes}`")
    print()

    # print_mappings(uthmani_text, ref_ph_out.mappings)
    print(f"Total errors: {len(errors)}")
    for index, err in enumerate(errors, 1):
        print_error(index, len(errors), err, uthmani_text, ref_ph_out.phonemes)
