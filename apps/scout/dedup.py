import hashlib
import json


def canonical_key(c):
    """Return a fixed-length dedup key for a scout challenge payload.

    SHA-256 over a normalized JSON tuple keeps keys at 64 hex chars (fits
    ``ScoutChallenge.canonical_key`` without escape expansion) while staying
    injective across benchmark_name / conference / year combinations.
    """
    parts = [
        c["benchmark_name"].strip().lower(),
        c["conference"].strip().lower(),
        str(int(c["year"])),
    ]
    payload = json.dumps(parts, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
