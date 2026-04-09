
from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Try multiple possible .env locations for different environments
env_paths = [
    os.path.join(BASE_DIR.parent, '.env'),  # Local development
    '/app/.env',  # Docker container
    '.env'  # Current directory
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# قراءة DEBUG أولاً لتحديد البيئة
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# URLs للخدمات الأخرى (يمكن أن تكون عامة)
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://upm_api_gateway:80/api/analysis/codefiles/')
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification_django:8000')

# ===== SECURITY: API Keys and Secret Keys =====
# في التطوير: استخدم قيم افتراضية آمنة
# في الإنتاج: يجب تعيين المتغيرات في .env
if DEBUG:
    # Development environment - safe defaults
    AI_SERVICE_KEY = os.environ.get('AI_SERVICE_KEY', "dev-service-key-not-for-production")
    SECRET_KEY = os.environ.get('UPM_DJANGO_SECRET_KEY', 'dev-upm-secret-key-change-in-production')
else:
    # Production environment - must be set in .env
    AI_SERVICE_KEY = os.environ.get('AI_SERVICE_KEY')
    SECRET_KEY = os.environ.get('UPM_DJANGO_SECRET_KEY')
    
    # Validate that required keys are set
    if not AI_SERVICE_KEY:
        raise ValueError("❌ AI_SERVICE_KEY must be set in production environment")
    if not SECRET_KEY:
        raise ValueError("❌ UPM_DJANGO_SECRET_KEY must be set in production environment")

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,web,upm_backend,upm_api_gateway,nginx,upm_django_app').split(',')




INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core_upm', # التطبيق الأساسي
    'rest_framework', 
    'rest_framework_simplejwt',
    #'rest_framework.authtoken',
    'corsheaders',
    'drf_yasg',  # أضف هذا لـ Swagger
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core_upm.middleware.OnlineStatusMiddleware',
]

ROOT_URLCONF = 'UPM_Project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [

                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'UPM_Project.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'upm_mysql_db'),
        'USER': os.environ.get('MYSQL_USER', 'admin3'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD'),  # ✅ بدون default value
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': '3306',
        # (إضافة Charset لضمان دعم اللغة العربية)
        'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
        'CHARSET': 'utf8mb4',
    }
}

# Validate database password
if not DATABASES['default']['PASSWORD']:
    if DEBUG:
        DATABASES['default']['PASSWORD'] = 'dev_password'
        print("⚠️ WARNING: Using default development database password")
    else:
        raise ValueError("❌ MYSQL_PASSWORD must be set in production environment")

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}
      
  



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



STATIC_URL = '/static/upm/'
STATIC_ROOT= os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=365),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}


CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",  # For Nginx proxy
    "http://127.0.0.1",  # For Nginx proxy
    "http://localhost:80",  # Nginx port
    "http://127.0.0.1:80",  # Nginx port
    "http://upm_api_gateway",  # Docker service name
]

CORS_ALLOW_ALL_ORIGINS = True  # For development only

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",  # For Nginx proxy
    "http://127.0.0.1",  # For Nginx proxy
    "http://localhost:80",  # Nginx port
    "http://127.0.0.1:80",  # Nginx port
    "http://upm_api_gateway",  # Docker service name
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'core_upm': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,  # Allow child loggers to propagate
        },
        'core_upm.views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',  # Log 4xx and 5xx errors
            'propagate': False,
        },
    },
}

if DEBUG:
    # Development settings - more permissive
    CSRF_COOKIE_SECURE = False
    CSRF_USE_SESSIONS = False
    # Add additional development origins
    CSRF_TRUSTED_ORIGINS.extend([
        "http://localhost:80",  # Nginx port
        "http://127.0.0.1:80",  # Nginx port
    ])
else:
    # Production CSRF settings
    CSRF_COOKIE_SECURE = True
    CSRF_USE_SESSIONS = False
    # Add production trusted origins from environment
    additional_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
    if additional_origins:
        CSRF_TRUSTED_ORIGINS.extend(additional_origins.split(','))