"""
Крутые фишки и вау-эффекты для Telegram бота

Этот модуль содержит продвинутые функции для улучшения UX:
- Inline режим поиска
- Кнопки с действиями (share, open_url)
- Медиа группы
- Прогресс-бары
- Эмодзи реакции
- Web App интеграция
"""
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, InputMediaDocument, BotCommand
)
from aiogram.filters import Command
from typing import List, Optional
import asyncio

from database.db import async_session_maker
from database.crud import search_content, get_content_by_id
from database.models import User, Content

router = Router()


# ========== INLINE РЕЖИМ ПОИСКА ==========

@router.inline_query()
async def inline_search(inline_query):
    """
    Inline режим поиска - позволяет искать контент прямо из любого чата
    
    Использование: @your_bot_name запрос
    """
    query = inline_query.query.strip()
    
    if not query or len(query) < 2:
        # Показываем популярный контент если запрос пустой
        await inline_query.answer(
            results=[],
            switch_pm_text="🔍 Введите запрос для поиска",
            switch_pm_parameter="search"
        )
        return
    
    async with async_session_maker() as session:
        # Ищем контент
        results_list = await search_content(session, query, limit=10)
    
    # Формируем результаты для inline режима
    results = []
    for i, content in enumerate(results_list[:10]):
        # Создаем результат для inline режима
        result = {
            "type": "article",
            "id": str(content.id),
            "title": content.title[:64],  # Максимум 64 символа
            "description": (content.body or "")[:128] if content.body else "Контент из бота",
            "message_text": f"📄 <b>{content.title}</b>\n\n{content.body or ''}",
            "parse_mode": "HTML",
            "reply_markup": InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Открыть в боте", url=f"https://t.me/{inline_query.bot.username}?start=content_{content.id}")]
            ])
        }
        results.append(result)
    
    await inline_query.answer(results=results, cache_time=60)


# ========== КНОПКИ С ДЕЙСТВИЯМИ ==========

def get_share_keyboard(content_id: int, content_title: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой "Поделиться"
    
    Args:
        content_id: ID контента
        content_title: Название контента для шаринга
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Поделиться",
                switch_inline_query=f"📄 {content_title}"
            ),
            InlineKeyboardButton(
                text="⭐ В избранное",
                callback_data=f"toggle_favorite_{content_id}"
            )
        ]
    ])


def get_web_app_keyboard(url: str, text: str = "🌐 Открыть") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с Web App кнопкой
    
    Args:
        url: URL веб-приложения
        text: Текст кнопки
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, web_app={"url": url})]
    ])


# ========== МЕДИА ГРУППЫ ==========

async def send_media_group(bot, chat_id: int, content: Content):
    """
    Отправляет медиа группу (несколько фото/видео одним сообщением)
    
    Args:
        bot: Объект бота
        chat_id: ID чата
        content: Объект контента
    """
    media = []
    
    # Если есть фото
    if content.image_url:
        # В реальном проекте нужно скачать файл или использовать file_id
        # Здесь упрощенный пример
        media.append(InputMediaPhoto(media=content.image_url, caption=content.title))
    
    # Если есть файл
    if content.file_url:
        media.append(InputMediaDocument(media=content.file_url))
    
    if media:
        await bot.send_media_group(chat_id=chat_id, media=media)


# ========== ПРОГРЕСС-БАР ==========

async def show_progress(message: Message, text: str, progress: float):
    """
    Показывает прогресс-бар через редактирование сообщения
    
    Args:
        message: Сообщение для редактирования
        text: Текст прогресса
        progress: Прогресс от 0.0 до 1.0
    """
    bar_length = 20
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    percent = int(progress * 100)
    
    progress_text = f"{text}\n\n[{bar}] {percent}%"
    
    try:
        await message.edit_text(progress_text)
    except:
        pass  # Игнорируем ошибки редактирования


# ========== ЭМОДЗИ РЕАКЦИИ ==========

@router.callback_query(F.data.startswith("react_"))
async def callback_emoji_reaction(callback: CallbackQuery, db_user: User):
    """
    Обработка эмодзи реакций на контент
    
    Использование: callback_data="react_<content_id>_<emoji>"
    """
    try:
        parts = callback.data.split("_")
        content_id = int(parts[1])
        emoji = parts[2] if len(parts) > 2 else "👍"
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    # Здесь можно сохранить реакцию в БД для аналитики
    # Пока просто показываем уведомление
    await callback.answer(f"{emoji} Реакция добавлена!", show_alert=False)


def get_reactions_keyboard(content_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с эмодзи реакциями
    
    Args:
        content_id: ID контента
    """
    reactions = ["👍", "❤️", "🔥", "👏", "🎉"]
    buttons = []
    
    for emoji in reactions:
        buttons.append(
            InlineKeyboardButton(
                text=emoji,
                callback_data=f"react_{content_id}_{emoji}"
            )
        )
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


# ========== КОМАНДЫ БОТА ==========

async def set_bot_commands(bot):
    """
    Устанавливает команды бота для быстрого доступа
    
    Args:
        bot: Объект бота
    """
    commands = [
        BotCommand(command="start", description="🚀 Начать работу с ботом"),
        BotCommand(command="search", description="🔍 Поиск контента"),
        BotCommand(command="favorites", description="⭐ Избранное"),
        # Команда /admin убрана из меню для безопасности
    ]
    
    await bot.set_my_commands(commands)


# ========== УМНЫЕ УВЕДОМЛЕНИЯ ==========

async def send_smart_notification(bot, chat_id: int, text: str, 
                                 notification_type: str = "info"):
    """
    Отправляет умное уведомление с эмодзи и форматированием
    
    Args:
        bot: Объект бота
        chat_id: ID чата
        text: Текст уведомления
        notification_type: Тип (info, success, warning, error)
    """
    emojis = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    emoji = emojis.get(notification_type, "ℹ️")
    formatted_text = f"{emoji} {text}"
    
    await bot.send_message(chat_id=chat_id, text=formatted_text)


# ========== КНОПКИ С URL ==========

def get_url_keyboard(url: str, text: str = "🔗 Открыть ссылку") -> InlineKeyboardMarkup:
    """
    Создает кнопку с URL
    
    Args:
        url: URL для открытия
        text: Текст кнопки
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, url=url)]
    ])

