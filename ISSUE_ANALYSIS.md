# EvalAI Repository Analysis

## Tech Stack

### Backend
- **Framework**: Django 2.2.20 (Python web framework)
- **REST API**: Django REST Framework 3.10.3
- **Database**: PostgreSQL 16.8
- **Task Queue**: AWS SQS (Simple Queue Service) with Celery 4.3.0
- **Cloud Services**: AWS (S3, ECS/Fargate, EKS, EC2)
- **Authentication**: JWT (djangorestframework-simplejwt) + Token Auth
- **Other**: 
  - Boto3 (AWS SDK)
  - Docker & Docker Compose
  - Kubernetes (for code upload workers)
  - StatsD/Prometheus (monitoring)

### Frontend
- **Legacy Frontend**: AngularJS 1.x (in `frontend/` directory)
  - Gulp build system
  - Materialize CSS
- **Modern Frontend**: Angular 7.2.15 (in `frontend_v2/` directory)
  - TypeScript
  - Angular Material
  - RxJS

### Workers
- **Submission Workers**: Python scripts that process submissions
  - `submission_worker.py` - Standard submission processing
  - `remote_submission_worker.py` - Remote evaluation workers
  - `code_upload_submission_worker.py` - Code upload challenge workers
- **Python Versions**: 3.7, 3.8, 3.9 (separate Docker images)

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (dev/staging/prod)
- **Monitoring**: Prometheus, Grafana, StatsD
- **Message Queue**: AWS SQS (ElasticMQ for local dev)

---

## Issue Analysis: Submissions Stuck at "Submitted" Status

### Problem Description
Submissions to nuScenes 3D Detection and Prediction challenges remain stuck in "Submitted" status for 10+ days, while Tracking challenge submissions work correctly.

### How Submission Processing Works

1. **Submission Flow**:
   ```
   User Upload → API (challenge_submission) → Create Submission (status="submitted")
   → Publish Message to SQS Queue → Worker Consumes Message → Process Submission
   → Update Status to "running" → Evaluate → Update Status to "finished"/"failed"
   ```

2. **Key Components**:
   - **Submission Model** (`apps/jobs/models.py`): Tracks submission status
   - **Submission API** (`apps/jobs/views.py`): Creates submission and publishes to queue
   - **Queue Publisher** (`apps/jobs/sender.py`): Publishes messages to challenge-specific SQS queue
   - **Submission Worker** (`scripts/workers/submission_worker.py`): Consumes messages and processes submissions

3. **Queue Architecture**:
   - Each challenge has its own SQS queue (stored in `challenge.queue` field)
   - Queue name format: `{challenge-title}-{challenge-id}` (sanitized)
   - Workers are configured with `CHALLENGE_QUEUE` environment variable
   - Workers connect to specific queues and process messages

### Root Cause Analysis

The issue is likely one of these scenarios:

#### 1. **No Workers Running for Detection/Prediction Queues** ⚠️ MOST LIKELY
- Each challenge requires dedicated workers listening to its specific queue
- Workers are started with `CHALLENGE_QUEUE` environment variable set to the challenge's queue name
- If no workers are running for nuScenes Detection/Prediction queues, messages accumulate but are never processed
- **Evidence**: Tracking works (workers are running), Detection/Prediction don't (no workers)

#### 2. **Worker Configuration Issues**
- Workers might be crashing on startup for these specific challenges
- Check worker logs for errors during challenge loading
- Workers load evaluation scripts at startup - if scripts are corrupted or incompatible, workers fail

#### 3. **Queue Configuration Problems**
- Queue might not exist or have incorrect permissions
- AWS credentials might be expired or incorrect for these queues
- Queue retention period might be too short (messages expiring)

#### 4. **Challenge-Specific Issues**
- Evaluation scripts for Detection/Prediction might be broken
- Challenge configuration might have errors preventing worker startup
- Resource constraints (CPU/memory) for these specific challenges

### Code Locations to Investigate

