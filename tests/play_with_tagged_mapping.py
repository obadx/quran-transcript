from quran_transcript.phonetics.conv_base_operation import (
    PhonetizerMappings,
    init_mappings,
    sub_with_tagged_mapping,
)
from quran_transcript.phonetics.tajweed_rulses import TajweedRuleType


def check_mapping_continuty(mappings: PhonetizerMappings):
    if mappings.uth_to_ph:
        last_end = mappings.uth_to_ph[0].pos[1]
    for idx in range(1, len(mappings.uth_to_ph)):
        if last_end != mappings.uth_to_ph[idx].pos[0]:
            raise ValueError(f"Breaking mappings continutiy at idx: {idx}")
        last_end = mappings.uth_to_ph[idx].pos[1]


def render_mappings(in_text: str, out_text: str, out_mappings: PhonetizerMappings):
    ph_taj_rules = out_mappings.ph_to_taj_rules
    for idx, uth_c in enumerate(in_text):
        mapping = out_mappings[idx]
        ph_c = out_text[mapping.pos[0] : mapping.pos[1]]
        print(f"IN_IDX: `{idx}`, SPAN: `{mapping}`")
        print(f"UTH: `{uth_c}` -> PH: `{ph_c}`")
        if ph_taj_rules[mapping.pos[0]]:
            print("Tajweed Rules:")
            for taj in ph_taj_rules[mapping.pos[0]]:
                print(taj)
        else:
            print("No Tajweed Rules")
        print("-" * 40)


def run_case(
    in_text: str,
    pat: str,
    rep: str,
    mid_pat: str | None = None,
    mid_rep: str | None = None,
    first_taj_rule: TajweedRuleType | None = None,
    mid_taj_rule: TajweedRuleType | None = None,
    mid_insert_taj_cond=None,
):
    print("#" * 30, pat, "#" * 30)
    mappings = init_mappings(in_text)
    mid_text, mappings = sub_with_tagged_mapping(
        pat,
        rep,
        in_text,
        mappings,
        tajweed_rule_type=first_taj_rule,
    )
    check_mapping_continuty(mappings)
    print(f"in  pat: `{pat}`")
    print(f"in  rep: `{rep}`")
    print(f"IN   text: `{in_text}`")
    print(f"MID  text: `{mid_text}`")

    if mid_pat is not None:
        out_text, out_mappings = sub_with_tagged_mapping(
            mid_pat,
            mid_rep,
            mid_text,
            mappings,
            tajweed_rule_type=mid_taj_rule,
            insert_tajweed_cond=mid_insert_taj_cond,
        )
        check_mapping_continuty(out_mappings)
        print(f"mid pat: `{mid_pat}`")
        print(f"mid rep: `{mid_rep}`")
        print(f"Out  text: `{out_text}`")
        print("*" * 40)
        render_mappings(in_text, out_text, out_mappings)
    else:
        print("*" * 40)
        render_mappings(in_text, mid_text, mappings)
    print()


