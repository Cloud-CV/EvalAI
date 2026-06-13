def _escape(s):
    # Escape backslash first, then the field separator. This makes the
    # joined key injective: ("a|b", "c") and ("a", "b|c") encode to
    # distinct strings ("a\|b|c" vs "a|b\|c") instead of colliding.
    return s.replace("\\", "\\\\").replace("|", "\\|")


def canonical_key(c):
    return "{}|{}|{}".format(
        _escape(c["benchmark_name"].strip().lower()),
        _escape(c["conference"].strip().lower()),
        int(c["year"]),
    )
