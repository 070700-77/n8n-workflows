import json
#datetime es el módulo que nos permite trabajar con fechas y horas
import datetime as dt

# Abrimos el archivo JSON de entrada y lo cargamos en una variable llamada 'items'. La función json.load() convierte el contenido del archivo JSON en un objeto de Python (en este caso, una lista de diccionarios).
with open("/scripts/wf_ejer_01/input_1.json", 'r', encoding = 'utf-8') as file:
    # json.load() -> convierte un archivo JSON en un objeto de Python (en este caso, una lista de diccionarios)
    items = json.load(file)

for item in items:

    if '/' in item['fecha']:
        # dt.datetime.strptime() convierte un string en un objeto datetime. Osea, convierte un string en el formato de fecha que le indiquemos. En este caso, el string tiene el formato '%Y/%m/%d' (Año/Mes/Día) para que Python pueda reconocerlo como fecha.
        # strptime() -> de string a datetime 
        #strftime('%Y-%m-%d') convierte un objeto datetime en un string con el formato que le indiquemos. En este caso, el formato '%Y-%m-%d' (Año-Mes-Día) para que quede en el formato que necesitamos.
        # strftime() -> de datetime a string otra vez
        item['fecha'] = dt.datetime.strptime(item['fecha'], '%Y/%m/%d').strftime('%Y-%m-%d')
    else:
        # Si la fecha no tiene '/', entonces asumimos que tiene el formato '%d-%m-%Y' (Día-Mes-Año) y hacemos la conversión correspondiente.
        item['fecha'] = dt.datetime.strptime(item['fecha'], '%d-%m-%Y').strftime('%Y-%m-%d')

    # Validamos si el precio_unitario tiene el símbolo '$'
    if '$' in item['precio_unitario']:
        # Reemplazamos el símbolo '$' por una cadena vacía para poder convertirlo a float. 
        item['precio_unitario'] = item['precio_unitario'].replace('$','')
        # Validamos si el precio_unitario tiene un punto '.' para saber si es un número decimal o no. Si tiene un punto, lo reemplazamos por una cadena vacía para poder convertirlo a float. Si no tiene un punto, lo convertimos directamente a float.
        if '.' in item['precio_unitario']:
            item['precio_unitario'] = float(item['precio_unitario'].replace('.',''))
        else:
            item['precio_unitario'] = float(item['precio_unitario'])

    else:
        pass
        
# Abrimos el archivo JSON de salida y escribimos los datos procesados en él. El parametro "w" indica que vamos a escribir en el archivo, y el parametro "encoding = 'utf-8'" indica que vamos a usar la codificación UTF-8 para el archivo.
with open('/scripts/wf_ejer_01/output_1.json', 'w', encoding = 'utf-8') as file:
    # json.dump() -> convierte un objeto de Python en un archivo JSON. El parametro indent = 4 indica que queremos que el archivo JSON tenga una sangría de 4 espacios para que sea más legible.
    # el parametro file es el archivo donde vamos a escribir los datos procesados. En este caso, es el archivo de salida que acabamos de abrir.
    json.dump(items, file, indent = 4)

