# Leidy Make Up Maison 3.2 — Render GRATIS + Gmail API

Esta versión conserva los roles, reservas, galerías, el diseño Maison y el carrusel editable de la versión 3.1.

**EMPIEZA AQUÍ: [GUIA_RENDER_GRATIS_GMAIL_API.md](GUIA_RENDER_GRATIS_GMAIL_API.md)**

## Cambios técnicos

- `Pr_makeupweb/gmail_backend.py`: backend Django para Gmail API HTTPS con OAuth, sin SMTP.
- `App_usuarios/management/commands/configurar_gmail_api.py`: asistente para obtener tu autorización local de la cuenta remitente.
- `scripts/diagnosticar_supabase.py`: valida `DATABASE_URL` sin imprimirla; `--connect` hace una prueba TLS real con `SELECT 1`.
- `Pr_makeupweb/supabase_storage.py`: almacenamiento persistente de fotos públicas y adjuntos privados.
- `render.yaml`: Web Service **Free** sin bases Render Postgres con vencimiento.
- `.env.example`: variables documentadas sin credenciales.
- `tests_integracion_gratis.py`: pruebas offline que no requieren cuentas externas.

## Inicio local

```bash
bash iniciar_linux.sh
```

El script instala dependencias y arranca el servidor. Para usar Gmail API de verdad, primero autoriza OAuth siguiendo la guía.

## Límites

**No es un servicio de producción garantizado:** Render Free duerme, Supabase Free puede pausar, Gmail impone límites y OAuth Testing caduca a los 7 días. Las pruebas con servicios reales requieren tus propias credenciales que **no debes compartir**.

Version anterior: documentación histórica en `documentacion/README_MAISON_3_1_HISTORICO.md`.
