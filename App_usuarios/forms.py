from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import Persona


class RegistroClienteForm(forms.Form):
	nombre = forms.CharField(
		max_length=150,
		error_messages={'required': 'Completa tu nombre.'},
	)
	apellido = forms.CharField(max_length=150, error_messages={'required': 'Completa tus apellidos.'})
	email = forms.EmailField(
		max_length=150,
		error_messages={
			'invalid': 'Introduce un correo electrónico válido.',
			'max_length': 'El correo electrónico no puede superar 150 caracteres.',
			'required': 'Completa tu correo electrónico.',
		},
	)
	telefono = forms.CharField(max_length=30, error_messages={'required': 'Completa tu teléfono.'})
	password = forms.CharField(
		widget=forms.PasswordInput,
		error_messages={'required': 'Completa tu contraseña.'},
	)

	def clean_email(self):
		email = self.cleaned_data['email'].strip().lower()
		if Persona.objects.filter(email__iexact=email).exists():
			raise ValidationError('Este correo electrónico ya está registrado.')
		return email

	def clean_password(self):
		password = self.cleaned_data['password']
		email = self.cleaned_data.get('email', '')
		nombre = self.cleaned_data.get('nombre', '')
		password_validation.validate_password(
			password,
			user=Persona(username=email, email=email, first_name=nombre),
		)
		return password
