# tests/serializers.py

from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from .models import Oposicion, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, Post, Suscripcion, TestSession

from dj_rest_auth.serializers import PasswordResetSerializer, UserDetailsSerializer
from allauth.account.utils import user_pk_to_url_str
from django.conf import settings

User = get_user_model()

# --- SERIALIZERS PARA LA NUEVA ESTRUCTURA DE TEMAS ---

class TemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = ['id', 'numero', 'nombre_oficial', 'url_fuente_oficial', 'es_premium', 'slug']

class BloqueSerializer(serializers.ModelSerializer):
    temas = TemaSerializer(many=True, read_only=True)
    class Meta:
        model = Bloque
        fields = ['id', 'numero', 'nombre', 'temas']

class OposicionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oposicion
        fields = ['id', 'nombre', 'slug']

# Serializer completo para la vista de detalle
class OposicionSerializer(serializers.ModelSerializer):
    bloques = BloqueSerializer(many=True, read_only=True)
    class Meta:
        model = Oposicion
        # --- CAMPOS AÑADIDOS ---
        fields = [
            'id', 'nombre', 'slug', 'bloques',
            'descripcion_general', 'info_convocatoria', 'url_boe', 
            'requisitos', 'info_adicional'
        ]


# --- El resto de tus serializers no necesitan cambios ---

class RespuestaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id', 'texto_respuesta']

class RespuestaDetalladaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id', 'texto_respuesta', 'es_correcta', 'texto_justificacion', 'articulo_justificacion', 'url_fuente_oficial']

class PreguntaSimpleSerializer(serializers.ModelSerializer):
    respuestas = RespuestaSimpleSerializer(many=True, read_only=True)
    class Meta:
        model = Pregunta
        fields = ['id', 'texto_pregunta', 'respuestas']

class PreguntaDetalladaSerializer(serializers.ModelSerializer):
    respuestas = RespuestaDetalladaSerializer(many=True, read_only=True)
    class Meta:
        model = Pregunta
        fields = ['id', 'texto_pregunta', 'fuente_original', 'respuestas']

class ResultadoTestSerializer(serializers.ModelSerializer):
    tema_nombre = serializers.CharField(source='tema.nombre_oficial', read_only=True)
    oposicion_nombre = serializers.CharField(source='tema.bloque.oposicion.nombre', read_only=True)
    class Meta:
        model = ResultadoTest
        fields = ['id', 'tema', 'tema_nombre', 'puntuacion', 'total_preguntas', 'fecha', 'oposicion_nombre']

class ResultadoTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoTest
        fields = ['tema', 'puntuacion', 'total_preguntas']

class CustomRegisterSerializer(RegisterSerializer):
    def validate(self, data):
        super().validate(data)
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({'email': 'Este email ya está en uso'})
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({'username': 'Este username ya está en uso'})
        return data

    def save(self, request):
        user = super().save(request)
        user.is_active = False
        user.save()
        return user

class PostListSerializer(serializers.ModelSerializer):
    autor_username = serializers.CharField(source='autor.username', read_only=True)
    class Meta:
        model = Post
        fields = ['id', 'titulo', 'slug', 'autor_username', 'creado_en']

class PostDetailSerializer(serializers.ModelSerializer):
    autor_username = serializers.CharField(source='autor.username', read_only=True)
    class Meta:
        model = Post
        fields = ['id', 'titulo', 'slug', 'autor_username', 'contenido', 'creado_en', 'actualizado_en']

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def save(self):
        request = self.context.get('request')
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'email_template_name': 'account/email/password_reset_key_message.html',
            'url_generator': self.custom_url_generator,
        }
        self.reset_form.save(**opts)

    def custom_url_generator(self, request, user, temp_key):
        uid = user_pk_to_url_str(user)
        token = temp_key
        frontend_url = f"https://www.testestado.es/password-reset/{uid}/{token}/"
        return frontend_url

class SuscripcionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suscripcion
        fields = ['activa']

class CustomUserDetailsSerializer(UserDetailsSerializer):
    suscripcion = serializers.SerializerMethodField()

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('suscripcion',)

    def get_suscripcion(self, obj):
        if hasattr(obj, 'suscripcion'):
            return SuscripcionStatusSerializer(obj.suscripcion).data
        return None

# tests/serializers.py (sólo la clase TestSessionSerializer)

from rest_framework import serializers
from .models import TestSession

class TestSessionSerializer(serializers.ModelSerializer):
    # Alias de escritura: acepta "preguntas" además de "preguntas_ids"
    preguntas = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Alias de preguntas_ids. Lista de IDs de preguntas."
    )

    class Meta:
        model = TestSession
        read_only_fields = ("id", "user", "created_at", "updated_at")
        fields = (
            "id", "tipo",
            "preguntas_ids",     # ← guardamos aquí
            "preguntas",         # ← alias write_only
            "idx_actual", "respuestas",
            "tiempo_restante", "estado", "config",
            "created_at", "updated_at",
        )

    def _coerce_alias(self, validated_data):
        """
        Si llega 'preguntas', muévelo a 'preguntas_ids'.
        """
        preguntas = validated_data.pop("preguntas", None)
        if preguntas is not None:
            validated_data["preguntas_ids"] = preguntas
        return validated_data

    def validate(self, data):
        data = dict(data)  # asegurar que es mutable
        data = self._coerce_alias(data)

        # Si intentan finalizar sin preguntas, rechazamos
        if data.get("estado") == "finalizado":
            tiene_preguntas = bool(
                data.get("preguntas_ids")
                or getattr(self.instance, "preguntas_ids", None)
            )
            if not tiene_preguntas:
                raise serializers.ValidationError("No puedes finalizar una sesión sin preguntas.")
        return data

    def create(self, validated_data):
        validated_data = self._coerce_alias(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._coerce_alias(validated_data)
        return super().update(instance, validated_data)
