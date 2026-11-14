from django.db import migrations, models
import App_inicio.models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='FotoCarrusel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(storage=App_inicio.models.guardar_en_galeria_publica, upload_to=App_inicio.models.ubicacion_foto, validators=[App_inicio.models.validar_foto_servicio], verbose_name='fotografía')),
                ('titulo', models.CharField(blank=True, max_length=140, verbose_name='texto alternativo')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='orden de aparición')),
                ('activa', models.BooleanField(default=True, verbose_name='publicada')),
                ('mostrar_en_portada', models.BooleanField(default=True, verbose_name='mostrar en portada')),
                ('mostrar_en_login', models.BooleanField(default=True, verbose_name='mostrar en inicio de sesión')),
                ('creada_en', models.DateTimeField(auto_now_add=True, verbose_name='fecha de carga')),
            ],
            options={
                'verbose_name': 'fotografía del carrusel',
                'verbose_name_plural': 'fotografías del carrusel',
                'ordering': ('orden', 'pk'),
            },
        ),
    ]
