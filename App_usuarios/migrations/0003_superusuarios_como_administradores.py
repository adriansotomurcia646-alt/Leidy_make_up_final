from django.db import migrations


def corregir_superusuarios(apps, schema_editor):
    """Migra superusuarios preexistentes sin afectar cuentas de clientes o estilistas."""
    Persona=apps.get_model('App_usuarios','Persona')
    Persona.objects.filter(is_superuser=True).update(rol='administrador',is_staff=True)

class Migration(migrations.Migration):
    dependencies=[('App_usuarios','0002_rol_administrador_historial_y_direccion')]
    operations=[migrations.RunPython(corregir_superusuarios,migrations.RunPython.noop)]
