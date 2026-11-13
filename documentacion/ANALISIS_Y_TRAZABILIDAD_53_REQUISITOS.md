# Análisis y trazabilidad de requisitos — Leidy Make Up
**Fecha de revisión inicial:** 11 de noviembre de 2026. **Ajustes de registro y modelo:** 13 de noviembre de 2026.

> **Nota de actualización:** la sección de resultados "107 pruebas" describe el código previo y no fue reejecutada en el entorno de reconstrucción. El registro ahora **no exige activar la cuenta por correo**. Las referencias a 53 RF y 166 escenarios provienen de las historias actuales.  **Fuente:** historias de usuario y Stakeholders alineados; código Django del ZIP más reciente; apuntes de clase.

> **Alcance real:** se han cruzado 53 requisitos funcionales y sus 166 escenarios de aceptación, más 23 requisitos no funcionales. No se afirma que las 166 verificaciones estén automatizadas ni que todas las funciones sean completas. **Implementado** significa que hay código funcional y comprobaciones de los módulos; **Parcial** indica algún criterio incumplido o pendiente de pruebas; **Por validar** indica ausencia de ensayo de aceptación real.

## Inventario y verificación

| Rol | Requisitos | Escenarios |
|---|---:|---:|
| Visitante | 3 | 9 |
| Cliente | 18 | 57 |
| Estilista | 14 | 46 |
| Administrador | 18 | 54 |
| **Total** | **53** | **166** |

En la **versión base anterior** se informaron pruebas Django en tres grupos: **36 + 54 + 17 = 107**, todas correctas; `manage.py check`, `makemigrations --check --dry-run` y migraciones desde base vacía correctas. La prueba de respaldo con una base SQLite persistente devolvió un archivo con cabecera SQLite válida.

**Privacidad:** el proyecto entregable excluye base de datos original, adjuntos personales, claves `.env`, carpetas `.venv` y copias de respaldo. Se recomienda cambiar cualquier secreto expuesto en versiones anteriores.

## Relación requisito → implementación → brecha

### Visitante

| Código | Estado | Implementación/limitación |
|---|---|---|
| **RF-VI-001** | Implementado | Formulario de alta de cliente, contraseña validada, correo único y campos obligatorios. **Pendiente / atención:** El registro activa la cuenta inmediatamente y no pide verificación del correo, conforme al alcance actual; la validez sintáctica y unicidad se comprueban. |
| **RF-VI-002** | Implementado | Catálogo de servicios activos accesible sin autenticación. **Pendiente / atención:** Revisar presentación visual con datos comerciales reales. |
| **RF-VI-003** | Parcial | Consulta pública de huecos; la confirmación de reserva exige sesión de cliente. **Pendiente / atención:** La respuesta depende de horarios cargados; falta ensayo integral del calendario en navegadores. |

### Cliente

| Código | Estado | Implementación/limitación |
|---|---|---|
| **RF-CLI-001** | Por validar | Formulario actualizado para validar nombre, apellidos, teléfono, correo único y contraseña; falta ejecución de las pruebas en el equipo destino. **Pendiente / atención:** Ahora apellidos y teléfono son obligatorios; debe validarse el flujo completo mediante navegador y pruebas Django. |
| **RF-CLI-002** | Implementado | Inicio y cierre de sesión; verificación estricta de rol real almacenado. **Pendiente / atención:** Requiere contraseñas de usuarios reales para validación de aceptación final. |
| **RF-CLI-003** | Parcial | Flujo Django de enlace con token y caducidad para restablecer contraseñas. **Pendiente / atención:** El correo real requiere configurar y verificar servidor SMTP. |
| **RF-CLI-004** | Implementado | Cliente puede modificar datos, email único, teléfono y dirección. **Pendiente / atención:** Sin prueba manual con navegador móvil. |
| **RF-CLI-005** | Implementado | Catálogo con detalles y filtros de los servicios activos. **Pendiente / atención:** Comprobar accesibilidad de controles en navegadores reales. |
| **RF-CLI-006** | Parcial | Selección de fecha con consulta de disponibilidad. **Pendiente / atención:** No hay una garantía validada de calendario visual completo con todos los días libres/ocupados de cada estilista. |
| **RF-CLI-007** | Implementado | Cálculo de intervalos, duración y separaciones para evitar solapamientos. **Pendiente / atención:** SQLite requiere endurecer concurrencia con transacciones y pruebas de carga para producción. |
| **RF-CLI-008** | Implementado | Reserva con servicio, estilista elegida, fecha, franja y notas; valida horario en servidor. **Pendiente / atención:** Confirmar visualmente el recorrido completo visitante→login→reserva. |
| **RF-CLI-009** | Implementado | Archivos asociados a la cita con descarga protegida por autorización. **Pendiente / atención:** Almacenamiento cloud y compresión automática pendientes. |
| **RF-CLI-010** | Implementado | Historial de citas y estados conforme al modelo de negocio. **Pendiente / atención:** El estado EN ESPERA en la UI se corresponde internamente con PENDIENTE. |
| **RF-CLI-011** | Implementado | Controla antelación mínima de cancelación según política. **Pendiente / atención:** La ventana de cancelación puede ser ajustada mediante parámetros. |
| **RF-CLI-012** | Implementado | Reprogramación limitada a estados permitidos y huecos válidos. **Pendiente / atención:** Requiere validación de simultaneidad en producción. |
| **RF-CLI-013** | Parcial | Avisos internos de cambios y recordatorios programables. **Pendiente / atención:** No hay push en tiempo real (WebSocket) ni planificador externo activo por defecto. |
| **RF-CLI-014** | Implementado | Mensajería interna entre cliente y estilista de sus citas. **Pendiente / atención:** No sustituye mensajería instantánea con entrega en vivo. |
| **RF-CLI-015** | Implementado | Muestra total del servicio, pagos y saldo pendiente. **Pendiente / atención:** El saldo refleja abonos introducidos manualmente. |
| **RF-CLI-016** | Parcial | Selección de método efectivo/transferencia y registro de pagos por profesional. **Pendiente / atención:** No existe pasarela bancaria ni confirmación automática de transferencias. |
| **RF-CLI-017** | Implementado | Recibo digital accesible con control de permisos. **Pendiente / atención:** No equivale a factura electrónica DIAN. |
| **RF-CLI-018** | Implementado | Manual y ayuda para clientes. **Pendiente / atención:** Su contenido deberá revisarse después de incorporar módulos futuros. |

### Estilista

| Código | Estado | Implementación/limitación |
|---|---|---|
| **RF-ES-001** | Implementado | Login estilista explícito y autorización comprobada por cada vista. **Pendiente / atención:** Cuenta debe tener el rol estilista en BD. |
| **RF-ES-002** | Parcial | Agenda de estilista con citas y filtros. **Pendiente / atención:** No se verificó una presentación diferenciada funcional de día, semana y mes. |
| **RF-ES-003** | Implementado | Configuración de horarios semanales y pausas/bloqueos. **Pendiente / atención:** Un horario ausente implica ninguna franja reservable. |
| **RF-ES-004** | Implementado | Especialidad editable y expuesta al escoger estilista en la reserva. **Pendiente / atención:** Las descripciones profesionales adicionales no están desarrolladas. |
| **RF-ES-005** | Implementado | Listado y detalle de citas PENDIENTE con cliente, servicio y nota. **Pendiente / atención:** Los adjuntos se acceden desde la cita protegida. |
| **RF-ES-006** | Implementado | Confirmación de solicitud con verificación de disponibilidad. **Pendiente / atención:** Se requieren pruebas de concurrencia con motor de producción. |
| **RF-ES-007** | Implementado | Rechazo con motivo y trazabilidad. **Pendiente / atención:** La razón debe redactarse apropiadamente por la estilista. |
| **RF-ES-008** | Implementado | Marca EN_PROCESO bajo transiciones válidas. **Pendiente / atención:** La presencia física la confirma la estilista, no hay sensor externo. |
| **RF-ES-009** | Implementado | Finalización explícita con fecha/hora de atención. **Pendiente / atención:** No se finalizan citas automáticamente al pasar su fecha. |
| **RF-ES-010** | Implementado | Adjuntos de sus citas con permiso de lectura. **Pendiente / atención:** Verificar tipos MIME permitidos en producción. |
| **RF-ES-011** | Implementado | Chat interno restringido a los participantes de la cita. **Pendiente / atención:** No es WebSocket en tiempo real. |
| **RF-ES-012** | Implementado | Pago manual con efectivo/transferencia y control de saldo. **Pendiente / atención:** No realiza cobros bancarios automáticamente. |
| **RF-ES-013** | Implementado | Reportes de la estilista y saldos por fechas. **Pendiente / atención:** Cifras basadas en registros de cobro existentes. |
| **RF-ES-014** | Implementado | Manual operativo del rol Estilista. **Pendiente / atención:** Revisar y actualizar cuando cambien flujos del salón. |

### Administrador

| Código | Estado | Implementación/limitación |
|---|---|---|
| **RF-AD-001** | Parcial | Administrador gestiona cuentas activas/inactivas para cliente, estilista y admin. **Pendiente / atención:** El rol recepcionista del requisito original fue excluido por la indicación posterior de clase; conversión de perfiles con citas previas se restringe. |
| **RF-AD-002** | Implementado | Alta y modificación de servicios, categorías, precios y duración. **Pendiente / atención:** La estructura de categorías se ajusta al catálogo del proyecto. |
| **RF-AD-003** | Implementado | Desactivación sin eliminar historial de citas. **Pendiente / atención:** No es eliminación irreversible. |
| **RF-AD-004** | Parcial | Visión central de citas por profesionales, estados y fecha. **Pendiente / atención:** Actualización por recarga; falta calendario maestro visual y canal en tiempo real. |
| **RF-AD-005** | Implementado | Reasigna citas con verificación de disponibilidad y bitácora. **Pendiente / atención:** Concurrencia avanzada requiere PostgreSQL en producción. |
| **RF-AD-006** | Implementado | Directorio de clientes, contacto y detalle de citas anteriores. **Pendiente / atención:** Solo accesible a administradores. |
| **RF-AD-007** | Implementado | Bloqueos por fechas para una profesional o todas las activas con validación de citas existentes. **Pendiente / atención:** Si hay citas confirmadas en el período, el cierre general se rechaza hasta resolverlas. |
| **RF-AD-008** | Parcial | Dashboard ingresos, citas, servicios populares y ocupación calculada. **Pendiente / atención:** Indicadores se actualizan con recarga y la ocupación es estimación. |
| **RF-AD-009** | Implementado | Consolidado de ingresos/saldos por fechas y profesional. **Pendiente / atención:** Los filtros se aplican a fecha de cita y registros de cobro. |
| **RF-AD-010** | Implementado | Exportación XLSX y PDF autenticada. **Pendiente / atención:** El PDF puede requerir mejoras para listas extensas. |
| **RF-AD-011** | Implementado | Auditoría de cobros: total, pagado y saldo. **Pendiente / atención:** Registro de pago manual. |
| **RF-AD-012** | Implementado | Bitácora consultable de acciones sobre citas y accesos. **Pendiente / atención:** Revisar políticas de retención y acceso antes del despliegue. |
| **RF-AD-013** | Implementado | Parámetros de antelación y cancelación por profesional. **Pendiente / atención:** No sustituye una política global de todas las estilistas. |
| **RF-AD-014** | Parcial | Ayuda operativa en panel y documentación de revisión. **Pendiente / atención:** No se han elaborado diagramas UML/Figma de documentación técnica completa (etapa posterior según apuntes verdes). |
| **RF-AD-015** | Implementado | Cliente puede contactar administración; admin puede responder. **Pendiente / atención:** Mensajería por recarga, no tiempo real. |
| **RF-AD-016** | Parcial | Supervisión de referencias y descarga autorizada. **Pendiente / atención:** Falta gestión avanzada de moderación/borrado del archivo y almacenamiento cloud. |
| **RF-AD-017** | Implementado | Cierre diario consolidando efectivo y transferencia con prevención de duplicados. **Pendiente / atención:** Verificar coordinación con el cierre legado de estilista y las políticas financieras. |
| **RF-AD-018** | Parcial | Respaldo consistente SQLite descargable por administrador; probado en base persistente. **Pendiente / atención:** No existe sincronización remota ni recuperación automatizada; en PostgreSQL debe configurarse estrategia del servidor. |

