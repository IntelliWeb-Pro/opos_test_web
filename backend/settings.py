# backend/settings.py

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-%9&dz2)ae_#jate7a+*tri=6ahq-1vwp3!nvx58qdp!mx7(n^*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# --- APLICACIONES ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps de terceros
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth.registration',
    # Nuestras apps
    'tests',
]

SITE_ID = 1

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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


# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- VALIDACIÓN DE CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True


# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = 'static/'

# --- CLAVE PRIMARIA POR DEFECTO ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# --- CONFIGURACIONES DE NUESTRO PROYECTO ---
# ==============================================================================

# --- CORS (Permisos para el Frontend) ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# --- DJANGO REST FRAMEWORK ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# --- DJ-REST-AUTH Y ALLAUTH ---
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'opos-test-auth',
    'JWT_AUTH_REFRESH_COOKIE': 'opos-test-refresh-token',
    'REGISTER_SERIALIZER': 'dj_rest_auth.registration.serializers.RegisterSerializer',
}

# Línea CLAVE que faltaba: Le dice a Django que use el sistema de autenticación de allauth.
AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Configuración de Allauth para que no pida verificación de email y funcione bien con la API
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email' # Permite login con usuario o email
ACCOUNT_EMAIL_REQUIRED = True

# Le decimos a Django que "imprima" los emails en la consola en lugar de enviarlos
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Al final de backend/settings.py

# ==============================================================================
# --- CONFIGURACIONES DE NUESTRO PROYECTO ---
# ==============================================================================

# --- CORS (Permisos para el Frontend) ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# --- DJANGO REST FRAMEWORK ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Usamos la autenticación de simplejwt
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# --- DJ-REST-AUTH ---
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': False, # Importante para que el frontend pueda leer el token
    'USER_DETAILS_SERIALIZER': 'dj_rest_auth.serializers.UserDetailsSerializer',
}

# --- DJANGO-ALLAUTH ---
# Línea CLAVE: Le dice a Django que use el sistema de autenticación de allauth.
AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# Configuración de Allauth para un sistema basado en email
ACCOUNT_AUTHENTICATION_METHOD = 'email'       # Login con email
ACCOUNT_EMAIL_REQUIRED = True                 # El email es obligatorio
ACCOUNT_UNIQUE_EMAIL = True                   # Cada email debe ser único
ACCOUNT_USERNAME_REQUIRED = False             # No pedimos un nombre de usuario al registrarse
ACCOUNT_USER_MODEL_USERNAME_FIELD = None      # Le decimos que no hay campo de username en el modelo
ACCOUNT_EMAIL_VERIFICATION = 'none'           # No pedimos verificación de email

# Le decimos a Django que "imprima" los emails en la consola en lugar de enviarlos
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Al final de backend/settings.py

# --- CLAVES DE STRIPE ---
STRIPE_PUBLISHABLE_KEY = 'pk_live_51RprfeBX1J8TMJHD47LveYeuejEjOauTcAAvnIv8fKK8prkSMrLbEllbCxjyGMhKu4S6143dhXLV7Ak5AO2Pklpz0048tPcIz4'
STRIPE_SECRET_KEY = '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'