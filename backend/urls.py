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
    
    # --- RUTAS DE AUTENTICACIÓN ---
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # --- RUTAS ESPECÍFICAS (PAGOS, ESTADÍSTICAS) ---
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/ranking/', RankingSemanalView.as_view(), name='ranking-semanal'),
    path('api/refuerzo/', AnalisisRefuerzoView.as_view(), name='analisis-refuerzo'),
    # --- RUTA GENERAL PARA EL RESTO DE LA API ---
    # Incluye /oposiciones, /temas, etc. del archivo tests.urls
    path('api/', include('tests.urls')),
]
