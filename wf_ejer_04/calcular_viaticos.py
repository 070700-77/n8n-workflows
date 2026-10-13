import os
import ssl
import json
from dotenv import load_dotenv
import urllib.request, urllib.error, urllib.parse
import re


def normalize_number(value):
    # Si el valor ya es numérico, convertirlo directamente a float.
    if isinstance(value, (int, float)):
        return float(value)

    # Eliminar símbolos de moneda, espacios y caracteres no numéricos.
    # Ejemplo: "$ 1.250,75 COP" -> "1.250,75"
    clean_value = re.sub(r'[^\d.,]', '', str(value))

    # Validar que el valor no esté vacío.
    if not clean_value:
        raise ValueError(f"No se encontró un número en: {value!r}")

    # Identificar la posición del último punto o coma.
    last_separator_position = max(
        clean_value.rfind('.'),
        clean_value.rfind(',')
    )

    # Si no existen separadores, convertir directamente.
    if last_separator_position == -1:
        return float(clean_value)

    # Contar los dígitos después del último separador.
    digits_after_separator = (
        len(clean_value) - last_separator_position - 1
    )

    # Verificar si el número contiene puntos y comas.
    has_both_separators = (
        '.' in clean_value and ',' in clean_value
    )

    # Interpretar el último separador como decimal si hay ambos
    # tipos de separadores o si no tiene exactamente 3 dígitos después.
    if has_both_separators or digits_after_separator != 3:

        # Eliminar los separadores de miles de la parte entera.
        integer_part = re.sub(
            r'[.,]',
            '',
            clean_value[:last_separator_position]
        )

        # Extraer la parte decimal.
        decimal_part = clean_value[last_separator_position + 1:]

        return float(f"{integer_part}.{decimal_part}")

    # Si el último separador tiene 3 dígitos después,
    # interpretarlo como separador de miles.
    # Ejemplo: "1.250" -> 1250.0
    return float(re.sub(r'[.,]', '', clean_value))


def get_policy_limit(policy, category):
    # Busca el límite de una categoría sin importar cómo esté organizado
    # politica_viajes.json. Soporta, por ejemplo:
    #   {"alimentacion": 60}
    #   {"alimentacion": "60"}
    #   {"alimentacion": {"limite_diario_usd": 60}}
    #   {"categorias": {"alimentacion": {"limite_diario": 60}}}
    #   {"categorias": [{"categoria": "alimentacion", "limite_diario_usd": 60}]}
    category = category.strip().lower()

    if isinstance(policy, dict):
        for key, value in policy.items():
            if str(key).strip().lower() == category:
                # El valor puede ser directamente el número...
                if not isinstance(value, (dict, list)):
                    return normalize_number(value)
                # ...o un diccionario con el límite adentro
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if 'limite' in str(sub_key).lower() or 'limit' in str(sub_key).lower():
                            return normalize_number(sub_value)
        # Si no está en este nivel, buscar en los niveles internos
        for value in policy.values():
            if isinstance(value, (dict, list)):
                found = get_policy_limit(value, category)
                if found is not None:
                    return found

    elif isinstance(policy, list):
        for entry in policy:
            if isinstance(entry, dict):
                name = str(entry.get('categoria', entry.get('nombre', ''))).strip().lower()
                if name == category:
                    for sub_key, sub_value in entry.items():
                        if 'limite' in str(sub_key).lower() or 'limit' in str(sub_key).lower():
                            return normalize_number(sub_value)
                found = get_policy_limit(entry, category)
                if found is not None:
                    return found

    return None


load_dotenv()

x_rapidapi_key = os.getenv("X_RAPIDAPI_KEY")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'info_consolidada_base.json'), 'r', encoding='utf-8') as employees_invoices:
    employees_data = json.load(employees_invoices)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'politica_viajes.json'), 'r', encoding='utf-8') as policy_file:
    policy_data = json.load(policy_file)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input0_listaempleados.json'), 'r', encoding='utf-8') as employees_info:
    list_employees = json.load(employees_info)

# Memoria de tasas: guarda la tasa de cada moneda la primera vez que se consulta.
# Así se hace UNA llamada por moneda (EUR, MXN, PEN...) en vez de una por cada gasto.
# USD -> USD no necesita API: la tasa es 1.
rates_cache = {'USD': 1.0}

# Las tasas se guardan en un archivo. Si el programa se vuelve a correr,
# las reutiliza y NO gasta llamadas a la API. Borra tasas_cache.json
# cuando quieras tasas nuevas.
rates_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasas_cache.json')
if os.path.exists(rates_file):
    with open(rates_file, 'r', encoding='utf-8') as f:
        rates_cache.update(json.load(f))

