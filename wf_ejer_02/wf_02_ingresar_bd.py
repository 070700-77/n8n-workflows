import os
import ssl
import json
import sqlite3
import urllib.request, urllib.parse, urllib.error
from dotenv import load_dotenv

load_dotenv()

x_rapidapi_key = os.getenv("X_RAPIDAPI_KEY")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# os.path.dirname(os.path.abspath(__file__)) obtiene la ruta del directorio donde se encuentra el script actual. Esto es útil para construir rutas relativas a partir de la ubicación del script, asegurando que los archivos se encuentren correctamente independientemente de desde dónde se ejecute el script.
# Esta línea de código obtiene la ruta del directorio donde se encuentra el script actual y la almacena en la variable 'script_dir'. Esto es útil para construir rutas relativas a partir de la ubicación del script, asegurando que los archivos se encuentren correctamente independientemente de desde dónde se ejecute el script.
script_dir = os.path.dirname(os.path.abspath(__file__))
# os.path.join(script_dir, 'wf_02_bank clients scoring.db') combina la ruta del directorio del script con el nombre del archivo de la base de datos para crear una ruta completa y correcta al archivo de la base de datos. Esto es importante para asegurarse de que el script pueda encontrar y acceder a la base de datos sin importar desde qué directorio se ejecute.
conn = sqlite3.connect(os.path.join(script_dir, 'wf_02_bank clients scoring.db'))

cur = conn.cursor()

