# tests/urls.py (Versión Corregida)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Asegúrate de que ResultadoTestViewSet está importado en esta línea
from .views import OposicionViewSet, TemaViewSet, PreguntaViewSet, ResultadoTestViewSet

router = DefaultRouter()
router.register(r'oposiciones', OposicionViewSet, basename='oposicion')
router.register(r'temas', TemaViewSet, basename='tema')
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'resultados', ResultadoTestViewSet, basename='resultado') # Ahora esta línea funcionará

urlpatterns = [
    path('', include(router.urls)),
]