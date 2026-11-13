from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'App_usuarios'

urlpatterns = [
	path('login/', views.login_view, name='login'),
	path('registro/', views.registro_view, name='registro'),
	path('recuperar-clave/', auth_views.PasswordResetView.as_view(template_name='App_usuarios/recuperar_clave.html',email_template_name='App_usuarios/email_recuperacion.txt',success_url='/usuarios/recuperar-clave/enviado/'),name='password_reset'),
	path('recuperar-clave/enviado/',auth_views.PasswordResetDoneView.as_view(template_name='App_usuarios/recuperacion_enviada.html'),name='password_reset_done'),
	path('restablecer/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='App_usuarios/restablecer_clave.html',success_url='/usuarios/restablecer/realizado/'),name='password_reset_confirm'),
	path('restablecer/realizado/',auth_views.PasswordResetCompleteView.as_view(template_name='App_usuarios/recuperacion_completa.html'),name='password_reset_complete'),
	path('ayuda/', views.ayuda_view, name='ayuda'),
	path('soporte/', views.soporte_view, name='soporte'),
	path('perfil/', views.perfil_view, name='perfil'),
	path('configuracion/', views.configuracion_view, name='configuracion'),
	path('logout/', views.logout_view, name='logout'),
	path('estilista/login/', views.e_login, name='e_login'),
	path('administrador/login/', views.a_login, name='a_login'),
]
