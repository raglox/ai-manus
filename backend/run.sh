#!/bin/bash

# Manus AI Backend Startup Script with Health Checks
set -e

echo "=========================================="
echo "🚀 Starting Manus AI Backend"
echo "=========================================="

# Wait for dependencies (optional pre-check)
echo "📋 Configuration:"
echo "   PORT: ${PORT:-8000}"
echo "   MONGODB_URI: ${MONGODB_URI:0:30}..."
echo "   REDIS_HOST: ${REDIS_HOST}"
echo "   REDIS_PORT: ${REDIS_PORT}"
echo ""

# Optional: Run health check script before starting
if [ -f "/app/check_connections.py" ]; then
    echo "🔍 Running pre-startup health checks..."
    python /app/check_connections.py || echo "⚠️  Health check failed, but continuing..."
    echo ""
fi

echo "🎯 Starting FastAPI application..."
echo "=========================================="

# Start uvicorn with proper settings
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --timeout-graceful-shutdown 5 \
    --log-level info