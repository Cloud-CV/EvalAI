# Auto-Scaling and Auto-Cancellation Scripts

EvalAI provides automated scripts to manage worker scaling and submission lifecycle in production environments. These tools help optimize resource usage and reduce costs by automatically starting/stopping workers based on submission load.

## Overview

The auto-scaling infrastructure consists of several monitoring scripts located in `scripts/monitoring/`:

- `auto_scale_workers.py` - Scales evaluation workers up/down based on pending submissions
- `auto_scale_ec2_workers.py` - Manages AWS EC2 worker instances
- `auto_scale_eks_nodes.py` - Scales Amazon EKS cluster nodes
- `auto_cancel_submissions.py` - Auto-cancels stale submissions
- `auto_stop_workers.py` - Stops idle worker instances

## Auto-Scaling Workers

### How It Works

The auto-scaling script monitors pending submissions for each challenge and automatically:

1. **Scales UP**: Starts a worker when submissions are pending and no workers are running
2. **Scales DOWN**: Stops workers when no pending submissions exist or the challenge has ended

### Submission States Monitored

The script tracks submissions in these states:
- `submitted` - Queued for evaluation
- `running` - Currently being evaluated  
- `queued` - Waiting in queue
- `resuming` - Rerun in progress

### Running the Auto-Scaling Script

**Prerequisites:**
```bash
export API_HOST_URL="https://your-evalai-instance.com"
export AUTH_TOKEN="your-evalai-auth-token"
export ENV="prod"  # or "dev" for development
```

**Execute:**
```bash
python scripts/monitoring/auto_scale_workers.py
```

**As a Cron Job** (recommended for production):
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/EvalAI && bash scripts/monitoring/run_auto_scale_workers.sh
```

### Configuration

The script uses these AWS environment variables for worker management:
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_DEFAULT_REGION` - AWS region (e.g., `us-east-1`)

### Behavior by Environment

**Production (`ENV=prod`):**
- Only scales workers for challenges with `remote_evaluation=False`
- Local evaluation workers are managed automatically

**Development (`ENV=dev`):**
- Scales all workers regardless of evaluation type
- Useful for testing auto-scaling logic

### Key Functions

```python
# Get pending submission count across all states
def get_pending_submission_count(challenge_metrics):
    pending_submissions = 0
    for status in ["running", "submitted", "queued", "resuming"]:
        pending_submissions += challenge_metrics.get(status, 0)
    return pending_submissions

# Scale down when idle or challenge ended
def scale_down_workers(challenge, num_workers):
    if num_workers > 0:
        response = stop_worker(challenge["id"])
        
# Scale up when work is pending
def scale_up_workers(challenge, num_workers):
    if num_workers == 0:
        response = start_worker(challenge["id"])
```

## Auto-Cancelling Stale Submissions

### Purpose

The auto-cancel script prevents resource waste by cancelling submissions that have been stuck in `submitted`, `running`, or `resuming` states for an extended period.

### Default Thresholds

- **Cancellation Timeout**: 14 days (configurable)
- **Cancellation States**: `submitted`, `running`, `resuming`

### Running the Auto-Cancel Script

**Prerequisites:**
```bash
export AUTH_TOKEN="your-evalai-auth-token"
export API_HOST_URL="https://your-evalai-instance.com"
```

**Execute:**
```bash
python scripts/monitoring/auto_cancel_submissions.py
```

**Customize Timeout** (in script or via modification):
```python
# Cancel submissions older than 7 days instead of 14
auto_cancel_submissions(challenge_pk, days_threshold=7)
```

**As a Cron Job**:
```bash
# Run daily at midnight
0 0 * * * cd /path/to/EvalAI && bash scripts/monitoring/run_auto_cancel_submissions.sh
```

### How It Works

1. Fetches all challenges from the EvalAI API
2. For each challenge, retrieves submissions in `submitted`, `running`, and `resuming` states
3. Checks submission time (uses `rerun_resumed_at` if available, otherwise `submitted_at`)
4. Cancels submissions older than the threshold
5. Updates submission status to `cancelled`

### Example Log Output

```
Running auto-cancel script for challenge 123
Cancelled submission with PK 45678. Previous status: running. Time Lapsed: 15 days, 3:24:15
Running auto-cancel script for challenge 124
...
```

## AWS-Specific Auto-Scaling

### EC2 Workers

`auto_scale_ec2_workers.py` manages AWS EC2 instances directly:
```bash
python scripts/monitoring/auto_scale_ec2_workers.py
```

### EKS Cluster Nodes

`auto_scale_eks_nodes.py` scales Amazon EKS Kubernetes cluster nodes:
```bash
python scripts/monitoring/auto_scale_eks_nodes.py
```

Both scripts require appropriate AWS IAM permissions for EC2/EKS management.

## Monitoring and Alerts

### Checking Worker Status

Use the EvalAI interface to monitor active workers:
```python
from evalai_interface import EvalAI_Interface

evalai = EvalAI_Interface(auth_token, api_url)
challenge = evalai.get_challenge_by_pk(challenge_id)
print(f"Active workers: {challenge['workers']}")
```

### Log Files

Scripts log important events:
- Worker start/stop operations
- API responses
- Errors and exceptions
- Challenge metrics

Monitor logs to track auto-scaling behavior and troubleshoot issues.

## Important Warnings

### ⚠️ AWS Usage and Costs

**EvalAI is not liable for AWS costs incurred due to auto-scaling failures or misconfigurations.**

- **Monitor your AWS billing dashboard regularly**
- Set up AWS billing alerts for cost thresholds
- Verify auto-scaling is working correctly after setup
- Manually scale down workers if auto-scaling fails

### Failure Scenarios to Watch

1. **Script Failures**: If the cron job stops running, workers may remain active indefinitely
2. **API Downtime**: Workers won't scale down if the EvalAI API is unreachable
3. **Auth Token Expiry**: Ensure your `AUTH_TOKEN` remains valid
4. **AWS Limits**: Check AWS service quotas and limits

### Recommended Safety Measures

```bash
# Set maximum instance limits in AWS
# Configure AWS cost alerts
# Run scripts with proper error handling
# Keep logs for debugging
# Test in dev environment first
```

## Contact Support

If auto-scaling fails or behaves unexpectedly:
1. Check your AWS usage immediately
2. Manually scale down workers if necessary
3. Review script logs for errors
4. Contact the EvalAI team on Slack/GitHub with:
   - Error messages
   - Challenge ID
   - AWS region and configuration
   - Timeline of the issue

## Related Documentation

- [Worker Setup](worker-setup.md) - Setting up evaluation workers
- [Production Deployment](production-deployment.md) - Deploying EvalAI in production
- [Scaling Guidelines](scaling-guidelines.md) - General scaling best practices
