# Evaluation Metrics Reference

Metrics are produced by your `evaluate()` function and declared in the leaderboard schema.

## Return structure

```python
{
  "result": [
    {"<split_codename>": {"MetricA": 0.9, "MetricB": 0.1}},
  ]
}
```

- **split_codename** must match a `dataset_splits[].codename` linked to the phase.
- **Metric keys** should match `leaderboard[].schema.labels` (except derived columns you compute client-side).

## Leaderboard metadata

Per-metric metadata in YAML:

```yaml
"Metric1": {
  "sort_ascending": true,
  "description": "Shown in UI tooltips"
}
```

Use `is_leaderboard_order_descending: false` on phase splits when lower values rank higher (error rates).

## Visibility levels

| Value | Who sees scores |
|-------|-----------------|
| 1 | Challenge host only |
| 2 | Host and submitting team |
| 3 | Everyone on public leaderboard |

## Examples

See [Evaluation Scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html) and [Example challenge configs](../../02-for-challenge-hosts/templates/example-challenges.html).
