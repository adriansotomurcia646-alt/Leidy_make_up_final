"""Formularios con validaciones centralizadas para evitar privilegios y duplicados."""
from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.db.models import Q
from App_usuarios.models import Persona, Cliente
from App_servicios.models import Servicio


class CuentaForm(forms.Form):
    first_name = forms.CharField(label='Nombres', max_length=150)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=False)
    email = forms.EmailField(label='Correo único', max_length=150)
    telefono = forms.CharField(label='Teléfono', required=False, max_length=30)
    direccion = forms.CharField(label='Dirección', required=False, max_length=255)
    especialidad = forms.CharField(label='Especialidad', required=False, max_length=120)
    rol = forms.ChoiceField(choices=Persona.ROLES, label='Rol')
    password = forms.CharField(label='Contraseña (dejar en blanco para conservar)',
                               widget=forms.PasswordInput(render_value=False), required=False)

    def __init__(self, *args, instancia=None, **kwargs):
        self.instancia = instancia
        initial = kwargs.pop('initial', {})
        if instancia is not None and not args and 'data' not in kwargs:
            initial.update({key: getattr(instancia,key) for key in ('first_name','last_name','email','rol')})
            if hasattr(instancia,'cliente'):
                initial.update(telefono=instancia.cliente.telefono,direccion=instancia.cliente.direccion)
            if hasattr(instancia,'estilista'):
                initial.update(especialidad=instancia.estilista.especialidad)
        super().__init__(*args, initial=initial, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        otros = Persona.objects.filter(Q(email__iexact=email)|Q(username__iexact=email))
        if self.instancia:
            otros = otros.exclude(pk=self.instancia.pk)
        if otros.exists():
            raise ValidationError('Este correo ya pertenece a una cuenta.')
        return email

    def clean(self):
        values = super().clean()
        password = values.get('password')
        if self.instancia is None and not password:
            self.add_error('password','Debes asignar una contraseña inicial.')
        if password:
            try:
                password_validation.validate_password(password, user=Persona(
                    email=values.get('email',''),username=values.get('email',''),
                    first_name=values.get('first_name',''),
                ))
            except ValidationError as error:
                self.add_error('password',error)
        if self.instancia and self.instancia.rol != values.get('rol'):
            # No romper FKs del historial por cambiar un perfil con citas.
            if (hasattr(self.instancia,'cliente') and self.instancia.cliente.citas.exists()) or (
                    hasattr(self.instancia,'estilista') and self.instancia.estilista.citas.exists()):
                self.add_error('rol','No se puede cambiar el rol de una cuenta con citas históricas.')
        return values


class ServicioAdministrativoForm(forms.ModelForm):
    class Meta:
        model=Servicio
        fields=('nombre','categoria','descripcion','precio','duracion','activo')

    def clean_precio(self):
        precio=self.cleaned_data['precio']
        if precio < 0: raise ValidationError('El precio debe ser mayor o igual a cero.')
        return precio

    def clean_duracion(self):
        duracion=self.cleaned_data['duracion']
        if duracion < 1 or duracion > 1440:
            raise ValidationError('La duración debe estar entre 1 y 1440 minutos.')
        return duracion
