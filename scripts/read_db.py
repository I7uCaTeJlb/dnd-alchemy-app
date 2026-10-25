import sqlite3
import json
import os

DB_PATH = "../data/alchemy_database.db"


def get_conn():
    if not os.path.exists(DB_PATH):
        print(f"❌ Файл БД не найден: {DB_PATH}")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def main():
    conn = get_conn()
    if not conn:
        return

    cur = conn.cursor()

    # Получаем все таблицы
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row['name'] for row in cur.fetchall()]

    print("=" * 80)
    print(f"  БАЗА ДАННЫХ: {os.path.abspath(DB_PATH)}")
    print(f"  Таблиц: {len(tables)}")
    print("=" * 80)

    for table in tables:
        print(f"\n{'─' * 80}")
        print(f"   ТАБЛИЦА: {table}")
        print(f"{'─' * 80}")

        # --- Колонки ---
        cur.execute(f"PRAGMA table_info('{table}')")
        cols = cur.fetchall()

        print(f"\n  Колонки ({len(cols)}):")
        print(f"  {'#':<3} {'Имя':<25} {'Тип':<10} {'PK':<5} {'NotNull':<8} {'Default'}")
        print(f"  {'─' * 75}")
        for col in cols:
            pk = "✅" if col['pk'] else ""
            nn = "✅" if col['notnull'] else ""
            dflt = col['dflt_value'] if col['dflt_value'] else "-"
            col_type = col['type'] or "TEXT"
            print(f"  {col['cid']:<3} {col['name']:<25} {col_type:<10} {pk:<5} {nn:<8} {dflt}")

        # --- Foreign Keys ---
        cur.execute(f"PRAGMA foreign_key_list('{table}')")
        fks = cur.fetchall()

        if fks:
            print(f"\n  🔗 Foreign Keys ({len(fks)}):")
            for fk in fks:
                print(f"     {fk['from']} → {fk['table']}.{fk['to']} "
                      f"[UPDATE: {fk['on_update']}, DELETE: {fk['on_delete']}]")

        # --- Индексы ---
        cur.execute(f"PRAGMA index_list('{table}')")
        indexes = cur.fetchall()

        if indexes:
            print(f"\n  📇 Индексы ({len(indexes)}):")
            for idx in indexes:
                cur.execute(f"PRAGMA index_info('{idx['name']}')")
                idx_cols = cur.fetchall()
                col_names = ", ".join(c['name'] for c in idx_cols)
                unique = "UNIQUE" if idx['unique'] else ""
                print(f"     {idx['name']} ({unique}) → [{col_names}]")

        # --- Количество записей ---
        cur.execute(f"SELECT COUNT(*) as cnt FROM '{table}'")
        count = cur.fetchone()['cnt']
        print(f"\n  📊 Записей: {count}")

        # --- Примеры данных ---
        if count > 0:
            cur.execute(f"SELECT * FROM '{table}' LIMIT 30")
            rows = cur.fetchall()

            print(f"\n  💾 Примеры (до 3 записей):")
            for i, row in enumerate(rows, 1):
                print(f"\n    Запись #{i}:")
                for col in cols:
                    val = row[col['name']]
                    col_type = (col['type'] or '').upper()

                    # Красивый вывод JSON
                    if col_type == 'JSON' and val:
                        try:
                            parsed = json.loads(val)
                            if isinstance(parsed, list):
                                print(f"      {col['name']}: {parsed}")
                            else:
                                print(f"      {col['name']}: {parsed}")
                        except:
                            print(f"      {col['name']}: {val}")
                    else:
                        print(f"      {col['name']}: {val}")

        print()

    print("=" * 80)
    print("  ✅ Просмотр завершен. Данные не изменялись.")
    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    main()