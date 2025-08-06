from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, Post, PreguntaFallada

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
    username = serializers.CharField(max_length=13, min_length=4)
    def save(self, request):
        user = super().save(request)
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


class CustomRegisterSerializer(RegisterSerializer):
    # Puedes añadir campos extra si quieres que se pidan en el registro
    # Por ejemplo, nombre y apellidos.
    # first_name = serializers.CharField(required=False)
    # last_name = serializers.CharField(required=False)

    def save(self, request):
        # Llama al método save() original de dj-rest-auth
        user = super().save(request)
        
        # Modificamos el usuario ANTES de que se guarde del todo
        user.is_active = False # ¡La clave! El usuario no podrá hacer login hasta verificar.
        
        # Si añadiste campos extra, aquí los guardarías
        # user.first_name = self.data.get('first_name', '')
        # user.last_name = self.data.get('last_name', '')
        
        user.save()
        return user