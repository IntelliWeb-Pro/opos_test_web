# tests/management/commands/importar_preguntas.py

import csv
from django.core.management.base import BaseCommand
from tests.models import Oposicion, Tema, Pregunta, Respuesta

class Command(BaseCommand):
    help = 'Importa preguntas desde un archivo CSV a la base de datos'

    def handle(self, *args, **options):
        # Ruta al archivo CSV. Django buscará en la raíz del proyecto.
        file_path = 'preguntas.csv'
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando importación desde {file_path}...'))

        try:
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                
                # Omitimos la cabecera
                next(csv_reader)

                for row in csv_reader:
                    # Extraemos los datos de cada columna de la fila
                    id_pregunta = row[0]
                    fuente_original = row[1]
                    nombre_oposicion = row[2]
                    nombre_tema = row[3]
                    texto_pregunta = row[4]
                    opcion_a = row[5]
                    opcion_b = row[6]
                    opcion_c = row[7]
                    opcion_d = row[8]
                    respuesta_correcta = row[9]
                    articulo_justificacion = row[10]
                    texto_justificacion = row[11]
                    url_fuente = row[12]

                    # Usamos get_or_create para no duplicar datos.
                    # Busca un objeto con ese nombre, si no existe, lo crea.
                    oposicion_obj, created = Oposicion.objects.get_or_create(nombre=nombre_oposicion)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Creada nueva oposición: {nombre_oposicion}'))
                    
                    tema_obj, created = Tema.objects.get_or_create(
                        nombre=nombre_tema, 
                        oposicion=oposicion_obj
                    )
                    if created:
                        self.stdout.write(f' -> Creado nuevo tema: {nombre_tema}')

                    # Creamos la pregunta
                    pregunta_obj = Pregunta.objects.create(
                        tema=tema_obj,
                        texto_pregunta=texto_pregunta,
                        fuente_original=fuente_original
                    )
                    
                    # Creamos las respuestas asociadas a la pregunta
                    Respuesta.objects.create(
                        pregunta=pregunta_obj,
                        texto_respuesta=opcion_a,
                        es_correcta= (respuesta_correcta == 'A'),
                        texto_justificacion=texto_justificacion,
                        fuente_justificacion=articulo_justificacion,
                        url_fuente_oficial=url_fuente
                    )
                    Respuesta.objects.create(
                        pregunta=pregunta_obj,
                        texto_respuesta=opcion_b,
                        es_correcta= (respuesta_correcta == 'B'),
                        texto_justificacion=texto_justificacion,
                        fuente_justificacion=articulo_justificacion,
                        url_fuente_oficial=url_fuente
                    )
                    Respuesta.objects.create(
                        pregunta=pregunta_obj,
                        texto_respuesta=opcion_c,
                        es_correcta= (respuesta_correcta == 'C'),
                        texto_justificacion=texto_justificacion,
                        fuente_justificacion=articulo_justificacion,
                        url_fuente_oficial=url_fuente
                    )
                    Respuesta.objects.create(
                        pregunta=pregunta_obj,
                        texto_respuesta=opcion_d,
                        es_correcta= (respuesta_correcta == 'D'),
                        texto_justificacion=texto_justificacion,
                        fuente_justificacion=articulo_justificacion,
                        url_fuente_oficial=url_fuente
                    )

                    line_count += 1
                    if line_count % 100 == 0:
                        self.stdout.write(f'{line_count} preguntas importadas...')

                self.stdout.write(self.style.SUCCESS(f'¡Proceso completado! Se han importado {line_count} preguntas.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Error: No se encontró el archivo preguntas.csv en la raíz del proyecto.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ha ocurrido un error inesperado: {e}'))