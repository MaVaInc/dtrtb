"""
Клавиатуры для админ-панели

Этот модуль содержит все клавиатуры для управления контентом бота
через админ-панель.
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Category, Content, User


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню админ-панели
    
    Returns:
        InlineKeyboardMarkup с кнопками управления
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📁 Категории", callback_data="admin_categories"),
            InlineKeyboardButton(text="📝 Контент", callback_data="admin_content")
        ],
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_categories_list_keyboard(
    categories: List[Category],
    show_back: bool = True,
    add_type_choice: bool = False,
    select_mode: bool = False,
    show_no_parent: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком категорий для управления
    
    Args:
        categories: Список категорий
        show_back: Показывать кнопку "Назад"
        add_type_choice: Показывать выбор типа категории (главное меню/подкатегория)
        select_mode: Режим выбора категории (для добавления контента/подкатегории)
    
    Returns:
        InlineKeyboardMarkup с кнопками категорий
    """
    keyboard = []
    
    if add_type_choice:
        # Выбор типа категории
        keyboard.append([
            InlineKeyboardButton(
                text="📋 Главное меню",
                callback_data="add_category_type_main"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="📂 Подкатегория",
                callback_data="add_category_type_sub"
            )
        ])
    else:
        # Кнопка "Без родителя" для создания категории 1 уровня
        if show_no_parent and select_mode:
            keyboard.append([
                InlineKeyboardButton(
                    text="📋 Без родителя (1 уровень - главное меню)",
                    callback_data="select_category_none"
                )
            ])
            keyboard.append([])  # Разделитель
        
        # Список категорий с указанием уровня
        # Уровень будет вычисляться динамически при выборе
        for category in categories[:20]:  # Ограничиваем 20 категориями
            # Определяем префикс по типу
            if category.is_main_menu:
                prefix = "📋"
                level_text = "1"
            else:
                prefix = "📂"
                level_text = "2-3"  # Будет уточнено при выборе
            
            icon = category.icon_emoji or "📁"
            text = f"{prefix} {category.name} (ур. {level_text})"
            
            if select_mode:
                # Режим выбора - callback для выбора категории
                callback_data = f"select_category_{category.id}"
            else:
                # Режим управления - callback для редактирования
                callback_data = f"admin_edit_category_{category.id}"
            
            keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # Кнопка добавления новой категории
    if not add_type_choice and not select_mode:
        keyboard.append([
            InlineKeyboardButton(
                text="➕ Добавить категорию",
                callback_data="admin_add_category"
            )
        ])
    
    # Кнопка "Назад"
    if show_back:
        keyboard.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_edit_keyboard(category: Category) -> InlineKeyboardMarkup:
    """
    Клавиатура для редактирования категории
    
    Args:
        category: Объект категории
    
    Returns:
        InlineKeyboardMarkup с кнопками редактирования
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"edit_category_name_{category.id}"),
        ],
        [
            InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"edit_category_desc_{category.id}"),
            InlineKeyboardButton(text="🔢 Изменить порядок", callback_data=f"edit_category_order_{category.id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить категорию", callback_data=f"delete_category_{category.id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_categories")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_content_list_keyboard(
    contents: Optional[List[Content]] = None,
    show_back: bool = True
) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления контентом
    
    Args:
        contents: Список контента (опционально)
        show_back: Показывать кнопку "Назад"
    
    Returns:
        InlineKeyboardMarkup с кнопками управления контентом
    """
    keyboard = []
    
    if contents:
        # Список контента
        for content in contents[:20]:  # Ограничиваем 20 элементами
            text = f"📄 {content.title[:30]}..." if len(content.title) > 30 else f"📄 {content.title}"
            keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"admin_edit_content_{content.id}"
                )
            ])
    
    # Кнопка добавления нового контента
    keyboard.append([
        InlineKeyboardButton(
            text="➕ Добавить контент",
            callback_data="admin_add_content"
        )
    ])
    
    # Кнопка "Назад"
    if show_back:
        keyboard.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_content_edit_keyboard(content: Content) -> InlineKeyboardMarkup:
    """
    Клавиатура для редактирования контента
    
    Args:
        content: Объект контента
    
    Returns:
        InlineKeyboardMarkup с кнопками редактирования
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Изменить заголовок", callback_data=f"edit_content_title_{content.id}"),
            InlineKeyboardButton(text="📝 Изменить текст", callback_data=f"edit_content_body_{content.id}")
        ],
        [
            InlineKeyboardButton(text="📷 Изменить фото", callback_data=f"edit_content_photo_{content.id}"),
            InlineKeyboardButton(text="📎 Изменить файл", callback_data=f"edit_content_file_{content.id}")
        ],
        [
            InlineKeyboardButton(text="📁 Изменить категорию", callback_data=f"edit_content_category_{content.id}")
        ],
        [
            InlineKeyboardButton(text="👁️ Просмотр", callback_data=f"view_content_{content.id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_content_{content.id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_content")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_users_list_keyboard(
    users: List[User],
    show_back: bool = True
) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком пользователей
    
    Args:
        users: Список пользователей
        show_back: Показывать кнопку "Назад"
    
    Returns:
        InlineKeyboardMarkup с кнопками пользователей
    """
    keyboard = []
    
    for user in users[:30]:  # Ограничиваем 30 пользователями
        status = "👑" if user.is_admin else "👤"
        name = user.first_name or user.username or f"ID: {user.telegram_id}"
        external_id_text = f" ({user.external_id})" if user.external_id else ""
        text = f"{status} {name}{external_id_text}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"toggle_user_{user.telegram_id}"
            )
        ])
    
    # Кнопка "Назад"
    if show_back:
        keyboard.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

