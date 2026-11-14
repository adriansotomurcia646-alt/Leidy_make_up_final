# Leidy Make Up · Maison 3.1 — Carrusel editable por Administrador

## Qué cambió

- La ilustración que aparecía en el hero **de la página de inicio** y en el panel izquierdo **del inicio de sesión** se sustituye por una galería de fotos administrable. Si no existen fotos activas para esa zona, aparece la ilustración anterior, sin errores.
- Nueva entidad `App_inicio.FotoCarrusel`: cada imagen se puede activar/desactivar, ordenar, mostrar en portada, mostrar en login o ambas. Máximo 12 imágenes activas por zona; cada carga múltiple acepta 12 archivos.
- En `/administracion/portada/` existe una pantalla exclusiva para rol **administrador** que permite seleccionar varias fotos a la vez, visualizar las miniaturas, guardar, ordenar y eliminar.
- Django Admin (`/admin/`) permite además editar las fotos individualmente en **App_inicio → Fotografías del carrusel**.
- El carrusel cambia automáticamente cada 5,8 segundos con **transición de opacidad de 1,25 s**. Los puntos permiten elegir imagen y el carrusel se pausa durante interacción o al cambiar a otra pestaña. Respeta *reducir movimiento* del sistema.
- Formatos JPG, PNG o WebP, 5 MB y 24 megapíxeles máximo por foto, validados en servidor. Los archivos se almacenan bajo el almacenamiento público existente `servicios_publicos` y no exponen adjuntos privados de citas.

## Pasos para actualizar una instalación existente

1. Conserva una copia segura de tu base de datos y de la carpeta de fotos (`media/servicios_publicos/`) antes de sustituir el código.
2. Copia esta versión del código encima de tu instalación o clona en una carpeta nueva y conserva tu `.env` y tu base de datos existente.
3. Activa el entorno virtual y ejecuta `python manage.py migrate` para crear la tabla `App_inicio_fotocarrusel`.
4. Ejecuta `python manage.py check` y `python manage.py runserver`.
5. Inicia sesión como **Administrador** y abre **Fotos de portada** en el menú lateral. Selecciona varias fotos, elige dónde se mostrarán y pulsa **Publicar fotografías**.
6. Si quieres cambiar el orden, escribe un número (0 va primero) y pulsa **Guardar cambios** en cada foto. Desmarca **Publicada** para ocultar sin eliminar.

## Producción

La galería utiliza el almacenamiento `servicios_publicos`. En Render, el disco temporal **no conserva imágenes** entre despliegues: configura almacenamiento público persistente con `SERVICE_IMAGES_BUCKET` y las variables R2/S3 descritas en el README antes de publicar. El backend no expone archivos privados de citas.

## Pruebas recomendadas

`python manage.py check`
`python manage.py makemigrations --check --dry-run`
`python manage.py test App_inicio App_administracion`

Se añadieron pruebas para carga, permisos, validación, orden y aparición de fotos. Se mantiene la lógica de registro Gmail, servicios y citas; no se alteraron sus modelos.
