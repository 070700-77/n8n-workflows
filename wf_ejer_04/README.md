# Caso 4 (Intermedio) — Reembolsos de gastos de viaje multimoneda

## Contexto del problema

Andes Advisory es una consultora (empresa ficticia) cuyos consultores viajan a Lima, Ciudad de México, Miami y Madrid. Cada mes cada consultor sube un Excel con sus gastos a una carpeta de Drive. Hoy finanzas lo revisa a mano, convierte monedas en una calculadora y se equivoca con los límites de la política de viajes.

## Objetivo

Procesar automáticamente los archivos nuevos: validar cada gasto contra la política, convertirlo a USD y decidir cuánto es reembolsable.

## Datos de entrada (en `andes_advisory_datos_entrada/`)

- `Gastos/Entrantes/gastos_<cedula>_<AAAA-MM>.xlsx` con columnas `fecha, categoria, descripcion, moneda, valor, tiene_soporte`.
- `Empleados.xlsx` (se carga como Google Sheet `Empleados`: cédula, nombre, área, centro de costo, aprobador).
- `politica_viajes.json`: límites diarios por categoría en USD (alimentación 60, transporte 40, hospedaje 180, otros 25) y reglas.
- `README_CASOS_PRUEBA.txt`: **casos borde** incluidos a propósito (valores `"1.250,50"`, `"1,250.50"`, `"$ 45"`, monedas en minúscula, fecha vacía, categoría inventada, archivo mal nombrado, cédula inexistente, dos archivos del mismo mes).

## Cómo funciona

1. **Google Drive Trigger** vigila la carpeta de entrada y lista los archivos nuevos.
2. **Google Sheets** lee la hoja `Empleados`.
3. **Python** `wf_04_validar_nombres_archivos.py`: valida que el nombre cumpla `gastos_<cedula>_...` y que la cédula exista en Empleados → `fname_validation_results.json`.
4. **IF**: los archivos inválidos se registran en la hoja `Archivos con error` (nombre, motivo, enlace); los válidos continúan, uno a uno (*Loop Over Items*).
5. **Loop Over Items** recorre los archivos válidos: de cada uno lee su hoja `Gastos` (los Excel se suben a Drive como Google Sheets) y `agregar_nombre_resultados.py` le agrega cédula y período a cada fila → `output_resultados.json`.
6. Al terminar el ciclo se consolida todo en `info_consolidada_base.json` y se ejecuta **una sola vez** `calcular_viaticos.py`, que:
   - Normaliza números en varios formatos (`1.250,50`, `1,250.50`, `$ 45`).
   - Pasa la moneda a mayúsculas.
   - Consulta la tasa a USD **una sola vez por moneda** y la guarda en `tasas_cache.json` (no una llamada por fila).
   - Calcula `valor_convertido_USD`, la `tasa_usada` y el `valor_no_respaldado_USD` (excedente sobre el límite de su categoría).
7. **Google Sheets** agrega cada gasto a la hoja `Registro consolidado invoices autorizados`.

## Archivos

| Archivo | Rol |
|---|---|
| `wf_ejer_04_workflow.json` | Workflow de n8n (importable) |
| `wf_04_validar_nombres_archivos.py` | Valida patrón del nombre y cédula |
| `agregar_nombre_resultados.py` | Anexa cédula y período a las filas |
| `calcular_viaticos.py` | Normalización, conversión de moneda y excedentes |
| `politica_viajes.json` | Política de viajes (límites en USD) |
| `tasas_cache.json` | Caché de tasas de cambio (bórralo para refrescarlas) |
| `andes_advisory_datos_entrada/` | Excel de ejemplo y casos borde |
| `input*.json`, `info_consolidada_*.json`, `output_resultados.json`, `fname_validation_results.json` | Archivos intermedios de ejemplo |

## Variables de entorno

| Variable | Descripción |
|---|---|
| `X_RAPIDAPI_KEY` | Key de [RapidAPI](https://rapidapi.com/) suscrita a *Currency Conversion and Exchange Rates* |

## Cómo ejecutar

1. Configura `.env` y monta el repo como `/scripts` en n8n.
2. Crea en Google Drive la carpeta de entrada y sube los Excel de `Gastos/Entrantes` (con conversión a Google Sheets). Carga `Empleados.xlsx` como Google Sheet.
3. Importa `wf_ejer_04_workflow.json`, reconecta **Google Drive** y **Google Sheets**, y reselecciona la carpeta vigilada y los documentos.
4. Activa el workflow o ejecútalo manualmente.

## Alcance frente al enunciado (estado actual)

Implementado: disparador por Drive, validación del nombre y la cédula con registro de errores, normalización de formatos numéricos, conversión a USD con una consulta por moneda y tasa usada por fila, y exceso sobre el límite por categoría.

Pendiente respecto al enunciado completo: aprobación parcial **sumando los gastos del día** por categoría (hoy el límite se compara gasto a gasto), estados `APROBADO / PARCIAL / RECHAZADO` con motivo, rechazo de gastos sin soporte > 20 USD, conversión a COP, registro de la fecha y hora de la tasa, mover archivos a `Gastos/Errores` y `Gastos/Procesados/AAAA-MM/` (con creación de carpeta), la hoja `Reembolsos_Resumen` con upsert por empleado y mes, y el JSON resumen en `salida/`.

---

## Seguridad

- Las credenciales de Google se configuran **dentro de n8n** (OAuth2); el JSON exportado no contiene tokens, solo el nombre de la credencial.
- Los IDs de Google Sheets/Drive, el correo destinatario y el `instanceId` fueron reemplazados por placeholders. Reconfigúralos con tus propios valores tras importar.
- Nunca subas tu `.env` real: está en `.gitignore`.
