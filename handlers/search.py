"""
Обработчики поиска
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from database.db import async_session_maker
from database.crud import search_content, search_categories
from keyboards.menu import get_search_keyboard
from utils.formatters import format_search_results
from database.models import User

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()


@router.callback_query(F.data == "search_menu")
async def callback_search_menu(callback: CallbackQuery, state: FSMContext, user_language: str = "ru"):
    """
    Обработчик открытия меню поиска
    """
    # Тексты на разных языках
    if user_language == "de":
        text = (
            "🔍 <b>Suche</b>\n\n"
            "Schnellsuche nach:\n"
            "• 📁 Kategorienamen\n"
            "• 📄 Titel und Text von Inhalten\n\n"
            "Geben Sie Ihre Suchanfrage ein:"
        )
    else:  # ru
        text = (
            "🔍 <b>Поиск</b>\n\n"
            "Быстрый поиск по:\n"
            "• 📁 Названиям категорий\n"
            "• 📄 Названиям и тексту контента\n\n"
            "Введите поисковый запрос:"
        )
    
    # Редактируем существующее сообщение вместо отправки нового
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_search_keyboard(user_language),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        # Игнорируем ошибку, если сообщение не изменилось
        if "message is not modified" not in str(e):
            raise
    # Сохраняем message_id для последующего удаления
    await state.update_data(search_message_id=callback.message.message_id)
    await state.set_state(SearchStates.waiting_for_query)
    await callback.answer()


@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext, db_user: User, user_language: str = "ru"):
    """
    Обработчик поискового запроса
    """
    query = message.text.strip()
    
    if len(query) < 2:
        # Удаляем предыдущее сообщение и отправляем новое
        try:
            # Пытаемся найти и удалить предыдущее сообщение с поиском
            # Сохраняем message_id в state при открытии поиска
            search_message_id = (await state.get_data()).get("search_message_id")
            if search_message_id:
                try:
                    await message.bot.delete_message(chat_id=message.chat.id, message_id=search_message_id)
                except:
                    pass
        except:
            pass
        
        # Текст ошибки на разных языках
        if user_language == "de":
            error_text = "❌ Die Suchanfrage muss mindestens 2 Zeichen enthalten."
        else:  # ru
            error_text = "❌ Поисковый запрос должен содержать минимум 2 символа."
        
        # Отправляем новое сообщение с ошибкой
        sent_msg = await message.answer(
            error_text,
            reply_markup=get_search_keyboard(user_language)
        )
        await state.update_data(search_message_id=sent_msg.message_id)
        return
    
    async with async_session_maker() as session:
        # Ищем контент на языке пользователя (с учетом тегов)
        content_results = await search_content(session, query, limit=15, language=user_language)
        
        # Ищем категории на языке пользователя
        category_results = await search_categories(session, query, limit=10, language=user_language)
    
    # Формируем результаты
    all_results = []
    text_parts = []
    
    # Добавляем найденные категории
    if category_results:
        if user_language == "de":
            text_parts.append(f"📁 <b>Gefundene Kategorien: {len(category_results)}</b>")
        else:  # ru
            text_parts.append(f"📁 <b>Найдено категорий: {len(category_results)}</b>")
        for category in category_results:
            all_results.append({
                "type": "category",
                "id": category.id,
                "name": category.name,
                "is_main_menu": category.is_main_menu
            })
    
    # Добавляем найденный контент
    if content_results:
        if user_language == "de":
            text_parts.append(f"📄 <b>Gefundene Inhalte: {len(content_results)}</b>")
        else:  # ru
            text_parts.append(f"📄 <b>Найдено контента: {len(content_results)}</b>")
        for content in content_results:
            all_results.append({
                "type": "content",
                "id": content.id,
                "title": content.title,
                "category_name": content.category.name if content.category else None
            })
    
    # Удаляем предыдущее сообщение с поиском
    try:
        search_message_id = (await state.get_data()).get("search_message_id")
        if search_message_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=search_message_id)
            except:
                pass
    except:
        pass
    
    # Удаляем сообщение с запросом пользователя
    try:
        await message.delete()
    except:
        pass
    
    if not all_results:
        # Отправляем новое сообщение с результатами
        sent_msg = await message.answer(
            format_search_results(0, query, language=user_language),
            reply_markup=get_search_keyboard(user_language),
            parse_mode="HTML"
        )
        await state.update_data(search_message_id=sent_msg.message_id)
        await state.clear()
        return
    
    # Форматируем текст результатов
    if user_language == "de":
        text = f"🔍 <b>Suchergebnisse: «{query}»</b>\n\n"
        text += "\n".join(text_parts)
        text += "\n\nWählen Sie ein Ergebnis zur Anzeige:"
    else:  # ru
        text = f"🔍 <b>Результаты поиска: «{query}»</b>\n\n"
        text += "\n".join(text_parts)
        text += "\n\nВыберите результат для просмотра:"
    
    # Создаем клавиатуру с результатами
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = []
    
    for result in all_results[:20]:  # Ограничиваем 20 результатами
        if result["type"] == "category":
            icon = "📁"
            text_btn = f"{icon} {result['name']}"
            callback_data = f"category_{result['id']}"
        else:
            icon = "📄"
            title = result['title'][:40] + "..." if len(result['title']) > 40 else result['title']
            text_btn = f"{icon} {title}"
            callback_data = f"content_{result['id']}"
        
        keyboard.append([
            InlineKeyboardButton(text=text_btn, callback_data=callback_data)
        ])
    
    # Кнопка "Главное меню" на разных языках
    if user_language == "de":
        main_menu_text = "🏠 Hauptmenü"
    else:  # ru
        main_menu_text = "🏠 Главное меню"
    
    keyboard.append([
        InlineKeyboardButton(text=main_menu_text, callback_data="main_menu")
    ])
    
    # Отправляем новое сообщение с результатами
    sent_msg = await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await state.update_data(search_message_id=sent_msg.message_id)
    await state.clear()

