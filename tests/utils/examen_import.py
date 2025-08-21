# tests/utils/examen_import.py
import csv
import io
from pathlib import Path
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from tests.models import Oposicion, Bloque, Tema, Pregunta, Respuesta

def _resolve_oposicion(value: str) -> Oposicion:
    try:
        return Oposicion.objects.get(slug=value)
    except ObjectDoesNotExist:
        try:
            return Oposicion.objects.get(nombre__iexact=value)
        except ObjectDoesNotExist:
            raise ValueError(f"Oposición no encontrada: {value}")

def _get_or_create_bloque(oposicion: Oposicion, numero: int, nombre: str) -> Bloque:
    obj, _ = Bloque.objects.get_or_create(
        oposicion=oposicion, numero=numero,
        defaults={"nombre": nombre},
    )
    return obj

def _get_or_create_tema_especial(bloque: Bloque, numero: int, slug: str, nombre: str) -> Tema:
    obj, _ = Tema.objects.get_or_create(
        bloque=bloque, slug=slug,
        defaults={"numero": numero, "nombre_oficial": nombre, "es_premium": True}
    )
    return obj

def import_examen_oficial(file_obj, oposicion_value: str) -> dict:
    """
    file_obj: UploadedFile / file-like (bytes). CSV con cabeceras:
      ID_Pregunta,Año,Oposicion,Bloque,Texto_Pregunta,
      Opcion_A,Opcion_B/Oposicion_B,Opcion_C,Opcion_D,
      Respuesta_Correcta,Articulo_Justificacion,Texto_Justificacion,URL_Fuente_Oficial
    oposicion_value: slug o nombre de la Oposición destino
    """
    oposicion = _resolve_oposicion(oposicion_value)

    bloque1 = _get_or_create_bloque(oposicion, 1, "Bloque 1")
    bloque2 = _get_or_create_bloque(oposicion, 2, "Bloque 2")
    tema_b1 = _get_or_create_tema_especial(bloque1, 99901, "examen-oficial-b1", "Examen oficial – Bloque 1")
    tema_b2 = _get_or_create_tema_especial(bloque2, 99902, "examen-oficial-b2", "Examen oficial – Bloque 2")

    existentes_b1 = set(Pregunta.objects.filter(tema=tema_b1).values_list("texto_pregunta", flat=True))
    existentes_b2 = set(Pregunta.objects.filter(tema=tema_b2).values_list("texto_pregunta", flat=True))

    creadas = 0
    saltadas = 0
    errores = 0
    errores_detalle = []

    # Asegura lectura texto
    if hasattr(file_obj, "read"):
        text_stream = io.TextIOWrapper(file_obj, encoding="utf-8", newline="")
    else:
        # por si pasaran una ruta de archivo (no necesario desde API)
        text_stream = open(Path(file_obj), newline="", encoding="utf-8")

    with text_stream as fh:
        reader = csv.DictReader(fh)
        has_opcion_b = "Opcion_B" in reader.fieldnames
        has_oposicion_b_typo = "Oposicion_B" in reader.fieldnames

        required = [
            "Bloque", "Texto_Pregunta", "Opcion_A", "Opcion_C", "Opcion_D",
            "Respuesta_Correcta", "Texto_Justificacion", "Articulo_Justificacion",
            "URL_Fuente_Oficial"
        ]
        missing = [k for k in required if k not in reader.fieldnames]
        if missing:
            raise ValueError(f"Faltan columnas en el CSV: {', '.join(missing)}")

        for i, row in enumerate(reader, start=2):
            try:
                bloque_val_raw = (row.get("Bloque") or "").strip()
                bloque_val = int(bloque_val_raw) if bloque_val_raw else 1
                texto = (row.get("Texto_Pregunta") or "").strip()
                if not texto:
                    saltadas += 1
                    continue

                if bloque_val == 2:
                    tema = tema_b2
                    existentes = existentes_b2
                else:
                    tema = tema_b1
                    existentes = existentes_b1

                if texto in existentes:
                    saltadas += 1
                    continue

                anio = (row.get("Año") or "").strip()
                fuente = f"Examen oficial {anio}".strip() if anio else "Examen oficial"

                with transaction.atomic():
                    pregunta = Pregunta.objects.create(
                        tema=tema,
                        texto_pregunta=texto,
                        fuente_original=fuente,
                    )
                    a = (row.get("Opcion_A") or "").strip()
                    b = (row.get("Opcion_B") or (row.get("Oposicion_B") or "")).strip() if has_opcion_b or has_oposicion_b_typo else ""
                    c = (row.get("Opcion_C") or "").strip()
                    d = (row.get("Opcion_D") or "").strip()
                    correct = (row.get("Respuesta_Correcta") or "").strip().upper()[:1]

                    just_text = (row.get("Texto_Justificacion") or "").strip()
                    just_art = (row.get("Articulo_Justificacion") or "").strip()
                    just_url = (row.get("URL_Fuente_Oficial") or "").strip()

                    opciones = [("A", a), ("B", b), ("C", c), ("D", d)]
                    for key, texto_resp in opciones:
                        if not texto_resp:
                            continue
                        Respuesta.objects.create(
                            pregunta=pregunta,
                            texto_respuesta=texto_resp,
                            es_correcta=(key == correct),
                            texto_justificacion=just_text if key == correct else "",
                            articulo_justificacion=just_art if key == correct else "",
                            url_fuente_oficial=just_url if key == correct else "",
                        )

                existentes.add(texto)
                creadas += 1

            except Exception as e:
                errores += 1
                errores_detalle.append({"linea": i, "error": str(e)})

    return {
        "oposicion": {"slug": oposicion.slug, "nombre": oposicion.nombre},
        "creadas": creadas, "saltadas": saltadas, "errores": errores,
        "errores_detalle": errores_detalle[:50],  # cap
    }
