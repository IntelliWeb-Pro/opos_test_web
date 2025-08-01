#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from tests.models import Post

def test_blog_api():
    client = Client()
    
    print("=== PRUEBA DE API DEL BLOG ===")
    
    # Crear usuario admin si no existe
    User = get_user_model()
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True}
    )
    
    # Crear posts de prueba si no existen
    if Post.objects.count() == 0:
        posts_data = [
            {
                'titulo': 'Guía Completa para Oposiciones 2024',
                'slug': 'guia-completa-oposiciones-2024',
                'contenido': '<p>Esta es una guía completa para preparar oposiciones en 2024.</p><p>Incluye consejos, estrategias y recursos útiles.</p>',
                'estado': 'publicado'
            },
            {
                'titulo': 'Técnicas de Estudio Efectivas',
                'slug': 'tecnicas-estudio-efectivas',
                'contenido': '<p>Descubre las mejores técnicas de estudio para maximizar tu rendimiento.</p>',
                'estado': 'publicado'
            },
            {
                'titulo': 'Post en Borrador',
                'slug': 'post-borrador',
                'contenido': '<p>Este post está en borrador y no debería aparecer en la API.</p>',
                'estado': 'borrador'
            }
        ]
        
        for post_data in posts_data:
            Post.objects.create(autor=admin_user, **post_data)
        
        print(f"✅ Creados {len(posts_data)} posts de prueba")
    
    # Probar endpoint de lista de posts
    print("\n1. Probando GET /api/blog/")
    response = client.get('/api/blog/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Lista de posts obtenida correctamente")
        print(f"   - Total posts: {len(data)}")
        for post in data:
            print(f"   - {post['titulo']} (slug: {post['slug']})")
    else:
        print(f"❌ Error en lista de posts: {response.content}")
        return False
    
    # Probar endpoint de detalle de post
    print("\n2. Probando GET /api/blog/{slug}/")
    test_slug = 'guia-completa-oposiciones-2024'
    response = client.get(f'/api/blog/{test_slug}/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Detalle de post obtenido correctamente")
        print(f"   - Título: {data['titulo']}")
        print(f"   - Autor: {data['autor_username']}")
        print(f"   - Contenido: {data['contenido'][:100]}...")
    else:
        print(f"❌ Error en detalle de post: {response.content}")
        return False
    
    # Probar post inexistente
    print("\n3. Probando GET /api/blog/post-inexistente/")
    response = client.get('/api/blog/post-inexistente/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ Error 404 manejado correctamente para post inexistente")
    else:
        print(f"⚠️  Respuesta inesperada para post inexistente: {response.status_code}")
    
    # Verificar que posts en borrador no aparecen
    print("\n4. Verificando que posts en borrador no aparecen en la API")
    all_posts = Post.objects.all()
    published_posts = Post.objects.filter(estado='publicado')
    print(f"   - Total posts en BD: {all_posts.count()}")
    print(f"   - Posts publicados: {published_posts.count()}")
    
    response = client.get('/api/blog/')
    if response.status_code == 200:
        api_posts = response.json()
        if len(api_posts) == published_posts.count():
            print("✅ Solo se muestran posts publicados en la API")
        else:
            print("❌ La API muestra posts que no deberían estar visibles")
    
    print("\n=== PRUEBAS COMPLETADAS ===")
    return True

if __name__ == '__main__':
    try:
        test_blog_api()
        print("\n🎉 Todas las pruebas del blog pasaron correctamente!")
    except Exception as e:
        print(f"\n💥 Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()