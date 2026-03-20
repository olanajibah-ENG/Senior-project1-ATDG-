#!/bin/bash
set -e

echo "Waiting for MongoDB..."
/usr/local/bin/python << END
import sys
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

mongo_host = os.environ.get("MONGO_HOST", "mongodb")
mongo_port = int(os.environ.get("MONGO_PORT", 27017))
max_attempts = 15
attempt = 0

while attempt < max_attempts:
    try:
        client = MongoClient(host=mongo_host, port=mongo_port, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("MongoDB is ready!")
        sys.exit(0)
    except ConnectionFailure:
        attempt += 1
        print(f"MongoDB is unavailable - waiting... ({attempt}/{max_attempts})")
        time.sleep(2)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

print("MongoDB connection failed after maximum attempts")
sys.exit(1)
END

echo "Running Django checks and migrations..."
python manage.py makemigrations core_ai || true
python manage.py migrate
echo "Collecting static files..."
python manage.py collectstatic --no-input

if [[ "$*" == *"celery"* ]]; then
    echo "Starting Celery Worker..."
    exec "$@"
else
    echo "Starting Django Web Server..."
    export DJANGO_SETTINGS_MODULE=Ai_project.settings
    exec gunicorn Ai_project.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --keep-alive 75
fi