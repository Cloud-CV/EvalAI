from scout.models import ScoutChallenge


def build_template_data(challenge, organizer):
    return {
        "organizer_name": (organizer.get("name") or ""),
        "benchmark_name": challenge.benchmark_name,
        "conference": challenge.conference,
        "year": challenge.year,
        "official_url": challenge.official_url,
        "evalai_pitch": challenge.evalai_reasoning or "",
    }


def pending_challenges():
    """Return a QuerySet of ScoutChallenge rows that have not been
    emailed about yet."""
    return ScoutChallenge.objects.filter(outreach_sent_at__isnull=True)


def iter_pending_targets():
    """Yield (challenge, organizer_dict) pairs for every pending row's
    organizers that have a usable email."""
    for challenge in pending_challenges().iterator():
        for organizer in (challenge.organizers or []):
            email = (organizer.get("email") or "").strip()
            if not email:
                continue
            yield challenge, organizer
