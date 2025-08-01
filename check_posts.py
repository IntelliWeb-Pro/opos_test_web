#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from tests.models import Post

print('Posts en la base de datos:')
posts = Post.objects.all()
print(f'Total: {posts.count()}')
for post in posts:
    print(f'- {post.titulo} (Estado: {post.estado}, Slug: {post.slug})')

# Crear un post de prueba si no hay ninguno
if posts.count() == 0:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Crear un usuario admin si no existe
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True}
    )
    
    # Crear un post de prueba
    test_post = Post.objects.create(
        titulo='Bienvenido al Blog de TestEstado',
        slug='bienvenido-blog-testestado',
        autor=admin_user,
        contenido='<p>Este es el primer artículo de nuestro blog. Aquí encontrarás consejos, trucos y noticias sobre oposiciones.</p><p>¡Mantente al día con las últimas novedades!</p>',
        estado='publicado'
    )
    print(f'Post de prueba creado: {test_post.titulo}')