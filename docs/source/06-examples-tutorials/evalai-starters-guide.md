# Challenge examples with EvalAI-Starters

[EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) is the official GitHub template for hosting challenges on EvalAI. Fork it, edit configuration and scripts on the `challenge` branch, and GitHub Actions syncs your challenge to EvalAI.

This page maps the starter repository to common challenge patterns documented in EvalAI. For full YAML samples of each pattern, see [Challenge configuration examples](../../02-for-challenge-hosts/templates/example-challenges.html).

## Repository layout

| Path | Purpose |
|------|---------|
| [`challenge_config.yaml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) | Challenge metadata, phases, leaderboards, splits |
| [`evaluation_script/main.py`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/evaluation_script/main.py) | `evaluate()` implementation zipped as `evaluation_script.zip` |
| [`annotations/`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/annotations) | Ground-truth files referenced by phase `test_annotation_file` |
| [`templates/`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/templates) | HTML for description, guidelines, phase text, terms |
| [`worker/run.py`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/worker/run.py) | Run evaluation locally before pushing |
| [`github/host_config.json`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/github/host_config.json) | EvalAI auth token, host team PK, API URL |
| [`remote_challenge_evaluation/`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/remote_challenge_evaluation) | Worker for `remote_evaluation: true` challenges |

## Default template (included in the repo)

The stock `challenge_config.yaml` is a **two-phase prediction challenge** (Random Number Generator Challenge) with:

- `remote_evaluation: false` — EvalAI workers run your script
- **Dev** phase (`codename: dev`) and **Test** phase (`codename: test`)
- Dataset splits `train_split` and `test_split`
- Sample metrics `Metric1`, `Metric2`, `Metric3`, `Total`

The matching [`evaluation_script/main.py`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/evaluation_script/main.py) branches on `phase_codename` and returns scores per split — use it as a reference for multi-phase `evaluate()` logic.

To try the default setup locally:

1. Copy `evaluation_script/` into `challenge_data/challenge_1/` (see [EvalAI-Starters README](https://github.com/Cloud-CV/EvalAI-Starters#test-your-evaluation-script-locally)).
2. Set phase codename, annotation file, and submission file in `worker/run.py`.
3. From the repo root (where `annotations/`, `challenge_data/`, and `worker/` live), run:

```bash
python -m worker.run
```

## Map doc examples to EvalAI-Starters

Use the table below when adapting a fork of EvalAI-Starters. Copy fields from [Example challenge configs](../../02-for-challenge-hosts/templates/example-challenges.html) into your fork’s `challenge_config.yaml`, and keep file paths consistent with files you add under `annotations/` and `templates/`.

| Pattern | Doc reference | Changes in your EvalAI-Starters fork |
|---------|---------------|--------------------------------------|
| One phase, one leaderboard | [Example 1](../../02-for-challenge-hosts/templates/example-challenges.html#example-1-one-challenge-one-phase-one-leaderboard-one-phase-split) | Keep one entry in `challenge_phases`; one `dataset_splits` row; one `challenge_phase_splits` row; simplify `evaluation_script/main.py` to a single `phase_codename` |
| One phase, two leaderboards | [Example 2](../../02-for-challenge-hosts/templates/example-challenges.html#example-2-one-challenge-one-phase-two-leaderboards-two-phase-splits) | Add a second `leaderboard` and map two `challenge_phase_splits` to different `dataset_split_id` values; return both splits in `evaluate()` |
| Two phases, one leaderboard | [Example 3](../../02-for-challenge-hosts/templates/example-challenges.html#example-3-one-challenge-two-phases-one-leaderboard-two-phase-splits) | Closest to the **default** starters config — adjust phase dates, annotations (`test_annotations_devsplit.json` / `test_annotations_testsplit.json`), and metric names |
| Three phases, two leaderboards | [Example 4](../../02-for-challenge-hosts/templates/example-challenges.html#example-4-one-challenge-three-phases-two-leaderboards-four-phase-splits) | Add a third phase template HTML, annotation file, and `challenge_phase_splits`; extend `evaluate()` with another `phase_codename` branch |
| Remote evaluation | [Remote evaluation example](host-examples/remote-evaluation.html) | Set `remote_evaluation: true`; deploy [`remote_challenge_evaluation/`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/remote_challenge_evaluation) on your infrastructure |

Walkthroughs that follow this mapping:

- [Simple prediction challenge](host-examples/simple-prediction.html)
- [Multi-phase challenge](host-examples/multi-phase.html)
- [Remote evaluation challenge](host-examples/remote-evaluation.html)
- [GitHub integration](integration-examples/github-integration.html)

## Quick start from the template

1. [Create a repository from the template](https://github.com/Cloud-CV/EvalAI-Starters/generate).
2. Add GitHub secret `AUTH_TOKEN` (personal access token).
3. Create branch `challenge` and fill `github/host_config.json` (see [Getting started as a host](../../02-for-challenge-hosts/hosting-guide/getting-started.html)).
4. Edit `challenge_config.yaml`, `templates/*.html`, and `evaluation_script/main.py`.
5. Push to `challenge` and check GitHub Actions; fix any auto-opened configuration issues.
6. After approval, view the challenge under [Hosted Challenges](https://eval.ai/web/hosted-challenges).

Optional: add Python dependencies for evaluation via [dependency installation in EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/evaluation_script/dependency-installation.md).

## Remote evaluation variant

For challenges where **you** run the worker:

1. In `challenge_config.yaml`, set `remote_evaluation: true`.
2. After the challenge exists on EvalAI, copy queue name and keys from the challenge **Manage** tab into `remote_challenge_evaluation/`.
3. Install requirements and run the worker (see [Remote evaluation](../../02-for-challenge-hosts/evaluation/remote-evaluation.html)).

## See also

- [Challenge configuration](../../02-for-challenge-hosts/configuration/challenge-config.html)
- [YAML schema reference](../../08-reference/config-reference/yaml-schema.html)
- [Community support — EvalAI-Starters issues](../../07-troubleshooting/support/community-support.html)