## Análisis detallado de los 166 escenarios por requisito

Los escenarios siguientes se extraen del Excel. La presencia de un escenario en esta matriz **no** implica que disponga de una prueba automatizada independiente. Para cada uno se conserva la numeración interna y su resultado esperado.

### RF-VI-001 — Visitante

**Necesidad:** Necesito registrarme como cliente mediante un formulario de datos personales, correo electrónico válido y contraseña; validar campos obligatorios y evitar cuentas con correo duplicado.
**Objetivo:** Para conocer Leidy Make Up y acceder posteriormente a sus servicios.
**Diagnóstico:** Implementado. Formulario de alta de cliente, contraseña validada, correo único y campos obligatorios.
**Código asociado:** `App_usuarios/forms.py; App_usuarios/views.py (registro_view); App_usuarios/models.py`
**Brecha:** El registro activa la cuenta inmediatamente y no pide verificación del correo, conforme al alcance actual; la validez sintáctica y unicidad se comprueban.

**Escenarios originales de aceptación:**

1. **Registro exitoso** — La persona no ha iniciado sesión y proporciona nombre, correo válido y una contraseña que cumple las reglas de seguridad. Cuando envía el formulario de registro con los campos requeridos completos. **Resultado esperado:** El sistema crea la cuenta con rol de cliente y su perfil asociado, y muestra un mensaje que indica que puede iniciar sesión.
2. **Campos obligatorios incompletos** — El formulario de registro contiene vacío el nombre, el correo o la contraseña. Cuando la persona intenta enviar el formulario. **Resultado esperado:** El sistema no crea la cuenta y muestra un mensaje solicitando completar los datos obligatorios.
3. **Correo inválido o ya registrado** — El correo no tiene un formato válido o ya está asociado a una cuenta existente. Cuando la persona envía el formulario de registro. **Resultado esperado:** El sistema rechaza el registro y muestra un mensaje de validación; no crea una cuenta duplicada.

### RF-VI-002 — Visitante

**Necesidad:** Necesito consultar públicamente el catálogo de servicios activos de Leidy Make Up, incluyendo descripción, precio y duración, sin necesidad de iniciar sesión; no mostrar servicios desactivados.
**Objetivo:** Para conocer Leidy Make Up y acceder posteriormente a sus servicios.
**Diagnóstico:** Implementado. Catálogo de servicios activos accesible sin autenticación.
**Código asociado:** `App_servicios/views.py; App_usuarios/templates/App_usuarios/home.html`
**Brecha:** Revisar presentación visual con datos comerciales reales.

**Escenarios originales de aceptación:**

1. **Consulta de servicios activos** — Existen servicios marcados como activos en el catálogo. Cuando el cliente abre la lista de servicios. **Resultado esperado:** El sistema muestra los servicios activos con la información registrada de cada uno.
2. **No hay servicios activos** — No existen servicios activos registrados. Cuando el cliente abre el catálogo. **Resultado esperado:** El sistema muestra el catálogo vacío o el mensaje informativo previsto, sin ofrecer servicios inactivos.
3. **Servicio desactivado** — Un servicio está marcado como inactivo. Cuando el cliente consulta el catálogo. **Resultado esperado:** El sistema no muestra el servicio inactivo en el catálogo del cliente.

### RF-VI-003 — Visitante

**Necesidad:** Necesito consultar fechas y franjas disponibles para un servicio activo sin iniciar sesión; indicar cuando no existan horarios y exigir autenticación antes de confirmar una reserva.
**Objetivo:** Para conocer Leidy Make Up y acceder posteriormente a sus servicios.
**Diagnóstico:** Parcial. Consulta pública de huecos; la confirmación de reserva exige sesión de cliente.
**Código asociado:** `App_agenda/views.py (disponibilidad); App_agenda/forms.py; App_agenda/templates/App_agenda/C_reservar_cita.html`
**Brecha:** La respuesta depende de horarios cargados; falta ensayo integral del calendario en navegadores.

**Escenarios originales de aceptación:**

1. **Consulta de horarios libres** — El visitante selecciona un servicio activo y una fecha válida. Cuando solicita consultar la disponibilidad. **Resultado esperado:** El sistema muestra las franjas calculadas con los horarios laborales y las reservas existentes, sin exigir inicio de sesión.
2. **Horario sin disponibilidad** — La fecha no tiene franjas disponibles por bloqueos, jornada o citas existentes. Cuando consulta esa fecha. **Resultado esperado:** El sistema informa que no hay horarios disponibles y permite elegir otra fecha.
3. **Intento de reservar sin sesión** — El visitante seleccionó servicio, fecha y hora, pero no ha iniciado sesión. Cuando intenta confirmar la solicitud de cita. **Resultado esperado:** El sistema solicita iniciar sesión antes de registrar la reserva; no crea una cita anónima.

### RF-CLI-001 — Cliente

**Necesidad:** Necesito registrarme en la plataforma como nuevo cliente con nombres, apellidos, correo electrónico único, teléfono y contraseña segura.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Por validar. Formulario actualizado para validar nombre, apellidos, teléfono, correo único y contraseña; falta ejecución de las pruebas en el equipo destino.
**Código asociado:** `App_usuarios/forms.py (RegistroClienteForm); App_usuarios/views.py (registro_view)`
**Brecha:** Ahora apellidos y teléfono son obligatorios; debe validarse el flujo completo mediante navegador y pruebas Django.

**Escenarios originales de aceptación:**

1. **Registro exitoso** — La persona no ha iniciado sesión y proporciona nombre, correo válido y una contraseña que cumple las reglas de seguridad. Cuando envía el formulario de registro con los campos requeridos completos. **Resultado esperado:** El sistema crea la cuenta con rol de cliente y su perfil asociado, y muestra un mensaje que indica que puede iniciar sesión.
2. **Campos obligatorios incompletos** — El formulario de registro contiene vacío el nombre, el correo o la contraseña. Cuando la persona intenta enviar el formulario. **Resultado esperado:** El sistema no crea la cuenta y muestra un mensaje solicitando completar los datos obligatorios.
3. **Correo inválido o ya registrado** — El correo no tiene un formato válido o ya está asociado a una cuenta existente. Cuando la persona envía el formulario de registro. **Resultado esperado:** El sistema rechaza el registro y muestra un mensaje de validación; no crea una cuenta duplicada.

### RF-CLI-002 — Cliente

**Necesidad:** Necesito iniciar sesión y cerrar sesión en la aplicación seleccionando el tipo de cuenta correspondiente.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Inicio y cierre de sesión; verificación estricta de rol real almacenado.
**Código asociado:** `App_usuarios/views.py (login_view,logout_view); App_usuarios/decorators.py; App_usuarios/templates/App_usuarios/C_login.html`
**Brecha:** Requiere contraseñas de usuarios reales para validación de aceptación final.

**Escenarios originales de aceptación:**

1. **Inicio de sesión válido** — La cuenta existe y las credenciales son correctas; el tipo de cuenta seleccionado coincide con el rol registrado. Cuando el usuario envía el formulario de inicio de sesión. **Resultado esperado:** El sistema autentica al usuario y lo dirige al inicio correspondiente a su rol.
2. **Credenciales incorrectas** — El usuario o la contraseña no corresponden a una cuenta válida. Cuando el usuario intenta iniciar sesión. **Resultado esperado:** El sistema no permite el acceso y muestra un mensaje de credenciales incorrectas.
3. **Tipo de cuenta no coincidente** — Las credenciales son válidas, pero el tipo de cuenta seleccionado no corresponde al rol del usuario. Cuando el usuario envía el formulario de inicio de sesión. **Resultado esperado:** El sistema rechaza el acceso con ese tipo de cuenta e informa que la selección no corresponde al usuario.
4. **Cierre de sesión** — El usuario tiene una sesión autenticada activa. Cuando selecciona la opción para cerrar sesión mediante la acción habilitada. **Resultado esperado:** El sistema cierra la sesión y redirige a la pantalla de inicio de sesión.

### RF-CLI-003 — Cliente

**Necesidad:** Necesito recuperar contraseña de acceso mediante enlace seguro enviado al correo electrónico registrado.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Parcial. Flujo Django de enlace con token y caducidad para restablecer contraseñas.
**Código asociado:** `App_usuarios/urls.py (PasswordResetView/ConfirmView); App_usuarios/templates/App_usuarios/recuperar_clave.html`
**Brecha:** El correo real requiere configurar y verificar servidor SMTP.

**Escenarios originales de aceptación:**

1. **Solicitud válida de recuperación** — Existe una cuenta asociada al correo proporcionado. Cuando el cliente solicita recuperar su contraseña. **Resultado esperado:** El sistema genera un enlace seguro de recuperación y tramita su envío al correo registrado.
2. **Correo no registrado** — El correo indicado no corresponde a una cuenta existente. Cuando se envía la solicitud de recuperación. **Resultado esperado:** El sistema presenta una respuesta que no revela innecesariamente la existencia de cuentas.
3. **Enlace vencido o inválido** — El enlace ha expirado o ya fue utilizado. Cuando se intenta restablecer la contraseña. **Resultado esperado:** El sistema rechaza el enlace e invita a solicitar uno nuevo.

