# Code Upload / RL Challenge Example

Code-upload challenges collect participant code (often Docker images) and evaluate inside managed environments on EvalAI workers.

## When to use

- Reinforcement learning tasks with custom simulators
- Submissions that must execute arbitrary code safely in sandboxes
- Metrics computed by running participant agents against hidden tests

## Configuration

Follow challenge-type guidance in [Challenge Types](../../02-for-challenge-hosts/hosting-guide/challenge-types.html) and the EvalAI-Starters templates for code-upload challenges.

Key differences from prediction upload:

- Submission artifact is executable code or an image, not just result files
- Worker path uses `code_upload_submission_worker.py`
- Stricter resource and timeout limits apply

## Host responsibilities

- Provide clear resource limits and baseline instructions in HTML templates
- Test evaluation images locally before publishing phases
- Monitor worker logs for OOM or timeout failures

## See also

- [Worker setup](../../04-development/deployment/worker-setup.html)
- [Hosting guide](../../02-for-challenge-hosts/hosting-guide/host-challenge.html)
