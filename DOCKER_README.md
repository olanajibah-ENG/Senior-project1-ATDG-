# Docker Setup Guide

This guide explains how to run the UPM Project using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Quick Start

1. **Create environment file** (optional, defaults are provided):
   ```bash
   cp env.example .env
   ```
   Edit `.env` file if you need to change any settings.

2. **Build and start containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/swagger/
   - ReDoc: http://localhost:8000/redoc/
   - Admin Panel: http://localhost:8000/admin/

## Common Commands

### Start services in detached mode:
```bash
docker-compose up -d
```

### Stop services:
```bash
docker-compose down
```

### Stop and remove volumes (⚠️ deletes database data):
```bash
docker-compose down -v
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

### Run Django management commands:
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations manually
docker-compose exec web python manage.py migrate

# Access Django shell
docker-compose exec web python manage.py shell
```

### Rebuild after code changes:
```bash
docker-compose up --build
```

## Services

### Web (Django Application)
- **Container**: `upm_django_app`
- **Port**: 8000
- **Volumes**: Project code is mounted for live development

### Database (MySQL)
- **Container**: `upm_mysql_db`
- **Port**: 3307
- **Volume**: `mysql_data` (persistent storage)
- **Database**: `upm_mysql_db`
- **User**: `admin3`
- **Password**: `admin3` (change in `.env`)

## Environment Variables

Key environment variables (set in `.env` file):

- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_HOST`: Database host (use `db` for Docker)
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `MYSQL_ROOT_PASSWORD`: MySQL root password

## Database Access

To connect to MySQL from outside Docker:
```bash
mysql -h localhost -P 3306 -u admin3 -p
# Password: admin3
```

Or using Docker:
```bash
docker-compose exec db mysql -u admin3 -p
```

## Troubleshooting

### Database connection errors:
- Wait for the database to be healthy (entrypoint script handles this)
- Check database credentials in `.env`
- Verify `DB_HOST=db` in `.env`

### Port already in use:
- Change `DJANGO_PORT` or `MYSQL_PORT` in `.env`
- Or stop the service using the port

### Permission errors:
- Ensure `entrypoint.sh` has execute permissions (handled in Dockerfile)
- Check file ownership

### Reset everything:
```bash
docker-compose down -v
docker-compose up --build
```

## Production Considerations

⚠️ **This setup is for development only!** For production:

1. Set `DEBUG=False` in `.env`
2. Use a strong `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Use environment-specific database credentials
5. Set up proper static file serving
6. Use a production WSGI server (gunicorn/uwsgi)
7. Configure SSL/TLS
8. Set up proper backup strategy for database

