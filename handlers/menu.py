"""
Обработчики меню и навигации

Этот модуль обрабатывает навигацию по категориям:
1. Возврат в главное меню (кнопка "Главное меню")
2. Выбор категории (нажатие на кнопку категории)

Обработчики работают с callback_query - это нажатия на inline кнопки.
Callback data имеет формат: "category_<id>" для категорий.
"""
from aiogram import Router, F  # F - фильтры для callback data
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from database.db import async_session_maker
from database.crud import (
    get_category_by_id,
    get_category_children,
    get_content_by_category,
    get_main_menu_categories,
    set_user_language
)
from keyboards.menu import get_main_menu_keyboard, get_category_keyboard
from utils.formatters import format_category_menu, format_breadcrumbs, format_welcome_message
from database.models import User

# Создаем роутер для этого модуля
router = Router()


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик возврата в главное меню
    
    Вызывается, когда пользователь нажимает кнопку "Главное меню".
    
    Args:
        callback: Объект callback query (нажатие на кнопку)
        db_user: Объект пользователя из БД
    
    Что делает:
        1. Получает категории главного меню
        2. Форматирует приветственное сообщение
        3. Обновляет сообщение, показывая главное меню
    
    ВАЖНО: Используется edit_text вместо answer, чтобы обновить существующее
    сообщение, а не отправлять новое.
    """
    # Получаем категории главного меню из БД на языке пользователя
    async with async_session_maker() as session:
        categories = await get_main_menu_categories(session, language=user_language)
    
    # Форматируем приветственное сообщение на языке пользователя
    welcome_text = format_welcome_message(
        db_user.first_name or db_user.username,
        language=user_language
    )
    
    # Обновляем сообщение, показывая главное меню
    # edit_text изменяет существующее сообщение (не отправляет новое)
    try:
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(categories, is_admin=db_user.is_admin, language=user_language),  # Клавиатура с категориями
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        # Игнорируем ошибку, если сообщение не изменилось (пользователь нажал на ту же кнопку)
        if "message is not modified" not in str(e):
            raise  # Если другая ошибка - пробрасываем дальше
    
    # Отвечаем на callback, чтобы убрать индикатор загрузки на кнопке
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def callback_category(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик выбора категории
    
    Вызывается, когда пользователь нажимает на кнопку категории.
    Callback data имеет формат: "category_<id>", где <id> - ID категории.
    
    Args:
        callback: Объект callback query
        db_user: Объект пользователя из БД
    
    Что делает:
        1. Извлекает ID категории из callback data
        2. Получает категорию из БД
        3. Получает подкатегории и контент этой категории
        4. Форматирует сообщение с информацией о категории
        5. Создает клавиатуру с подкатегориями и контентом
        6. Обновляет сообщение
    
    Пример callback data: "category_5" - открыть категорию с ID=5
    """
    # Извлекаем ID категории из callback data
    # Формат: "category_<id>"
    try:
        # Разделяем строку по "_" и берем второй элемент (индекс 1)
        # "category_5" -> ["category", "5"] -> "5" -> 5
        category_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        # Если формат неверный, показываем ошибку
        await callback.answer("❌ Ошибка: неверный ID категории", show_alert=True)
        return
    
    # Получаем категорию из БД
    async with async_session_maker() as session:
        category = await get_category_by_id(session, category_id)
        
        # Проверяем, существует ли категория
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        
        # Получаем подкатегории (дочерние категории) на языке пользователя
        # Подкатегории - это категории, у которых parent_id = category_id
        children = await get_category_children(session, category_id, language=user_language)
        
        # Получаем контент этой категории на языке пользователя
        # Контент - это материалы (статьи, рецепты), принадлежащие категории
        contents = await get_content_by_category(session, category_id, language=user_language)
        
        # Форматируем сообщение с информацией о категории
        # Включает название, описание и эмодзи категории
        text = format_category_menu(
            category.name,
            category.description,
            category.icon_emoji,
            language=user_language
        )
        
        # Создаем клавиатуру с подкатегориями и контентом
        # parent_id нужен для кнопки "Назад" (если есть родительская категория)
        # show_back=True показывает кнопку "Назад" или "Главное меню"
        keyboard = get_category_keyboard(
            children,           # Подкатегории (кнопки для перехода в подкатегории)
            contents,           # Контент (кнопки для просмотра материалов)
            parent_id=category.parent_id,  # ID родительской категории (для кнопки "Назад")
            show_back=True,     # Показывать кнопку "Назад"
            language=user_language  # Язык интерфейса
        )
        
        # Обновляем сообщение, показывая содержимое категории
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            # Игнорируем ошибку, если сообщение не изменилось
            if "message is not modified" not in str(e):
                raise  # Если другая ошибка - пробрасываем дальше
        
        # Отвечаем на callback
        await callback.answer()


@router.callback_query(F.data == "toggle_language")
async def callback_toggle_language(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик переключения языка
    
    Переключает язык пользователя между русским и немецким.
    После переключения обновляет главное меню на новом языке.
    """
    # Определяем новый язык (переключаем ru <-> de)
    new_language = "de" if user_language == "ru" else "ru"
    
    # Обновляем язык в БД
    async with async_session_maker() as session:
        await set_user_language(session, db_user.telegram_id, new_language)
        # Обновляем объект пользователя в памяти
        db_user.language_code = new_language
        
        # Получаем категории главного меню на новом языке
        categories = await get_main_menu_categories(session, language=new_language)
    
    # Форматируем приветственное сообщение на новом языке
    welcome_text = format_welcome_message(
        db_user.first_name or db_user.username,
        language=new_language
    )
    
    # Обновляем сообщение с новым языком
    try:
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(categories, is_admin=db_user.is_admin, language=new_language),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    # Показываем уведомление о смене языка
    lang_text = "Deutsch" if new_language == "de" else "Русский"
    await callback.answer(f"🌐 Язык изменен на {lang_text}", show_alert=False)
