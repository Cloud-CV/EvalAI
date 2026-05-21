# Multi-Phase Challenge Example

Use multiple `challenge_phases` when you need dev/test stages, staggered deadlines, or different annotation files per stage.

## Pattern

```yaml
challenge_phases:
  - id: 1
    name: Development Phase
    codename: dev
    test_annotation_file: annotations/dev.json
    ...
  - id: 2
    name: Test Phase
    codename: test
    test_annotation_file: annotations/test.json
    ...
```

In `evaluate()`, branch on `phase_codename`:

```python
def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):
    if phase_codename == "dev":
        ...
    elif phase_codename == "test":
        ...
```

## Phase splits

Map each phase to leaderboard columns and splits with `challenge_phase_splits` (different `visibility` per split if needed).

## Examples in repo

See [Example 2 and 3](../../02-for-challenge-hosts/templates/example-challenges.html) for multi-leaderboard and multi-phase YAML samples.

## See also

- [Phase settings reference](../../08-reference/config-reference/phase-settings.html)
- [Challenge phases setup](../../02-for-challenge-hosts/configuration/challenge-phases-setup.html)
