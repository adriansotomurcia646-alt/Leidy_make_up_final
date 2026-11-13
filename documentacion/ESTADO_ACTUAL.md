# Estado de reconstrucción — 13/11/2026

- Fuente: Excel de 53 historias (3 Visitante, 18 Cliente, 14 Estilista, 18 Administrador) + Stakeholders + modelo de 16 entidades.
- Base: versión de Django previamente desarrollada con módulos de administración, agenda, servicios, facturación y usuarios.
- Se cambió la relación de HistorialAcceso, BitacoraCita y Notificacion para que la columna FK sea `persona_id`.
- Se incorporó `Mensaje.cita_id`, opcional para chat de soporte, y se vincula al escribir a una estilista.
- Se agregó unicidad del correo insensible a mayúsculas para correos no vacíos.
- Registro directo: cliente activo sin enlaces de verificación; validaciones de nombre, apellidos, teléfono, correo y contraseña.
- Las tareas fuera de alcance local (push real, servidor SMTP, nube, accesibilidad certificada) permanecen como pendientes reales.
- No se ejecutaron pruebas Django en el entorno donde se armó el ZIP: dependencia ausente y sin acceso a PyPI. No afirmar validación funcional total hasta correr la suite en el equipo del usuario.
