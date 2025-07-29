from django.contrib import admin
from django.urls import path, include
from tests.views import CreateCheckoutSessionView, StripeWebhookView, EstadisticasUsuarioView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- RUTAS ESPECÍFICAS DE LA API ---
    # Estas deben ir ANTES de la ruta general 'api/'
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # --- RUTA GENERAL DE LA API ---
    # Esta va al final de las rutas /api/ para que no capture las anteriores
    path('api/', include('tests.urls')),
]
