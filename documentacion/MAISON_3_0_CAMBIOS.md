# Maison 3.0 · Notas de diseño

El nuevo diseño es una evolución visual que deja intacta la base de datos, migraciones y reglas de negocio. No se han insertado servicios ficticios ni fotografías atribuidas a la estilista. La ilustración original para portada y acceso se almacena en `static/img/beauty-illustration.svg`. Una vez que la estilista cargue fotos, el portal utiliza las imágenes de los servicios.

Componentes modificados: portada, login, servicio formulario, estilos compartidos, tarjetas catálogo, detalle de servicio y paneles por rol.

## Pruebas visuales recomendadas
1. Portada y menú móvil (360px, 768px, 1440px).
2. Acceso cliente / estilista / administrador.
3. Listado de servicios con y sin fotografías.
4. Carga múltiple y selección de portada.
5. Revisión de citas y horarios de la estilista.

## No cambios funcionales
Verificación SMTP, autenticación y autorización se mantienen de la base anterior; la interfaz no implementa inicio de sesión con Google OAuth ni doble factor en cada inicio de sesión.
