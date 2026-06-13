# Monitoring

Operators should monitor API health, worker backlog, and infrastructure metrics during active challenges.

## Application health

- HTTP health endpoints and load balancer checks for Django/API services.
- Error rates and latency from your APM or load balancer logs.

## Submission queue

- Queue depth for `submission_task_queue` — sustained growth indicates worker starvation.
- Age of oldest message — alerts before deadlines help prevent participant delays.

## Workers

- Worker process restarts and OOM kills.
- Logs in worker containers for repeated evaluation exceptions (often host script bugs).

## Scripts in this repository

`scripts/monitoring/` contains utilities used in deployed environments, including auto-scaling helpers. Adapt them to your metrics stack (CloudWatch, Prometheus, etc.).

## Challenge hosts

Hosts using remote evaluation should monitor their own worker processes separately — EvalAI does not run `evaluate()` on platform workers for those challenges.

## See also

- [Scaling Guidelines](../deployment/scaling-guidelines.html)
- [Common evaluation issues](../../07-troubleshooting/common-issues/evaluation-issues.html)
