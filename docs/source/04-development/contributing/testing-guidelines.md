# Testing Guidelines

EvalAI uses pytest for backend tests and frontend test tooling in `frontend/`.

## Running backend tests

With Docker (recommended):

```bash
docker compose exec django pytest
```

Or locally with development settings and dependencies from `requirements/dev.txt`.

## Coverage

CI reports coverage on pull requests. If coverage drops, add tests for new branches and edge cases. Open the coverage report linked from the PR checks to find uncovered lines.

## Test layout

Tests live under `tests/` mirroring app structure, for example `tests/unit/challenges/`, `tests/unit/jobs/`.

## Writing good tests

- Test API contracts and worker behavior for submission flows.
- Mock external services (S3, SQS) where existing tests do.
- Avoid flaky timing-dependent assertions on queue workers.

## See also

- [Code Standards](code-standards.html)
- [Contribution Guide](contribution-guide.html)
