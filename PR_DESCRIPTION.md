## Summary

This PR fixes the issue where the `Subscribers` model lacked a database-level uniqueness constraint on the `email` field, which could lead to duplicate subscriber records.

## Problem

The `Subscribers` model only had application-level validation for duplicate emails in the subscription API endpoint (`apps/web/views.py`). This approach is vulnerable to:
- **Race conditions** when multiple requests arrive simultaneously
- **Concurrent database inserts** that bypass application logic
- **Direct database operations** (SQL, admin panel, data migrations)
- **Bulk imports** that don't go through the API

## Solution

### 1. Model Change
Added `unique=True` constraint to the `email` field in the `Subscribers` model:

**File:** `apps/web/models.py`
```python
email = models.EmailField(max_length=70, unique=True)
```

### 2. Database Migration
Created migration `0011_add_unique_constraint_to_subscribers_email.py` to apply the constraint at the database level.

**File:** `apps/web/migrations/0011_add_unique_constraint_to_subscribers_email.py`

### 3. Test Coverage
Added a test to verify the unique constraint enforcement:

**File:** `tests/unit/web/test_models.py`
```python
def test_email_unique_constraint(self):
    """Test that duplicate email addresses raise IntegrityError"""
    with self.assertRaises(IntegrityError):
        Subscribers.objects.create(email="subscriber@domain.com")
```

### 4. Duplicate Check Script
Created a utility script to check for existing duplicates before migration:

**File:** `scripts/check_subscriber_duplicates.py`

This script helps identify any existing duplicate records that would prevent the migration from running successfully.

## Files Changed

- `apps/web/models.py` - Added `unique=True` to email field
- `apps/web/migrations/0011_add_unique_constraint_to_subscribers_email.py` - New migration
- `tests/unit/web/test_models.py` - Added test for uniqueness constraint
- `scripts/check_subscriber_duplicates.py` - New utility script

## Testing

### Run the test
```bash
pytest tests/unit/web/test_models.py::SubscribersTestCase::test_email_unique_constraint -v
```

### Check for duplicates before migration
```bash
python scripts/check_subscriber_duplicates.py
```

### Apply the migration
```bash
python manage.py migrate web
```

Or with Docker:
```bash
docker-compose run --rm django python manage.py migrate web
```

## Notes

- The existing application-level check in the subscription API remains valuable for providing user-friendly error messages
- The database constraint serves as a final safety net to guarantee data integrity
- If existing duplicates are found, they must be cleaned up before the migration can be applied

## Backward Compatibility

This change enforces stricter data integrity but should not break existing functionality:
- ✅ API behavior remains the same (application-level check still returns the same error)
- ✅ No breaking changes to the API interface
- ⚠️ Migration requires no existing duplicates in the database

## Resolves

Fixes the issue: "Subscribers model does not enforce a database-level uniqueness constraint on the email field"

