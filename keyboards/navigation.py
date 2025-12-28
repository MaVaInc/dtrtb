"""
Навигационные клавиатуры
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """
    Создает простую клавиатуру с кнопкой "Назад"
    """
    keyboard = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_main_menu_only_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру только с кнопкой главного меню
    
    Args:
        language: Язык интерфейса ("ru" или "de")
    """
    if language == "de":
        main_menu_text = "🏠 Hauptmenü"
    else:  # ru
        main_menu_text = "🏠 Главное меню"
    
    keyboard = [
        [InlineKeyboardButton(text=main_menu_text, callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

