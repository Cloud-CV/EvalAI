# Challenges API

Base path: `/api/challenges/`

Interactive schema (when enabled on your instance): `/api/schema/swagger-ui/`.

## List challenges

```
GET /api/challenges/challenge/<challenge_time>/<challenge_approved>/<challenge_published>
```

`challenge_time`: `all`, `future`, `past`, or `present` (case insensitive).

`challenge_approved` / `challenge_published`: `approved`, `unapproved`, `public`, `private`, etc.

## Challenge detail

```
GET /api/challenges/challenge_host_team/<host_team_pk>/challenge/<challenge_pk>
```

Requires host permissions for private management fields.

## Phases

```
GET /api/challenges/challenge/<challenge_pk>/challenge_phase
GET /api/challenges/challenge/<challenge_pk>/challenge_phase/<phase_pk>
```

## Participant registration

```
POST /api/challenges/challenge/<challenge_pk>/participant_team/<participant_team_pk>
```

## Management (hosts)

- `POST /api/challenges/challenge/<challenge_pk>/disable`
- `POST /api/challenges/challenge/<challenge_pk>/pause_submissions/`
- Phase-level pause endpoints under `challenge_phase/`

Exact payloads match serializers in `apps/challenges/`. Inspect OpenAPI schema on your deployment for required fields.

## See also

- [Authentication](../authentication.html)
- [Submissions API](submissions.html)
- [Challenge configuration](../../02-for-challenge-hosts/configuration/challenge-config.html)
