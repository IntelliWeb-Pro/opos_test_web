from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de Autenticación
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # Todas las demás rutas de nuestra aplicación (oposiciones, temas, pagos, etc.)
    # se gestionarán en el archivo urls.py de la app 'tests'
    path('api/', include('tests.urls')),
]
