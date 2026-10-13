import json
import datetime as dt

with open('/scripts/wf_ejer_01/input_2.json', 'r', encoding= 'utf_8') as file:
    items = json.load(file)

ventas_totales = 0
valor_total_vendido = 0

resumem = {}

for item in items:
    subtotal_factura = item['precio_unitario']*item['cantidad']
    item['total_vendido'] = subtotal_factura

    ventas_totales += 1 

    valor_total_vendido += subtotal_factura
    

resumem['numero_de_ventas_diaria'] =  ventas_totales
resumem['valor_total_vendido'] = valor_total_vendido
resumem['ticket_promedio'] = valor_total_vendido/ventas_totales
resumem['fecha'] = dt.datetime.now().strftime('%Y-%m-%d')


info_consolidada = {
    'desglose_de_ventas': items,
    'resumen': resumem
}

with open('/scripts/wf_ejer_01/output_2.json', 'w', encoding= 'utf_8') as file:
    json.dump(info_consolidada, file, indent=4)