# Simple Prediction Challenge Example

Single-phase prediction upload challenge with one leaderboard — adapt [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) using [Example 1](../../02-for-challenge-hosts/templates/example-challenges.html#example-1-one-challenge-one-phase-one-leaderboard-one-phase-split).

## Highlights

- `remote_evaluation: false` — EvalAI workers run `evaluate()`
- One `challenge_phases` entry with `codename: dev`
- One `dataset_splits` entry (`test_split`)
- Leaderboard schema with a single metric (for example `Accuracy`)

## Steps (EvalAI-Starters)

1. [Create a repo from EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters/generate) and configure secrets plus `github/host_config.json` ([getting started](../../02-for-challenge-hosts/hosting-guide/getting-started.html)).
2. Replace [`challenge_config.yaml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) with the YAML from [Example 1](../../02-for-challenge-hosts/templates/example-challenges.html#example-1-one-challenge-one-phase-one-leaderboard-one-phase-split) (or remove the second phase and extra splits from the default template).
3. Add `annotations/test_annotations_devsplit.json` (or your annotation filename) and point `test_annotation_file` at it.
4. Update `templates/*.html` and package `evaluation_script/` into `evaluation_script.zip` for CI.
5. Simplify [`evaluation_script/main.py`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/evaluation_script/main.py) — one branch for your phase `codename`.
6. Test locally with `python -m worker.run` (see [EvalAI-Starters guide](../evalai-starters-guide.html#default-template-included-in-the-repo)).
7. Push to the `challenge` branch and verify GitHub Actions.

## Evaluation output

Return metrics for `test_split`:

```python
return {
    "result": [
        {"test_split": {"Accuracy": 0.87}}
    ]
}
```

## See also

- [EvalAI-Starters challenge examples](../evalai-starters-guide.html)
- [Prediction upload](../../02-for-challenge-hosts/evaluation/prediction-upload.html)
- [Evaluation scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html)
