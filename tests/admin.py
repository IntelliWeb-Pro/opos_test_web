# tests/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Oposicion, Tema, Pregunta, Respuesta, ResultadoTest, Post, Suscripcion

# --- 1. ACCIÓN DE BORRADO FORZADO ---
@admin.action(description="Forzar borrado de usuarios seleccionados (y sus datos)")
def force_delete_users(modeladmin, request, queryset):
    """
    Acción que borra usuarios y sus datos relacionados de forma controlada
    para evitar timeouts en el servidor.
    """
    deleted_count = 0
    for user in queryset:
        print(f"--- ADMIN ACTION: Forzando borrado del usuario: {user.username} (ID: {user.id})")
        try:
            # Borramos el usuario. on_delete=CASCADE se encargará del resto.
            user.delete()
            deleted_count += 1
        except Exception as e:
            print(f"--- ADMIN ACTION ERROR: No se pudo borrar al usuario {user.username}. Error: {e}")
            modeladmin.message_user(request, f"Error al borrar al usuario {user.username}: {e}", messages.ERROR)
    
    if deleted_count > 0:
        modeladmin.message_user(request, f"{deleted_count} usuarios han sido borrados con éxito.", messages.SUCCESS)

# --- 2. ADMIN PERSONALIZADO CON LA NUEVA ACCIÓN ---
class CustomUserAdmin(BaseUserAdmin):
    # Añadimos nuestra nueva acción a la lista de acciones disponibles
    actions = [force_delete_users]

# --- 3. TUS CLASES DE ADMIN EXISTENTES (SIN CAMBIOS) ---
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

# --- 4. REGISTRO DE TODOS LOS MODELOS EN EL ADMIN ---
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Oposicion)
admin.site.register(Tema)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
