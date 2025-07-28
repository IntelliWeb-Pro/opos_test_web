# backend/urls.py (Modificar)

from django.contrib import admin
from django.urls import path, include
from tests.views import CreateCheckoutSessionView # <-- IMPORTA LA NUEVA VISTA

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tests.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    # --- AÑADE ESTA LÍNEA ---
    path('api/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
]