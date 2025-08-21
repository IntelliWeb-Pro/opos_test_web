# tests/views.py

import random
import stripe
import os
import sys
import traceback
from datetime import date, timedelta

from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Avg, Sum, ExpressionWrapper, FloatField, F
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.generics import CreateAPIView
from django.utils import timezone
from dj_rest_auth.views import PasswordResetView
from django_filters.rest_framework import DjangoFilterBackend  # ⬅️ NUEVO
from .permissions import IsSubscribed
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .utils.examen_import import import_examen_oficial

from .models import Oposicion, Tema, Pregunta, ResultadoTest, Suscripcion, Post, CodigoVerificacion, Respuesta, TestSession, ExamenOficial
from .serializers import (
    OposicionSerializer, OposicionListSerializer,
    TemaSerializer, PreguntaSimpleSerializer,
    PreguntaDetalladaSerializer, ResultadoTestSerializer, ResultadoTestCreateSerializer,
    PostListSerializer, PostDetailSerializer, CustomRegisterSerializer, TestSessionSerializer, ExamenOficialSerializer
)

# --- VISTAS DEL ROUTER ---
class OposicionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Oposicion.objects.all()
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return OposicionListSerializer
        return OposicionSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return Oposicion.objects.prefetch_related('bloques__temas').all()
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        print("--- OPOSICIONES: Iniciando listado ---", file=sys.stderr, flush=True)
        try:
            queryset = self.filter_queryset(self.get_queryset())
            print(f"--- OPOSICIONES: Queryset obtenido.", file=sys.stderr, flush=True)

            page = self.paginate_queryset(queryset)
            if page is not None:
                queryset = page
            
            serializer_class = self.get_serializer_class()
            print(f"--- OPOSICIONES: Usando serializer: {serializer_class.__name__}", file=sys.stderr, flush=True)
            serializer = self.get_serializer(queryset, many=True)
            
            print("--- OPOSICIONES: Iniciando serialización...", file=sys.stderr, flush=True)
            serialized_data = serializer.data
            print("--- OPOSICIONES: Serialización completada.", file=sys.stderr, flush=True)

            if page is not None:
                return self.get_paginated_response(serialized_data)
            return Response(serialized_data)

        except Exception as e:
            print(f"--- ERROR CRÍTICO EN OPOSICIONES LIST: {type(e).__name__} - {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            return Response({"error": "Error interno del servidor al listar oposiciones."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# tests/views.py

class TemaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'  # ⬅️ ahora el retrieve es /api/temas/<slug>/

    def get_queryset(self):
        qs = super().get_queryset()
        # opcional: permitir ?oposicion=<slug_oposicion>
        opos_slug = self.request.query_params.get('oposicion')
        if opos_slug:
            qs = qs.filter(bloque__oposicion__slug=opos_slug)
        return qs



class PreguntaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Pregunta.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PreguntaSimpleSerializer
        return PreguntaDetalladaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # ⬅️ nuevo: filtrar por slug del tema
        tema_slug = self.request.query_params.get('tema_slug')

        if tema_slug:
            try:
                tema = Tema.objects.get(slug=tema_slug)
            except Tema.DoesNotExist:
                return Pregunta.objects.none()

            user = self.request.user
            is_subscribed = getattr(getattr(user, 'suscripcion', None), 'activa', False)

            queryset = queryset.filter(tema=tema)

            # gating premium
            if tema.es_premium and (not user.is_authenticated or not is_subscribed):
                # muestra 5 primeras (orden estable) para free
                return queryset.order_by('id')[:5]

            # suscrito o tema no premium → aleatorio y 20 máx (como tenías)
            return queryset.order_by('?')[:20]

        # si no viene tema_slug devolvemos el QS sin tocar (p.ej. admin/scripts)
        return queryset
    
    @action(detail=False, methods=['post'])
    def corregir(self, request):
        ids_preguntas = request.data.get('ids', [])
        if not ids_preguntas:
            return Response({"error": "No se proporcionaron IDs de preguntas"}, status=status.HTTP_400_BAD_REQUEST)
        preguntas_corregidas = Pregunta.objects.filter(id__in=ids_preguntas)
        serializer = self.get_serializer(preguntas_corregidas, many=True)
        return Response(serializer.data)

    
    @action(detail=False, methods=['post'])
    def corregir(self, request):
        ids_preguntas = request.data.get('ids', [])
        if not ids_preguntas: return Response({"error": "No se proporcionaron IDs de preguntas"}, status=status.HTTP_400_BAD_REQUEST)
        preguntas_corregidas = Pregunta.objects.filter(id__in=ids_preguntas)
        serializer = self.get_serializer(preguntas_corregidas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def detalle(self, request):
        """
        GET /api/preguntas/detalle/?ids=1,2,3
        Devuelve preguntas + respuestas SIN el flag es_correcta.
        """
        ids = request.query_params.get('ids', '')
        try:
            ids = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        except ValueError:
            ids = []
        if not ids:
            return Response([], status=200)

        qs = Pregunta.objects.filter(id__in=ids).prefetch_related('respuestas')
        data = PreguntaSimpleSerializer(qs, many=True).data
        # PreguntaSimpleSerializer ya NO incluye es_correcta → seguro
        # (si incluyera, aquí podríamos borrar esos campos manualmente)
        return Response(data)


class ResultadoTestViewSet(viewsets.ModelViewSet):
    queryset = ResultadoTest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ResultadoTestCreateSerializer
        return ResultadoTestSerializer

    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        tema_slug = data.get('tema_slug')
        tema_id = data.get('tema')

        # Si nos mandan slug, lo resolvemos a id
        if tema_slug and not tema_id:
            try:
                tema_obj = Tema.objects.only('id').get(slug=tema_slug)
                data['tema'] = tema_obj.id
            except Tema.DoesNotExist:
                return Response({'error': 'Tema no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)  # guarda con usuario en perform_create
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)



class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.filter(estado='publicado').select_related('autor')
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list': 
            return PostListSerializer
        return PostDetailSerializer

    def list(self, request, *args, **kwargs):
        print("--- BLOG: Iniciando listado de posts ---", file=sys.stderr, flush=True)
        return super().list(request, *args, **kwargs)

# --- VISTAS ESPECÍFICAS (FUERA DEL ROUTER) ---
class EstadisticasUsuarioView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            print("--- STATS: Iniciando cálculo de estadísticas ---", file=sys.stderr, flush=True)
            usuario = request.user
            
            print("--- STATS: Obteniendo resultados del usuario...", file=sys.stderr, flush=True)
            resultados = ResultadoTest.objects.filter(usuario=usuario)
            if not resultados.exists(): 
                print("--- STATS: No se encontraron resultados.", file=sys.stderr, flush=True)
                return Response({"message": "No hay resultados de tests para este usuario."}, status=status.HTTP_200_OK)

            print("--- STATS: Calculando resumen total...", file=sys.stderr, flush=True)
            resumen_total = resultados.aggregate(total_aciertos=Sum('puntuacion'), total_preguntas=Sum('total_preguntas'))
            total_aciertos = resumen_total['total_aciertos'] or 0
            total_preguntas_global = resumen_total['total_preguntas'] or 0
            total_fallos = total_preguntas_global - total_aciertos
            media_general = (total_aciertos * 100.0 / total_preguntas_global) if total_preguntas_global > 0 else 0

            print("--- STATS: Calculando estadísticas por oposición...", file=sys.stderr, flush=True)
            stats_oposicion = resultados.values('tema__bloque__oposicion__nombre').annotate(media_oposicion=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_oposicion')

            print("--- STATS: Calculando histórico...", file=sys.stderr, flush=True)
            historico = resultados.order_by('fecha')[:15].annotate(media_test=ExpressionWrapper((F('puntuacion') * 100.0) / F('total_preguntas'), output_field=FloatField()))

            print("--- STATS: Calculando estadísticas por tema...", file=sys.stderr, flush=True)
            stats_tema = resultados.values('tema__id', 'tema__nombre_oficial', 'tema__bloque__oposicion__nombre', 'tema__url_fuente_oficial').annotate(media_tema=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField()))

            print("--- STATS: Calculando puntos fuertes y débiles...", file=sys.stderr, flush=True)
            puntos_fuertes = sorted([t for t in stats_tema if t['media_tema'] is not None], key=lambda x: x['media_tema'], reverse=True)[:5]
            puntos_debiles = sorted([t for t in stats_tema if t['media_tema'] is not None], key=lambda x: x['media_tema'])[:5]
            
            print("--- STATS: Construyendo respuesta final...", file=sys.stderr, flush=True)
            data = {
                "media_general": round(media_general, 2),
                "resumen_aciertos": { "aciertos": total_aciertos, "fallos": total_fallos },
                "stats_por_oposicion": [{"oposicion": item['tema__bloque__oposicion__nombre'], "media": round(item['media_oposicion'], 2)} for item in stats_oposicion],
                "historico_resultados": [{"fecha": item.fecha.strftime('%d/%m/%Y'), "nota": round(item.media_test, 2)} for item in historico],
                "puntos_fuertes": [{"tema_id": item['tema__id'], "tema": item['tema__nombre_oficial'], "oposicion": item['tema__bloque__oposicion__nombre'], "media": round(item['media_tema'], 2)} for item in puntos_fuertes],
                "puntos_debiles": [{"tema_id": item['tema__id'], "tema": item['tema__nombre_oficial'], "oposicion": item['tema__bloque__oposicion__nombre'], "media": round(item['media_tema'], 2)} for item in puntos_debiles],
            }
            
            print("--- STATS: Proceso completado con éxito. ---", file=sys.stderr, flush=True)
            return Response(data)

        except Exception as e:
            print(f"--- ERROR CRÍTICO EN ESTADÍSTICAS: {type(e).__name__} - {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            return Response({"error": "Error interno del servidor al calcular las estadísticas."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RankingSemanalView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        resultados_semanales = ResultadoTest.objects.filter(fecha__gte=start_of_week)
        ranking_data = resultados_semanales.values('usuario__username').annotate(puntuacion_total=Sum('puntuacion'), preguntas_totales=Sum('total_preguntas')).filter(preguntas_totales__gt=0)
        ranking_list = []
        for item in ranking_data:
            porcentaje = (item['puntuacion_total'] * 100.0) / item['preguntas_totales']
            ranking_list.append({'username': item['usuario__username'], 'porcentaje_aciertos': round(porcentaje, 2)})
        ranking_list.sort(key=lambda x: x['porcentaje_aciertos'], reverse=True)
        user_rank = None
        for i, user_data in enumerate(ranking_list):
            if user_data['username'] == request.user.username:
                user_rank = {'rank': i + 1, 'username': user_data['username'], 'porcentaje_aciertos': user_data['porcentaje_aciertos']}
                break
        response_data = {'podium': ranking_list[:3], 'user_rank': user_rank}
        return Response(response_data)

class AnalisisRefuerzoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        usuario = request.user
        resultados = ResultadoTest.objects.filter(usuario=usuario)
        if not resultados.exists(): return Response({"message": "No hay suficientes datos para generar un análisis."}, status=200)
        stats_tema = resultados.values('tema__id', 'tema__nombre_oficial', 'tema__bloque__oposicion__nombre', 'tema__url_fuente_oficial').annotate(puntuacion_total=Sum('puntuacion'), preguntas_totales=Sum('total_preguntas')).filter(preguntas_totales__gt=0)
        temas_analizados = []
        for item in stats_tema:
            porcentaje = (item['puntuacion_total'] * 100.0) / item['preguntas_totales']
            temas_analizados.append({'tema_id': item['tema__id'], 'tema_nombre': item['tema__nombre_oficial'], 'oposicion_nombre': item['tema__bloque__oposicion__nombre'], 'url_boe': item['tema__url_fuente_oficial'], 'porcentaje_aciertos': round(porcentaje, 2)})
        dominados = sorted([t for t in temas_analizados if t['porcentaje_aciertos'] > 90], key=lambda x: x['porcentaje_aciertos'], reverse=True)[:5]
        repasar = sorted([t for t in temas_analizados if 60 <= t['porcentaje_aciertos'] <= 90], key=lambda x: x['porcentaje_aciertos'])[:5]
        profundizar = sorted([t for t in temas_analizados if t['porcentaje_aciertos'] < 60], key=lambda x: x['porcentaje_aciertos'])[:5]
        response_data = {'dominados': dominados, 'repasar': repasar, 'profundizar': profundizar}
        return Response(response_data)

stripe.api_key = settings.STRIPE_SECRET_KEY
class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        # Nuevo: soporte de múltiples planes y prueba de 7 días (Stripe gestiona el trial)
        plan = (request.data.get('plan') or '').lower()
        plan_env = {
            'bronce': os.environ.get('NEXT_PUBLIC_STRIPE_PRICE_BRONCE'),
            'plata': os.environ.get('NEXT_PUBLIC_STRIPE_PRICE_PLATA'),
            'oro': os.environ.get('NEXT_PUBLIC_STRIPE_PRICE_ORO'),
            'platino': os.environ.get('NEXT_PUBLIC_STRIPE_PRICE_PLATINO'),
        }
        price_id = None
        if plan:
            price_id = plan_env.get(plan)
        # retrocompatibilidad: si no se envía plan, usamos la variable existente
        if not price_id:
            price_id = os.environ.get('STRIPE_PRICE_ID')
        if not price_id:
            return Response({'error': 'Plan inválido o configuración de precios incompleta.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                # Prueba gratuita de 7 días (opción B)
                subscription_data={
                    'trial_period_days': 7,
                },
                success_url='https://www.testestado.es/pago-exitoso?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://www.testestado.es/pago-cancelado',
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

class ContactoView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        nombre = request.data.get('nombre')
        email = request.data.get('email')
        telefono = request.data.get('telefono')
        asunto = request.data.get('asunto')
        mensaje = request.data.get('mensaje')
        if not all([nombre, email, asunto, mensaje]):
            return Response({"error": "Todos los campos excepto el teléfono son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)
        
        print("--- DIAGNÓSTICO (CONTACTO): CONFIGURACIÓN DE EMAIL ---", file=sys.stderr, flush=True)
        print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'No definido')}", file=sys.stderr, flush=True)
        print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No definido')}", file=sys.stderr, flush=True)
        print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No definido')}", file=sys.stderr, flush=True)
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
        password_exists = "Sí" if password else "No"
        password_length = len(password) if password else 0
        print(f"EMAIL_HOST_PASSWORD: Existe={password_exists}, Longitud={password_length}", file=sys.stderr, flush=True)
        print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No definido')}", file=sys.stderr, flush=True)
        print("----------------------------------------------------", file=sys.stderr, flush=True)

        try:
            context = {'nombre': nombre, 'email': email, 'telefono': telefono, 'asunto': asunto, 'mensaje': mensaje}
            email_html_message = render_to_string('emails/contacto.html', context)
            email_plaintext_message = f"Nuevo mensaje de contacto de {nombre} ({email}):\n\nTeléfono: {telefono}\nAsunto: {asunto}\n\nMensaje:\n{mensaje}"
            
            print("--- DIAGNÓSTICO (CONTACTO): Intentando enviar email...", file=sys.stderr, flush=True)
            send_mail(
                subject=f'Nuevo Mensaje de Contacto: {asunto}',
                message=email_plaintext_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['deventerprisedtb@gmail.com'],
                html_message=email_html_message,
                fail_silently=False,
            )
            print("--- DIAGNÓSTICO (CONTACTO): La llamada a send_mail se completó sin errores.", file=sys.stderr, flush=True)
            return Response({"success": "Mensaje enviado correctamente."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"--- ERROR ATRAPADO (CONTACTO): {type(e).__name__} - {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            return Response({"error": "Hubo un problema al enviar tu mensaje. Por favor, inténtalo de nuevo más tarde."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomRegisterView(CreateAPIView):
    serializer_class = CustomRegisterSerializer
    permission_classes = [permissions.AllowAny]
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save(self.request)
            codigo = str(random.randint(100000, 999999))
            CodigoVerificacion.objects.create(usuario=user, codigo=codigo)
            
            print("--- DIAGNÓSTICO (REGISTRO): CONFIGURACIÓN DE EMAIL ---", file=sys.stderr, flush=True)
            print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'No definido')}", file=sys.stderr, flush=True)
            print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No definido')}", file=sys.stderr, flush=True)
            print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No definido')}", file=sys.stderr, flush=True)
            password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            password_exists = "Sí" if password else "No"
            password_length = len(password) if password else 0
            print(f"EMAIL_HOST_PASSWORD: Existe={password_exists}, Longitud={password_length}", file=sys.stderr, flush=True)
            print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No definido')}", file=sys.stderr, flush=True)
            print("----------------------------------------------------", file=sys.stderr, flush=True)

            context = {'username': user.username, 'codigo': codigo}
            email_html_message = render_to_string('emails/verificacion_cuenta.html', context)
            
            print(f"--- REGISTRO: Intentando enviar email a '{user.email}'...", file=sys.stderr, flush=True)
            send_mail(
                subject='Código de Verificación para tu cuenta en TestEstado.es',
                message=f'Hola {user.username},\n\nTu código de verificación es: {codigo}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_html_message,
                fail_silently=False
            )
            print("--- REGISTRO: Email enviado con éxito.", file=sys.stderr, flush=True)
            
            response_data = {"detail": "Registro exitoso. Por favor, revisa tu email para el código de verificación."}
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"--- ERROR CRÍTICO EN REGISTRO: {type(e).__name__} - {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            return Response({"error": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerificarCuentaView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        codigo = request.data.get('codigo')
        if not email or not codigo:
            return Response({'error': 'El email y el código de verificación son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.filter(email=email, is_active=False).order_by('-date_joined').first()
        if not user:
            if get_user_model().objects.filter(email=email, is_active=True).exists():
                return Response({'error': 'Esta cuenta ya ha sido activada previamente.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'El código o el email son incorrectos.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            codigo_verificacion = CodigoVerificacion.objects.get(usuario=user, codigo=codigo)
            if timezone.now() > codigo_verificacion.creado_en + timedelta(minutes=15):
                codigo_verificacion.delete()
                return Response({'error': 'El código de verificación ha expirado. Por favor, solicita uno nuevo.'}, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            codigo_verificacion.delete()
            return Response({'success': '¡Cuenta activada con éxito! Ya puedes iniciar sesión.'}, status=status.HTTP_200_OK)
        except CodigoVerificacion.DoesNotExist:
            return Response({'error': 'El código o el email son incorrectos.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Ha ocurrido un error inesperado en el servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        try:
            print("--- PASSWORD RESET: Iniciando proceso de reseteo.", file=sys.stderr, flush=True)
            
            print("--- DIAGNÓSTICO (RESET): CONFIGURACIÓN DE EMAIL ---", file=sys.stderr, flush=True)
            print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'No definido')}", file=sys.stderr, flush=True)
            print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No definido')}", file=sys.stderr, flush=True)
            print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No definido')}", file=sys.stderr, flush=True)
            password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            password_exists = "Sí" if password else "No"
            password_length = len(password) if password else 0
            print(f"EMAIL_HOST_PASSWORD: Existe={password_exists}, Longitud={password_length}", file=sys.stderr, flush=True)
            print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No definido')}", file=sys.stderr, flush=True)
            print("----------------------------------------------------", file=sys.stderr, flush=True)

            print("--- PASSWORD RESET: Llamando a la lógica original para enviar email...", file=sys.stderr, flush=True)
            response = super().post(request, *args, **kwargs)
            print("--- PASSWORD RESET: Lógica original completada sin errores.", file=sys.stderr, flush=True)
            return response

        except Exception as e:
            print(f"--- ERROR CRÍTICO EN PASSWORD RESET: {type(e).__name__} - {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            return Response({"error": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DemoQuestionsView(APIView):
    """
    Devuelve N preguntas aleatorias (por defecto 15), públicas,
    con opciones sin marcar cuál es correcta.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Número solicitado (clamp a 1..15 para que sea ligero)
        try:
            n = int(request.query_params.get("n", 15))
        except (TypeError, ValueError):
            n = 15
        n = max(1, min(15, n))

        qs = (
            Pregunta.objects
            .select_related("tema")
            .prefetch_related("respuestas")
            .order_by("?")[:n]
        )
        data = PreguntaSimpleSerializer(qs, many=True).data
        return Response({"count": len(data), "results": data})

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user_id", None) == request.user.id

class TestSessionViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
      - POST   /api/sesiones/                         (crear)
      - GET    /api/sesiones/?pendientes=1&limit=5    (listar)
      - GET    /api/sesiones/<uuid>/                  (detalle)
      - PATCH  /api/sesiones/<uuid>/                  (parchear)
    """
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = TestSession.objects.filter(user=self.request.user)
        pendientes = self.request.query_params.get("pendientes")
        tipo = self.request.query_params.get("tipo")
        if pendientes:
            qs = qs.filter(estado__in=["en_curso", "abandonado"])
        if tipo in {"tema", "repaso"}:
            qs = qs.filter(tipo=tipo)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        limit = request.query_params.get("limit")
        if limit:
            try:
                qs = qs[:int(limit)]
            except ValueError:
                pass
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExamenOficialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/examenes-oficiales/?oposicion=<slug>    -> lista plantillas activas
    /api/examenes-oficiales/<slug>/              -> detalle de plantilla
    /api/examenes-oficiales/<slug>/iniciar/     -> POST: crea sesión (tipo=examen)
    """
    queryset = ExamenOficial.objects.filter(activo=True).select_related('oposicion')
    serializer_class = ExamenOficialSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        opos_slug = self.request.query_params.get('oposicion')
        if opos_slug:
            qs = qs.filter(oposicion__slug=opos_slug)
        return qs

    @action(detail=True, methods=['post'])
    def iniciar(self, request, slug=None):
        plantilla = self.get_object()
        user = request.user
        op = plantilla.oposicion

        # 60 del bloque 1, 50 del bloque 2 (por defecto de la plantilla)
        n1 = int(request.data.get('n1', plantilla.preguntas_bloque1))
        n2 = int(request.data.get('n2', plantilla.preguntas_bloque2))
        mezclar = str(request.data.get('mezclar', '1')) in {'1', 'true', 'True'}

        # Preguntas por bloque
        qs_b1 = Pregunta.objects.filter(tema__bloque__oposicion=op, tema__bloque__numero=1)
        qs_b2 = Pregunta.objects.filter(tema__bloque__oposicion=op, tema__bloque__numero=2)

        ids_b1 = list(qs_b1.order_by('?').values_list('id', flat=True)[:n1])
        ids_b2 = list(qs_b2.order_by('?').values_list('id', flat=True)[:n2])

        preguntas_ids = ids_b1 + ids_b2
        if not preguntas_ids:
            return Response({'error': 'No hay preguntas suficientes para generar el examen.'}, status=400)

        if mezclar:
            random.shuffle(preguntas_ids)

        minutos = int(request.data.get('minutos', plantilla.duracion_minutos))
        ses = TestSession.objects.create(
            user=user,
            tipo='examen',
            preguntas_ids=preguntas_ids,
            idx_actual=0,
            respuestas={},
            tiempo_restante=max(1, minutos)*60,
            estado='en_curso',
            config={
                'oposicion': op.slug,
                'examen_slug': plantilla.slug,
                'plantilla': {
                    'preguntas_bloque1': plantilla.preguntas_bloque1,
                    'preguntas_bloque2': plantilla.preguntas_bloque2,
                    'duracion_minutos': plantilla.duracion_minutos,
                }
            }
        )
        # Respondemos con la sesión y, si quieres, con el “esqueleto” del examen
        return Response({
            'id': str(ses.id),
            'count': len(preguntas_ids),
            'tiempo_restante': ses.tiempo_restante,
            'config': ses.config,
        }, status=201)

class ImportExamenOficialView(APIView):
    """
    POST /api/examenes/importar/
      - FormData:
        - file: (CSV)
        - oposicion: slug o nombre
      Autorización:
        - staff autenticado  (Authorization: Bearer ...)
        - o cabecera X-Import-Key que coincida con settings.EXAMEN_IMPORT_KEY
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Seguridad sencilla y práctica:
        ok = False
        if request.user and request.user.is_authenticated and request.user.is_staff:
            ok = True
        else:
            provided = request.headers.get("X-Import-Key", "")
            secret = getattr(settings, "EXAMEN_IMPORT_KEY", "")
            if secret and provided and provided == secret:
                ok = True
        if not ok:
            return Response({"error": "No autorizado"}, status=403)

        file = request.FILES.get("file")
        oposicion = request.data.get("oposicion", "").strip()
        if not file or not oposicion:
            return Response({"error": "Faltan parámetros: 'file' y 'oposicion'."}, status=400)

        try:
            stats = import_examen_oficial(file, oposicion)
            return Response(stats, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)