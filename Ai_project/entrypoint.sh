#!/bin/bash
set -e

# Wait for MongoDB to be ready (less strict than SQL, but good practice)
echo "Waiting for MongoDB..."
/usr/local/bin/python << END
import sys
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

mongo_host = os.environ.get('MONGO_HOST', 'mongodb')
mongo_port = int(os.environ.get('MONGO_PORT', 27017))
max_attempts = 15
attempt = 0

while attempt < max_attempts:
    try:
        client = MongoClient(host=mongo_host, port=mongo_port, serverSelectionTimeoutMS=5000)
        client.admin.command('ping') # Test connection
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
# Djongo لا يحتاج migrations بالمعنى التقليدي، لكن Django يتتبع النماذج
python manage.py makemigrations core_ai --noinput || true # لا يجب أن يفشل إذا لم يكن هناك تغيير
python manage.py migrate --noinput
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute the main command (e.g., runserver or celery worker)
# Check if this is a celery worker container
if [[ "$*" == *"celery"* ]]; then
    echo "Starting Celery Worker..."
    exec "$@"
else
    echo "Starting Django Web Server..."
    # Set Django settings module explicitly for Ai_project
    export DJANGO_SETTINGS_MODULE=Ai_project.settings
    exec gunicorn Ai_project.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --keep-alive 75
fi
