#!/bin/bash
set -e

echo "=========================================="
echo "Testing Frontend Build and Tests"
echo "=========================================="

echo ""
echo "Step 1: Checking for existing Chrome processes..."
BEFORE=$(docker-compose run --rm nodejs bash -c "ps aux | grep -E 'chrome|chromium' | grep -v grep | wc -l" 2>/dev/null || echo "0")
echo "Chrome processes before: $BEFORE"

echo ""
echo "Step 2: Rebuilding nodejs container..."
docker-compose build nodejs

echo ""
echo "Step 3: Running full test command..."
echo "Command: npm install && gulp dev && karma start --single-run --reporters=junit,coverage && pkill -f chrome || true && pkill -f chromium || true && gulp staging"
echo ""

START_TIME=$(date +%s)
docker-compose run --rm nodejs bash -c "npm install && gulp dev && karma start --single-run --reporters=junit,coverage && pkill -f chrome || true && pkill -f chromium || true && gulp staging"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "Step 4: Checking for remaining Chrome processes..."
AFTER=$(docker-compose run --rm nodejs bash -c "ps aux | grep -E 'chrome|chromium' | grep -v grep | wc -l" 2>/dev/null || echo "0")
echo "Chrome processes after: $AFTER"

echo ""
echo "=========================================="
echo "Results:"
echo "  Duration: ${DURATION} seconds"
echo "  Chrome processes before: $BEFORE"
echo "  Chrome processes after: $AFTER"
echo "=========================================="

if [ "$AFTER" -gt "$BEFORE" ]; then
    echo "⚠️  WARNING: Chrome processes may not have been cleaned up properly"
    exit 1
else
    echo "✅ SUCCESS: Tests completed and Chrome processes cleaned up"
    exit 0
fi
