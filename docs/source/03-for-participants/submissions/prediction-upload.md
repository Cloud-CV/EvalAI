# Prediction Upload (Participant)

Prediction upload challenges accept result files (predictions, labels, archives) through the web UI or CLI.

## Submit via the website

1. Open the challenge and select your participant team.
2. Go to the **Submit** tab for the active phase.
3. Upload a file matching the allowed types in the challenge guidelines.
4. Optionally fill submission metadata fields (method name, description, etc.).
5. Submit and wait for evaluation to finish.

Check status under **My Submissions**. States include running, finished, and failed.

## Submit via EvalAI CLI

Install the CLI from [cli.eval.ai](https://cli.eval.ai/) and authenticate:

```bash
pip install evalai
evalai login
```

Upload for a phase (replace placeholders with your challenge and phase identifiers):

```bash
evalai challenge <challenge_id> phase <phase_id> submit --file <path_to_submission>
```

See [EvalAI CLI](../cli-tools/evalai-cli.html) and the official CLI docs for the latest commands.

## File formats

Allowed extensions are set by the host in `allowed_submission_file_types` (for example `.json`, `.zip`, `.csv`). Read the challenge **Submission Guidelines** before uploading.

## After submission

- Successful runs appear on the leaderboard when the phase leaderboard is public and your submission is marked visible.
- Failed runs include stderr logs on the submission detail view — see [Submission Troubleshooting](troubleshooting.html).

## See also

- [Submission Types](submission-types.html)
- [Submission Status](submission-status.html)
- [First submission example](../../06-examples-tutorials/participant-examples/first-submission.html)
