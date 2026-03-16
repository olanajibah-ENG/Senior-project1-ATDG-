#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
python << 'END'
import sys
import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UPM_Project.settings')
django.setup()

from django.db import connection
from django.db.utils import OperationalError

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        connection.ensure_connection()
        print("Database is ready!")
        sys.exit(0)
    except OperationalError:
        attempt += 1
        print(f"Database is unavailable - waiting... ({attempt}/{max_attempts})")
        time.sleep(2)

print("Database connection failed after maximum attempts")
sys.exit(1)
END

echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
# python manage.py collectstatic --noinput

# Execute the main command
exec gunicorn UPM_Project.wsgi:application --bind 0.0.0.0:8000
