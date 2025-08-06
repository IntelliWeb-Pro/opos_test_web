# tests/apps.py

from django.apps import AppConfig

class TestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests'

    def ready(self):
        # Importa los módulos de admin aquí para asegurar que Django los descubra.
        # Esta línea fuerza la carga de nuestro archivo admin.py.
        import tests.admin