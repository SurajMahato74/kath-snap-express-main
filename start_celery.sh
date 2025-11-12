#!/bin/bash

# Script to start Celery workers and beat scheduler for the calling system
# Usage: ./start_celery.sh [dev|prod]

MODE=${1:-dev}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DJANGO_SETTINGS_MODULE="ezeyway.settings"

echo "🚀 Starting Celery for Call System"
echo "Mode: $MODE"
echo "Project Directory: $PROJECT_DIR"

# Navigate to Django project directory
cd "$PROJECT_DIR/backend/ezeyway"

# Set environment variables
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH="$PROJECT_DIR/backend:$PYTHONPATH"

if [ "$MODE" = "dev" ]; then
    echo "🛠️  Starting Celery Worker (Development Mode)"
    celery -A ezeyway worker --loglevel=info --concurrency=2 &
    WORKER_PID=$!
    
    echo "📅 Starting Celery Beat (Development Mode)"
    celery -A ezeyway beat --loglevel=info &
    BEAT_PID=$!
    
    echo "📊 Starting Celery Flower (Development Mode - Optional)"
    celery -A ezeyway flower &
    FLOWER_PID=$!
    
else
    echo "🏭 Starting Celery Worker (Production Mode)"
    celery -A ezeyway worker --loglevel=warning --concurrency=4 --max-tasks-per-child=1000 &
    WORKER_PID=$!
    
    echo "📅 Starting Celery Beat (Production Mode)"
    celery -A ezeyway beat --loglevel=warning &
    BEAT_PID=$!
    
    echo "📊 Starting Celery Flower (Production Mode)"
    celery -A ezeyway flower --port=5555 &
    FLOWER_PID=$!
fi

# Save PIDs for cleanup
echo "$WORKER_PID" > /tmp/celery_worker.pid
echo "$BEAT_PID" > /tmp/celery_beat.pid
echo "$FLOWER_PID" > /tmp/celery_flower.pid

echo "✅ Celery Started Successfully!"
echo "   - Worker PID: $WORKER_PID"
echo "   - Beat PID: $BEAT_PID"
echo "   - Flower PID: $FLOWER_PID"
echo ""
echo "📋 Available Celery Tasks for Call System:"
echo "   - cleanup_stale_calls (runs every 2 minutes)"
echo "   - cleanup_ended_calls (runs every 30 minutes)"
echo "   - generate_call_analytics (runs every hour)"
echo "   - cleanup_call_history (runs daily)"
echo "   - send_periodic_health_check (runs every 5 minutes)"
echo "   - send_realtime_call_updates (runs every 30 seconds)"
echo "   - cleanup_orphaned_websockets (runs every 10 minutes)"
echo ""
echo "🌐 Flower Monitor (if started): http://localhost:5555"
echo ""
echo "📝 To stop all Celery processes:"
echo "   ./stop_celery.sh"

# Keep script running
wait