# tests/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Oposicion, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, Post, Suscripcion, TestSession


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
    list_display = ('numero', 'nombre_oficial', 'slug', 'bloque', 'get_oposicion', 'es_premium')
    list_editable = ('es_premium',)
    list_filter = ('bloque__oposicion', 'bloque', 'es_premium')
    search_fields = ('nombre_oficial', 'slug')
    list_display_links = ('nombre_oficial',)

    # Relleno automático del slug (puedes editarlo manualmente si quieres)
    prepopulated_fields = {'slug': ('nombre_oficial',)}

    # Opcional: orden y campos visibles en el formulario
    fieldsets = (
        (None, {
            'fields': ('bloque', 'numero', 'nombre_oficial', 'slug', 'es_premium')
        }),
        ('Metadatos', {
            'fields': ('url_fuente_oficial',),
            'classes': ('collapse',),
        }),
    )
    ordering = ('bloque', 'numero')

    @admin.display(description='Oposición', ordering='bloque__oposicion')
    def get_oposicion(self, obj):
        return obj.bloque.oposicion

    def save_model(self, request, obj, form, change):
        # Si el slug viene vacío, lo generamos automáticamente
        if not obj.slug and obj.nombre_oficial:
            base = f"{obj.numero}-{obj.nombre_oficial}" if getattr(obj, "numero", None) else obj.nombre_oficial
            obj.slug = slugify(base)
        super().save_model(request, obj, form, change)

class BloqueAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'oposicion')
    list_filter = ('oposicion',)
    search_fields = ('nombre',)

# --- 4. TUS OTRAS CLASES DE ADMIN ---
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

# --- NUEVA CLASE AÑADIDA PARA GESTIONAR LA GUÍA DE OPOSICIÓN ---
class OposicionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    # Organiza los campos en el formulario de edición para que sea más claro
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug')
        }),
        ('Contenido de la Guía', {
            'fields': ('descripcion_general', 'info_convocatoria', 'url_boe', 'requisitos', 'info_adicional'),
            'description': 'Rellena aquí la información que se mostrará en la página de guía de la oposición.'
        }),
    )
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tipo", "estado", "updated_at")
    list_filter = ("tipo", "estado")
    search_fields = ("id", "user__email", "user__username")


# --- 5. REGISTRO DE TODOS LOS MODELOS EN EL ADMIN ---
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# --- LÍNEA MODIFICADA ---
# Ahora registramos Oposicion usando nuestra nueva clase personalizada
admin.site.register(Oposicion, OposicionAdmin)
admin.site.register(Bloque, BloqueAdmin)
admin.site.register(Tema, TemaAdmin)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
