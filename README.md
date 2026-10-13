# n8n Workflows + Python

Colección de cuatro casos de estudio de automatización con **n8n** donde la lógica de negocio pesada se ejecuta en **scripts de Python** llamados desde el nodo *Execute Command*. Cada caso va de un problema de negocio realista a un workflow completo con lectura de archivos, APIs REST, validaciones y salida a Google Sheets.

---

## Casos

| Carpeta | Caso | Nivel | Qué ejercita |
|---|---|---|---|
| [`wf_ejer_01`](./wf_ejer_01/) | Normalización de ventas diarias | Básico | CSV → JSON, limpieza de fechas y precios, validaciones, Google Sheets, Gmail |
| [`wf_ejer_02`](./wf_ejer_02/) | Scoring de clientes bancarios | Intermedio | API REST (RapidAPI), SQLite, scoring en Python, upsert en Sheets por email |
| [`wf_ejer_03`](./wf_ejer_03/) | Conciliación de pagos con Merge | Intermedio-Avanzado | API + Sheets, nodo Merge, tolerancia de $1, reportes por categoría, alertas |
| [`wf_ejer_04`](./wf_ejer_04/) | Reembolsos de viaje multimoneda | Intermedio | Trigger de Drive, validación de nombres, conversión de monedas con caché, Sheets |

Cada carpeta tiene su propio `README.md` con el enunciado, la explicación del flujo y su alcance real frente al enunciado.

---

## Arquitectura común

```
Trigger (manual o Drive)
   ↓
Nodos n8n (leer archivo / API / Google Sheets)
   ↓  escribe un JSON de entrada en /scripts/<caso>/
Execute Command  →  python3 /scripts/<caso>/<script>.py
   ↓  el script escribe un JSON de salida
Read/Write File → Extract from File → Split Out
   ↓
Google Sheets / Gmail / (Drive)
```

El patrón es siempre el mismo: **n8n orquesta, Python calcula**. Los scripts leen y escriben archivos JSON en `/scripts/...`, por eso este repositorio debe montarse en el contenedor de n8n **exactamente en `/scripts`**.

---

## Requisitos

- n8n (probado en Docker) con el nodo *Execute Command* habilitado.
- Python 3 dentro del contenedor de n8n y `python-dotenv` (`pip install -r requirements.txt`).
- Cuenta de Google con credenciales OAuth2 configuradas en n8n para **Google Sheets**, **Gmail** y **Google Drive** (según el caso).
- Una [RapidAPI key](https://rapidapi.com/) (casos 2 y 4) y un proyecto en [MockAPI](https://mockapi.io/) (caso 3).

### Ejemplo de montaje en Docker

Ejemplo ilustrativo (adáptalo a tu imagen y versión de n8n):

```dockerfile
FROM n8nio/n8n:latest
USER root
RUN apk add --no-cache python3 py3-pip && pip3 install --break-system-packages python-dotenv
USER node
```

```bash
docker run -it --rm -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -v "$(pwd)":/scripts \
  <tu-imagen-n8n-con-python>
```

Si tu versión de n8n restringe el acceso a archivos o deshabilita *Execute Command*, ajusta las variables de entorno correspondientes de n8n (por ejemplo `N8N_RESTRICT_FILE_ACCESS_TO` y `NODES_EXCLUDE`).

---

## Puesta en marcha

```bash
# 1. Clona el repositorio
git clone https://github.com/YOUR_USERNAME/n8n-workflows.git
cd n8n-workflows

# 2. Configura tus variables de entorno
cp .env.example .env          # Windows: copy .env.example .env
# Edita .env con tus valores reales

# 3. Monta esta carpeta como /scripts en tu contenedor de n8n (ver arriba)
```

Luego, en n8n:

1. **Importa** el workflow: *Workflows → Import from file* → `wf_ejer_0X/wf_ejer_0X_workflow.json`.
2. **Reconecta tus credenciales** (Google Sheets / Gmail / Drive). Los workflows exportados traen solo el *nombre* de la credencial; el ID es un placeholder (`REPLACE_WITH_YOUR_CREDENTIAL_ID`).
3. **Reselecciona tus documentos**: los nodos de Google Sheets y Drive apuntan a IDs de ejemplo (`GOOGLE_FILE_ID_00X`). Abre cada nodo y elige tu propia hoja o carpeta.
4. Cambia el destinatario de los nodos Gmail (`you@example.com`) por tu correo.
5. Ejecuta el workflow.

---

## Estructura

```
n8n-workflows/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── wf_ejer_01/        # Normalización de ventas diarias
├── wf_ejer_02/        # Scoring de clientes bancarios
├── wf_ejer_03/        # Conciliación de pagos
└── wf_ejer_04/        # Reembolsos de viaje multimoneda
```

Los archivos `input_*.json` / `output_*.json` dentro de cada caso son los **archivos intermedios** que n8n y Python se pasan entre sí; se incluyen como ejemplo de datos y se sobrescriben en cada ejecución.

---

## Seguridad y privacidad

- Ningún secreto está versionado: las claves se leen con `os.getenv()` desde `.env`, que está en `.gitignore`.
- Los workflows exportados fueron **sanitizados**: se reemplazaron IDs de credenciales, de Google Sheets/Drive, el `instanceId` de n8n, correos personales y metadatos de cuenta de Google por placeholders.
- Todos los datos de ejemplo son **sintéticos** (generados con Faker o inventados). Los correos del caso 1 usan `example.com`.
- Las bases SQLite (`*.db`) no se suben; los scripts las recrean al ejecutarse.

> **Advertencia:** nunca subas tu `.env` ni un export de n8n con credenciales reales. Si alguna vez publicas una clave por error, revócala y genera una nueva de inmediato.

### Nota técnica conocida

Algunos scripts que llaman APIs desactivan la verificación de certificados SSL (`ssl.CERT_NONE`) mientras se desarrollaba. Para uso real, elimina esas líneas y usa el contexto SSL por defecto.
