# tests/management/commands/import_questions.py

import csv
from django.core.management.base import BaseCommand
from tests.models import Oposicion, Bloque, Tema, Pregunta, Respuesta

class Command(BaseCommand):
    help = 'Importa preguntas desde un archivo CSV con el nuevo formato.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='La ruta al archivo CSV que se va a importar.')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        self.stdout.write(self.style.SUCCESS(f'Iniciando importación desde "{csv_file_path}"...'))

        # Borra todas las preguntas y respuestas antiguas para evitar duplicados
        self.stdout.write('Borrando datos antiguos...')
        Pregunta.objects.all().delete()
        Respuesta.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Datos antiguos eliminados.'))

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    try:
                        # 1. Obtener o crear la Oposición
                        oposicion, _ = Oposicion.objects.get_or_create(nombre=row['Oposicion'])

                        # 2. Obtener o crear el Bloque
                        bloque, _ = Bloque.objects.get_or_create(
                            oposicion=oposicion,
                            numero=int(row['Bloque_Num']),
                            defaults={'nombre': row['Bloque_Nombre']}
                        )

                        # 3. Obtener o crear el Tema
                        tema, _ = Tema.objects.get_or_create(
                            bloque=bloque,
                            numero=int(row['Tema_Num']),
                            defaults={'nombre_oficial': row['Tema_Oficial']}
                        )

                        # 4. Crear la Pregunta
                        pregunta = Pregunta.objects.create(
                            tema=tema,
                            texto_pregunta=row['Texto_Pregunta'],
                            fuente_original=row['Fuente_Original']
                        )

                        # 5. Crear las Respuestas
                        opciones = ['A', 'B', 'C', 'D']
                        for opcion in opciones:
                            es_correcta = (row['Respuesta_Correcta'] == opcion)
                            Respuesta.objects.create(
                                pregunta=pregunta,
                                texto_respuesta=row[f'Opcion_{opcion}'],
                                es_correcta=es_correcta,
                                texto_justificacion=row['Texto_Justificacion'],
                                articulo_justificacion=row['Articulo_Justificacion'],
                                url_fuente_oficial=row['URL_Fuente_Oficial']
                            )

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error procesando la fila con ID {row.get('ID_Pregunta', 'N/A')}: {e}"))

            self.stdout.write(self.style.SUCCESS('¡Importación completada con éxito!'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Error: El archivo "{csv_file_path}" no fue encontrado.'))
