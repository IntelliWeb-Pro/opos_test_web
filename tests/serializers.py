from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, Post

# Serializers Base (se usan dentro de otros)
class TemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = ['id', 'nombre']

class RespuestaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id', 'texto_respuesta']

class RespuestaDetalladaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id', 'texto_respuesta', 'es_correcta', 'texto_justificacion', 'fuente_justificacion', 'url_fuente_oficial']

# Serializers Compuestos
class OposicionSerializer(serializers.ModelSerializer):
    temas = TemaSerializer(many=True, read_only=True)
    class Meta:
        model = Oposicion
        fields = ['id', 'nombre', 'temas']

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
    tema = TemaSerializer(read_only=True)
    oposicion_nombre = serializers.CharField(source='tema.oposicion.nombre', read_only=True)
    class Meta:
        model = ResultadoTest
        fields = ['id', 'tema', 'puntuacion', 'total_preguntas', 'fecha', 'oposicion_nombre']

class ResultadoTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoTest
        fields = ['tema', 'puntuacion', 'total_preguntas']

# Serializers de Autenticación y Blog
class CustomRegisterSerializer(RegisterSerializer):
    # Sobrescribimos el método save para desactivar al usuario por defecto
    def save(self, request):
        # Llama al método original para crear el objeto de usuario
        user = super().save(request)
        # La clave: marcamos al usuario como inactivo
        user.is_active = False
        # Guardamos el cambio en la base de datos
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

from dj_rest_auth.serializers import PasswordResetSerializer
from allauth.account.utils import user_pk_to_url_str
from django.conf import settings

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def save(self):
        request = self.context.get('request')
        # Llama al método original de la librería, pero sobreescribiendo el generador de URL
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'email_template_name': 'account/email/password_reset_key_message.html',
            'url_generator': self.custom_url_generator,
        }
        self.reset_form.save(**opts)

    def custom_url_generator(self, request, user, temp_key):
        # Construye la URL del frontend
        uid = user_pk_to_url_str(user)
        token = temp_key
        
        # Asegúrate de que esta URL coincide con la ruta de tu frontend
        frontend_url = f"https://www.testestado.es/password-reset/{uid}/{token}/"
        return frontend_url