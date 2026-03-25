#!/bin/bash
set -e

echo "Waiting for database..."
python << 'END'
import sys
import time
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UPM_Project.settings")
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

echo "Making migrations..."
python manage.py makemigrations core_upm --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Setting up roles..."
python manage.py setup_roles

echo "Creating admin account (if not exists)..."
if [ -z "${ADMIN_PASSWORD}" ]; then
    echo "ERROR: ADMIN_PASSWORD is not set in environment."
    exit 1
fi

python manage.py create_admin --username "${ADMIN_USERNAME:-admin}" --email "${ADMIN_EMAIL:-admin@upm.edu}" --password "${ADMIN_PASSWORD}" --fullname "${ADMIN_FULLNAME:-System Admin}" || echo "Admin already exists - skipped."

exec gunicorn UPM_Project.wsgi:application --bind 0.0.0.0:8000
