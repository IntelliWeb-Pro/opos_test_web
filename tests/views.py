# ... (al final del archivo tests/views.py)

from django.db.models import Avg, F, ExpressionWrapper, FloatField
from .models import ResultadoTest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model

# --- VISTA PARA LAS ESTADÍSTICAS DEL USUARIO (CORREGIDA) ---
class EstadisticasUsuarioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        usuario = request.user
        resultados = ResultadoTest.objects.filter(usuario=usuario)

        if not resultados.exists():
            # CORRECCIÓN: Devolvemos un 200 OK con un mensaje claro, no un 404.
            return Response({
                "message": "No hay resultados de tests para este usuario."
            }, status=status.HTTP_200_OK)

        media_general = resultados.aggregate(media=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField()))['media']
        stats_oposicion = resultados.values('tema__oposicion__nombre').annotate(media_oposicion=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_oposicion')
        stats_tema = resultados.values('tema__nombre', 'tema__oposicion__nombre').annotate(media_tema=ExpressionWrapper((Avg('puntuacion') * 100.0) / Avg('total_preguntas'), output_field=FloatField())).order_by('-media_tema')
        
        data = {
            "media_general": round(media_general, 2) if media_general is not None else 0,
            "stats_por_oposicion": [{"oposicion": item['tema__oposicion__nombre'], "media": round(item['media_oposicion'], 2)} for item in stats_oposicion],
            "stats_por_tema": [{"oposicion": item['tema__oposicion__nombre'],"tema": item['tema__nombre'],"media": round(item['media_tema'], 2)} for item in stats_tema[:10]]
        }
        
        return Response(data)
