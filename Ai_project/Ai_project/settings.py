from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv  # 👈 أضف هذا السطر

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

# ===== SECURITY: API Keys and Secret Keys =====
# في التطوير: استخدم قيم افتراضية آمنة
# في الإنتاج: يجب تعيين المتغيرات في .env
if DEBUG:
    # Development environment - use free test key
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d")
    SERVICE_API_KEY = os.environ.get('AI_SERVICE_KEY', "test-service-key")
    SECRET_KEY = os.environ.get('AI_DJANGO_SECRET_KEY', 'django-insecure-test-key-for-development-only')
else:
    # Production environment - must be set in .env
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    SERVICE_API_KEY = os.environ.get('AI_SERVICE_KEY')
    SECRET_KEY = os.environ.get('AI_DJANGO_SECRET_KEY')
    
    # Validate that required keys are set
    if not OPENROUTER_API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY must be set in production environment")
    if not SERVICE_API_KEY:
        raise ValueError("❌ AI_SERVICE_KEY must be set in production environment")
    if not SECRET_KEY:
        raise ValueError("❌ AI_DJANGO_SECRET_KEY must be set in production environment")

# Notification Service URL
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification_django:8000') 

# دائماً استخدم ['*'] في التطوير لتجنب مشاكل Host
ALLOWED_HOSTS = ['*', 'ai_web', 'localhost', '127.0.0.1', '0.0.0.0', 'ai_django_app', '172.18.0.10', 'upm_api_gateway']

# Disable host validation to allow Docker service names with underscores
SILENCED_SYSTEM_CHECKS = ['security.W004']
    

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core_ai',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',

]


MIDDLEWARE = [
    'Ai_project.middleware.AllowAllHostsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # CommonMiddleware disabled — causes DisallowedHost for Docker service names with underscores
    # 'django.middleware.common.CommonMiddleware',
    # Disable CSRF for API requests
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Ai_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'Ai_project.wsgi.application'



DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3', 
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')  
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'ai_mongodb_db')


CODE_FILES_COLLECTION = 'code_files'
ANALYSIS_JOBS_COLLECTION = 'analysis_jobs'
ANALYSIS_RESULTS_COLLECTION = 'analysis_results'
AI_EXPLANATIONS_COLLECTION = 'ai_explanations'
AI_TASKS_COLLECTION = 'ai_tasks'
DOCUMENTATION_FILES_COLLECTION = 'documentation_files'
GENERATED_FILES_COLLECTION = 'generated_files'


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



STATIC_URL = '/static/ai/'
STATIC_ROOT= os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

ADMIN_URL = 'admin/'  # مسار admin الداخلي

USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

FORCE_SCRIPT_NAME = None
ADMIN_MEDIA_PREFIX = '/static/ai/admin/'

SESSION_COOKIE_NAME = 'ai_sessionid'
SESSION_COOKIE_AGE = 1209600  # أسبوعين
SESSION_COOKIE_SECURE = False  # False للـ HTTP
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CSRF_COOKIE_NAME = 'ai_csrftoken'
CSRF_COOKIE_SECURE = False  # False للـ HTTP
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
    'http://localhost:80',
    'http://127.0.0.1:80',
    'http://upm_api_gateway'
]
CSRF_USE_SESSIONS = False
CSRF_COOKIE_AGE = 31449600  # سنة واحدة

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1",
    "http://127.0.0.1:80",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
   'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework_simplejwt.authentication.JWTAuthentication', # إضافة هذا السطر
       'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
  ),
  'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', # يمكن تغييرها حسب الحاجة
    ),
}

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')  # localhost للتطوير، redis للـ Docker
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True


CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO', # أو DEBUG
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': { # هذا هو المهم لأخطاء 500
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'Ai_project.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'llm-cache',
        'TIMEOUT': 3600 * 24,  # 24 ساعة
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

LLM_RATE_LIMIT = {
    'MAX_REQUESTS_PER_DAY': 50,  # للحساب المجاني
    'CACHE_TIMEOUT': 3600 * 24,  # 24 ساعة
    'RETRY_AFTER_MINUTES': 60,   # انتظار ساعة بعد rate limit
}
