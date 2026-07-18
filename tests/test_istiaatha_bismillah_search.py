"""
pytest tests for Istiaatha / Bismillah support in
quran_transcript.phonetics.search.PhoneticSearch (GitHub issue #15).

These follow the same conventions as test_phonemes_search_pytest.py:
a session-scoped `phonemes_searcher` fixture, and Uthmani-string comparison
via `uthmani_equal`. All expected values below were generated against a real
rebuilt `ph_index.npy` (via `create_phonemes_index()`), not hand-computed.

Requires the rebuilt (8-column) index -- run `create_phonemes_index()` once
before running these tests if you're still on an old index. See the
"Running everything" walkthrough for the exact steps.

Usage:
    pytest test_istiaatha_bismillah_search.py -v
"""

import pytest
from quran_transcript import MoshafAttributes, quran_phonetizer, Aya, alphabet as alph
from quran_transcript.phonetics.search import (
    PhoneticSearch,
    NoPhonemesSearchResult,
    PhonmesSearhResult,
    PhonemesSearchSpan,
    SEGMENT_QURAN,
    SEGMENT_ISTIAATHA,
    SEGMENT_BISMILLAH,
)


@pytest.fixture(scope="session")
def moshaf():
    return MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )


@pytest.fixture(scope="session")
def phonemes_searcher():
    """PhoneticSearch instance using the pre-built index (from package data)."""
    return PhoneticSearch()


@pytest.fixture(scope="session")
def istiaatha_ph(moshaf):
    return quran_phonetizer(alph.istiaatha.uthmani, moshaf, remove_spaces=True).phonemes


@pytest.fixture(scope="session")
def bismillah_ph(moshaf):
    # sura 2 has a standalone Bismillah segment; the text is identical for
    # every sura that has one, so any such sura works as the query source.
    text = Aya(2, 1).get().bismillah_uthmani
    return quran_phonetizer(text, moshaf, remove_spaces=True).phonemes


def uthmani_equal(a: str, b: str) -> bool:
    """Compare two Uthmani strings after normalising spaces to the standard space character."""
    space = alph.uthmani.space
    a_norm = space.join(a.split())
    b_norm = space.join(b.split())
    return a_norm == b_norm


# ----------------------------------------------------------------------
# Part 1 -- index shape / segment_type sanity
# ----------------------------------------------------------------------
def test_index_has_segment_type_column(phonemes_searcher):
    assert phonemes_searcher.index.shape[1] == 8


def test_istiaatha_indexed_once_per_sura(phonemes_searcher):
    seg = phonemes_searcher.index[:, 7]
    istiaatha_rows = (seg == SEGMENT_ISTIAATHA).sum()
    # "أَعُوذُ بِٱللَّهِ مِنَ ٱلشَّيْطَانِ ٱلرَّجِيمِ" -> 19 phoneme groups,
    # once before every one of the 114 suras.
    assert istiaatha_rows == 19 * 114


def test_bismillah_indexed_for_112_suras(phonemes_searcher):
    seg = phonemes_searcher.index[:, 7]
    bismillah_rows = (seg == SEGMENT_BISMILLAH).sum()
    # "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ" -> 15 phoneme groups,
    # once before every sura except 1 (it's aya 1 itself) and 9 (none).
    assert bismillah_rows == 15 * 112


# ----------------------------------------------------------------------
# Part 3 -- search() flags
# ----------------------------------------------------------------------
def test_istiaatha_excluded_by_default(phonemes_searcher, istiaatha_ph):
    with pytest.raises(NoPhonemesSearchResult):
        phonemes_searcher.search(istiaatha_ph, error_ratio=0.1)


def test_istiaatha_included_when_requested(phonemes_searcher, istiaatha_ph):
    results = phonemes_searcher.search(
        istiaatha_ph, error_ratio=0.1, include_istiaatha=True
    )
    # prepended before every one of the 114 suras
    assert len(results) == 114
    assert all(r.start.segment_type == SEGMENT_ISTIAATHA for r in results)