### RF-CLI-004 — Cliente

**Necesidad:** Necesito consultar y actualizar la información de su perfil personal y número telefónico de contacto.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Cliente puede modificar datos, email único, teléfono y dirección.
**Código asociado:** `App_usuarios/views.py (perfil_view); App_usuarios/models.py (Cliente.direccion)`
**Brecha:** Sin prueba manual con navegador móvil.

**Escenarios originales de aceptación:**

1. **Actualización válida del perfil** — El cliente ha iniciado sesión y proporciona un correo válido que no pertenece a otra cuenta. Cuando guarda los cambios de nombre, apellido, correo o teléfono. **Resultado esperado:** El sistema guarda los datos modificados y muestra un mensaje de actualización exitosa.
2. **Correo con formato inválido** — El cliente introduce un correo que no cumple el formato requerido. Cuando intenta guardar el perfil. **Resultado esperado:** El sistema no guarda los cambios y muestra el error de validación del correo.
3. **Correo utilizado por otra cuenta** — El cliente introduce un correo que ya está asociado a otro usuario. Cuando intenta guardar el perfil. **Resultado esperado:** El sistema rechaza el cambio de correo y comunica que ya está asociado a otra cuenta.

### RF-CLI-005 — Cliente

**Necesidad:** Necesito consultar el catálogo interactivo de servicios de maquillaje y belleza (nombre, descripción, categoría, precio y duración).
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Catálogo con detalles y filtros de los servicios activos.
**Código asociado:** `App_servicios/views.py; App_servicios/models.py; App_servicios/templates`
**Brecha:** Comprobar accesibilidad de controles en navegadores reales.

**Escenarios originales de aceptación:**

1. **Consulta de servicios activos** — Existen servicios marcados como activos en el catálogo. Cuando el cliente abre la lista de servicios. **Resultado esperado:** El sistema muestra los servicios activos con la información registrada de cada uno.
2. **No hay servicios activos** — No existen servicios activos registrados. Cuando el cliente abre el catálogo. **Resultado esperado:** El sistema muestra el catálogo vacío o el mensaje informativo previsto, sin ofrecer servicios inactivos.
3. **Servicio desactivado** — Un servicio está marcado como inactivo. Cuando el cliente consulta el catálogo. **Resultado esperado:** El sistema no muestra el servicio inactivo en el catálogo del cliente.

### RF-CLI-006 — Cliente

**Necesidad:** Necesito visualizar calendario interactivo con indicación clara de días disponibles y días ocupados de la estilista.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Parcial. Selección de fecha con consulta de disponibilidad.
**Código asociado:** `App_agenda/views.py; App_agenda/templates/App_agenda/C_reservar_cita.html`
**Brecha:** No hay una garantía validada de calendario visual completo con todos los días libres/ocupados de cada estilista.

**Escenarios originales de aceptación:**

1. **Consulta del calendario** — El usuario ha iniciado sesión y existen citas visibles para su rol. Cuando abre el calendario y selecciona el periodo o vista disponible. **Resultado esperado:** El sistema muestra las citas correspondientes al calendario y periodo seleccionados.
2. **Calendario sin citas** — No existen citas en el periodo seleccionado que correspondan al usuario. Cuando abre el calendario para ese periodo. **Resultado esperado:** El sistema muestra el calendario sin eventos de citas ajenos al usuario.
3. **Acceso al calendario de estilista restringido** — El cliente está autenticado, pero no cuenta con permisos de estilista. Cuando intenta abrir el calendario privado de la estilista. **Resultado esperado:** El sistema deniega el acceso al calendario reservado para la estilista.

### RF-CLI-007 — Cliente

**Necesidad:** Necesito consultar las franjas horarias disponibles para una fecha seleccionada evitando solapamiento de turnos.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Cálculo de intervalos, duración y separaciones para evitar solapamientos.
**Código asociado:** `App_agenda/forms.py; App_agenda/views.py (disponibilidad)`
**Brecha:** SQLite requiere endurecer concurrencia con transacciones y pruebas de carga para producción.

**Escenarios originales de aceptación:**

1. **Consulta de franjas disponibles** — El cliente elige un servicio activo y fecha futura con jornada laboral. Cuando consulta las franjas horarias. **Resultado esperado:** El sistema muestra únicamente franjas disponibles que no se solapan con otras citas.
2. **Sin horarios libres** — No hay franjas habilitadas para la fecha y servicio. Cuando consulta disponibilidad. **Resultado esperado:** El sistema muestra un mensaje de ausencia de disponibilidad y permite cambiar la selección.
3. **Horario tomado por otra solicitud** — Una franja antes disponible queda ocupada. Cuando el cliente vuelve a consultar. **Resultado esperado:** El sistema actualiza la disponibilidad y no ofrece la franja ocupada.

### RF-CLI-008 — Cliente

**Necesidad:** Necesito solicitar reserva de cita seleccionando servicio, estilista preferida, fecha, horario disponible y nota informativa.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Reserva con servicio, estilista elegida, fecha, franja y notas; valida horario en servidor.
**Código asociado:** `App_agenda/views.py (reservar_cita); App_agenda/templates/App_agenda/C_reservar_cita.html`
**Brecha:** Confirmar visualmente el recorrido completo visitante→login→reserva.

**Escenarios originales de aceptación:**

1. **Solicitud en horario disponible** — El cliente está autenticado, el servicio está activo y la fecha no es pasada; el horario aparece disponible. Cuando selecciona el servicio, la estilista, la fecha y la hora, y envía la solicitud. **Resultado esperado:** El sistema registra la cita en estado pendiente y confirma que la solicitud fue enviada.
2. **Horario ocupado o que deja de estar disponible** — El horario se encuentra ocupado o deja de estar disponible antes de guardar la solicitud. Cuando el cliente intenta enviar la reserva para ese horario. **Resultado esperado:** El sistema no registra la solicitud en ese horario y muestra un mensaje para seleccionar otro horario.
3. **Fecha pasada o servicio inválido** — La fecha seleccionada es anterior a la fecha actual o el servicio no existe o está inactivo. Cuando el cliente consulta horarios o intenta enviar la solicitud. **Resultado esperado:** El sistema rechaza la consulta o la solicitud y comunica que debe seleccionar una fecha y un servicio válidos.
4. **Datos obligatorios inválidos** — Falta uno o más datos requeridos para reservar, o los datos no cumplen las validaciones del formulario. Cuando el cliente envía la solicitud. **Resultado esperado:** El sistema no crea la cita y señala los datos que deben corregirse.

### RF-CLI-009 — Cliente

**Necesidad:** Necesito adjuntar archivos multimedia o imágenes de referencia fotográfica del maquillaje o peinado deseado.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Archivos asociados a la cita con descarga protegida por autorización.
**Código asociado:** `App_agenda/models.py (CitaArchivo); App_agenda/views.py (guardar/descargar_adjuntos)`
**Brecha:** Almacenamiento cloud y compresión automática pendientes.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para adjuntar archivos multimedia o imágenes de referencia fotográfica del maquillaje o peinado deseado. Cuando el cliente solicita adjuntar archivos multimedia o imágenes de referencia fotográfica del maquillaje o peinado deseado. **Resultado esperado:** El sistema permite adjuntar archivos multimedia o imágenes de referencia fotográfica del maquillaje o peinado deseado y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta adjuntar archivos multimedia o imágenes de referencia fotográfica del maquillaje o peinado deseado sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita adjuntar archivos multimedia o imágenes de referencia fotográfica del maquillaje o peinado deseado bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-CLI-010 — Cliente

**Necesidad:** Necesito consultar el historial y estado de sus citas (Pendiente, Confirmada, En espera, En proceso, Completada, Cancelada).
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Historial de citas y estados conforme al modelo de negocio.
**Código asociado:** `App_agenda/views.py (panel/historial cliente); App_agenda/models.py (Cita)`
**Brecha:** El estado EN ESPERA en la UI se corresponde internamente con PENDIENTE.

**Escenarios originales de aceptación:**

1. **Consulta de citas propias** — El cliente ha iniciado sesión y tiene citas registradas. Cuando abre la sección de mis citas. **Resultado esperado:** El sistema muestra únicamente sus citas, con los datos del servicio, estilista, fecha, hora y estado disponibles.
2. **Cliente sin citas registradas** — El cliente ha iniciado sesión y no tiene citas asociadas. Cuando abre la sección de mis citas. **Resultado esperado:** El sistema muestra una lista vacía o un mensaje informativo, sin mostrar citas de otras personas.
3. **Cancelación de cita pendiente o confirmada** — La cita pertenece al cliente autenticado y está pendiente o confirmada. Cuando el cliente solicita cancelar esa cita. **Resultado esperado:** El sistema cambia el estado de la cita a cancelada y muestra una confirmación.
4. **Cancelación no permitida** — La cita no pertenece al cliente autenticado o su estado no es pendiente ni confirmado. Cuando el cliente intenta cancelar la cita. **Resultado esperado:** El sistema impide la operación y no modifica una cita ajena o no elegible.

### RF-CLI-011 — Cliente

**Necesidad:** Necesito cancelar una cita agendada con antelación mínima requerida (al menos 2 horas antes de la hora fijada).
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Controla antelación mínima de cancelación según política.
**Código asociado:** `App_agenda/views.py (cancelar_cita); App_agenda/forms.py`
**Brecha:** La ventana de cancelación puede ser ajustada mediante parámetros.

**Escenarios originales de aceptación:**

1. **Cancelación permitida** — El cliente tiene una cita propia cancelable y faltan al menos dos horas para su inicio. Cuando confirma la cancelación. **Resultado esperado:** El sistema cancela la cita, actualiza su estado y libera la franja conforme a las reglas.
2. **Cancelación fuera del plazo** — Faltan menos de dos horas para la cita. Cuando el cliente intenta cancelarla. **Resultado esperado:** El sistema impide la cancelación ordinaria e informa la restricción.
3. **Cancelación de cita ajena** — El cliente intenta acceder a una cita de otra cuenta. Cuando envía la solicitud. **Resultado esperado:** El sistema deniega la operación y mantiene la cita sin cambios.

### RF-CLI-012 — Cliente

**Necesidad:** Necesito reprogramar fecha y hora de una cita en estado pendiente sujeta a disponibilidad de la estilista.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Reprogramación limitada a estados permitidos y huecos válidos.
**Código asociado:** `App_agenda/views.py (reprogramar_cita); App_agenda/forms.py`
**Brecha:** Requiere validación de simultaneidad en producción.

**Escenarios originales de aceptación:**

