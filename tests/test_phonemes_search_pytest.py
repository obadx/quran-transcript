"""
pytest test script for quran_transcript.phonetics.search.PhoneticSearch.

Usage:
    pytest test_phonetic_search.py -v

To add a new test case, simply append a tuple to the 'test_cases' list in the
parametrize decorator. Each tuple must contain:
    - uth_text: the Uthmani text to search for (string)
    - expected_results: a list of (sura, aya, expected_uthmani_text) triples
      that are known to be returned by the search.
"""

import pytest
from quran_transcript import MoshafAttributes, quran_phonetizer, alphabet as alph
from quran_transcript.phonetics.search import (
    PhoneticSearch,
    NoPhonemesSearchResult,
    PhonmesSearhResult,
    PhonemesSearchSpan,
)


@pytest.fixture(scope="session")
def phonemes_searcher():
    """PhoneticSearch instance using the pre‑built index (from package data)."""
    return PhoneticSearch()


# ----------------------------------------------------------------------
# Helper: compare Uthmani strings ignoring possible extra spaces
# ----------------------------------------------------------------------
def uthmani_equal(a: str, b: str) -> bool:
    """Compare two Uthmani strings after normalising spaces to the standard space character."""
    space = alph.uthmani.space
    a_norm = space.join(a.split())  # replace any whitespace with the standard space
    b_norm = space.join(b.split())
    return a_norm == b_norm


# ----------------------------------------------------------------------
# Parametrized test for phonetic search
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "ph_text, exp_results, error_ratio",
    [
        (
            "قَلِۦۦلَممممَاا",
            [
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=2,
                        aya_idx=88,
                        uthmani_word_idx=7,
                        uthmani_char_idx=69,
                        phonemes_idx=62,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=2,
                        aya_idx=88,
                        uthmani_word_idx=8,
                        uthmani_char_idx=84,
                        phonemes_idx=77,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=7,
                        aya_idx=3,
                        uthmani_word_idx=11,
                        uthmani_char_idx=97,
                        phonemes_idx=94,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=7,
                        aya_idx=3,
                        uthmani_word_idx=12,
                        uthmani_char_idx=112,
                        phonemes_idx=109,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=7,
                        aya_idx=10,
                        uthmani_word_idx=8,
                        uthmani_char_idx=75,
                        phonemes_idx=65,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=7,
                        aya_idx=10,
                        uthmani_word_idx=9,
                        uthmani_char_idx=90,
                        phonemes_idx=80,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=23,
                        aya_idx=78,
                        uthmani_word_idx=7,
                        uthmani_char_idx=74,
                        phonemes_idx=61,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=23,
                        aya_idx=78,
                        uthmani_word_idx=8,
                        uthmani_char_idx=89,
                        phonemes_idx=76,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=27,
                        aya_idx=62,
                        uthmani_word_idx=13,
                        uthmani_char_idx=125,
                        phonemes_idx=113,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=27,
                        aya_idx=62,
                        uthmani_word_idx=14,
                        uthmani_char_idx=140,
                        phonemes_idx=128,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=32,
                        aya_idx=9,
                        uthmani_word_idx=11,
                        uthmani_char_idx=104,
                        phonemes_idx=88,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=32,
                        aya_idx=9,
                        uthmani_word_idx=12,
                        uthmani_char_idx=119,
                        phonemes_idx=103,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=38,
                        aya_idx=24,
                        uthmani_word_idx=20,
                        uthmani_char_idx=192,
                        phonemes_idx=171,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=38,
                        aya_idx=24,
                        uthmani_word_idx=21,
                        uthmani_char_idx=206,
                        phonemes_idx=186,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=40,
                        aya_idx=58,
                        uthmani_word_idx=10,
                        uthmani_char_idx=110,
                        phonemes_idx=89,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=40,
                        aya_idx=58,
                        uthmani_word_idx=11,
                        uthmani_char_idx=125,
                        phonemes_idx=104,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=67,
                        aya_idx=23,
                        uthmani_word_idx=9,
                        uthmani_char_idx=90,
                        phonemes_idx=73,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=67,
                        aya_idx=23,
                        uthmani_word_idx=10,
                        uthmani_char_idx=105,
                        phonemes_idx=88,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=69,
                        aya_idx=41,
                        uthmani_word_idx=4,
                        uthmani_char_idx=29,
                        phonemes_idx=28,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=69,
                        aya_idx=41,
                        uthmani_word_idx=5,
                        uthmani_char_idx=44,
                        phonemes_idx=43,
                    ),
                ),
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=69,
                        aya_idx=42,
                        uthmani_word_idx=3,
                        uthmani_char_idx=24,
                        phonemes_idx=24,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=69,
                        aya_idx=42,
                        uthmani_word_idx=4,
                        uthmani_char_idx=39,
                        phonemes_idx=39,
                    ),
                ),
            ],
            0.1,
        ),
        (
            "يُجِۦۦۦۦبڇ",
            [
                PhonmesSearhResult(
                    start=PhonemesSearchSpan(
                        sura_idx=27,
                        aya_idx=62,
                        uthmani_word_idx=1,
                        uthmani_char_idx=5,
                        phonemes_idx=7,
                    ),
                    end=PhonemesSearchSpan(
                        sura_idx=27,
                        aya_idx=62,
                        uthmani_word_idx=1,
                        uthmani_char_idx=16,
                        phonemes_idx=17,
                    ),
                )
            ],
            0.1,
        ),
    ],
)
def test_search(
    phonemes_searcher,
    ph_text,
    exp_results: list[PhonmesSearhResult],
    error_ratio: float,
):
    """Verify that the phonetic search returns all expected ayas with correct Uthmani text."""
    out_results = phonemes_searcher.search(ph_text, error_ratio=error_ratio)
    assert out_results == exp_results
