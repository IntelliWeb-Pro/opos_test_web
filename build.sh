#!/usr/bin/env bash
# build.sh - Script de construcción para Render

set -o errexit  # Salir si cualquier comando falla

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic --noinput