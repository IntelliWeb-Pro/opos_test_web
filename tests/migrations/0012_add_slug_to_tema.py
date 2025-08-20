# tests/migrations/0012_add_slug_to_tema.py
from django.db import migrations, models
from django.utils.text import slugify

def populate_slugs(apps, schema_editor):
    Tema = apps.get_model('tests', 'Tema')
    seen = set()
    for tema in Tema.objects.all().order_by('id'):
        base = slugify(tema.nombre_oficial or '', allow_unicode=True) or f"tema-{tema.id}"
        candidate = base
        n = 2
        # Garantizar unicidad
        while candidate in seen or Tema.objects.filter(slug=candidate).exclude(pk=tema.pk).exists():
            candidate = f"{base}-{n}"
            n += 1
        tema.slug = candidate
        tema.save(update_fields=['slug'])
        seen.add(candidate)

class Migration(migrations.Migration):

    # ⬇️ CAMBIA '0011_previous' por el ÚLTIMO nombre real de tu app tests
    dependencies = [
        ('tests', '0011_oposicion_descripcion_general_and_more'),
    ]

    operations = [
        # 1) Añadimos el campo de forma laxa (null/blank) para poder rellenarlo
        migrations.AddField(
            model_name='tema',
            name='slug',
            field=models.SlugField(max_length=220, null=True, blank=True, db_index=True),
        ),
        # 2) Rellenamos datos existentes
        migrations.RunPython(populate_slugs, reverse_code=migrations.RunPython.noop),
        # 3) Cerramos restricciones: único y no nulo
        migrations.AlterField(
            model_name='tema',
            name='slug',
            field=models.SlugField(max_length=220, unique=True, null=False, db_index=True),
        ),
    ]
