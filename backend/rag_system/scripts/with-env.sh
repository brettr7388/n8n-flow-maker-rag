#!/bin/bash
# Helper script to run Python commands with .env loaded

# Load .env file
if [ -f "../../../.env" ]; then
    export $(cat ../../../.env | grep -v '^#' | xargs)
    echo "✓ Loaded environment variables from .env"
elif [ -f "../../.env" ]; then
    export $(cat ../../.env | grep -v '^#' | xargs)
    echo "✓ Loaded environment variables from .env"
else
    echo "⚠ No .env file found, using existing environment"
fi

# Run the provided command
"$@"


