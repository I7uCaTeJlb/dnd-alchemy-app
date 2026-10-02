from sqlalchemy import create_engine, Table, MetaData, select
from contextlib import contextmanager

type_db = "sqlite"
db_path = "../data/alchemy_database.db"

# engine (Движок) — это «Администратор» или «Шлюз».
#       Он знает, где лежит база данных и на каком языке с ней разговаривать (SQLite, PostgreSQL и т.д.).
#       Он управляет пулом соединений, но сам по себе запросы не выполняет.
# connection (Соединение) — это «Сеанс работы» или «Телефонная линия».
#       Это активная связь с базой. Именно через этот объект вы физически отправляете SQL-команды
#       (SELECT, INSERT) и получаете ответы. Когда вы закрываете соединение (connection.close()), линия обрывается.
# MetaData (Метаданные) — это «Каталог» или «Чертеж».
#       Это словарь, в котором SQLAlchemy хранит схему вашей базы: какие есть таблицы,
#       какие в них колонки, какие типы данных и ограничения. Благодаря MetaData вам не нужно писать
#       названия таблиц и колонок строками — вы обращаетесь к ним как к объектам Python.

@contextmanager
def CONNECT(database: str = type_db, path: str = db_path):               # Контекстный менеджер для работы внутри with
    engine = create_engine(f"{database}:///{path}", echo=False)
    connect = engine.connect()
    metadata = MetaData()
    try:
        yield engine, connect, metadata
    finally:
        connect.commit()

def CREATE(table: str, data: tuple, columns: tuple = ()):
    table = Table(table, data[2], autoload_with=data[0])                        # Подгружаем структуру таблицы из БД


def READ(table_name: str, data: tuple, columns: tuple = ()):

    # table: название таблицы, из которой читаем данные
    # data: engine, connect, metadata
    # *colums: список столбцов, которые читаем. Если пусто читаем все

    table = Table(table_name, data[2], autoload_with=data[0])                        # Подгружаем структуру таблицы из БД

    if len(columns) == 0: select_query = select(table)                          # READ ALL
    else:
        cols_to_select = [getattr(table.c, col_name) for col_name in columns]   # читаем определенные столбцы
        select_query = select(*cols_to_select)

    return [dict(row._mapping) for row in connection.execute(select_query)]     # Возвращаем массив словарей

with CONNECT() as data:
    connection = data[1]
    engine = data[0]
    print(READ("actions", data))