# backend/settings.py (VERSIÓN FINAL PARA PRODUCCIÓN)

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Lee la SECRET_KEY de una variable de entorno. ¡Más seguro!
SECRET_KEY = os.environ.get('SECRET_KEY', 'una_clave_secreta_por_defecto_para_desarrollo')

# DEBUG se desactiva automáticamente en producción (en Render)
DEBUG = 'RENDER' not in os.environ

# Añade aquí la URL de tu futuro servicio de Render
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # <--- AÑADIR WHITENOISE
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth.registration',
    'tests',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- AÑADIR WHITENOISE
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# --- BASE DE DATOS (Configuración dinámica para Render) ---
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURACIONES DE NUESTRO PROYECTO ---

# Añade aquí la URL de tu frontend en Vercel cuando la tengas
# backend/settings.py

# --- CORS y CSRF (Permisos para el Frontend) ---
# Leemos la URL del frontend de una variable de entorno para producción
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    FRONTEND_URL,
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    FRONTEND_URL,
]

REST_FRAMEWORK = { 'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',) }
REST_AUTH = { 'USE_JWT': True, 'JWT_AUTH_HTTPONLY': False }
AUTHENTICATION_BACKENDS = [ 'allauth.account.auth_backends.AuthenticationBackend', 'django.contrib.auth.backends.ModelBackend',]
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- CLAVES DE STRIPE (leídas de variables de entorno) ---
# --- CLAVES DE STRIPE ---
STRIPE_PUBLISHABLE_KEY = 'pk_live_51RprfeBX1J8TMJHD47LveYeuejEjOauTcAAvnIv8fKK8prkSMrLbEllbCxjyGMhKu4S6143dhXLV7Ak5AO2Pklpz0048tPcIz4'
STRIPE_SECRET_KEY = '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'