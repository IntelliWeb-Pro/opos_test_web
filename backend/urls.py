from django.contrib import admin
from django.urls import path, include
from tests.views import (
    CreateCheckoutSessionView, 
    StripeWebhookView, 
    EstadisticasUsuarioView, 
    RankingSemanalView,
    AnalisisRefuerzoView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- RUTAS ESPECÍFICAS DE LA API ---
    # Estas deben ir ANTES de la ruta general 'api/' para que se detecten correctamente.
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/ranking/', RankingSemanalView.as_view(), name='ranking-semanal'),
    path('api/refuerzo/', AnalisisRefuerzoView.as_view(), name='analisis-refuerzo'),
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('api/contacto/', ContactoView.as_view(), name='contacto'),
    
    # --- RUTA GENERAL PARA EL RESTO DE LA API ---
    # Esta va al final para que no "atrape" las rutas específicas de arriba.
    path('api/', include('tests.urls')),
]