def test_bismillah_excluded_by_default_except_quranic_occurrences(
    phonemes_searcher, bismillah_ph
):
    """Sura 1 (Al-Fatiha, aya 1) and Sura 27 (An-Naml, aya 30) contain the
    Bismillah wording as literal Quranic text -- those are segment_type=quran
    and stay searchable even with include_bismillah=False. The 112 standalone
    Bismillah segments are correctly excluded."""
    results = phonemes_searcher.search(bismillah_ph, error_ratio=0.1)
    suras = sorted(set(r.start.sura_idx for r in results))
    assert suras == [1, 27]
    assert all(r.start.segment_type == SEGMENT_QURAN for r in results)


def test_bismillah_included_when_requested(phonemes_searcher, bismillah_ph):
    results = phonemes_searcher.search(
        bismillah_ph, error_ratio=0.1, include_bismillah=True
    )
    suras = sorted(set(r.start.sura_idx for r in results))
    # 112 standalone segments + sura 1 (quranic) = 113; sura 9 has none.
    assert len(suras) == 113
    assert 9 not in suras


def test_sura9_has_no_bismillah_false_positive(phonemes_searcher, bismillah_ph):
    results = phonemes_searcher.search(
        bismillah_ph, error_ratio=0.1, include_bismillah=True
    )
    assert all(r.start.sura_idx != 9 for r in results)


# ----------------------------------------------------------------------
# Part 2 -- boundary (start, end) in __init__
# ----------------------------------------------------------------------
def test_boundary_restricts_to_requested_sura(bismillah_ph):
    bounded_searcher = PhoneticSearch(start=(2, 1), end=(2, 286))
    results = bounded_searcher.search(
        bismillah_ph, error_ratio=0.1, include_bismillah=True
    )
    assert all(r.start.sura_idx == 2 for r in results)


def test_boundary_excludes_out_of_range_matches(istiaatha_ph):
    # Istiaatha is prepended before every sura, but bounding to sura 2 only
    # should surface only sura 2's occurrence, not sura 1's or sura 3's.
    bounded_searcher = PhoneticSearch(start=(2, 1), end=(2, 286))
    results = bounded_searcher.search(
        istiaatha_ph, error_ratio=0.1, include_istiaatha=True
    )
    assert len(results) == 1
    assert results[0].start.sura_idx == 2


def test_old_style_full_range_still_works(phonemes_searcher):
    """Default __init__() with no start/end covers the whole Quran, exactly
    like before this feature -- existing callers see no behavior change."""
    assert phonemes_searcher.start == (1, 1)
    assert phonemes_searcher.end == (114, 6)


# ----------------------------------------------------------------------
# Part 4 -- get_uthmani_from_result()
# ----------------------------------------------------------------------
def test_reconstruct_istiaatha_only(phonemes_searcher, istiaatha_ph):
    bounded_searcher = PhoneticSearch(start=(1, 1), end=(1, 7))
    results = bounded_searcher.search(
        istiaatha_ph, error_ratio=0.1, include_istiaatha=True
    )
    assert len(results) == 1
    assert results[0] == PhonmesSearhResult(
        start=PhonemesSearchSpan(
            sura_idx=1, aya_idx=1, uthmani_word_idx=0, uthmani_char_idx=0,
            phonemes_idx=0, segment_type=SEGMENT_ISTIAATHA,
        ),
        end=PhonemesSearchSpan(
            sura_idx=1, aya_idx=1, uthmani_word_idx=4, uthmani_char_idx=46,
            phonemes_idx=41, segment_type=SEGMENT_ISTIAATHA,
        ),
    )
    uthmani = bounded_searcher.get_uthmani_from_result(results[0])
    assert uthmani_equal(uthmani, alph.istiaatha.uthmani)


