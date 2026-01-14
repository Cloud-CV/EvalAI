#!/bin/bash
set -e

# Cleanup function to kill Chrome processes
cleanup() {
    echo "Cleaning up Chrome processes..."
    pkill -f chrome || true
    pkill -f chromium || true
    pkill -f google-chrome || true
}

# Set up trap to cleanup on exit
trap cleanup EXIT INT TERM

# If a command is provided (e.g., via docker-compose run), execute it
if [ $# -gt 0 ]; then
    exec "$@"
fi

# If BUILD_ONLY is set, just build and exit
if [ "${BUILD_ONLY}" = "true" ]; then
    echo "Building frontend assets..."
    gulp dev
    echo "Build complete. Exiting."
    cleanup
    exit 0
fi

# Otherwise, run the development server (default behavior)
exec gulp dev:runserver
