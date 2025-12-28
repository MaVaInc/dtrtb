"""
Обработчики для аутентификации пользователей

Обрабатывает ввод external_id при первом запуске бота.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import async_session_maker
from database.crud import (
    get_user_by_telegram_id,
    is_external_id_allowed,
    link_external_id_to_user,
    is_external_id_used,
    accept_disclaimer
)
from database.models import User
from utils.formatters import format_welcome_message
from keyboards.menu import get_main_menu_keyboard
from keyboards.disclaimer import get_disclaimer_keyboard
from database.crud import get_main_menu_categories
from pathlib import Path
from aiogram.types import FSInputFile

router = Router()


class AuthStates(StatesGroup):
    """Состояния для процесса аутентификации"""
    waiting_for_external_id = State()


@router.message(CommandStart())
async def cmd_start_auth(message: Message, db_user: User, state: FSMContext, user_language: str = "ru"):
    """
    Обработчик команды /start
    
    Если у пользователя нет external_id, запрашивает его ввод.
    Если external_id есть, показывает главное меню.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Обработчик /start вызван для пользователя {db_user.telegram_id}, external_id={db_user.external_id}, is_allowed={db_user.is_allowed}")
    
    # Если у пользователя уже есть external_id и доступ, проверяем дисклеймер
    if db_user.external_id and db_user.is_allowed:
        async with async_session_maker() as session:
            # Обновляем db_user из БД для получения актуального статуса дисклеймера
            db_user = await get_user_by_telegram_id(session, db_user.telegram_id)
            
            # Если дисклеймер не принят, показываем его
            if not db_user.disclaimer_accepted:
                disclaimer_path = Path("images/disclaimer.PNG")
                
                if user_language == "de":
                    caption = (
                        "📋 <b>Wichtiger Hinweis</b>\n\n"
                        "Bitte lesen Sie den Disclaimer sorgfältig durch.\n\n"
                        "Nach dem Lesen klicken Sie auf die Schaltfläche unten, um fortzufahren."
                    )
                else:  # ru
                    caption = (
                        "📋 <b>Важное уведомление</b>\n\n"
                        "Пожалуйста, внимательно ознакомьтесь с дисклеймером.\n\n"
                        "После прочтения нажмите кнопку внизу, чтобы продолжить."
                    )
                
                if disclaimer_path.exists():
                    photo = FSInputFile(str(disclaimer_path))
                    await message.answer_photo(
                        photo=photo,
                        caption=caption,
                        reply_markup=get_disclaimer_keyboard(user_language),
                        parse_mode="HTML"
                    )
                else:
                    await message.answer(
                        caption,
                        reply_markup=get_disclaimer_keyboard(user_language),
                        parse_mode="HTML"
                    )
                return
            
            # Если дисклеймер принят, показываем главное меню
            categories = await get_main_menu_categories(session, language=user_language)
        
        welcome_text = format_welcome_message(
            db_user.first_name or db_user.username,
            language=user_language
        )
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(categories, is_admin=db_user.is_admin, language=user_language),
            parse_mode="HTML"
        )
        return
    
    # Если external_id нет, запрашиваем его
    if not db_user.external_id:
        if user_language == "de":
            text = (
                "🔐 <b>Willkommen!</b>\n\n"
                "Um den Bot zu verwenden, müssen Sie Ihre ID eingeben.\n\n"
                "Ihre ID ist eine 7-9-stellige Nummer (z.B. 12345678).\n\n"
                "Bitte geben Sie Ihre ID ein:"
            )
        else:  # ru
            text = (
                "🔐 <b>Добро пожаловать!</b>\n\n"
                "Для использования бота необходимо ввести ваш ID.\n\n"
                "Ваш ID - это набор из 7-9 цифр (например, 12345678).\n\n"
                "Пожалуйста, введите ваш ID:"
            )
        
        await message.answer(text, parse_mode="HTML")
        await state.set_state(AuthStates.waiting_for_external_id)
        return
    
    # Если external_id есть, но доступ не разрешен
    if user_language == "de":
        text = (
            "🔒 Ihr ID wurde nicht in der Datenbank gefunden.\n\n"
            "Bitte wenden Sie sich an den Administrator für den Zugang."
        )
    else:  # ru
        text = (
            "🔒 Ваш ID не найден в базе данных.\n\n"
            "Обратитесь к администратору для получения доступа."
        )
    
    await message.answer(text, parse_mode="HTML")


