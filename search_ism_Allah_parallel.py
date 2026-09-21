import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from quran_transcript import Aya, MoshafAttributes, quran_phonetizer
from quran_transcript.alphabet import phonetics as ph
from quran_transcript.alphabet import uthmani as uth


def get_margin(x: int, boundries: set[int]) -> tuple[int, int]:
    start = x
    while start not in boundries:
        start -= 1

    end = x
    while end not in boundries:
        end += 1
    return (start, end)


def load_segments() -> list[str]:
    with open(
        "./quran-script/muallem_ds_uthmani_ayat.json", "r", encoding="utf-8"
    ) as f:
        quran_segments = json.load(f)

    start_aya = Aya()
    for aya in start_aya.get_ayat_after():
        quran_segments.append(aya.get().uthmani)

    return quran_segments


def search_chunk(
    segment_chunk: list[str],
    pattern_str: str,
    moshaf: MoshafAttributes,
    ignore_trick_to_match: bool = False,
) -> set[str]:
    found_matches = set()
    pattern = re.compile(pattern_str)
    space = re.compile(r"\s")

    for q_seg in segment_chunk:
        ph_text = quran_phonetizer(q_seg, moshaf).phonemes
        boundries = {m.span()[0] for m in space.finditer(ph_text)}
        boundries.add(0)
        boundries.add(len(ph_text))

        for mat in pattern.finditer(ph_text):
            # finding start
            start = mat.start()
            end = mat.end()
            if not ignore_trick_to_match:
                start_margin = get_margin(start, boundries)
                if start_margin[1] < end:
                    start = start_margin[1]
                else:
                    start = start_margin[0]
                end = get_margin(end, boundries)[1]

            found_matches.add(ph_text[start:end])

    return found_matches


def search(
    pattern_str: str,
    moshaf: MoshafAttributes,
    num_workers: int | None = os.cpu_count(),
    ignore_trick_to_match: bool = False,
) -> set[str]:
    quran_segments = load_segments()

    chunks = [quran_segments[i::num_workers] for i in range(num_workers or 8)]

    with ProcessPoolExecutor(max_workers=num_workers) as pool:
        chunk_results = pool.map(
            partial(
                search_chunk,
                pattern_str=pattern_str,
                moshaf=moshaf,
                ignore_trick_to_match=ignore_trick_to_match,
            ),
            chunks,
        )

    found_matches: set[str] = set()
    for chunk_result in chunk_results:
        found_matches.update(chunk_result)

    return found_matches


def fix_original_found_matches(found: set[str]) -> set[str]:
    fixed_founds = set()
    for word in sorted(found):
        if word[-1] in {ph.fatha, ph.dama, ph.kasra}:
            word = word + uth.space
        mat = re.search(f"{ph.meem_mokhfah}{{3}}", word)
        if mat:
            fixed_founds.add(word[mat.start() :])
            continue

        mat = re.search(f"{ph.waw}{{3}}", word)
        if mat:
            fixed_founds.add(word[mat.start() :])
            continue

        mat = re.search(f"{ph.noon_mokhfah}{{3}}", word)
        if mat:
            fixed_founds.add(word[mat.start() :])
            continue

        mat = re.search(f"{ph.noon_mokhfah}{{3}}", word)
        if mat:
            fixed_founds.add(word[mat.start() :])
            continue

        mat = re.search(f"{ph.lam}{{2}}{ph.kasra}{ph.lam}{{2}}", word)
        if mat:
            fixed_founds.add(word[mat.start() :])
            continue

        fixed_founds.add(word)

    return fixed_founds


if __name__ == "__main__":
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    orig_pat = f"(?<!{ph.jeem})(?<!{ph.daal})(?<!{ph.taa}{ph.fatha}{ph.waw})(.{uth.space}?{ph.lam}{{2}}){ph.fatha}{ph.alif}{{2,6}}{ph.haa}(?!{ph.dama}{ph.meem}(?!{ph.meem}))"

    space_or_start = "|".join(
        [
            f"{ph.hamza}{ph.fatha}{ph.baa}{ph.kasra}",
            f"{ph.baa}{ph.kasra}",
            f"{ph.lam}{ph.kasra}",
            f"{ph.hamza}{ph.fatha}",
            f"{ph.taa}{ph.fatha}",
            f"{ph.faa}{ph.fatha}",
            f"{ph.waw}{ph.fatha}",
            f"{ph.waw}{ph.fatha}{ph.taa}{ph.fatha}",
            f"{ph.faa}{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.waw}{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.hamza}{ph.fatha}{ph.alif}{{6}}",
            f"{ph.hamza}{ph.fatha}{ph.hamza_mosahala}",
        ]
    )
    middle = "|".join(
        [
            f"[{ph.meem_mokhfah}{ph.meem}]{{3}}{ph.baa}{ph.kasra}",
            f"{ph.waw}{{3}}{ph.fatha}",
            f"{ph.waw}{{3}}{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.noon_mokhfah}{{3}}[{ph.faa}{ph.taa}]{ph.fatha}",
            f"{ph.noon_mokhfah}{{3}}{ph.faa}{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.lam}{{2}}{ph.kasra}",
        ]
    )
    simple_pat = f"(?:(?:^|{uth.space})(?:{space_or_start})|{middle}|{uth.space}){ph.lam}{{2}}{ph.fatha}{ph.alif}{{2,6}}{ph.haa}(?:.{uth.space}|$|{ph.dama}{ph.meem}{{3,4}})"

    print("\nOriginal pattern")
    found_matches_orig = search(orig_pat, moshaf)
    found_matches_orig = fix_original_found_matches(found_matches_orig)
    print(f"Found `{len(found_matches_orig)}`")
    print("-" * 40)
    for idx, match in enumerate(sorted(found_matches_orig)):
        print(f"{idx}: `{match}`")

    print("\nSimple pattern")
    found_matches_simple = search(simple_pat, moshaf, ignore_trick_to_match=True)
    print(f"Found `{len(found_matches_simple)}`")
    print("-" * 40)
    for idx, match in enumerate(sorted(found_matches_simple)):
        print(f"{idx}: `{match}`")

    print("\nDiffs\n")
    diffs = found_matches_orig - found_matches_simple
    print(f"Len of diffs: {len(diffs)}")
    for idx, diff in enumerate(sorted(diffs)):
        print(f"{idx}: `{diff}`")
