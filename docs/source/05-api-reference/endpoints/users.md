# Users API

Account-related endpoints live under `/api/accounts/` and `/api/auth/`.

## Registration

```
POST /api/auth/registration/
```

See Django Rest Auth registration flow in `rest_auth` URLs.

## Login

```
POST /api/auth/login/
```

Returns an API token — see [Authentication](../authentication.html).

## Profile and account management

```
GET/PATCH /api/accounts/...
```

Specific routes are defined in `apps/accounts/urls.py` (profile details, email settings, etc.).

## Password reset

Password reset flows use `/api/auth/password/` endpoints and email confirmation templates.

## Participants and hosts

Participant teams and host teams have dedicated namespaces:

- `/api/participants/`
- `/api/hosts/`

Use challenge APIs to link participant teams to challenges.

## See also

- [Authentication](../authentication.html)
- [Getting started as participant](../../03-for-participants/participation-guide/getting-started.html)
