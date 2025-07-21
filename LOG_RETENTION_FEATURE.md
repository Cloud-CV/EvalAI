# EvalAI Log Retention Feature

## Overview

The Log Retention feature in EvalAI manages data lifecycle by automatically cleaning up submission artifacts, logs, and evaluation outputs after a specified retention period. This helps reduce storage costs while ensuring compliance with data retention policies.

## Core Components

### Backend Models

#### Challenge Model Fields
- `retention_policy_consent`: Boolean flag indicating host consent
- `retention_policy_consent_date`: When consent was provided
- `retention_policy_consent_by`: User who provided consent
- `retention_policy_notes`: Optional notes about retention policy
- `log_retention_days_override`: Admin override for retention period

#### Submission Model Fields
- `retention_eligible_date`: When submission becomes eligible for deletion
- `is_artifact_deleted`: Flag indicating if artifacts were deleted
- `artifact_deletion_date`: Timestamp of deletion
- `retention_policy_applied`: Description of applied policy
- `retention_override_reason`: Reason for any overrides

### API Endpoints

#### Retention Consent Management
- `POST /challenges/{challenge_pk}/retention-consent/` - Provide consent
- `GET /challenges/{challenge_pk}/retention-consent-status/` - Get consent status
- `POST /challenges/{challenge_pk}/update-retention-consent/` - Update consent
- `GET /challenges/{challenge_pk}/retention-info/` - Get comprehensive retention info

### Frontend Implementation

#### Challenge Controller (`challengeCtrl.js`)
- `fetchRetentionConsentStatus()`: Loads current consent status
- `toggleRetentionConsent()`: Shows confirmation dialog and handles consent toggle
- `actuallyToggleRetentionConsent()`: Makes API call to update consent

#### UI Components
- Toggle switch for consent management
- Status display showing consent state
- Confirmation dialogs for consent actions
- Loading states and error handling

### Celery Tasks

#### Scheduled Tasks (Celery Beat)
```python
CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-submission-artifacts": {
        "task": "challenges.aws_utils.cleanup_expired_submission_artifacts",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),  # Monthly on 1st at 2 AM UTC
    },
    "weekly-retention-notifications-and-consent-log": {
        "task": "challenges.aws_utils.weekly_retention_notifications_and_consent_log",
        "schedule": crontab(hour=10, minute=0, day_of_week=1),  # Weekly on Mondays at 10 AM UTC
    },
    "update-submission-retention-dates": {
        "task": "challenges.aws_utils.update_submission_retention_dates",
        "schedule": crontab(hour=1, minute=0, day_of_week=0),  # Weekly on Sundays at 1 AM UTC
    },
}
```

#### Task Functions

**cleanup_expired_submission_artifacts()**
- Runs monthly on the 1st at 2 AM UTC
- Finds submissions with `retention_eligible_date <= now()`
- Deletes submission files from storage
- Updates `is_artifact_deleted` flag

**weekly_retention_notifications_and_consent_log()**
- Runs weekly on Mondays at 10 AM UTC
- Sends warning emails for submissions expiring in 14 days
- Logs recent consent changes for audit purposes

**update_submission_retention_dates()**
- Runs weekly on Sundays at 1 AM UTC
- Updates retention dates for submissions based on current challenge settings
- Handles changes in challenge phase end dates

### AWS Integration

#### CloudWatch Log Retention
- `set_cloudwatch_log_retention()`: Sets CloudWatch log retention policy
- Requires host consent before applying retention policies
- Default: 30 days after challenge end date
- Admin can override with `log_retention_days_override`

#### Automatic Triggers
- Challenge approval: Updates log retention
- Worker restart: Updates log retention
- Task definition registration: Updates log retention

### Signals and Automation

#### Django Signals
- `update_submission_retention_on_phase_change`: Updates retention dates when phase changes
- `set_submission_retention_on_create`: Sets initial retention date for new submissions

#### Retention Calculation
- Based on challenge phase end date
- Only applies to non-public phases
- Requires host consent
- Default: 30 days after phase end

## User Consent Flow

1. **Host Access**: Only challenge hosts can provide consent
2. **Consent Dialog**: Frontend shows confirmation dialog explaining implications
3. **API Call**: Consent is recorded via API with optional notes
4. **Automatic Application**: Once consent is given, retention policies are automatically applied
5. **Withdrawal**: Hosts can withdraw consent at any time

## Data Safety

- **No Consent = No Deletion**: Without consent, data is retained indefinitely
- **Warning Notifications**: Hosts receive 14-day advance warnings
- **Audit Trail**: All consent changes are logged with timestamps
- **Admin Override**: Admins can set custom retention periods

---

## manage_retention.py Script

### Overview
A command-line utility for managing retention policies and performing cleanup operations.

### Usage
```bash
docker-compose exec django python scripts/manage_retention.py <command> [options]
```

### Commands

#### `cleanup [--dry-run]`
**Purpose**: Clean up expired submission artifacts

**Options**:
- `--dry-run`: Show what would be cleaned without actually deleting

**Example**:
```bash
# Perform actual cleanup
docker-compose exec django python scripts/manage_retention.py cleanup

# Preview what would be cleaned
docker-compose exec django python scripts/manage_retention.py cleanup --dry-run
```

**Functionality**:
- Triggers the `cleanup_expired_submission_artifacts` Celery task
- Returns task ID for monitoring

#### `status [--challenge-id <id>]`
**Purpose**: Show retention status for challenges

**Options**:
- `--challenge-id <id>`: Show status for specific challenge

**Example**:
```bash
# Show overall system status
docker-compose exec django python scripts/manage_retention.py status

# Show status for specific challenge
docker-compose exec django python scripts/manage_retention.py status --challenge-id 123
```

**Output**:
- Overall: Number of challenges with consent, total submissions, eligible for cleanup
- Specific challenge: Consent status, consent details, submission counts

#### `set-retention <challenge_id> [--days <days>]`
**Purpose**: Set CloudWatch log retention for a challenge

**Parameters**:
- `challenge_id`: ID of the challenge
- `--days <days>`: Optional custom retention period

**Example**:
```bash
# Set default retention (30 days)
docker-compose exec django python scripts/manage_retention.py set-retention 123

# Set custom retention (60 days)
docker-compose exec django python scripts/manage_retention.py set-retention 123 --days 60
```

**Functionality**:
- Requires host consent before applying
- Sets CloudWatch log retention policy
- Returns success/error status

#### `consent <challenge_id> <username>`
**Purpose**: Record retention consent for a challenge

**Parameters**:
- `challenge_id`: ID of the challenge
- `username`: Username of the person providing consent

**Example**:
```bash
docker-compose exec django python scripts/manage_retention.py consent 123 john_doe
```

**Functionality**:
- Records consent in the database
- Updates challenge model with consent details
- Enables retention policies for the challenge

### Error Handling
- Validates challenge and user existence
- Checks authorization (user must be challenge host)
- Provides clear error messages for failures
- Graceful handling of missing parameters

### Use Cases
1. **Administrative Cleanup**: Regular maintenance of expired data
2. **Compliance Auditing**: Checking consent status across challenges
3. **Manual Override**: Setting custom retention periods
4. **Consent Management**: Recording consent for challenges
5. **Troubleshooting**: Investigating retention-related issues 