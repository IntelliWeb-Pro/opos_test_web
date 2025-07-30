import random
import stripe
import os
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Avg, Sum, ExpressionWrapper, FloatField, F
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

# ... (OposicionViewSet, TemaViewSet, PreguntaViewSet, ResultadoTestViewSet no cambian)
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


# --- VISTA DE ESTADÍSTICAS (ACTUALIZADA CON PUNTOS DÉBILES) ---
class EstadisticasUsuarioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        usuario = request.user
        resultados = ResultadoTest.objects.filter(usuario=usuario)

        if not resultados.exists():
            return Response({"message": "No hay resultados de tests para este usuario."}, status=status.HTTP_200_OK)
        
        # ... (Cálculos de resumen y media general no cambian)
        resumen_total = resultados.aggregate(total_aciertos=Sum('puntuacion'), total_preguntas=Sum('total_preguntas'))
        total_aciertos = resumen_total['total_aciertos'] or 0
        total_preguntas_global = resumen_total['total_preguntas'] or 0
        total_fallos = total_preguntas_global - total_aciertos
        media_general = (total_aciertos * 100.0 / total_preguntas_global) if total_preguntas_global > 0 else 0

        stats_oposicion = resultados.values('tema__oposicion__nombre').annotate(
            media_oposicion=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())
        ).order_by('-media_oposicion')

        historico = resultados.order_by('fecha')[:15].annotate(
            media_test=ExpressionWrapper((F('puntuacion') * 100.0) / F('total_preguntas'), output_field=FloatField())
        )

        # --- NUEVO: CÁLCULO DE PUNTOS DÉBILES Y FUERTES ---
        stats_tema = resultados.values('tema__id', 'tema__nombre', 'tema__oposicion__nombre').annotate(
            media_tema=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())
        )
        
        puntos_fuertes = sorted([t for t in stats_tema if t['media_tema'] is not None], key=lambda x: x['media_tema'], reverse=True)[:5]
        puntos_debiles = sorted([t for t in stats_tema if t['media_tema'] is not None], key=lambda x: x['media_tema'])[:5]


        data = {
            "media_general": round(media_general, 2),
            "resumen_aciertos": { "aciertos": total_aciertos, "fallos": total_fallos },
            "stats_por_oposicion": [{"oposicion": item['tema__oposicion__nombre'], "media": round(item['media_oposicion'], 2)} for item in stats_oposicion],
            "historico_resultados": [{"fecha": item.fecha.strftime('%d/%m/%Y'), "nota": round(item.media_test, 2)} for item in historico],
            # --- AÑADIMOS LOS NUEVOS DATOS A LA RESPUESTA ---
            "puntos_fuertes": [{"tema_id": item['tema__id'], "tema": item['tema__nombre'], "oposicion": item['tema__oposicion__nombre'], "media": round(item['media_tema'], 2)} for item in puntos_fuertes],
            "puntos_debiles": [{"tema_id": item['tema__id'], "tema": item['tema__nombre'], "oposicion": item['tema__oposicion__nombre'], "media": round(item['media_tema'], 2)} for item in puntos_debiles],
        }
        
        return Response(data)

# ... (El resto de las vistas de Stripe no cambian)
stripe.api_key = settings.STRIPE_SECRET_KEY
class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        price_id = os.environ.get('STRIPE_PRICE_ID')
        if not price_id:
            return Response({'error': 'La configuración de pagos en el servidor está incompleta.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
