import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .tajweed_rulses import (
    TAJ_TYPE_TO_RULE,
    ExplainedTajweedRule,
    TajweedRuleMetadata,
    TajweedRuleType,
    get_full_taj_rule_type,
)

TashkeelErrorType: TypeAlias = Literal["fatha", "dama", "kasra", "skoon"]

ReciterErrOp: TypeAlias = Literal["e", "i", "r", "d"]


@dataclass(frozen=True)
class PhonemesGroupsAligment:
    op_type: Literal["insert", "replace", "delete", "equal"]
    ref_idx: int
    pred_idx: int


@dataclass(frozen=True)
class ReciterError:
    """A single recitation error.

    Tajweed rule fields contain :class:`ExplainedTajweedRule` snapshots, ready
    for display or serialization.
    """

    uthmani_pos: tuple[int, int]  # start, end
    ph_pos: tuple[int, int]  # start, end
    error_type: Literal["tajweed", "normal", "tashkeel"]
    speech_error_type: Literal["insert", "delete", "replace"]
    expected_ph: str
    preditected_ph: str
    expected_len: int = -1
    predicted_len: int = -1
    expected_tashkeel: TashkeelErrorType | None = None
    predicted_tashkeel: TashkeelErrorType | None = None
    ref_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)
    inserted_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)
    replaced_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)
    missing_tajweed_rules: list[ExplainedTajweedRule] = field(default_factory=list)


@dataclass(frozen=True)
class ReciterErrPatMatches:
    """Errors produced by a pattern and the alignments it dominates.

    ``covered_alignments`` contains every alignment consumed by an accepted
    pattern match that produced an error. Callers can use it to suppress
    generic errors for those alignments, because the pattern error already
    explains them.
    """

    errors: list[ReciterError]
    covered_alignments: frozenset[PhonemesGroupsAligment]


class ReciterErrPatParsingError(Exception): ...


@dataclass
class ReciterErrPatTag:
    start: int
    end: int
    op: ReciterErrOp
    tag: str  # "" when unnamed
    pat: str  # exact regex segment used in the full pattern
    compiled_pat: re.Pattern  # re.compile(pat)


# A tag is `<op[,name]:tag pattern>`. The tag pattern is a regex source and
# must not contain a literal `>` outside a character class because `>` closes
# the tag.
_reciter_error_tags = re.compile(
    r"<([eird])(?:,([a-z][0-9]?))?:"
    r"((?:\\.|\[(?:\\.|[^\]\\])*\]|\(\?P<\w+>|[^>\\])*)>"
)


