# Authentication

EvalAI REST APIs use token authentication for programmatic access.

## Obtain a token

### Web UI

1. Log in at [eval.ai](https://eval.ai).
2. Open [Profile](https://eval.ai/web/profile).
3. Click **Get your Auth Token** and copy the token.

### API login endpoint

```
POST /api/auth/login/
```

Body (JSON):

```json
{
  "username": "<email_or_username>",
  "password": "<password>"
}
```

Response includes a `token` field. Use it in the `Authorization` header:

```
Authorization: Token <your_token>
```

Tokens may expire depending on server configuration (`rest_framework_expiring_authtoken`).

## Using the token

Include the header on all authenticated API requests:

```bash
curl -H "Authorization: Token <token>" https://eval.ai/api/challenges/challenge/present/approved/public
```

Staging base URL: `https://staging.eval.ai`.

## EvalAI CLI

```bash
pip install evalai
evalai login
```

The CLI stores credentials locally. See [EvalAI CLI](https://cli.eval.ai/).

## Security

- Do not commit tokens to git or share them in public issues.
- Rotate tokens if exposed.
- Use staging only for testing.

## See also

- [Challenges endpoints](endpoints/challenges.html)
- [Submissions endpoints](endpoints/submissions.html)
