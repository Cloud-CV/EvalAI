# Submissions API

Base path: `/api/jobs/`

## Create submission

```
POST /api/jobs/challenge/<challenge_id>/challenge_phase/<challenge_phase_id>/submission/
```

Multipart form upload with submission file and metadata. Requires participant authentication and an enrolled team.

This endpoint queues evaluation — see [Submission processing](../../04-development/deployment/worker-setup.html).

## Get submission

```
GET /api/jobs/submission/<submission_id>
```

## List challenge submissions (hosts)

```
GET /api/jobs/challenge/<challenge_pk>/submission/
```

## Remaining submission quota

```
GET /api/jobs/<challenge_pk>/remaining_submissions/
```

## Re-run / resume

```
POST /api/jobs/submissions/<submission_pk>/re-run/
POST /api/jobs/submissions/<submission_pk>/resume/
```

## Update visibility / metadata

```
PATCH /api/jobs/challenge/<challenge_pk>/challenge_phase/<challenge_phase_pk>/submission/<submission_pk>
```

## Queue utilities (workers / remote eval)

```
GET /api/jobs/challenge/queues/<queue_name>/
DELETE /api/jobs/queues/<queue_name>/
```

Used by remote evaluation workers to fetch and acknowledge messages.

## Signed file URLs

```
GET /api/jobs/submission_files/
```

Query parameters specify submission-related files for secure download.

## See also

- [Leaderboards API](leaderboards.html)
- [Authentication](../authentication.html)
- [Participant submission guide](../../03-for-participants/submissions/prediction-upload.html)
