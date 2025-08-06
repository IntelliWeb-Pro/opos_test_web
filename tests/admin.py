# tests/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User # Importamos el modelo User
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, PreguntaFallada, Post, Suscripcion

# --- PRUEBA DE CARGA: Si ves este mensaje en los logs, significa que Django está leyendo este archivo. ---
print("--- ADMIN.PY DE 'TESTS' CARGADO CORRECTAMENTE ---")

# --- 1. ADMIN PERSONALIZADO PARA DEPURAR EL BORRADO DE USUARIOS ---
class CustomUserAdmin(BaseUserAdmin):
    
    def delete_model(self, request, obj):
        # Este método es para borrar UN solo usuario desde su página de edición.
        print(f"--- ADMIN DEBUG (single): Intentando borrar al usuario: {obj.username}")
        try:
            super().delete_model(request, obj)
            print(f"--- ADMIN DEBUG (single): Usuario {obj.username} borrado con éxito.")
        except Exception as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"--- ADMIN DEBUG (single): ERROR ATRAPADO AL BORRAR USUARIO ---")
            print(f"USUARIO: {obj.username}")
            print(f"ERROR: {type(e).__name__} - {e}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            raise e

    def delete_queryset(self, request, queryset):
        # ESTE ES EL MÉTODO NUEVO: Se ejecuta al borrar VARIOS usuarios desde la lista.
        print(f"--- ADMIN DEBUG (bulk): Intentando borrar {queryset.count()} usuarios.")
        try:
            # Intentamos ejecutar el borrado normal del queryset
            super().delete_queryset(request, queryset)
            print(f"--- ADMIN DEBUG (bulk): Queryset borrado con éxito.")
        except Exception as e:
            # ¡AQUÍ ATRAPAREMOS EL ERROR!
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"--- ADMIN DEBUG (bulk): ERROR ATRAPADO AL BORRAR USUARIOS ---")
            print(f"ERROR: {type(e).__name__} - {e}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # Lanzamos el error de nuevo para que el admin muestre un mensaje
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
