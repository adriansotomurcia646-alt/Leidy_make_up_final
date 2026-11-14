from django.apps import AppConfig


class AppServiciosConfig(AppConfig):
    name = 'App_servicios'

    def ready(self):
        from . import galeria  # noqa: F401 registra signal post_delete
