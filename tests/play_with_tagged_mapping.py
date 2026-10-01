from quran_transcript.phonetics.conv_base_operation import (
    MappingPos,
    sub_with_tagged_mapping,
)

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

    # Whithin text
    in_text = "Ahmed aNdef Mahmoud"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = [MappingPos(pos=(i, i + 1)) for i in range(len(in_text))]

    # Whithin text (more than a match)
    in_text = "Ahmed aNdef Mahmoud aNdef Hello"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = [MappingPos(pos=(i, i + 1)) for i in range(len(in_text))]

    # Whithin text (more than a match)
    in_text = "Ahmed aNdef Mahmoud aNdef"
    pat = r"M:<x:[ab]>.<r:(def)>"
    rep = r"<x:A><r:\1>"
    mappings = [MappingPos(pos=(i, i + 1)) for i in range(len(in_text))]

    # # More than one group
    # in_text = "a123"
    # pat = r"M:<x:(a)><r:(\d+)>"
    # rep = r"<x:\1><r:\2>"
    # mappings = [MappingPos(pos=(i, i + 1)) for i in range(len(in_text))]

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
