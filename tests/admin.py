# tests/admin.py
import csv
import io
import logging
import unicodedata

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.shortcuts import render, redirect
from django import forms
from django.db import transaction
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.utils.text import slugify

from .models import (
    Oposicion, Bloque, Tema, Pregunta, Respuesta,
    ResultadoTest, Post, Suscripcion, TestSession
)

logger = logging.getLogger(__name__)

# -----------------------------
# 1) ACCIÓN: borrado forzado
# -----------------------------
@admin.action(description="Forzar borrado de usuarios seleccionados (y sus datos)")
def force_delete_users(modeladmin, request, queryset):
    borrados = 0
    for user in queryset:
        try:
            user.delete()
            borrados += 1
        except Exception as e:
            modeladmin.message_user(
                request, f"Error al borrar {user.username}: {e}", messages.ERROR
            )
    if borrados:
        modeladmin.message_user(
            request, f"{borrados} usuario(s) borrado(s) con éxito.", messages.SUCCESS
        )

class CustomUserAdmin(BaseUserAdmin):
    actions = [force_delete_users]


# -----------------------------
# 2) Admins de Temas/Bloques
# -----------------------------
class TemaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre_oficial', 'slug', 'bloque', 'get_oposicion', 'es_premium')
    list_editable = ('es_premium',)
    list_filter = ('bloque__oposicion', 'bloque', 'es_premium')
    search_fields = ('nombre_oficial', 'slug')
    list_display_links = ('nombre_oficial',)
    prepopulated_fields = {'slug': ('nombre_oficial',)}
    ordering = ('bloque', 'numero')

    @admin.display(description='Oposición', ordering='bloque__oposicion')
    def get_oposicion(self, obj):
        return obj.bloque.oposicion

    def save_model(self, request, obj, form, change):
        if not obj.slug and obj.nombre_oficial:
            base = f"{obj.numero}-{obj.nombre_oficial}" if getattr(obj, "numero", None) else obj.nombre_oficial
            obj.slug = slugify(base)
        super().save_model(request, obj, form, change)

class BloqueAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'oposicion')
    list_filter = ('oposicion',)
    search_fields = ('nombre',)


# -----------------------------
# 3) Otros admins
# -----------------------------
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'autor', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('titulo', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}

class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'stripe_customer_id', 'activa')
    list_filter = ('activa',)
    search_fields = ('usuario__username', 'stripe_customer_id')

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tipo", "estado", "updated_at")
    list_filter = ("tipo", "estado")
    search_fields = ("id", "user__email", "user__username")


# -----------------------------
# 4) Formulario subida CSV
# -----------------------------
class ExamenCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Archivo CSV",
        help_text=(
            "Cabeceras (variantes aceptadas): "
            "ID_Pregunta, Año, Oposicion, Bloque, Texto_Pregunta, "
            "Opcion_A, Opcion_B (o 'Oposicion_B' / 'Opcion_B/Oposicion_B'), "
            "Opcion_C, Opcion_D, Respuesta_Correcta, "
            "Articulo_Justificacion, Texto_Justificacion, URL_Fuente_Oficial"
        ),
    )


