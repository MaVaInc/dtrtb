"""
Админ-панель для управления контентом бота

Этот модуль предоставляет интерактивный интерфейс для администраторов
для управления контентом бота без знания программирования.

Функционал:
- Добавление категорий (главное меню и подкатегории)
- Добавление контента (статьи, рецепты) с фото и файлами
- Редактирование категорий и контента
- Управление пользователями
- Просмотр статистики

Доступ: только для пользователей с is_admin=True
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from typing import Optional
import os

from database.db import async_session_maker
from database.crud import (
    create_category, create_content,
    get_category_by_id, get_main_menu_categories, get_category_children,
    get_content_by_id, get_content_by_category,
    update_category, update_content, delete_category, delete_content,
    get_all_categories, get_allowed_users, set_user_allowed,
    get_user_by_telegram_id, get_category_level
)
from utils.formatters import safe_edit_text
from sqlalchemy import select
from database.models import User
from keyboards.admin import (
    get_admin_menu_keyboard,
    get_categories_list_keyboard,
    get_category_edit_keyboard,
    get_content_list_keyboard,
    get_content_edit_keyboard,
    get_users_list_keyboard
)
from utils.formatters import format_category_menu, format_content_card

router = Router()


# ========== FSM СОСТОЯНИЯ ДЛЯ ДОБАВЛЕНИЯ ДАННЫХ ==========

class AddCategoryStates(StatesGroup):
    """Состояния для добавления категории"""
    waiting_for_name = State()  # Ожидание названия категории
    waiting_for_description = State()  # Ожидание описания
    waiting_for_parent = State()  # Ожидание выбора родительской категории (для подкатегорий)


class AddContentStates(StatesGroup):
    """Состояния для добавления контента"""
    waiting_for_category = State()  # Ожидание выбора категории
    waiting_for_title = State()  # Ожидание заголовка
    waiting_for_body = State()  # Ожидание текста контента
    waiting_for_photo = State()  # Ожидание фото (опционально)
    waiting_for_file = State()  # Ожидание файла (опционально)
    waiting_for_tags = State()  # Ожидание скрытых тегов для поиска


class EditCategoryStates(StatesGroup):
    """Состояния для редактирования категории"""
    waiting_for_field = State()  # Ожидание выбора поля для редактирования
    waiting_for_value = State()  # Ожидание нового значения


class EditContentStates(StatesGroup):
    """Состояния для редактирования контента"""
    waiting_for_field = State()  # Ожидание выбора поля для редактирования
    waiting_for_value = State()  # Ожидание нового значения


# ========== ПРОВЕРКА ПРАВ АДМИНА ==========

def is_admin(db_user: User) -> bool:
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        db_user: Объект пользователя из БД
    
    Returns:
        True если пользователь администратор, иначе False
    """
    return db_user.is_admin if db_user else False


# ========== ГЛАВНОЕ МЕНЮ АДМИН-ПАНЕЛИ ==========

@router.message(Command("admin"))
async def cmd_admin(message: Message, db_user: User, state: FSMContext):
    """
    Команда /admin - открывает админ-панель
    
    Доступна только администраторам.
    """
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass
    
    # Отправляем сообщение с админ-панелью
    sent_msg = await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
    # Сохраняем message_id для последующего редактирования
    await state.update_data(admin_message_id=sent_msg.message_id)


