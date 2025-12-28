"""
Клавиатуры для меню и навигации
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Category, Content


def get_main_menu_keyboard(categories: List[Category], is_admin: bool = False, language: str = "ru") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру главного меню с 4 основными категориями
    
    Args:
        categories: Список категорий главного меню
        is_admin: Флаг администратора (если True, добавляется кнопка админ-панели)
        language: Язык интерфейса ("ru" или "de")
    """
    keyboard = []
    
    for category in categories:
        icon = category.icon_emoji or "📁"
        button_text = f"{icon} {category.name}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"category_{category.id}"
            )
        ])
    
    # Дополнительные кнопки (переведенные)
    if language == "de":
        search_text = "🔍 Suche"
        favorites_text = "⭐ Favoriten"
        admin_text = "🔧 Admin-Panel"
    else:  # ru
        search_text = "🔍 Поиск"
        favorites_text = "⭐ Избранное"
        admin_text = "🔧 Админ-панель"
    
    keyboard.append([
        InlineKeyboardButton(text=search_text, callback_data="search_menu"),
        InlineKeyboardButton(text=favorites_text, callback_data="favorites_list")
    ])
    
    # Кнопка админ-панели для администраторов
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(text=admin_text, callback_data="admin_menu")
        ])
    
    # Кнопка смены языка (маленькая, внизу)
    keyboard.append([
        InlineKeyboardButton(text="🌐 RU/DE", callback_data="toggle_language")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_keyboard(
    categories: List[Category],
    contents: List[Content],
    parent_id: Optional[int] = None,
    show_back: bool = True,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для категории с подкатегориями и контентом
    
    Args:
        categories: Список подкатегорий
        contents: Список контента
        parent_id: ID родительской категории
        show_back: Показывать кнопку "Назад"
        language: Язык интерфейса ("ru" или "de")
    """
    keyboard = []
    
    # Подкатегории
    for category in categories:
        icon = category.icon_emoji or "📁"
        button_text = f"{icon} {category.name}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"category_{category.id}"
            )
        ])
    
    # Контент
    for content in contents:
        # Ограничиваем длину названия для кнопки
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
    
    # Навигационные кнопки (переведенные)
    if language == "de":
        back_text = "◀️ Zurück"
        main_menu_text = "🏠 Hauptmenü"
    else:  # ru
        back_text = "◀️ Назад"
        main_menu_text = "🏠 Главное меню"
    
    nav_buttons = []
    if show_back:
        if parent_id:
            nav_buttons.append(InlineKeyboardButton(text=back_text, callback_data=f"category_{parent_id}"))
        else:
            nav_buttons.append(InlineKeyboardButton(text=main_menu_text, callback_data="main_menu"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_content_keyboard(
    content_id: int,
    category_id: int,
    is_favorite: bool = False,
    show_back: bool = True,
    content_title: Optional[str] = None,
    language: str = "ru"
) -> InlineKeyboardMarkup:
    """
    Создает минималистичную клавиатуру для просмотра контента
    
    Убраны кнопки эмодзи реакций и поделиться для приватного бота.
    Эмодзи реакции доступны через стандартную функцию Telegram (долгое нажатие на сообщение).
    
    Args:
        content_id: ID контента
        category_id: ID категории
        is_favorite: В избранном ли контент
        show_back: Показывать кнопку "Назад"
        content_title: Название контента (не используется, для совместимости)
        language: Язык интерфейса ("ru" или "de")
    """
    keyboard = []
    
    # Кнопка избранного (переведенная)
    favorite_icon = "⭐" if not is_favorite else "💛"
    if language == "de":
        favorite_text = "Zu Favoriten" if not is_favorite else "Aus Favoriten"
        back_text = "◀️ Zurück"
        main_menu_text = "🏠 Hauptmenü"
    else:  # ru
        favorite_text = "В избранное" if not is_favorite else "Из избранного"
        back_text = "◀️ Назад"
        main_menu_text = "🏠 Главное меню"
    
    keyboard.append([
        InlineKeyboardButton(
            text=f"{favorite_icon} {favorite_text}",
            callback_data=f"favorite_toggle_{content_id}"
        )
    ])
    
    # Навигационные кнопки
    nav_buttons = []
    if show_back:
        nav_buttons.append(InlineKeyboardButton(text=back_text, callback_data=f"category_{category_id}"))
    
    nav_buttons.append(InlineKeyboardButton(text=main_menu_text, callback_data="main_menu"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_search_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для поиска
    
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


def get_favorites_keyboard(contents: List[Content], language: str = "ru") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для списка избранного
    
    Args:
        contents: Список избранного контента
        language: Язык интерфейса ("ru" или "de")
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
    
    if language == "de":
        main_menu_text = "🏠 Hauptmenü"
    else:  # ru
        main_menu_text = "🏠 Главное меню"
    
    keyboard.append([
        InlineKeyboardButton(text=main_menu_text, callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

