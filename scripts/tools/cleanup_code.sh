#!/bin/bash

# Only process staged Python files
# IMPORTANT: This script only modifies files that are already staged.
# It will NOT stage any unstaged files or new files.
# Get staged files (files that are in the index)
echo "Finding staged Python files..."
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)

# If files are passed as arguments (from pre-commit), filter to only include staged ones
if [ $# -gt 0 ]; then
    STAGED_FILES=""
    for file in "$@"; do
        # Check if file is staged
        if git diff --cached --name-only --diff-filter=ACM | grep -q "^${file}$"; then
            STAGED_FILES="$STAGED_FILES $file"
        fi
    done
    if [ -n "$STAGED_FILES" ]; then
        CHANGED_FILES="$STAGED_FILES"
        echo "Processing staged files from pre-commit:"
    fi
fi

if [ -z "$CHANGED_FILES" ]; then
    echo "No changed Python files found."
    exit 0
fi

# Filter out excluded paths
FILTERED_FILES=""
for file in $CHANGED_FILES; do
    if [[ ! "$file" =~ ^(env/|docs/) ]]; then
        FILTERED_FILES="$FILTERED_FILES $file"
    fi
done

if [ -z "$FILTERED_FILES" ]; then
    echo "No changed Python files to process (all excluded)."
    exit 0
fi

echo "Processing changed files:"
echo "$FILTERED_FILES" | sed 's/^/  /'

# Clean unused imports (W0611, W0614) and variables (W0612)
echo ""
echo "Removing unused imports and variables with autoflake..."
for file in $FILTERED_FILES; do
    autoflake --in-place \
        --remove-duplicate-keys \
        --remove-unused-variables \
        --expand-star-imports \
        --remove-all-unused-imports "$file"
done

# Fix long lines (C0301): max 79 characters
# Use Black first as it's more aggressive about line wrapping
echo ""
echo "Running Black to fix line lengths (79 chars max)..."
for file in $FILTERED_FILES; do
    black --line-length 79 --quiet "$file" || true
done

# Then use autopep8 to fix any remaining line length issues
echo ""
echo "Running autopep8 to fix any remaining line length issues..."
for file in $FILTERED_FILES; do
    autopep8 --in-place \
        --aggressive --aggressive \
        --select=E501 \
        --max-line-length=79 \
        --ignore-local-config "$file" || true
done

# Run Black again to ensure consistency after autopep8
echo ""
echo "Running Black again for final formatting..."
for file in $FILTERED_FILES; do
    black --line-length 79 --quiet "$file" || true
done

# Stage the modified files so pylint/flake8 check the cleaned versions
# Only stage files that were already staged
echo ""
echo "Staging cleaned files..."
for file in $FILTERED_FILES; do
    if git diff --cached --name-only --diff-filter=ACM | grep -q "^${file}$"; then
        git add "$file"
    fi
done

echo ""
echo "Code cleanup complete. Cleaned files have been re-staged."
