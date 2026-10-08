from quran_transcript.phonetics.conv_base_operation import (
    init_mappings,
    sub_with_tagged_mapping,
)


def check_mapping_continuty(mappings: PhonetizerMappings):
    if mappings.uth_to_ph:
        last_end = mappings.uth_to_ph[0].pos[1]
    for idx in range(1, len(mappings.uth_to_ph)):
        if last_end != mappings.uth_to_ph[idx].pos[0]:
            raise ValueError(f"Breaking mappings continutiy at idx: {idx}")
        last_end = mappings.uth_to_ph[idx].pos[1]


if __name__ == "__main__":
    # delete
    in_text = "aNdef"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = init_mappings(in_text)

    # no mapping chainge
    in_text = "adef"
    pat = r"M:<x:[ab]><r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = init_mappings(in_text)

    # one to many + shifting
    in_text = "adef"
    pat = r"M:<x:[ab]><r:(def)>"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)

    # one to many + shifting + normal text
    in_text = "adef Hello"
    pat = r"M:<x:[ab]><r:(def)>"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)

    # one to many + shifting + on to many + normal text
    in_text = "adefn Hello"
    pat = r"M:<x:[ab]><r:(def)><y:n>"
    rep = r"<x:AAAA><r:\1><y:NNN>"
    mappings = init_mappings(in_text)

    # Whithin text
    in_text = "Ahmed aNdef Mahmoud"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = init_mappings(in_text)

    # Whithin text (more than a match)
    in_text = "Ahmed aNdef Mahmoud aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = init_mappings(in_text)

    # Whithin text (more than a match)
    in_text = "Ahmed aNdef Mahmoud aNdef"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = init_mappings(in_text)

    # Whithin text (more than a match)
    in_text = "END"
    pat = r"M:<x:END><r:($)>"
    rep = r"<x:end><r:\1>"
    mappings = init_mappings(in_text)

    # Whithin text (more than a match)
    in_text = "START"
    pat = r"M:<x:(^)><r:START>"
    rep = r"<x:\1><r:start>"
    mappings = init_mappings(in_text)

    # Whithin text (more than a match)
    in_text = "word"
    pat = r"M:<x:(word\b)>"
    rep = r"<x:WORD>"
    mappings = init_mappings(in_text)

    # Whithin text (more than a match)
    in_text = "wordF"
    pat = r"M:<x:(word\b)>"
    rep = r"<x:WORD>"
    mappings = init_mappings(in_text)

    # More than one group
    in_text = "a123"
    pat = r"M:<x:(a)><r:(\d+)>"
    rep = r"<x:\1><r:\2>"
    mappings = init_mappings(in_text)

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

    # out_text, out_mappings = sub_with_tagged_mapping(
    #     pat,
    #     rep,
    #     in_text,
    #     mappings,
    # )
    # print(f"pat: `{pat}`")
    # print(f"rep: `{rep}`")
    # print(f"IN  text: `{in_text}`")
    # print(f"Out text: `{out_text}`")
    # print("*" * 40)
    #
    # for idx, uth_c in enumerate(in_text):
    #     mapping = out_mappings[idx]
    #     print(f"IN_IDX: `{idx}`, SPAN: `{mapping}`")
    #     ph_c = ""
    #     ph_c = out_text[mapping.pos[0] : mapping.pos[1]]
    #     print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")
    #     print("-" * 40)

    print("#" * 30, "Cascaed", "#" * 30)

    # Cascadded: one to many + Delerte + shifting + normal text
    in_text = "aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
    check_mapping_continuty(mappings)
    mid_pat = r"M:<x:A><r:d>"
    mid_rep = r"<x:FFF><r:d>"

    # one ot many + delete + shfit
    in_text = "aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
    check_mapping_continuty(mappings)
    mid_pat = r"M:<x:A>.<r:(ef)>"
    mid_rep = r"<x:FFF><r:\1>"

    # delete at begin + mid delte + shfift
    in_text = "aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
    check_mapping_continuty(mappings)
    mid_pat = r"M:<x:A>.<r:(ef)>"
    mid_rep = r"<r:\1>"

    # delete at the end (last case)
    in_text = "aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
    check_mapping_continuty(mappings)
    mid_pat = r"M:<x:o$>"
    mid_rep = r""

    # delete at the end (first)
    in_text = "aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)> Hello"
    rep = r"<x:AAAA><r:\1>"
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
    check_mapping_continuty(mappings)
    mid_pat = r"M:<x:A>.<r:(ef)>"
    mid_rep = r"<x:FFF><r:\1>"

    # on to many at the end
    print("*" * 40)
    in_text = "aNdef Hello"
    pat = r"M:<x: Hello>"
    rep = r""
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(pat, rep, in_text, mappings)
    check_mapping_continuty(mappings)
    mid_pat = r"M:<x:f$>"
    mid_rep = r"<x:FFFF>"

    out_text, out_mappings = sub_with_tagged_mapping(
        mid_pat,
        mid_rep,
        mid_text,
        mappings,
    )

    print(f"in  pat: `{pat}`")
    print(f"in  rep: `{rep}`")
    print(f"mid pat: `{mid_pat}`")
    print(f"mid rep: `{mid_rep}`")
    print(f"IN   text: `{in_text}`")
    print(f"MID  text: `{mid_text}`")
    print(f"Out  text: `{out_text}`")
    print("*" * 40)

    for idx, uth_c in enumerate(in_text):
        mapping = out_mappings[idx]
        print(f"IN_IDX: `{idx}`, SPAN: `{mapping}`")
        ph_c = ""
        ph_c = out_text[mapping.pos[0] : mapping.pos[1]]
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")
        print("-" * 40)
    check_mapping_continuty(mappings)
