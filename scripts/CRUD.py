import sqlite3
from contextlib import contextmanager
from json import dumps, loads

from sqlalchemy.engine import cursor

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


from json import loads

def read_all(table: str, cursor):
    cursor.execute(f"SELECT * FROM {table}")
    result = []

    for data in cursor.fetchall():
        parsed_data = []

        # Проверяем каждое значение в строке
        for value in data:
            if isinstance(value, str):                      # JSON может быть только в строках, поэтому проверяем тип
                try:
                    parsed = loads(value)                   # Пытаемся распарсить строку как JSON
                    if isinstance(parsed, (dict, list)):    # Если dict или list заменяем на Python-объект
                        parsed_data.append(parsed)
                    else:
                        parsed_data.append(value)           # Иначе оставляем как строку
                except:
                    parsed_data.append(value)               # Если не удалось распарсить (обычный текст) — оставляем как есть
            else:
                parsed_data.append(value)

        result.append(tuple(parsed_data))

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

def upsert(cursor, table: str, *data, columns=None, primary_key=None):
    new_name = data[0]
    old_name = data[1][0]

    # Сериализуем ВСЕ нестандартные типы (list, tuple, dict, set)
    values = []
    for x in data[1][1:]:
        if isinstance(x, (list, tuple, dict, set)):
            values.append(dumps(x, ensure_ascii=False))
        else:
            values.append(x)

    if columns is None or primary_key is None:
        temp_cursor = cursor.connection.cursor()
        names_list, PK_list, _ = get_structure_table(temp_cursor, table)
        temp_cursor.close()
    else:
        names_list, PK_list = columns, primary_key

    other_cols = [c for c in names_list if c not in PK_list]
    if len(values) != len(other_cols):
        raise ValueError(f"{table}: ожидалось {len(other_cols)} значений, получено {len(values)}")

    if old_name is None:
        cols = [f'"{PK_list[0]}"'] + [f'"{c}"' for c in other_cols]
        query = (f'INSERT INTO {table} ({", ".join(cols)}) '
                 f'VALUES ({", ".join(["?"] * len(cols))})')
        cursor.execute(query, (new_name, *values))
        return

    if new_name.strip() == str(old_name).strip():
        set_clause   = ", ".join(f'"{c}" = ?' for c in other_cols)
        where_clause = ", ".join(f'"{c}" = ?' for c in PK_list)

        query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
        cursor.execute(query, (*values, old_name))
    else:
        set_clause   = ", ".join(f'"{c}" = ?' for c in names_list)
        where_clause = ", ".join(f'"{c}" = ?' for c in PK_list)

        query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
        cursor.execute(query, (new_name, *values, old_name))