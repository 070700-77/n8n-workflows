import os
import re
import sqlite3
import json
from datetime import datetime as dt


script_dir = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(os.path.join(script_dir, 'wf_02_bank clients scoring.db'))
cur = conn.cursor()


cards = {}
persons = {}
addresses = {}
bank_accounts = {}
transactions = {}
profiles = {}
profiles_transactions = {}
transactions_per_client = {}
profiles_rank = []


cur.execute('''SELECT * FROM cards''')
rows = cur.fetchall()
for row in rows:
    cards[row[0]] = {
        "type": row[1],
        "number": row[2],
        "raw_number": row[3],
        "expiry": row[4],
        "expiry_month": row[5],
        "expiry_year": row[6],
        "cvv": row[7],
        "name": row[8],
        "street": row[9],
        "city": row[10],
        "state": row[11],
        "zip": row[12],
        "country": row[13]
    }


cur.execute('''SELECT * FROM persons''')
rows = cur.fetchall()
for row in rows:
    persons[row[0]] = {
        "first_name": row[1],
        "last_name": row[2],
        "gender": row[3],
        "birth_date": row[4],
        "street": row[5],
        "city": row[6],
        "state": row[7],
        "zip": row[8],
        "country": row[9],
        "phone": row[10],
        "email": row[11]
    }


cur.execute('''SELECT * FROM addresses''')
rows = cur.fetchall()
for row in rows:
    addresses[row[0]] = {
        "street": row[1],
        "city": row[2],
        "state": row[3],
        "zip": row[4],
        "country": row[5]
    }


cur.execute('''SELECT * FROM bank_accounts''')
rows = cur.fetchall()
for row in rows:
    bank_accounts[row[0]] = {
        "bank_name": row[1],
        "routing_number": row[2],
        "account_number": row[3],
        "account_type": row[4]
    }


cur.execute('''SELECT * FROM transactions''')
rows = cur.fetchall()
for row in rows:
    transactions[row[0]] = {
        "amount": row[1],
        "currency": row[2],
        "merchant": row[3],
        "category": row[4],
        "date": row[5],
        "status": row[6]
    }


cur.execute('''SELECT * FROM profiles''')
rows = cur.fetchall()
for row in rows:
    profiles[row[0]] = {
        "first_name": row[1],
        "last_name": row[2],
        "gender": row[3],
        "birth_date": row[4],
        "ssn": row[5],
        "street": row[6],
        "city": row[7],
        "state": row[8],
        "zip": row[9],
        "country": row[10],
        "phone": row[11],
        "email": row[12],
        "card_type": row[13],
        "card_number": row[14],
        "card_raw_number": row[15],
        "card_expiry": row[16],
        "card_cvv": row[17],
        "bank_name": row[18],
        "routing_number": row[19],
        "account_number": row[20],
        "account_type": row[21]
    }


cur.execute('''SELECT * FROM profile_transactions''')
rows = cur.fetchall()
for row in rows:
    profiles_transactions[row[0]] = {
        "profile_id": row[1],
        "amount": row[2],
        "currency": row[3],
        "merchant": row[4], 
        "category": row[5],
        "date": row[6],
        "status": row[7]
    }



cur.execute('''CREATE VIEW IF NOT EXISTS Transacciones_por_cliente AS
SELECT
    profiles.id AS profile_id,
    profiles.first_name,
    profiles.last_name,
    profiles.email,
    profiles.account_type,
    profiles.birth_date,
    SUM(CASE WHEN profile_transactions.status = 'completed' THEN 1 ELSE 0 END) AS completed_purchase,
    SUM(CASE WHEN profile_transactions.status = 'failed'    THEN 1 ELSE 0 END) AS failed_purchase,
    SUM(CASE WHEN profile_transactions.status = 'pending'   THEN 1 ELSE 0 END) AS pending_purchase,
    COUNT(profile_transactions.id) AS total_transacciones
FROM profiles
LEFT JOIN profile_transactions
    ON profiles.id = profile_transactions.profile_id
GROUP BY profiles.id''')

