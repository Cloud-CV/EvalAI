#!/bin/bash

# AWS Retention Management Test Runner
# This script runs comprehensive tests for the AWS retention management system

set -e  # Exit on any error

echo "🚀 AWS Retention Management Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Function to run a test and check result
run_test() {
    local test_name=$1
    local test_command=$2
    
    print_status "INFO" "Running $test_name..."
    
    if eval "$test_command"; then
        print_status "SUCCESS" "$test_name passed"
        return 0
    else
        print_status "ERROR" "$test_name failed"
        return 1
    fi
}

# Check if we're in the correct directory
if [ ! -f "manage.py" ]; then
    print_status "ERROR" "Please run this script from the Django project root directory"
    exit 1
fi

# Check if Docker is running (for docker-compose tests)
if ! docker info > /dev/null 2>&1; then
    print_status "WARNING" "Docker is not running. Some tests may be skipped."
    DOCKER_AVAILABLE=false
else
    print_status "INFO" "Docker is available"
    DOCKER_AVAILABLE=true
fi

# Initialize test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to update test counts
update_test_count() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo ""
print_status "INFO" "Starting test execution..."

# Test 1: Database Migration Check
print_status "INFO" "Checking database migrations..."
if python manage.py showmigrations challenges | grep -q "0113_add_log_retention_override"; then
    if python manage.py showmigrations challenges | grep "0113_add_log_retention_override" | grep -q "\[X\]"; then
        print_status "SUCCESS" "Migration 0113_add_log_retention_override is applied"
        update_test_count 0
    else
        print_status "WARNING" "Migration 0113_add_log_retention_override exists but not applied"
        print_status "INFO" "Applying migration..."
        if python manage.py migrate challenges 0113_add_log_retention_override; then
            print_status "SUCCESS" "Migration applied successfully"
            update_test_count 0
        else
            print_status "ERROR" "Failed to apply migration"
            update_test_count 1
        fi
    fi
else
    print_status "ERROR" "Migration 0113_add_log_retention_override not found"
    update_test_count 1
fi

# Test 2: Core Unit Tests
print_status "INFO" "Running core unit tests..."
if $DOCKER_AVAILABLE; then
    run_test "Core Unit Tests" "docker-compose exec django python manage.py test tests.unit.challenges.test_aws_utils.TestRetentionPeriodCalculation tests.unit.challenges.test_aws_utils.TestGetLogGroupName tests.unit.challenges.test_aws_utils.TestLogRetentionCallbacks tests.unit.challenges.test_aws_utils.TestSubmissionRetentionCalculation tests.unit.challenges.test_aws_utils.TestSubmissionRetentionCleanupTasks -v 0"
    update_test_count $?
else
    run_test "Core Unit Tests" "python manage.py test tests.unit.challenges.test_aws_utils.TestRetentionPeriodCalculation tests.unit.challenges.test_aws_utils.TestGetLogGroupName tests.unit.challenges.test_aws_utils.TestLogRetentionCallbacks tests.unit.challenges.test_aws_utils.TestSubmissionRetentionCalculation tests.unit.challenges.test_aws_utils.TestSubmissionRetentionCleanupTasks -v 0"
    update_test_count $?
fi

# Test 3: Management Command Tests
print_status "INFO" "Testing management commands..."
if $DOCKER_AVAILABLE; then
    run_test "Management Command Status" "docker-compose exec django python manage.py manage_retention status"
    update_test_count $?
else
    run_test "Management Command Status" "python manage.py manage_retention status"
    update_test_count $?
fi

# Test 4: AWS Simulation Tests
print_status "INFO" "Running AWS simulation tests..."
if [ -f "test_aws_retention_simulation.py" ]; then
    if $DOCKER_AVAILABLE; then
        run_test "AWS Simulation Tests" "docker-compose exec django python test_aws_retention_simulation.py"
        update_test_count $?
    else
        run_test "AWS Simulation Tests" "python test_aws_retention_simulation.py"
        update_test_count $?
    fi
else
    print_status "WARNING" "AWS simulation test file not found, skipping"
fi

# Test 5: Production Readiness Tests
print_status "INFO" "Running production readiness tests..."
if [ -f "test_production_readiness.py" ]; then
    if $DOCKER_AVAILABLE; then
        run_test "Production Readiness Tests" "docker-compose exec django python test_production_readiness.py"
        update_test_count $?
    else
        run_test "Production Readiness Tests" "python test_production_readiness.py"
        update_test_count $?
    fi
