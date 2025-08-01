#!/usr/bin/env python
"""
Script para arreglar problemas del blog y asegurar que funciona en producción
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from tests.models import Post
from django.utils.text import slugify

def fix_blog():
    print("🔧 ARREGLANDO FUNCIONALIDAD DEL BLOG")
    
    # 1. Verificar y crear usuario admin
    User = get_user_model()
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@testestado.es',
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Admin',
            'last_name': 'TestEstado'
        }
    )
    
    if created:
        admin_user.set_password('admin123')  # Solo para desarrollo
        admin_user.save()
        print("✅ Usuario admin creado")
    else:
        print("✅ Usuario admin ya existe")
    
    # 2. Verificar y arreglar slugs de posts existentes
    posts_sin_slug = Post.objects.filter(slug__isnull=True) | Post.objects.filter(slug='')
    for post in posts_sin_slug:
        post.slug = slugify(post.titulo)
        post.save()
        print(f"✅ Slug arreglado para: {post.titulo}")
    
    # 3. Crear posts de ejemplo si no hay ninguno publicado
    posts_publicados = Post.objects.filter(estado='publicado')
    if posts_publicados.count() == 0:
        posts_ejemplo = [
            {
                'titulo': 'Bienvenido al Blog de TestEstado',
                'slug': 'bienvenido-blog-testestado',
                'contenido': '''
                <h2>¡Bienvenido a nuestro blog!</h2>
                <p>Este es el lugar donde encontrarás los mejores consejos, trucos y estrategias para preparar tus oposiciones.</p>
                <p>Nuestro equipo de expertos comparte regularmente contenido de calidad para ayudarte a alcanzar tus objetivos.</p>
                <h3>¿Qué encontrarás aquí?</h3>
                <ul>
                    <li>Guías de estudio actualizadas</li>
                    <li>Técnicas de memorización efectivas</li>
                    <li>Análisis de convocatorias</li>
                    <li>Consejos para el día del examen</li>
                </ul>
                <p>¡Mantente al día con las últimas novedades!</p>
                ''',
                'estado': 'publicado'
            },
            {
                'titulo': 'Cómo Organizar tu Tiempo de Estudio',
                'slug': 'como-organizar-tiempo-estudio',
                'contenido': '''
                <h2>La importancia de una buena planificación</h2>
                <p>Organizar tu tiempo de estudio es fundamental para el éxito en las oposiciones. Una buena planificación te permitirá:</p>
                <ul>
                    <li>Cubrir todo el temario de manera equilibrada</li>
                    <li>Tener tiempo para repasos</li>
                    <li>Reducir el estrés y la ansiedad</li>
                    <li>Mantener la motivación a largo plazo</li>
                </ul>
                <h3>Consejos prácticos</h3>
                <p>1. <strong>Establece objetivos diarios</strong>: Define qué vas a estudiar cada día.</p>
                <p>2. <strong>Usa la técnica Pomodoro</strong>: 25 minutos de estudio, 5 de descanso.</p>
                <p>3. <strong>Planifica los repasos</strong>: Dedica tiempo semanal a repasar lo estudiado.</p>
                ''',
                'estado': 'publicado'
            },
            {
                'titulo': 'Técnicas de Memorización para Oposiciones',
                'slug': 'tecnicas-memorizacion-oposiciones',
                'contenido': '''
                <h2>Mejora tu capacidad de memorización</h2>
                <p>La memorización es una habilidad clave en las oposiciones. Aquí te compartimos las técnicas más efectivas:</p>
                
                <h3>1. Método de los Loci (Palacio de la Memoria)</h3>
                <p>Asocia la información que quieres recordar con lugares familiares. Visualiza un recorrido por tu casa y coloca cada dato en una habitación específica.</p>
                
                <h3>2. Técnica de la Repetición Espaciada</h3>
                <p>Repasa la información en intervalos crecientes: 1 día, 3 días, 1 semana, 2 semanas, 1 mes.</p>
                
                <h3>3. Mapas Mentales</h3>
                <p>Crea diagramas visuales que conecten conceptos relacionados. Usa colores, símbolos e imágenes para hacer la información más memorable.</p>
                
                <h3>4. Acrónimos y Reglas Nemotécnicas</h3>
                <p>Crea palabras o frases que te ayuden a recordar listas o secuencias importantes.</p>
                ''',
                'estado': 'publicado'
            }
        ]
        
        for post_data in posts_ejemplo:
            Post.objects.create(autor=admin_user, **post_data)
        
        print(f"✅ Creados {len(posts_ejemplo)} posts de ejemplo")
    else:
        print(f"✅ Ya existen {posts_publicados.count()} posts publicados")
    
    # 4. Verificar integridad de datos
    posts_problematicos = Post.objects.filter(autor__isnull=True)
    if posts_problematicos.exists():
        posts_problematicos.update(autor=admin_user)
        print(f"✅ Arreglados {posts_problematicos.count()} posts sin autor")
    
    # 5. Mostrar resumen final
    total_posts = Post.objects.count()
    posts_publicados = Post.objects.filter(estado='publicado').count()
    posts_borrador = Post.objects.filter(estado='borrador').count()
    
    print("\n📊 RESUMEN DEL BLOG:")
    print(f"   - Total posts: {total_posts}")
    print(f"   - Posts publicados: {posts_publicados}")
    print(f"   - Posts en borrador: {posts_borrador}")
    
    print("\n🎉 Blog arreglado y listo para producción!")
    
    return True

if __name__ == '__main__':
    try:
        fix_blog()
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()