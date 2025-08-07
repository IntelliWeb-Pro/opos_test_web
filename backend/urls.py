from django.contrib import admin
from django.urls import path, include

# --- PRUEBA DE CARGA ---
# Si ves este mensaje en los logs de arranque de Render, significa que este archivo se está ejecutando.
print("--- URLS.PY: VERSIÓN CON DIAGNÓSTICO DE ALLAUTH CARGADA ---")

# --- Vistas importadas desde la app 'tests' ---
from tests.views import (
    CustomRegisterView,
    VerificarCuentaView,
    CreateCheckoutSessionView, 
    StripeWebhookView, 
    EstadisticasUsuarioView, 
    RankingSemanalView,
    AnalisisRefuerzoView,
    ContactoView,
    CustomPasswordResetView 
)

# Forzamos la importación del admin para que Django lo registre al arrancar.
import tests.admin

urlpatterns = [
    # --- Rutas de Administración y Autenticación ---
    path('admin/', admin.site.urls),
    path('api/auth/registration/', CustomRegisterView.as_view(), name='custom_register'),
    path('api/auth/verify/', VerificarCuentaView.as_view(), name='verify_account'),
    
    # --- RUTA DE DIAGNÓSTICO AÑADIDA ---
    # Esta línea intercepta la petición de reseteo y la envía a nuestra vista personalizada.
    path('api/auth/password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    
    # Incluimos el resto de URLs de dj-rest-auth (login, logout, etc.)
    path('api/auth/', include('dj_rest_auth.urls')),

    # --- LÍNEA AÑADIDA ---
    # Incluimos las URLs de allauth. Esto proporciona la URL 'password_reset_confirm'
    # que dj-rest-auth necesita para generar el enlace del email.
    path('accounts/', include('allauth.urls')),

    # --- Rutas específicas de la API ---
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/ranking/', RankingSemanalView.as_view(), name='ranking-semanal'),
    path('api/refuerzo/', AnalisisRefuerzoView.as_view(), name='analisis-refuerzo'),
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('api/contacto/', ContactoView.as_view(), name='contacto'),
    
    # --- RUTA GENERAL PARA EL RESTO DE LA API (ViewSets) ---
    path('api/', include('tests.urls')),
]
