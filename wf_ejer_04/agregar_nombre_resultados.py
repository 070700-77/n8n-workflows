import os
import json
# Set the path to the input JSON file

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input_informacion_usuarios_ok.json'), 'r', encoding = 'utf_8') as employees_invoices:
    employees_data = json.load(employees_invoices)

results = []    
file_name = None  # Initialize file_name variable

for item in employees_data:
    if 'result' in item and item['result'] == 'ok':
        file_name = employees_data[0]['name']
        continue
    else:
        item['cedula'] = file_name.split('_')[1]
        item['fecha'] = file_name.split('_')[2]
        results.append(item)

pretty_json = json.dumps(results, indent=4, ensure_ascii=False)
print(pretty_json)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output_resultados.json'), 'w', encoding='utf-8') as output_file:
    json.dump(results, output_file, ensure_ascii=False, indent=4)