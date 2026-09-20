import json
import re
from dataclasses import asdict, dataclass, field

from quran_transcript import Aya, MoshafAttributes, quran_phonetizer
from quran_transcript.alphabet import BeginHamzatWasl
from quran_transcript.alphabet import phonetic_groups as phg
from quran_transcript.alphabet import phonetics as ph
from quran_transcript.alphabet import uthmani as uth


@dataclass
class WordPart:
    sura: int
    aya: int
    word_index: int
    part_index: int
    form: str
    tag: str
    features: Dict[str, Optional[str]] = field(default_factory=dict)


@dataclass
class QuranWord:
    sura: int
    aya: int
    word_index: int
    uthmani_word: str
    parts: List[WordPart] = field(default_factory=list)

    @property
    def combined_form(self) -> str:
        return "".join(
            part.form for part in sorted(self.parts, key=lambda p: p.part_index)
        )


def parse_corpus_data(corpus_text: str) -> List[QuranWord]:
    # prepare aya
    sura_to_aya_to_uthmani_word = [[] for _ in range(114)]
    start_aya = Aya(1, 1)
    for aya in start_aya.get_ayat_after():
        info = aya.get()
        sura_to_aya_to_uthmani_word[info.sura_idx - 1].append(info.uthmani_words)

    # Skip header and copyright lines
    lines = [line.strip() for line in corpus_text.split("\n")]
    data_lines = []
    found_header = False

    for line in lines:
        if line.startswith("LOCATION\tFORM\tTAG\tFEATURES"):
            found_header = True
            continue
        if not found_header or not line or line.startswith("#"):
            continue
        if line.startswith("(") and "\t" in line:
            data_lines.append(line)

    # Group parts by word
    words_dict: Dict[Tuple[int, int, int], QuranWord] = {}

    for line in data_lines:
        parts = line.split("\t")
        if len(parts) < 4:
            continue

        loc_str, form, tag, features_str = parts[:4]

        # Parse location (1:1:1:1)
        loc_parts = loc_str.strip("()").split(":")
        try:
            sura = int(loc_parts[0])
            aya = int(loc_parts[1])
            word_idx = int(loc_parts[2])
            part_idx = int(loc_parts[3])
        except (ValueError, IndexError):
            continue

        # Parse features into dictionary
        features = {}
        for item in features_str.split("|"):
            if ":" in item:
                key, value = item.split(":", 1)
                features[key] = value
            else:
                features[item] = None

        # Create WordPart
        word_part = WordPart(
            sura=sura,
            aya=aya,
            word_index=word_idx,
            part_index=part_idx,
            form=form,
            tag=tag,
            features=features,
        )

        # Group into QuranWord
        word_key = (sura, aya, word_idx)
        if word_key not in words_dict:
            try:
                words_dict[word_key] = QuranWord(
                    sura=sura,
                    aya=aya,
                    word_index=word_idx,
                    uthmani_word=sura_to_aya_to_uthmani_word[sura - 1][aya - 1][
                        word_idx - 1
                    ],
                )
            except Exception as e:
                print(sura, aya, word_idx)
                print(Aya(sura, aya))
                print(sura_to_aya_to_uthmani_word[sura - 1][aya - 1])
                raise e

        words_dict[word_key].parts.append(word_part)

    # Sort parts within each word
    for word in words_dict.values():
        word.parts.sort(key=lambda p: p.part_index)

    quran_words = list(words_dict.values())
    sura_to_aya_to_q_word = [[] for _ in range(114)]
    for q_word in quran_words:
        sura_idx = q_word.sura - 1
        aya_idx = q_word.aya - 1
        if aya_idx >= len(sura_to_aya_to_q_word[sura_idx]):
            sura_to_aya_to_q_word[sura_idx].append([])
        sura_to_aya_to_q_word[sura_idx][aya_idx].append(q_word)

    for sura_idx in range(len(sura_to_aya_to_uthmani_word)):
        for aya_idx in range(len(sura_to_aya_to_uthmani_word[sura_idx])):
            uthmani_len = len(sura_to_aya_to_uthmani_word[sura_idx][aya_idx])
            q_word_len = len(sura_to_aya_to_q_word[sura_idx][aya_idx])
            if uthmani_len != q_word_len:
                print(
                    f"Index: ({sura_idx + 1}, {aya_idx + 1})# of Uthmani words: {uthmani_len}, # of corpus words: {q_word_len}"
                )
                print("-" * 10)

    print("Print attempt to fix mislighnment")
    miss_aligned = {
        (2, 181): 3,
        (8, 6): 4,
        (13, 37): 8,
        (37, 130): 3,
    }
    for sura_abs_idx, aya_abs_idx in miss_aligned:
        sura_idx = sura_abs_idx - 1
        aya_idx = aya_abs_idx - 1
        word_idx = miss_aligned[(sura_abs_idx, aya_abs_idx)] - 1
        sura_to_aya_to_q_word[sura_idx][aya_idx][word_idx].uthmani_word = " ".join(
            sura_to_aya_to_uthmani_word[sura_idx][aya_idx][word_idx : word_idx + 2]
        )
        print(sura_to_aya_to_q_word[sura_idx][aya_idx][word_idx].uthmani_word)
        for idx in range(word_idx + 1, len(sura_to_aya_to_q_word[sura_idx][aya_idx])):
            sura_to_aya_to_q_word[sura_idx][aya_idx][
                idx
            ].uthmani_word = sura_to_aya_to_uthmani_word[sura_idx][aya_idx][idx + 1]

    # fixed_quran_words = []
    # for sura_idx in range(len(sura_to_aya_to_q_word)):
    #     for aya_idx in range(len(sura_to_aya_to_q_word[sura_idx])):
    #         fixed_quran_words += sura_to_aya_to_q_word[sura_idx][aya_idx]

    return quran_words


