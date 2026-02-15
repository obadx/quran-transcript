import numpy as np
import re
import importlib.resources as pkg_resources
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from fuzzysearch import find_near_matches

from ..utils import Aya
from .phonetizer import quran_phonetizer
from .sifa import chunck_phonemes
from .moshaf_attributes import MoshafAttributes
from .conv_base_operation import MappingListType
from .. import alphabet as alph


def clean_uthmani_spaces(uth_text: str) -> str:
    """Remove residual spaces from Uthmani text.

    Replaces any whitespace sequence with the Uthmani space character,
    and strips leading/trailing spaces.

    Args:
        uth_text: Raw Uthmani text possibly containing multiple spaces.

    Returns:
        Cleaned Uthmani text with single Uthmani spaces between words.
    """
    uth_text = re.sub(r"\s+", f"{alph.uthmani.space}", uth_text)
    uth_text = re.sub(r"(\s$|^\s)", r"", uth_text)
    return uth_text


def normalize_phonetic_groups(ph_groups: list[str]) -> str:
    """Normalize a list of phoneme groups by taking the first character of each group.

    This is used to create a simplified phonetic representation where each group
    (e.g., a consonant with diacritics) is reduced to its base character.

    Args:
        ph_groups: List of phoneme group strings.

    Returns:
        Concatenated string of the first character from each group.
    """
    out = ""
    for g in ph_groups:
        out += g[0]
    return out


def get_uth_word_boundaries_in_ph(
    uth_text: str, mappings: MappingListType
) -> list[int]:
    """Get Uthmani word boundary indices in the phonetic script.

    Uses the mapping from Uthmani characters to phonetic positions. Each Uthmani
    space is expected to correspond to a deleted mapping entry, and the phonetic
    start index of that deleted entry marks the word boundary.

    Args:
        uth_text: Uthmani text (spaces are explicit).
        mappings: List of Mapping objects linking Uthmani indices to phonetic ranges.

    Returns:
        List of phonetic indices where each Uthmani word ends.
    """
    boundries = []
    for idx in range(len(uth_text)):
        if uth_text[idx] == alph.uthmani.space:
            assert mappings[idx].deleted, (
                f"`{uth_text}`, `{len(uth_text)}`, `IDX={idx}`, `{uth_text[idx]}`, `{uth_text[idx + 1 :]}`, `{mappings[idx]}`"
            )
            boundries.append(mappings[idx].pos[0])
    return boundries


def get_phonetic_to_char_uthmani(mappings: MappingListType) -> dict[int, int]:
    """Create a mapping from phonetic index to Uthmani character index.

    For each phonetic position, store the index of the Uthmani character it originated from.
    Also adds an extra mapping for the position immediately after the last phonetic character
    to the total number of Uthmani characters (as an exclusive end marker).

    Args:
        mappings: List of Mapping objects.

    Returns:
        Dictionary where keys are phonetic indices and values are Uthmani character indices.
    """
    ph_to_uth = {}
    for uth_idx, m in enumerate(mappings):
        for ph_idx in range(m.pos[0], m.pos[1]):
            ph_to_uth[ph_idx] = uth_idx
    ph_to_uth[mappings[-1].pos[1]] = len(mappings)  # last index
    return ph_to_uth


