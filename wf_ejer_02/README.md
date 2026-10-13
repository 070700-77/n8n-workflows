# Caso 2 (Intermedio) — Scoring de clientes con API, Python y Sheets

## Contexto del problema

El enunciado original plantea un equipo comercial que recibe leads con datos mínimos y necesita enriquecerlos y priorizarlos con un score automático: consultar una API REST, calcular el score con reglas de negocio en **Python vía Execute Command**, validar el email y actualizar Google Sheets sin duplicar (actualiza si el email existe, agrega si no).

## Qué implementa esta versión

Adapta ese mismo patrón a un escenario bancario con datos sintéticos: ordena **clientes de un banco** por un puntaje de calidad usando perfiles y transacciones obtenidos de una API REST.

## Cómo funciona

1. **Execute Command** → `wf_02_ingresar_bd.py`: consulta la API *Dummy Payment & Banking Data* (RapidAPI, `count=100`) y guarda tarjetas, personas, direcciones, cuentas, transacciones y perfiles en una base **SQLite** local (se crea sola).
2. **Execute Command** → `wf_02_consultar_bd_sqlite.py`: arma una vista `Transacciones_por_cliente` (compras completadas / fallidas / pendientes por perfil), **valida el formato del email** con una expresión regular y calcula el score:

   | Factor | Regla |
   |---|---|
   | Tipo de cuenta | `checking` = 30, `savings` = 20, otro = 10 |
   | Edad | ≥ 60 años = 20, 35–59 = 10, menor = 5 |
   | Compras | `completadas / total de transacciones × 50` (0 si no hay completadas) |

   **Score total = tipo de cuenta + edad + compras.** El resultado se escribe en `output_2.json`.
3. **Read/Write File → Extract from File → Split Out**: lee el JSON y lo separa por cliente.
4. **Google Sheets** (`Append or update row`): upsert en la hoja `users_rank` usando `email` como llave, para no duplicar clientes.

## Archivos

| Archivo | Rol |
|---|---|
| `wf_ejer_02_workflow.json` | Workflow de n8n (importable) |
| `wf_02_ingresar_bd.py` | Llama a la API y crea/llena la base SQLite |
| `wf_02_consultar_bd_sqlite.py` | Calcula el score y genera `output_2.json` |
| `wf_02_Bank clients scoring_ejemplo db de llegada.json` | Ejemplo de respuesta de la API |
| `output_2.json` | Salida de ejemplo (clientes con su score) |

La base `wf_02_bank clients scoring.db` **no se versiona**; se recrea al ejecutar el primer script.

## Variables de entorno

| Variable | Descripción |
|---|---|
| `X_RAPIDAPI_KEY` | Tu key de [RapidAPI](https://rapidapi.com/), suscrita a *Dummy Payment & Banking Data* |

Copia `.env.example` (en la raíz) a `.env`. Los scripts usan `python-dotenv`, que busca el `.env` hacia arriba desde la carpeta del script.

## Cómo ejecutar

1. Configura `.env` y monta el repo como `/scripts` en n8n.
2. Importa `wf_ejer_02_workflow.json`, reconecta **Google Sheets** y elige un documento con una hoja `users_rank`.
3. Ejecuta el workflow manualmente.

## Alcance frente al enunciado

El patrón (API REST → score en Python por Execute Command → upsert en Sheets por email → validación de email) está cubierto. Esta versión **no** incluye la lectura de un CSV de leads, el enriquecimiento por lead individual con marca “sin enriquecer” ni un log aparte de fallos: los errores de la API se capturan con `try/except` en el script.

---

## Seguridad

- Las credenciales de Google se configuran **dentro de n8n** (OAuth2); el JSON exportado no contiene tokens, solo el nombre de la credencial.
- Los IDs de Google Sheets/Drive, el correo destinatario y el `instanceId` fueron reemplazados por placeholders. Reconfigúralos con tus propios valores tras importar.
- Nunca subas tu `.env` real: está en `.gitignore`.
