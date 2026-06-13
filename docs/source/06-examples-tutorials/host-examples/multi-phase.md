# Multi-Phase Challenge Example

Use multiple `challenge_phases` when you need dev/test stages, staggered deadlines, or different annotation files per stage. The **default** [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) `challenge_config.yaml` already implements this pattern (dev + test phases).

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

In `evaluate()`, branch on `phase_codename` (see [evaluation_script/main.py](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/evaluation_script/main.py) in the template):

```python
def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):
    if phase_codename == "dev":
        ...
    elif phase_codename == "test":
        ...
```

## Phase splits

Map each phase to leaderboard columns and splits with `challenge_phase_splits` (different `visibility` per split if needed). The starters repo links dev phase to `train_split` and test phase to both `train_split` and `test_split` — adjust to match your [Example 3](../../02-for-challenge-hosts/templates/example-challenges.html#example-3-one-challenge-two-phases-one-leaderboard-two-phase-splits) or [Example 4](../../02-for-challenge-hosts/templates/example-challenges.html#example-4-one-challenge-three-phases-two-leaderboards-four-phase-splits) design.

## Steps (EvalAI-Starters)

1. Fork [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) — start from the **stock** two-phase config or merge [Example 3](../../02-for-challenge-hosts/templates/example-challenges.html#example-3-one-challenge-two-phases-one-leaderboard-two-phase-splits).
2. Keep [`annotations/test_annotations_devsplit.json`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/annotations) and [`annotations/test_annotations_testsplit.json`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/annotations) (or add your own files and update YAML paths).
3. Edit [`templates/challenge_phase_1_description.html`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/templates) and `challenge_phase_2_description.html`.
4. Run `python -m worker.run` for each `phase_codename` you support.
5. Push to `challenge`.

## See also

- [EvalAI-Starters challenge examples](../evalai-starters-guide.html)
- [Phase settings reference](../../08-reference/config-reference/phase-settings.html)
- [Challenge phases setup](../../02-for-challenge-hosts/configuration/challenge-phases-setup.html)
