"""
Middleware для сбора аналитики
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.db import async_session_maker
from database.crud import add_analytics, get_user_by_telegram_id


class AnalyticsMiddleware(BaseMiddleware):
    """Middleware для сбора статистики использования бота"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Выполняем handler
        result = await handler(event, data)

        # Собираем аналитику после выполнения handler
        try:
            user_id = None
            content_id = None
            action = None

            if isinstance(event, Message):
                user_id = event.from_user.id if event.from_user else None
                # Определяем действие по команде или тексту
                if event.text:
                    if event.text.startswith("/"):
                        action = "command"
                    else:
                        action = "message"
                elif event.photo:
                    action = "photo"
                elif event.document:
                    action = "document"

            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id if event.from_user else None
                # Парсим callback_data для определения действия
                callback_data = event.data
                if callback_data:
                    if callback_data.startswith("category_"):
                        action = "category_view"
                    elif callback_data.startswith("content_"):
                        action = "content_view"
                        # Пытаемся извлечь content_id из callback_data
                        try:
                            parts = callback_data.split("_")
                            if len(parts) > 1:
                                content_id = int(parts[1])
                        except (ValueError, IndexError):
                            pass
                    elif callback_data.startswith("search_"):
                        action = "search"
                    elif callback_data.startswith("favorite_"):
                        action = "favorite_toggle"

            # Сохраняем аналитику
            if action and user_id:
                async with async_session_maker() as session:
                    db_user = await get_user_by_telegram_id(session, user_id)
                    user_db_id = db_user.id if db_user else None
                    await add_analytics(
                        session=session,
                        action=action,
                        user_id=user_db_id,
                        content_id=content_id
                    )

        except Exception as e:
            # Не прерываем работу бота из-за ошибок аналитики
            print(f"Analytics error: {e}")

        return result

