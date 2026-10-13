ANDES ADVISORY — DATOS DE ENTRADA PARA EL CASO DE ESTUDIO

1) Cargar Empleados.xlsx como Google Sheet llamado "Empleados".
2) Dejar politica_viajes.json disponible para el workflow como archivo local.
3) Subir el contenido de Gastos/Entrantes a la carpeta Drive Gastos/Entrantes.
4) Ejecutar el workflow.
5) Para probar reproceso/upsert del mismo empleado y mes, después de la primera corrida
   subir Gastos/Reproceso_Mismo_Mes/gastos_1018456721_2026-09.xlsx a Gastos/Entrantes
   y ejecutar otra vez.

CASOS BORDE INCLUIDOS
- "1.250,50": gastos_1018456721_2026-09.xlsx
- "1,250.50": gastos_1020304050_2026-09.xlsx
- "$ 45": gastos_1020304050_2026-09.xlsx
- moneda "usd": gastos_1033445566_2026-09.xlsx
- moneda "mxn": gastos_1020304050_2026-09.xlsx
- fecha vacía: gastos_1020304050_2026-09.xlsx
- categoría inventada "entretenimiento": gastos_1020304050_2026-09.xlsx
- nombre de archivo inválido: gasto_1098765432_2026-09.xlsx
- cédula no existente: gastos_5555555555_2026-09.xlsx
- aprobación parcial diaria determinística:
  * alimentación USD 35 + 40 el 2026-09-21 (límite 60)
  * transporte USD 30 + 25 el 2026-09-22 (límite 40)
- segundo archivo mismo empleado/mes:
  Gastos/Reproceso_Mismo_Mes/gastos_1018456721_2026-09.xlsx

NOTA
La regla para fecha vacía no especifica explícitamente el resultado en el enunciado.
El dato está incluido para que el workflow implemente una validación de integridad de fila
(por ejemplo, RECHAZADO con motivo FECHA_VACIA) sin bloquear el archivo completo.
