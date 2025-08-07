# tests/views.py

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
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.generics import CreateAPIView
from django.utils import timezone

from .models import Oposicion, Tema, Pregunta, ResultadoTest, Suscripcion, Post, CodigoVerificacion
from .serializers import (
    OposicionSerializer, TemaSerializer, PreguntaSimpleSerializer,
    PreguntaDetalladaSerializer, ResultadoTestSerializer, ResultadoTestCreateSerializer,
    PostListSerializer, PostDetailSerializer, CustomRegisterSerializer
)

# --- (El resto de tus vistas se quedan igual) ---
# ... OposicionViewSet, TemaViewSet, etc. ...

class CustomRegisterView(CreateAPIView):
    serializer_class = CustomRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(self.request)
        
        codigo = str(random.randint(100000, 999999))
        CodigoVerificacion.objects.create(usuario=user, codigo=codigo)
        
        # --- PRUEBA DE HUMO (SMOKE TEST) ---
        # Hemos comentado temporalmente todo el bloque de envío de correo.
        # Ahora, la vista simplemente creará el usuario y el código, y devolverá éxito.
        print("--- SMOKE TEST: Bloque de envío de email OMITIDO. ---")
        
        # try:
        #     context = {'username': user.username, 'codigo': codigo}
        #     email_html_message = render_to_string('emails/verificacion_cuenta.html', context)
        #     send_mail(
        #         subject='Código de Verificación para tu cuenta en TestEstado.es',
        #         message=f'Hola {user.username},\n\nTu código de verificación es: {codigo}',
        #         from_email=settings.DEFAULT_FROM_EMAIL,
        #         recipient_list=[user.email],
        #         html_message=email_html_message,
        #         fail_silently=False
        #     )
        # except Exception as e:
        #     print(f"Error al enviar email de verificación al usuario {user.email}: {e}")

        response_data = {
            "detail": "Prueba de registro exitosa (email no enviado).",
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

# --- (El resto de tus vistas se quedan igual) ---
# ... VerificarCuentaView, etc. ...
