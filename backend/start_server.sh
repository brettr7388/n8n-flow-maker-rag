#!/bin/bash
# Start backend server with environment variables

# Load .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start uvicorn
echo "Starting n8n Flow Generator Backend..."
echo "Enhanced RAG Generator will be loaded..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
