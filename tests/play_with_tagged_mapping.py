import re
from dataclasses import dataclass

from quran_transcript.phonetics.conv_base_operation import MappingPos

# Avoiding catching preious tag patter for example <x:aa><y:aa> we will hit the same match again so we want to have a moving cursor to avoid that

_groups = re.compile(
    r"""
      (?P<escape>\\\\)                              # literal backslash  \\
    | \\g<(?P<gname>[A-Za-z_][A-Za-z0-9_]*|\d+)>    # \g<name>  or  \g<1>
    | \\(?P<gnum>[0-9]{1,2})                        # \1 .. \99
    """,
    re.VERBOSE,
)
_mapped_tags = re.compile(
    r"<(\w\d?):((?:\\.|\[(?:\\.|[^\]\\])*\]|\(\?P<\w+>|[^>\\])*)>"
)


def _expand_replacement(rep: str, match: re.Match) -> str:
    """Expand backreferences in a replacement string for a single match."""
    result = []
    last_end = 0

    for m in _groups.finditer(rep):
        result.append(rep[last_end : m.start()])
        if m.group("escape"):
            result.append("\\")
        elif m.group("gname") is not None:
            name = m.group("gname")
            result.append(match.group(int(name) if name.isdigit() else name))
        elif m.group("gnum") is not None:
            result.append(match.group(int(m.group("gnum"))))
        last_end = m.end()

    result.append(rep[last_end:])
    return "".join(result)


@dataclass
class MapTag:
    start: int
    end: int
    tag: str
    pat: str
    rep: str
    compiled_pat: re.Pattern


class MappedTagPrasingError(Exception): ...


class MappedTagPrasingCardinalityError(Exception): ...


def parse_tags(pat: re.Pattern, rep: re.Pattern) -> list[MapTag]:

    rep_tag_to_text = {}
    last_idx = 0
    for match in _mapped_tags.finditer(rep):
        if last_idx != match.start():
            raise MappedTagPrasingError(
                f"`rep` should be connected like `<a:abc><b:cde>` but found "
                f"out-of-bounds element at position {match.start()}: "
                f"`{rep[last_idx : match.start()]}`",
            )
        rep_tag_to_text[match.group(1)] = match.group(2)
        last_idx = match.end()
    if last_idx != len(rep):
        raise MappedTagPrasingError(
            f"`rep` should be connected like `<a:abc><b:cde>` but found "
            f"out-of-bounds element from position {last_idx}: `{rep[last_idx:]}`",
        )

    mapped_tags = []
    offset = 0
    last_idx = 0
    for match in _mapped_tags.finditer(str(pat)):
        # non tag pattern
        start = match.start()
        if start != last_idx:
            mapped_tags.append(
                MapTag(
                    start=last_idx,
                    end=start,
                    pat=pat[last_idx:start],
                    rep="",
                    tag="",
                    compiled_pat=re.compile(pat[last_idx:start]),
                )
            )
        tag = match.group(1)
        if tag not in rep_tag_to_text:
            raise MappedTagPrasingError(
                f"Tag: `{tag}` is found in the pattern but not found in the replacment"
            )
        start_offset = match.end(1) - match.start(1) + 2
        mapped_tag = MapTag(
            start=match.start(2) - offset - start_offset,
            end=match.end(2) - offset - start_offset,
            tag=tag,
            pat=match.group(2),
            rep=rep_tag_to_text[tag],
            compiled_pat=re.compile(match.group(2)),
        )
        offset += start_offset + 1
        mapped_tags.append(mapped_tag)
        last_idx = match.end()

    # last non tag pattern
    start = len(pat)
    if start != last_idx:
        mapped_tags.append(
            MapTag(
                start=last_idx,
                end=start,
                pat=pat[last_idx:start],
                rep="",
                tag="",
                compiled_pat=re.compile(pat[last_idx:start]),
            )
        )

    return mapped_tags


