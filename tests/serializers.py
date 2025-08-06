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
    def save(self, request):
        print("--- SERIALIZER LOG 1: Entrando en el método save() del serializador.")
        
        # Llama al método save() original de dj-rest-auth para crear el objeto de usuario
        user = super().save(request)
        print(f"--- SERIALIZER LOG 2: Usuario '{user.username}' creado en memoria por super().save().")
        
        # Modificamos el usuario ANTES de que se guarde del todo
        user.is_active = False
        print("--- SERIALIZER LOG 3: 'is_active' establecido en False.")
        
        # Guardamos el cambio final en la base de datos
        user.save()
        print("--- SERIALIZER LOG 4: Cambios guardados en la BBDD. Saliendo del serializador.")
        
        return user