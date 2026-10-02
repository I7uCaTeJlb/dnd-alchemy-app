import sqlite3
import os

DB_PATH = "../data/alchemy_database.db"


def recreate_effects_table():
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: файл базы данных не найден по пути {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN TRANSACTION")

        # 1. Получаем текущую структуру таблицы Effects
        cursor.execute("PRAGMA table_info(Effects)")
        columns_info = cursor.fetchall()
        # Формат: (cid, name, type, notnull, dflt_value, pk)

        # 2. Получаем внешние ключи
        cursor.execute("PRAGMA foreign_key_list(Effects)")
        fk_list = cursor.fetchall()
        # Формат: (id, seq, table, from, to, on_update, on_delete, match)

        # 3. Получаем индексы и триггеры
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type IN ('index', 'trigger') 
            AND tbl_name = 'Effects' 
            AND sql IS NOT NULL
        """)
        schema_objects = [row[0] for row in cursor.fetchall()]

        # 4. Формируем новую структуру таблицы
        # Новая структура: name, state, state_options, cost, action, action_options, main_tag, additional_tag, effect
        new_columns = [
            ("name", "VARCHAR", True, None, True),  # PK, FK -> Components
            ("state", "VARCHAR", True, None, True),  # PK, FK -> State
            ("state_options", "JSON", False, "NULL", False),  # Новая колонка (переименованная part)
            ("cost", "FLOAT", False, None, False),
            ("action", "VARCHAR", True, None, True),  # PK, FK -> Actions
            ("action_options", "JSON", False, "NULL", False),  # Новая колонка
            ("main_tag", "VARCHAR", False, None, False),
            ("additional_tag", "JSON", False, None, False),
            ("effect", "VARCHAR", False, None, False),
        ]

        # 5. Создаём CREATE TABLE
        col_defs = []
        pk_cols = []

        for name, col_type, notnull, dflt_value, pk in new_columns:
            parts = [f"{name} {col_type}"]
            if notnull:
                parts.append("NOT NULL")
            if dflt_value is not None:
                parts.append(f"DEFAULT {dflt_value}")
            if pk:
                pk_cols.append(name)
            col_defs.append(" ".join(parts))

        if pk_cols:
            col_defs.append(f"PRIMARY KEY ({', '.join(pk_cols)})")

        # Добавляем FK (только для name, state, action)
        for fk in fk_list:
            _, _, ref_table, from_col, to_col, on_update, on_delete, _ = fk
            # Пропускаем part, так как мы его переименовали
            if from_col == "part":
                continue
            fk_def = f"FOREIGN KEY ({from_col}) REFERENCES {ref_table}({to_col})"
            if on_update and on_update != "NO ACTION":
                fk_def += f" ON UPDATE {on_update}"
            if on_delete and on_delete != "NO ACTION":
                fk_def += f" ON DELETE {on_delete}"
            col_defs.append(fk_def)

        create_sql = f"CREATE TABLE Effects_new ({', '.join(col_defs)})"
        print(f"Создаём новую таблицу:\n{create_sql}\n")

        # 6. Создаём новую таблицу
        cursor.execute(create_sql)

        # 7. Копируем данные
        # Старая структура: name, state, part, cost, action, main_tag, additional_tag, effect
        # Новая структура: name, state, state_options, cost, action, action_options, main_tag, additional_tag, effect
        cursor.execute("""
            INSERT INTO Effects_new (name, state, state_options, cost, action, action_options, main_tag, additional_tag, effect)
            SELECT name, state, part, cost, action, NULL, main_tag, additional_tag, effect
            FROM Effects
        """)

        # 8. Удаляем старую таблицу
        cursor.execute("DROP TABLE Effects")

        # 9. Переименовываем новую
        cursor.execute("ALTER TABLE Effects_new RENAME TO Effects")

        # 10. Восстанавливаем индексы и триггеры
        for sql in schema_objects:
            cursor.execute(sql)

        # 11. Проверяем целостность
        conn.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()

        if violations:
            raise RuntimeError(f"Нарушения целостности FK: {violations}")

        cursor.execute("COMMIT")
        print("✓ Таблица Effects успешно пересоздана!")
        print("  - part переименован в state_options (тип изменён на JSON)")
        print("  - добавлен action_options (JSON, default NULL) после action")

    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"✗ Ошибка: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    recreate_effects_table()