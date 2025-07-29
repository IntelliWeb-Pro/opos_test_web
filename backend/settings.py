# Al final de backend/settings.py

# ==============================================================================
# --- CONFIGURACIONES DE NUESTRO PROYECTO ---
# ==============================================================================

# --- CORS y CSRF (Permisos para el Frontend) ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://opos-test-frontend.vercel.app",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://opos-test-frontend.vercel.app",
]

# --- DJANGO REST FRAMEWORK ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# --- DJ-REST-AUTH Y ALLAUTH (Configuración Completa) ---
# CORRECCIÓN: Le decimos que use nuestro nuevo serializer personalizado
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': False,
    'USER_DETAILS_SERIALIZER': 'dj_rest_auth.serializers.UserDetailsSerializer',
    'REGISTER_SERIALIZER': 'tests.serializers.CustomRegisterSerializer', # <-- CAMBIO CLAVE
    'SESSION_LOGIN': False,
}
    
AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
    
# CORRECCIÓN: Volvemos a hacer el username obligatorio, pero mantenemos el login con email
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True # <-- CAMBIO CLAVE
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username' # <-- CAMBIO CLAVE
ACCOUNT_EMAIL_VERIFICATION = 'none'
    
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- CLAVES DE STRIPE (leídas de forma segura de variables de entorno) ---
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