cur.execute('''SELECT * FROM Transacciones_por_cliente''')
rows = cur.fetchall()

for row in rows:
    transactions_per_client[row[0]] = {
        "first_name": row[1],
        "last_name": row[2],
        "email": row[3],
        "account_type": row[4],
        "birth_date": row[5],
        "completed_purchase": row[6],
        "failed_purchase": row[7],
        "pending_purchase": row[8],
        "total_transacciones": row[9]
    }
    _id = row[0]
    first_name = row[1]
    last_name = row[2]
    email = row[3]

    # re.match(r"[^@]+@[^@]+\.[^@]+", email) sirve para validar que el correo electrónico tenga un formato válido, es decir, que contenga un "@" y un "." en la posición correcta.
    # [^@]+ significa que puede haber cualquier cantidad de caracteres que no sean "@", seguido de un "@", seguido de cualquier cantidad de caracteres que no sean "@", seguido de un ".", seguido de cualquier cantidad de caracteres que no sean "@".
    # \. significa que el punto debe ser un carácter literal, y no un comodín que puede representar cualquier carácter
    email_pattern = re.match(r"[^@]+@[^@]+\.[^@]+", email)
    # Se valida si el correo electrónico es válido o no, asignando un valor booleano a la variable email_valid
    if email_pattern is not None:
        valid_email = True
    else:
        valid_email = False

    # Se le asigna un puntaje a cada tipo de cuenta bancaria, siendo la cuenta corriente la de mayor puntaje, seguida de la cuenta de ahorros y finalmente cualquier otro tipo de cuenta.
    account_type = row[4]
    if account_type == 'checking':
        account_rank = 30
    elif account_type == 'savings':
        account_rank = 20
    else:
        account_rank = 10

    # dt.strptime(row[5], '%Y-%m-%d') funciona para convertir la fecha de nacimiento en un objeto datetime
    birth_date = dt.strptime(row[5], '%Y-%m-%d')
    formated_birth_date = birth_date.strftime('%Y-%m-%d')
    today = dt.now()
    # age sirve para calcular la edad del cliente a partir de su fecha de nacimiento y la fecha actual 
    # .year permite obtener el año de la fecha de nacimiento y de la fecha actual, y restarlos para obtener la edad
    age = today.year - birth_date.year
    if age >= 60:
        age_rank = 20
    elif age <= 59 and age >= 35:
        age_rank = 10
    else:
        age_rank = 5

    
    completed_purchase = int(row[6])
    failed_purchase = int(row[7])
    pending_purchase = int(row[8])

    total_transacciones = int(row[9])
    if total_transacciones == 0:
        sin_historial = True
    else:
        sin_historial = False
    

    # purcharse_rank sirve para calcular el puntaje de compra del cliente a partir de la cantidad de compras completadas
    purchase_rank = completed_purchase/total_transacciones * 50 if completed_purchase > 0 else 0

    rank = account_rank + age_rank + purchase_rank
    
    profiles_rank.append({
        "id": _id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "account_type": account_type,
        "account_rank": account_rank,
        "birth_date": formated_birth_date,
        "age": age,
        "age_rank": age_rank,
        "completed_purchase": completed_purchase,
        "failed_purchase": failed_purchase,
        "pending_purchase": pending_purchase,
        "total_transacciones": total_transacciones,
        "purchase_rank": purchase_rank,
        "average_rank": rank,
        "user without history": sin_historial,
        "valid_email": valid_email  
    })

with open('/scripts/wf_ejer_02/output_2.json', 'w', encoding='utf-8') as file:
    json.dump({
        "cards": cards,
        "persons": persons,
        "addresses": addresses,
        "bank_accounts": bank_accounts,
        "transactions": transactions,
        "profiles": profiles,
        "profiles_transactions": profiles_transactions,
        "transactions_per_client": transactions_per_client,
        "profiles_rank": profiles_rank
    }, file, ensure_ascii=False, indent=2)
