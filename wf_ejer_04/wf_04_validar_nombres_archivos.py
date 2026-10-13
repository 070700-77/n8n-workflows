import os
import json

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input1_docsguardados.json'), 'r', encoding='utf-8') as info_drive:
    folder_data = json.load(info_drive)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input0_listaempleados.json'), 'r', encoding='utf-8') as info_sheet:
    employees_data = json.load(info_sheet)

results = []

for item in folder_data:
    name = item.get('name', '')
    name = name.split('.')[0]  # Remove file extension
    print(f"Validating file name: {name}")

    link = item.get('webViewLink', '')

    file_name = name.split('_')[0]

    if file_name != 'gastos':
        results.append({'name': name, 'result': 'Invalid file name format. Expected string at the beggining of file: gastos', 'link': link})
        continue

    else:
        file_name_id = name.split('_')[1] 
        identifier = 0 
        for info in employees_data:
            employee_id = info.get('cedula', '')
            if file_name_id != employee_id:
                continue
            else:
                identifier = 1
                break
        if identifier == 0:
            results.append({'name': name, 'result': f'Employee ID {file_name_id} not found in employee list.', 'link': link})
        else:
            results.append({'name': name, 'result': 'ok', 'link': link, 'Sheet': 'Gastos'})

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fname_validation_results.json'), 'w', encoding='utf-8') as output_file:
    json.dump(results, output_file, ensure_ascii=False, indent=4)