@router.message(AuthStates.waiting_for_external_id)
async def process_external_id(message: Message, db_user: User, state: FSMContext, user_language: str = "ru"):
    """
    Обработчик ввода external_id
    
    Проверяет ID в базе разрешенных ID и связывает с пользователем.
    """
    external_id = message.text.strip()
    
    # Проверяем формат ID (7-9 цифр)
    if not external_id.isdigit() or len(external_id) < 7 or len(external_id) > 9:
        if user_language == "de":
            error_text = (
                "❌ <b>Ungültiges Format</b>\n\n"
                "Die ID muss aus 7-9 Ziffern bestehen.\n\n"
                "Bitte versuchen Sie es erneut:"
            )
        else:  # ru
            error_text = (
                "❌ <b>Неверный формат</b>\n\n"
                "ID должен состоять из 7-9 цифр.\n\n"
                "Пожалуйста, попробуйте снова:"
            )
        await message.answer(error_text, parse_mode="HTML")
        return
    
    # Проверяем ID в базе
    async with async_session_maker() as session:
        # Проверяем, разрешен ли ID
        if not await is_external_id_allowed(session, external_id):
            if user_language == "de":
                error_text = (
                    "❌ <b>ID nicht gefunden</b>\n\n"
                    "Ihr ID wurde nicht in der Datenbank gefunden.\n\n"
                    "Bitte wenden Sie sich an den Administrator für den Zugang."
                )
            else:  # ru
                error_text = (
                    "❌ <b>ID не найден</b>\n\n"
                    "Ваш ID не найден в базе данных.\n\n"
                    "Обратитесь к администратору для получения доступа."
                )
            await message.answer(error_text, parse_mode="HTML")
            await state.clear()
            return
        
        # Проверяем, не используется ли ID другим пользователем
        if await is_external_id_used(session, external_id):
            if user_language == "de":
                error_text = (
                    "❌ <b>ID bereits verwendet</b>\n\n"
                    "Dieser ID ist bereits einem anderen Benutzer zugewiesen.\n\n"
                    "Ein ID kann nur einem Benutzer zugewiesen werden."
                )
            else:  # ru
                error_text = (
                    "❌ <b>ID уже используется</b>\n\n"
                    "Этот ID уже присвоен другому пользователю.\n\n"
                    "Один ID может быть присвоен только одному пользователю."
                )
            await message.answer(error_text, parse_mode="HTML")
            await state.clear()
            return
        
        # Связываем ID с пользователем
        success = await link_external_id_to_user(session, db_user.telegram_id, external_id)
        
        if success:
            # Успешно связали - показываем дисклеймер
            await state.clear()
            
            # Обновляем db_user из БД
            db_user = await get_user_by_telegram_id(session, db_user.telegram_id)
            
            # Проверяем, принял ли пользователь дисклеймер
            if not db_user.disclaimer_accepted:
                # Показываем дисклеймер
                disclaimer_path = Path("images/disclaimer.PNG")
                
                if user_language == "de":
                    caption = (
                        "📋 <b>Wichtiger Hinweis</b>\n\n"
                        "Bitte lesen Sie den Disclaimer sorgfältig durch.\n\n"
                        "Nach dem Lesen klicken Sie auf die Schaltfläche unten, um fortzufahren."
                    )
                else:  # ru
                    caption = (
                        "📋 <b>Важное уведомление</b>\n\n"
                        "Пожалуйста, внимательно ознакомьтесь с дисклеймером.\n\n"
                        "После прочтения нажмите кнопку внизу, чтобы продолжить."
                    )
                
                if disclaimer_path.exists():
                    photo = FSInputFile(str(disclaimer_path))
                    await message.answer_photo(
                        photo=photo,
                        caption=caption,
                        reply_markup=get_disclaimer_keyboard(user_language),
                        parse_mode="HTML"
                    )
                else:
                    # Если изображение не найдено, отправляем текстовое сообщение
                    await message.answer(
                        caption,
                        reply_markup=get_disclaimer_keyboard(user_language),
                        parse_mode="HTML"
                    )
                return
            
            # Если дисклеймер уже принят, показываем главное меню
            categories = await get_main_menu_categories(session, language=user_language)
            welcome_text = format_welcome_message(
                db_user.first_name or db_user.username,
                language=user_language
            )
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(categories, is_admin=db_user.is_admin, language=user_language),
                parse_mode="HTML"
            )
        else:
            if user_language == "de":
                error_text = "❌ Fehler beim Verknüpfen des ID. Bitte versuchen Sie es erneut."
            else:  # ru
                error_text = "❌ Ошибка при привязке ID. Пожалуйста, попробуйте снова."
            await message.answer(error_text, parse_mode="HTML")


@router.callback_query(F.data == "disclaimer_accepted")
async def callback_disclaimer_accepted(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик нажатия кнопки "Ознакомился" с дисклеймером
    
    Сохраняет факт ознакомления в БД и показывает главное меню.
    """
    async with async_session_maker() as session:
        # Сохраняем факт ознакомления
        success = await accept_disclaimer(session, db_user.telegram_id)
        
        if success:
            # Обновляем db_user из БД
            db_user = await get_user_by_telegram_id(session, db_user.telegram_id)
            
            # Получаем категории главного меню
            categories = await get_main_menu_categories(session, language=user_language)
            
            # Форматируем приветственное сообщение
            welcome_text = format_welcome_message(
                db_user.first_name or db_user.username,
                language=user_language
            )
            
            # Удаляем сообщение с дисклеймером
            try:
                await callback.message.delete()
            except:
                pass
            
            # Показываем главное меню
            await callback.message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(categories, is_admin=db_user.is_admin, language=user_language),
                parse_mode="HTML"
            )
            
            if user_language == "de":
                await callback.answer("✅ Disclaimer akzeptiert. Willkommen!", show_alert=False)
            else:  # ru
                await callback.answer("✅ Дисклеймер принят. Добро пожаловать!", show_alert=False)
        else:
            if user_language == "de":
                await callback.answer("❌ Fehler beim Speichern. Bitte versuchen Sie es erneut.", show_alert=True)
            else:  # ru
                await callback.answer("❌ Ошибка при сохранении. Пожалуйста, попробуйте снова.", show_alert=True)

