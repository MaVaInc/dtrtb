"""
Обработчики избранного
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import async_session_maker
from database.crud import get_user_favorites
from keyboards.menu import get_favorites_keyboard
from utils.formatters import format_favorites_list
from database.models import User

router = Router()


@router.callback_query(F.data == "favorites_list")
async def callback_favorites_list(callback: CallbackQuery, db_user: User, user_language: str = "ru"):
    """
    Обработчик просмотра списка избранного
    """
    async with async_session_maker() as session:
        favorites = await get_user_favorites(session, db_user.id)
    
    text = format_favorites_list(len(favorites), language=user_language)
    
    if favorites:
        keyboard = get_favorites_keyboard(favorites, user_language)
    else:
        from keyboards.navigation import get_main_menu_only_keyboard
        keyboard = get_main_menu_only_keyboard(user_language)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

