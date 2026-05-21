# Submission Errors

Participant and host issues when creating or processing submissions.

## Cannot create submission

- Phase may be outside start/end window (UTC).
- Team may not be registered for the challenge.
- Submission limits (`max_submissions_per_day`, etc.) may be exhausted.
- Email domain restrictions may block your account.

## Submission failed immediately

Read stderr on the submission page. Common causes:

- Invalid JSON or archive structure
- Evaluation script exception
- Missing annotation file for the phase

## Stuck in running

- Queue backlog — wait or contact hosts near deadlines.
- Remote evaluation — host worker offline.
- Worker crash — operators should check worker logs.

## Leaderboard visibility

- Toggle **Show on Leaderboard** when submissions are private by default.
- Host may keep leaderboard private until phase completion.

## import file mismatch (tests)

When running tests locally:

```bash
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
```

## See also

- [Participant submission troubleshooting](../../03-for-participants/submissions/troubleshooting.html)
- [Debugging guide](../error-codes/debugging-guide.html)
