"""Barrera extra para impedir que cuentas de staff sin rol AD entren a /admin/."""
from django.http import HttpResponseForbidden
from .decorators import rol_real

class AdminRoleMiddleware:
    def __init__(self, get_response):self.get_response=get_response
    def __call__(self,request):
        if request.path.startswith('/admin/') and request.user.is_authenticated and rol_real(request.user)!='administrador':
            return HttpResponseForbidden('Acceso exclusivo para administradores.')
        return self.get_response(request)
