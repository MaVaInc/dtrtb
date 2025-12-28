"""
Скрипт для назначения администратора

Этот скрипт позволяет назначить пользователя администратором бота.
Администратор получает доступ к админ-панели через команду /admin.

Использование:
    python set_admin.py <telegram_id>

Пример:
    python set_admin.py 123456789
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from database.db import async_session_maker
from database.crud import get_user_by_telegram_id
from database.models import User


async def set_admin(telegram_id: int):
    """
    Назначить пользователя администратором
    
    Args:
        telegram_id: Telegram ID пользователя
    """
    async with async_session_maker() as session:
        # Ищем пользователя
        user = await get_user_by_telegram_id(session, telegram_id)
        
        if not user:
            print(f"❌ Пользователь с Telegram ID {telegram_id} не найден в базе данных.")
            print("Пользователь должен сначала написать боту хотя бы раз.")
            return
        
        # Назначаем администратором
        user.is_admin = True
        user.is_allowed = True  # Также даем доступ
        await session.commit()
        
        print(f"✅ Пользователь {user.first_name or user.username or telegram_id} назначен администратором!")
        print(f"   Telegram ID: {telegram_id}")
        print(f"   Username: {user.username or 'не указан'}")
        print(f"\nТеперь пользователь может использовать команду /admin для доступа к админ-панели.")


async def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python set_admin.py <telegram_id>")
        print("\nПример:")
        print("  python set_admin.py 123456789")
        print("\nКак узнать Telegram ID:")
        print("  1. Напишите боту @userinfobot в Telegram")
        print("  2. Он покажет ваш ID")
        return
    
    try:
        telegram_id = int(sys.argv[1])
    except ValueError:
        print("❌ Ошибка: Telegram ID должен быть числом")
        return
    
    try:
        await set_admin(telegram_id)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

