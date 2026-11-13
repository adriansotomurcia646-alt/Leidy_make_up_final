"""Portada pública para visitantes, independiente de los tres paneles privados."""
from django.shortcuts import redirect, render
from App_servicios.models import Servicio
from App_usuarios.views import dashboard_url


def home(request):
    """Punto de entrada: los visitantes ven servicios; cada cuenta ve su Home de rol."""
    if request.user.is_authenticated:
        return redirect(dashboard_url(request.user))
    return render(request, 'App_usuarios/home.html', {
        'servicios': Servicio.objects.filter(activo=True).order_by('nombre')[:6],
    })
