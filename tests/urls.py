from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OposicionViewSet,
    TemaViewSet,
    PreguntaViewSet,
    ResultadoTestViewSet,
    EstadisticasUsuarioView,
    CreateCheckoutSessionView,
    StripeWebhookView
)

# El router crea automáticamente las URLs para Oposiciones, Temas, etc.
router = DefaultRouter()
router.register(r'oposiciones', OposicionViewSet, basename='oposicion')
router.register(r'temas', TemaViewSet, basename='tema')
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'resultados', ResultadoTestViewSet, basename='resultado')

# Juntamos todas las URLs de nuestra aplicación aquí
urlpatterns = [
    # Incluye las URLs generadas por el router (/oposiciones, /temas, etc.)
    path('', include(router.urls)),
    
    # Añadimos las URLs específicas que no son del router
    path('estadisticas/', EstadisticasUsuarioView.as_view(), name='estadisticas-usuario'),
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
