"""
Middleware для проверки доступа пользователей

Этот модуль содержит два middleware:
1. AuthMiddleware - создает/обновляет пользователя в БД
2. AccessMiddleware - проверяет права доступа пользователя

Middleware выполняются ДО обработчиков и обрабатывают ВСЕ сообщения и callback'и.

ВАЖНО: Порядок регистрации middleware имеет значение!
AuthMiddleware должен быть зарегистрирован ПЕРЕД AccessMiddleware.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.db import async_session_maker
from database.crud import (
    get_user_by_telegram_id, create_user, update_user_last_active,
    is_external_id_allowed, link_external_id_to_user, is_external_id_used
)
from database.models import User


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для аутентификации пользователей
    
    Этот middleware выполняется ПЕРВЫМ для каждого сообщения/callback.
    Он отвечает за:
    1. Создание пользователя в БД при первом обращении
    2. Обновление информации о пользователе (имя, username)
    3. Обновление времени последней активности
    4. Передачу объекта db_user в обработчики через data["db_user"]
    
    Как работает:
        - Получает пользователя из события (message.from_user или callback.from_user)
        - Ищет пользователя в БД по telegram_id
        - Если не найден - создает нового (с is_allowed=False)
        - Если найден - обновляет информацию
        - Сохраняет объект db_user в data для использования в handlers
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Метод, который вызывается для каждого события
        
        Args:
            handler: Следующий обработчик в цепочке
            event: Событие (Message, CallbackQuery и т.д.)
            data: Словарь с данными, передаваемыми между middleware и handlers
        
        Returns:
            Результат выполнения handler
        """
        # Получаем пользователя из события
        # Пользователь может быть в Message или CallbackQuery
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user  # from_user - объект пользователя из Telegram

        # Если пользователя нет (например, для других типов событий), пропускаем
        if not user:
            return await handler(event, data)

        # Получаем или создаем пользователя в БД
        async with async_session_maker() as session:
            # Ищем пользователя в БД по Telegram ID
            db_user = await get_user_by_telegram_id(session, user.id)

            if not db_user:
                # Пользователь не найден - создаем нового
                # Это первое обращение пользователя к боту
                db_user = await create_user(
                    session=session,
                    telegram_id=user.id,           # Telegram ID пользователя
                    username=user.username,         # Имя пользователя в Telegram
                    first_name=user.first_name,     # Имя пользователя
                    is_allowed=False                # По умолчанию НЕТ доступа
                    # Администратор должен дать доступ вручную через set_user_allowed()
                )
            else:
                # Пользователь найден - обновляем информацию
                # Пользователь мог изменить имя или username в Telegram
                updated = False
                if db_user.username != user.username:
                    db_user.username = user.username
                    updated = True
                if db_user.first_name != user.first_name:
                    db_user.first_name = user.first_name
                    updated = True
                
                # Сохраняем изменения, если они были
                if updated:
                    await session.commit()

            # Обновляем время последней активности пользователя
            # Это нужно для аналитики - знать, когда пользователь был активен
            await update_user_last_active(session, db_user.id)

            # Сохраняем объект пользователя в data
            # Это позволяет handlers получать db_user как параметр
            # Например: async def handler(message: Message, db_user: User)
            data["db_user"] = db_user

        # Вызываем следующий обработчик в цепочке
        return await handler(event, data)


class AccessMiddleware(BaseMiddleware):
    """
    Middleware для проверки whitelist доступа
    
    Этот middleware выполняется ПОСЛЕ AuthMiddleware.
    Он проверяет, имеет ли пользователь доступ к боту.
    
    Как работает:
        - Получает db_user из data (должен быть установлен AuthMiddleware)
        - Проверяет флаг is_allowed
        - Если is_allowed=False - блокирует доступ и отправляет сообщение
        - Если is_allowed=True - пропускает дальше к handlers
    
    ВАЖНО: Администраторы (is_admin=True) имеют полный доступ независимо от is_allowed.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Метод, который вызывается для каждого события
        
        Args:
            handler: Следующий обработчик в цепочке
            event: Событие (Message, CallbackQuery и т.д.)
            data: Словарь с данными (должен содержать db_user от AuthMiddleware)
        
        Returns:
            Результат выполнения handler или None (если доступ запрещен)
        """
        # Получаем пользователя из data
        # db_user должен быть установлен AuthMiddleware (который выполняется первым)
        db_user: User = data.get("db_user")

        # Если пользователя нет, пропускаем (на всякий случай)
        if not db_user:
            return await handler(event, data)

        # Админы имеют полный доступ независимо от is_allowed
        # Это позволяет админам использовать бота даже если is_allowed=False
        if db_user.is_admin:
            return await handler(event, data)

        # Проверяем доступ для обычных пользователей
        # Если у пользователя нет external_id, он должен его ввести
        # Если external_id есть, но дисклеймер не принят, показываем дисклеймер
        if db_user.external_id and db_user.is_allowed and not db_user.disclaimer_accepted:
            # Пользователь должен ознакомиться с дисклеймером
            # Пропускаем только callback для принятия дисклеймера
            if isinstance(event, CallbackQuery):
                if event.data == "disclaimer_accepted":
                    return await handler(event, data)
                # Для других callback'ов показываем alert
                await event.answer(
                    "📋 Сначала ознакомьтесь с дисклеймером",
                    show_alert=True
                )
                return
            elif isinstance(event, Message):
                # Для сообщений разрешаем только /start
                from aiogram.filters import CommandStart
                if not event.text or not event.text.startswith("/start"):
                    await event.answer(
                        "📋 Для использования бота необходимо ознакомиться с дисклеймером.\n\n"
                        "Отправьте команду /start для просмотра.",
                        parse_mode="HTML"
                    )
                    return
        
        if not db_user.external_id:
            # Пользователь еще не ввел external_id
            # Пропускаем только команду /start и обработку ввода external_id
            # Остальные команды блокируем
            if isinstance(event, Message):
                # Разрешаем только команду /start и обработку ввода external_id
                from aiogram.filters import CommandStart
                if not event.text or (not event.text.startswith("/start") and not event.text.isdigit()):
                    await event.answer(
                        "🔐 Для использования бота необходимо ввести ваш ID.\n\n"
                        "Отправьте команду /start для начала.",
                        parse_mode="HTML"
                    )
                    return
            elif isinstance(event, CallbackQuery):
                # Для callback'ов показываем alert
                await event.answer(
                    "🔐 Сначала введите ваш ID через команду /start",
                    show_alert=True
                )
                return
        
        # Если external_id есть, но is_allowed=False, проверяем, разрешен ли ID
        if db_user.external_id and not db_user.is_allowed:
            async with async_session_maker() as session:
                if await is_external_id_allowed(session, db_user.external_id):
                    # ID разрешен, но почему-то is_allowed=False - исправляем
                    db_user.is_allowed = True
                    await session.commit()
                else:
                    # ID не разрешен - блокируем доступ
                    if isinstance(event, Message):
                        await event.answer(
                            "🔒 Ваш ID не найден в базе разрешенных пользователей.\n\n"
                            "Обратитесь к администратору для получения доступа.",
                            parse_mode="HTML"
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "🔒 Ваш ID не найден в базе",
                            show_alert=True
                        )
                    return
        
        # Если is_allowed=False и нет external_id или external_id не разрешен
        if not db_user.is_allowed:
            return

        # Доступ разрешен - вызываем следующий обработчик
        return await handler(event, data)
