"""
Миграция для добавления поля disclaimer_accepted в таблицу users

Запуск: python migrate_disclaimer.py
"""
import asyncio
from sqlalchemy import text
from database.db import async_session_maker, engine


async def migrate():
    """Добавляет поле disclaimer_accepted в таблицу users"""
    print("Начинаем миграцию для добавления disclaimer_accepted...")
    
    async with engine.begin() as conn:
        # Проверяем, существует ли колонка
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='disclaimer_accepted'
        """))
        exists = result.scalar() > 0
        
        if exists:
            print("Колонка disclaimer_accepted уже существует. Пропускаем миграцию.")
            return
        
        # Добавляем колонку disclaimer_accepted
        print("Добавляем колонку disclaimer_accepted...")
        await conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN disclaimer_accepted BOOLEAN NOT NULL DEFAULT 0
        """))
        
        # Добавляем колонку disclaimer_accepted_at
        print("Добавляем колонку disclaimer_accepted_at...")
        await conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN disclaimer_accepted_at DATETIME
        """))
        
        print("Миграция успешно завершена!")


if __name__ == "__main__":
    asyncio.run(migrate())