def filter_words(
    quran_words: list[QuranWord],
    regs: str,
    tags: list[str] | str,
    part_idx: int | None = None,
    trans_func=None,
    trans_func_out=lambda x: x,
    trans_func_kwargs: dict = {},
    print_sets=False,
    verbose=True,
):
    if isinstance(tags, str):
        tags = [tags]
    tags = set(tags)
    word_forms = set()
    counter = 0
    for q_word in quran_words:
        if trans_func:
            txt = trans_func_out(trans_func(q_word.uthmani_word, **trans_func_kwargs))
        else:
            txt = q_word.uthmani_word
        re_outs = re.finditer(regs, txt)
        for re_out in re_outs:
            for target_tag in tags:
                if part_idx is not None:
                    parts = [q_word.parts[part_idx]]
                else:
                    parts = q_word.parts
                for part in parts:
                    if (part.tag == target_tag) or (target_tag == "all"):
                        counter += 1
                        word_forms.add(txt)
                        if verbose:
                            print(f"Case: `{counter}`")
                            print(re_out)
                            print(q_word.uthmani_word)
                            print("Index: ", q_word.sura, q_word.aya, q_word.word_index)
                            print("-" * 40)
                            print("\n" * 2)

    if print_sets:
        print(f"Word Forms `{len(word_forms)}`")
        for word in word_forms:
            print(f"'{word}'")

    return word_forms


