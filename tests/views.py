import random
import stripe
from django.conf import settings
from django.db.models import Avg, ExpressionWrapper, FloatField
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Oposicion, Tema, Pregunta, ResultadoTest, Suscripcion
from .serializers import (
    OposicionSerializer, TemaSerializer, PreguntaSimpleSerializer,
    PreguntaDetalladaSerializer, ResultadoTestSerializer, ResultadoTestCreateSerializer
)

# --- VISTAS DE LA API PRINCIPAL (ROUTER) ---

class OposicionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows oposiciones to be viewed.
    """
    queryset = Oposicion.objects.all()
    serializer_class = OposicionSerializer
    permission_classes = [permissions.AllowAny]

class TemaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows temas to be viewed.
    """
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [permissions.AllowAny]

class PreguntaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for preguntas. Allows filtering by tema.
    """
    permission_classes = [permissions.AllowAny]
    queryset = Pregunta.objects.all()

    def get_serializer_class(self):
        # Use a simple serializer for lists (for the test) and a detailed one for single items (for correction)
        if self.action == 'list':
            return PreguntaSimpleSerializer
        return PreguntaDetalladaSerializer

    def get_queryset(self):
        queryset = Pregunta.objects.all()
        tema_id = self.request.query_params.get('tema')
        if tema_id is not None:
            queryset = queryset.filter(tema__id=tema_id)
            all_questions = list(queryset)
            random.shuffle(all_questions)
            return all_questions[:20] # Limit test to 20 questions
        return queryset
    
    @action(detail=False, methods=['post'])
    def corregir(self, request):
        ids_preguntas = request.data.get('ids', [])
        if not ids_preguntas:
            return Response({"error": "No se proporcionaron IDs de preguntas"}, status=400)
        
        preguntas_corregidas = Pregunta.objects.filter(id__in=ids_preguntas)
        serializer = self.get_serializer(preguntas_corregidas, many=True)
        return Response(serializer.data)

class ResultadoTestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and creating test results for the logged-in user.
    """
    queryset = ResultadoTest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # Use a different serializer for creating vs reading results
        if self.action == 'create':
            return ResultadoTestCreateSerializer
        return ResultadoTestSerializer

    def get_queryset(self):
        # Users can only see their own results
        return self.queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the logged-in user when a result is created
        serializer.save(usuario=self.request.user)


# --- VISTAS ESPECÍFICAS (NO ROUTER) ---

class EstadisticasUsuarioView(APIView):
    """
    API endpoint for user statistics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        usuario = request.user
        resultados = ResultadoTest.objects.filter(usuario=usuario)
        if not resultados.exists():
            return Response({"message": "No hay resultados de tests para este usuario."}, status=status.HTTP_200_OK)
        
        media_general = resultados.aggregate(media=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField()))['media']
        stats_oposicion = resultados.values('tema__oposicion__nombre').annotate(media_oposicion=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_oposicion')
        stats_tema = resultados.values('tema__nombre', 'tema__oposicion__nombre').annotate(media_tema=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_tema')
        
        data = {
            "media_general": round(media_general, 2) if media_general is not None else 0,
            "stats_por_oposicion": [{"oposicion": item['tema__oposicion__nombre'], "media": round(item['media_oposicion'], 2)} for item in stats_oposicion],
            "stats_por_tema": [{"oposicion": item['tema__oposicion__nombre'],"tema": item['tema__nombre'],"media": round(item['media_tema'], 2)} for item in stats_tema[:10]]
        }
        return Response(data)

# --- VISTAS DE PAGOS (STRIPE) ---

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    """
    API endpoint to create a Stripe Checkout session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # REMEMBER TO REPLACE THIS WITH YOUR REAL PRICE ID FROM THE STRIPE DASHBOARD
        price_id = 'price_1PabcdeFGHIjklmnOPQRS' 
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url='https://opos-test-frontend.vercel.app/pago-exitoso?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://opos-test-frontend.vercel.app/pago-cancelado',
                customer_email=request.user.email
            )
            return Response({'sessionId': checkout_session.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StripeWebhookView(APIView):
    """
    API endpoint to handle incoming webhooks from Stripe.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=400)
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_email = session['customer_details']['email']
            User = get_user_model()
            try:
                user = User.objects.get(email=customer_email)
                suscripcion, created = Suscripcion.objects.get_or_create(usuario=user)
                suscripcion.stripe_customer_id = session.customer
                suscripcion.stripe_subscription_id = session.subscription
                suscripcion.activa = True
                suscripcion.save()
            except User.DoesNotExist:
                return Response(status=400)
        
        return Response(status=200)
