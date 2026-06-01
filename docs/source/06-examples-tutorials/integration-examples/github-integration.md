# GitHub Integration

EvalAI syncs challenges from GitHub repositories created from [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters).

## Workflow

1. Create a repo from the template.
2. Add `AUTH_TOKEN` secret (GitHub PAT).
3. Configure `github/host_config.json` with EvalAI token and `host_team_pk`.
4. Work on the `challenge` branch only — pushes trigger CI to validate and sync YAML, templates, and evaluation scripts.
5. View build logs in GitHub Actions; configuration errors open automated issues.

## Detailed steps

See [Getting Started as a Challenge Host](../../02-for-challenge-hosts/hosting-guide/getting-started.html).

## Updating challenges

Push commits to `challenge`. EvalAI updates challenge metadata when the workflow succeeds.

## See also

- [Challenge examples with EvalAI-Starters](../evalai-starters-guide.html)
- [Host a challenge](../../02-for-challenge-hosts/hosting-guide/host-challenge.html)
- [Remote evaluation example](../host-examples/remote-evaluation.html)
