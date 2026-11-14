# Renombrado de registro_id -> registro_cobro_id acorde al diagrama aprobado.
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('App_facturacion', '0003_cierrecaja_pago')]
    operations = [
        migrations.RenameField(model_name='pago',old_name='registro',new_name='registro_cobro'),
    ]