else
    print_status "WARNING" "Production readiness test file not found, skipping"
fi

# Test 6: Core Function Import Tests
print_status "INFO" "Testing core function imports..."
if $DOCKER_AVAILABLE; then
    IMPORT_TEST="docker-compose exec django python -c \"
from challenges.aws_utils import (
    calculate_retention_period_days,
    map_retention_days_to_aws_values,
    get_log_group_name,
    set_cloudwatch_log_retention,
    update_challenge_log_retention_on_approval,
    update_challenge_log_retention_on_restart,
    update_challenge_log_retention_on_task_def_registration,
    calculate_submission_retention_date,
    cleanup_expired_submission_artifacts,
    update_submission_retention_dates,
    send_retention_warning_notifications,
    delete_submission_files_from_storage
)
print('All core functions imported successfully')
\""
else
    IMPORT_TEST="python -c \"
from challenges.aws_utils import (
    calculate_retention_period_days,
    map_retention_days_to_aws_values,
    get_log_group_name,
    set_cloudwatch_log_retention,
    update_challenge_log_retention_on_approval,
    update_challenge_log_retention_on_restart,
    update_challenge_log_retention_on_task_def_registration,
    calculate_submission_retention_date,
    cleanup_expired_submission_artifacts,
    update_submission_retention_dates,
    send_retention_warning_notifications,
    delete_submission_files_from_storage
)
print('All core functions imported successfully')
\""
fi

run_test "Core Function Imports" "$IMPORT_TEST"
update_test_count $?

# Test 7: Management Command Import Test
print_status "INFO" "Testing management command imports..."
if $DOCKER_AVAILABLE; then
    MGMT_IMPORT_TEST="docker-compose exec django python -c \"
from challenges.management.commands.manage_retention import Command
print('Management command imported successfully')
\""
else
    MGMT_IMPORT_TEST="python -c \"
from challenges.management.commands.manage_retention import Command
print('Management command imported successfully')
\""
fi

run_test "Management Command Import" "$MGMT_IMPORT_TEST"
update_test_count $?

# Test 8: Model Field Tests
print_status "INFO" "Testing model field existence..."
if $DOCKER_AVAILABLE; then
    MODEL_TEST="docker-compose exec django python -c \"
from challenges.models import Challenge
from jobs.models import Submission
c = Challenge.objects.first()
s = Submission.objects.first()
if c and hasattr(c, 'log_retention_days_override'):
    print('Challenge.log_retention_days_override field exists')
else:
    raise Exception('Challenge.log_retention_days_override field missing')
if s and hasattr(s, 'retention_eligible_date') and hasattr(s, 'is_artifact_deleted'):
    print('Submission retention fields exist')
else:
    raise Exception('Submission retention fields missing')
\""
else
    MODEL_TEST="python -c \"
from challenges.models import Challenge
from jobs.models import Submission
c = Challenge.objects.first()
s = Submission.objects.first()
if c and hasattr(c, 'log_retention_days_override'):
    print('Challenge.log_retention_days_override field exists')
else:
    raise Exception('Challenge.log_retention_days_override field missing')
if s and hasattr(s, 'retention_eligible_date') and hasattr(s, 'is_artifact_deleted'):
    print('Submission retention fields exist')
else:
    raise Exception('Submission retention fields missing')
\""
fi

run_test "Model Field Tests" "$MODEL_TEST"
update_test_count $?

# Test 9: Basic Retention Calculation Tests
print_status "INFO" "Testing basic retention calculations..."
if $DOCKER_AVAILABLE; then
    CALC_TEST="docker-compose exec django python -c \"
from challenges.aws_utils import calculate_retention_period_days, map_retention_days_to_aws_values
from django.utils import timezone
from datetime import timedelta

now = timezone.now()
future_date = now + timedelta(days=10)
past_date = now - timedelta(days=5)

# Test future date
future_retention = calculate_retention_period_days(future_date)
print(f'Future retention: {future_retention} days')

# Test past date
past_retention = calculate_retention_period_days(past_date)
print(f'Past retention: {past_retention} days')

# Test AWS mapping
aws_mapped = map_retention_days_to_aws_values(25)
print(f'AWS mapped (25 days): {aws_mapped}')

if future_retention > 30 and past_retention > 0 and aws_mapped in [30, 60]:
    print('Basic retention calculations working correctly')
