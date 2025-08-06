# tests/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, PreguntaFallada, Post, Suscripcion

# --- PRUEBA DE CARGA ---
print("--- ADMIN.PY DE 'TESTS' CARGADO CORRECTAMENTE ---")

# --- ADMIN PERSONALIZADO CON PRUEBA DE HUMO (NO BORRA NADA) ---
class CustomUserAdmin(BaseUserAdmin):
    
    def delete_queryset(self, request, queryset):
        # --- PRUEBA DE HUMO ---
        # Si ves este mensaje en los logs, significa que nuestro código se está ejecutando.
        # No vamos a borrar nada, solo a confirmar que llegamos hasta aquí.
        
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("--- ADMIN SMOKE TEST: ¡El método delete_queryset ha sido llamado! ---")
        print(f"--- Se iban a borrar {queryset.count()} usuarios. ---")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        # Mostramos un mensaje de éxito en la interfaz del admin para que sepas que funcionó.
        self.message_user(request, f"Prueba de humo exitosa. Se habrían borrado {queryset.count()} usuarios.", messages.SUCCESS)
        
        # IMPORTANTE: No llamamos a super().delete_queryset(request, queryset)
        # para no interactuar con la base de datos.

# --- TUS CLASES DE ADMIN EXISTENTES (SIN CAMBIOS) ---
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

# --- REGISTRO DE TODOS LOS MODELOS EN EL ADMIN ---
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Oposicion)
admin.site.register(Tema)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(PreguntaFallada)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