1. **Cambio válido de cita pendiente** — La cita pertenece al cliente, está pendiente y la nueva franja está libre. Cuando solicita reprogramarla. **Resultado esperado:** El sistema actualiza fecha y hora, revalida disponibilidad y conserva el historial correspondiente.
2. **Franja alternativa ocupada** — La nueva franja se solapa con una cita existente. Cuando se intenta reprogramar. **Resultado esperado:** El sistema rechaza el cambio y mantiene la programación anterior.
3. **Cita en estado no permitido** — La cita está confirmada, cancelada o terminada. Cuando el cliente solicita cambiarla. **Resultado esperado:** El sistema impide la reprogramación e informa las condiciones permitidas.

### RF-CLI-013 — Cliente

**Necesidad:** Necesito recibir notificaciones en tiempo real sobre la confirmación, rechazo, recordatorio o cambio de estado de su cita.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Parcial. Avisos internos de cambios y recordatorios programables.
**Código asociado:** `App_agenda/models.py (Notificacion); App_agenda/management/commands/recordatorios_citas.py`
**Brecha:** No hay push en tiempo real (WebSocket) ni planificador externo activo por defecto.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para recibir notificaciones en tiempo real sobre la confirmación, rechazo, recordatorio o cambio de estado de su cita. Cuando el cliente solicita recibir notificaciones en tiempo real sobre la confirmación, rechazo, recordatorio o cambio de estado de su cita. **Resultado esperado:** El sistema permite recibir notificaciones en tiempo real sobre la confirmación, rechazo, recordatorio o cambio de estado de su cita y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta recibir notificaciones en tiempo real sobre la confirmación, rechazo, recordatorio o cambio de estado de su cita sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita recibir notificaciones en tiempo real sobre la confirmación, rechazo, recordatorio o cambio de estado de su cita bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-CLI-014 — Cliente

**Necesidad:** Necesito enviar y recibir mensajes de chat interno con la estilista asignada para resolver dudas sobre el servicio a prestar.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Mensajería interna entre cliente y estilista de sus citas.
**Código asociado:** `App_agenda/views.py (mensajes); App_agenda/models.py (Mensaje)`
**Brecha:** No sustituye mensajería instantánea con entrega en vivo.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para enviar y recibir mensajes de chat interno con la estilista asignada para resolver dudas sobre el servicio a prestar. Cuando el cliente solicita enviar y recibir mensajes de chat interno con la estilista asignada para resolver dudas sobre el servicio a prestar. **Resultado esperado:** El sistema permite enviar y recibir mensajes de chat interno con la estilista asignada para resolver dudas sobre el servicio a prestar y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta enviar y recibir mensajes de chat interno con la estilista asignada para resolver dudas sobre el servicio a prestar sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita enviar y recibir mensajes de chat interno con la estilista asignada para resolver dudas sobre el servicio a prestar bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-CLI-015 — Cliente

**Necesidad:** Necesito consultar el resumen de liquidación de su cita (costo del servicio, monto abonado y saldo pendiente por pagar).
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Muestra total del servicio, pagos y saldo pendiente.
**Código asociado:** `App_facturacion/models.py (RegistroCobro); App_facturacion/views.py`
**Brecha:** El saldo refleja abonos introducidos manualmente.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para consultar el resumen de liquidación de su cita (costo del servicio, monto abonado y saldo pendiente por pagar). Cuando el cliente solicita consultar el resumen de liquidación de su cita (costo del servicio, monto abonado y saldo pendiente por pagar). **Resultado esperado:** El sistema permite consultar el resumen de liquidación de su cita (costo del servicio, monto abonado y saldo pendiente por pagar) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta consultar el resumen de liquidación de su cita (costo del servicio, monto abonado y saldo pendiente por pagar) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita consultar el resumen de liquidación de su cita (costo del servicio, monto abonado y saldo pendiente por pagar) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-CLI-016 — Cliente

**Necesidad:** Necesito seleccionar método de pago preferido para registrar abonos o pagos de la cita (efectivo o transferencia bancaria).
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Parcial. Selección de método efectivo/transferencia y registro de pagos por profesional.
**Código asociado:** `App_agenda/models.py (metodo_pago_preferido); App_facturacion/views.py`
**Brecha:** No existe pasarela bancaria ni confirmación automática de transferencias.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para seleccionar método de pago preferido para registrar abonos o pagos de la cita (efectivo o transferencia bancaria). Cuando el cliente solicita seleccionar método de pago preferido para registrar abonos o pagos de la cita (efectivo o transferencia bancaria). **Resultado esperado:** El sistema permite seleccionar método de pago preferido para registrar abonos o pagos de la cita (efectivo o transferencia bancaria) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta seleccionar método de pago preferido para registrar abonos o pagos de la cita (efectivo o transferencia bancaria) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita seleccionar método de pago preferido para registrar abonos o pagos de la cita (efectivo o transferencia bancaria) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-CLI-017 — Cliente

**Necesidad:** Necesito visualizar comprobante o recibo digital de la cita y del pago registrado en el sistema.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Recibo digital accesible con control de permisos.
**Código asociado:** `App_facturacion/views.py (comprobante/recibo); App_facturacion/urls.py`
**Brecha:** No equivale a factura electrónica DIAN.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para visualizar comprobante o recibo digital de la cita y del pago registrado en el sistema. Cuando el cliente solicita visualizar comprobante o recibo digital de la cita y del pago registrado en el sistema. **Resultado esperado:** El sistema permite visualizar comprobante o recibo digital de la cita y del pago registrado en el sistema y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta visualizar comprobante o recibo digital de la cita y del pago registrado en el sistema sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita visualizar comprobante o recibo digital de la cita y del pago registrado en el sistema bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-CLI-018 — Cliente

**Necesidad:** Necesito visualizar manual de usuario interactivo y preguntas frecuentes sobre el proceso de reserva.
**Objetivo:** Para gestionar mis servicios, citas y datos de manera autónoma.
**Diagnóstico:** Implementado. Manual y ayuda para clientes.
**Código asociado:** `App_usuarios/views.py (ayuda_view); App_usuarios/templates/App_usuarios/C_ayuda.html`
**Brecha:** Su contenido deberá revisarse después de incorporar módulos futuros.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El cliente ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para visualizar manual de usuario interactivo y preguntas frecuentes sobre el proceso de reserva. Cuando el cliente solicita visualizar manual de usuario interactivo y preguntas frecuentes sobre el proceso de reserva. **Resultado esperado:** El sistema permite visualizar manual de usuario interactivo y preguntas frecuentes sobre el proceso de reserva y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el cliente intenta visualizar manual de usuario interactivo y preguntas frecuentes sobre el proceso de reserva sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita visualizar manual de usuario interactivo y preguntas frecuentes sobre el proceso de reserva bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-ES-001 — Estilista

**Necesidad:** Necesito iniciar sesión y autenticarme con credenciales asignadas con rol de estilista profesional.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Login estilista explícito y autorización comprobada por cada vista.
**Código asociado:** `App_usuarios/views.py (e_login); App_usuarios/decorators.py`
**Brecha:** Cuenta debe tener el rol estilista en BD.

**Escenarios originales de aceptación:**

1. **Inicio de sesión válido** — La cuenta existe y las credenciales son correctas; el tipo de cuenta seleccionado coincide con el rol registrado. Cuando el usuario envía el formulario de inicio de sesión. **Resultado esperado:** El sistema autentica al usuario y lo dirige al inicio correspondiente a su rol.
2. **Credenciales incorrectas** — El usuario o la contraseña no corresponden a una cuenta válida. Cuando el usuario intenta iniciar sesión. **Resultado esperado:** El sistema no permite el acceso y muestra un mensaje de credenciales incorrectas.
3. **Tipo de cuenta no coincidente** — Las credenciales son válidas, pero el tipo de cuenta seleccionado no corresponde al rol del usuario. Cuando el usuario envía el formulario de inicio de sesión. **Resultado esperado:** El sistema rechaza el acceso con ese tipo de cuenta e informa que la selección no corresponde al usuario.
4. **Cierre de sesión** — El usuario tiene una sesión autenticada activa. Cuando selecciona la opción para cerrar sesión mediante la acción habilitada. **Resultado esperado:** El sistema cierra la sesión y redirige a la pantalla de inicio de sesión.

### RF-ES-002 — Estilista

**Necesidad:** Necesito consultar su agenda personal y calendario de citas por vista diaria, semanal y mensual.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Parcial. Agenda de estilista con citas y filtros.
**Código asociado:** `App_agenda/views.py (e_inicio, agenda); App_agenda/templates`
**Brecha:** No se verificó una presentación diferenciada funcional de día, semana y mes.

**Escenarios originales de aceptación:**

1. **Consulta del calendario** — El usuario ha iniciado sesión y existen citas visibles para su rol. Cuando abre el calendario y selecciona el periodo o vista disponible. **Resultado esperado:** El sistema muestra las citas correspondientes al calendario y periodo seleccionados.
2. **Calendario sin citas** — No existen citas en el periodo seleccionado que correspondan al usuario. Cuando abre el calendario para ese periodo. **Resultado esperado:** El sistema muestra el calendario sin eventos de citas ajenos al usuario.
3. **Acceso restringido al calendario** — El usuario no dispone del rol de estilista autorizado. Cuando intenta ingresar al calendario de la estilista. **Resultado esperado:** El sistema impide el acceso y no expone las citas ajenas.

### RF-ES-003 — Estilista

**Necesidad:** Necesito configurar y actualizar horarios laborales de atención disponibles (días de la semana, hora de inicio y hora fin).
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Configuración de horarios semanales y pausas/bloqueos.
**Código asociado:** `App_usuarios/views.py (configuracion_view); App_agenda/models.py (Horario)`
**Brecha:** Un horario ausente implica ninguna franja reservable.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El estilista ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para configurar y actualizar horarios laborales de atención disponibles (días de la semana, hora de inicio y hora fin). Cuando el estilista solicita configurar y actualizar horarios laborales de atención disponibles (días de la semana, hora de inicio y hora fin). **Resultado esperado:** El sistema permite configurar y actualizar horarios laborales de atención disponibles (días de la semana, hora de inicio y hora fin) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el estilista intenta configurar y actualizar horarios laborales de atención disponibles (días de la semana, hora de inicio y hora fin) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita configurar y actualizar horarios laborales de atención disponibles (días de la semana, hora de inicio y hora fin) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-ES-004 — Estilista

**Necesidad:** Necesito actualizar información de especialidad estética y datos profesionales visibles para las clientas.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Especialidad editable y expuesta al escoger estilista en la reserva.
**Código asociado:** `App_usuarios/models.py (Estilista.especialidad); App_usuarios/views.py (configuracion_view); App_agenda/templates/App_agenda/C_reservar_cita.html`
**Brecha:** Las descripciones profesionales adicionales no están desarrolladas.

