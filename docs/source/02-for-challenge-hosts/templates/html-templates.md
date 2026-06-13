# HTML Templates

Challenge descriptions, rules, and phase text on EvalAI are HTML files referenced from `challenge_config.yaml`.

## Template fields in challenge_config.yaml

| Field | Purpose |
|-------|---------|
| `description` | Main challenge overview |
| `evaluation_details` | How submissions are evaluated |
| `terms_and_conditions` | Legal / participation terms |
| `submission_guidelines` | What and how participants should submit |
| `leaderboard_description` | Text shown above the leaderboard |

Each value is a **relative path** to an HTML file in your challenge repository, for example:

```yaml
description: templates/description.html
evaluation_details: templates/evaluation_details.html
terms_and_conditions: templates/terms_and_conditions.html
submission_guidelines: templates/submission_guidelines.html
```

Phase descriptions use a similar pattern under `challenge_phases`:

```yaml
challenge_phases:
  - id: 1
    name: Dev Phase
    description: templates/challenge_phase_1_description.html
```

## Starter templates

[EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) includes sample templates under `templates/`. Fork the repository and edit HTML to match your challenge.

Tips:

- Use headings and lists for readability on the challenge page.
- Link to external datasets, papers, and baseline code.
- Keep submission format and file naming rules in `submission_guidelines.html`.

## Images and assets

Place images next to your templates or under an `images/` folder in the challenge repo. Reference them with relative paths in HTML.

The challenge logo is configured separately via the `image` field (JPG, JPEG, or PNG).

## See also

- [Submission Guidelines](submission-guidelines.html)
- [Challenge Configuration](../configuration/challenge-config.html)
- [Example challenge configs](example-challenges.html)
