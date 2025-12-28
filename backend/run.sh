#!/bin/bash

# Manus AI Backend Startup Script - FAST MODE for Cloud Run
# DBs will be initialized AFTER port binding (in lifespan)

echo "==========================================="
echo "🚀 Manus AI Backend - FAST START"
echo "==========================================="
echo "📋 Configuration:"
echo "   PORT: ${PORT:-8000}"
echo "   MONGODB_URI: ${MONGODB_URI:0:30}..."
echo "   REDIS_HOST: ${REDIS_HOST}"
echo "   LOG_LEVEL: ${LOG_LEVEL:-INFO}"
echo ""
echo "⚡ Starting FastAPI (DBs will initialize in background)..."
echo "==========================================="

# Convert LOG_LEVEL to lowercase for uvicorn
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# Start uvicorn immediately - no pre-checks!
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --timeout-graceful-shutdown 5 \
    --log-level ${LOG_LEVEL_LOWER}