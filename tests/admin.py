# tests/admin.py (Versión Corregida)

from django.contrib import admin
# Asegúrate de que ResultadoTest está importado en esta línea
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest

# Registramos los modelos para que aparezcan en el panel de administración
admin.site.register(Oposicion)
admin.site.register(Tema)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest) # Ahora esta línea funcionará