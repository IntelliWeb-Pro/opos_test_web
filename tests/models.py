# tests/models.py

from django.db import models

class Oposicion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

class Tema(models.Model):
    nombre = models.CharField(max_length=255)
    oposicion = models.ForeignKey(Oposicion, on_delete=models.CASCADE, related_name='temas')

    def __str__(self):
        return f"{self.oposicion.nombre} - {self.nombre}"

class Pregunta(models.Model):
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.TextField()
    fuente_original = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        # Devuelve los primeros 80 caracteres de la pregunta para una vista previa
        return self.texto_pregunta[:80] + '...'

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    texto_respuesta = models.CharField(max_length=1000)
    es_correcta = models.BooleanField(default=False)
    texto_justificacion = models.TextField()
    fuente_justificacion = models.CharField(max_length=255)
    url_fuente_oficial = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.texto_respuesta[:80]

        # tests/models.py (Añadir al final)

from django.conf import settings # Asegúrate de que esta línea esté al principio del archivo

class ResultadoTest(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    total_preguntas = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test de {self.usuario.username} en {self.tema.nombre} - {self.puntuacion}/{self.total_preguntas}"

    class Meta:
        ordering = ['-fecha']


# tests/models.py (Añadir al final)

class Suscripcion(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario.username} - {'Activa' if self.activa else 'Inactiva'}"