def parse_reciter_error_tags(
    pat: str,
    rules: dict[str, TajweedRuleType],
) -> list[ReciterErrPatTag]:
    """Parse a reciter-error pattern into its tags.

    Args:
        pat: The pattern without the leading ``R:`` prefix.
        rules: Mapping from named tag to the Tajweed rule it requires.

    Raises:
        ReciterErrPatParsingError: If the pattern is malformed or if a tag is
            used inconsistently with ``rules``.
    """
    for rule_tag, rule_type in rules.items():
        if not isinstance(rule_type, TajweedRuleType):
            raise ReciterErrPatParsingError(
                f"Rule type of tag `{rule_tag}` has to be a `TajweedRuleType` "
                f"but got `{type(rule_type).__name__}`"
            )

    mapped_tags: list[ReciterErrPatTag] = []
    pat_tags: set[str] = set()
    last_idx = 0
    prev_op: ReciterErrOp | None = None

    for match in _reciter_error_tags.finditer(pat):
        if last_idx != match.start():
            raise ReciterErrPatParsingError(
                f"`pat` should be connected like `<e,t0:abc><i:d>` but found "
                f"out-of-bounds element at position {match.start()}: "
                f"`{pat[last_idx : match.start()]}`"
            )

        op: ReciterErrOp = match.group(1)
        tag = match.group(2) or ""
        tag_pat = match.group(3)

        if tag:
            if tag in pat_tags:
                raise ReciterErrPatParsingError(
                    f"Repeated tag `{tag}` at position `{match.start(2)}` "
                    f"in `pat` pattern. Tag should be used only once in the pat!"
                )
            pat_tags.add(tag)

        if not tag_pat:
            raise ReciterErrPatParsingError(
                f"Empty tag pattern at position `{match.start(3)}`"
            )

        try:
            compiled_tag_pat = re.compile(tag_pat)
        except re.error as exc:
            raise ReciterErrPatParsingError(
                f"Invalid regex in tag `{tag}` at position `{match.start(3)}`: {exc}"
            ) from exc

        if compiled_tag_pat.fullmatch("") is not None and tag in rules:
            raise ReciterErrPatParsingError(
                f"Tag pattern `{tag_pat}` at position `{match.start(3)}` "
                f"can match an empty string but tag `{tag}` requires a "
                f"Tajweed rule. An empty match has no reference groups to "
                f"anchor the rule"
            )

        # One operation letter per run of same-op tags. The tag pattern is
        # wrapped in a non-capturing group so alternation keeps its meaning
        # without shifting the user's capture-group numbering.
        op_prefix = op if op != prev_op else ""
        full_pat = f"{op_prefix}(?:{tag_pat})"

        mapped_tags.append(
            ReciterErrPatTag(
                start=match.start(),
                end=match.end(),
                op=op,
                tag=tag,
                pat=full_pat,
                compiled_pat=re.compile(full_pat),
            )
        )
        prev_op = op
        last_idx = match.end()

    if last_idx != len(pat):
        raise ReciterErrPatParsingError(
            f"`pat` should be connected like `<e,t0:abc><i:d>` but found "
            f"out-of-bounds element from position {last_idx}: `{pat[last_idx:]}`"
        )

    if not mapped_tags:
        raise ReciterErrPatParsingError(
            "`pat` has to contain at least one tag like `<e,t0:abc>`"
        )

    # Every tag in `rules` must exist in `pat` and must not be an insert tag:
    # insert tags have no reference groups, so a strict Tajweed lookup would
    # always fail.
    for m_tag in mapped_tags:
        if m_tag.tag in rules and m_tag.op == "i":
            raise ReciterErrPatParsingError(
                f"tag: `{m_tag.tag}` is an insert tag and can not require a "
                f"Tajweed rule in `rules`"
            )
    for rule_tag in rules:
        if rule_tag not in pat_tags:
            raise ReciterErrPatParsingError(
                f"tag: `{rule_tag}` exists in the `rules` but does not "
                f"exist in the `pat`"
            )

    return mapped_tags


_ALIGN_TO_OP: dict[str, ReciterErrOp] = {
    "equal": "e",
    "insert": "i",
    "replace": "r",
    "delete": "d",
}


def _encode_alignments(
    ref_ph_groups: list[str],
    pred_ph_groups: list[str],
    ph_groups_align: list[PhonemesGroupsAligment],
) -> tuple[str, list[int]]:
    """Encode alignments as one op letter per run followed by group first chars.

    Example::

        equal A, equal B, equal C, insert D, delete E
        -> encoded = "eABCiDdE"
        -> enc_to_align = [0, 0, 1, 2, 3, 3, 4, 4, 5]

    ``enc_to_align`` maps every encoded character index to its alignment index.
    Its last entry maps the end of the encoded string to
    ``len(ph_groups_align)``.
    """
    parts: list[str] = []
    enc_to_align: list[int] = []
    prev_op: ReciterErrOp | None = None

    for i, align in enumerate(ph_groups_align):
        op = _ALIGN_TO_OP[align.op_type]

        if op != prev_op:
            parts.append(op)
            enc_to_align.append(i)

        if align.op_type == "delete":
            group = ref_ph_groups[align.ref_idx]
        else:
            group = pred_ph_groups[align.pred_idx]

        parts.append(group[0])
        enc_to_align.append(i)
        prev_op = op

    enc_to_align.append(len(ph_groups_align))
    return "".join(parts), enc_to_align


def _group_char_offsets(ph_groups: list[str]) -> list[int]:
    """Cumulative character offsets of phoneme groups (inclusive end)."""
    offsets = [0]
    for group in ph_groups:
        offsets.append(offsets[-1] + len(group))
    return offsets


def _static_tajweed_rules(
    wanted_types: Sequence[TajweedRuleType],
) -> list[ExplainedTajweedRule]:
    """Build static rule snapshots without runtime position data."""
    return [
        ExplainedTajweedRule.from_rule(TAJ_TYPE_TO_RULE[wanted])
        for wanted in wanted_types
    ]


