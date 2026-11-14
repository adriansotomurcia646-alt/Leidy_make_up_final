"""Catálogo para visitantes/clientas y galería editable para personal autorizado."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError, Prefetch
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from App_usuarios.decorators import role_required, rol_real
from .forms import ServicioForm
from .galeria import LIMITE_IMAGENES, guardar_fotos
from .models import ImagenServicio, Servicio


def _servicios_visibles():
    return Servicio.objects.filter(activo=True).prefetch_related('imagenes').order_by('nombre')


def lista_servicios_view(request):
    if rol_real(request.user) == 'estilista':
        return render(request, 'App_servicios/E_servicios.html', {
            'servicios': _servicios_visibles(),
            'servicios_desactivados': Servicio.objects.filter(activo=False).prefetch_related('imagenes').order_by('nombre'),
        })
    return render(request, 'App_servicios/C_servicios.html', {'servicios': _servicios_visibles()})


def detalle_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio.objects.prefetch_related('imagenes'), pk=pk)
    if not servicio.activo and rol_real(request.user) not in ('estilista', 'administrador'):
        raise Http404('El servicio no está disponible.')
    return render(request, 'App_servicios/detalle.html', {'servicio': servicio})


def _contexto_form(accion, servicio, form):
    return {'accion': accion, 'servicio': servicio, 'form': form, 'limite_imagenes': LIMITE_IMAGENES}


@role_required('estilista')
def crear_servicio_view(request):
    form = ServicioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        fotos = request.FILES.getlist('fotografias')
        try:
            if len(fotos) > LIMITE_IMAGENES:
                raise ValidationError(f'Puedes cargar máximo {LIMITE_IMAGENES} imágenes por servicio.')
            # Guardar la fila del servicio solo si la galería fue válida.
            from .models import validar_foto_servicio
            for foto in fotos:
                validar_foto_servicio(foto)
            with transaction.atomic():
                servicio = form.save()
                guardar_fotos(servicio, fotos)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Servicio y fotografías guardados correctamente.')
            return redirect('App_servicios:lista')
    return render(request, 'E_servicio_form.html', _contexto_form('Crear', None, form))


@role_required('estilista')
def editar_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    form = ServicioForm(request.POST or None, instance=servicio)
    if request.method == 'POST' and form.is_valid():
        try:
            fotos = request.FILES.getlist('fotografias')
            if len(fotos) + servicio.imagenes.count() > LIMITE_IMAGENES:
                raise ValidationError(f'Límite de {LIMITE_IMAGENES} imágenes por servicio.')
            from .models import validar_foto_servicio
            for foto in fotos:
                validar_foto_servicio(foto)
            with transaction.atomic():
                form.save()
                guardar_fotos(servicio, fotos)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Servicio y galería actualizados.')
            return redirect('App_servicios:lista')
    return render(request, 'E_servicio_form.html', _contexto_form('Editar', servicio, form))


def _autorizar_personal(request):
    return rol_real(request.user) in ('estilista', 'administrador')


def _destino_editor(request, servicio):
    if rol_real(request.user) == 'administrador':
        return redirect('App_administracion:servicio_editar', pk=servicio.pk)
    return redirect('App_servicios:editar', pk=servicio.pk)


@login_required
@require_POST
def eliminar_imagen_view(request, pk):
    if not _autorizar_personal(request):
        return HttpResponseForbidden('No tienes permiso para modificar fotos.')
    foto = get_object_or_404(ImagenServicio.objects.select_related('servicio'), pk=pk)
    servicio = foto.servicio
    foto.delete()
    # Conservar una portada visible si se elimina la imagen principal.
    if not servicio.imagenes.filter(es_portada=True).exists():
        primera = servicio.imagenes.first()
        if primera:
            primera.es_portada = True
            primera.save(update_fields=['es_portada'])
    messages.success(request, 'Fotografía eliminada de la galería.')
    return _destino_editor(request, servicio)


@login_required
@require_POST
def elegir_portada_view(request, pk):
    if not _autorizar_personal(request):
        return HttpResponseForbidden('No tienes permiso para cambiar la portada.')
    foto = get_object_or_404(ImagenServicio.objects.select_related('servicio'), pk=pk)
    with transaction.atomic():
        ImagenServicio.objects.filter(servicio=foto.servicio, es_portada=True).update(es_portada=False)
        ImagenServicio.objects.filter(pk=foto.pk).update(es_portada=True)
    messages.success(request, 'Esta imagen es ahora la portada del servicio.')
    return _destino_editor(request, foto.servicio)


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


@role_required('estilista')
@require_POST
def eliminar_permanentemente_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk, activo=False)
    if servicio.citas.exists():
        messages.error(request, 'No se puede eliminar porque hay citas asociadas. El servicio seguirá desactivado.')
        return redirect('App_servicios:lista')
    try:
        servicio.delete()
    except ProtectedError:
        messages.error(request, 'Hay información relacionada. El servicio se conservará desactivado.')
        return redirect('App_servicios:lista')
    messages.success(request, 'El servicio fue eliminado permanentemente.')
    return redirect('App_servicios:lista')
