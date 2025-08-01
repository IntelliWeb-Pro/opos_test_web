# Opos Test Web - API Backend

API REST para aplicación de tests de oposiciones con Django REST Framework.

## Características

- 🔐 Autenticación JWT con django-allauth
- 💳 Integración con Stripe para suscripciones
- 📝 Sistema de tests por temas
- 📊 Seguimiento de resultados y preguntas falladas
- 📰 Sistema de blog/posts
- 🚀 Listo para despliegue en Render

## Instalación Local

1. Clona el repositorio:
```bash
git clone <tu-repo-url>
cd opos_test_web
```

2. Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecuta las migraciones:
```bash
python manage.py migrate
```

5. Crea un superusuario:
```bash
python manage.py createsuperuser
```

6. Ejecuta el servidor:
```bash
python manage.py runserver
```

## Variables de Entorno

Para producción, configura estas variables:

- `SECRET_KEY`: Clave secreta de Django
- `DATABASE_URL`: URL de la base de datos PostgreSQL
- `RENDER_EXTERNAL_HOSTNAME`: Hostname de Render
- `FRONTEND_URL`: URL del frontend
- `STRIPE_PUBLISHABLE_KEY`: Clave pública de Stripe
- `STRIPE_SECRET_KEY`: Clave secreta de Stripe
- `STRIPE_WEBHOOK_SECRET`: Secret del webhook de Stripe

## Despliegue en Render

1. Conecta tu repositorio de GitHub a Render
2. Configura las variables de entorno
3. El script `build.sh` se ejecutará automáticamente

## API Endpoints

- `/api/auth/` - Autenticación
- `/api/oposiciones/` - Gestión de oposiciones
- `/api/tests/` - Sistema de tests
- `/api/suscripciones/` - Gestión de suscripciones
- `/api/posts/` - Sistema de blog

## Estructura del Proyecto

```
opos_test_web/
├── backend/          # Configuración Django
├── tests/           # App principal
├── manage.py
├── requirements.txt
└── build.sh        # Script de despliegue
```