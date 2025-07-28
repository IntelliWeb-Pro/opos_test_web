# tests/views.py (Versión actualizada)

from rest_framework import viewsets, permissions
from rest_framework.decorators import action # <-- AÑADE ESTA LÍNEA
from rest_framework.response import Response # <-- AÑADE ESTA LÍNEA
from .models import Oposicion, Tema, Pregunta
from .serializers import OposicionSerializer, TemaSerializer, PreguntaSimpleSerializer, PreguntaDetalladaSerializer
import random

# ... (OposicionViewSet y TemaViewSet no cambian)
class OposicionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Oposicion.objects.all()
    serializer_class = OposicionSerializer
    permission_classes = [permissions.AllowAny]

class TemaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [permissions.AllowAny]

class PreguntaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Pregunta.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return PreguntaSimpleSerializer
        # Para la acción 'retrieve' (una sola pregunta) o nuestra nueva acción 'corregir'
        return PreguntaDetalladaSerializer

    def get_queryset(self):
        # ... (esta función no cambia)
        queryset = Pregunta.objects.all()
        tema_id = self.request.query_params.get('tema')
        if tema_id is not None:
            queryset = queryset.filter(tema__id=tema_id)
            all_questions = list(queryset)
            random.shuffle(all_questions)
            return all_questions[:20] # Aumentamos a 20 preguntas por test
        return queryset

    # --- NUEVA FUNCIÓN PARA LA CORRECCIÓN MASIVA ---
    @action(detail=False, methods=['post'])
    def corregir(self, request):
        ids_preguntas = request.data.get('ids', [])
        if not ids_preguntas:
            return Response({"error": "No se proporcionaron IDs de preguntas"}, status=400)

        preguntas_corregidas = Pregunta.objects.filter(id__in=ids_preguntas)
        serializer = self.get_serializer(preguntas_corregidas, many=True)
        return Response(serializer.data)

# tests/views.py (Añadir)

from .models import ResultadoTest # Añade ResultadoTest a la importación
from .serializers import ResultadoTestSerializer # Añade el nuevo serializer

class ResultadoTestViewSet(viewsets.ModelViewSet):
    queryset = ResultadoTest.objects.all()
    serializer_class = ResultadoTestSerializer
    permission_classes = [permissions.IsAuthenticated] # ¡Solo usuarios logueados!

    def get_queryset(self):
        # Hacemos que cada usuario solo pueda ver sus propios resultados
        return self.queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # Asignamos el usuario actual al resultado automáticamente al guardar
        serializer.save(usuario=self.request.user)

# tests/views.py (Añadir al final)

import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # ID del precio que creaste en el panel de Stripe
        price_id = 'price_1Rps29BX1J8TMJHDa5JBbY17' # <-- ¡¡Pega aquí tu ID de Precio!!

        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url='http://localhost:3000/pago-exitoso?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:3000/pago-cancelado',
                customer_email=request.user.email # Opcional: Rellena el email del usuario
            )
            return Response({'sessionId': checkout_session.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)