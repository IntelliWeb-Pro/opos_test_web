from django.contrib import admin
from django.urls import path, include
from tests.views import CreateCheckoutSessionView, StripeWebhookView, EstadisticasUsuarioView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- CORRECCIÓN: La ruta específica va PRIMERO ---
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    
    # La ruta general que incluye el resto de la API va DESPUÉS
    path('api/', include('tests.urls')),
    
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
