# Jupyter Notebook Integration

Use notebooks to prototype submissions before uploading to EvalAI.

## Typical workflow

1. Download or generate predictions locally in a notebook.
2. Save outputs in the format required by the challenge (JSON, CSV, ZIP).
3. Validate file structure against sample annotations.
4. Upload via the web **Submit** tab or [EvalAI CLI](../../03-for-participants/cli-tools/evalai-cli.html).

## Tips

- Keep random seeds fixed for reproducibility.
- Match column names and IDs to the host's sample submission file.
- Watch submission size limits for large archives.

## API from notebooks

Authenticate with a token from [profile](https://eval.ai/web/profile) and call REST endpoints documented in [Submissions API](../../05-api-reference/endpoints/submissions.html) using `requests` or `httpx`.

## See also

- [First submission example](../participant-examples/first-submission.html)
- [Colab integration](colab-integration.html)
