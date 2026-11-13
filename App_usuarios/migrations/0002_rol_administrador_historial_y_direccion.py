from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('App_usuarios', '0001_initial')]
    operations = [
        migrations.AlterField(model_name='persona', name='rol', field=models.CharField(choices=[('cliente', 'Cliente'), ('estilista', 'Estilista'), ('administrador', 'Administrador')], default='cliente', max_length=20)),
        migrations.AddField(model_name='cliente', name='direccion', field=models.CharField(blank=True, max_length=255)),
        migrations.CreateModel(name='HistorialAcceso', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('identificador', models.CharField(blank=True, max_length=150)),
            ('evento', models.CharField(choices=[('LOGIN','Inicio de sesión'),('FALLO','Acceso rechazado'),('LOGOUT','Cierre de sesión')], max_length=30)),
            ('rol_solicitado', models.CharField(blank=True, max_length=20)),
            ('fecha', models.DateTimeField(auto_now_add=True)),
            ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':('-fecha',)}),
    ]
