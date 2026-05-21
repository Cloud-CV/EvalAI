# Leaderboards API

Base path: `/api/jobs/`

## Leaderboard for a phase split

```
GET /api/jobs/challenge_phase_split/<challenge_phase_split_id>/leaderboard/
```

Returns ranked entries for the given phase/split/leaderboard combination. Visibility respects challenge configuration (`visibility` levels 1–3).

## Public leaderboard entries

```
GET /api/jobs/phase_split/<challenge_phase_split_pk>/public_leaderboard_all_entries/
```

## Update leaderboard data (hosts)

```
PATCH /api/jobs/leaderboard_data/<leaderboard_data_pk>/
```

Host-only maintenance for correcting or updating displayed values when supported.

## Metric configuration

Leaderboard columns come from `challenge_config.yaml` schema and evaluation script output — see [Metrics and Leaderboards](../../02-for-challenge-hosts/evaluation/metrics-leaderboards.html).

## See also

- [Submissions API](submissions.html)
- [Challenges API](challenges.html)
