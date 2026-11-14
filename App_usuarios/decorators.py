"""Decoradores RBAC: la sesión nunca permite elevar permisos por elegir otro rol."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.urls import reverse


def rol_real(usuario):
    """Devuelve el rol persistido y verificado; ignora valores manipulables de sesión/POST."""
    if not usuario.is_authenticated or not usuario.is_active:
        return None
    if usuario.is_superuser:
        return 'administrador'
    if usuario.rol == 'administrador':
        return 'administrador' if usuario.is_staff else None
    if usuario.rol in ('cliente', 'estilista'):
        return usuario.rol
    return None


def role_required(role):
    """Exige el mismo rol autenticado que solicita la vista, sin excepción para staff."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_name = {
                    'estilista': 'App_usuarios:e_login',
                    'administrador': 'App_usuarios:a_login',
                }.get(role, 'App_usuarios:login')
                return redirect_to_login(request.get_full_path(), login_url=reverse(login_name))
            actual = rol_real(request.user)
            if actual != role:
                messages.error(request, 'No tienes permiso para acceder a esta página.')
                return HttpResponseForbidden('No tienes permiso para acceder a esta página.')
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
