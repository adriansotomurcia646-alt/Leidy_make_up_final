# Modelo relacional Leidy Make Up: Persona e HistorialAcceso.
from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower

class Migration(migrations.Migration):
    dependencies = [('App_usuarios', '0003_superusuarios_como_administradores')]
    operations = [
        migrations.RenameField(model_name='historialacceso', old_name='usuario', new_name='persona'),
        migrations.AddConstraint(
            model_name='persona',
            constraint=models.UniqueConstraint(
                Lower('email'), condition=~Q(email=''), name='persona_email_unico_ci',
            ),
        ),
    ]
