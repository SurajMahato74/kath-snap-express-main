#!/bin/bash

# Script to stop all Celery workers and services
# Usage: ./stop_celery.sh

echo "🛑 Stopping Celery Services..."

# Stop Celery Worker
if [ -f /tmp/celery_worker.pid ]; then
    WORKER_PID=$(cat /tmp/celery_worker.pid)
    if ps -p $WORKER_PID > /dev/null; then
        echo "🛑 Stopping Celery Worker (PID: $WORKER_PID)"
        kill $WORKER_PID
        rm /tmp/celery_worker.pid
    else
        echo "⚠️  Celery Worker process not found"
        rm -f /tmp/celery_worker.pid
    fi
fi

# Stop Celery Beat
if [ -f /tmp/celery_beat.pid ]; then
    BEAT_PID=$(cat /tmp/celery_beat.pid)
    if ps -p $BEAT_PID > /dev/null; then
        echo "🛑 Stopping Celery Beat (PID: $BEAT_PID)"
        kill $BEAT_PID
        rm /tmp/celery_beat.pid
    else
        echo "⚠️  Celery Beat process not found"
        rm -f /tmp/celery_beat.pid
    fi
fi

# Stop Celery Flower
if [ -f /tmp/celery_flower.pid ]; then
    FLOWER_PID=$(cat /tmp/celery_flower.pid)
    if ps -p $FLOWER_PID > /dev/null; then
        echo "🛑 Stopping Celery Flower (PID: $FLOWER_PID)"
        kill $FLOWER_PID
        rm /tmp/celery_flower.pid
    else
        echo "⚠️  Celery Flower process not found"
        rm -f /tmp/celery_flower.pid
    fi
fi

# Force kill any remaining celery processes
echo "🔍 Checking for any remaining Celery processes..."
CELERY_PROCESSES=$(ps aux | grep celery | grep -v grep | awk '{print $2}')
if [ ! -z "$CELERY_PROCESSES" ]; then
    echo "⚠️  Found remaining Celery processes: $CELERY_PROCESSES"
    echo "🔧 Force killing remaining processes..."
    kill -9 $CELERY_PROCESSES 2>/dev/null
else
    echo "✅ No remaining Celery processes found"
fi

# Clean up Redis (optional - be careful in production!)
echo "🧹 Cleaning up Redis connections..."
redis-cli FLUSHALL 2>/dev/null || echo "⚠️  Could not connect to Redis (might not be running)"

echo ""
echo "✅ Celery Services Stopped Successfully!"
echo ""
echo "📋 Services stopped:"
echo "   - Celery Worker"
echo "   - Celery Beat (Scheduler)"
echo "   - Celery Flower (Monitor)"
echo ""
echo "🛠️  To restart:"
echo "   ./start_celery.sh"