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

# --- SERIALIZERS DE RESULTADOS (CORREGIDOS) ---

# Serializer para LEER resultados (muestra toda la info del tema)
class ResultadoTestSerializer(serializers.ModelSerializer):
    tema = TemaSerializer(read_only=True)
    oposicion_nombre = serializers.CharField(source='tema.oposicion.nombre', read_only=True)
    
    class Meta:
        model = ResultadoTest
        fields = ['id', 'tema', 'puntuacion', 'total_preguntas', 'fecha', 'oposicion_nombre']

# NUEVO Serializer para CREAR resultados (acepta solo el ID del tema)
class ResultadoTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoTest
        # Solo necesita los campos que el frontend envía para crear
        fields = ['tema', 'puntuacion', 'total_preguntas']
