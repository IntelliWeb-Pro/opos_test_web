#!/usr/bin/env python
"""
Script para verificar que el blog funciona correctamente en producción
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from tests.models import Post
from django.contrib.auth import get_user_model

def verify_blog_production():
    print("🔍 VERIFICANDO BLOG PARA PRODUCCIÓN")
    
    client = Client()
    
    # 1. Verificar que hay posts publicados
    posts_publicados = Post.objects.filter(estado='publicado')
    print(f"✅ Posts publicados en BD: {posts_publicados.count()}")
    
    if posts_publicados.count() == 0:
        print("❌ No hay posts publicados. Ejecuta fix_blog.py primero.")
        return False
    
    # 2. Probar endpoint de lista
    try:
        response = client.get('/api/blog/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Lista (/api/blog/): {len(data)} posts")
            
            # Verificar estructura de respuesta
            if data and all(key in data[0] for key in ['id', 'titulo', 'slug', 'autor_username', 'creado_en']):
                print("✅ Estructura de respuesta correcta")
            else:
                print("❌ Estructura de respuesta incorrecta")
                return False
        else:
            print(f"❌ Error en API Lista: {response.status_code}")
            print(f"   Contenido: {response.content}")
            return False
    except Exception as e:
        print(f"❌ Excepción en API Lista: {e}")
        return False
    
    # 3. Probar endpoint de detalle
    try:
        primer_post = posts_publicados.first()
        response = client.get(f'/api/blog/{primer_post.slug}/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Detalle (/api/blog/{primer_post.slug}/): OK")
            
            # Verificar estructura de respuesta
            required_fields = ['id', 'titulo', 'slug', 'autor_username', 'contenido', 'creado_en', 'actualizado_en']
            if all(key in data for key in required_fields):
                print("✅ Estructura de detalle correcta")
            else:
                missing = [key for key in required_fields if key not in data]
                print(f"❌ Campos faltantes en detalle: {missing}")
                return False
        else:
            print(f"❌ Error en API Detalle: {response.status_code}")
            print(f"   Contenido: {response.content}")
            return False
    except Exception as e:
        print(f"❌ Excepción en API Detalle: {e}")
        return False
    
    # 4. Probar manejo de errores 404
    try:
        response = client.get('/api/blog/post-que-no-existe/')
        if response.status_code == 404:
            print("✅ Error 404 manejado correctamente")
        else:
            print(f"⚠️  Respuesta inesperada para 404: {response.status_code}")
    except Exception as e:
        print(f"❌ Error probando 404: {e}")
    
    # 5. Verificar que posts en borrador no aparecen
    posts_borrador = Post.objects.filter(estado='borrador')
    if posts_borrador.exists():
        response = client.get('/api/blog/')
        if response.status_code == 200:
            api_posts = response.json()
            api_slugs = [post['slug'] for post in api_posts]
            borrador_slugs = [post.slug for post in posts_borrador]
            
            if not any(slug in api_slugs for slug in borrador_slugs):
                print("✅ Posts en borrador no aparecen en API")
            else:
                print("❌ Posts en borrador aparecen en API")
                return False
    
    # 6. Verificar configuración CORS para producción
    from django.conf import settings
    cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    production_domains = ['https://testestado.es', 'https://www.testestado.es']
    
    if any(domain in cors_origins for domain in production_domains):
        print("✅ CORS configurado para producción")
    else:
        print("⚠️  CORS podría no estar configurado para producción")
    
    print("\n🎉 BLOG VERIFICADO Y LISTO PARA PRODUCCIÓN!")
    print("\n📋 URLs disponibles:")
    print("   - Lista de posts: /api/blog/")
    print("   - Detalle de post: /api/blog/{slug}/")
    print("\n📝 Ejemplo de uso:")
    print("   curl https://tu-dominio.com/api/blog/")
    print(f"   curl https://tu-dominio.com/api/blog/{primer_post.slug}/")
    
    return True

if __name__ == '__main__':
    try:
        verify_blog_production()
    except Exception as e:
        print(f"💥 Error durante verificación: {e}")
        import traceback
        traceback.print_exc()