# TODO: Add is_cli flag to submissions for CLI vs UI tracking

## Backend Implementation (Django)

### Tasks:

- [x] Add `is_cli` field to Submission model in `apps/jobs/models.py`
- [x] Add `is_cli` to SubmissionSerializer in `apps/jobs/serializers.py`
- [x] Add `is_cli` to ChallengeSubmissionManagementSerializer in `apps/jobs/serializers.py`
- [x] Create migration file `apps/jobs/migrations/0027_add_is_cli_field.py`

## Implementation Details:

### 1. Model (apps/jobs/models.py)

Added `is_cli` boolean field with default=False and db_index=True:

```
python
is_cli = models.BooleanField(default=False, db_index=True)
```

### 2. Serializers (apps/jobs/serializers.py)

Added `is_cli` to both:

- SubmissionSerializer (for participant submissions)
- ChallengeSubmissionManagementSerializer (for host management)

### 3. Migration (apps/jobs/migrations/0027_add_is_cli_field.py)

Created migration to add the field to the database.

## Usage:

- When `is_cli=True`: Submission was made via CLI
- When `is_cli=False` (default): Submission was made via UI

## To run the migration:

```
bash
python manage.py migrate
```

## Notes:

- The CLI should send `is_cli=True` in the submission request body when making submissions
- The UI will automatically have `is_cli=False` (default value)
- The field is indexed for efficient querying
