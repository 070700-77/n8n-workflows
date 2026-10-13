import os
import ssl
import json
import sqlite3
from dotenv import load_dotenv
import urllib.request, urllib.error, urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

load_dotenv()

x_rapidapi_key = os.getenv("X_RAPIDAPI_KEY")
payment_data = []

print("CWD actual:", os.getcwd())

try:
    # os.path.abspath(__file__) devuelve la ruta absoluta del archivo actual. Osea, la ruta completa del script que se está ejecutando.
    # os.path.dirname() devuelve el directorio que contiene el archivo actual. Osea, el directorio donde se encuentra este script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # os.path.join( script_dir, 'wf_03_userstransactions.db') une el directorio del script con el nombre del archivo de la base de datos. Esto asegura que la ruta sea correcta sin importar el sistema operativo. 
    conn = sqlite3.connect(os.path.join(script_dir, 'wf_03_userstransactions.db'))
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users_payment_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        country TEXT,
        phone_number TEXT,
        payment_amount FLOAT,
        payment_invoice_date TEXT
    )''')

    api_url = os.getenv("MOCKAPI_URL")

    if not api_url:

        raise SystemExit("Falta la variable de entorno MOCKAPI_URL (ver .env.example)")
    get_data = urllib.request.urlopen(api_url, context=ctx)
    read_data = get_data.read().decode()

    access_data = json.loads(read_data)

    for item in access_data:
        cur.execute('''INSERT INTO users_payment_info (name, email, country, phone_number, payment_amount, payment_invoice_date)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (item['name'], item['email'], item['residence_country'], item['phone_number'], item['payment_amount'], item['createdAt']))

    for item in access_data:
        payment_data.append({
            "name": item['name'],
            "email": item['email'],
            "country": item['residence_country'],
            "phone_number": item['phone_number'],
            "payment_amount": item['payment_amount'],
            "payment_invoice_date": item['createdAt'],
            "id": int(item['id'])
        })

    print("Voy a guardar el JSON en:", os.path.abspath('wf_03_payment_data.json'))

    # os.path.join(script_dir, 'wf_03_payment_data.json') une el directorio del script con el nombre del archivo JSON. Esto asegura que la ruta sea correcta sin importar el sistema operativo.
    with open(os.path.join(script_dir, 'wf_03_payment_data.json'), 'w') as json_file:
        json.dump({"payment_data": payment_data}, json_file, indent=4)

except (IndexError, KeyError, ValueError, json.JSONDecodeError, sqlite3.Error) as e:
    print(f"Error: {e}")

except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")

except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")

finally:
    if conn:
        conn.commit()
        conn.close()

