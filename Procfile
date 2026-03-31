web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --max-requests 1000 --max-requests-jitter 50 --log-level info --access-logfile - --error-logfile - --capture-output
worker: celery -A eko worker --loglevel=info --concurrency=2
beat: celery -A eko beat --loglevel=info
