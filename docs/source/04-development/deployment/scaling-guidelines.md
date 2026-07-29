# Scaling Guidelines

EvalAI scales web traffic and evaluation throughput independently.

## Submission workers

- Add worker processes or containers when submission backlog grows (near challenge deadlines).
- Workers are stateless aside from per-process evaluation script caches — horizontal scaling is safe.
- Remote evaluation challenges do not use EvalAI workers for `evaluate()` — hosts scale their own workers instead.

## Auto-scaling scripts

The repository includes maintenance scripts under `scripts/monitoring/` (for example `auto_scale_workers.py`, `auto_scale_eks_nodes.py`) used in deployed environments to adjust capacity from queue depth and challenge metadata.

## EKS node auto-scaling

Code-upload challenges run submissions as Kubernetes Jobs on a per-challenge EKS cluster. `scripts/lambda/auto_scale_eks_nodes_lambda.py` resizes that cluster's nodegroup from the challenge's pending submission count.

It runs in two modes:

- **Event-driven** — Django invokes it asynchronously via `trigger_eks_node_autoscale()` when a submission is created or crosses the pending/terminal boundary.
- **Scheduled sweep** — an EventBridge rule invokes it with `{"sweep": true}` to reconcile every eligible challenge. Event-driven invocations are best-effort, so this sweep is what prevents a single dropped invoke from leaving a nodegroup stuck at zero nodes with submissions pending.

Deploy both with:

```bash
ENVIRONMENT=production EVALAI_API_SERVER=https://eval.ai LAMBDA_AUTH_TOKEN=xxx \
  ./scripts/lambda/deploy_auto_scale_eks_nodes_lambda.sh
```

Pass `DLQ_ARN` to route failed asynchronous invocations to a dead-letter queue. The handler raises on unrecoverable failures rather than returning an error status code, so those failures appear in the Lambda `Errors` metric — alarm on it.

### Challenges in a host's own AWS account

A challenge with `use_host_credentials` keeps its EKS cluster in the challenge host's AWS account, which the Lambda's own execution role cannot reach. Scaling for those challenges goes through an IAM role named `evalai-autoscale-crossaccount` in the host account, which the Lambda assumes.

`setup_eks_cluster()` provisions that role automatically during cluster setup. It requires `EKS_AUTOSCALE_LAMBDA_ROLE_ARN` to be set to the autoscale Lambda's execution role ARN — without it the role is skipped with a warning and autoscaling for that challenge will fail with `AccessDeniedException` on `eks:ListNodegroups`.

The challenge must also have `aws_account_id` set. If `use_host_credentials` is enabled without it, the Lambda logs a warning and falls back to its own account.

## Database

- Monitor PostgreSQL CPU, connections, and slow queries during large challenges.
- Index-heavy tables include submissions and leaderboard entries — avoid long-running migrations during active competitions.

## Cost awareness

Challenge hosts on EvalAI hosted plans may purchase additional workers; see [Pricing](../../01-getting-started/pricing.html).

## See also

- [Worker Setup](worker-setup.html)
- [Monitoring](../maintenance/monitoring.html)
