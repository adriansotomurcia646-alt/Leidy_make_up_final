# Modelo relacional Leidy Make Up: relaciones normalizadas de cita y persona.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('App_agenda', '0008_cita_metodo_pago_preferido_alter_cita_estado_and_more'),
        ('App_usuarios', '0004_relaciones_persona_y_email_unico'),
    ]
    operations = [
        migrations.RenameField(model_name='bitacoracita', old_name='usuario', new_name='persona'),
        migrations.RenameField(model_name='notificacion', old_name='usuario', new_name='persona'),
        migrations.AddField(
            model_name='mensaje', name='cita',
            field=models.ForeignKey(
                to='App_agenda.cita', related_name='mensajes', null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
    ]
