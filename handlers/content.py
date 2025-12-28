"""
Обработчики отображения контента
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from database.db import async_session_maker
from database.crud import (
    get_content_by_id,
    is_favorite,
    add_analytics
)
from keyboards.menu import get_content_keyboard
from keyboards.navigation import get_main_menu_only_keyboard
from utils.formatters import format_content_card
from database.models import User
from pathlib import Path
import config

router = Router()


@router.callback_query(F.data.startswith("content_"))
async def callback_content(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик просмотра контента
    """
    try:
        content_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка: неверный ID контента", show_alert=True)
        return
    
    async with async_session_maker() as session:
        content = await get_content_by_id(session, content_id)
        
        if not content:
            await callback.answer("❌ Контент не найден", show_alert=True)
            return
        
        # Проверяем, опубликован ли контент
        if not content.is_published:
            await callback.answer("❌ Этот контент недоступен", show_alert=True)
            return
        
        # Проверяем избранное
        favorite = await is_favorite(session, db_user.id, content_id)
        
        # Форматируем карточку
        text = format_content_card(
            title=content.title,
            body=content.body,
            category_name=content.category.name if content.category else None,
            has_image=bool(content.image_url),
            has_file=bool(content.file_url)
        )
        
        # Создаем клавиатуру
        keyboard = get_content_keyboard(
            content_id=content_id,
            category_id=content.category_id,
            is_favorite=favorite,
            show_back=True,
            content_title=content.title,
            language=user_language
        )
        
        # Отправляем изображение, если есть
        if content.image_url:
            try:
                # Проверяем, локальный ли это файл
                image_path = Path(content.image_url)
                if image_path.exists() and image_path.is_absolute():
                    photo = FSInputFile(str(image_path))
                    await callback.message.answer_photo(
                        photo=photo,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                        protect_content=True  # Защита от пересылки и скриншотов
                    )
                    await callback.message.delete()
                else:
                    # URL изображения
                    await callback.message.answer_photo(
                        photo=content.image_url,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                        protect_content=True  # Защита от пересылки и скриншотов
                    )
                    await callback.message.delete()
            except Exception as e:
                # Если не удалось отправить фото, отправляем текст
                print(f"Error sending photo: {e}")
                from utils.formatters import safe_edit_text
                # Для текстовых сообщений защита через protect_content недоступна
                # Используем обычное редактирование
                await safe_edit_text(
                    callback.message,
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            # Отправляем только текст
            from utils.formatters import safe_edit_text
            await safe_edit_text(
                callback.message,
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
        # Отправляем файл, если есть
        if content.file_url:
            try:
                file_path = Path(content.file_url)
                if file_path.exists() and file_path.is_absolute():
                    document = FSInputFile(str(file_path))
                    await callback.message.answer_document(
                        document=document,
                        reply_markup=get_main_menu_only_keyboard(),
                        protect_content=True  # Защита от пересылки и скриншотов
                    )
            except Exception as e:
                print(f"Error sending file: {e}")
        
        # Записываем аналитику
        await add_analytics(
            session=session,
            action="view",
            user_id=db_user.id,
            content_id=content_id
        )
        
        await callback.answer()


@router.callback_query(F.data.startswith("favorite_toggle_"))
async def callback_favorite_toggle(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик добавления/удаления из избранного
    """
    try:
        content_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    from database.crud import add_favorite, remove_favorite, get_content_by_id
    
    async with async_session_maker() as session:
        content = await get_content_by_id(session, content_id)
        if not content:
            await callback.answer("❌ Контент не найден", show_alert=True)
            return
        
        is_fav = await is_favorite(session, db_user.id, content_id)
        
        if is_fav:
            await remove_favorite(session, db_user.id, content_id)
            message = "💔 Удалено из избранного"
            await add_analytics(session, "favorite_remove", db_user.id, content_id)
        else:
            await add_favorite(session, db_user.id, content_id)
            message = "⭐ Добавлено в избранное"
            await add_analytics(session, "favorite_add", db_user.id, content_id)
        
        # Обновляем клавиатуру
        keyboard = get_content_keyboard(
            content_id=content_id,
            category_id=content.category_id,
            is_favorite=not is_fav,
            show_back=True,
            language=user_language
        )
        
        # Обновляем сообщение
        text = format_content_card(
            title=content.title,
            body=content.body,
            category_name=content.category.name if content.category else None,
            has_image=bool(content.image_url),
            has_file=bool(content.file_url)
        )
        
        # Тексты сообщений на разных языках
        if user_language == "de":
            if is_fav:
                message = "💔 Aus Favoriten entfernt"
            else:
                message = "⭐ Zu Favoriten hinzugefügt"
        else:  # ru
            if is_fav:
                message = "💔 Удалено из избранного"
            else:
                message = "⭐ Добавлено в избранное"
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer(message)

