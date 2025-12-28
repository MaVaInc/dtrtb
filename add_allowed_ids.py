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

from database.db import async_session_maker
from database.crud import add_allowed_external_id


async def add_ids_from_file(filename: str = "ids.txt"):
    """Добавляет ID из файла в базу данных"""
    ids_file = Path(filename)
    
    if not ids_file.exists():
        print(f"❌ Файл {filename} не найден!")
        print(f"Создайте файл {filename} с ID (по одному на строку)")
        return
    
    print(f"Читаем ID из файла {filename}...")
    with open(ids_file, "r", encoding="utf-8") as f:
        ids = [line.strip() for line in f if line.strip()]
    
    print(f"Найдено {len(ids)} ID для добавления")
    
    async with async_session_maker() as session:
        added = 0
        skipped = 0
        
        for external_id in ids:
            try:
                # Проверяем формат (7-9 цифр)
                if not external_id.isdigit() or len(external_id) < 7 or len(external_id) > 9:
                    print(f"⚠ Пропущен неверный формат: {external_id}")
                    skipped += 1
                    continue
                
                # Добавляем ID
                await add_allowed_external_id(session, external_id)
                added += 1
                print(f"✓ Добавлен: {external_id}")
                
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    print(f"⚠ Уже существует: {external_id}")
                    skipped += 1
                else:
                    print(f"❌ Ошибка при добавлении {external_id}: {e}")
                    skipped += 1
    
    print(f"\n✅ Готово!")
    print(f"Добавлено: {added}")
    print(f"Пропущено: {skipped}")


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "ids.txt"
    asyncio.run(add_ids_from_file(filename))

