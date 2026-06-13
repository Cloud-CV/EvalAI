# Phase Settings Reference

Fields available on each `challenge_phases` entry in `challenge_config.yaml`.

## Core fields

| Field | Description |
|-------|-------------|
| `id` | Unique positive integer |
| `name` | Display name |
| `description` | Relative path to HTML description |
| `codename` | Unique string; must match evaluation script branching |
| `challenge` | Challenge ID reference in template (usually `1`) |
| `start_date` / `end_date` | Phase window (UTC) |
| `test_annotation_file` | Ground-truth / test annotations for scoring |

## Visibility and access

| Field | Default | Description |
|-------|---------|-------------|
| `leaderboard_public` | `False` | Show phase leaderboard to participants |
| `is_public` | `False` | Show phase on challenge page |
| `is_submission_public` | `False` | Default submission visibility on public leaderboard |
| `allowed_email_ids` | `[]` | Restrict phase to specific emails (optional) |

## Limits

| Field | Default | Description |
|-------|---------|-------------|
| `max_submissions_per_day` | large | Daily cap per team |
| `max_submissions_per_month` | large | Monthly cap |
| `max_submissions` | large | Total cap |
| `max_concurrent_submissions_allowed` | — | Parallel runs |

## Submission behavior

| Field | Description |
|-------|-------------|
| `allowed_submission_file_types` | Comma-separated extensions |
| `is_restricted_to_select_one_submission` | Only one public leaderboard submission |
| `is_partial_submission_evaluation_enabled` | Partial evaluation support |
| `default_submission_meta_attributes` | Standard metadata visibility |
| `submission_meta_attributes` | Custom form fields |
| `disable_logs` | Hide execution logs from participants when `True` |

## Phase splits

Link phases to leaderboards and dataset splits via `challenge_phase_splits` — see [YAML Schema](yaml-schema.html) and [Metrics and Leaderboards](../../02-for-challenge-hosts/evaluation/metrics-leaderboards.html).
