"""
Скрипт миграции базы данных

Добавляет новые поля для поддержки языков и тегов:
- users.language_code
- categories.language, categories.linked_category_id
- content.language, content.linked_content_id, content.search_tags

Запустите этот скрипт один раз после обновления моделей.
"""
import asyncio
import sqlite3
from pathlib import Path
import config


async def migrate_database():
    """
    Добавляет новые колонки в существующую базу данных
    """
    db_path = Path("bot.db")
    
    if not db_path.exists():
        print("База данных не найдена. Она будет создана автоматически при первом запуске бота.")
        return
    
    print(f"Начинаю миграцию базы данных: {db_path}")
    
    # Используем синхронный sqlite3 для миграции
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Проверяем и добавляем колонки в таблицу users
        print("Проверяю таблицу users...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "language_code" not in columns:
            print("  -> Добавляю колонку language_code в users")
            cursor.execute("ALTER TABLE users ADD COLUMN language_code VARCHAR(10) DEFAULT 'ru'")
        else:
            print("  [OK] Колонка language_code уже существует")
        
        # Проверяем и добавляем колонки в таблицу categories
        print("Проверяю таблицу categories...")
        cursor.execute("PRAGMA table_info(categories)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "language" not in columns:
            print("  -> Добавляю колонку language в categories")
            cursor.execute("ALTER TABLE categories ADD COLUMN language VARCHAR(10) DEFAULT 'ru'")
        else:
            print("  [OK] Колонка language уже существует")
        
        if "linked_category_id" not in columns:
            print("  -> Добавляю колонку linked_category_id в categories")
            cursor.execute("ALTER TABLE categories ADD COLUMN linked_category_id INTEGER")
        else:
            print("  [OK] Колонка linked_category_id уже существует")
        
        # Проверяем и добавляем колонки в таблицу content
        print("Проверяю таблицу content...")
        cursor.execute("PRAGMA table_info(content)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "language" not in columns:
            print("  -> Добавляю колонку language в content")
            cursor.execute("ALTER TABLE content ADD COLUMN language VARCHAR(10) DEFAULT 'ru'")
        else:
            print("  [OK] Колонка language уже существует")
        
        if "linked_content_id" not in columns:
            print("  -> Добавляю колонку linked_content_id в content")
            cursor.execute("ALTER TABLE content ADD COLUMN linked_content_id INTEGER")
        else:
            print("  [OK] Колонка linked_content_id уже существует")
        
        if "search_tags" not in columns:
            print("  -> Добавляю колонку search_tags в content")
            cursor.execute("ALTER TABLE content ADD COLUMN search_tags TEXT")
        else:
            print("  [OK] Колонка search_tags уже существует")
        
        # Сохраняем изменения
        conn.commit()
        print("\n[OK] Миграция завершена успешно!")
        
        # Обновляем существующие записи
        print("\nОбновляю существующие записи...")
        cursor.execute("UPDATE users SET language_code = 'ru' WHERE language_code IS NULL")
        cursor.execute("UPDATE categories SET language = 'ru' WHERE language IS NULL")
        cursor.execute("UPDATE content SET language = 'ru' WHERE language IS NULL")
        conn.commit()
        print("[OK] Существующие записи обновлены")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка при миграции: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Миграция базы данных для поддержки языков")
    print("=" * 50)
    print()
    
    try:
        asyncio.run(migrate_database())
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        exit(1)

