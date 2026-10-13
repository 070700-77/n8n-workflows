# Caso 3 (Intermedio-Avanzado) — Conciliación de pagos con Merge

## Contexto del problema

Una empresa de suscripciones concilia cada mes lo que su pasarela de pagos reporta (vía API) contra lo que su sistema contable registra (archivo local). Necesita detectar pagos cobrados que no aparecen en contabilidad y registros contables sin pago asociado. Hoy se cruzan dos Excel a mano y se escapan cosas.

## Objetivo

Traer los pagos desde una API en una rama y los registros contables en otra, combinarlos con **Merge** por un ID común, detectar discrepancias con **Python** y dejar un reporte organizado.

## Regla crítica de negocio

**Tolerancia de redondeo:** una diferencia menor a $1 entre los montos de ambas fuentes **no** es una discrepancia. En `wf_03_comparar_registros.py` se cumple con `-1 < diferencia < 1`.

## Cómo funciona

1. **Execute Command** → `wf_03_ingresar_info_api_bd.py`: consulta tu API MockAPI (URL en `MOCKAPI_URL`), guarda los pagos en SQLite y en `wf_03_payment_data.json`.
2. **Read File → Extract → Split Out**: rama de la **pasarela** (API).
3. **Google Sheets** (`Get row(s)`): rama **contable**, lee la hoja `Contabilidad` (cargada desde `pagos_contabilidad.xlsx`).
4. **Merge** de ambas ramas → se escribe `input_merge_payment_invoices.json`.
5. **Execute Command** → `wf_03_comparar_registros.py` clasifica cada `id` y escribe `invoice_categories.json`:
   - `conciliated`: está en ambas fuentes y el monto coincide (o difiere menos de $1).
   - `amount_discrepancy`: está en ambas, pero la diferencia es de $1 o más (se informa el monto).
   - `api_only`: solo en la pasarela.
   - `sheet_only`: solo en contabilidad.
   - `empty_info`: si **alguna fuente llega vacía** se registra un error en lugar de cruzar.
6. **IF**: si `empty_info` trae errores, **Gmail** avisa que una fuente no arrojó registros y el flujo se detiene sin generar un reporte incompleto.
7. Si todo está bien, cada categoría se escribe (upsert por `id`) en su propia hoja del Sheet de reporte y **Gmail** envía la notificación.

## Hojas de reporte

`Conciliados`, `Discrepancia en valor`, `Registro unicamente en pasarela de pagos` y `Registro unicamente local`.

## Archivos

| Archivo | Rol |
|---|---|
| `wf_ejer_03_workflow.json` | Workflow de n8n (importable) |
| `wf_03_ingresar_info_api_bd.py` | Trae los pagos de la API y los guarda |
| `wf_03_comparar_registros.py` | Cruce, tolerancia y clasificación |
| `pagos_contabilidad.xlsx` | Registros contables de ejemplo (para cargar al Sheet) |
| `wf_03_payment_data.json`, `input_merge_payment_invoices.json`, `invoice_categories.json` | Datos intermedios de ejemplo |
| `ejemplo input1.json`, `ejemplo_merge.json` | Ejemplos de entrada/salida del Merge |

La base `wf_03_userstransactions.db` no se versiona; se recrea al ejecutar.

## Variables de entorno

| Variable | Descripción |
|---|---|
| `MOCKAPI_URL` | URL de **tu** proyecto en [MockAPI](https://mockapi.io/) con el recurso de pagos (campos: `name`, `email`, `residence_country`, `phone_number`, `payment_amount`, `createdAt`, `id`) |

## Cómo ejecutar

1. Crea tu recurso en MockAPI, ponlo en `.env` como `MOCKAPI_URL` y monta el repo como `/scripts` en n8n.
2. Sube `pagos_contabilidad.xlsx` a Google Sheets (hoja `Contabilidad`) y crea un documento de reporte con las cuatro hojas de arriba.
3. Importa `wf_ejer_03_workflow.json`, reconecta **Google Sheets** y **Gmail** y reselecciona tus documentos.
4. Ejecuta el workflow manualmente.

## Alcance frente al enunciado

Cubierto: cruce con Merge por ID, lógica en Python, tolerancia de $1, validación de fuentes vacías con aborto y mensaje claro, reporte por categorías. **No incluido en esta versión:** la creación/subida del reporte a carpetas de Drive por mes, ni la hoja de resumen con conteos y monto total de discrepancias (el correo menciona Drive, pero el workflow exportado no tiene nodo de Drive).

---

## Seguridad

- Las credenciales de Google se configuran **dentro de n8n** (OAuth2); el JSON exportado no contiene tokens, solo el nombre de la credencial.
- Los IDs de Google Sheets/Drive, el correo destinatario y el `instanceId` fueron reemplazados por placeholders. Reconfigúralos con tus propios valores tras importar.
- Nunca subas tu `.env` real: está en `.gitignore`.
