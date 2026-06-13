# Error Reference

EvalAI REST APIs return standard HTTP status codes. Response bodies often include a `detail` field with a human-readable message.

## Common HTTP statuses

| Code | Meaning | Typical cause |
|------|---------|----------------|
| 400 | Bad Request | Invalid payload, wrong phase, limits exceeded |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Not a host/participant for this resource |
| 404 | Not Found | Wrong challenge, phase, or submission ID |
| 429 | Too Many Requests | Rate limiting |
| 500 | Server Error | Unexpected server failure — retry and report |

## Submission-specific failures

Evaluation failures are reflected on the submission record (status **Failed**) rather than only HTTP errors at upload time. Always check:

- Submission status in **My Submissions**
- stderr/stdout logs attached to the submission

## Authentication errors

- Regenerate token from [profile](https://eval.ai/web/profile)
- CLI: `evalai login` after token rotation

## Reporting bugs

Include challenge ID, phase, submission ID (if any), timestamp (UTC), and redacted logs when opening [GitHub issues](https://github.com/Cloud-CV/EvalAI/issues/new).

## See also

- [Debugging Guide](debugging-guide.html)
- [API Authentication](../../05-api-reference/authentication.html)
