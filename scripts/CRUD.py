import sqlite3
from contextlib import contextmanager
from json import dumps

db_path = "./data/alchemy_database.db"

# connection    - соединение с БД
# cursor        - объект для SQL запросов

@contextmanager
def open_db(database: str = db_path):               # Контекстный менеджер для работы внутри with
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        connection.commit()
        connection.close()

def read_all(table, cursor):                        # Функция для получения всех данных из таблицы
    cursor.execute(f"SELECT * FROM {table}")
    result = []
    for data in cursor.fetchall():
        result.append(data)
    return result

def delete_of_name(cursor, table: str, name: str):  # Функция удаления строки по name
    cursor.execute(f'DELETE FROM {table} WHERE Name = ?', (name,))

def get_structure_table(cursor, table: str):        # Функуция для возврата данных о столбцах

    cursor.execute(f'PRAGMA table_info({table})')

    fields = cursor.fetchall()
    name_column    = []     # Названия колонок таблиц
    PK_list        = []     # Списко PK таблицы
    name_type_list = []     # Имя столбца и его тип данных

    for x in fields:
        if x[5]: PK_list.append(x[1])
        name_column.append(x[1])
        name_type_list.append((x[1], x[2]))

    return name_column, PK_list, name_type_list

def upsert(cursor, table: str, *data, columns = None, primary_key = None): # UPDATE and INSERT INTO

    new_name = data[0]
    old_name = data[1][0]
    values = []
    # Если есть список, его нужно передать как json, а не просто данные!
    for x in data[1][1:]:
        if isinstance(x, list): values.append(dumps(x, ensure_ascii=False))
        else: values.append(x)

    if columns == None or primary_key == None:
        names_list, PK_list, _ = get_structure_table(cursor, table)
    else:
        names_list, PK_list = columns, primary_key

    print(new_name)
    print(old_name)
    print(values)

    print(f'INSERT INTO {table} ({names_list}, {PK_list}) VALUES ({ ", ".join(["?"] * len(data[1])) })', (new_name, *values))
    return
    if old_name == None:

        cursor.execute(
            f'INSERT INTO {table} ({new_name}, {values}) VALUES ({ ", ".join(["?"] * len(data[1])) })',
            (new_name, *values)
        )
    else:

        if new_name.strip() == old_name.strip():
            cursor.execute(f'UPDATE {table} SET '
                            f'{ ", ".join([f"{x} = ?" for x in names_list if x not in PK_list]) } '
                            f'WHERE { ", ".join([f"{x} = ?" for x in PK_list]) }',
                (*values, old_name)
            )
        else:
            cursor.execute(f'UPDATE {table} SET '
                            f'{ ", ".join([f"{x} = ?" for x in names_list]) } '
                            f'WHERE { ", ".join([f"{x} = ?" for x in PK_list]) }',
                (new_name, *values, old_name)
            )