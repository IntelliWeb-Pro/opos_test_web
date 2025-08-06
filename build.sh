#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# --- PASO 1: SINCRONIZAR LA BASE DE DATOS (MODO SEGURO) ---
# Le decimos a Django que finja que todas las migraciones ya están aplicadas.
# Esto evita el error "DuplicateTable" y alinea el registro de Django con la realidad.
python3 manage.py migrate --fake

# --- PASO 2: APLICAR MIGRACIONES NUEVAS ---
# Ahora que todo está sincronizado, aplicamos solo las migraciones que falten
# (como la que elimina el modelo PreguntaFallada).
python3 manage.py migrate

# --- PASO 3: RECOLECTAR ARCHIVOS ESTÁTICOS ---
python3 manage.py collectstatic --no-input