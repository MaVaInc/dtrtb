"""
Скрипт для добавления разрешенных external_id в базу данных

Использование:
1. Создайте файл ids.txt с ID (по одному на строку)
2. Запустите: python add_allowed_ids.py

Формат файла ids.txt:
12343412
13324066
11234067
...
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db import async_session_maker, init_db
from database.crud import add_allowed_external_id, get_all_allowed_external_ids, get_allowed_external_id


async def add_ids_from_file(filename: str = "ids.txt"):
    """Добавляет ID из файла в базу данных"""
    import traceback
    from database.crud import is_external_id_allowed, get_allowed_external_id
    
    ids_file = Path(filename)
    
    if not ids_file.exists():
        print(f"Файл {filename} не найден!")
        print(f"Создайте файл {filename} с ID (по одному на строку)")
        return
    
    print(f"Читаем ID из файла {filename}...")
    with open(ids_file, "r", encoding="utf-8") as f:
        ids = [line.strip() for line in f if line.strip()]
    
    print(f"Найдено {len(ids)} ID для добавления")
    
    # Проверяем подключение к БД
    from config import DATABASE_URL
    print(f"База данных: {DATABASE_URL}")
    
    async with async_session_maker() as session:
        added = 0
        skipped = 0
        errors = 0
        
        for external_id in ids:
            try:
                # Проверяем формат (7-9 цифр)
                if not external_id.isdigit() or len(external_id) < 7 or len(external_id) > 9:
                    print(f"Пропущен неверный формат: {external_id} (должно быть 7-9 цифр)")
                    skipped += 1
                    continue
                
                # Проверяем, существует ли уже
                existing = await get_allowed_external_id(session, external_id)
                if existing:
                    print(f"Уже существует: {external_id} (id={existing.id}, active={existing.is_active})")
                    skipped += 1
                    continue
                
                # Добавляем ID
                result = await add_allowed_external_id(session, external_id)
                added += 1
                print(f"Добавлен: {external_id} (id={result.id})")
                
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                print(f"\nОШИБКА при добавлении {external_id}:")
                print(f"  Тип: {error_type}")
                print(f"  Сообщение: {error_msg}")
                print(f"  Полный traceback:")
                traceback.print_exc()
                errors += 1
                skipped += 1
        
        # Проверяем результат
        print(f"\nРезультат:")
        print(f"  Добавлено: {added}")
        print(f"  Пропущено: {skipped}")
        print(f"  Ошибок: {errors}")
        
        # Показываем все ID в базе
        if added > 0 or errors > 0:
            print(f"\nПроверяем базу данных...")
            all_ids = await get_all_allowed_external_ids(session)
            print(f"Всего ID в базе: {len(all_ids)}")
            for allowed_id in all_ids:
                print(f"  - {allowed_id.external_id} (id={allowed_id.id}, active={allowed_id.is_active})")


if __name__ == "__main__":
    async def main():
        # Инициализируем БД (создаем таблицы, если их нет)
        await init_db()
        print("База данных инициализирована\n")
        
        filename = sys.argv[1] if len(sys.argv) > 1 else "ids.txt"
        await add_ids_from_file(filename)
    
    asyncio.run(main())