**Escenarios originales de aceptación:**

1. **Actualización de especialidad** — La estilista ha iniciado sesión y accede a la configuración de su perfil. Cuando modifica y guarda el campo de especialidad. **Resultado esperado:** El sistema guarda la especialidad y muestra un mensaje de actualización exitosa.
2. **Consulta de horarios activos** — La estilista tiene horarios laborales activos registrados. Cuando abre la configuración de su perfil. **Resultado esperado:** El sistema muestra los horarios activos ordenados por día y hora.
3. **Acceso no autorizado** — El usuario autenticado no tiene rol de estilista. Cuando intenta acceder a la configuración de estilista. **Resultado esperado:** El sistema impide el acceso a la configuración restringida.

### RF-ES-005 — Estilista

**Necesidad:** Necesito consultar lista de solicitudes de citas pendientes con detalle del cliente, servicio y notas adicionales.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Listado y detalle de citas PENDIENTE con cliente, servicio y nota.
**Código asociado:** `App_agenda/views.py (solicitudes pendientes); App_agenda/models.py`
**Brecha:** Los adjuntos se acceden desde la cita protegida.

**Escenarios originales de aceptación:**

1. **Consulta de solicitudes** — La estilista ha iniciado sesión y existen solicitudes asociadas a ella. Cuando abre la sección de solicitudes y selecciona un filtro de estado válido. **Resultado esperado:** El sistema muestra las solicitudes de esa estilista filtradas por el estado seleccionado.
2. **Aceptación de solicitud disponible** — La solicitud pertenece a la estilista, está pendiente y su intervalo no se superpone con otra solicitud activa. Cuando la estilista acepta la solicitud. **Resultado esperado:** El sistema cambia el estado a confirmada y registra la información de aceptación.
3. **Aceptación con conflicto de horario** — La solicitud está pendiente, pero su intervalo se superpone con otra cita activa de la estilista. Cuando la estilista intenta aceptarla. **Resultado esperado:** El sistema no confirma la solicitud y muestra un mensaje indicando el conflicto de horario.
4. **Rechazo de solicitud pendiente** — La solicitud pertenece a la estilista autenticada y está pendiente. Cuando la estilista la rechaza. **Resultado esperado:** El sistema cambia el estado de la solicitud a rechazada y muestra la confirmación correspondiente.

### RF-ES-006 — Estilista

**Necesidad:** Necesito aceptar solicitudes de citas verificando automáticamente la no superposición de horarios en agenda.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Confirmación de solicitud con verificación de disponibilidad.
**Código asociado:** `App_agenda/views.py (confirmar_cita); App_agenda/forms.py`
**Brecha:** Se requieren pruebas de concurrencia con motor de producción.

**Escenarios originales de aceptación:**

1. **Cambio de estado válido** — La cita está asignada a la estilista y cumple las condiciones para aceptar. Cuando la estilista decide aceptar la cita. **Resultado esperado:** El sistema actualiza el estado de la cita, registra el cambio y lo refleja en la agenda.
2. **Cita en estado incompatible** — La cita está cancelada, finalizada o tiene un estado incompatible con la acción. Cuando la estilista intenta cambiar el estado. **Resultado esperado:** El sistema rechaza el cambio y conserva el estado anterior.
3. **Cita de otra profesional** — La solicitud pertenece a otra estilista. Cuando se intenta ejecutar la acción. **Resultado esperado:** El sistema impide modificar citas ajenas y mantiene los datos originales.

### RF-ES-007 — Estilista

**Necesidad:** Necesito rechazar solicitudes de citas no compatibles con la disponibilidad operativa con justificación informativa.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Rechazo con motivo y trazabilidad.
**Código asociado:** `App_agenda/views.py (rechazar_cita)`
**Brecha:** La razón debe redactarse apropiadamente por la estilista.

**Escenarios originales de aceptación:**

1. **Cambio de estado válido** — La cita está asignada a la estilista y cumple las condiciones para rechazar. Cuando la estilista decide rechazar la cita. **Resultado esperado:** El sistema actualiza el estado de la cita, registra el cambio y lo refleja en la agenda.
2. **Cita en estado incompatible** — La cita está cancelada, finalizada o tiene un estado incompatible con la acción. Cuando la estilista intenta cambiar el estado. **Resultado esperado:** El sistema rechaza el cambio y conserva el estado anterior.
3. **Cita de otra profesional** — La solicitud pertenece a otra estilista. Cuando se intenta ejecutar la acción. **Resultado esperado:** El sistema impide modificar citas ajenas y mantiene los datos originales.

### RF-ES-008 — Estilista

**Necesidad:** Necesito marcar cita en estado 'En proceso' una vez el cliente se presenta físicamente en las instalaciones.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Marca EN_PROCESO bajo transiciones válidas.
**Código asociado:** `App_agenda/views.py (iniciar_atencion)`
**Brecha:** La presencia física la confirma la estilista, no hay sensor externo.

**Escenarios originales de aceptación:**

1. **Cambio de estado válido** — La cita está asignada a la estilista y cumple las condiciones para marcar en proceso. Cuando la estilista decide marcar en proceso la cita. **Resultado esperado:** El sistema actualiza el estado de la cita, registra el cambio y lo refleja en la agenda.
2. **Cita en estado incompatible** — La cita está cancelada, finalizada o tiene un estado incompatible con la acción. Cuando la estilista intenta cambiar el estado. **Resultado esperado:** El sistema rechaza el cambio y conserva el estado anterior.
3. **Cita de otra profesional** — La solicitud pertenece a otra estilista. Cuando se intenta ejecutar la acción. **Resultado esperado:** El sistema impide modificar citas ajenas y mantiene los datos originales.

### RF-ES-009 — Estilista

**Necesidad:** Necesito marcar cita como 'Finalizada' registrando la fecha y hora exacta de culminación del servicio prestado.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Finalización explícita con fecha/hora de atención.
**Código asociado:** `App_agenda/views.py (finalizar_cita); App_agenda/models.py`
**Brecha:** No se finalizan citas automáticamente al pasar su fecha.

**Escenarios originales de aceptación:**

1. **Finalización de cita válida** — La cita está asociada a la estilista autenticada y se encuentra en un estado que permite completarla. Cuando la estilista ejecuta la acción de completar la cita. **Resultado esperado:** El sistema cambia el estado de la cita a finalizada y registra la fecha de finalización.
2. **Cita no disponible para completar** — La cita no pertenece a la estilista autenticada o no cumple el estado requerido para completarse. Cuando la estilista intenta marcarla como finalizada. **Resultado esperado:** El sistema impide la operación y conserva el estado de la cita.
3. **Consulta posterior** — La cita ya fue marcada como finalizada. Cuando la estilista vuelve a consultar el calendario o los detalles de la cita. **Resultado esperado:** El sistema refleja el estado finalizado según las reglas de presentación del calendario.

### RF-ES-010 — Estilista

**Necesidad:** Necesito visualizar imágenes de referencia fotográfica y especificaciones adjuntas por la clienta para el servicio.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Adjuntos de sus citas con permiso de lectura.
**Código asociado:** `App_agenda/views.py (descargar_adjunto)`
**Brecha:** Verificar tipos MIME permitidos en producción.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El estilista ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para visualizar imágenes de referencia fotográfica y especificaciones adjuntas por la clienta para el servicio. Cuando el estilista solicita visualizar imágenes de referencia fotográfica y especificaciones adjuntas por la clienta para el servicio. **Resultado esperado:** El sistema permite visualizar imágenes de referencia fotográfica y especificaciones adjuntas por la clienta para el servicio y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el estilista intenta visualizar imágenes de referencia fotográfica y especificaciones adjuntas por la clienta para el servicio sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita visualizar imágenes de referencia fotográfica y especificaciones adjuntas por la clienta para el servicio bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-ES-011 — Estilista

**Necesidad:** Necesito mantener comunicación directa por mensajes con las clientas asociadas a sus citas programadas.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Chat interno restringido a los participantes de la cita.
**Código asociado:** `App_agenda/views.py (mensajes)`
**Brecha:** No es WebSocket en tiempo real.

**Escenarios originales de aceptación:**

1. **Consulta de clientes asociados** — La estilista ha iniciado sesión y tiene clientes asociados a sus citas. Cuando abre la sección de clientes. **Resultado esperado:** El sistema muestra la información de los clientes relacionados con sus citas.
2. **Envío de mensaje válido** — Existe un contacto de conversación determinado y el mensaje contiene entre 1 y 2000 caracteres. Cuando la estilista envía el mensaje. **Resultado esperado:** El sistema registra el mensaje con remitente, destinatario y fecha de creación.
3. **Mensaje vacío o demasiado largo** — El contenido está vacío o supera los 2000 caracteres. Cuando el usuario intenta enviar el mensaje. **Resultado esperado:** El sistema no registra el mensaje y muestra una indicación para corregir el contenido.
4. **Consulta de conversación** — Hay mensajes entre el usuario autenticado y el contacto permitido. Cuando abre la sección de mensajes. **Resultado esperado:** El sistema muestra la conversación correspondiente y marca como leídos los mensajes recibidos que se consultan.

### RF-ES-012 — Estilista

**Necesidad:** Necesito registrar cobros, abonos recibidos y registrar método de pago en el módulo de cobro de la cita.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Pago manual con efectivo/transferencia y control de saldo.
**Código asociado:** `App_facturacion/views.py; App_facturacion/servicios.py`
**Brecha:** No realiza cobros bancarios automáticamente.

**Escenarios originales de aceptación:**

1. **Consulta de registros de cobro** — La estilista ha iniciado sesión y existen registros de cobro asociados a sus citas. Cuando abre la sección de inventario o registros de cobro. **Resultado esperado:** El sistema muestra los registros correspondientes, el cliente, el servicio, la fecha, el monto y el saldo pendiente.
2. **No existen registros de cobro** — No hay registros de cobro asociados a las citas de la estilista. Cuando abre la sección de inventario. **Resultado esperado:** El sistema muestra una lista vacía y los totales en cero, sin exponer registros de otra estilista.
3. **Cálculo de resumen de saldos** — Existen registros de cobro con saldos pendientes. Cuando la estilista consulta el resumen del inventario. **Resultado esperado:** El sistema muestra el total pendiente calculado a partir de los registros que corresponden a la estilista.

### RF-ES-013 — Estilista

**Necesidad:** Necesito consultar reporte de ingresos propios devengados y saldos pendientes de liquidación por rango de fechas.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Reportes de la estilista y saldos por fechas.
**Código asociado:** `App_facturacion/views.py (reportes); App_facturacion/models.py`
**Brecha:** Cifras basadas en registros de cobro existentes.

**Escenarios originales de aceptación:**

