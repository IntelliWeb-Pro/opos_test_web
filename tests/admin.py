# tests/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User # Importamos el modelo User
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, PreguntaFallada, Post, Suscripcion

# --- 1. ADMIN PERSONALIZADO PARA DEPURAR EL BORRADO DE USUARIOS ---
class CustomUserAdmin(BaseUserAdmin):
    def delete_model(self, request, obj):
        # Este método se ejecuta cuando borras UN solo usuario desde el admin.
        print(f"--- ADMIN DEBUG: Intentando borrar al usuario: {obj.username}")
        try:
            # Intentamos ejecutar el borrado normal
            super().delete_model(request, obj)
            print(f"--- ADMIN DEBUG: Usuario {obj.username} borrado con éxito.")
        except Exception as e:
            # ¡AQUÍ ATRAPAREMOS EL ERROR!
            # Si algo falla durante el borrado, lo imprimiremos en los logs.
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"--- ADMIN DEBUG: ERROR ATRAPADO AL BORRAR USUARIO ---")
            print(f"USUARIO: {obj.username}")
            print(f"ERROR: {type(e).__name__} - {e}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # Lanzamos el error de nuevo para que el admin muestre un error
            raise e

# --- 2. TUS CLASES DE ADMIN EXISTENTES (SIN CAMBIOS) ---
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

# --- 3. REGISTRO DE TODOS LOS MODELOS EN EL ADMIN ---

# Para el modelo User, damos de baja el admin por defecto y registramos el nuestro
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# El resto de tus registros se quedan igual
admin.site.register(Oposicion)
admin.site.register(Tema)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(PreguntaFallada)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
