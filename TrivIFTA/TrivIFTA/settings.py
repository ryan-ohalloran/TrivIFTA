"""
Django settings for TrivIFTA project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv
import os
from celery.schedules import crontab

# Set Geotab API credentials from the .env file 
load_dotenv()
MYGEOTAB_USERNAME = os.environ.get('MYGEOTAB_USERNAME')
MYGEOTAB_PASSWORD = os.environ.get('MYGEOTAB_PASSWORD')
MYGEOTAB_DATABASE = os.environ.get('MYGEOTAB_DATABASE')
FTP_HOST          = os.environ.get('FTP_HOST')
FTP_USERNAME      = os.environ.get('FTP_USERNAME')
FTP_KEY           = os.environ.get('FTP_KEY')
FERNET_KEY        = os.environ.get('FERNET_KEY')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

EMAIL_BACKEND     = 'django.core.mail.backends.smtp.EmailBackend'

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Celery beat settings
'''
Commands to run the celery worker and beat:
nohup celery -A TrivIFTA worker --loglevel=info -c 3 &
nohup celery -A TrivIFTA beat --loglevel=info &

Note: the -c 3 flag in the first command specifies the number of concurrent processes to run.
'''

CELERY_BEAT_SCHEDULE = {
    'run_daily_job': {
        'task': 'daily_compliance_job.tasks.run_daily_job_task',
        'schedule': crontab(hour=12, minute=0), # scheduled to run at 12:00 PM every day
    },
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Set timezone
TIME_ZONE = 'America/Chicago'
USE_TZ = True


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "daily_compliance_job",
    'django_celery_beat',
    'rest_framework',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware", # CORS middleware
    "django.middleware.common.CommonMiddleware", # CORS middleware
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://192.168.4.32",
    "http://127.0.0.1:8000"
]

ROOT_URLCONF = "TrivIFTA.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "TrivIFTA.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configure logging for the project
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',  # Path to the log file
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'run_daily_job': { 
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'root': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}