1. **Consulta de reporte con datos** — Existen registros de cobro de citas confirmadas con pagos registrados. Cuando la estilista abre los reportes. **Resultado esperado:** El sistema muestra los registros que cumplen los filtros del reporte, los ingresos, los saldos pendientes y el resumen mensual disponible.
2. **Filtrado por periodo válido** — La fecha inicial y la fecha final tienen un formato válido y forman un periodo permitido. Cuando la estilista aplica el filtro por fechas. **Resultado esperado:** El sistema calcula y muestra el total del periodo con los registros que cumplen los criterios.
3. **Rango de fechas inválido** — La fecha tiene un formato inválido o la fecha inicial es posterior a la fecha final. Cuando la estilista aplica el filtro por fechas. **Resultado esperado:** El sistema informa el error de fechas y no presenta el rango inválido como un reporte válido.
4. **Reporte sin resultados** — No hay registros que cumplan los filtros seleccionados. Cuando la estilista consulta el reporte o aplica un periodo sin movimientos. **Resultado esperado:** El sistema muestra resultados vacíos y totales en cero para el periodo consultado.

### RF-ES-014 — Estilista

**Necesidad:** Necesito visualizar manual de usuario operativo con flujos y funciones asignadas al rol de estilista.
**Objetivo:** Para organizar mi trabajo y atender correctamente las citas del salón.
**Diagnóstico:** Implementado. Manual operativo del rol Estilista.
**Código asociado:** `App_usuarios/views.py (ayuda_view); App_usuarios/templates/App_usuarios/E_ayuda.html`
**Brecha:** Revisar y actualizar cuando cambien flujos del salón.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El estilista ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para visualizar manual de usuario operativo con flujos y funciones asignadas al rol de estilista. Cuando el estilista solicita visualizar manual de usuario operativo con flujos y funciones asignadas al rol de estilista. **Resultado esperado:** El sistema permite visualizar manual de usuario operativo con flujos y funciones asignadas al rol de estilista y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el estilista intenta visualizar manual de usuario operativo con flujos y funciones asignadas al rol de estilista sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita visualizar manual de usuario operativo con flujos y funciones asignadas al rol de estilista bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-001 — Administrador

**Necesidad:** Necesito gestionar cuentas y roles de usuarios (crear, consultar, actualizar, activar y desactivar perfiles de estilistas, recepcionistas y clientes).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Parcial. Administrador gestiona cuentas activas/inactivas para cliente, estilista y admin.
**Código asociado:** `App_administracion/views.py (usuarios,usuario_crear,usuario_editar,usuario_estado); App_administracion/forms.py`
**Brecha:** El rol recepcionista del requisito original fue excluido por la indicación posterior de clase; conversión de perfiles con citas previas se restringe.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para gestionar cuentas y roles de usuarios (crear, consultar, actualizar, activar y desactivar perfiles de estilistas, recepcionistas y clientes). Cuando el administrador solicita gestionar cuentas y roles de usuarios (crear, consultar, actualizar, activar y desactivar perfiles de estilistas, recepcionistas y clientes). **Resultado esperado:** El sistema permite gestionar cuentas y roles de usuarios (crear, consultar, actualizar, activar y desactivar perfiles de estilistas, recepcionistas y clientes) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta gestionar cuentas y roles de usuarios (crear, consultar, actualizar, activar y desactivar perfiles de estilistas, recepcionistas y clientes) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita gestionar cuentas y roles de usuarios (crear, consultar, actualizar, activar y desactivar perfiles de estilistas, recepcionistas y clientes) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-002 — Administrador

**Necesidad:** Necesito configurar catálogo y categorías de servicios de estética y maquillaje (nombre, descripción, duración estimada y precio estándar).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Alta y modificación de servicios, categorías, precios y duración.
**Código asociado:** `App_administracion/views.py (servicios,servicio_editar); App_administracion/forms.py`
**Brecha:** La estructura de categorías se ajusta al catálogo del proyecto.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para configurar catálogo y categorías de servicios de estética y maquillaje (nombre, descripción, duración estimada y precio estándar). Cuando el administrador solicita configurar catálogo y categorías de servicios de estética y maquillaje (nombre, descripción, duración estimada y precio estándar). **Resultado esperado:** El sistema permite configurar catálogo y categorías de servicios de estética y maquillaje (nombre, descripción, duración estimada y precio estándar) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta configurar catálogo y categorías de servicios de estética y maquillaje (nombre, descripción, duración estimada y precio estándar) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita configurar catálogo y categorías de servicios de estética y maquillaje (nombre, descripción, duración estimada y precio estándar) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-003 — Administrador

**Necesidad:** Necesito desactivar servicios del catálogo manteniendo la integridad histórica y referencial de las citas registradas previamente.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Desactivación sin eliminar historial de citas.
**Código asociado:** `App_administracion/views.py (servicio_estado); App_servicios/models.py`
**Brecha:** No es eliminación irreversible.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para desactivar servicios del catálogo manteniendo la integridad histórica y referencial de las citas registradas previamente. Cuando el administrador solicita desactivar servicios del catálogo manteniendo la integridad histórica y referencial de las citas registradas previamente. **Resultado esperado:** El sistema permite desactivar servicios del catálogo manteniendo la integridad histórica y referencial de las citas registradas previamente y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta desactivar servicios del catálogo manteniendo la integridad histórica y referencial de las citas registradas previamente sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita desactivar servicios del catálogo manteniendo la integridad histórica y referencial de las citas registradas previamente bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-004 — Administrador

**Necesidad:** Necesito supervisar el calendario maestro y agenda global con visualización en tiempo real de todas las citas y estados por estilista.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Parcial. Visión central de citas por profesionales, estados y fecha.
**Código asociado:** `App_administracion/views.py (agenda)`
**Brecha:** Actualización por recarga; falta calendario maestro visual y canal en tiempo real.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para supervisar el calendario maestro y agenda global con visualización en tiempo real de todas las citas y estados por estilista. Cuando el administrador solicita supervisar el calendario maestro y agenda global con visualización en tiempo real de todas las citas y estados por estilista. **Resultado esperado:** El sistema permite supervisar el calendario maestro y agenda global con visualización en tiempo real de todas las citas y estados por estilista y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta supervisar el calendario maestro y agenda global con visualización en tiempo real de todas las citas y estados por estilista sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita supervisar el calendario maestro y agenda global con visualización en tiempo real de todas las citas y estados por estilista bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-005 — Administrador

**Necesidad:** Necesito reasignar citas y turnos entre estilistas disponibles ante contingencias o cambios de turno operacional.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Reasigna citas con verificación de disponibilidad y bitácora.
**Código asociado:** `App_administracion/views.py (reasignar)`
**Brecha:** Concurrencia avanzada requiere PostgreSQL en producción.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para reasignar citas y turnos entre estilistas disponibles ante contingencias o cambios de turno operacional. Cuando el administrador solicita reasignar citas y turnos entre estilistas disponibles ante contingencias o cambios de turno operacional. **Resultado esperado:** El sistema permite reasignar citas y turnos entre estilistas disponibles ante contingencias o cambios de turno operacional y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta reasignar citas y turnos entre estilistas disponibles ante contingencias o cambios de turno operacional sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita reasignar citas y turnos entre estilistas disponibles ante contingencias o cambios de turno operacional bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-006 — Administrador

**Necesidad:** Necesito consultar el directorio de clientes con historial de servicios recibidos, citas previas, cancelaciones y teléfonos de contacto.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Directorio de clientes, contacto y detalle de citas anteriores.
**Código asociado:** `App_administracion/views.py (clientes)`
**Brecha:** Solo accesible a administradores.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para consultar el directorio de clientes con historial de servicios recibidos, citas previas, cancelaciones y teléfonos de contacto. Cuando el administrador solicita consultar el directorio de clientes con historial de servicios recibidos, citas previas, cancelaciones y teléfonos de contacto. **Resultado esperado:** El sistema permite consultar el directorio de clientes con historial de servicios recibidos, citas previas, cancelaciones y teléfonos de contacto y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta consultar el directorio de clientes con historial de servicios recibidos, citas previas, cancelaciones y teléfonos de contacto sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita consultar el directorio de clientes con historial de servicios recibidos, citas previas, cancelaciones y teléfonos de contacto bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-007 — Administrador

**Necesidad:** Necesito configurar parámetros de bloqueo de agenda general por días festivos, capacitaciones o descansos del salón.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Bloqueos por fechas para una profesional o todas las activas con validación de citas existentes.
**Código asociado:** `App_administracion/views.py (bloquear); App_agenda/models.py (BloqueoAgenda)`
**Brecha:** Si hay citas confirmadas en el período, el cierre general se rechaza hasta resolverlas.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para configurar parámetros de bloqueo de agenda general por días festivos, capacitaciones o descansos del salón. Cuando el administrador solicita configurar parámetros de bloqueo de agenda general por días festivos, capacitaciones o descansos del salón. **Resultado esperado:** El sistema permite configurar parámetros de bloqueo de agenda general por días festivos, capacitaciones o descansos del salón y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta configurar parámetros de bloqueo de agenda general por días festivos, capacitaciones o descansos del salón sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita configurar parámetros de bloqueo de agenda general por días festivos, capacitaciones o descansos del salón bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-008 — Administrador

**Necesidad:** Necesito visualizar dashboard administrativo con métricas en tiempo real (ingresos del día/mes, citas totales, servicios más solicitados y tasa de ocupación).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Parcial. Dashboard ingresos, citas, servicios populares y ocupación calculada.
**Código asociado:** `App_administracion/views.py (inicio)`
**Brecha:** Indicadores se actualizan con recarga y la ocupación es estimación.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para visualizar dashboard administrativo con métricas en tiempo real (ingresos del día/mes, citas totales, servicios más solicitados y tasa de ocupación). Cuando el administrador solicita visualizar dashboard administrativo con métricas en tiempo real (ingresos del día/mes, citas totales, servicios más solicitados y tasa de ocupación). **Resultado esperado:** El sistema permite visualizar dashboard administrativo con métricas en tiempo real (ingresos del día/mes, citas totales, servicios más solicitados y tasa de ocupación) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta visualizar dashboard administrativo con métricas en tiempo real (ingresos del día/mes, citas totales, servicios más solicitados y tasa de ocupación) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita visualizar dashboard administrativo con métricas en tiempo real (ingresos del día/mes, citas totales, servicios más solicitados y tasa de ocupación) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-009 — Administrador