# Validar la política ANTES de gastar llamadas a la API.
# Si un límite no se encuentra, el programa se detiene aquí y muestra el archivo.
for policy_category in ['alimentacion', 'transporte', 'hospedaje', 'otros']:
    found_limit = get_policy_limit(policy_data, policy_category)
    if found_limit is None:
        print(f"No encontré el límite de '{policy_category}' en politica_viajes.json:")
        print(json.dumps(policy_data, ensure_ascii=False, indent=4))
        raise SystemExit(1)
    print(f"Límite {policy_category}: {found_limit} USD")

for item in employees_data:
    for employee in list_employees:
        if item['cedula'] == employee['cedula']:
            item['nombre'] = employee.get('nombre', '')
            cost = item.get('valor', 0)
            real_cost = normalize_number(item.get('valor', 0))
            # Para que el valor tenga doble digito decimal, se puede usar la función round() y luego formatear el número a una cadena con dos decimales.
            item['valor'] = round(real_cost, 2)

            currency = item.get('moneda', '').upper()
            item['moneda'] = currency  # Guardar la moneda ya normalizada (usd -> USD)
            category = item.get('categoria', '')

            try:
                if currency not in rates_cache:
                    headers = {
                        'X-RapidAPI-Key': x_rapidapi_key,
                        'X-RapidAPI-Host': 'currency-conversion-and-exchange-rates.p.rapidapi.com'
                    }

                    # Se pide la conversión de 1 unidad para obtener la tasa
                    params = {
                    'amount': 1,
                    'from': currency,
                    'to': 'USD'
                    }

                    query_string = urllib.parse.urlencode(params)

                    base_url = 'https://currency-conversion-and-exchange-rates.p.rapidapi.com/convert'
                    full_url = f"{base_url}?{query_string}"

                    req = urllib.request.Request(full_url, headers=headers)
                    acess = urllib.request.urlopen(req, context=ctx)
                    response = acess.read().decode('utf-8')

                    data = json.loads(response)

                    # La API devuelve el valor convertido en la llave 'result', no en 'amount'.
                    # ('amount' solo existe dentro de data['query'] y es el valor que se envió.)
                    rate = data.get('result')
                    if not isinstance(rate, (int, float)):
                        # Mostrar la respuesta completa para saber qué devolvió la API
                        print(f"Respuesta inesperada de la API para {currency}: {data}")
                        rate = 0
                    rates_cache[currency] = float(rate)
                    # Guardar solo tasas válidas para no repetir la llamada en la próxima corrida
                    if rate:
                        with open(rates_file, 'w', encoding='utf-8') as f:
                            json.dump(rates_cache, f, indent=4)

                rate = rates_cache[currency]
                converted_amount_usd = round(real_cost * rate, 2)
                item['tasa_usada'] = rate
                item['valor_convertido_USD'] = converted_amount_usd
                # Se crea siempre la llave; si el gasto supera el límite se sobrescribe abajo
                item['valor_no_respaldado_USD'] = 0

                print(f"Converted {real_cost} {currency} to {converted_amount_usd} USD for category '{category}'.")

                if item['categoria'] == 'alimentacion':
                        policy_limit = get_policy_limit(policy_data, 'alimentacion')
                        if converted_amount_usd > policy_limit:
                            unrespalded_amount = converted_amount_usd - policy_limit
                            item['valor_no_respaldado_USD'] = round(unrespalded_amount, 2)
                elif item['categoria'] == 'transporte':
                    policy_limit = get_policy_limit(policy_data, 'transporte')
                    if converted_amount_usd > policy_limit:
                        unrespalded_amount = converted_amount_usd - policy_limit
                        item['valor_no_respaldado_USD'] = round(unrespalded_amount, 2)
                elif item['categoria'] == 'hospedaje':
                    policy_limit = get_policy_limit(policy_data, 'hospedaje')
                    if converted_amount_usd > policy_limit:
                        unrespalded_amount = converted_amount_usd - policy_limit
                        item['valor_no_respaldado_USD'] = round(unrespalded_amount, 2)
                else:
                    policy_limit = get_policy_limit(policy_data, 'otros')
                    if converted_amount_usd > policy_limit:
                        unrespalded_amount = converted_amount_usd - policy_limit
                        item['valor_no_respaldado_USD'] = round(unrespalded_amount, 2)


            except urllib.error.HTTPError as e:
                print(f"HTTP Error: {e.code} - {e.reason} for category '{category}'.")
            except urllib.error.URLError as e:
                print(f"URL Error: {e.reason} for category '{category}'.")

        else:
            continue  # Si la cédula no coincide, pasar al siguiente item

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'info_consolidada_contable.json'), 'w', encoding='utf-8') as employees_invoices:
    json.dump(employees_data, employees_invoices, ensure_ascii=False, indent=4)