"""
Клавиатуры для контента
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Content


def get_content_list_keyboard(contents: List[Content]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком контента
    """
    keyboard = []
    
    for content in contents:
        title = content.title[:40] + "..." if len(content.title) > 40 else content.title
        icon = "📄"
        if content.image_url:
            icon = "🖼️"
        if content.file_url:
            icon = "📎"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {title}",
                callback_data=f"content_{content.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

