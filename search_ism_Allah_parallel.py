import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from math import ceil

from quran_transcript import Aya, MoshafAttributes, quran_phonetizer
from quran_transcript.alphabet import phonetic_groups as phg
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


@dataclass
class QuranSegment:
    uth: str
    aya: str


def load_segments(complete_aya_only: bool = False) -> list[QuranSegment]:
    quran_segments = []
    if not complete_aya_only:
        with open(
            "./quran-script/muallem_ds_uthmani_ayat.json", "r", encoding="utf-8"
        ) as f:
            segments = json.load(f)
        for seg in segments:
            quran_segments.append(QuranSegment(uth=seg, aya="None"))

    start_aya = Aya()
    for aya in start_aya.get_ayat_after():
        quran_segments.append(
            QuranSegment(
                uth=aya.get().uthmani, aya=f"{aya.get().sura_idx}_{aya.get().aya_idx}"
            )
        )

    return quran_segments


@dataclass
class SearchOut:
    maches: set[str]
    counts: int
    ayat: set[str]
    idx_to_count: list[int]
    offset: int = 0


def search_chunk(
    segment_chunk: list[QuranSegment],
    offset: int,
    pattern_str: str,
    moshaf: MoshafAttributes,
    ignore_trick_to_match: bool = False,
) -> SearchOut:
    found_matches = set()
    pattern = re.compile(pattern_str)
    space = re.compile(r"\s")
    counts = 0
    ayat = set()
    idx_to_count = []

    for idx, q_seg in enumerate(segment_chunk):
        ph_text = quran_phonetizer(q_seg.uth, moshaf).phonemes
        boundries = {m.span()[0] for m in space.finditer(ph_text)}
        boundries.add(0)
        boundries.add(len(ph_text))
        idx_to_count.append(0)

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
            counts += 1
            idx_to_count[idx] += 1
            ayat.add(q_seg.aya)

    return SearchOut(
        maches=found_matches,
        counts=counts,
        ayat=ayat,
        idx_to_count=idx_to_count,
        offset=offset,
    )


def search(
    pattern_str: str,
    moshaf: MoshafAttributes,
    num_workers: int | None = os.cpu_count(),
    ignore_trick_to_match: bool = False,
    complete_aya_only=False,
) -> SearchOut:
    quran_segments = load_segments(complete_aya_only=complete_aya_only)
    num_workers = num_workers or 8
    num_q_segs = len(quran_segments)
    num_chunk_segs = ceil(num_q_segs / num_workers)

    chunks = [
        quran_segments[i * num_chunk_segs : (i + 1) * num_chunk_segs]
        for i in range(num_workers)
    ]
    offsets = [i * num_chunk_segs for i in range(num_workers)]

    with ProcessPoolExecutor(max_workers=num_workers) as pool:
        chunk_results = pool.map(
            partial(
                search_chunk,
                pattern_str=pattern_str,
                moshaf=moshaf,
                ignore_trick_to_match=ignore_trick_to_match,
            ),
            chunks,
            offsets,
        )

    counts = 0
    found_matches: set[str] = set()
    ayat: set[str] = set()
    idx_to_count = [0] * num_q_segs
    for chunk_res in chunk_results:
        found_matches.update(chunk_res.maches)
        counts += chunk_res.counts
        ayat.update(chunk_res.ayat)
        for idx in range(len(chunk_res.idx_to_count)):
            idx_to_count[idx + chunk_res.offset] = chunk_res.idx_to_count[idx]

    return SearchOut(
        maches=found_matches,
        counts=counts,
        ayat=ayat,
        idx_to_count=idx_to_count,
    )


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
            f"[{ph.baa}{ph.lam}]{ph.kasra}",
            f"[{ph.hamza}{ph.taa}{ph.faa}{ph.waw}]{ph.fatha}",
            f"{ph.waw}{ph.fatha}{ph.taa}{ph.fatha}",
            f"[{ph.faa}{ph.waw}]{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.hamza}{ph.fatha}{ph.alif}{{6}}",
            f"{ph.hamza}{ph.fatha}{ph.hamza_mosahala}",
        ]
    )
    middle = "|".join(
        [
            f"[{ph.meem_mokhfah}{ph.meem}]{{3}}{ph.baa}{ph.kasra}",
            f"{ph.waw}{{3}}{ph.fatha}",
            f"{ph.waw}{{3}}{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.waw}{{3}}{ph.fatha}{ph.taa}{ph.fatha}",
            f"{ph.noon_mokhfah}{{3}}[{ph.faa}{ph.taa}]{ph.fatha}",
            f"{ph.noon_mokhfah}{{3}}{ph.faa}{ph.fatha}{ph.lam}{ph.kasra}",
            f"{ph.lam}{{2}}{ph.kasra}",
        ]
    )
    simple_pat = f"(?:(?:^|{uth.space})(?:{space_or_start})|{middle}|{uth.space}){ph.lam}{{2}}{ph.fatha}{ph.alif}{{2,6}}{ph.haa}(?:[{phg.harakat}](?={uth.space})|$|{ph.dama}{ph.meem}{{3,4}})"

    complete_aya_only = False
    num_workers = os.cpu_count()

    print("\nOriginal pattern")
    orig_res = search(
        orig_pat,
        moshaf,
        complete_aya_only=complete_aya_only,
        num_workers=num_workers,
    )
    found_matches_orig = fix_original_found_matches(orig_res.maches)
    print(f"Found `{len(found_matches_orig)}`")
    print("-" * 40)
    for idx, match in enumerate(sorted(found_matches_orig)):
        print(f"{idx}: `{match}`")

    print("\nSimple pattern")
    sim_res = search(
        simple_pat,
        moshaf,
        ignore_trick_to_match=True,
        complete_aya_only=complete_aya_only,
        num_workers=num_workers,
    )
    print(f"Found `{len(sim_res.maches)}`")
    print("-" * 40)
    for idx, match in enumerate(sorted(sim_res.maches)):
        print(f"{idx}: `{match}`")

    print(f"Orig Counts: {orig_res.counts}, Simple Counts: {sim_res.counts}")

    print("\nDiffs\n")
    diffs = found_matches_orig - sim_res.maches
    print(f"Len of diffs: {len(diffs)}")
    for idx, diff in enumerate(sorted(diffs)):
        print(f"{idx}: `{diff}`")

    print("\nPer Segments Counts Diffs\n")
    quran_segments = load_segments(complete_aya_only=complete_aya_only)
    for idx, (orig_idx_counts, sim_idx_counts) in enumerate(
        zip(orig_res.idx_to_count, sim_res.idx_to_count)
    ):
        if orig_idx_counts != sim_idx_counts:
            print(f"Orig Counts: {orig_idx_counts}, Sim Counts: {sim_idx_counts}")
            print(f"`{quran_segments[idx]}`")
            ph_text = quran_phonetizer(quran_segments[idx].uth, moshaf).phonemes
            print(ph_text)
            print("Original Founds:")
            for m in re.finditer(orig_pat, ph_text):
                print(m)
            print("Simple Founds:")
            for m in re.finditer(simple_pat, ph_text):
                print(m)
            print("-" * 30)
