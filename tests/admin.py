# tests/admin.py
import csv, io
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Oposicion, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, Post, Suscripcion, TestSession
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, render, redirect
from django import forms
from django.db import transaction
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

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

class ExamenCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Archivo CSV",
        help_text=(
            "Cabeceras: ID_Pregunta, Año, Oposicion, Bloque, Texto_Pregunta, "
            "Opcion_A, Opcion_B (o 'Oposicion_B'), Opcion_C, Opcion_D, "
            "Respuesta_Correcta, Articulo_Justificacion, Texto_Justificacion, URL_Fuente_Oficial"
        ),
    )


@admin.register(Oposicion)
class OposicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    search_fields = ("nombre", "slug")
    actions = ["importar_examen_oficial_action"]

    # Acción de admin: abrir formulario / procesar CSV
    def importar_examen_oficial_action(self, request, queryset):
        """
        Uso:
          1) Admin -> Tests -> Oposiciones
          2) Marca EXACTAMENTE una oposición
          3) Acción: "Importar examen oficial (CSV)" -> "Ir"
          4) Sube el CSV y pulsa "Importar"
        """
        if request.method == "POST" and "apply" in request.POST:
            # Procesar subida
            ids = request.POST.getlist("_selected_action")
            if len(ids) != 1:
                self.message_user(request, "Selecciona exactamente una oposición.", level=messages.ERROR)
                return redirect(request.path)
            oposicion = Oposicion.objects.get(pk=ids[0])

            form = ExamenCSVUploadForm(request.POST, request.FILES)
            if not form.is_valid():
                context = {"form": form, "title": f"Importar examen oficial en {oposicion.nombre}", "ids": ids}
                return render(request, "admin/tests/oposicion/import_examen.html", context)

            # leer CSV en texto
            f = form.cleaned_data["csv_file"]
            fh = io.TextIOWrapper(f.file, encoding="utf-8")
            reader = csv.DictReader(fh)

            # soporte del typo 'Oposicion_B'
            has_opcion_b = "Opcion_B" in reader.fieldnames
            has_oposicion_b_typo = "Oposicion_B" in reader.fieldnames

            required = [
                "Bloque", "Texto_Pregunta", "Opcion_A", "Opcion_C", "Opcion_D",
                "Respuesta_Correcta", "Texto_Justificacion", "Articulo_Justificacion",
                "URL_Fuente_Oficial"
            ]
            missing = [k for k in required if k not in reader.fieldnames]
            if missing:
                self.message_user(request, f"Faltan columnas: {', '.join(missing)}", level=messages.ERROR)
                return redirect(request.get_full_path())

            # Asegurar bloques 1/2 y temas especiales
            bloque1, _ = Bloque.objects.get_or_create(oposicion=oposicion, numero=1, defaults={"nombre": "Bloque 1"})
            bloque2, _ = Bloque.objects.get_or_create(oposicion=oposicion, numero=2, defaults={"nombre": "Bloque 2"})
            tema_b1, _ = Tema.objects.get_or_create(
                bloque=bloque1, slug="examen-oficial-b1",
                defaults={"numero": 99901, "nombre_oficial": "Examen oficial – Bloque 1", "es_premium": True},
            )
            tema_b2, _ = Tema.objects.get_or_create(
                bloque=bloque2, slug="examen-oficial-b2",
                defaults={"numero": 99902, "nombre_oficial": "Examen oficial – Bloque 2", "es_premium": True},
            )

            existentes_b1 = set(Pregunta.objects.filter(tema=tema_b1).values_list("texto_pregunta", flat=True))
            existentes_b2 = set(Pregunta.objects.filter(tema=tema_b2).values_list("texto_pregunta", flat=True))

            creadas = saltadas = errores = 0

            for i, row in enumerate(reader, start=2):
                try:
                    bloque_val_raw = (row.get("Bloque") or "").strip()
                    bloque_val = int(bloque_val_raw) if bloque_val_raw else 1
                    texto = (row.get("Texto_Pregunta") or "").strip()
                    if not texto:
                        saltadas += 1
                        continue

                    tema = tema_b2 if bloque_val == 2 else tema_b1
                    existentes = existentes_b2 if bloque_val == 2 else existentes_b1
                    if texto in existentes:
                        saltadas += 1
                        continue

                    anio = (row.get("Año") or "").strip()
                    fuente = f"Examen oficial {anio}".strip() if anio else "Examen oficial"

                    a = (row.get("Opcion_A") or "").strip()
                    b = (row.get("Opcion_B") or (row.get("Oposicion_B") or "")).strip() if has_opcion_b or has_oposicion_b_typo else ""
                    c = (row.get("Opcion_C") or "").strip()
                    d = (row.get("Opcion_D") or "").strip()
                    correct = (row.get("Respuesta_Correcta") or "").strip().upper()[:1]  # 'A'/'B'/'C'/'D'

                    just_text = (row.get("Texto_Justificacion") or "").strip()
                    just_art = (row.get("Articulo_Justificacion") or "").strip()
                    just_url = (row.get("URL_Fuente_Oficial") or "").strip()

                    with transaction.atomic():
                        p = Pregunta.objects.create(
                            tema=tema,
                            texto_pregunta=texto,
                            fuente_original=fuente,
                        )
                        for key, text in [("A", a), ("B", b), ("C", c), ("D", d)]:
                            if not text:
                                continue
                            Respuesta.objects.create(
                                pregunta=p,
                                texto_respuesta=text,
                                es_correcta=(key == correct),
                                texto_justificacion=just_text if key == correct else "",
                                articulo_justificacion=just_art if key == correct else "",
                                url_fuente_oficial=just_url if key == correct else "",
                            )

                    existentes.add(texto)
                    creadas += 1
                except Exception as e:
                    errores += 1

            self.message_user(
                request,
                f"Importación completada: creadas {creadas}, saltadas {saltadas}, errores {errores}.",
                level=messages.SUCCESS,
            )
            return redirect("..")  # volver al listado

        else:
            # Mostrar formulario
            selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
            if len(selected) != 1:
                self.message_user(request, "Selecciona exactamente una oposición.", level=messages.ERROR)
                return redirect(request.path)

            oposicion = queryset.get(pk=selected[0])
            form = ExamenCSVUploadForm()
            context = {"form": form, "title": f"Importar examen oficial en {oposicion.nombre}", "ids": selected}
            return render(request, "admin/tests/oposicion/import_examen.html", context)

    importar_examen_oficial_action.short_description = "Importar examen oficial (CSV)"
# --- 5. REGISTRO DE TODOS LOS MODELOS EN EL ADMIN ---
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# --- LÍNEA MODIFICADA ---
# Ahora registramos Oposicion usando nuestra nueva clase personalizada
admin.site.register(Bloque, BloqueAdmin)
admin.site.register(Tema, TemaAdmin)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