def write_begin_hamzat_wasl(quran_words: list[QuranWord], path: str):
    al_group_jamda = filter_words(
        quran_words,
        regs=f"^{uth.hamzat_wasl}{uth.lam}",
        tags=["N", "PN", "ADJ", "IMPN", "PRON", "DEM", "REL", "T", "LOC"],
        part_idx=0,
        verbose=False,
        print_sets=False,
    )
    al_group_zaeda = filter_words(
        quran_words,
        regs=f"^{uth.hamzat_wasl}{uth.lam}",
        tags="DET",
        part_idx=0,
        verbose=False,
        print_sets=False,
    )

    verbs_group = filter_words(
        quran_words,
        regs=f"^{uth.hamzat_wasl}",
        tags="V",
        part_idx=0,
        verbose=False,
        print_sets=False,
    )

    names_group = filter_words(
        quran_words,
        regs=f"^{uth.hamzat_wasl}",
        tags=["N", "PN", "ADJ", "IMPN", "PRON", "DEM", "REL", "T", "LOC"],
        part_idx=0,
        verbose=False,
        print_sets=False,
    )
    names_group = names_group - al_group_jamda

    names_verbs_inter = names_group.intersection(verbs_group)
    hazat_wasl_begin = BeginHamzatWasl(
        verbs_nouns_inter=names_verbs_inter,
        damma_aarida_verbs={
            "ٱمْشُوا۟",
            "ٱبْنُوا۟",
            "ٱقْضُوٓا۟",
            "ٱئْتُوا۟",
            "ٱئْتُونِى",
        },
        verbs=verbs_group,
        nouns=names_group,
    )
    data = asdict(hazat_wasl_begin)
    for k in data:
        data[k] = list(data[k])
    with open(path, "w+", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Example usage:
if __name__ == "__main__":
    file_path = "./quran-script/quranic-corpus-morphology-0.4.txt"
    with open(file_path, "r", encoding="utf-8") as f:
        corpus_text = f.read()

    quran_words = parse_corpus_data(corpus_text)

    # # Filtering
    # print("\n\nVerbs start with Lam\n\n")
    # filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}{uth.lam}",
    #     tags="V",
    # )

    # print("\n\nالأسماء المعرفة\n\n")
    # filter_words(
    #     quran_words,
    #     regs=f"{uth.lam}{uth.kasra}?{uth.lam}{uth.shadda}{uth.fatha}{uth.haa}.(?![{uth.baa}{uth.waw}])",
    #     # tags=["PN", "N"],
    #     tags="all",
    #     part_idx=0,
    #     print_sets=True,
    # )

    # # Filtering
    # print("\n\nالاسم المعرف بال\n\n")
    # filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}{uth.lam}",
    #     tags="DET",
    # )

    # print("\n\nالاسم المكتوب بال الجامدة\n\n")
    # al_group_jamda = filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}{uth.lam}",
    #     tags=["N", "PN", "ADJ", "IMPN", "PRON", "DEM", "REL", "T", "LOC"],
    #     part_idx=0,
    #     verbose=False,
    #     print_sets=False,
    # )
    # print(f"Al group Jameda: {len(al_group_jamda)}")
    # al_group_zaeda = filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}{uth.lam}",
    #     tags="DET",
    #     part_idx=0,
    #     verbose=False,
    #     print_sets=False,
    # )
    # print(f"Al group Zeda: {len(al_group_zaeda)}")
    #
    # print("\n\nالأفعلا \n\n")
    # verbs_group = filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}",
    #     tags="V",
    #     part_idx=0,
    #     verbose=False,
    #     print_sets=False,
    # )
    # letters = f"{uth.pure_letters_group}{uth.hamazat_group}"
    # sel_verbs_group = filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}(?:{uth.noon}[{uth.noon_ikhfaa_group}]|[{letters}]{uth.shadda}|(?:{uth.noon}{uth.meem_iqlab}|[{letters}][{uth.harakat_group}{uth.ras_haaa}])[{letters}])(.)",
    #     tags="V",
    #     part_idx=0,
    #     verbose=True,
    #     print_sets=False,
    # )
    #
    # print(f"Len of verbs: {len(verbs_group)}")
    # print(f"Len of selected: {len(sel_verbs_group)}")
    # print("Missings:")
    # for v in verbs_group - sel_verbs_group:
    #     print(f"'{v}'")
    #
    # print("\n\nالأسماء\n\n")
    # names_group = filter_words(
    #     quran_words,
    #     regs=f"^{uth.hamzat_wasl}",
    #     tags=["N", "PN", "ADJ", "IMPN", "PRON", "DEM", "REL", "T", "LOC"],
    #     part_idx=0,
    #     verbose=False,
    #     print_sets=False,
    # )
    # names_group = names_group - al_group_jamda
    # print(f"Len of names: {len(names_group)}")
    #
    # print(f"Names Verb Intersection: {verbs_group.intersection(names_group)}")
    # print(f"Names Al Zeda Intersection: {names_group.intersection(al_group_zaeda)}")
    # print(f"Verbs Al Zeda Intersection: {verbs_group.intersection(al_group_zaeda)}")
    # print(f"Verbs Al Jamida Intersection: {verbs_group.intersection(al_group_jamda)}")

    # write_begin_hamzat_wasl(quran_words, "./quran-script/begin_with_hamzat_wasl.json")

    # print("\n\nالراء الساكنو سكون عارض\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     regs=f"{uth.hamzat_wasl}{uth.raa}{uth.ras_haaa}",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    # )

    # print("\n\nاسم الله قبل التحويل\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     f"({uth.lam}{uth.kasra}?{uth.lam}{uth.shadda}{uth.fatha})({uth.haa}(?:.|$)(?![{uth.baa}{uth.waw}]))",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    # )

    print("\n\nاسم الله\n\n")
    raa_group = filter_words(
        quran_words,
        regs=f"(?<!{ph.jeem})(?<!{ph.daal})(?<!{ph.taa}{ph.fatha}{ph.waw})(.){uth.space}?{ph.lam}{{2}}{ph.fatha}{ph.alif}{{2,6}}{ph.haa}(?!{ph.dama}{ph.meem}(?!{ph.meem}))",
        tags="all",
        # part_idx=0,
        verbose=False,
        print_sets=True,
        trans_func=quran_phonetizer,
        trans_func_out=lambda x: x.phonemes,
        trans_func_kwargs={
            "moshaf": MoshafAttributes(
                rewaya="hafs",
                madd_monfasel_len=4,
                madd_mottasel_len=4,
                madd_mottasel_waqf=4,
                madd_aared_len=4,
                # tasheel_or_madd='tasheel',
            ),
        },
    )

    # print("\n\nحرف الراء\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     regs=f"{ph.raa}{uth.fatha}{ph.alif}",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    #     trans_func=quran_phonetizer,
    #     trans_func_out=lambda x: x.phonemes,
    #     trans_func_kwargs={
    #         "moshaf": MoshafAttributes(
    #             rewaya="hafs",
    #             madd_monfasel_len=4,
    #             madd_mottasel_len=4,
    #             madd_mottasel_waqf=4,
    #             madd_aared_len=4,
    #             # tasheel_or_madd='tasheel',
    #         ),
    #     },
    # )

    # print("\n\nراء نذر\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     regs=f"{ph.waw}{ph.fatha}{ph.noon}{ph.dama}{ph.thaal}{uth.dama}{ph.raa}$",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    #     trans_func=quran_phonetizer,
    #     trans_func_out=lambda x: x.phonemes,
    #     trans_func_kwargs={
    #         "moshaf": MoshafAttributes(
    #             rewaya="hafs",
    #             madd_monfasel_len=4,
    #             madd_mottasel_len=4,
    #             madd_mottasel_waqf=4,
    #             madd_aared_len=4,
    #             # tasheel_or_madd='tasheel',
    #         ),
    #     },
    # )

    # print("\n\nراء يسر\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     regs=f"[{uth.hamza}{uth.yaa}]{uth.fatha}{uth.seen}{uth.raa}$",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    #     trans_func=quran_phonetizer,
    #     trans_func_out=lambda x: x.phonemes,
    #     trans_func_kwargs={
    #         "moshaf": MoshafAttributes(
    #             rewaya="hafs",
    #             madd_monfasel_len=4,
    #             madd_mottasel_len=4,
    #             madd_mottasel_waqf=4,
    #             madd_aared_len=4,
    #             # tasheel_or_madd='tasheel',
    #         ),
    #     },
    # )

    # print("\n\nالمبدوء بساكن\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     regs=f"^.[^{uth.harakat_group}]",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    #     trans_func=quran_phonetizer,
    #     trans_func_out=lambda x: x.phonemes,
    #     trans_func_kwargs={
    #         "moshaf": MoshafAttributes(
    #             rewaya="hafs",
    #             madd_monfasel_len=4,
    #             madd_mottasel_len=4,
    #             madd_mottasel_waqf=4,
    #             madd_aared_len=4,
    #             # tasheel_or_madd='tasheel',
    #         ),
    #     },
    # )

    # print("\n\nالمبدوء بساكن\n\n")
    # raa_group = filter_words(
    #     quran_words,
    #     regs=f"^.{uth.ras_haaa}",
    #     tags="all",
    #     # part_idx=0,
    #     verbose=False,
    #     print_sets=True,
    # )
