"""Проверка ID в базе данных"""
import asyncio
from database.db import async_session_maker
from database.crud import is_external_id_allowed, get_all_allowed_external_ids

async def check():
    async with async_session_maker() as session:
        # Проверяем конкретный ID
        test_id = "12344321"
        is_allowed = await is_external_id_allowed(session, test_id)
        print(f"ID {test_id} разрешен: {is_allowed}")
        
        # Показываем все разрешенные ID
        all_ids = await get_all_allowed_external_ids(session)
        print(f"\nВсего разрешенных ID в базе: {len(all_ids)}")
        for allowed_id in all_ids[:10]:  # Показываем первые 10
            print(f"  - {allowed_id.external_id} (active: {allowed_id.is_active})")

if __name__ == "__main__":
    asyncio.run(check())