# ============================================================
# 5) OposicionAdmin con acción de importar examen oficial CSV
#    (robusto a encoding, delimitador y nombres de cabecera)
# ============================================================
def _norm(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip().lower().replace(" ", "_")

@admin.register(Oposicion)
class OposicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    search_fields = ("nombre", "slug")
    actions = ["importar_examen_oficial_action"]
    # Conservamos los fieldsets y slug autogenerado aquí:
    fieldsets = (
        ('Información Básica', {'fields': ('nombre', 'slug')}),
        ('Contenido de la Guía', {
            'fields': ('descripcion_general', 'info_convocatoria', 'url_boe', 'requisitos', 'info_adicional'),
            'description': 'Información mostrada en la página de la oposición.'
        }),
    )
    prepopulated_fields = {'slug': ('nombre',)}

    def importar_examen_oficial_action(self, request, queryset):
        """
        Uso:
          1) Admin -> Tests -> Oposiciones
          2) Marca EXACTAMENTE una oposición
          3) Acción: "Importar examen oficial (CSV)" -> "Ir"
          4) Sube el CSV y pulsa "Importar"
        """
        # Mostrar formulario si no estamos aplicando
        if not (request.method == "POST" and "apply" in request.POST):
            seleccion = request.POST.getlist(ACTION_CHECKBOX_NAME)
            if len(seleccion) != 1:
                self.message_user(request, "Selecciona exactamente una oposición.", level=messages.ERROR)
                return redirect(request.path)
            oposicion = queryset.get(pk=seleccion[0])
            form = ExamenCSVUploadForm()
            ctx = {"form": form, "title": f"Importar examen oficial en {oposicion.nombre}", "ids": seleccion}
            return render(request, "admin/tests/oposicion/import_examen.html", ctx)

        # Procesar import
        ids = request.POST.getlist("_selected_action")
        if len(ids) != 1:
            self.message_user(request, "Selecciona exactamente una oposición.", level=messages.ERROR)
            return redirect(request.path)
        oposicion = Oposicion.objects.get(pk=ids[0])

        form = ExamenCSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            ctx = {"form": form, "title": f"Importar examen oficial en {oposicion.nombre}", "ids": ids}
            return render(request, "admin/tests/oposicion/import_examen.html", ctx)

        # ---- Lectura robusta del CSV ----
        upload = form.cleaned_data["csv_file"]
        raw = upload.read()
        # Encoding
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        # Delimitador
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        except Exception:
            dialect = csv.excel
            dialect.delimiter = ","
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)

        if not reader.fieldnames:
            self.message_user(request, "El CSV no tiene cabecera legible.", level=messages.ERROR)
            return redirect("..")

        # Mapa de cabeceras normalizadas -> reales
        header_map = {_norm(h): h for h in reader.fieldnames}

        def pick(*candidatos):
            for cand in candidatos:
                key = _norm(cand)
                if key in header_map:
                    return header_map[key]
            return None

        REQ = {
            "bloque": ("Bloque",),
            "texto_pregunta": ("Texto_Pregunta", "Pregunta", "Texto pregunta"),
            "opcion_a": ("Opcion_A", "Opción_A", "Opcion A"),
            "opcion_b": ("Opcion_B", "Oposicion_B", "Opcion_B/Oposicion_B", "Opción_B", "Opcion B"),
            "opcion_c": ("Opcion_C", "Opción_C", "Opcion C"),
            "opcion_d": ("Opcion_D", "Opción_D", "Opcion D"),
            "respuesta_correcta": ("Respuesta_Correcta", "Correcta", "Respuesta correcta"),
            "texto_justificacion": ("Texto_Justificacion", "Justificacion", "Texto justificacion"),
            "articulo_justificacion": ("Articulo_Justificacion", "Articulo", "Artículo"),
            "url_fuente_oficial": ("URL_Fuente_Oficial", "URL", "Fuente", "Enlace"),
            # opcional:
            "anio": ("Año", "Anio", "Ano"),
        }

        missing = [k for k, alts in REQ.items() if k != "anio" and pick(*alts) is None]
        if missing:
            self.message_user(
                request,
                "Faltan columnas requeridas en el CSV: " + ", ".join(missing),
                level=messages.ERROR
            )
            return redirect("..")

        # Asegurar Bloques y Temas especiales
        b1, _ = Bloque.objects.get_or_create(oposicion=oposicion, numero=1, defaults={"nombre": "Bloque 1"})
        b2, _ = Bloque.objects.get_or_create(oposicion=oposicion, numero=2, defaults={"nombre": "Bloque 2"})
        t1, _ = Tema.objects.get_or_create(
            bloque=b1, slug="examen-oficial-b1",
            defaults={"numero": 99901, "nombre_oficial": "Examen oficial – Bloque 1", "es_premium": True},
        )
        t2, _ = Tema.objects.get_or_create(
            bloque=b2, slug="examen-oficial-b2",
            defaults={"numero": 99902, "nombre_oficial": "Examen oficial – Bloque 2", "es_premium": True},
        )

        existentes_b1 = set(Pregunta.objects.filter(tema=t1).values_list("texto_pregunta", flat=True))
        existentes_b2 = set(Pregunta.objects.filter(tema=t2).values_list("texto_pregunta", flat=True))

        def get(row, key):
            real = pick(*REQ[key])
            return (row.get(real) or "").strip()

        creadas = saltadas = errores = 0
        muestras_error = []  # guardamos muestras (máx 10)

        fila = 1  # 1 = cabecera
        for row in reader:
            fila += 1
            try:
                bloque_raw = get(row, "bloque")
                bloque_val = 2 if "2" in bloque_raw else 1

                texto = get(row, "texto_pregunta")
                if not texto:
                    saltadas += 1
                    continue

                tema = t2 if bloque_val == 2 else t1
                existentes = existentes_b2 if bloque_val == 2 else existentes_b1
                if texto in existentes:
                    saltadas += 1
                    continue

                anio = get(row, "anio")
                fuente = f"Examen oficial {anio}".strip() if anio else "Examen oficial"

                a = get(row, "opcion_a")
                b = get(row, "opcion_b")
                c = get(row, "opcion_c")
                d = get(row, "opcion_d")

                correct = get(row, "respuesta_correcta").upper()
                # Limpiar "A)", "B." etc. y quedarnos con la letra
                if correct:
                    correct = next((ch for ch in correct if ch in "ABCD"), correct[:1])
                if correct not in {"A", "B", "C", "D"}:
                    raise ValueError(f"Respuesta_Correcta inválida: '{correct}'")

                just_text = get(row, "texto_justificacion")
                just_art  = get(row, "articulo_justificacion")
                just_url  = get(row, "url_fuente_oficial")

                # Al menos 2 opciones con texto
                if sum(bool(x) for x in (a, b, c, d)) < 2:
                    raise ValueError("Fila sin opciones suficientes (mínimo 2).")

                with transaction.atomic():
                    p = Pregunta.objects.create(
                        tema=tema,
                        texto_pregunta=texto,
                        fuente_original=fuente,
                    )
                    for key, txt in (("A", a), ("B", b), ("C", c), ("D", d)):
                        if not txt:
                            continue
                        Respuesta.objects.create(
                            pregunta=p,
                            texto_respuesta=txt[:1000],
                            es_correcta=(key == correct),
                            texto_justificacion=just_text if key == correct else "",
                            articulo_justificacion=just_art if key == correct else "",
                            url_fuente_oficial=(just_url[:500] if key == correct else ""),
                        )

                existentes.add(texto)
                creadas += 1

            except Exception as e:
                errores += 1
                logger.exception("Error importando fila %s: %s", fila, e)
                if len(muestras_error) < 10:
                    muestras_error.append(f"Fila {fila}: {e}")

        if muestras_error:
            self.message_user(
                request,
                "Muestras de errores:\n- " + "\n- ".join(muestras_error),
                level=messages.ERROR
            )

        self.message_user(
            request,
            f"Importación completada: creadas {creadas}, saltadas {saltadas}, errores {errores}.",
            level=messages.SUCCESS,
        )
        return redirect("..")

    importar_examen_oficial_action.short_description = "Importar examen oficial (CSV)"


# -----------------------------
# 6) Registro final de modelos
# -----------------------------
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Bloque, BloqueAdmin)
admin.site.register(Tema, TemaAdmin)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(ResultadoTest)
admin.site.register(Post, PostAdmin)
admin.site.register(Suscripcion, SuscripcionAdmin)
