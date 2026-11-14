# Nueva entidad: galería de fotos por servicio.
from django.db import migrations, models
import django.db.models.deletion
import App_servicios.models


class Migration(migrations.Migration):
    dependencies = [('App_servicios', '0002_service_fields')]

    operations = [
        migrations.CreateModel(
            name='ImagenServicio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(
                    storage=App_servicios.models.almacenamiento_fotos_publicas,
                    upload_to=App_servicios.models.ruta_foto_servicio,
                    validators=[App_servicios.models.validar_foto_servicio],
                )),
                ('descripcion', models.CharField(blank=True, max_length=150)),
                ('es_portada', models.BooleanField(default=False)),
                ('orden', models.PositiveSmallIntegerField(default=0)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('servicio', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='imagenes', to='App_servicios.servicio',
                )),
            ],
            options={'ordering': ('-es_portada', 'orden', 'pk')},
        ),
    ]
