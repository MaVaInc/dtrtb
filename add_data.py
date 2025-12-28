"""
Скрипт для добавления категорий и контента в базу данных

Этот скрипт позволяет легко добавлять категории и контент в бота.
Запустите его после первого запуска бота для заполнения базы данных.

Использование:
    python add_data.py

ВНИМАНИЕ: Этот скрипт добавляет данные в БД. Если данные уже существуют,
они могут быть продублированы. Для очистки БД удалите файл bot.db.
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from database.db import async_session_maker, init_db
from database.crud import (
    create_category,
    create_content,
    get_category_by_id
)


async def add_sample_data():
    """
    Добавляет примеры категорий и контента в базу данных
    
    Эта функция создает:
    1. Категории верхнего уровня (главное меню)
    2. Подкатегории
    3. Контент для категорий
    
    Вы можете изменить эту функцию для добавления своих данных.
    """
    # Инициализируем БД (создаем таблицы, если их нет)
    await init_db()
    print("✅ База данных инициализирована")
    
    async with async_session_maker() as session:
        # ========== СОЗДАНИЕ КАТЕГОРИЙ ВЕРХНЕГО УРОВНЯ (ГЛАВНОЕ МЕНЮ) ==========
        # Эти категории будут отображаться в главном меню бота
        
        print("\n📁 Создание категорий главного меню...")
        
        # Категория 1: Рецепты и аптечка
        category_recipes = await create_category(
            session=session,
            name="Рецепты и аптечка",
            icon_emoji="💊",
            description="Рецепты применения эфирных масел и аптечка первой помощи",
            is_main_menu=True,  # Это категория главного меню
            order_index=1  # Порядок отображения (1 = первая)
        )
        print(f"✅ Создана категория: {category_recipes.name} (ID: {category_recipes.id})")
        
        # Категория 2: Однокомпонентные масла
        category_single = await create_category(
            session=session,
            name="Однокомпонентные масла",
            icon_emoji="🌿",
            description="Описание и применение отдельных эфирных масел",
            is_main_menu=True,
            order_index=2
        )
        print(f"✅ Создана категория: {category_single.name} (ID: {category_single.id})")
        
        # Категория 3: Смеси эфирных масел
        category_blends = await create_category(
            session=session,
            name="Смеси эфирных масел",
            icon_emoji="🧪",
            description="Готовые смеси и рецепты комбинаций масел",
            is_main_menu=True,
            order_index=3
        )
        print(f"✅ Создана категория: {category_blends.name} (ID: {category_blends.id})")
        
        # Категория 4: Детская коллекция
        category_kids = await create_category(
            session=session,
            name="Детская коллекция",
            icon_emoji="👶",
            description="Безопасные рецепты и масла для детей",
            is_main_menu=True,
            order_index=4
        )
        print(f"✅ Создана категория: {category_kids.name} (ID: {category_kids.id})")
        
        # ========== СОЗДАНИЕ ПОДКАТЕГОРИЙ ==========
        # Подкатегории отображаются внутри родительской категории
        
        print("\n📂 Создание подкатегорий...")
        
        # Подкатегории для "Рецепты и аптечка"
        subcategory_first_aid = await create_category(
            session=session,
            name="Первая помощь",
            parent_id=category_recipes.id,  # Родительская категория
            icon_emoji="🚑",
            description="Рецепты для экстренных ситуаций",
            is_main_menu=False,
            order_index=1
        )
        print(f"✅ Создана подкатегория: {subcategory_first_aid.name} (ID: {subcategory_first_aid.id})")
        
        subcategory_daily = await create_category(
            session=session,
            name="Ежедневные рецепты",
            parent_id=category_recipes.id,
            icon_emoji="📅",
            description="Рецепты для повседневного использования",
            is_main_menu=False,
            order_index=2
        )
        print(f"✅ Создана подкатегория: {subcategory_daily.name} (ID: {subcategory_daily.id})")
        
        # Подкатегории для "Однокомпонентные масла"
        subcategory_common = await create_category(
            session=session,
            name="Популярные масла",
            parent_id=category_single.id,
            icon_emoji="⭐",
            description="Самые популярные и часто используемые масла",
            is_main_menu=False,
            order_index=1
        )
        print(f"✅ Создана подкатегория: {subcategory_common.name} (ID: {subcategory_common.id})")
        
        # ========== СОЗДАНИЕ КОНТЕНТА ==========
        # Контент - это конкретные материалы (статьи, рецепты и т.д.)
        
        print("\n📝 Создание контента...")
        
        # Контент для категории "Первая помощь"
        content1 = await create_content(
            session=session,
            category_id=subcategory_first_aid.id,
            title="Рецепт от головной боли",
            body=(
                "Этот рецепт поможет быстро снять головную боль:\n\n"
                "Состав:\n"
                "• Мята перечная - 2 капли\n"
                "• Лаванда - 2 капли\n"
                "• Эвкалипт - 1 капля\n\n"
                "Применение:\n"
                "Смешайте масла и нанесите на виски и затылок легкими массажными движениями.\n"
                "Избегайте попадания в глаза."
            ),
            order_index=1,
            is_published=True
        )
        print(f"✅ Создан контент: {content1.title} (ID: {content1.id})")
        
        # Контент для категории "Ежедневные рецепты"
        content2 = await create_content(
            session=session,
            category_id=subcategory_daily.id,
            title="Утренний энергетический рецепт",
            body=(
                "Начните день с бодрости и энергии:\n\n"
                "Состав:\n"
                "• Апельсин - 3 капли\n"
                "• Лимон - 2 капли\n"
                "• Розмарин - 1 капля\n\n"
                "Применение:\n"
                "Добавьте масла в диффузор утром для создания бодрящей атмосферы."
            ),
            order_index=1,
            is_published=True
        )
        print(f"✅ Создан контент: {content2.title} (ID: {content2.id})")
        
        # Контент для категории "Популярные масла"
        content3 = await create_content(
            session=session,
            category_id=subcategory_common.id,
            title="Лаванда - универсальное масло",
            body=(
                "Лаванда - одно из самых популярных и универсальных эфирных масел.\n\n"
                "Свойства:\n"
                "• Успокаивающее\n"
                "• Антисептическое\n"
                "• Регенерирующее\n\n"
                "Применение:\n"
                "Используйте для расслабления, заживления ран, улучшения сна.\n"
                "Можно наносить на кожу (разбавленным) или использовать в ароматерапии."
            ),
            order_index=1,
            is_published=True
        )
        print(f"✅ Создан контент: {content3.title} (ID: {content3.id})")
        
        # Контент напрямую в главную категорию (без подкатегории)
        content4 = await create_content(
            session=session,
            category_id=category_blends.id,
            title="Релаксирующая смесь для вечера",
            body=(
                "Создайте уютную атмосферу перед сном:\n\n"
                "Состав:\n"
                "• Лаванда - 3 капли\n"
                "• Ромашка - 2 капли\n"
                "• Иланг-иланг - 1 капля\n\n"
                "Применение:\n"
                "Используйте в диффузоре за час до сна для расслабления."
            ),
            order_index=1,
            is_published=True
        )
        print(f"✅ Создан контент: {content4.title} (ID: {content4.id})")
        
        print("\n" + "="*50)
        print("✅ Все данные успешно добавлены в базу данных!")
        print("="*50)
        print("\nТеперь вы можете запустить бота командой: python main.py")
        print("И использовать бота для просмотра добавленного контента.")


async def main():
    """
    Главная функция для запуска скрипта
    """
    try:
        await add_sample_data()
    except Exception as e:
        print(f"\n❌ Ошибка при добавлении данных: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())

