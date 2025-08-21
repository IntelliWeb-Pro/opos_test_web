# tests/management/commands/import_examen_oficial.py
import csv
from pathlib import Path
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tests.models import Oposicion, Bloque, Tema, Pregunta, Respuesta


class Command(BaseCommand):
    help = "Importa preguntas de examen oficial desde un CSV en los temas especiales 'examen-oficial-b1/b2'."

    # Aliases tolerantes para cabeceras
    # La clave es el nombre canónico que usaremos en el código
    HEADER_ALIASES = {
        "Bloque": {"Bloque"},
        "Año": {"Año", "Anio", "Ano"},
        "Texto_Pregunta": {"Texto_Pregunta", "Pregunta", "Texto"},
        "Opcion_A": {"Opcion_A", "Opción_A"},
        "Opcion_B": {"Opcion_B", "Opción_B", "Oposicion_B"},  # <- typo tolerado
        "Opcion_C": {"Opcion_C", "Opción_C"},
        "Opcion_D": {"Opcion_D", "Opción_D"},
        "Respuesta_Correcta": {"Respuesta_Correcta", "Correcta"},
        "Texto_Justificacion": {"Texto_Justificacion", "Texto_Justificación"},
        "Articulo_Justificacion": {"Articulo_Justificacion", "Artículo_Justificacion", "Articulo", "Artículo"},
        "URL_Fuente_Oficial": {"URL_Fuente_Oficial", "Url_Fuente_Oficial", "URL_Fuente", "Fuente_URL"},
        "Oposicion": {"Oposicion", "Oposición"},  # no es requerida para crear pero la toleramos
        "ID_Pregunta": {"ID_Pregunta", "ID"},
        "tipo_pregunta": {"tipo_pregunta", "Tipo"},
        # cualquier otra columna extra será ignorada
    }

    REQUIRED_CANONICAL = [
        "Bloque",
        "Texto_Pregunta",
        "Opcion_A",
        "Opcion_B",
        "Opcion_C",
        "Opcion_D",
        "Respuesta_Correcta",
        "Texto_Justificacion",
        "Articulo_Justificacion",
        "URL_Fuente_Oficial",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            required=True,
            help=(
                "Ruta al CSV. Cabeceras esperadas (con tolerancia a acentos/typos): "
                "Bloque, Año, Texto_Pregunta, Opcion_A, Opcion_B, Opcion_C, Opcion_D, "
                "Respuesta_Correcta, Texto_Justificacion, Articulo_Justificacion, URL_Fuente_Oficial"
            ),
        )
        parser.add_argument(
            "--oposicion",
            required=True,
            help="Slug o nombre de la oposición de destino (p.ej. 'auxiliar-adm-estado-c2-temas').",
        )

    def resolve_oposicion(self, value: str) -> Oposicion:
        try:
            return Oposicion.objects.get(slug=value)
        except Oposicion.DoesNotExist:
            try:
                return Oposicion.objects.get(nombre__iexact=value)
            except Oposicion.DoesNotExist:
                raise CommandError(f"Oposición no encontrada: {value}")

    def get_or_create_bloque(self, oposicion: Oposicion, numero: int, nombre: str) -> Bloque:
        obj, _ = Bloque.objects.get_or_create(
            oposicion=oposicion, numero=numero,
            defaults={"nombre": nombre},
        )
        return obj

    def get_or_create_tema_especial(self, bloque: Bloque, numero: int, slug: str, nombre: str) -> Tema:
        obj, _ = Tema.objects.get_or_create(
            bloque=bloque, slug=slug,
            defaults={
                "numero": numero,
                "nombre_oficial": nombre,
                "es_premium": True,
            }
        )
        return obj

    # ---- Helpers de normalización ----

    @staticmethod
    def _strip_bom(s: str) -> str:
        if not isinstance(s, str):
            return s
        return s.lstrip("\ufeff").strip()

    def _make_name_map(self, fieldnames):
        """
        Devuelve un dict {canonical: actual_en_csv} usando HEADER_ALIASES.
        Ignora columnas no conocidas.
        """
        # normalizamos por si hay BOM
        normalized = {self._strip_bom(fn): fn for fn in fieldnames}
        name_map = {}
        for canonical, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                if alias in normalized:
                    name_map[canonical] = normalized[alias]
                    break
        return name_map

    @staticmethod
    def _parse_bloque(value: str) -> int:
        """
        Acepta '1', '2', 'Bloque 1', 'Bloque I', 'I', 'II' y devuelve 1 o 2 (por defecto 1).
        """
        if not value:
            return 1
        v = value.strip().upper()
        # Números directos
        if v.isdigit():
            try:
                n = int(v)
                return 2 if n == 2 else 1
            except ValueError:
                return 1
        # 'Bloque 1', 'Bloque 2'
        m = re.search(r"(\d+)", v)
        if m:
            return 2 if m.group(1) == "2" else 1
        # Romanos: I/II
        if "II" in v:
            return 2
        if "I" in v:
            return 1
        return 1

    def handle(self, *args, **opts):
        csv_path = Path(opts["csv"])
        if not csv_path.exists():
            raise CommandError(f"No existe el fichero: {csv_path}")

        oposicion = self.resolve_oposicion(opts["oposicion"])
        self.stdout.write(self.style.NOTICE(f"→ Oposición: {oposicion.nombre} ({oposicion.slug})"))

        # Bloques y temas especiales
        bloque1 = self.get_or_create_bloque(oposicion, 1, "Bloque 1")
        bloque2 = self.get_or_create_bloque(oposicion, 2, "Bloque 2")
        tema_b1 = self.get_or_create_tema_especial(bloque1, 99901, "examen-oficial-b1", "Examen oficial – Bloque 1")
        tema_b2 = self.get_or_create_tema_especial(bloque2, 99902, "examen-oficial-b2", "Examen oficial – Bloque 2")

        # Evitar duplicados por texto (separado por tema)
        existentes_b1 = set(Pregunta.objects.filter(tema=tema_b1).values_list("texto_pregunta", flat=True))
        existentes_b2 = set(Pregunta.objects.filter(tema=tema_b2).values_list("texto_pregunta", flat=True))

        creadas = 0
        saltadas = 0
        errores = 0
        creadas_b1 = 0
        creadas_b2 = 0

        # Abrimos con utf-8-sig para limpiar BOM
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise CommandError("El CSV no tiene cabeceras.")

            # Mapa canónico -> nombre real en el CSV
            name_map = self._make_name_map(reader.fieldnames)

            # Comprobamos requeridos (si alguno no está mapeado, fallamos)
            missing = [k for k in self.REQUIRED_CANONICAL if k not in name_map]
            if missing:
                raise CommandError(f"Faltan columnas en el CSV: {', '.join(missing)}")

            for i, raw_row in enumerate(reader, start=2):  # línea 2 = primera fila tras cabecera
                try:
                    # Normalizamos claves (por si el DictReader trae BOM en la primera)
                    row = {self._strip_bom(k): v for k, v in raw_row.items()}

                    bloque_raw = (row.get(name_map["Bloque"]) or "").strip()
                    bloque_val = self._parse_bloque(bloque_raw)

                    texto = (row.get(name_map["Texto_Pregunta"]) or "").strip()
                    if not texto:
                        saltadas += 1
                        continue

                    # Tema destino
                    if bloque_val == 2:
                        tema = tema_b2
                        existentes = existentes_b2
                    else:
                        tema = tema_b1
                        existentes = existentes_b1

                    if texto in existentes:
                        saltadas += 1
                        continue

                    anio = (row.get(name_map.get("Año", ""), "") or "").strip()
                    fuente = f"Examen oficial {anio}".strip() if anio else "Examen oficial"

                    # Opciones
                    a = (row.get(name_map["Opcion_A"]) or "").strip()
                    b = (row.get(name_map["Opcion_B"]) or "").strip()
                    c = (row.get(name_map["Opcion_C"]) or "").strip()
                    d = (row.get(name_map["Opcion_D"]) or "").strip()
                    correct = (row.get(name_map["Respuesta_Correcta"]) or "").strip().upper()[:1]  # 'A','B','C','D'

                    just_text = (row.get(name_map["Texto_Justificacion"]) or "").strip()
                    just_art = (row.get(name_map["Articulo_Justificacion"]) or "").strip()
                    just_url = (row.get(name_map["URL_Fuente_Oficial"]) or "").strip()

                    opciones = {
                        "A": a,
                        "B": b,
                        "C": c,
                        "D": d,
                    }

                    # Validaciones mínimas
                    if correct not in opciones:
                        self.stderr.write(f"[L{i}] Respuesta_Correcta '{correct}' inválida; se espera A/B/C/D. Saltada.")
                        saltadas += 1
                        continue
                    if not opciones.get(correct):
                        self.stderr.write(f"[L{i}] La opción correcta '{correct}' está vacía. Saltada.")
                        saltadas += 1
                        continue

                    # Crear pregunta + respuestas
                    with transaction.atomic():
                        pregunta = Pregunta.objects.create(
                            tema=tema,
                            texto_pregunta=texto,
                            fuente_original=fuente,
                        )

                        for key in ("A", "B", "C", "D"):
                            texto_resp = (opciones.get(key) or "").strip()
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
                    if bloque_val == 2:
                        creadas_b2 += 1
                    else:
                        creadas_b1 += 1

                except Exception as e:
                    errores += 1
                    self.stderr.write(f"[L{i}] Error importando: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"✔ Importación finalizada. Creadas: {creadas} "
            f"(B1: {creadas_b1} · B2: {creadas_b2}) · Saltadas: {saltadas} · Errores: {errores}"
        ))
