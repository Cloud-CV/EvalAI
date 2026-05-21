# Simple Prediction Challenge Example

Single-phase prediction upload challenge with one leaderboard — based on [Example 1](../../02-for-challenge-hosts/templates/example-challenges.html) in the templates doc.

## Highlights

- `remote_evaluation: false` — EvalAI workers run `evaluate()`
- One `challenge_phases` entry with `codename: dev`
- One `dataset_splits` entry (`test_split`)
- Leaderboard schema with a single metric (for example `Accuracy`)

## Steps

1. Fork [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters).
2. Copy `example_1` patterns from [Example challenge configs](../../02-for-challenge-hosts/templates/example-challenges.html).
3. Place test annotations and HTML templates at paths referenced in YAML.
4. Implement `evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs)`.
5. Push to `challenge` branch and verify GitHub Actions build.

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

- [Prediction upload](../../02-for-challenge-hosts/evaluation/prediction-upload.html)
- [Evaluation scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html)
