# Caso 1 (Básico) — Normalización de ventas diarias

## Contexto del problema

Una tienda retail exporta cada noche un CSV desde su POS con las ventas del día. El archivo llega sucio: encabezados con espacios, fechas en formatos mezclados, precios como texto con símbolo de moneda (`"$12.500"`) y algunas filas basura. El equipo administrativo pierde media hora cada mañana limpiándolo a mano en Excel antes de poder reportarlo.

## Objetivo

Un workflow que lea el CSV local, lo limpie y normalice, lo convierta a JSON, calcule métricas simples del día y deje todo listo en Google Sheets, además de guardar una copia limpia en disco.

## Reglas de negocio

- Descartar filas sin producto o con cantidad ≤ 0.
- Normalizar todas las fechas a ISO `YYYY-MM-DD` (entrada `2026/07/28` o `28-07-2026`).
- Convertir los precios de texto a número real.
- `cliente_email` es opcional: si está vacío, el flujo no debe romperse.
- Guardar una copia del JSON limpio en disco.

## Cómo funciona

1. **Leer CSV** `ventas_20260728.csv` y extraer sus filas (nodos 02–03).
2. **Normalizar campos** y guardar el resultado como `input_1.json` (nodos 04–06).
3. **Python** `leer_json_registros_entrada.py` (Execute Command): convierte fechas a ISO y precios a número → `output_1.json` (nodo 07).
4. **Filtrar ventas válidas**: `producto` no vacío y `cantidad > 0` (nodos 08–11).
5. **Google Sheets**: agrega el detalle fila por fila en la hoja `DETALLE` (nodo 12).
6. **Python** `resumir_ventas.py`: calcula total vendido, número de ventas, ticket promedio y desglose por producto → `output_2.json` (nodos 13–17).
7. **Google Sheets**: agrega/actualiza el resumen en la hoja `RESUMEN`, con upsert por `FECHA` (nodos 18–21).
8. **Gmail**: envía un correo con los productos actualizados (nodos 22–24).

## Archivos

| Archivo | Rol |
|---|---|
| `wf_ejer_01_workflow.json` | Workflow de n8n (importable) |
| `leer_json_registros_entrada.py` | Normaliza fechas y precios |
| `resumir_ventas.py` | Calcula las métricas del día |
| `ventas_20260728.csv`, `input_1.csv` | CSV de ejemplo con suciedad típica |
| `input_*.json`, `output_*.json` | Archivos intermedios entre n8n y Python |

## Variables de entorno

Ninguna. Este caso no usa APIs externas con clave.

## Cómo ejecutar

1. Monta el repo como `/scripts` en tu contenedor de n8n (ver [README principal](../README.md)).
2. Importa `wf_ejer_01_workflow.json` en n8n.
3. Reconecta tus credenciales de **Google Sheets** y **Gmail**, y elige tu propio documento con las hojas `DETALLE` y `RESUMEN`.
4. Cambia el destinatario del nodo Gmail.
5. Ejecuta el workflow manualmente.

## Notas

- La fecha del resumen se toma del día de ejecución (`datetime.now()`), no de la fecha de las ventas.
- Los correos de ejemplo usan el dominio `example.com`.

---

## Seguridad

- Las credenciales de Google se configuran **dentro de n8n** (OAuth2); el JSON exportado no contiene tokens, solo el nombre de la credencial.
- Los IDs de Google Sheets/Drive, el correo destinatario y el `instanceId` fueron reemplazados por placeholders. Reconfigúralos con tus propios valores tras importar.
- Nunca subas tu `.env` real: está en `.gitignore`.