try:
    # 1. Tarjetas sueltas (nivel raíz "cards")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            number TEXT,
            raw_number TEXT,
            expiry TEXT,
            expiry_month TEXT,
            expiry_year TEXT,
            cvv TEXT,
            name TEXT,
            street TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT
        )
    ''')

    # 2. Personas sueltas (nivel raíz "persons")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            birth_date TEXT,
            street TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT,
            phone TEXT,
            email TEXT
        )
    ''')

    # 3. Direcciones sueltas (nivel raíz "addresses")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            street TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT
        )
    ''')

    # 4. Cuentas bancarias sueltas (nivel raíz "bankAccounts")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT,
            routing_number TEXT,
            account_number TEXT,
            account_type TEXT
        )
    ''')

    # 5. Transacciones sueltas (nivel raíz "transactions")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            currency TEXT,
            merchant TEXT,
            category TEXT,
            date TEXT,
            status TEXT
        )
    ''')

    # 6. Perfiles (nivel raíz "profiles") — la parte "cabeza" del perfil
    cur.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            birth_date TEXT,
            ssn TEXT,
            street TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            country TEXT,
            phone TEXT,
            email TEXT,
            card_type TEXT,
            card_number TEXT,
            card_raw_number TEXT,
            card_expiry TEXT,
            card_cvv TEXT,
            bank_name TEXT,
            routing_number TEXT,
            account_number TEXT,
            account_type TEXT
        )
    ''')

    # 7. Transacciones DE cada perfil ("profiles[].recentTransactions")
    #    Necesita foreign key porque es una lista DENTRO de cada perfil
    cur.execute('''
        CREATE TABLE IF NOT EXISTS profile_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            amount REAL,
            currency TEXT,
            merchant TEXT,
            category TEXT,
            date TEXT,
            status TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
    ''')

    query_params = {
        "count": "100"
    }

    headers = {
        'x-rapidapi-key': os.getenv("X_RAPIDAPI_KEY"),
        "x-rapidapi-host": "dummy-payment-and-banking-data.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    base_url = 'https://dummy-payment-and-banking-data.p.rapidapi.com/everything'

    query_string = urllib.parse.urlencode(query_params)

    full_url = f"{base_url}?{query_string}"

    req = urllib.request.Request(full_url, headers=headers)
    get_response = urllib.request.urlopen(req, context=ctx)
    read_response = get_response.read().decode('utf-8')

    data = json.loads(read_response)

    # --- cards: dirección va anidada en card['address'] ---
    for card in data.get('cards', []):
        address = card.get('address', {}) or {}
        cur.execute('''
            INSERT INTO cards
                (type, number, raw_number, expiry, expiry_month, expiry_year, cvv, name,
                 street, city, state, zip, country)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            card.get('type'), card.get('number'), card.get('rawNumber'),
            card.get('expiry'), card.get('expiryMonth'), card.get('expiryYear'),
            card.get('cvv'), card.get('name'),
            address.get('street'), address.get('city'), address.get('state'),
            address.get('zip'), address.get('country')
        ))

    # --- persons: misma corrección de dirección anidada + claves camelCase ---
    for person in data.get('persons', []):
        address = person.get('address', {}) or {}
        cur.execute('''
            INSERT INTO persons
                (first_name, last_name, gender, birth_date,
                 street, city, state, zip, country, phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            person.get('firstName'), person.get('lastName'),
            person.get('gender'), person.get('birthDate'),
            address.get('street'), address.get('city'), address.get('state'),
            address.get('zip'), address.get('country'),
            person.get('phone'), person.get('email')
        ))

    # --- addresses: ya viene plano, no necesita ajuste de anidación ---
    for address in data.get('addresses', []):
        cur.execute('''
            INSERT INTO addresses (street, city, state, zip, country)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            address.get('street'), address.get('city'), address.get('state'),
            address.get('zip'), address.get('country')
        ))

    # --- bankAccounts: plano, pero con claves camelCase ---
    for bank_account in data.get('bankAccounts', []):
        cur.execute('''
            INSERT INTO bank_accounts (bank_name, routing_number, account_number, account_type)
            VALUES (?, ?, ?, ?)
        ''', (
            bank_account.get('bankName'), bank_account.get('routingNumber'),
            bank_account.get('accountNumber'), bank_account.get('accountType')
        ))

    # --- transactions: ya era correcto en el original (claves de una sola palabra) ---
    for transaction in data.get('transactions', []):
        cur.execute('''
            INSERT INTO transactions (amount, currency, merchant, category, date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            transaction.get('amount'), transaction.get('currency'),
            transaction.get('merchant'), transaction.get('category'),
            transaction.get('date'), transaction.get('status')
        ))

    # --- profiles: navega person -> primaryCard -> bankAccount, y ahora SÍ
    #     inserta recentTransactions usando el id real recién generado ---
    for profile in data.get('profiles', []):
        person = profile.get('person', {}) or {}
        address = person.get('address', {}) or {}
        card = profile.get('primaryCard', {}) or {}
        bank_account = profile.get('bankAccount', {}) or {}

        cur.execute('''
            INSERT INTO profiles
                (first_name, last_name, gender, birth_date, ssn,
                 street, city, state, zip, country, phone, email,
                 card_type, card_number, card_raw_number, card_expiry, card_cvv,
                 bank_name, routing_number, account_number, account_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            person.get('firstName'), person.get('lastName'), person.get('gender'),
            person.get('birthDate'), person.get('ssn'),
            address.get('street'), address.get('city'), address.get('state'),
            address.get('zip'), address.get('country'),
            person.get('phone'), person.get('email'),
            card.get('type'), card.get('number'), card.get('rawNumber'),
            card.get('expiry'), card.get('cvv'),
            bank_account.get('bankName'), bank_account.get('routingNumber'),
            bank_account.get('accountNumber'), bank_account.get('accountType')
        ))

        # id real que SQLite le acaba de asignar a este perfil -> es lo que
        # usamos como profile_id (FK) en profile_transactions
        # cur.lastrowid devuelve el id de la última fila insertada en la tabla, que en este caso es el id del perfil recién insertado. Esto nos permite relacionar las transacciones recientes con el perfil correspondiente.
        profile_id = cur.lastrowid

        for tx in profile.get('recentTransactions', []) or []:
            cur.execute('''
                INSERT INTO profile_transactions
                    (profile_id, amount, currency, merchant, category, date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile_id, tx.get('amount'), tx.get('currency'),
                tx.get('merchant'), tx.get('category'), tx.get('date'), tx.get('status')
            ))

    conn.commit()
    print(f"OK: {len(data.get('cards', []))} cards, {len(data.get('persons', []))} persons, "
          f"{len(data.get('profiles', []))} profiles insertados.")

except (IndexError, json.JSONDecodeError):
    print("Error: Failed to parse the response as JSON.")

except urllib.error.URLError as e:
    print(f"Error: {e.reason}")

except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")

except sqlite3.Error as e:
    print(f"SQLite Error: {e.args[0]}")

# finally siempre se ejecuta, aunque haya habido un error. Se usa para cerrar la conexión a la base de datos.
finally:
    conn.close()