def create_phonemes_index(output_dir: Path | None = None):
    """Create a phoneme index and reference phoneme string and save to disk.

    Iterates over all ayas, generates phonetic representation for each,
    normalizes phoneme groups, and builds a 2D numpy array with the following
    columns per phoneme group:
        [sura_idx, aya_idx, uth_word_start_idx, uth_char_start_idx, uth_char_end_idx,
         ph_start_idx, ph_end_idx]

    Also writes the concatenated normalized phonemes to a text file as a reference.

    TODO:
        - Decide whether we need both uth_word_start_idx and uth_word_end_idx or just a single word index.
        - Add handling for deleted Uthmani characters at the end.

    Args:
        output_dir: Directory where 'ph_index.npy' and 'ref_norm_ph.txt' will be saved.
                    If None, defaults to the package's 'quran-script' folder.
    """
    moshaf = MoshafAttributes(
        rewaya="hafs",
        madd_monfasel_len=4,
        madd_mottasel_len=4,
        madd_mottasel_waqf=4,
        madd_aared_len=4,
    )
    start_aya = Aya()
    ph_grp_to_index = []
    ref_ph = ""
    for aya in start_aya.get_ayat_after():
        uth_text = aya.get().uthmani
        uth_text = clean_uthmani_spaces(uth_text)
        ph_out = quran_phonetizer(uth_text, moshaf, remove_spaces=True)
        ph_text = ph_out.phonemes
        ph_groups = chunck_phonemes(ph_text)
        ph_norm = normalize_phonetic_groups(ph_groups)
        ref_ph += ph_norm
        uth_word_bound = get_uth_word_boundaries_in_ph(uth_text, ph_out.mappings)
        ph_to_uth_idx = get_phonetic_to_char_uthmani(ph_out.mappings)

        # TODO::
        # Do we need uth word start and end or a single word
        # Add deleted uthmani chars to the end
        ph_start_idx = 0
        ph_end_idx = 0
        next_ph_end_idx = 0
        uth_word_idx = 0
        curr_wrd_bound_idx = 0
        for g_idx, ph_g in enumerate(ph_groups):
            # print(uth_word_idx)
            # print(ph_g)
            # print("-" * 10)
            ph_end_idx = ph_start_idx + len(ph_g)
            if (g_idx + 1) < len(ph_groups):
                next_ph_end_idx = ph_end_idx + len(ph_groups[g_idx + 1])

            ph_grp_to_index.append(
                [
                    aya.get().sura_idx,
                    aya.get().aya_idx,
                    uth_word_idx,
                    ph_to_uth_idx[ph_start_idx],
                    ph_to_uth_idx[ph_end_idx],
                    ph_start_idx,
                    ph_end_idx,
                ]
            )

            # Adjusting Values for the following steps
            if curr_wrd_bound_idx < len(uth_word_bound):
                if (ph_end_idx >= uth_word_bound[curr_wrd_bound_idx]) or (
                    # The case where we have phoneme group is commen between two words
                    # we will make this common part associated to the second word
                    ph_end_idx < uth_word_bound[curr_wrd_bound_idx]
                    and next_ph_end_idx > uth_word_bound[curr_wrd_bound_idx]
                ):
                    uth_word_idx += 1
                    curr_wrd_bound_idx += 1
            ph_start_idx = ph_end_idx

    # Convert to numpy array of uint16
    index_array = np.array(ph_grp_to_index, dtype=np.uint16)

    # Determine output directory
    if output_dir is None:
        # Default to package's quran-script folder
        output_dir = Path(pkg_resources.files("quran_transcript")) / "quran-script"
    else:
        output_dir = Path(output_dir)

    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save index as .npy
    index_path = output_dir / "ph_index.npy"
    np.save(index_path, index_array)
    print(f"Phoneme index saved to {index_path}")

    # Save reference phonemes as text
    ref_ph_path = output_dir / "ref_norm_ph.txt"
    with open(ref_ph_path, "w", encoding="utf-8") as f:
        f.write(ref_ph)
    print(f"Reference phonemes saved to {ref_ph_path}")


class NoPhonemesSearchResult(Exception):
    """Exception raised when no search results are found."""

    pass


@dataclass
class PhonemesSearchSpan:
    """Represents a position in the Uthmani Quran text.

    All indices are 0‑based except sura and aya which are 1‑based.

    Attributes:
        sura_idx: Sura number (1..114)
        aya_idx: Aya number (1..)
        uthmani_word_idx: 0‑based index of the word within the aya
        uthmani_char_idx: 0‑based character index within the word
                          (inclusive for start, exclusive for end)
        phonemes_idx: 0‑based index in the phoneme sequence
                      (inclusive for start, exclusive for end)
    """

    sura_idx: int
    aya_idx: int
    uthmani_word_idx: int
    uthmani_char_idx: int
    phonemes_idx: int


@dataclass
class PhonmesSearhResult:
    """Result of a phonetic search containing start and end spans.

    Attributes:
        start: Span marking the beginning of the match.
        end: Span marking the end of the match (exclusive).
    """

    start: PhonemesSearchSpan
    end: PhonemesSearchSpan


