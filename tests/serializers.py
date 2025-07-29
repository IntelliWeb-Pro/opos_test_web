from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest

# --- NUEVO: Serializer de Registro Personalizado ---
class CustomRegisterSerializer(RegisterSerializer):
    # Sobrescribimos el campo 'username' del serializer original
    username = serializers.CharField(max_length=13, min_length=4)

    def save(self, request):
        # Llamamos al método 'save' original para que haga todo el trabajo de crear el usuario
        user = super().save(request)
        return user

# --- SERIALIZERS SIMPLES Y DETALLADOS PARA PREGUNTAS (Sin cambios) ---
class RespuestaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id', 'texto_respuesta']

class RespuestaDetalladaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id', 'texto_respuesta', 'es_correcta', 'texto_justificacion', 'fuente_justificacion', 'url_fuente_oficial']

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

# --- SERIALIZERS DE TEMAS Y OPOSICIONES (Sin cambios) ---
class TemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = ['id', 'nombre']

class OposicionSerializer(serializers.ModelSerializer):
    temas = TemaSerializer(many=True, read_only=True)
    class Meta:
        model = Oposicion
        fields = ['id', 'nombre', 'temas']

# --- SERIALIZERS DE RESULTADOS (Sin cambios) ---
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
