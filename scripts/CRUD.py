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


def delete_of_name(cursor, table: str, name):
    if isinstance(name, str):
        cursor.execute(f'DELETE FROM {table} WHERE "name" = ?', (name,))
    elif isinstance(name, (tuple, list)):
        _, PK_list, _ = get_structure_table(cursor, table)
        if len(name) != len(PK_list):
            raise ValueError(
                f"Ожидается {len(PK_list)} значений PK для {table}, получено {len(name)}"
            )
        where_clause = " AND ".join([f'"{c}" = ?' for c in PK_list])
        query = f'DELETE FROM {table} WHERE {where_clause}'
        cursor.execute(query, tuple(name))
    else:
        raise TypeError(f"Неподдерживаемый тип name: {type(name)}")

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
    """
    data[0] - новый PK (кортеж в порядке PK_list)
    data[1] - (старый PK, value1, value2, ...)
    """
    new_pk = data[0]
    old_pk = data[1][0]
    values = data[1][1:]

    if not isinstance(new_pk, (tuple, list)):
        new_pk = (new_pk,)
    if not isinstance(old_pk, (tuple, list)):
        old_pk = (old_pk,)

    if columns is None or primary_key is None:
        temp_cursor = cursor.connection.cursor()
        names_list, PK_list, _ = get_structure_table(temp_cursor, table)
        temp_cursor.close()
    else:
        names_list, PK_list = columns, primary_key

    other_cols = [c for c in names_list if c not in PK_list]

    # Сериализуем JSON поля
    serialized_values = []
    for x in values:
        if isinstance(x, (list, tuple, dict, set)):
            serialized_values.append(dumps(x, ensure_ascii=False))
        else:
            serialized_values.append(x)

    if len(serialized_values) != len(other_cols):
        raise ValueError(f"{table}: ожидалось {len(other_cols)} значений, получено {len(serialized_values)}")

    # Создаём словарь: имя колонки → значение
    col_values = {}

    # Заполняем PK значения
    for i, col in enumerate(PK_list):
        if i < len(new_pk):
            col_values[col] = new_pk[i]

    # Заполняем остальные значения
    for i, col in enumerate(other_cols):
        col_values[col] = serialized_values[i]

    # Проверяем, является ли запись новой
    is_new_record = all(v is None for v in old_pk)

    if is_new_record:
        # INSERT
        cols = [f'"{c}"' for c in names_list]
        all_values = [col_values[c] for c in names_list]
        query = f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({", ".join(["?"] * len(cols))})'
        print(f"DEBUG INSERT: {query}")
        print(f"DEBUG VALUES: {all_values}")
        cursor.execute(query, all_values)
        return

    # UPDATE
    set_clause = ", ".join([f'"{c}" = ?' for c in names_list])
    where_clause = " AND ".join([f'"{c}" = ?' for c in PK_list])

    all_values = [col_values[c] for c in names_list] + list(old_pk)
    query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'

    print(f"DEBUG UPDATE: {query}")
    print(f"DEBUG VALUES: {all_values}")
    print(f"DEBUG col_values: {col_values}")

    cursor.execute(query, all_values)