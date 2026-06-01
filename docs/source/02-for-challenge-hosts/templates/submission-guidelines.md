# Submission Guidelines

Submission guidelines tell participants what to upload, which formats are allowed, and how results are evaluated.

## In challenge configuration

Point `submission_guidelines` to an HTML template:

```yaml
submission_guidelines: templates/submission_guidelines.html
```

Edit `templates/submission_guidelines.html` in your [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) fork. Common sections include:

- Allowed file formats and naming conventions
- Maximum file size expectations
- Whether submissions must include code, reports, or metadata
- Links to validation scripts or format checkers
- Contact information for submission questions

## Per-phase file types

Restrict uploads per phase with `allowed_submission_file_types`:

```yaml
challenge_phases:
  - id: 1
    codename: dev
    allowed_submission_file_types: ".json, .zip"
```

## Submission metadata

Collect extra fields (method name, paper link, model type) with `submission_meta_attributes` and control defaults with `default_submission_meta_attributes`. See [Challenge Configuration](../configuration/challenge-config.html).

## Submission limits

Configure fairness and cost with:

- `max_submissions_per_day`
- `max_submissions_per_month`
- `max_submissions`
- `max_concurrent_submissions_allowed`

## See also

- [HTML Templates](html-templates.html)
- [Prediction Upload Challenges](../evaluation/prediction-upload.html)
- [Participant submission guide](../../03-for-participants/submissions/index.html)
