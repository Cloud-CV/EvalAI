# First Submission Example

Walkthrough for your first prediction upload submission.

## Prerequisites

- EvalAI account and [participant team](../../03-for-participants/participation-guide/getting-started.html)
- Challenge participation completed
- Submission file matching host guidelines

## Steps

1. Open the challenge → **Submit** tab.
2. Select the active phase (for example **Dev Phase**).
3. Upload your file (`.json`, `.zip`, etc.).
4. Fill optional metadata (method name, description).
5. Submit and open **My Submissions** to watch status.

## Success

Status becomes **Finished** and scores appear when:

- Evaluation succeeds
- Leaderboard is public for the phase
- Your submission is visible on the leaderboard (if required)

## Failure

Open the submission row, read **stderr**, fix the format, and resubmit if quota allows. See [Submission troubleshooting](../../03-for-participants/submissions/troubleshooting.html).

## CLI alternative

```bash
evalai login
evalai challenge <id> phase <phase_id> submit --file submission.json
```

## See also

- [Prediction upload](../../03-for-participants/submissions/prediction-upload.html)
- [Submission types](../../03-for-participants/submissions/submission-types.html)