class PhoneticSearch:
    """Fuzzy search in the Quran phonetic script using precomputed index.

    Loads the index (ph_index.npy) and reference phoneme string (ref_norm_ph.txt)
    and provides methods to search for phonetic patterns.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Load the index and reference phoneme string.

        Args:
            data_dir: Directory containing 'ph_index.npy' and 'ref_norm_ph.txt'.
                      If None, uses the package's default 'quran-script' folder.

        Raises:
            FileNotFoundError: If either required file is missing.
            ValueError: If reference length does not match index length.
        """
        if data_dir is None:
            data_dir = Path(pkg_resources.files("quran_transcript")) / "quran-script"
        else:
            data_dir = Path(data_dir)

        # Load index: [sura, aya, word_idx, char_idx, ph_idx_start]
        index_path = data_dir / "ph_index.npy"
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        self.index = np.load(index_path)  # shape (N, 5), dtype uint16

        # Load reference phoneme string (normalized: first phoneme of each group)
        ref_path = data_dir / "ref_norm_ph.txt"
        if not ref_path.exists():
            raise FileNotFoundError(f"Reference file not found: {ref_path}")
        with open(ref_path, "r", encoding="utf-8") as f:
            self.ref_ph_norm = f.read().strip()

        # Verify consistency
        if len(self.ref_ph_norm) != len(self.index):
            raise ValueError(
                f"Reference length ({len(self.ref_ph_norm)}) does not match "
                f"index length ({len(self.index)})"
            )

    def _normalize_query(self, query: str) -> str:
        """Apply the same normalization to the query as was used for the index.

        Args:
            query: Raw phonetic query string.

        Returns:
            Normalized query string (first character of each phoneme group).
        """
        groups = chunck_phonemes(query)
        return normalize_phonetic_groups(groups)

    def _ref_idx_to_span(self, ref_idx: int, end=False) -> PhonemesSearchSpan:
        """Convert a reference index (ph_idx_start) to a PhonemesSearchSpan.

        Args:
            ref_idx: Index into the reference phoneme string (and correspondingly into the index array).
            end: If True, return the span using the uth_char_end_idx and ph_end_idx columns;
                 otherwise use start columns.

        Returns:
            PhonemesSearchSpan corresponding to that reference position.

        Raises:
            IndexError: If ref_idx is out of range.
        """
        if ref_idx < 0 or ref_idx >= len(self.index):
            raise IndexError(f"Reference index {ref_idx} out of range")
        row = self.index[ref_idx]
        return PhonemesSearchSpan(
            sura_idx=int(row[0]),
            aya_idx=int(row[1]),
            uthmani_word_idx=int(row[2]),
            uthmani_char_idx=int(row[4]) if end else int(row[3]),
            phonemes_idx=int(row[6]) if end else int(row[5]),
        )

    def search(
        self,
        query: str,
        start: tuple[int, int, int] | None = None,
        window: int | None = None,
        error_ratio: float = 0.1,
    ) -> list[PhonmesSearhResult]:
        """Find all substrings in the Quran phonetic script that match the query.

        Performs fuzzy matching using Levenshtein distance. The query is normalized
        internally before searching.

        TODO:
            - Implement boundary restrictions with `start` and `window` parameters.

        Args:
            query: Phonetic query string (will be normalized).
            start: Optional (sura, aya, word) tuple to limit search start.
            window: Optional maximum number of phoneme groups to search from start.
            error_ratio: Maximum allowed Levenshtein distance as a fraction of query length.
                         Must be between 0 and 1.

        Returns:
            List of PhonmesSearhResult objects, each containing start and end spans.

        Raises:
            ValueError: If query is empty or error_ratio is out of bounds.
            NoPhonemesSearchResult: If no matches are found.
        """
        if not query:
            raise ValueError("Query is longer then the Holy Quarn Text")

        assert error_ratio >= 0 and error_ratio <= 1

        # TODO:
        # Add boudary to search resutls with start and window

        # Normalize query
        norm_query = self._normalize_query(query)
        max_edits = int(len(norm_query) * error_ratio)
        outs = find_near_matches(norm_query, self.ref_ph_norm, max_l_dist=max_edits)
        if not outs:
            raise NoPhonemesSearchResult(
                "No Resulsts found!. to ensure to have resutls Please increate the error ratio"
            )

        results = []
        for out in outs:
            results.append(
                PhonmesSearhResult(
                    start=self._ref_idx_to_span(out.start, end=False),
                    end=self._ref_idx_to_span(out.end - 1, end=True),
                )
            )
        return results

    def get_uthmani_from_result(self, r: PhonmesSearhResult) -> str:
        """Extract the Uthmani text corresponding to a search result.

        Traverses ayas from the start to the end span and collects the relevant
        Uthmani words, joining them with the Uthmani space character.

        Args:
            r: A PhonmesSearhResult object.

        Returns:
            Uthmani text snippet representing the matched portion.
        """
        out_uth_words = []
        aya = Aya(r.start.sura_idx, r.start.aya_idx)
        start_word_idx = r.start.uthmani_word_idx
        while True:
            if (
                aya.get().sura_idx == r.end.sura_idx
                and aya.get().aya_idx == r.end.aya_idx
            ):
                out_uth_words.extend(
                    aya.get().uthmani_words[start_word_idx : r.end.uthmani_word_idx + 1]
                )
                break
            else:
                out_uth_words.extend(aya.get().uthmani_words[start_word_idx:])
                start_word_idx = 0
                aya = aya.step(1)

        return alph.uthmani.space.join(out_uth_words)

