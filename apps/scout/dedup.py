def canonical_key(c):
    return "{}|{}|{}".format(
        c["benchmark_name"].strip().lower(),
        c["conference"].strip().lower(),
        int(c["year"]),
    )
