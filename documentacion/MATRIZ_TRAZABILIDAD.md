# Matriz de trazabilidad vigente — Leidy Make Up

Esta versión sustituye la matriz histórica que correspondía a otro alcance (50 RF, 15 historias, 83 pruebas), porque ahora **Stakeholders e Historias de Usuario** contienen **53 RF, 166 escenarios** y se añadieron los roles Administrador, Visitante, Cliente y Estilista.

Usa la [matriz detallada requisito por requisito](ANALISIS_Y_TRAZABILIDAD_53_REQUISITOS.md) como referencia canónica.

También está disponible el [inventario CSV de los 53 RF](MATRIZ_ESTADOS_RF.csv) para revisar y filtrar en Excel.

**Validación de la versión anterior:** se informaron 107 pruebas (36 + 54 + 17), migraciones de base vacía y verificación del respaldo SQLite. **La reconstrucción actual no se pudo ejecutar en Django dentro de este entorno**; sus verificaciones son de sintaxis Python y estructura estática. Los flujos deben someterse a `python manage.py check`, migraciones y pruebas en el equipo destino. Faltan también criterios que dependen de servicios externos.