@router.callback_query(F.data == "admin_menu")
async def callback_admin_menu(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Возврат в главное меню админ-панели"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await safe_edit_text(
        callback.message,
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
    # Сохраняем message_id для последующего редактирования
    await state.update_data(admin_message_id=callback.message.message_id)
    await callback.answer()


# ========== УПРАВЛЕНИЕ КАТЕГОРИЯМИ ==========

@router.callback_query(F.data == "admin_categories")
async def callback_admin_categories(callback: CallbackQuery, db_user: User):
    """Показать список категорий для управления"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    async with async_session_maker() as session:
        categories = await get_all_categories(session)
    
    if not categories:
        await safe_edit_text(
            callback.message,
            "📁 <b>Управление категориями</b>\n\n"
            "Категорий пока нет.\n\n"
            "Создайте первую категорию!",
            reply_markup=get_categories_list_keyboard(categories, show_back=True),
            parse_mode="HTML"
        )
    else:
        text = "📁 <b>Управление категориями</b>\n\n"
        text += f"Всего категорий: {len(categories)}\n\n"
        text += "Выберите категорию для редактирования или создайте новую:"
        
        await safe_edit_text(
            callback.message,
            text,
            reply_markup=get_categories_list_keyboard(categories, show_back=True),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_category_"))
async def callback_edit_category(callback: CallbackQuery, db_user: User):
    """Редактирование категории"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    async with async_session_maker() as session:
        category = await get_category_by_id(session, category_id)
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        
        # Получаем информацию о категории
        parent_name = None
        if category.parent_id:
            parent = await get_category_by_id(session, category.parent_id)
            parent_name = parent.name if parent else None
        
        text = f"📁 <b>Категория: {category.name}</b>\n\n"
        text += f"ID: {category.id}\n"
        text += f"Тип: {'Главное меню' if category.is_main_menu else 'Подкатегория'}\n"
        if parent_name:
            text += f"Родитель: {parent_name}\n"
        text += f"Порядок: {category.order_index}\n"
        if category.description:
            text += f"\nОписание: {category.description}\n"
        
        await safe_edit_text(
            callback.message,
            text,
            reply_markup=get_category_edit_keyboard(category),
            parse_mode="HTML"
        )
    
    await callback.answer()


# ========== РЕДАКТИРОВАНИЕ КАТЕГОРИЙ ==========

@router.callback_query(F.data.startswith("edit_category_name_"))
async def callback_edit_category_name(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Начать редактирование названия категории"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await state.update_data(category_id=category_id, edit_field="name")
    await state.set_state(EditCategoryStates.waiting_for_value)
    await safe_edit_text(
        callback.message,
        "✏️ <b>Редактирование названия категории</b>\n\n"
        "Введите новое название:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_category_desc_"))
async def callback_edit_category_desc(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Начать редактирование описания категории"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await state.update_data(category_id=category_id, edit_field="description")
    await state.set_state(EditCategoryStates.waiting_for_value)
    await safe_edit_text(
        callback.message,
        "📝 <b>Редактирование описания категории</b>\n\n"
        "Введите новое описание (или отправьте /skip чтобы удалить):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_category_order_"))
async def callback_edit_category_order(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Начать редактирование порядка категории"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await state.update_data(category_id=category_id, edit_field="order_index")
    await state.set_state(EditCategoryStates.waiting_for_value)
    await safe_edit_text(
        callback.message,
        "🔢 <b>Редактирование порядка категории</b>\n\n"
        "Введите новый порядок (число, меньше = выше в списке):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_category_"))
async def callback_delete_category(callback: CallbackQuery, db_user: User):
    """Удаление категории"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    async with async_session_maker() as session:
        category = await get_category_by_id(session, category_id)
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        
        # Удаляем категорию
        deleted = await delete_category(session, category_id)
        if deleted:
            await callback.answer("✅ Категория удалена", show_alert=True)
            # Возвращаемся к списку категорий
            categories = await get_all_categories(session)
            text = "📁 <b>Управление категориями</b>\n\n"
            text += f"Всего категорий: {len(categories)}\n\n"
            text += "Выберите категорию для редактирования или создайте новую:"
            await safe_edit_text(
                callback.message,
                text,
                reply_markup=get_categories_list_keyboard(categories, show_back=True),
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.message(EditCategoryStates.waiting_for_value)
async def process_edit_category_value(message: Message, state: FSMContext, db_user: User):
    """Обработка нового значения для редактирования категории"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    data = await state.get_data()
    category_id = data["category_id"]
    edit_field = data["edit_field"]
    
    # Получаем значение
    if edit_field == "description" and message.text == "/skip":
        value = None
    elif edit_field == "order_index":
        try:
            value = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Порядок должен быть числом. Введите число:")
            return
    else:
        value = message.text.strip() if message.text else None
    
    # Обновляем категорию
    async with async_session_maker() as session:
        category = await update_category(session, category_id, **{edit_field: value})
        if category:
            await message.answer(
                f"✅ Категория обновлена!\n\n"
                f"Поле <b>{edit_field}</b> изменено.",
                parse_mode="HTML",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await message.answer("❌ Ошибка при обновлении категории")
    
    await state.clear()


@router.callback_query(F.data == "admin_add_category")
async def callback_add_category_start(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Начать процесс добавления категории"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    # Показываем все категории для выбора родителя
    # Если выбрать "Без родителя" - это будет 1 уровень (главное меню)
    async with async_session_maker() as session:
        all_categories = await get_all_categories(session)
    
    await state.set_state(AddCategoryStates.waiting_for_parent)
    await safe_edit_text(
        callback.message,
        "📁 <b>Добавление категории</b>\n\n"
        "Выберите родительскую категорию:\n"
        "• <b>Без родителя</b> - для категории 1 уровня (главное меню)\n"
        "• <b>Любая категория</b> - для категории 2 или 3 уровня",
        reply_markup=get_categories_list_keyboard(all_categories, show_back=True, select_mode=True, show_no_parent=True),
        parse_mode="HTML"
    )
    # Сохраняем message_id для последующего редактирования
    await state.update_data(admin_message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data == "select_category_none")
async def callback_select_no_parent(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Выбор "Без родителя" - создание категории 1 уровня"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await state.update_data(is_main_menu=True, parent_id=None)
    await state.set_state(AddCategoryStates.waiting_for_name)
    await safe_edit_text(
        callback.message,
        "📁 <b>Добавление категории 1 уровня</b>\n\n"
        "Эта категория будет отображаться в главном меню.\n\n"
        "Введите название категории:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_category_"))
async def callback_select_category_for_parent(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Выбор категории (может быть для родителя подкатегории или для контента)"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        category_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    # Проверяем, в каком состоянии мы находимся
    current_state = await state.get_state()
    
    if current_state == AddCategoryStates.waiting_for_parent.state:
        # Выбираем родительскую категорию для подкатегории
        async with async_session_maker() as session:
            parent_category = await get_category_by_id(session, category_id)
            if not parent_category:
                await callback.answer("❌ Категория не найдена", show_alert=True)
                return
            
            # Определяем уровень родительской категории
            parent_level = await get_category_level(session, category_id)
            
            # Уровень новой категории = уровень родителя + 1
            new_level = parent_level + 1
            
            # Максимум 3 уровень категорий (4 уровень - это контент)
            if new_level > 3:
                await callback.answer(
                    "❌ Максимальная глубина - 3 уровня категорий.\n"
                    "4 уровень - это контент (статьи, рецепты).",
                    show_alert=True
                )
                return
        
        await state.update_data(parent_id=category_id, is_main_menu=False)
        await state.set_state(AddCategoryStates.waiting_for_name)
        await safe_edit_text(
            callback.message,
            f"📁 <b>Добавление категории {new_level} уровня</b>\n\n"
            f"Родитель: <b>{parent_category.name}</b> (уровень {parent_level})\n\n"
            f"Введите название категории:",
            parse_mode="HTML"
        )
    elif current_state == AddContentStates.waiting_for_category.state:
        # Выбираем категорию для контента
        async with async_session_maker() as session:
            category = await get_category_by_id(session, category_id)
            if not category:
                await callback.answer("❌ Категория не найдена", show_alert=True)
                return
        
        await state.update_data(category_id=category_id)
        await state.set_state(AddContentStates.waiting_for_title)
        await safe_edit_text(
            callback.message,
            f"📝 <b>Добавление контента</b>\n\n"
            f"Категория: <b>{category.name}</b>\n\n"
            f"Введите заголовок контента:",
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.message(AddCategoryStates.waiting_for_name)
async def process_category_name(message: Message, state: FSMContext, db_user: User):
    """Обработка названия категории"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    category_name = message.text.strip()
    if not category_name:
        # Удаляем сообщение пользователя и редактируем последнее сообщение бота
        try:
            await message.delete()
        except:
            pass
        data = await state.get_data()
        admin_message_id = data.get("admin_message_id")
        if admin_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=admin_message_id,
                    text="❌ Название не может быть пустым. Введите название:",
                    parse_mode="HTML"
                )
            except:
                pass
        return
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    await state.update_data(name=category_name)
    await state.set_state(AddCategoryStates.waiting_for_description)
    
    # Редактируем последнее сообщение бота
    data = await state.get_data()
    admin_message_id = data.get("admin_message_id")
    if admin_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=admin_message_id,
                text=f"✅ Название: <b>{category_name}</b>\n\n"
                     "💡 <i>Совет: если хотите добавить эмодзи, включите его в название категории</i>\n\n"
                     "Введите описание категории:\n"
                     "Или отправьте /skip чтобы пропустить",
                parse_mode="HTML"
            )
        except:
            # Если не удалось отредактировать, отправляем новое
            sent_msg = await message.answer(
                f"✅ Название: <b>{category_name}</b>\n\n"
                "💡 <i>Совет: если хотите добавить эмодзи, включите его в название категории</i>\n\n"
                "Введите описание категории:\n"
                "Или отправьте /skip чтобы пропустить",
                parse_mode="HTML"
            )
            await state.update_data(admin_message_id=sent_msg.message_id)
    else:
        # Если нет сохраненного сообщения, отправляем новое
        sent_msg = await message.answer(
            f"✅ Название: <b>{category_name}</b>\n\n"
            "💡 <i>Совет: если хотите добавить эмодзи, включите его в название категории</i>\n\n"
            "Введите описание категории:\n"
            "Или отправьте /skip чтобы пропустить",
            parse_mode="HTML"
        )
        await state.update_data(admin_message_id=sent_msg.message_id)


@router.message(AddCategoryStates.waiting_for_description)
async def process_category_description(message: Message, state: FSMContext, db_user: User):
    """Обработка описания категории и создание категории"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    description = message.text.strip() if message.text != "/skip" else None
    data = await state.get_data()
    
    # Получаем порядок для новой категории
    async with async_session_maker() as session:
        if data.get("is_main_menu"):
            # Для главного меню - считаем существующие
            existing = await get_main_menu_categories(session)
            order_index = len(existing) + 1
        else:
            # Для подкатегорий - считаем в родительской категории
            existing = await get_category_children(session, data.get("parent_id"))
            order_index = len(existing) + 1
        
        # Создаем категорию на русском языке
        # Автоматически создастся связанная категория на немецком
        category = await create_category(
            session=session,
            name=data["name"],
            parent_id=data.get("parent_id"),
            icon_emoji=None,  # Не сохраняем эмодзи отдельно
            description=description,
            language="ru",  # Создаем на русском
            auto_create_linked=True,  # Автоматически создаст связанную на немецком
            is_main_menu=data.get("is_main_menu", False),
            order_index=order_index
        )
    
    # Получаем информацию о связанной категории
    linked_category_name = None
    async with async_session_maker() as session:
        # Обновляем категорию из БД, чтобы получить linked_category_id
        category = await get_category_by_id(session, category.id)
        if category and category.linked_category_id:
            linked_category = await get_category_by_id(session, category.linked_category_id)
            if linked_category:
                linked_category_name = linked_category.name
    
    # Формируем сообщение
    message_text = f"✅ <b>Категория создана!</b>\n\n"
    message_text += f"Название: {category.name}\n"
    message_text += f"ID: {category.id}\n"
    message_text += f"Тип: {'Главное меню' if category.is_main_menu else 'Подкатегория'}\n\n"
    if linked_category_name:
        message_text += f"🌍 Автоматически создана связанная категория на немецком:\n"
        message_text += f"   <b>{linked_category_name}</b>\n\n"
    message_text += f"Категория добавлена в бота и будет отображаться пользователям."
    
    # Редактируем последнее сообщение бота
    admin_message_id = data.get("admin_message_id")
    if admin_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=admin_message_id,
                text=message_text,
                parse_mode="HTML",
                reply_markup=get_admin_menu_keyboard()
            )
        except:
            # Если не удалось отредактировать, отправляем новое
            sent_msg = await message.answer(
                message_text,
                parse_mode="HTML",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.update_data(admin_message_id=sent_msg.message_id)
    else:
        # Если нет сохраненного сообщения, отправляем новое
        sent_msg = await message.answer(
            message_text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.update_data(admin_message_id=sent_msg.message_id)
    
    await state.clear()


# ========== УПРАВЛЕНИЕ КОНТЕНТОМ ==========

@router.callback_query(F.data == "admin_content")
async def callback_admin_content(callback: CallbackQuery, db_user: User):
    """Показать управление контентом"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    # Получаем весь контент для отображения
    async with async_session_maker() as session:
        from sqlalchemy import select
        from database.models import Content
        result = await session.execute(
            select(Content)
            .order_by(Content.created_at.desc())
            .limit(30)
        )
        all_contents = list(result.scalars().all())
    
    if not all_contents:
        text = "📝 <b>Управление контентом</b>\n\n"
        text += "Контента пока нет.\n\n"
        text += "Создайте первый контент!"
    else:
        text = "📝 <b>Управление контентом</b>\n\n"
        text += f"Всего контента: {len(all_contents)}\n\n"
        text += "Выберите контент для редактирования или создайте новый:"
    
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=get_content_list_keyboard(all_contents, show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_content")
async def callback_add_content_start(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Начать процесс добавления контента"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    async with async_session_maker() as session:
        categories = await get_all_categories(session)
    
    await state.set_state(AddContentStates.waiting_for_category)
    await safe_edit_text(
        callback.message,
        "📝 <b>Добавление контента</b>\n\n"
        "Выберите категорию, в которую добавить контент:",
        reply_markup=get_categories_list_keyboard(categories, show_back=True, select_mode=True),
        parse_mode="HTML"
    )
    await callback.answer()




@router.message(AddContentStates.waiting_for_title)
async def process_content_title(message: Message, state: FSMContext, db_user: User):
    """Обработка заголовка контента"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    title = message.text.strip()
    if not title:
        await message.answer("❌ Заголовок не может быть пустым. Введите заголовок:")
        return
    
    await state.update_data(title=title)
    await state.set_state(AddContentStates.waiting_for_body)
    await message.answer(
        f"✅ Заголовок: <b>{title}</b>\n\n"
        "Введите текст контента (статья, рецепт и т.д.):\n"
        "Или отправьте /skip чтобы пропустить",
        parse_mode="HTML"
    )


@router.message(AddContentStates.waiting_for_body)
async def process_content_body(message: Message, state: FSMContext, db_user: User):
    """Обработка текста контента"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    body = message.text.strip() if message.text != "/skip" else None
    await state.update_data(body=body)
    await state.set_state(AddContentStates.waiting_for_photo)
    await message.answer(
        f"✅ Текст сохранен\n\n"
        "Отправьте фото для контента (или отправьте /skip чтобы пропустить):"
    )


@router.message(AddContentStates.waiting_for_photo, F.photo)
async def process_content_photo(message: Message, state: FSMContext, db_user: User):
    """Обработка фото контента"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Получаем файл фото
    photo = message.photo[-1]  # Берем фото наибольшего размера
    file_info = await message.bot.get_file(photo.file_id)
    
    # Сохраняем file_id (Telegram хранит файлы, можно использовать file_id напрямую)
    # Или можно скачать и сохранить локально
    await state.update_data(photo_file_id=photo.file_id)
    await state.set_state(AddContentStates.waiting_for_file)
    await message.answer(
        "✅ Фото сохранено\n\n"
        "Отправьте файл/документ для контента (или отправьте /skip чтобы пропустить):"
    )


@router.message(AddContentStates.waiting_for_photo)
async def process_content_photo_skip(message: Message, state: FSMContext, db_user: User):
    """Пропуск фото"""
    if message.text == "/skip":
        await state.update_data(photo_file_id=None)
        await state.set_state(AddContentStates.waiting_for_file)
        await message.answer(
            "Фото пропущено\n\n"
            "Отправьте файл/документ для контента (или отправьте /skip чтобы пропустить):"
        )


@router.message(AddContentStates.waiting_for_file, F.document)
async def process_content_file(message: Message, state: FSMContext, db_user: User):
    """Обработка файла контента и создание контента"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Получаем файл
    document = message.document
    file_info = await message.bot.get_file(document.file_id)
    
    await state.update_data(file_file_id=document.file_id)
    await state.set_state(AddContentStates.waiting_for_tags)
    await message.answer(
        "✅ Файл сохранен\n\n"
        "💡 <b>Скрытые теги для поиска</b>\n\n"
        "Введите ключевые слова через запятую для улучшения поиска.\n"
        "Например: головная боль, мигрень, масло, рецепт\n\n"
        "Эти теги не видны пользователям, но помогают находить контент.\n"
        "Можно указать теги на обоих языках (ru и de).\n\n"
        "Отправьте /skip чтобы пропустить:",
        parse_mode="HTML"
    )


@router.message(AddContentStates.waiting_for_file)
async def process_content_file_skip(message: Message, state: FSMContext, db_user: User):
    """Пропуск файла"""
    if message.text == "/skip":
        await state.update_data(file_file_id=None)
        await state.set_state(AddContentStates.waiting_for_tags)
        await message.answer(
            "💡 <b>Скрытые теги для поиска</b>\n\n"
            "Введите ключевые слова через запятую для улучшения поиска.\n"
            "Например: головная боль, мигрень, масло, рецепт\n\n"
            "Эти теги не видны пользователям, но помогают находить контент.\n"
            "Можно указать теги на обоих языках (ru и de).\n\n"
            "Отправьте /skip чтобы пропустить:",
            parse_mode="HTML"
        )


@router.message(AddContentStates.waiting_for_tags)
async def process_content_tags(message: Message, state: FSMContext, db_user: User):
    """Обработка тегов и создание контента"""
    if not is_admin(db_user):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    search_tags = message.text.strip() if message.text != "/skip" else None
    await state.update_data(search_tags=search_tags)
    await _create_content_from_state(message, state, db_user)


async def _create_content_from_state(message: Message, state: FSMContext, db_user: User):
    """Создание контента из данных состояния"""
    data = await state.get_data()
    
    async with async_session_maker() as session:
        # Получаем порядок для нового контента (без фильтра по языку для админ-панели)
        existing = await get_content_by_category(session, data["category_id"], only_published=False, language="ru")
        order_index = len(existing) + 1
        
        # Создаем контент на русском языке
        # Для фото и файлов используем file_id (Telegram хранит файлы)
        # В реальном проекте можно скачать файлы и сохранить локально или в облако
        content = await create_content(
            session=session,
            category_id=data["category_id"],
            title=data["title"],
            body=data.get("body"),
            image_url=data.get("photo_file_id"),  # Используем file_id как URL
            file_url=data.get("file_file_id"),    # Используем file_id как URL
            order_index=order_index,
            is_published=True,
            language="ru",  # Создаем на русском (немецкую версию админ добавит отдельно)
            search_tags=data.get("search_tags")  # Скрытые теги для поиска
        )
        
        category = await get_category_by_id(session, data["category_id"])
    
    await state.clear()
    
    text = f"✅ <b>Контент создан!</b>\n\n"
    text += f"Заголовок: {content.title}\n"
    text += f"ID: {content.id}\n"
    text += f"Категория: {category.name}\n"
    if data.get("photo_file_id"):
        text += "📷 Фото: добавлено\n"
    if data.get("file_file_id"):
        text += "📎 Файл: добавлен\n"
    text += "\nКонтент добавлен в бота и будет отображаться пользователям."
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )


# ========== РЕДАКТИРОВАНИЕ КОНТЕНТА ==========

@router.callback_query(F.data.startswith("admin_edit_content_"))
async def callback_edit_content(callback: CallbackQuery, db_user: User):
    """Редактирование контента"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        content_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    async with async_session_maker() as session:
        content = await get_content_by_id(session, content_id)
        if not content:
            await callback.answer("❌ Контент не найден", show_alert=True)
            return
        
        category = content.category
        
        text = f"📝 <b>Контент: {content.title}</b>\n\n"
        text += f"ID: {content.id}\n"
        text += f"Категория: {category.name if category else 'Не указана'}\n"
        text += f"Порядок: {content.order_index}\n"
        text += f"Опубликован: {'✅ Да' if content.is_published else '❌ Нет'}\n"
        if content.body:
            body_preview = content.body[:100] + "..." if len(content.body) > 100 else content.body
            text += f"\nТекст: {body_preview}\n"
        if content.image_url:
            text += "📷 Фото: есть\n"
        if content.file_url:
            text += "📎 Файл: есть\n"
        
        await safe_edit_text(
            callback.message,
            text,
            reply_markup=get_content_edit_keyboard(content),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("delete_content_"))
async def callback_delete_content(callback: CallbackQuery, db_user: User):
    """Удаление контента"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        content_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    async with async_session_maker() as session:
        content = await get_content_by_id(session, content_id)
        if not content:
            await callback.answer("❌ Контент не найден", show_alert=True)
            return
        
        deleted = await delete_content(session, content_id)
        if deleted:
            await callback.answer("✅ Контент удален", show_alert=True)
            # Возвращаемся к списку контента
            from sqlalchemy import select
            from database.models import Content
            result = await session.execute(
                select(Content)
                .order_by(Content.created_at.desc())
                .limit(30)
            )
            all_contents = list(result.scalars().all())
            
            text = "📝 <b>Управление контентом</b>\n\n"
            text += f"Всего контента: {len(all_contents)}\n\n"
            text += "Выберите контент для редактирования или создайте новый:"
            
            await safe_edit_text(
                callback.message,
                text,
                reply_markup=get_content_list_keyboard(all_contents, show_back=True),
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.callback_query(F.data.startswith("view_content_"))
async def callback_view_content(callback: CallbackQuery, db_user: User):
    """Просмотр контента (как пользователь)"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        content_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    # Перенаправляем на обычный обработчик просмотра контента
    callback.data = f"content_{content_id}"
    # Импортируем обработчик из content.py
    from handlers.content import callback_content
    await callback_content(callback, db_user)


# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========

@router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery, db_user: User):
    """Показать список пользователей"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    async with async_session_maker() as session:
        users = await get_allowed_users(session)
        all_users = await session.execute(select(User))
        all_users_list = list(all_users.scalars().all())
    
    # Считаем админов
    admins_count = sum(1 for u in all_users_list if u.is_admin)
    
    text = "👥 <b>Управление пользователями</b>\n\n"
    text += f"Всего пользователей: {len(all_users_list)}\n"
    text += f"Администраторов: {admins_count}\n\n"
    text += "Выберите пользователя для управления:"
    
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=get_users_list_keyboard(all_users_list, show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_user_"))
async def callback_toggle_user(callback: CallbackQuery, db_user: User):
    """Назначить/снять права администратора пользователю"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        telegram_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Нельзя снять права администратора у самого себя
        if user.telegram_id == db_user.telegram_id:
            await callback.answer("❌ Вы не можете снять права администратора у самого себя", show_alert=True)
            return
        
        # Переключаем права администратора
        from database.crud import set_user_admin
        new_status = not user.is_admin
        await set_user_admin(session, telegram_id, new_status)
        
        status_text = "✅ Права администратора назначены" if new_status else "❌ Права администратора сняты"
        await callback.answer(status_text, show_alert=True)
        
        # Обновляем список
        all_users = await session.execute(select(User))
        all_users_list = list(all_users.scalars().all())
        
        # Считаем админов
        admins_count = sum(1 for u in all_users_list if u.is_admin)
        
        text = "👥 <b>Управление пользователями</b>\n\n"
        text += f"Всего пользователей: {len(all_users_list)}\n"
        text += f"Администраторов: {admins_count}\n\n"
        text += "Выберите пользователя для управления:"
        
        await safe_edit_text(
            callback.message,
            text,
            reply_markup=get_users_list_keyboard(all_users_list, show_back=True),
            parse_mode="HTML"
        )


# ========== СТАТИСТИКА ==========

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery, db_user: User):
    """Показать статистику бота"""
    if not is_admin(db_user):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    from database.crud import get_popular_content
    from sqlalchemy import func, select
    from database.models import Analytics, Content, Category, User
    
    async with async_session_maker() as session:
        # Общая статистика
        total_users = await session.execute(select(func.count(User.id)))
        total_users = total_users.scalar() or 0
        
        allowed_users = await get_allowed_users(session)
        
        total_categories = await session.execute(select(func.count(Category.id)))
        total_categories = total_categories.scalar() or 0
        
        total_content = await session.execute(select(func.count(Content.id)))
        total_content = total_content.scalar() or 0
        
        total_views = await session.execute(
            select(func.count(Analytics.id)).where(Analytics.action == 'view')
        )
        total_views = total_views.scalar() or 0
        
        # Популярный контент
        popular = await get_popular_content(session, limit=5)
    
    text = "📊 <b>Статистика бота</b>\n\n"
    text += f"👥 <b>Пользователи:</b>\n"
    text += f"   Всего: {total_users}\n"
    text += f"   С доступом: {len(allowed_users)}\n\n"
    text += f"📁 <b>Контент:</b>\n"
    text += f"   Категорий: {total_categories}\n"
    text += f"   Материалов: {total_content}\n\n"
    text += f"👀 <b>Активность:</b>\n"
    text += f"   Просмотров: {total_views}\n\n"
    
    if popular:
        text += "🔥 <b>Популярный контент:</b>\n"
        for i, content in enumerate(popular, 1):
            text += f"   {i}. {content.title[:40]}...\n"
    
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

