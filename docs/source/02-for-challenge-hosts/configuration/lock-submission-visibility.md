# Lock Submission Visibility

By default, participants can toggle their submissions between public and private from the leaderboard view. If you want to remove this option and ensure that all submissions are always visible, you can configure it in your challenge's YAML file.

This feature is useful when challenge organizers may want to enforce full transparency to:
- Prevent participants from concealing their performance

- Ensure all baselines and results remain visible to organizers and other participants.

## How to Lock Submission Visibility

1. Open your `challenge_config.yaml` file for the challenge phase you want to modify.

2. Locate or add the `is_submission_public` property in the challenge phase configuration.

3. Set it to `True` and ensure `leaderboard_public` is also set to `True`.

**Example:**

```yaml
leaderboard_public: True
is_submission_public: True
```

## What happens when you lock/unlock submission visibility

- When `is_submission_public`: `True`

  - All submissions in this phase are public by default.

  - Participants cannot hide their submissions (the “Hide/Show” option is removed).

- When `is_submission_public`: `False` (default)

  - Submissions are private by default, and participants can toggle their visibility.

## Important Notes

- This setting is applied per challenge phase, so repeat it for each phase where you want enforced visibility.

- If `leaderboard_public` is set to `False`, this setting has no effect.