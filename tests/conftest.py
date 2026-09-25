import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from math import ceil

import pytest

from quran_transcript import Aya
from quran_transcript.phonetics.moshaf_attributes import MoshafAttributes
from quran_transcript.phonetics.phonetizer import (
    QuranPhoneticScriptOutput,
    quran_phonetizer,
)


@dataclass
class QuranSegment:
    uth: str
    aya: str


def load_quran_segments(complete_aya_only: bool = False) -> list[QuranSegment]:
    quran_segments = []
    if not complete_aya_only:
        with open(
            "./quran-script/muallem_ds_uthmani_ayat.json", "r", encoding="utf-8"
        ) as f:
            segments = json.load(f)
        for seg in segments:
            seg = re.sub(r"\s+", r" ", seg)
            seg = re.sub(r"^\s|\s$", r"", seg)
            quran_segments.append(QuranSegment(uth=seg, aya="None"))

    start_aya = Aya()
    for aya in start_aya.get_ayat_after():
        quran_segments.append(
            QuranSegment(
                uth=aya.get().uthmani, aya=f"{aya.get().sura_idx}_{aya.get().aya_idx}"
            )
        )

    return quran_segments


def phonetize_worker(
    uth_texts: list[str],
    offset: int,
    moshaf: MoshafAttributes,
    **kwargs,
) -> tuple[int, list[QuranPhoneticScriptOutput]]:
    ph_outs = []
    for uth_text in uth_texts:
        ph_outs.append(quran_phonetizer(uth_text, moshaf, **kwargs))
    return (offset, ph_outs)


def phonetize_parallel(
    quran_segments: list[QuranSegment],
    moshaf: MoshafAttributes,
    num_workers: int = os.cpu_count() or 8,
    **kwargs,
) -> list[QuranPhoneticScriptOutput]:
    num_q_segs = len(quran_segments)
    num_chunk_segs = ceil(num_q_segs / num_workers)

    uth_texts = [q.uth for q in quran_segments]
    chunks = [
        uth_texts[i * num_chunk_segs : (i + 1) * num_chunk_segs]
        for i in range(num_workers)
    ]
    offsets = [i * num_chunk_segs for i in range(num_workers)]

    with ProcessPoolExecutor(max_workers=num_workers) as pool:
        chunk_results = pool.map(
            partial(
                phonetize_worker,
                moshaf=moshaf,
                **kwargs,
            ),
            chunks,
            offsets,
        )

    ph_outs: list[QuranPhoneticScriptOutput] = [None] * num_q_segs
    for chunk_res in chunk_results:
        offset = chunk_res[0]
        for idx in range(len(chunk_res[1])):
            ph_outs[idx + offset] = chunk_res[1][idx]
    return ph_outs


@pytest.fixture(scope="session")
def quran_segs_phonetized_with_constat_moshaf() -> tuple[
    list[QuranSegment], list[QuranPhoneticScriptOutput]
]:
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    quran_segments = load_quran_segments()
    ph_outs = phonetize_parallel(quran_segments, moshaf)
    return (quran_segments, ph_outs)


def pytest_addoption(parser):
    parser.addoption(
        "--skip-stress",
        action="store_true",
        default=False,
        help="Skip tests marked with @pytest.mark.stress",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-stress"):
        skip = pytest.mark.skip(reason="skipped via --skip-stress")
        for item in items:
            if "stress" in item.keywords:
                item.add_marker(skip)