1. **Worker Startup** (`scripts/workers/submission_worker.py:876-920`):
   - Workers load challenges based on `CHALLENGE_PK` or filter active challenges
   - They connect to queue specified by `CHALLENGE_QUEUE` environment variable
   - If challenge loading fails, worker exits

2. **Queue Connection** (`scripts/workers/submission_worker.py:808-856`):
   - Workers get or create SQS queues
   - Handles both host-managed and EvalAI-managed queues

3. **Message Processing** (`scripts/workers/submission_worker.py:922-984`):
   - Workers poll queue for messages
   - Process messages and update submission status
   - If workers aren't running, messages never get processed

4. **Submission Creation** (`apps/jobs/views.py:140-400`):
   - Creates submission with status="submitted"
   - Publishes message to challenge queue
   - If queue doesn't exist or has issues, message might be lost

### Diagnostic Steps

1. **Check Worker Status**:
   ```bash
   # Check if workers are running for nuScenes Detection/Prediction queues
   # Look for containers/processes with CHALLENGE_QUEUE matching these challenges
   ```

2. **Check Queue Messages**:
   ```python
   # In Django shell or via AWS console
   # Check if messages are accumulating in the queues
   challenge = Challenge.objects.get(title__icontains="nuScenes Detection")
   queue_name = challenge.queue
   # Check SQS queue for pending messages
   ```

3. **Check Worker Logs**:
   - Look for errors during worker startup
   - Check if workers are successfully loading challenges
   - Verify queue connections are successful

4. **Check Challenge Configuration**:
   ```python
   # Verify challenge queue names
   detection_challenge = Challenge.objects.get(title__icontains="Detection")
   prediction_challenge = Challenge.objects.get(title__icontains="Prediction")
   tracking_challenge = Challenge.objects.get(title__icontains="Tracking")
   
   print(f"Detection queue: {detection_challenge.queue}")
   print(f"Prediction queue: {prediction_challenge.queue}")
   print(f"Tracking queue: {tracking_challenge.queue}")
   ```

### Solutions

#### Immediate Fix
1. **Deploy Workers for Detection/Prediction Queues**:
   ```bash
   # Start workers with correct CHALLENGE_QUEUE environment variable
   docker-compose run -e CHALLENGE_QUEUE={detection_queue_name} worker_py3_9
   docker-compose run -e CHALLENGE_QUEUE={prediction_queue_name} worker_py3_9
   ```

2. **Verify Queue Existence**:
   - Ensure queues exist in AWS SQS
   - Check queue permissions and retention settings

3. **Check Worker Health**:
   - Monitor worker logs for errors
   - Verify workers can connect to queues
   - Ensure workers can load challenge evaluation scripts

#### Long-term Improvements
1. **Worker Health Monitoring**: Add alerts when workers go down
2. **Queue Monitoring**: Track message age in queues
3. **Automatic Worker Scaling**: Scale workers based on queue depth
4. **Better Error Handling**: Retry failed submissions automatically

### Files to Check

- `scripts/workers/submission_worker.py` - Main worker logic
- `apps/jobs/sender.py` - Queue publishing
- `apps/jobs/views.py` - Submission API
- `apps/challenges/models.py` - Challenge model (queue field)
- `scripts/monitoring/auto_scale_workers.py` - Worker scaling logic

---

## Additional Issues Found

### 1. **Outdated Dependencies**
- Django 2.2.20 is EOL (End of Life) - security risk
- Angular 7 is outdated (current is Angular 17+)
- Many Python packages are pinned to old versions

### 2. **Code Quality**
- No linter errors found (good!)
- Large codebase with multiple worker implementations
- Some duplicate code between worker types

### 3. **Documentation**
- Good documentation in `docs/` directory
- README provides clear setup instructions
- Architecture documentation available

### 4. **Testing**
- Comprehensive test suite in `tests/` directory
- Unit tests for workers, views, models
- Integration tests available

---

## Recommendations

1. **Immediate**: Deploy workers for nuScenes Detection/Prediction queues
2. **Short-term**: Add monitoring/alerting for worker health
3. **Medium-term**: Upgrade Django and Angular versions
4. **Long-term**: Implement automatic worker scaling and better queue management

