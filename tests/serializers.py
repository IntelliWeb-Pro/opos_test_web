# tests/serializers.py (Versión Actualizada)

from rest_framework import serializers
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest

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

# --- SERIALIZER DE RESULTADOS (ACTUALIZADO) ---
class ResultadoTestSerializer(serializers.ModelSerializer):
    # Le decimos que use el TemaSerializer para mostrar los detalles del tema
    tema = TemaSerializer(read_only=True)
    # Añadimos el nombre de la oposición a través del tema
    oposicion_nombre = serializers.CharField(source='tema.oposicion.nombre', read_only=True)

    class Meta:
        model = ResultadoTest
        # Añadimos 'oposicion_nombre' a los campos que devolverá la API
        fields = ['id', 'tema', 'puntuacion', 'total_preguntas', 'fecha', 'oposicion_nombre']
        read_only_fields = ['usuario']