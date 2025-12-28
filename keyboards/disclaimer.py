"""
Клавиатуры для дисклеймера
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_disclaimer_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для дисклеймера с кнопкой подтверждения
    
    Args:
        language: Язык интерфейса ("ru" или "de")
    """
    if language == "de":
        button_text = "✅ Ich habe gelesen und verstanden"
    else:  # ru
        button_text = "✅ Я ознакомился и согласен"
    
    keyboard = [
        [InlineKeyboardButton(text=button_text, callback_data="disclaimer_accepted")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

