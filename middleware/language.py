"""
Middleware для определения и установки языка пользователя

Этот middleware определяет язык пользователя из Telegram и устанавливает его в data.
Язык определяется из language_code пользователя Telegram:
- ru, ru-RU -> русский
- de, de-DE -> немецкий
- По умолчанию -> русский

Язык сохраняется в БД в поле language_code пользователя.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.db import async_session_maker
from database.crud import get_user_by_telegram_id
from database.models import User


def detect_language(language_code: str) -> str:
    """
    Определяет язык из language_code Telegram
    
    Args:
        language_code: Код языка из Telegram (например, "ru", "de", "ru-RU")
    
    Returns:
        "ru" или "de"
    """
    if not language_code:
        return "ru"  # По умолчанию русский
    
    lang = language_code.lower().split("-")[0]  # Берем основную часть (ru-RU -> ru)
    
    # Немецкий язык
    if lang in ["de", "deutsch"]:
        return "de"
    
    # Русский язык (по умолчанию)
    return "ru"


class LanguageMiddleware(BaseMiddleware):
    """
    Middleware для определения языка пользователя
    
    Определяет язык из Telegram language_code и сохраняет в data["user_language"].
    Также обновляет language_code в БД, если он изменился.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Определяет язык пользователя и сохраняет в data
        
        Args:
            handler: Следующий обработчик
            event: Событие
            data: Словарь данных
        
        Returns:
            Результат выполнения handler
        """
        # Получаем пользователя из события
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        
        if not user:
            # Если пользователя нет, используем русский по умолчанию
            data["user_language"] = "ru"
            return await handler(event, data)
        
        # db_user должен быть установлен AuthMiddleware (который выполняется раньше)
        db_user: User = data.get("db_user")
        
        # Используем язык из БД, если он уже установлен (включая ручную установку)
        # Иначе определяем из Telegram
        if db_user and db_user.language_code in ["ru", "de"]:
            # Используем язык из БД (может быть установлен вручную)
            data["user_language"] = db_user.language_code
        else:
            # Определяем язык из Telegram (первый запуск или язык не установлен)
            telegram_lang = user.language_code or "ru"
            detected_lang = detect_language(telegram_lang)
            data["user_language"] = detected_lang
            
            # Обновляем язык в БД только при первом запуске или если язык не установлен
            if db_user and (not db_user.language_code or db_user.language_code not in ["ru", "de"]):
                async with async_session_maker() as session:
                    db_user.language_code = detected_lang
                    await session.commit()
        
        return await handler(event, data)

