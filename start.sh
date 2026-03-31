#!/bin/bash
# Railway Startup Script - Web service only
# Celery worker and beat should run as separate Railway services.

echo "════════════════════════════════════════════════════════════"
echo "🚀 E-KOLEK Railway Startup"
echo "════════════════════════════════════════════════════════════"

# Exit on error
set -e

# Run database migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn web server
echo "🌐 Starting Gunicorn web server..."
echo "════════════════════════════════════════════════════════════"

exec gunicorn eko.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output
