from django.contrib import admin
from django.urls import path, include
from dj_rest_auth.views import PasswordResetConfirmView # <-- Importamos la vista que falta

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
    CustomPasswordResetView,
    DemoQuestionsView
)

# Forzamos la importación del admin para que Django lo registre al arrancar.
import tests.admin

urlpatterns = [
    # --- Rutas de Administración y Autenticación ---
    path('admin/', admin.site.urls),
    path('api/auth/registration/', CustomRegisterView.as_view(), name='custom_register'),
    path('api/auth/verify/', VerificarCuentaView.as_view(), name='verify_account'),
    
    # --- RUTA DE DIAGNÓSTICO AÑADIDA ---
    path('api/auth/password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    
    # --- LÍNEA AÑADIDA ---
    # Añadimos explícitamente la URL que dj-rest-auth busca con el nombre 'password_reset_confirm'
    path('api/auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Incluimos el resto de URLs de dj-rest-auth (login, logout, etc.)
    path('api/auth/', include('dj_rest_auth.urls')),

    # Incluimos las URLs de allauth para otras funcionalidades
    path('accounts/', include('allauth.urls')),

    # --- Rutas específicas de la API ---
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/ranking/', RankingSemanalView.as_view(), name='ranking-semanal'),
    path('api/refuerzo/', AnalisisRefuerzoView.as_view(), name='analisis-refuerzo'),
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('api/contacto/', ContactoView.as_view(), name='contacto'),
    path('api/demo-questions/', DemoQuestionsView.as_view(), name='demo-questions'),

    
    # --- RUTA GENERAL PARA EL RESTO DE LA API (ViewSets) ---
    path('api/', include('tests.urls')),
]
