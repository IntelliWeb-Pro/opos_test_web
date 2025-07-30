import random
import stripe
from datetime import date, timedelta
from django.db.models import Sum
from django.conf import settings
from django.db.models import Avg, ExpressionWrapper, FloatField
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
import os # Importamos 'os' para leer variables de entorno

from .models import Oposicion, Tema, Pregunta, ResultadoTest, Suscripcion
from .serializers import (
    OposicionSerializer, TemaSerializer, PreguntaSimpleSerializer,
    PreguntaDetalladaSerializer, ResultadoTestSerializer, ResultadoTestCreateSerializer
)

# ... (El resto de las vistas no cambian) ...
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
        if self.action == 'list': return PreguntaSimpleSerializer
        return PreguntaDetalladaSerializer
    def get_queryset(self):
        queryset = Pregunta.objects.all()
        tema_id = self.request.query_params.get('tema')
        if tema_id is not None:
            queryset = queryset.filter(tema__id=tema_id)
            all_questions = list(queryset)
            random.shuffle(all_questions)
            return all_questions[:20]
        return queryset
    @action(detail=False, methods=['post'])
    def corregir(self, request):
        ids_preguntas = request.data.get('ids', [])
        if not ids_preguntas: return Response({"error": "No se proporcionaron IDs de preguntas"}, status=400)
        preguntas_corregidas = Pregunta.objects.filter(id__in=ids_preguntas)
        serializer = self.get_serializer(preguntas_corregidas, many=True)
        return Response(serializer.data)

class ResultadoTestViewSet(viewsets.ModelViewSet):
    queryset = ResultadoTest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_class(self):
        if self.action == 'create': return ResultadoTestCreateSerializer
        return ResultadoTestSerializer
    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class EstadisticasUsuarioView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        usuario = request.user
        resultados = ResultadoTest.objects.filter(usuario=usuario)
        if not resultados.exists(): return Response({"message": "No hay resultados de tests para este usuario."}, status=status.HTTP_200_OK)
        media_general = resultados.aggregate(media=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField()))['media']
        stats_oposicion = resultados.values('tema__oposicion__nombre').annotate(media_oposicion=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_oposicion')
        stats_tema = resultados.values('tema__nombre', 'tema__oposicion__nombre').annotate(media_tema=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_tema')
        data = {
            "media_general": round(media_general, 2) if media_general is not None else 0,
            "stats_por_oposicion": [{"oposicion": item['tema__oposicion__nombre'], "media": round(item['media_oposicion'], 2)} for item in stats_oposicion],
            "stats_por_tema": [{"oposicion": item['tema__oposicion__nombre'],"tema": item['tema__nombre'],"media": round(item['media_tema'], 2)} for item in stats_tema[:10]]
        }
        return Response(data)

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # --- DEPURACIÓN: Leemos el ID de la variable de entorno ---
        price_id = os.environ.get('STRIPE_PRICE_ID')
        
        # --- DEPURACIÓN: Imprimimos el valor en los logs de Render ---
        print(f"DEBUG: Intentando crear sesión de pago con Price ID: {price_id}")

        if not price_id:
            print("ERROR: La variable de entorno STRIPE_PRICE_ID no está configurada o está vacía.")
            return Response(
                {'error': 'La configuración de pagos en el servidor está incompleta.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
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
            # --- DEPURACIÓN: Imprimimos el error exacto de Stripe ---
            print(f"ERROR de Stripe: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StripeWebhookView(APIView):
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
class RankingSemanalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        resultados_semanales = ResultadoTest.objects.filter(fecha__gte=start_of_week)

        ranking_data = resultados_semanales.values('usuario__username').annotate(
            puntuacion_total=Sum('puntuacion'),
            preguntas_totales=Sum('total_preguntas')
        ).filter(preguntas_totales__gt=0)

        ranking_list = []
        for item in ranking_data:
            porcentaje = (item['puntuacion_total'] * 100.0) / item['preguntas_totales']
            ranking_list.append({
                'username': item['usuario__username'],
                'porcentaje_aciertos': round(porcentaje, 2)
            })
        
        ranking_list.sort(key=lambda x: x['porcentaje_aciertos'], reverse=True)

        # Buscamos la posición del usuario actual
        user_rank = None
        for i, user_data in enumerate(ranking_list):
            if user_data['username'] == request.user.username:
                user_rank = {
                    'rank': i + 1,
                    'username': user_data['username'],
                    'porcentaje_aciertos': user_data['porcentaje_aciertos']
                }
                break

        # Preparamos la respuesta final
        response_data = {
            'podium': ranking_list[:3],
            'user_rank': user_rank
        }
        
        return Response(response_data)
