# Submission Troubleshooting

Common participant issues when uploading or waiting for results.

## Submission stuck in "Running"

- Evaluation can take minutes to hours depending on challenge load and script complexity.
- For remote evaluation challenges, the host must keep their worker running — delays may occur if the host worker is offline.
- Check again after the phase's typical runtime stated in the challenge description.

## Submission failed

Open the submission detail page and review **stderr** and **stdout** logs. Typical causes:

- Wrong file format or schema
- Missing required fields in JSON submissions
- Evaluation script raised an exception (message appears in logs)

Fix the format and resubmit if you have remaining submission quota.

## Cannot submit to a phase

Verify:

- Phase start/end dates (UTC)
- You joined the challenge with a participant team
- You have not exceeded `max_submissions_per_day` or total limits
- Your email domain is allowed (if the host restricted domains)

## Leaderboard does not show my score

- The host may use a private leaderboard until the phase ends.
- Your submission may be private — toggle **Show on Leaderboard** in **My Submissions** when allowed.
- Only one submission may count when `is_restricted_to_select_one_submission` is enabled — select the correct row.

## CLI authentication errors

Re-run `evalai login` and confirm the token from [profile](https://eval.ai/web/profile). Ensure `EVALAI_API_SERVER` points to production or staging consistently.

## More help

- [Common submission errors](../../07-troubleshooting/common-issues/submission-errors.html)
- [FAQ](../../07-troubleshooting/support/faq.html)
- [Contact support](../../07-troubleshooting/support/contact-support.html)
