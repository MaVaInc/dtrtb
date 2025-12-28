"""Проверка базы данных"""
import sqlite3
from pathlib import Path

db_path = Path("bot.db")
if not db_path.exists():
    print(f"❌ Файл {db_path} не найден!")
    exit(1)

print(f"Проверяем базу данных: {db_path.absolute()}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Проверяем таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"\nТаблицы в базе: {tables}")

# Проверяем таблицу allowed_external_ids
if 'allowed_external_ids' in tables:
    cursor.execute("SELECT COUNT(*) FROM allowed_external_ids")
    count = cursor.fetchone()[0]
    print(f"\nЗаписей в allowed_external_ids: {count}")
    
    cursor.execute("SELECT external_id, is_active, created_at FROM allowed_external_ids")
    rows = cursor.fetchall()
    print("\nВсе ID в базе:")
    for row in rows:
        print(f"  - {row[0]} (active: {row[1]}, created: {row[2]})")
else:
    print("\n❌ Таблица allowed_external_ids не найдена!")

conn.close()