def test_reconstruct_bismillah_only(bismillah_ph):
    bounded_searcher = PhoneticSearch(start=(2, 1), end=(2, 286))
    results = bounded_searcher.search(
        bismillah_ph, error_ratio=0.1, include_bismillah=True
    )
    assert len(results) == 1
    assert results[0] == PhonmesSearhResult(
        start=PhonemesSearchSpan(
            sura_idx=2, aya_idx=1, uthmani_word_idx=0, uthmani_char_idx=0,
            phonemes_idx=0, segment_type=SEGMENT_BISMILLAH,
        ),
        end=PhonemesSearchSpan(
            sura_idx=2, aya_idx=1, uthmani_word_idx=3, uthmani_char_idx=39,
            phonemes_idx=32, segment_type=SEGMENT_BISMILLAH,
        ),
    )
    uthmani = bounded_searcher.get_uthmani_from_result(results[0])
    assert uthmani_equal(uthmani, Aya(2, 1).get().bismillah_uthmani)


def test_reconstruct_quranic_bismillah_in_sura1_and_sura27(
    phonemes_searcher, bismillah_ph
):
    # Compare against the real source string (Aya(2,1)'s Bismillah), not a
    # hand-retyped Arabic literal -- diacritic ordering is easy to get
    # subtly wrong by hand and will silently fail string equality.
    expected = Aya(2, 1).get().bismillah_uthmani

    results = phonemes_searcher.search(bismillah_ph, error_ratio=0.1)
    by_sura = {r.start.sura_idx: r for r in results}
    assert set(by_sura) == {1, 27}
    for sura_idx, r in by_sura.items():
        assert r.start.segment_type == SEGMENT_QURAN
        uthmani = phonemes_searcher.get_uthmani_from_result(r)
        assert uthmani_equal(
            uthmani, expected
        ), f"sura {sura_idx}: got {uthmani!r}"


def test_reconstruct_combined_istiaatha_bismillah_aya(moshaf):
    """Sura 112 (Al-Ikhlas) has a standalone Bismillah segment, so a query
    spanning Istiaatha + Bismillah + aya 1 should reconstruct all three in
    order via a single PhonmesSearhResult."""
    istiaatha_uth = alph.istiaatha.uthmani
    bismillah_uth = Aya(112, 1).get().bismillah_uthmani
    aya_uth = Aya(112, 1).get().uthmani
    combined_uth = f"{istiaatha_uth} {bismillah_uth} {aya_uth}"
    combined_ph = quran_phonetizer(combined_uth, moshaf, remove_spaces=True).phonemes

    searcher = PhoneticSearch()
    results = searcher.search(
        combined_ph, error_ratio=0.2, include_istiaatha=True, include_bismillah=True
    )
    sura112_hits = [r for r in results if r.start.sura_idx == 112]
    assert len(sura112_hits) == 1

    r = sura112_hits[0]
    assert r.start.segment_type == SEGMENT_ISTIAATHA
    assert r.end.segment_type == SEGMENT_QURAN

    uthmani = searcher.get_uthmani_from_result(r)
    assert uthmani_equal(uthmani, combined_uth)


def test_cross_sura_boundary_not_implemented(phonemes_searcher):
    """A match starting in Quran text and ending in the *next* sura's
    Istiaatha/Bismillah isn't resolvable by the current aya-walk loop --
    this should fail loudly, not silently return wrong text."""
    fake_result = PhonmesSearhResult(
        start=PhonemesSearchSpan(
            sura_idx=111, aya_idx=5, uthmani_word_idx=0, uthmani_char_idx=0,
            phonemes_idx=0, segment_type=SEGMENT_QURAN,
        ),
        end=PhonemesSearchSpan(
            sura_idx=112, aya_idx=1, uthmani_word_idx=2, uthmani_char_idx=10,
            phonemes_idx=10, segment_type=SEGMENT_ISTIAATHA,
        ),
    )
    with pytest.raises(NotImplementedError):
        phonemes_searcher.get_uthmani_from_result(fake_result)


# ----------------------------------------------------------------------
# Backward compatibility: old-format (7-column) index must fail loudly
# ----------------------------------------------------------------------
def test_old_index_format_rejected(tmp_path):
    import numpy as np

    old_index = np.zeros((10, 7), dtype=np.uint16)
    np.save(tmp_path / "ph_index.npy", old_index)
    (tmp_path / "ref_norm_ph.txt").write_text("ابتث" * 3, encoding="utf-8")

    with pytest.raises(ValueError, match="8"):
        PhoneticSearch(data_dir=tmp_path)