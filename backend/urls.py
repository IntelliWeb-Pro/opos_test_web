from django.contrib import admin
from django.urls import path, include
from tests.views import CreateCheckoutSessionView, StripeWebhookView, EstadisticasUsuarioView

# --- NUEVO: Creamos un conjunto de URLs para nuestra API ---
api_urlpatterns = [
    path('', include('tests.urls')), # Incluye /oposiciones, /temas, /preguntas, etc.
    path('estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- RUTAS DE AUTENTICACIÓN ---
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # --- RUTAS DE PAGOS ---
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # --- RUTA GENERAL PARA NUESTRA API (v1) ---
    # Todas las rutas de la aplicación (oposiciones, temas, etc.) estarán bajo /api/v1/
    path('api/v1/', include(api_urlpatterns)),
]
