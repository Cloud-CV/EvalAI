# Scaling Guidelines

EvalAI scales web traffic and evaluation throughput independently.

## Submission workers

- Add worker processes or containers when submission backlog grows (near challenge deadlines).
- Workers are stateless aside from per-process evaluation script caches — horizontal scaling is safe.
- Remote evaluation challenges do not use EvalAI workers for `evaluate()` — hosts scale their own workers instead.

## Auto-scaling scripts

The repository includes maintenance scripts under `scripts/monitoring/` (for example `auto_scale_workers.py`, `auto_scale_eks_nodes.py`) used in deployed environments to adjust capacity from queue depth and challenge metadata.

## Database

- Monitor PostgreSQL CPU, connections, and slow queries during large challenges.
- Index-heavy tables include submissions and leaderboard entries — avoid long-running migrations during active competitions.

## Cost awareness

Challenge hosts on EvalAI hosted plans may purchase additional workers; see [Pricing](../../01-getting-started/pricing.html).

## See also

- [Worker Setup](worker-setup.html)
- [Monitoring](../maintenance/monitoring.html)
