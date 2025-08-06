# tests/admin.py

from django.contrib import admin
# Se ha eliminado 'PreguntaFallada' de esta línea de importación
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, Post, Suscripcion

# --- Clases de Admin personalizadas para tus modelos ---
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

# --- Registro de todos los modelos en el Admin ---
# Django registrará el modelo User por defecto.
admin.site.register(Oposicion)
admin.site.register(Tema)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
# La línea de registro para PreguntaFallada ha sido eliminada.
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
