# Estado de la reconstrucción — 14/11/2026

## Cambio sobre la entrega del 13 de noviembre

- **SÍ incluye confirmación por código de 6 dígitos** al registrar una clienta; el código llega a la cuenta de correo que se quiere registrar (en local también puede imprimirse en terminal). Contraseña protegida mediante hash, vencimiento a los 10 min, bloqueo tras 5 intentos y límites de reenvío. La cuenta no existe antes de la verificación.
- Cambio de dirección de correo electrónico desde perfil de cliente exige confirmación en el nuevo buzón.
- Nueva entidad `ImagenServicio` relacionada 1:N con `Servicio`. Galería pública de hasta 12 fotos gestionada por estilista o administrador; visitantes/clientes ven el catálogo y detalle con galería.
- Se modernizaron portada, catálogo, ficha de servicio, creación/edición de servicios y estilos globales de paneles.
- Configuraciones de entorno para Gmail SMTP, PostgreSQL, Redis opcional, S3/R2, HTTPS y WhiteNoise en Render; sin credenciales reales.
- El resto de la base original permanece en el proyecto (agenda, roles, bitácora, pagos y documentos).

## Documentos históricos

Los archivos de trazabilidad de 53 historias/requisitos y el modelo relacional de 16 entidades fueron generados antes de añadir la galería. Deben actualizarse formalmente a 17 entidades, además de ajustar los escenarios de validación de correo, antes de presentarse como documentación final.

## Validación

Se verificó sintaxis Python y estructura del archivo ZIP. La disponibilidad de bibliotecas de Django y PyPI impidió correr los tests aquí, por lo que hace falta confirmar `python manage.py check`, `python manage.py makemigrations --check --dry-run` y la suite de test en un entorno con dependencias.
