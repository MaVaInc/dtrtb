"""
Скрипт миграции для новой системы аутентификации

Добавляет:
1. Поле external_id в таблицу users
2. Таблицу allowed_external_ids для хранения разрешенных ID

Запуск: python migrate_auth.py
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from database.db import async_session_maker, engine
from database.models import Base


async def migrate():
    """Выполняет миграцию базы данных"""
    print("Начинаем миграцию базы данных...")
    
    async with async_session_maker() as session:
        try:
            # Проверяем, существует ли поле external_id
            result = await session.execute(
                text("PRAGMA table_info(users)")
            )
            columns = [row[1] for row in result.fetchall()]
            
            if "external_id" not in columns:
                print("Добавляем поле external_id в таблицу users...")
                await session.execute(
                    text("ALTER TABLE users ADD COLUMN external_id VARCHAR(20)")
                )
                await session.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_users_external_id ON users(external_id)")
                )
                await session.commit()
                print("✓ Поле external_id добавлено")
            else:
                print("✓ Поле external_id уже существует")
            
            # Создаем таблицу allowed_external_ids
            print("Создаем таблицу allowed_external_ids...")
            await session.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS allowed_external_ids (
                        id INTEGER NOT NULL PRIMARY KEY,
                        external_id VARCHAR(20) NOT NULL UNIQUE,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            )
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS ix_allowed_external_ids_external_id ON allowed_external_ids(external_id)")
            )
            await session.commit()
            print("✓ Таблица allowed_external_ids создана")
            
            print("\n✅ Миграция завершена успешно!")
            print("\nСледующие шаги:")
            print("1. Добавьте разрешенные external_id в таблицу allowed_external_ids")
            print("2. Используйте скрипт add_allowed_ids.py для массового добавления ID")
            
        except Exception as e:
            print(f"❌ Ошибка при миграции: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())