else:
    raise Exception('Retention calculations not working as expected')
\""
else
    CALC_TEST="python -c \"
from challenges.aws_utils import calculate_retention_period_days, map_retention_days_to_aws_values
from django.utils import timezone
from datetime import timedelta

now = timezone.now()
future_date = now + timedelta(days=10)
past_date = now - timedelta(days=5)

# Test future date
future_retention = calculate_retention_period_days(future_date)
print(f'Future retention: {future_retention} days')

# Test past date
past_retention = calculate_retention_period_days(past_date)
print(f'Past retention: {past_retention} days')

# Test AWS mapping
aws_mapped = map_retention_days_to_aws_values(25)
print(f'AWS mapped (25 days): {aws_mapped}')

if future_retention > 30 and past_retention > 0 and aws_mapped in [30, 60]:
    print('Basic retention calculations working correctly')
else:
    raise Exception('Retention calculations not working as expected')
\""
fi

run_test "Basic Retention Calculations" "$CALC_TEST"
update_test_count $?

# Test 10: Log Group Name Generation
print_status "INFO" "Testing log group name generation..."
if $DOCKER_AVAILABLE; then
    LOG_GROUP_TEST="docker-compose exec django python -c \"
from challenges.aws_utils import get_log_group_name
from django.conf import settings

# Test different challenge IDs
test_ids = [1, 42, 999]
for challenge_id in test_ids:
    log_group = get_log_group_name(challenge_id)
    expected = f'challenge-pk-{challenge_id}-{settings.ENVIRONMENT}-workers'
    if log_group == expected:
        print(f'Challenge {challenge_id}: {log_group} ✓')
    else:
        raise Exception(f'Expected {expected}, got {log_group}')
print('Log group name generation working correctly')
\""
else
    LOG_GROUP_TEST="python -c \"
from challenges.aws_utils import get_log_group_name
from django.conf import settings

# Test different challenge IDs
test_ids = [1, 42, 999]
for challenge_id in test_ids:
    log_group = get_log_group_name(challenge_id)
    expected = f'challenge-pk-{challenge_id}-{settings.ENVIRONMENT}-workers'
    if log_group == expected:
        print(f'Challenge {challenge_id}: {log_group} ✓')
    else:
        raise Exception(f'Expected {expected}, got {log_group}')
print('Log group name generation working correctly')
\""
fi

run_test "Log Group Name Generation" "$LOG_GROUP_TEST"
update_test_count $?

# Generate test report
echo ""
echo "======================================"
print_status "INFO" "Test Execution Complete"
echo "======================================"

# Calculate pass rate
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
else
    PASS_RATE=0
fi

echo ""
echo "📊 Test Summary:"
echo "  Total Tests: $TOTAL_TESTS"
echo "  Passed: $PASSED_TESTS ✅"
echo "  Failed: $FAILED_TESTS ❌"
echo "  Pass Rate: $PASS_RATE%"

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    print_status "SUCCESS" "ALL TESTS PASSED! 🎉"
    echo ""
    echo "🚀 Production Readiness Status: READY"
    echo ""
    echo "✅ Pre-deployment checklist:"
    echo "  ✅ Core functions working"
    echo "  ✅ Management commands functional"
    echo "  ✅ Database models updated"
    echo "  ✅ Unit tests passing"
    echo "  ✅ Retention calculations accurate"
    echo "  ✅ AWS integration ready (mocked)"
    echo ""
    echo "🔧 Next steps for production:"
    echo "  1. Configure AWS credentials in production"
    echo "  2. Test with a small challenge first"
    echo "  3. Monitor CloudWatch logs for errors"
    echo "  4. Set up alerts for retention failures"
    echo "  5. Schedule regular cleanup jobs"
    
    exit 0
elif [ $FAILED_TESTS -le 2 ]; then
    print_status "WARNING" "MOSTLY READY - Minor issues detected"
    echo ""
    echo "⚠️  Production Readiness Status: READY WITH CAUTION"
    echo ""
    echo "Please review and fix the failed tests before deployment."
    echo "The system should work but may have minor issues."
    
    exit 1
else
    print_status "ERROR" "NOT READY FOR PRODUCTION"
    echo ""
    echo "❌ Production Readiness Status: NOT READY"
    echo ""
    echo "Critical issues detected. Please fix all failed tests"
    echo "before considering production deployment."
    
    exit 1
fi 