if __name__ == "__main__":
    # # delete
    # run_case("aNdef", r"M:<x:[ab]>.<r:(def)>", r"<x:A><r:\1>")
    #
    # # no mapping chainge
    # run_case("adef", r"M:<x:[ab]><r:(def)>", r"<x:A><r:\1>")
    #
    # # one to many + shifting
    # run_case("adef", r"M:<x:[ab]><r:(def)>", r"<x:AAAA><r:\1>")
    #
    # # one to many + shifting + normal text
    # run_case("adef Hello", r"M:<x:[ab]><r:(def)>", r"<x:AAAA><r:\1>")
    #
    # # one to many + shifting + on to many + normal text
    # run_case("adefn Hello", r"M:<x:[ab]><r:(def)><y:n>", r"<x:AAAA><r:\1><y:NNN>")
    #
    # # Whithin text
    # run_case("Ahmed aNdef Mahmoud", r"M:<x:[ab]>.<r:(def)>", r"<x:A><r:\1>")
    #
    # # Whithin text (more than a match)
    # run_case("Ahmed aNdef Mahmoud aNdef Hello", r"M:<x:[ab]>.<r:(def)>", r"<x:A><r:\1>")
    #
    # # Whithin text (more than a match)
    # run_case("Ahmed aNdef Mahmoud aNdef", r"M:<x:[ab]>.<r:(def)>", r"<x:A><r:\1>")
    #
    # # Whithin text (more than a match)
    # run_case("END", r"M:<x:END><r:($)>", r"<x:end><r:\1>")
    #
    # # Whithin text (more than a match)
    # run_case("START", r"M:<x:(^)><r:START>", r"<x:\1><r:start>")
    #
    # # Whithin text (more than a match)
    # run_case("word", r"M:<x:(word\b)>", r"<x:WORD>")
    #
    # # Whithin text (more than a match)
    # run_case("wordF", r"M:<x:(word\b)>", r"<x:WORD>")
    #
    # # More than one group
    # run_case("a123", r"M:<x:(a)><r:(\d+)>", r"<x:\1><r:\2>")

    # WARN: Many to one Parsing error
    # run_case("acNdef", r"M:<x:[ab]c>.<r:(def)>", r"<x:A><r:\1>")

    # WARN: Many to many Parsing error
    # run_case("acNdef", r"M:<x:[ab]c>.<r:(def)>", r"<x:ABC><r:\1>")

    # Cascadded: one to many + Delerte + shifting + normal text
    # run_case(
    #     "aNdef Hello",
    #     r"M:<x:[ab]>.<r:(def)>",
    #     r"<x:AAAA><r:\1>",
    #     r"M:<x:A><r:d>",
    #     r"<x:FFF><r:d>",
    # )
    # #
    # # one ot many + delete + shfit
    # run_case(
    #     "aNdef Hello",
    #     r"M:<x:[ab]>.<r:(def)>",
    #     r"<x:AAAA><r:\1>",
    #     r"M:<x:A>.<r:(ef)>",
    #     r"<x:FFF><r:\1>",
    # )
    # #
    # # delete at begin + mid delte + shfift
    # run_case(
    #     "aNdef Hello",
    #     r"M:<x:[ab]>.<r:(def)>",
    #     r"<x:AAAA><r:\1>",
    #     r"M:<x:A>.<r:(ef)>",
    #     r"<r:\1>",
    # )
    #
    # # delete at the end (last case)
    # run_case(
    #     "aNdef Hello",
    #     r"M:<x:[ab]>.<r:(def)>",
    #     r"<x:AAAA><r:\1>",
    #     r"M:<x:o$>",
    #     r"",
    # )

    # # delete at the end (first)
    # run_case(
    #     "aNdef Hello",
    #     r"M:<x:[ab]>.<r:(def)> Hello",
    #     r"<x:AAAA><r:\1>",
    #     r"M:<x:A>.<r:(ef)>",
    #     r"<x:FFF><r:\1>",
    # )
    #
    # # on to many at the end
    # run_case(
    #     "aNdef Hello",
    #     r"M:<x: Hello>",
    #     r"",
    #     r"M:<x:f$>",
    #     r"<x:FFFF>",
    # )
    #
    # # only on uth and is expanding
    # run_case(
    #     "a",
    #     r"M:<x:a>",
    #     r"<x:AAB>",
    #     r"M:<x:AA><y:B>",
    #     r"<x:aa><y:bbb>",
    # )

    # # Simple Case: Tajweed Rule only
    # run_case(
    #     "abcdef",
    #     r"M:<T:ab>",
    #     r"<T:AB>",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    # )

    # # Simple Case: Tajweed Rule only
    # run_case(
    #     "abcdef",
    #     r"M:<T:ab>",
    #     r"<T:AB>",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    # )

    # # Simple Case: Tajweed Rule on delete
    # run_case(
    #     "abcdef",
    #     r"M:<T:ef>",
    #     r"",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    # )

    # # Simple Case: Tajweed Rule one to many
    # run_case(
    #     "abcdef",
    #     r"M:<T:a>",
    #     r"<T:AAAA>",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    # )

    # # Cascaded: Tajweed Rule only + Dep
    # run_case(
    #     "abcdef",
    #     r"M:<T:ab><D0:(cd)>",
    #     r"<T:AB><D0:\1>",
    #     r"M:<x:AB>",
    #     r"<x:BA>",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    # )

    # # Cascaded: Tajweed Rule only + Dep + delete the tajweed rule
    # run_case(
    #     "abcdef",
    #     r"M:<T:ab><D0:(cd)>",
    #     r"<T:AB><D0:\1>",
    #     r"M:<x:AB>",
    #     r"",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    # )

    # # Cascaded: More than Tajweed Rule
    # run_case(
    #     "abcdef",
    #     r"M:<T:ab><D0:c>",
    #     r"<T:AB><D0:c>",
    #     r"M:<T:B>",
    #     r"<T:BBBB>",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    #     mid_taj_rule=TajweedRuleType.NORMAL_MADD,
    # )

    # # Cascaded: Tajweed Rule only + Dep + delete the tajweed rule at end
    # run_case(
    #     "abcdef",
    #     r"M:<T:ef><D0:($)>",
    #     r"",
    #     r"M:<T:cd><D0:($)>",
    #     r"",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    #     mid_taj_rule=TajweedRuleType.NORMAL_MADD,
    # )

    # # Cascaded: Tajweed Rule only + Dep + delete the tajweed rule at end in between text
    # run_case(
    #     "Ahmed Mahmoud abcdef",
    #     r"M:<T:ef><D0:($)>",
    #     r"",
    #     r"M:<T:cd><D0:($)>",
    #     r"",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    #     mid_taj_rule=TajweedRuleType.NORMAL_MADD,
    # )

    # # Cascaded: More than Tajweed Rule + in between text
    # run_case(
    #     "Hello How are you: abcdef Good ",
    #     r"M:<T:ab><D0:c>",
    #     r"<T:AB><D0:c>",
    #     r"M:<T:B>",
    #     r"<T:BBBB>",
    #     first_taj_rule=TajweedRuleType.LAZIM_MADD,
    #     mid_taj_rule=TajweedRuleType.NORMAL_MADD,
    # )

    # Cascaded: More than Tajweed Rule + in between text + condition
    run_case(
        "Hello How are you: abcdef Good ",
        r"M:<T:ab><D0:c>",
        r"<T:AB><D0:c>",
        r"M:<T:A>",
        r"<T:aaaa>",
        first_taj_rule=TajweedRuleType.LAZIM_MADD,
        mid_taj_rule=TajweedRuleType.NORMAL_MADD,
        mid_insert_taj_cond=lambda L, x: TajweedRuleType.LAZIM_MADD not in L,
        # mid_insert_taj_cond=lambda L, x: True,
    )
