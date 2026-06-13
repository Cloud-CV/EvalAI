# YAML Schema Reference

Overview of top-level fields in `challenge_config.yaml`. For narrative explanations see [Challenge Configuration](../../02-for-challenge-hosts/configuration/challenge-config.html).

## Required / common fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Challenge title |
| `short_description` | string | Short blurb (~140 chars) |
| `description` | path | HTML template path |
| `evaluation_details` | path | HTML evaluation description |
| `terms_and_conditions` | path | HTML terms |
| `image` | path | Logo (jpg/jpeg/png) |
| `submission_guidelines` | path | HTML submission rules |
| `evaluation_script` | path | Evaluation script zip or folder |
| `remote_evaluation` | bool | Run evaluation on host infrastructure (default `false`) |
| `start_date` / `end_date` | datetime | UTC `YYYY-MM-DD HH:MM:SS` |
| `published` | bool | Publish when approved (default `false`) |
| `leaderboard` | list | Leaderboard definitions |
| `challenge_phases` | list | Phases |
| `dataset_splits` | list | Splits (train/val/test) |
| `challenge_phase_splits` | list | Phase ↔ split ↔ leaderboard mapping |

## Optional fields

| Field | Description |
|-------|-------------|
| `tags` | List of tag strings |
| `domain` | CV, NLP, RL, MM, AL, TAB |
| `allowed_email_domains` | Restrict participants by email domain |
| `blocked_email_domains` | Block listed domains |

## Nested references

- [Phase settings](phase-settings.html)
- [Evaluation metrics](evaluation-metrics.html)
- [Example configs](../../02-for-challenge-hosts/templates/example-challenges.html)

Source template: [EvalAI-Starters challenge_config.yaml](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml).
