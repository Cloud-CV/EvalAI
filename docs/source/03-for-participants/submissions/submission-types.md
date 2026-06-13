# Submission Types

EvalAI supports different submission models depending on how the host configured the challenge.

## Prediction upload

Participants upload output files (JSON, ZIP, CSV, etc.). EvalAI runs the host's evaluation script and returns metrics. This is the most common format.

- Configure on host side: `remote_evaluation: false`
- Participant guide: [Prediction Upload](prediction-upload.html)

## Remote evaluation

Participants still upload through EvalAI, but evaluation runs on the host's remote worker. Behavior on the participant side is similar to prediction upload; processing may depend on the host worker being online.

- Host guide: [Remote Evaluation](../../02-for-challenge-hosts/evaluation/remote-evaluation.html)

## Code upload / environment-based

Some challenges accept code (for example Docker images) evaluated inside isolated environments on EvalAI workers. Requirements are defined in the challenge description and starter templates.

- Host example: [Code Upload RL Example](../../06-examples-tutorials/host-examples/code-upload-rl.html)

## Choosing what to submit

Always read the challenge-specific:

- Submission guidelines (format, naming, required fields)
- Phase codenames and date ranges
- Public vs private leaderboard rules

## Processing pipeline

All submission types follow the same high-level flow: REST API creates a submission record → message queue → worker runs `evaluate()` → leaderboard update. Details: [Submission processing](../../04-development/deployment/worker-setup.html) (developer docs).
