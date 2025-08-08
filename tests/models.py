# tests/models.py

from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Oposicion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    # --- CAMPO SLUG AÑADIDO ---
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Bloque(models.Model):
    numero = models.IntegerField()
    nombre = models.CharField(max_length=255)
    oposicion = models.ForeignKey(Oposicion, on_delete=models.CASCADE, related_name='bloques')

    class Meta:
        unique_together = ('oposicion', 'numero')
        ordering = ['numero']

    def __str__(self):
        return f"Bloque {self.numero}: {self.nombre} ({self.oposicion.nombre})"

class Tema(models.Model):
    # --- CAMBIO CLAVE: Se añade un valor por defecto para permitir la migración ---
    numero = models.IntegerField(default=0)
    nombre_oficial = models.CharField(max_length=500, null=True)
    bloque = models.ForeignKey(Bloque, on_delete=models.CASCADE, related_name='temas', null=True)
    url_fuente_oficial = models.URLField(blank=True, null=True)
    
    class Meta:
        unique_together = ('bloque', 'numero')
        ordering = ['numero']

    def __str__(self):
        return f"Tema {self.numero}: {self.nombre_oficial}"

class Pregunta(models.Model):
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.TextField()
    fuente_original = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.texto_pregunta[:80] + '...'

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    texto_respuesta = models.CharField(max_length=1000)
    es_correcta = models.BooleanField(default=False)
    texto_justificacion = models.TextField()
    articulo_justificacion = models.CharField(max_length=255, blank=True, null=True)
    url_fuente_oficial = models.URLField(blank=True, null=True)
    def __str__(self):
        return self.texto_respuesta[:80]

class Suscripcion(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.usuario.username} - {'Activa' if self.activa else 'Inactiva'}"

class ResultadoTest(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    total_preguntas = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Test de {self.usuario.username} en {self.tema.nombre_oficial} - {self.puntuacion}/{self.total_preguntas}"
    class Meta:
        ordering = ['-fecha']

class Post(models.Model):
    ESTADOS = (('borrador', 'Borrador'), ('publicado', 'Publicado'))
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, help_text="Versión del título amigable para la URL, sin espacios ni acentos.")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenido = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='borrador')
    
    class Meta:
        ordering = ['-creado_en']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.titulo

class CodigoVerificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Código para {self.usuario.username}"
