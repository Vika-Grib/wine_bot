import sqlite3

import openpyxl

list_of_wines = []

file_name = 'wine_data.xlsx'
# Excel и активный лист
workbook = openpyxl.load_workbook(file_name)  # нужно чтобы открылась таблица ДО парсера, а закрывалась уже только после парсера всех страниц
sheet = workbook.active

conn = sqlite3.connect('wine_database.db')
# Создаем объект cursor, который позволяет нам взаимодействовать с базой данных и добавлять записи
cursor = conn.cursor()

column_A = sheet['A']
column_B = sheet['B']
for elem in range(len(column_A)):
    cursor.execute('''INSERT INTO wine_ratings(wine_name, rating) VALUES (?,?)''',
                   (column_A[elem].value, column_B[elem].value)) # value - значение ячейки, а не сама ячейка
    conn.commit()
print('done')

