#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from tests.models import Post
from django.contrib.auth import get_user_model

User = get_user_model()

# Obtener o crear usuario admin
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True}
)

# Posts de ejemplo
sample_posts = [
    {
        'titulo': '5 Consejos para Preparar tu Oposición con Éxito',
        'slug': '5-consejos-preparar-oposicion-exito',
        'contenido': '''
        <h2>Preparar una oposición requiere estrategia y constancia</h2>
        <p>Aquí tienes 5 consejos fundamentales para maximizar tus posibilidades de éxito:</p>
        <ol>
            <li><strong>Planifica tu estudio:</strong> Crea un cronograma realista y cúmplelo.</li>
            <li><strong>Practica con tests:</strong> Los simulacros son clave para familiarizarte con el formato.</li>
            <li><strong>Repasa tus errores:</strong> Analiza las preguntas falladas para no repetir errores.</li>
            <li><strong>Mantén la motivación:</strong> Recuerda tu objetivo y celebra los pequeños logros.</li>
            <li><strong>Cuida tu salud:</strong> Descansa bien y mantén una alimentación equilibrada.</li>
        </ol>
        <p>¡Con constancia y la estrategia correcta, conseguirás tu plaza!</p>
        '''
    },
    {
        'titulo': 'Cómo Gestionar el Estrés Durante la Preparación de Oposiciones',
        'slug': 'gestionar-estres-preparacion-oposiciones',
        'contenido': '''
        <h2>El estrés es normal, pero se puede controlar</h2>
        <p>La preparación de oposiciones puede generar ansiedad. Te damos algunas técnicas para gestionarla:</p>
        <h3>Técnicas de relajación</h3>
        <ul>
            <li>Respiración profunda y meditación</li>
            <li>Ejercicio físico regular</li>
            <li>Técnicas de mindfulness</li>
        </ul>
        <h3>Organización del tiempo</h3>
        <p>Una buena planificación reduce la sensación de agobio. Divide el temario en bloques manejables y establece metas semanales.</p>
        <p>Recuerda: es un maratón, no un sprint. La constancia es más importante que la intensidad.</p>
        '''
    },
    {
        'titulo': 'Novedades en las Convocatorias de Oposiciones 2024',
        'slug': 'novedades-convocatorias-oposiciones-2024',
        'contenido': '''
        <h2>Mantente actualizado con las últimas convocatorias</h2>
        <p>El año 2024 trae importantes novedades en el mundo de las oposiciones:</p>
        <h3>Principales cambios</h3>
        <ul>
            <li>Digitalización de procesos selectivos</li>
            <li>Nuevos temarios actualizados</li>
            <li>Cambios en los sistemas de puntuación</li>
            <li>Mayor peso de las competencias digitales</li>
        </ul>
        <h3>Consejos para adaptarse</h3>
        <p>Es fundamental mantenerse informado de los cambios normativos y adaptar la preparación a las nuevas exigencias.</p>
        <p>En TestEstado actualizamos constantemente nuestro contenido para reflejar estos cambios.</p>
        '''
    }
]

# Crear los posts si no existen
for post_data in sample_posts:
    post, created = Post.objects.get_or_create(
        slug=post_data['slug'],
        defaults={
            'titulo': post_data['titulo'],
            'autor': admin_user,
            'contenido': post_data['contenido'],
            'estado': 'publicado'
        }
    )
    if created:
        print(f'Post creado: {post.titulo}')
    else:
        print(f'Post ya existe: {post.titulo}')

print(f'Total de posts en la base de datos: {Post.objects.count()}')