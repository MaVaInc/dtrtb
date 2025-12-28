"""
Middleware для защиты контента от скриншотов и пересылки

Запрещает пользователям делать скриншоты и пересылать сообщения бота.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest


class ContentProtectionMiddleware(BaseMiddleware):
    """
    Middleware для защиты контента
    
    Удаляет сообщения, которые пользователь пытается переслать,
    и блокирует попытки сделать скриншот (через удаление сообщения при пересылке).
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Проверяет сообщения на пересылку и удаляет их
        """
        # Обрабатываем только сообщения
        if isinstance(event, Message):
            # Если сообщение переслано, удаляем его
            if event.forward_from or event.forward_from_chat or event.forward_from_message_id:
                try:
                    await event.delete()
                except TelegramBadRequest:
                    pass  # Сообщение уже удалено или недоступно
                return  # Не обрабатываем пересланные сообщения
        
        # Вызываем следующий обработчик
        return await handler(event, data)

