"""
Django settings for giconfig project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

# Cargar variables del archivo .env
load_dotenv()

#api GI
API_GI = 'https://sistema.grupoimagensac.com.pe/api/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Lima' 
USE_TZ = True
USE_I18N = True

# Tamaño máximo de archivos en bytes (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB

# Tamaño máximo total de la solicitud
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Configuración para archivos media
MEDIA_URL = '/media/'  # Esto hace que los archivos media se sirvan desde la raíz
MEDIA_ROOT = BASE_DIR

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3s0-s19rqi$jb$0nm%#1vtx2+rcb&dz5e(7+$z*j(83y=5_n)%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG')

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://api2.grupoimagensac.com.pe',
    'http://api2.grupoimagensac.com.pe',
]

# PUSHER
PUSHER_APP_ID      = os.getenv('PUSHER_APP_ID')
PUSHER_KEY         = os.getenv('PUSHER_KEY')
PUSHER_SECRET      = os.getenv('PUSHER_SECRET')
PUSHER_CLUSTER     = os.getenv('PUSHER_CLUSTER')

# OPENAI
OPENAI_API_KEY      = os.getenv('OPENAI_API_KEY')

# Configuración de Wasabi
WASABI_ACCESS_KEY_ID = os.getenv('WAS_ACCESS_KEY_ID')
WASABI_SECRET_ACCESS_KEY = os.getenv('WAS_SECRET_ACCESS_KEY')
WASABI_DEFAULT_REGION = os.getenv('WAS_DEFAULT_REGION')
WASABI_BUCKET = os.getenv('WAS_BUCKET')
WASABI_ENDPOINT_URL = os.getenv('WAS_URL')

# Configuración de AWS/S3 para Django-storages
AWS_ACCESS_KEY_ID = WASABI_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = WASABI_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = WASABI_BUCKET
AWS_S3_ENDPOINT_URL = WASABI_ENDPOINT_URL
AWS_S3_REGION_NAME = WASABI_DEFAULT_REGION
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_S3_FILE_OVERWRITE = False

# Configuración de almacenamiento personalizado
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Si quieres usar un storage personalizado
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        'OPTIONS': {
            'access_key': WASABI_ACCESS_KEY_ID,
            'secret_key': WASABI_SECRET_ACCESS_KEY,
            'bucket_name': WASABI_BUCKET,
            'region_name': WASABI_DEFAULT_REGION,
            'endpoint_url': WASABI_ENDPOINT_URL,
        }
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'apps',
    'apps.users',
    'apps.redes_sociales',
    'apps.messenger',
    'apps.whatsapp',
    'apps.chat_interno',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

# Configuración de Celery
CELERY_BROKER_URL = 'redis://redis:6379/0'  # o usar RabbitMQ
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Lima'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Orígenes permitidos para las peticiones cross-site:
CORS_ALLOW_ALL_ORIGINS = True

# Métodos HTTP permitidos en CORS (incluye OPTIONS por defecto):
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

# Headers que puede enviar el cliente
CORS_ALLOW_HEADERS = list(default_headers) + [
    'userid',
    'idcompany',
    'content-type',
    'accept',
    'accept-encoding',
    'authorization',
    'x-requested-with',
]

# Configuración para manejar archivos grandes
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 horas

ROOT_URLCONF = 'giconfig.urls'

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

WSGI_APPLICATION = 'giconfig.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': '5432',      
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
