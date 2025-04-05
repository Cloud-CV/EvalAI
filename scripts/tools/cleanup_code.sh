#!/bin/bash

# Clean unused imports (W0611, W0614) and variables (W0612)
echo "Removing unused imports and variables with autoflake..."
find . -type f -name "*.py" \
  -not -path "./env/*" \
  -not -path "./docs/*" \
  -exec autoflake --in-place \
    --remove-duplicate-keys \
    --remove-unused-variables \
    --expand-star-imports \
    --remove-all-unused-imports {} +

# Fix long lines (C0301): max 79 characters
echo "Fixing formatting and line lengths with autopep8..."
find . -type f -name "*.py" \
  -not -path "./env/*" \
  -not -path "./docs/*" \
  -exec autopep8 --in-place \
    --aggressive --aggressive \
    --max-line-length=79 {} +

echo "Code cleanup complete. Review changes before committing."