**Necesidad:** Necesito generar reportes consolidados de ingresos y saldos pendientes con filtros por rangos de fechas y por profesional.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Consolidado de ingresos/saldos por fechas y profesional.
**Código asociado:** `App_administracion/views.py (_reporte_base, reportes)`
**Brecha:** Los filtros se aplican a fecha de cita y registros de cobro.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para generar reportes consolidados de ingresos y saldos pendientes con filtros por rangos de fechas y por profesional. Cuando el administrador solicita generar reportes consolidados de ingresos y saldos pendientes con filtros por rangos de fechas y por profesional. **Resultado esperado:** El sistema permite generar reportes consolidados de ingresos y saldos pendientes con filtros por rangos de fechas y por profesional y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta generar reportes consolidados de ingresos y saldos pendientes con filtros por rangos de fechas y por profesional sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita generar reportes consolidados de ingresos y saldos pendientes con filtros por rangos de fechas y por profesional bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-010 — Administrador

**Necesidad:** Necesito exportar reportes de ventas, recaudos y estadísticas de atención a formatos descargables (Excel y PDF).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Exportación XLSX y PDF autenticada.
**Código asociado:** `App_administracion/views.py (exportar)`
**Brecha:** El PDF puede requerir mejoras para listas extensas.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para exportar reportes de ventas, recaudos y estadísticas de atención a formatos descargables (Excel y PDF). Cuando el administrador solicita exportar reportes de ventas, recaudos y estadísticas de atención a formatos descargables (Excel y PDF). **Resultado esperado:** El sistema permite exportar reportes de ventas, recaudos y estadísticas de atención a formatos descargables (Excel y PDF) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta exportar reportes de ventas, recaudos y estadísticas de atención a formatos descargables (Excel y PDF) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita exportar reportes de ventas, recaudos y estadísticas de atención a formatos descargables (Excel y PDF) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-011 — Administrador

**Necesidad:** Necesito auditar y consultar registros de cobro asociados a cada cita (monto total presupuestado, abonos recibidos y saldo pendiente por recaudar).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Auditoría de cobros: total, pagado y saldo.
**Código asociado:** `App_administracion/views.py (reportes, caja)`
**Brecha:** Registro de pago manual.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para auditar y consultar registros de cobro asociados a cada cita (monto total presupuestado, abonos recibidos y saldo pendiente por recaudar). Cuando el administrador solicita auditar y consultar registros de cobro asociados a cada cita (monto total presupuestado, abonos recibidos y saldo pendiente por recaudar). **Resultado esperado:** El sistema permite auditar y consultar registros de cobro asociados a cada cita (monto total presupuestado, abonos recibidos y saldo pendiente por recaudar) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta auditar y consultar registros de cobro asociados a cada cita (monto total presupuestado, abonos recibidos y saldo pendiente por recaudar) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita auditar y consultar registros de cobro asociados a cada cita (monto total presupuestado, abonos recibidos y saldo pendiente por recaudar) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-012 — Administrador

**Necesidad:** Necesito consultar bitácora de auditoría de cancelaciones y reprogramaciones extemporáneas de turnos.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Bitácora consultable de acciones sobre citas y accesos.
**Código asociado:** `App_administracion/views.py (auditoria); App_agenda/models.py (BitacoraCita)`
**Brecha:** Revisar políticas de retención y acceso antes del despliegue.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para consultar bitácora de auditoría de cancelaciones y reprogramaciones extemporáneas de turnos. Cuando el administrador solicita consultar bitácora de auditoría de cancelaciones y reprogramaciones extemporáneas de turnos. **Resultado esperado:** El sistema permite consultar bitácora de auditoría de cancelaciones y reprogramaciones extemporáneas de turnos y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta consultar bitácora de auditoría de cancelaciones y reprogramaciones extemporáneas de turnos sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita consultar bitácora de auditoría de cancelaciones y reprogramaciones extemporáneas de turnos bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-013 — Administrador

**Necesidad:** Necesito parametrizar políticas de reservas (tiempo mínimo de antelación para agendamiento y política de cancelación de 2 horas).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Parámetros de antelación y cancelación por profesional.
**Código asociado:** `App_administracion/views.py (politicas); App_agenda/models.py (ConfiguracionAgenda)`
**Brecha:** No sustituye una política global de todas las estilistas.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para parametrizar políticas de reservas (tiempo mínimo de antelación para agendamiento y política de cancelación de 2 horas). Cuando el administrador solicita parametrizar políticas de reservas (tiempo mínimo de antelación para agendamiento y política de cancelación de 2 horas). **Resultado esperado:** El sistema permite parametrizar políticas de reservas (tiempo mínimo de antelación para agendamiento y política de cancelación de 2 horas) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta parametrizar políticas de reservas (tiempo mínimo de antelación para agendamiento y política de cancelación de 2 horas) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita parametrizar políticas de reservas (tiempo mínimo de antelación para agendamiento y política de cancelación de 2 horas) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-014 — Administrador

**Necesidad:** Necesito visualizar manual de usuario y documentación técnica del sistema administrativo.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Parcial. Ayuda operativa en panel y documentación de revisión.
**Código asociado:** `App_administracion/views.py (ayuda); App_administracion/templates/App_administracion/ayuda.html; documentacion`
**Brecha:** No se han elaborado diagramas UML/Figma de documentación técnica completa (etapa posterior según apuntes verdes).

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para visualizar manual de usuario y documentación técnica del sistema administrativo. Cuando el administrador solicita visualizar manual de usuario y documentación técnica del sistema administrativo. **Resultado esperado:** El sistema permite visualizar manual de usuario y documentación técnica del sistema administrativo y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta visualizar manual de usuario y documentación técnica del sistema administrativo sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita visualizar manual de usuario y documentación técnica del sistema administrativo bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-015 — Administrador

**Necesidad:** Necesito consultar y responder mensajes o solicitudes enviadas por clientas a través de los canales internos del sistema.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Cliente puede contactar administración; admin puede responder.
**Código asociado:** `App_administracion/views.py (mensajes_admin); App_usuarios/views.py (soporte_view)`
**Brecha:** Mensajería por recarga, no tiempo real.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para consultar y responder mensajes o solicitudes enviadas por clientas a través de los canales internos del sistema. Cuando el administrador solicita consultar y responder mensajes o solicitudes enviadas por clientas a través de los canales internos del sistema. **Resultado esperado:** El sistema permite consultar y responder mensajes o solicitudes enviadas por clientas a través de los canales internos del sistema y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta consultar y responder mensajes o solicitudes enviadas por clientas a través de los canales internos del sistema sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita consultar y responder mensajes o solicitudes enviadas por clientas a través de los canales internos del sistema bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-016 — Administrador

**Necesidad:** Necesito gestionar y supervisar archivos multimedia de referencia técnica adjuntos a las citas por parte del personal o clientes.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Parcial. Supervisión de referencias y descarga autorizada.
**Código asociado:** `App_administracion/views.py (archivos); App_agenda/views.py (descargar_adjunto)`
**Brecha:** Falta gestión avanzada de moderación/borrado del archivo y almacenamiento cloud.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para gestionar y supervisar archivos multimedia de referencia técnica adjuntos a las citas por parte del personal o clientes. Cuando el administrador solicita gestionar y supervisar archivos multimedia de referencia técnica adjuntos a las citas por parte del personal o clientes. **Resultado esperado:** El sistema permite gestionar y supervisar archivos multimedia de referencia técnica adjuntos a las citas por parte del personal o clientes y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta gestionar y supervisar archivos multimedia de referencia técnica adjuntos a las citas por parte del personal o clientes sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita gestionar y supervisar archivos multimedia de referencia técnica adjuntos a las citas por parte del personal o clientes bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-017 — Administrador

**Necesidad:** Necesito realizar cierre de caja diario consolidando métodos de pago recibidos (efectivo y transferencias electrónicas).
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Implementado. Cierre diario consolidando efectivo y transferencia con prevención de duplicados.
**Código asociado:** `App_administracion/views.py (caja,cerrar_caja); App_facturacion/models.py (CierreCaja)`
**Brecha:** Verificar coordinación con el cierre legado de estilista y las políticas financieras.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para realizar cierre de caja diario consolidando métodos de pago recibidos (efectivo y transferencias electrónicas). Cuando el administrador solicita realizar cierre de caja diario consolidando métodos de pago recibidos (efectivo y transferencias electrónicas). **Resultado esperado:** El sistema permite realizar cierre de caja diario consolidando métodos de pago recibidos (efectivo y transferencias electrónicas) y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta realizar cierre de caja diario consolidando métodos de pago recibidos (efectivo y transferencias electrónicas) sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita realizar cierre de caja diario consolidando métodos de pago recibidos (efectivo y transferencias electrónicas) bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

### RF-AD-018 — Administrador

**Necesidad:** Necesito gestionar copias de respaldo y sincronización de datos de la base de datos relacional.
**Objetivo:** Para supervisar la operación del salón y mantener el control de la información.
**Diagnóstico:** Parcial. Respaldo consistente SQLite descargable por administrador; probado en base persistente.
**Código asociado:** `App_administracion/views.py (respaldar); App_agenda/management/commands/respaldar_bd.py`
**Brecha:** No existe sincronización remota ni recuperación automatizada; en PostgreSQL debe configurarse estrategia del servidor.

**Escenarios originales de aceptación:**

1. **Operación realizada correctamente** — El administrador ha iniciado sesión y tiene los permisos correspondientes. Se dispone de la información necesaria para gestionar copias de respaldo y sincronización de datos de la base de datos relacional. Cuando el administrador solicita gestionar copias de respaldo y sincronización de datos de la base de datos relacional. **Resultado esperado:** El sistema permite gestionar copias de respaldo y sincronización de datos de la base de datos relacional y presenta el resultado o la confirmación correspondiente.
2. **Datos incompletos o no válidos** — Se introducen datos incompletos o incompatibles con las reglas del sistema. Cuando el administrador intenta gestionar copias de respaldo y sincronización de datos de la base de datos relacional sin cumplir las validaciones. **Resultado esperado:** El sistema no realiza la operación inválida, indica qué debe corregirse y conserva la integridad de los registros.
3. **Sin información o sin autorización** — La operación no tiene datos disponibles o el usuario carece del permiso requerido. Cuando se solicita gestionar copias de respaldo y sincronización de datos de la base de datos relacional bajo esas condiciones. **Resultado esperado:** El sistema informa que no hay registros o deniega el acceso, según corresponda, sin revelar información restringida.

## Requisitos no funcionales (23)

