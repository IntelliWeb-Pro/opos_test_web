from django.contrib import admin
from django.urls import path, include

# --- Vistas importadas desde la app 'tests' ---
from tests.views import (
    CustomRegisterView,
    VerificarCuentaView,
    CreateCheckoutSessionView, 
    StripeWebhookView, 
    EstadisticasUsuarioView, 
    RankingSemanalView,
    AnalisisRefuerzoView, # <-- CORREGIDO: 'Refuerzo' en lugar de 'Refuero'
    ContactoView
)

# --- LÍNEA AÑADIDA ---
# Forzamos la importación del admin para que Django lo registre al arrancar.
import tests.admin

urlpatterns = [
    # --- Rutas de Administración y Autenticación ---
    path('admin/', admin.site.urls),
    path('api/auth/registration/', CustomRegisterView.as_view(), name='custom_register'),
    path('api/auth/verify/', VerificarCuentaView.as_view(), name='verify_account'),
    path('api/auth/', include('dj_rest_auth.urls')),

    # --- Rutas específicas de la API ---
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/ranking/', RankingSemanalView.as_view(), name='ranking-semanal'),
    path('api/refuerzo/', AnalisisRefuerzoView.as_view(), name='analisis-refuerzo'), # <-- CORREGIDO
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('api/contacto/', ContactoView.as_view(), name='contacto'),
    
    # --- RUTA GENERAL PARA EL RESTO DE LA API (ViewSets) ---
    # Esta va al final para que no "atrape" las rutas específicas de arriba.
    # Asumo que 'tests.urls' contiene el router para Oposicion, Tema, Pregunta, etc.
    path('api/', include('tests.urls')),
]
