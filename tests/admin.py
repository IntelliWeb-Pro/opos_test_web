# tests/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Oposicion, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, Post, Suscripcion

# --- 1. ACCIÓN DE BORRADO FORZADO ---
@admin.action(description="Forzar borrado de usuarios seleccionados (y sus datos)")
def force_delete_users(modeladmin, request, queryset):
    """
    Acción que borra usuarios y sus datos relacionados de forma controlada
    para evitar timeouts en el servidor.
    """
    deleted_count = 0
    for user in queryset:
        try:
            # Borramos el usuario. on_delete=CASCADE se encargará del resto.
            user.delete()
            deleted_count += 1
        except Exception as e:
            modeladmin.message_user(request, f"Error al borrar al usuario {user.username}: {e}", messages.ERROR)
    
    if deleted_count > 0:
        modeladmin.message_user(request, f"{deleted_count} usuarios han sido borrados con éxito.", messages.SUCCESS)

# --- 2. ADMIN PERSONALIZADO PARA USER CON LA NUEVA ACCIÓN ---
class CustomUserAdmin(BaseUserAdmin):
    actions = [force_delete_users]

# --- 3. CLASES DE ADMIN PARA LA NUEVA ESTRUCTURA DE TEMAS ---
class TemaAdmin(admin.ModelAdmin):
    # --- CAMBIOS REALIZADOS AQUÍ ---
    list_display = ('numero', 'nombre_oficial', 'bloque', 'get_oposicion', 'es_premium')
    list_editable = ('es_premium',) # Permite editar el campo 'es_premium' desde la lista
    list_filter = ('bloque__oposicion', 'bloque', 'es_premium') # Añade filtro por estado premium
    search_fields = ('nombre_oficial',)
    list_display_links = ('nombre_oficial',)

    @admin.display(description='Oposición', ordering='bloque__oposicion')
    def get_oposicion(self, obj):
        return obj.bloque.oposicion

class BloqueAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'oposicion')
    list_filter = ('oposicion',)
    search_fields = ('nombre',)

# --- 4. TUS OTRAS CLASES DE ADMIN (SIN CAMBIOS) ---
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

# --- 5. REGISTRO DE TODOS LOS MODELOS EN EL ADMIN ---
# Para el modelo User, damos de baja el admin por defecto y registramos el nuestro
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Registramos el resto de modelos con sus configuraciones personalizadas
admin.site.register(Oposicion)
admin.site.register(Bloque, BloqueAdmin)
admin.site.register(Tema, TemaAdmin)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