def sub_with_tagged_mapping(
    pat: re.Pattern,
    rep: re.Pattern,
    text: str,
    mappings: list[MappingPos],
) -> tuple[str, list[MappingPos]]:
    """
    Rules:
    * This a modified re.sub the defines explicit mapping from `pat` to `rep`
    * `pat` should start with `M:`
    * EX: pat = r"<x:abc>D<y1:(def)>"
          rep = r"<x:ABC><y1:\1>"
    <x:abc>
    ^^    ^
    -^----- This is called a `tag` These brackets holds the pattern and is no rleated to re gropus.
     ^
     ^ `x` is called  the tag name and composed only of a single charcter and it can followed by a number like `x`
     `abc` is called `tag pattern`

    * for the rep <x:ABC> `ABC` is called `tag replacement`
    * rep patterns Have to be connected like r"<x:ABC><y1:\1>" but not r"<x:ABC>N<y1:\1>" (N) is not mapped
    * if a group of patterns is existis in the `pat` and does not exist in the `rep` it will be deleted like `D` in the example
    * the len of `tag pattern` and `tag replacemnt` has either to be euqal in length or one to many (on for `tag pattern` and many for `tag replacemnt`
    """

    assert str(pat).startswith("M:")
    pat = str(pat)[2:]

    out_text = ""
    mapped_tags = parse_tags(pat, rep)
    re_pat = ""
    re_rep = ""
    for m_tag in mapped_tags:
        re_pat += m_tag.pat
        re_rep += m_tag.rep

    re_pat = re.compile(re_pat)

    in_pos = 0
    out_pos = 0
    for match in re_pat.finditer(text):
        out_text += text[in_pos : match.start()]  # text not cpatured by the pat
        in_pos = match.start()
        for m_tag in mapped_tags:
            # pattern exist not deleted
            tag_mat = m_tag.compiled_pat.match(
                text, pos=in_pos
            )  # Avoiding catching preious tag patter for example <x:aa><y:aa> we will hit the same match again so we want to have a moving cursor to avoid that
            assert tag_mat != None
            tag_pat_text = tag_mat.group()
            tag_pat_len = len(tag_pat_text)

            if m_tag.tag != "" and m_tag.rep != "":
                tag_rep_text = _expand_replacement(m_tag.rep, tag_mat)
                if tag_pat_len == len(tag_rep_text):
                    # equal mapping
                    for in_idx, out_idx in zip(
                        range(in_pos, in_pos + tag_pat_len),
                        range(out_pos, out_pos + tag_pat_len),
                    ):
                        mappings[in_idx].pos = (out_idx, out_idx + 1)
                elif tag_pat_len == 1:
                    # one to many
                    mappings[in_pos].pos = (
                        out_pos,
                        out_pos + tag_pat_len,
                    )
                else:
                    raise MappedTagPrasingCardinalityError(
                        f"Not supporting many to many or many to one mapping you want to map: `{tag_pat_text}` to `{tag_rep_text}` corresponds to tag: `{m_tag}`"
                    )
            elif m_tag.rep == "":
                tag_rep_text = ""
                # Deletion
                for in_idx in range(in_pos, in_pos + tag_pat_len):
                    mappings[in_idx].pos = (out_pos, out_pos)
                    mappings[in_idx].deleted = True

            in_pos += tag_pat_len
            out_pos += len(tag_rep_text)
            out_text += tag_rep_text
        in_pos = match.end()

    out_text += text[in_pos:]
    return out_text, mappings


if __name__ == "__main__":
    # print(sub_with_tagged_mapping(r"(abc)", r"\1", "abc abc d", []))
    in_text = "aNdef"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = [
        MappingPos(pos=(0, 1)),
        MappingPos(pos=(1, 2)),
        MappingPos(pos=(2, 3)),
        MappingPos(pos=(3, 4)),
        MappingPos(pos=(4, 5)),
    ]

    # WARN: Many to one Parsing error
    # in_text = "acNdef"
    # pat = r"M:<x:[ab]c>.<r:(def)>"
    # rep = r"<x:A><r:\1>"
    # mappings = [
    #     MappingPos(pos=(0, 1)),
    #     MappingPos(pos=(1, 2)),
    #     MappingPos(pos=(2, 3)),
    #     MappingPos(pos=(3, 4)),
    #     MappingPos(pos=(4, 5)),
    #     MappingPos(pos=(5, 6)),
    # ]
    # WARN: Many to many Parsing error
    # in_text = "acNdef"
    # pat = r"M:<x:[ab]c>.<r:(def)>"
    # rep = r"<x:ABC><r:\1>"
    # mappings = [
    #     MappingPos(pos=(0, 1)),
    #     MappingPos(pos=(1, 2)),
    #     MappingPos(pos=(2, 3)),
    #     MappingPos(pos=(3, 4)),
    #     MappingPos(pos=(4, 5)),
    #     MappingPos(pos=(5, 6)),
    # ]

    out_text, out_mappings = sub_with_tagged_mapping(
        pat,
        rep,
        in_text,
        mappings,
    )
    print(f"pat: `{pat}`")
    print(f"rep: `{rep}`")
    print(f"IN  text: `{in_text}`")
    print(f"Out text: `{out_text}`")
    print("*" * 40)

    for idx, uth_c in enumerate(in_text):
        print(f"IN_IDX: `{idx}`, SPAN: `{out_mappings[idx]}`")
        ph_c = ""
        mapping = out_mappings[idx]
        ph_c = out_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")
        print("-" * 40)
