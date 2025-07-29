from django.contrib import admin
from django.urls import path, include
from tests.views import CreateCheckoutSessionView, StripeWebhookView, EstadisticasUsuarioView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- RUTAS ESPECÍFICAS DE LA API ---
    # Estas se comprueban primero para que no haya conflictos.
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('api/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # --- RUTA GENERAL DE LA API ---
    # Esta ruta captura el resto de peticiones como /api/oposiciones/, /api/temas/, etc.
    # y las envía a la app 'tests' para que las gestione.
    path('api/', include('tests.urls')),
]
