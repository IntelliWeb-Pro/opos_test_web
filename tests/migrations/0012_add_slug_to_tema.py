# tests/migrations/00XX_add_slug_to_tema.py
from django.db import migrations, models
from django.utils.text import slugify

def populate_slugs(apps, schema_editor):
    Tema = apps.get_model('tests', 'Tema')
    seen = set()
    for t in Tema.objects.all().only('id', 'nombre_oficial', 'slug'):
        base = slugify(t.nombre_oficial)[:240] or f"tema-{t.id}"
        slug = base
        i = 2
        # fuerza unicidad en memoria
        while slug in seen or Tema.objects.filter(slug=slug).exclude(pk=t.pk).exists():
            slug = f"{base}-{i}"
            i += 1
        t.slug = slug
        t.save(update_fields=['slug'])
        seen.add(slug)

class Migration(migrations.Migration):
    dependencies = [
        ('tests', 'XXXX_prev_migration'),  # ← ajusta al nombre real
    ]

    operations = [
        migrations.AddField(
            model_name='tema',
            name='slug',
            field=models.SlugField(max_length=255, unique=True, db_index=True, null=True, blank=True),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='tema',
            name='slug',
            field=models.SlugField(max_length=255, unique=True, db_index=True),
        ),
    ]
