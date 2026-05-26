# Code Standards

EvalAI follows PEP 8 style with automated formatting and linting.

## Formatting

- Use [Black](https://github.com/psf/black) for Python formatting.
- Pre-commit hooks run Black and Flake8 — install once with `pre-commit install` from the repo root.

## Pull requests

- Branch from `master` (see [Contribution Guide](contribution-guide.html)).
- Keep changes focused; include tests for backend logic changes.
- Follow existing patterns in the app you modify (`apps/challenges`, `apps/jobs`, etc.).

## Frontend

Match existing AngularJS structure in `frontend/src/`. Run frontend tests and linters as documented in the root README before submitting.

## Documentation

When changing user-facing behavior, update the relevant page under `docs/source/`. Build locally with:

```bash
cd docs && make html
```

## See also

- [Testing Guidelines](testing-guidelines.html)
- [Pull Requests](pull-requests.html)
