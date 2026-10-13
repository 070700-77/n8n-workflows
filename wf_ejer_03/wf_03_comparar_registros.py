import os
import json
# abspath trae toda la ruta del programa, dirname saca el nombre del programa de la ruta completa, join busca y trae el programa
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'input_merge_payment_invoices.json'), 'r', encoding= 'utf-8') as file:
    data = json.load(file)

api_invoices = []
sheet_invoices = []

empty_info = []
conciliated = []
api_only = []
sheet_only = []
amount_discrepancy = []

for item in data:
    if 'name' in item:
        api_invoices.append({
        "name": item['name'],
        "email": item['email'],
        "country": item['country'],
        "phone_number": item['phone_number'],
        "payment_amount": item['payment_amount'],
        "payment_invoice_date": item['payment_invoice_date'],
        "id": item['id']    
        })
    else:
        sheet_invoices.append({
        "id": item['id'],
        "name": item['cliente'],
        "payment_amount": item['monto'],
        "payment_invoice_date": item['fecha_registro']
        })

if api_invoices == []:
    empty_info.append({'error': 'API doesent give program any invoice input'})

elif sheet_invoices == []:
    empty_info.append({'error': 'Sheet doesent give program any invoiceinput'})

else:
    for api_item in api_invoices:
        count = 0
        for sheet_item in sheet_invoices:
            api_id = api_item['id']
            sheet_id = sheet_item['id']

            if api_id == sheet_id:
                count = 1
                api_amount = float(api_item['payment_amount'])
                sheet_amount = float(sheet_item['payment_amount'])

                if api_amount == sheet_amount:
                    result = 'OK'
                    conciliated.append({'id': api_id, 'result': result})
                    break

                elif api_amount > sheet_amount or api_amount < sheet_amount:
                    difference = api_amount - sheet_amount
                    if -1 < difference < 1:
                        result = 'OK'
                        conciliated.append({'id': api_id, 'result': result})
                        break
                    else:
                        if difference < 0:
                            difference = difference * - 1
                        amount_discrepancy.append({'id': api_id, 'result': f'The result of the crosschecking between both invoice records generates a discrepancy of: ${difference}'})
                        break
            else:
                continue

        if count == 1:
            continue
        else:
            api_only.append({'id': api_id, 'result': 'Program couldnt found id in Sheets invoices'})
            continue

    for sheet_item in sheet_invoices:
        count = 0
        for api_items in api_invoices:
            if sheet_item['id'] == api_items['id']:
                count = 1
                break
            else:
                continue
        if count == 1:
            continue
        else:
            sheet_only.append({'id': sheet_item['id'], 'result': 'Program couldnt found id APIs invoices '})
            continue
        
print(empty_info)
print('-----\n')
print(conciliated)
print('-----\n')
print(amount_discrepancy)
print('-----\n')
print(api_only)
print('-----\n')
print(sheet_only)

final_output = {
    'empty_info': empty_info,
    'conciliated': conciliated,
    'api_only': api_only,
    'sheet_only': sheet_only,
    'amount_discrepancy': amount_discrepancy
    }

base = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(base, 'invoice_categories.json')
with open(output_path, 'w', encoding='utf-8') as file:
    json.dump(final_output, file, indent=4)