from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from App_usuarios.decorators import role_required, rol_real

from .forms import ServicioForm
from .models import Servicio


# Explicación: RF-VI-002: visitantes/clientes ven solo servicios activos; personal ve catálogo.
def lista_servicios_view(request):
    if (
        rol_real(request.user) == 'estilista'
    ):
        return render(
            request,
            'App_servicios/E_servicios.html',
            {
                'servicios': Servicio.objects.filter(activo=True).order_by('id'),
                'servicios_desactivados': Servicio.objects.filter(
                    activo=False
                ).order_by('id'),
            },
        )
    return render(
        request,
        'App_servicios/C_servicios.html',
        {'servicios': Servicio.objects.filter(activo=True).order_by('id')},
    )

# Explicación: Valida un nuevo servicio antes de guardarlo en la base de datos.
@role_required('estilista')
def crear_servicio_view(request):
    if request.method != 'POST':
        return render(
            request,
            'E_servicio_form.html',
            {'accion': 'Crear', 'servicio': None},
        )

    form = ServicioForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'El servicio fue creado correctamente.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect('App_servicios:lista')


# Explicación: Aplica cambios del catálogo sin modificar citas históricas.
@role_required('estilista')
def editar_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method != 'POST':
        return render(
            request,
            'E_servicio_form.html',
            {'accion': 'Editar', 'servicio': servicio},
        )

    form = ServicioForm(request.POST, instance=servicio)
    if form.is_valid():
        form.save()
        messages.success(request, 'El servicio fue actualizado correctamente.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect('App_servicios:lista')


# Explicación: Desactiva un servicio sin borrar sus citas (eliminación lógica).
@role_required('estilista')
@require_POST
def eliminar_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if not servicio.activo:
        messages.info(request, 'El servicio ya estaba desactivado.')
        return redirect('App_servicios:lista')
    servicio.activo = False
    servicio.save(update_fields=['activo'])
    messages.success(request, 'El servicio fue desactivado y retirado del catálogo.')
    return redirect('App_servicios:lista')


# Explicación: Permite que un servicio vuelva al catálogo de reservas.
@role_required('estilista')
@require_POST
def reactivar_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if servicio.activo:
        messages.info(request, 'El servicio ya está activo.')
        return redirect('App_servicios:lista')
    servicio.activo = True
    servicio.save(update_fields=['activo'])
    messages.success(request, 'El servicio fue reactivado correctamente.')
    return redirect('App_servicios:lista')


# Explicación: Solo elimina servicios sin citas ni relaciones protegidas.
@role_required('estilista')
@require_POST
def eliminar_permanentemente_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk, activo=False)
    if servicio.citas.exists():
        messages.error(
            request,
            'No se puede eliminar permanentemente este servicio porque tiene citas '
            'asociadas. Se conservará como desactivado para proteger el historial.',
        )
        return redirect('App_servicios:lista')
    try:
        servicio.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar permanentemente este servicio porque tiene '
            'información relacionada. Se conservará como desactivado.',
        )
        return redirect('App_servicios:lista')
    messages.success(request, 'El servicio fue eliminado permanentemente.')
    return redirect('App_servicios:lista')