| Código | Área | Estado | Resultado de revisión |
|---|---|---|---|
| **RNF-UI-01** | Perceptible | Parcial | Hay clases/etiquetas visuales por estados; no hay auditoría WCAG certificada. |
| **RNF-UI-02** | Operable | Parcial | Plantillas responsive; faltan pruebas manuales táctiles y en navegadores. |
| **RNF-UI-03** | Comprensible | Parcial | Mensajes y validación Django; algunas interacciones son posteriores al envío. |
| **RNF-UI-04** | Robustez y Adaptabilidad | Por validar | No se ejecutó batería responsive Android/iOS/tablet/desktop. |
| **RNF-UI-05** | Accesibilidad | Parcial | Etiquetas y avisos en nuevos formularios; auditoría de contraste/lectores pendiente. |
| **RNF-UI-06** | Claridad de Agenda | Parcial | Servidor bloquea choques de agenda; calendario visual requiere ensayo integral. |
| **RNF-DDS-01** | Escalabilidad | Por validar | No se ejecutaron pruebas con 5000 clientes y 50 profesionales. |
| **RNF-DDS-02** | Mantenibilidad | Parcial | Separación MVT y pruebas; no hay API REST completa. |
| **RNF-DDS-03** | Rendimiento | Por validar | No se midieron SLA de 2s/1.5s en carga y red real. |
| **RNF-DDS-04** | Almacenamiento de Archivos | Parcial | Adjuntos con validaciones y ruta privada; compresión automática y nube pendientes. |
| **RNF-DDS-05** | Seguridad y Control de Acceso | Implementado | Django hash/sesiones/CSRF y permisos RBAC por rol; pruebas de acceso. |
| **RNF-DDS-06** | Disponibilidad | Pendiente de despliegue | No existe hospedaje 24/7 para medir 99.5%. |
| **RNF-DDS-07** | Integridad Transaccional | Parcial | Transacciones y soft delete de servicios; falta validar soft delete de citas y alta concurrencia. |
| **RNF-DDS-08** | Notificaciones Asíncronas | Pendiente de infraestructura | Avisos internos; sin servicio de colas ni workers de envío. |
| **RNF-HS-01** | Servidor Backend | Parcial | Django y soporte WSGI/ASGI en Linux; DRF no está instalado. |
| **RNF-HS-02** | Motor de Base de Datos | Parcial | SQLite operativo y opción PostgreSQL configurable; producción PostgreSQL sin verificar. |
| **RNF-HS-03** | Frontend y Navegación | Por validar | Front HTML/Tailwind/JS; compatibilidad en Chrome, Safari, Firefox, Edge no ensayada. |
| **RNF-HS-04** | Hardware del Cliente | Por validar | No se ensayó en hardware real de teléfonos especificados. |
| **RNF-HS-05** | Hardware de Estilista | Por validar | No se ensayó en tablet con cámara; captura y consulta de evidencias parcial. |
| **RNF-HS-06** | Hardware del Administrador | Por validar | Panel creado, no se probó en pantalla 1366×768 real. |
| **RNF-HS-07** | Servicio de Correo Transaccional | Parcial | Backend SMTP parametrizable; faltan credenciales y pruebas de envío real. |
| **RNF-HS-08** | Control de Versiones y Despliegue | Parcial | Gitignore y Dockerfile; flujo de ramas/repositorio y despliegue no verificables en ZIP. |
| **RNF-HS-09** | Herramientas de Modelado y Diseño | Pendiente documental | Diagramas UML/Figma aplazados de acuerdo con marcación verde de apuntes. |

### Textos de referencia de los 23 RNF

Las siguientes son las descripciones tomadas de Stakeholders, útiles para revisarlos sin perder sus metas medibles.

- **RNF-UI-01 — Perceptible:** La interfaz utiliza semántica visual estandarizada: estados diferenciados por color (Verde: Confirmada / Completada; Ámbar: Pendiente; Azul: En proceso; Rojo: Cancelada / Rechazada) y contraste cromático adecuado según WCAG 2.1 AA.
- **RNF-UI-02 — Operable:** Navegación fluida y accesible tanto en dispositivos móviles táctiles como en navegadores web de escritorio, integrando manual de usuario en línea mediante botón de ayuda contextual.
- **RNF-UI-03 — Comprensible:** Formularios claros con validación de entradas en tiempo real, mensajes de confirmación explícitos (ej. 'Cita agendada para el 15 de Mayo a las 10:00 AM') e indicación de errores sin tecnicismos.
- **RNF-UI-04 — Robustez y Adaptabilidad:** Diseño responsivo que garantiza consistencia visual y funcional en smartphones (Android/iOS), tablets y computadores de escritorio sin desbordamiento de componentes.
- **RNF-UI-05 — Accesibilidad:** Tipografía legible con tamaños escalables, iconografía asistida con etiquetas textuales y campos obligatorios claramente señalizados con asterisco (*) y alertas accesibles.
- **RNF-UI-06 — Claridad de Agenda:** El calendario interactivo presenta bloqueo visual instantáneo de franjas horarias ocupadas, imposibilitando la selección de turnos cruzados por parte del usuario.
- **RNF-DDS-01 — Escalabilidad:** Arquitectura modular capaz de soportar el incremento gradual de usuarios y sucursales (dimensionada inicialmente para hasta 5.000 clientes activos y 50 profesionales sin merma en el rendimiento).
- **RNF-DDS-02 — Mantenibilidad:** Estructura de software bajo arquitectura Modelo-Vista-Plantilla / API REST con desacoplamiento lógico, modelos de datos normalizados, código documentado y pruebas de regresión.
- **RNF-DDS-03 — Rendimiento:** Tiempo de respuesta del backend menor a 2.0 segundos en la consulta de catálogos y horarios, y confirmación transaccional de reservas en menos de 1.5 segundos bajo conexión estándar.
- **RNF-DDS-04 — Almacenamiento de Archivos:** Gestión de almacenamiento en servidor o servicio cloud para archivos multimedia e imágenes de referencia, implementando compresión automática y restricción de peso máximo a 5 MB por archivo.
- **RNF-DDS-05 — Seguridad y Control de Acceso:** Autenticación segura basada en sesiones/tokens con contraseñas cifradas bajo hash seguro (PBKDF2/Argon2) y control de acceso basado en roles (RBAC: Administrador, Estilista, Cliente).
- **RNF-DDS-06 — Disponibilidad:** Disponibilidad del servicio del 99.5% 24/7 en servidores de despliegue, asegurando que las clientas puedan reservar citas fuera del horario comercial del salón de belleza.
- **RNF-DDS-07 — Integridad Transaccional:** Políticas de eliminación lógica (soft delete) en registros de citas y servicios para preservar la trazabilidad contable; control de concurrencia en reservas para evitar solapamientos.
- **RNF-DDS-08 — Notificaciones Asíncronas:** Procesamiento en segundo plano para el envío de alertas y notificaciones por correo electrónico y sistema, evitando demoras o bloqueos en las peticiones del usuario.
- **RNF-HS-01 — Servidor Backend:** Servidor de aplicaciones configurado en Python 3.11+ ejecutando framework Django / Django REST Framework con servidor WSGI/ASGI en entorno Linux/Cloud.
- **RNF-HS-02 — Motor de Base de Datos:** Base de datos relacional compatible (PostgreSQL para entorno de producción o SQLite para pruebas y desarrollo local) con integridad referencial estricta.
- **RNF-HS-03 — Frontend y Navegación:** Aplicación web responsive construida con HTML5 semántico, CSS moderno (Tailwind CSS / Bootstrap) y JavaScript interactivo, con soporte en Chrome, Safari, Firefox y Edge.
- **RNF-HS-04 — Hardware del Cliente:** Smartphone con Android 8.0+ o iOS 13+, mínimo 2 GB de memoria RAM y conectividad a internet (red móvil o Wi-Fi) para acceso a la aplicación.
- **RNF-HS-05 — Hardware de Estilista:** Smartphone o tablet con Android 9.0+ o iOS 13+, mínimo 3 GB de RAM y cámara funcional para registro y consulta de evidencias fotográficas.
- **RNF-HS-06 — Hardware del Administrador:** Computador de escritorio, portátil o tablet con pantalla de resolución mínima 1366x768 píxeles y navegador web actualizado para reportería y control gerencial.
- **RNF-HS-07 — Servicio de Correo Transaccional:** Integración con servidor SMTP o API de mensajería (ej. Gmail SMTP, SendGrid o similar) para despacho de correos de confirmación y restablecimiento de claves.
- **RNF-HS-08 — Control de Versiones y Despliegue:** Repositorio centralizado en Git/GitHub con flujo de ramas para integración y soporte de empaquetado en contenedores Docker.
- **RNF-HS-09 — Herramientas de Modelado y Diseño:** Diagramas de arquitectura y modelado UML elaborados con StarUML y prototipos de alta fidelidad diseñados en Figma.

## Prioridades de las tres páginas de apuntes

La clasificación está determinada por las marcas del cuaderno compartidas por el usuario; no se ejecutan tareas verdes ni púrpuras posteriores como si fueran parte de la fase actual.

**Actividades inmediatas, sin paréntesis:** incorporar rol Visitante (sin credenciales), eliminar recepcionista del flujo, incluir Administrador en autenticación, arreglar ingreso cruzado al elegir Estilista, recuperación de contraseña y validación de formato/unicidad de correo, mensajes sobre contraseña errónea y observación de los RNF frente al código. En el proyecto existen controles para los puntos de autenticación y accesos; la validación por enlace del email registrado aún queda pendiente.

**Entre paréntesis verdes: después, documentación:** revisar/modelar diagrama de clases y modelo relacional, organizar `Persona`, diagramas UML, diccionario de datos y manuales finales según el diseño real. No se sustituyen diagramas por esquemas inventados.

**Entre paréntesis púrpuras: después de documentación:** palabras clave del navegador y trabajos de esta fase posterior; no forman parte de la implementación funcional prioritaria.

## Seguridad y pruebas de aceptación adicionales pendientes

- Verificación de propiedad del email mediante enlace de activación (diferente a verificar el formato).
- Pruebas reales con navegadores, móvil, teclado, lectores de pantalla, contraste WCAG y carga concurrente.
- SMTP real, notificaciones push/WebSockets, tareas asíncronas y respaldos remotos con restauración ensayada.
- Política de caja y auditoría contra la interfaz legada de estilistas; soft-delete de citas según RNF-DDS-07.
- Adecuar el requisito AD-001 original que menciona recepcionista a la corrección más reciente de clase; no crear cuentas recepcionista.
- Ajustar los criterios de aceptación generales de Administrador (muchos se generaron como escenarios genéricos) a pruebas específicas de errores y permisos.
- Añadir despliegue PostgreSQL, TLS, monitoreo y pruebas no funcionales antes de declarar producto listo para producción.

## Comandos de comprobación

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test App_usuarios App_servicios App_agenda.tests_requisitos App_facturacion
python manage.py test App_agenda.tests
python manage.py test App_administracion
```

**Advertencia:** el resultado corresponde a estas pruebas, no a una auditoría de penetración, rendimiento, accesibilidad ni cumplimiento legal de facturación.
