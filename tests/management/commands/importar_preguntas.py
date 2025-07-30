import csv
from django.core.management.base import BaseCommand
from tests.models import Oposicion, Tema, Pregunta, Respuesta

class Command(BaseCommand):
    help = 'Importa preguntas desde un archivo CSV a la base de datos'

    def handle(self, *args, **options):
        file_path = 'preguntas.csv'
        self.stdout.write(self.style.SUCCESS(f'Iniciando importación desde {file_path}...'))

        try:
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                next(csv_reader) # Omitir cabecera

                for row in csv_reader:
                    # ... (extracción de datos igual que antes)
                    id_pregunta, fuente_original, nombre_oposicion, nombre_tema, texto_pregunta, opcion_a, opcion_b, opcion_c, opcion_d, respuesta_correcta, articulo_justificacion, texto_justificacion, url_fuente = row

                    oposicion_obj, _ = Oposicion.objects.get_or_create(nombre=nombre_oposicion)
                    
                    # --- CORRECCIÓN CLAVE ---
                    # Usamos get_or_create para el tema y luego nos aseguramos de que la URL está guardada
                    tema_obj, created = Tema.objects.get_or_create(
                        nombre=nombre_tema, 
                        oposicion=oposicion_obj
                    )
                    # Si el tema es nuevo o no tiene URL, se la añadimos/actualizamos
                    if created or not tema_obj.url_fuente_oficial:
                        tema_obj.url_fuente_oficial = url_fuente
                        tema_obj.save()

                    pregunta_obj = Pregunta.objects.create(
                        tema=tema_obj,
                        texto_pregunta=texto_pregunta,
                        fuente_original=fuente_original
                    )
                    
                    respuestas_data = [
                        {'texto': opcion_a, 'correcta': respuesta_correcta == 'A'},
                        {'texto': opcion_b, 'correcta': respuesta_correcta == 'B'},
                        {'texto': opcion_c, 'correcta': respuesta_correcta == 'C'},
                        {'texto': opcion_d, 'correcta': respuesta_correcta == 'D'},
                    ]

                    for resp_data in respuestas_data:
                        Respuesta.objects.create(
                            pregunta=pregunta_obj,
                            texto_respuesta=resp_data['texto'],
                            es_correcta=resp_data['correcta'],
                            texto_justificacion=texto_justificacion,
                            fuente_justificacion=articulo_justificacion,
                            url_fuente_oficial=url_fuente
                        )

                    line_count += 1
                    if line_count % 250 == 0:
                        self.stdout.write(f'{line_count} preguntas importadas...')

                self.stdout.write(self.style.SUCCESS(f'¡Proceso completado! Se han importado {line_count} preguntas.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Error: No se encontró el archivo preguntas.csv'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ha ocurrido un error: {e}'))
