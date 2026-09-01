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

if ! command -v ruff >/dev/null 2>&1; then
    echo "ruff is not installed. Run: pip install -r requirements/dev.txt" >&2
    exit 1
fi

echo "Processing changed files:"
echo "$FILTERED_FILES" | sed 's/^/  /'

# Apply lint fixes: unused imports and variables (F401/F841, previously
# autoflake) and import ordering (I001, previously isort). Only safe fixes
# are applied -- ruff leaves anything it cannot rewrite without changing
# behaviour for the author to resolve.
echo ""
echo "Applying ruff lint fixes..."
# shellcheck disable=SC2086
ruff check --fix --quiet $FILTERED_FILES || true

# Format to the line-length configured in pyproject.toml (previously black
# plus an autopep8 E501 pass plus a second black pass).
echo ""
echo "Formatting with ruff..."
# shellcheck disable=SC2086
ruff format --quiet $FILTERED_FILES || true

# Stage the modified files so pylint checks the cleaned versions.
# Only stage files that were already staged.
echo ""
echo "Staging cleaned files..."
for file in $FILTERED_FILES; do
    if git diff --cached --name-only --diff-filter=ACM | grep -q "^${file}$"; then
        git add "$file"
    fi
done

echo ""
echo "Code cleanup complete. Cleaned files have been re-staged."
