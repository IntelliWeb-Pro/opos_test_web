# tests/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, PreguntaFallada, Post, Suscripcion

# --- 1. ADMIN PERSONALIZADO CON BORRADO MANUAL DE SUSCRIPCIONES ---
class CustomUserAdmin(BaseUserAdmin):
    
    def delete_queryset(self, request, queryset):
        # Este método se ejecuta al borrar VARIOS usuarios desde la lista.
        print(f"--- ADMIN DEBUG (bulk): Iniciando borrado de {queryset.count()} usuarios.")
        
        # --- PASO CLAVE: Borramos las suscripciones manualmente PRIMERO ---
        for user in queryset:
            try:
                # Buscamos si el usuario tiene una suscripción asociada
                if hasattr(user, 'suscripcion'):
                    print(f"--- ADMIN DEBUG (bulk): Borrando suscripción para el usuario: {user.username}")
                    user.suscripcion.delete()
            except Exception as e:
                # Si algo falla aquí, lo veremos en los logs
                print(f"--- ADMIN DEBUG (bulk): ERROR al borrar suscripción para {user.username}: {e}")

        # Ahora que los objetos más conflictivos han sido eliminados,
        # dejamos que Django borre los usuarios y el resto de datos en cascada.
        print("--- ADMIN DEBUG (bulk): Suscripciones eliminadas. Procediendo a borrar usuarios.")
        super().delete_queryset(request, queryset)
        print("--- ADMIN DEBUG (bulk): Proceso de borrado completado.")

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