class ReciterErrPatern:
    def __init__(
        self,
        pat: str,
        rules: dict[str, TajweedRuleType],
        *,
        error_type: Literal["tajweed", "normal", "tashkeel"] | None = None,
        speech_error_type: Literal["insert", "delete", "replace"] | None = None,
        err_tag: str = "",
        check_group: dict[str, Callable[[str, str], bool]] | None = None,
        inserted_tajweed_rules: Sequence[TajweedRuleType] = (),
        replaced_tajweed_rules: Sequence[TajweedRuleType] = (),
        missing_tajweed_rules: Sequence[TajweedRuleType] = (),
    ) -> None:
        """Detect reciter error patterns and build human readable errors.

        This is a minimal layer on top of ``re`` that captures error patterns
        in the predicted phoneme groups produced by a reciter.

        The predicted/reference alignments are encoded as one operation letter
        per maximal run of the same alignment operation followed by the first
        character of every phoneme group in that run. For example::

            equal A, equal B, equal C, insert D, delete E
            -> "eABCiDdE"

        ``pat`` should start with ``R:`` [R]eciter. A pattern is a connected
        sequence of tags::

            pat = r"R:<e,t0:abc><i:d>"
            <e,t0:abc>
            ^^ ^     ^
            -^-^------  This is called a `tag`; the brackets `<...>` hold the
             ^ ^        pattern and are not related to re groups.
             ^ ^
             ^ - > `e` is the **operation type**: `e` equal, `i` insert,
                    `r` replace, or `d` delete.
               ^ - > `t0` is the optional **tag name**, a single lowercase
                      character optionally followed by one digit (`x`, `y3`).
             `abc` is the tag pattern; every character represents the first
             character of a phoneme group.

        Operation matching side:

        * ``e`` matches the **predicted** group first char (the reference char
          is the same under an equal alignment).
        * ``i`` matches the **predicted** group first char.
        * ``r`` matches the **predicted** group first char.
        * ``d`` matches the **reference** group first char.

        Rules:

        * Tags have to be connected like ``<d,t0:ABC><r:m>`` but not
          ``<d,t0:ABC>N<r:m>``; text outside tags raises
          :class:`ReciterErrPatParsingError`.
        * Tag names are ``[a-z][0-9]?`` and have to be unique in ``pat``.
        * A tag name in ``rules`` has to exist as a named tag in ``pat`` and
          can not be an insert tag: insert tags have no reference groups, so a
          strict Tajweed lookup would always fail. For every remaining named
          tag in ``rules`` the matched reference span has to contain that
          :class:`TajweedRuleType`; otherwise the match is skipped. A named tag
          that is not in ``rules`` is only contextual.
        * Tag patterns are regex sources. They must not be empty. They may
          match the empty string (an optional tag), unless the tag is in
          ``rules`` — an empty match has no reference groups to anchor a
          Tajweed rule.
        * Tag patterns must not contain a literal ``>`` outside a character
          class because ``>`` closes the tag.
        * Adjacent tags with the same operation share one operation prefix:
          ``<e,t0:A><e,t1:B>`` compiles to ``e(?:A)(?:B)`` and matches
          ``eAB``.
        * Tag names do not add capture groups. Tag patterns are wrapped in
          non-capturing groups, so user-defined groups keep their numbering.

        The static rule lists (``inserted_tajweed_rules``,
        ``replaced_tajweed_rules`` and ``missing_tajweed_rules``) are reported
        as declared. Their static fields (name, description, rule type and
        correctness) come from the rule definition, while runtime position
        fields are left at sentinel values: ``(-1, -1)`` for pivots, empty
        dependency lists, an empty tag and ``golden_len = -1``.

        ``err_tag`` selects the tag whose matched alignments define the
        reported error. An empty string (the default) keeps the whole pattern
        match as the error span. A non-empty value must be a named tag in
        ``pat``; the tag's span then determines ``ph_pos``, ``uthmani_pos``,
        ``expected_ph``, ``preditected_ph``, reference rules and lengths, while
        the rest of the pattern acts as context. Pattern-level static rule
        lists are unchanged.

        ``check_group`` maps a named tag to an extra condition evaluated on
        that tag's matched span. The callable receives the joined reference
        phoneme groups (empty for a pure insert span) and the joined predicted
        phoneme groups (empty for a pure delete span) and returns ``False`` to
        reject the match, exactly like a strict rule failure. Keys must name a
        tag in ``pat``; they do not need to appear in ``rules``.

        Limitation:

        * Because the encoding emits one op letter per maximal run, a match can
          only start at a run boundary. To target a group in the middle of a
          run, include the preceding groups from that run in the tag pattern.
        * ``finditer`` is non-overlapping. If a strict rule lookup rejects a
          match, the scan continues after that match; it does not retry from
          ``match.start() + 1``.
        * Tag regexes must not consume another run's op letter. The
          ``_tag_span_ok`` check rejects such matches. Simple Arabic regexes
          (``ا+``, ``[اب]{2}``, ``ا[بت]``) are safe; ``.`` / ``.*`` may be
          rejected.
        * A backreference within one tag works (``<e,t0:(A)\\1>``), but numeric
          backreferences are resolved against the combined pattern. In a later
          tag, ``\\1`` can bind to a group defined in an earlier tag; cross-tag
          references are not supported. Use unique named groups when tags
          contain groups.
        * ``find_all`` re-matches each tag greedily at the matched position. If
          tag patterns have overlapping alternatives, for example
          ``<e,t0:AB|A><e,t1:B>`` against ``eAB``, the full pattern matches but
          the per-tag re-match can consume text needed by the next tag. This
          currently raises ``AssertionError``.
        * User-defined named groups must be unique across all tags. Duplicate
          names fail when the concatenated pattern is compiled in ``__init__``.
        """
        assert pat.startswith("R:")
        pat = pat[2:]

        self.pat = pat
        self.rules = rules
        self.error_type = error_type
        self.speech_error_type = speech_error_type
        self.err_tag = err_tag
        self.check_group = check_group or {}
        self.inserted_tajweed_rules = tuple(inserted_tajweed_rules)
        self.replaced_tajweed_rules = tuple(replaced_tajweed_rules)
        self.missing_tajweed_rules = tuple(missing_tajweed_rules)

        self.mapped_tags = parse_reciter_error_tags(pat, rules)
        named_tags = {m_tag.tag for m_tag in self.mapped_tags if m_tag.tag}
        if err_tag and err_tag not in named_tags:
            raise ReciterErrPatParsingError(
                f"`err_tag` must name a tag in `pat`; got `{err_tag}`"
            )
        for check_tag in self.check_group:
            if check_tag not in named_tags:
                raise ReciterErrPatParsingError(
                    f"`check_group` keys must name tags in `pat`; got "
                    f"`{check_tag}`"
                )
        self.re_pat = re.compile("".join(m_tag.pat for m_tag in self.mapped_tags))

    def find_all(
        self,
        ref_ph_groups: list[str],
        pred_ph_groups: list[str],
        ph_groups_align: list[PhonemesGroupsAligment],
        ref_group_rules: list[list[TajweedRuleMetadata]],
        ref_ph_to_uthmani: list[int],
    ) -> list[ReciterError]:
        """Find all non-overlapping error patterns in the alignments.

        This is a convenience wrapper around :meth:`find_all_matches` for
        callers that only need the errors.

        Args:
            ref_ph_groups: Reference phoneme groups.
            pred_ph_groups: Predicted phoneme groups.
            ph_groups_align: Reference/predicted phoneme group alignments.
            ref_group_rules: Tajweed rule metadata attached to every reference
                phoneme group.
            ref_ph_to_uthmani: Mapping from reference phonetic character index
                to Uthmani character index (with a final extra entry).

        Returns:
            One :class:`ReciterError` per accepted pattern match.
        """
        return self.find_all_matches(
            ref_ph_groups,
            pred_ph_groups,
            ph_groups_align,
            ref_group_rules,
            ref_ph_to_uthmani,
        ).errors

    def find_all_matches(
        self,
        ref_ph_groups: list[str],
        pred_ph_groups: list[str],
        ph_groups_align: list[PhonemesGroupsAligment],
        ref_group_rules: list[list[TajweedRuleMetadata]],
        ref_ph_to_uthmani: list[int],
    ) -> ReciterErrPatMatches:
        """Find all non-overlapping error patterns and their coverage.

        Args:
            ref_ph_groups: Reference phoneme groups.
            pred_ph_groups: Predicted phoneme groups.
            ph_groups_align: Reference/predicted phoneme group alignments.
            ref_group_rules: Tajweed rule metadata attached to every reference
                phoneme group.
            ref_ph_to_uthmani: Mapping from reference phonetic character index
                to Uthmani character index (with a final extra entry).

        Returns:
            The errors produced by accepted matches and the union of the
            alignments those matches consumed. An alignment is covered only
            when an accepted match consumes it and produces an error.
        """
        encoded, enc_to_align = _encode_alignments(
            ref_ph_groups,
            pred_ph_groups,
            ph_groups_align,
        )

        errors: list[ReciterError] = []
        covered: set[PhonemesGroupsAligment] = set()

        for match in self.re_pat.finditer(encoded):
            pos = match.start()
            strict_ok = True
            matched_ops: list[ReciterErrOp] = []
            tag_spans: dict[str, tuple[int, int]] = {}

            for m_tag in self.mapped_tags:
                tag_mat = m_tag.compiled_pat.match(encoded, pos=pos)
                assert tag_mat is not None

                # not ncessary
                if not self._tag_span_ok(m_tag, tag_mat):
                    strict_ok = False
                    break

                if m_tag.tag in self.rules and not self._tag_rule_ok(
                    m_tag,
                    tag_mat,
                    enc_to_align,
                    ph_groups_align,
                    ref_group_rules,
                ):
                    strict_ok = False
                    break

                if m_tag.tag in self.check_group and not self._tag_check_ok(
                    m_tag,
                    tag_mat,
                    enc_to_align,
                    ph_groups_align,
                    ref_ph_groups,
                    pred_ph_groups,
                ):
                    strict_ok = False
                    break

                a_start = enc_to_align[tag_mat.start()]
                a_end = enc_to_align[tag_mat.end()]

                if m_tag.tag:
                    tag_spans[m_tag.tag] = (a_start, a_end)

                # An optional tag that matched the empty string consumed no
                # alignments and contributes no op.
                if a_end > a_start:
                    matched_ops.append(m_tag.op)
                pos = tag_mat.end()

            if not strict_ok:
                continue

            assert pos == match.end()

            a_start = enc_to_align[match.start()]
            a_end = enc_to_align[match.end()]

            err_a_start, err_a_end = a_start, a_end
            if self.err_tag:
                err_a_start, err_a_end = tag_spans[self.err_tag]

            error = self._build_error(
                err_a_start,
                err_a_end,
                matched_ops,
                ref_ph_groups,
                pred_ph_groups,
                ph_groups_align,
                ref_group_rules,
                ref_ph_to_uthmani,
            )
            if error is not None:
                errors.append(error)
                covered.update(ph_groups_align[a_start:a_end])

        return ReciterErrPatMatches(
            errors=errors,
            covered_alignments=frozenset(covered),
        )

    def _tag_span_ok(
        self,
        m_tag: ReciterErrPatTag,
        tag_mat: re.Match,
    ) -> bool:
        """Reject a tag match that swallowed another run's operation letter."""
        text = tag_mat.group()
        offset = 1 if text and text[0] == m_tag.op else 0
        return not any(ch in "eird" for ch in text[offset:])

    def _tag_rule_ok(
        self,
        m_tag: ReciterErrPatTag,
        tag_mat: re.Match,
        enc_to_align: list[int],
        ph_groups_align: list[PhonemesGroupsAligment],
        ref_group_rules: list[list[TajweedRuleMetadata]],
    ) -> bool:
        """Check that the required rule exists in the matched reference span."""
        a_start = enc_to_align[tag_mat.start()]
        a_end = enc_to_align[tag_mat.end()]

        ref_idxs = {
            ph_groups_align[i].ref_idx
            for i in range(a_start, a_end)
            if ph_groups_align[i].op_type != "insert"
        }

        wanted = self.rules[m_tag.tag]
        return any(
            meta.rule_type == wanted
            for idx in ref_idxs
            for meta in ref_group_rules[idx]
        )

    def _tag_check_ok(
        self,
        m_tag: ReciterErrPatTag,
        tag_mat: re.Match,
        enc_to_align: list[int],
        ph_groups_align: list[PhonemesGroupsAligment],
        ref_ph_groups: list[str],
        pred_ph_groups: list[str],
    ) -> bool:
        """Run the tag's ``check_group`` condition on its matched span."""
        a_start = enc_to_align[tag_mat.start()]
        a_end = enc_to_align[tag_mat.end()]

        ref_group = "".join(
            ref_ph_groups[ph_groups_align[i].ref_idx]
            for i in range(a_start, a_end)
            if ph_groups_align[i].op_type != "insert"
        )
        pred_group = "".join(
            pred_ph_groups[ph_groups_align[i].pred_idx]
            for i in range(a_start, a_end)
            if ph_groups_align[i].op_type != "delete"
        )

        return self.check_group[m_tag.tag](ref_group, pred_group)

    def _build_error(
        self,
        a_start: int,
        a_end: int,
        matched_ops: list[ReciterErrOp],
        ref_ph_groups: list[str],
        pred_ph_groups: list[str],
        ph_groups_align: list[PhonemesGroupsAligment],
        ref_group_rules: list[list[TajweedRuleMetadata]],
        ref_ph_to_uthmani: list[int],
    ) -> ReciterError | None:
        ref_char_offsets = _group_char_offsets(ref_ph_groups)
        pred_char_offsets = _group_char_offsets(pred_ph_groups)

        ref_idxs = [
            ph_groups_align[i].ref_idx
            for i in range(a_start, a_end)
            if ph_groups_align[i].op_type != "insert"
        ]
        pred_idxs = [
            ph_groups_align[i].pred_idx
            for i in range(a_start, a_end)
            if ph_groups_align[i].op_type != "delete"
        ]

        if ref_idxs:
            ref_start, ref_end = min(ref_idxs), max(ref_idxs) + 1
        else:
            # Pure insert: use the boundary alignment as a zero-width span.
            boundary = (
                ph_groups_align[a_start].ref_idx
                if a_start < len(ph_groups_align)
                else len(ref_ph_groups)
            )
            ref_start = ref_end = boundary

        if pred_idxs:
            pred_start, pred_end = min(pred_idxs), max(pred_idxs) + 1
        else:
            # Pure delete: use the boundary alignment as a zero-width span.
            boundary = (
                ph_groups_align[a_start].pred_idx
                if a_start < len(ph_groups_align)
                else len(pred_ph_groups)
            )
            pred_start = pred_end = boundary

        ref_char_start = ref_char_offsets[ref_start]
        ref_char_end = ref_char_offsets[ref_end]
        pred_char_start = pred_char_offsets[pred_start]
        pred_char_end = pred_char_offsets[pred_end]

        expected_ph = "".join(ref_ph_groups[ref_start:ref_end])
        preditected_ph = "".join(pred_ph_groups[pred_start:pred_end])

        ph_pos = (ref_char_start, ref_char_end)
        if ref_start != ref_end:
            uthmani_pos = (
                ref_ph_to_uthmani[ref_char_start],
                ref_ph_to_uthmani[ref_char_end - 1] + 1,
            )
        else:
            uthmani_pos = (
                ref_ph_to_uthmani[ref_char_start],
                ref_ph_to_uthmani[ref_char_start],
            )

        ref_metas: list[TajweedRuleMetadata] = []
        for idx in range(ref_start, ref_end):
            ref_metas.extend(ref_group_rules[idx])

        full_rules = [
            get_full_taj_rule_type(meta, ref_ph_to_uthmani) for meta in ref_metas
        ]
        ref_tajweed_rules = [
            ExplainedTajweedRule.from_(rule, meta) for rule, meta in full_rules
        ]

        inserted_tajweed_rules = _static_tajweed_rules(self.inserted_tajweed_rules)
        replaced_tajweed_rules = _static_tajweed_rules(self.replaced_tajweed_rules)
        missing_tajweed_rules = _static_tajweed_rules(self.missing_tajweed_rules)

        expected_len = -1
        predicted_len = -1
        if expected_ph and preditected_ph and expected_ph[0] == preditected_ph[0]:
            for rule, meta in full_rules:
                if rule.correctness == "count":
                    expected_len = meta.golden_len
                    predicted_len = rule.count(expected_ph, preditected_ph)
                    break

        if self.error_type is not None:
            error_type = self.error_type
        elif ref_tajweed_rules:
            error_type = "tajweed"
        else:
            error_type = "normal"

        if self.speech_error_type is not None:
            speech_error_type = self.speech_error_type
        else:
            speech_error_type = "replace"
            for op in matched_ops:
                if op == "i":
                    speech_error_type = "insert"
                    break
                if op == "d":
                    speech_error_type = "delete"
                    break
                if op == "r":
                    speech_error_type = "replace"
                    break

        if (
            expected_ph == preditected_ph
            and not ref_tajweed_rules
            and not inserted_tajweed_rules
            and not replaced_tajweed_rules
            and not missing_tajweed_rules
        ):
            return None

        return ReciterError(
            uthmani_pos=uthmani_pos,
            ph_pos=ph_pos,
            error_type=error_type,
            speech_error_type=speech_error_type,
            expected_ph=expected_ph,
            preditected_ph=preditected_ph,
            expected_len=expected_len,
            predicted_len=predicted_len,
            expected_tashkeel=None,
            predicted_tashkeel=None,
            ref_tajweed_rules=ref_tajweed_rules,
            inserted_tajweed_rules=inserted_tajweed_rules,
            replaced_tajweed_rules=replaced_tajweed_rules,
            missing_tajweed_rules=missing_tajweed_rules,
        )
