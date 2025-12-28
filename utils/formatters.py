"""
Утилиты для форматирования текста и сообщений
"""
from typing import Optional
from html import escape
from aiogram.exceptions import TelegramBadRequest


def format_content_card(
    title: str,
    body: Optional[str] = None,
    category_name: Optional[str] = None,
    has_image: bool = False,
    has_file: bool = False
) -> str:
    """
    Форматирует карточку контента для отправки в Telegram
    """
    text = f"<b>{escape(title)}</b>\n\n"
    
    if category_name:
        text += f"📁 <i>{escape(category_name)}</i>\n\n"
    
    if body:
        # Ограничиваем длину body для предпросмотра
        body_preview = body[:500] + "..." if len(body) > 500 else body
        text += f"{escape(body_preview)}\n\n"
    
    # Индикаторы медиа
    if has_image:
        text += "🖼️ "
    if has_file:
        text += "📎 "
    
    return text.strip()


def format_category_menu(category_name: str, description: Optional[str] = None, icon: Optional[str] = None, language: str = "ru") -> str:
    """
    Форматирует меню категории
    
    Args:
        category_name: Название категории
        description: Описание категории
        icon: Эмодзи иконки
        language: Язык сообщения ("ru" или "de")
    """
    text = ""
    if icon:
        text += f"{icon} "
    text += f"<b>{escape(category_name)}</b>\n\n"
    
    if description:
        text += f"{escape(description)}\n\n"
    
    if language == "de":
        text += "Wählen Sie eine Unterkategorie oder Inhalte:"
    else:  # ru
        text += "Выберите подкатегорию или контент:"
    
    return text


def format_breadcrumbs(categories: list) -> str:
    """
    Форматирует хлебные крошки навигации
    """
    if not categories:
        return "🏠 Главное меню"
    
    breadcrumbs = "🏠 Главное меню"
    for cat in categories:
        breadcrumbs += f" → {cat.name}"
    
    return breadcrumbs


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Обрезает текст до максимальной длины
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_search_results(count: int, query: str, language: str = "ru") -> str:
    """
    Форматирует результаты поиска
    
    Args:
        count: Количество результатов
        query: Поисковый запрос
        language: Язык сообщения ("ru" или "de")
    """
    if language == "de":
        if count == 0:
            return f"🔍 Für die Anfrage <b>«{escape(query)}»</b> wurde nichts gefunden."
        return f"🔍 Gefundene Ergebnisse: <b>{count}</b> für die Anfrage <b>«{escape(query)}»</b>"
    else:  # ru
        if count == 0:
            return f"🔍 По запросу <b>«{escape(query)}»</b> ничего не найдено."
        return f"🔍 Найдено результатов: <b>{count}</b> по запросу <b>«{escape(query)}»</b>"


def format_favorites_list(count: int, language: str = "ru") -> str:
    """
    Форматирует список избранного
    
    Args:
        count: Количество избранных материалов
        language: Язык сообщения ("ru" или "de")
    """
    if language == "de":
        if count == 0:
            return "⭐ Sie haben noch keine Favoriten.\n\nFügen Sie Materialien zu den Favoriten hinzu, indem Sie auf ⭐ in der Inhaltskarte klicken."
        return f"⭐ Ihre Favoriten ({count} Materialien):"
    else:  # ru
        if count == 0:
            return "⭐ У вас пока нет избранных материалов.\n\nДобавьте материалы в избранное, нажав на ⭐ в карточке контента."
        return f"⭐ Ваше избранное ({count} материалов):"


def format_welcome_message(user_name: Optional[str] = None, language: str = "ru") -> str:
    """
    Форматирует приветственное сообщение на указанном языке
    
    Args:
        user_name: Имя пользователя
        language: Язык сообщения ("ru" или "de")
    """
    if language == "de":
        name = user_name or "Freund"
        return (
            f"👋 Hallo, <b>{escape(name)}</b>!\n\n"
            "Willkommen im Bot mit ätherischen Ölen und Rezepten!\n\n"
            "🌿 Hier finden Sie:\n"
            "• Rezepte und Hausapotheke\n"
            "• Einzelkomponenten-Öle\n"
            "• Ätherische Ölmischungen\n"
            "• Kinderkollektion\n"
            "• Und vieles mehr!\n\n"
            "Verwenden Sie das Menü unten zur Navigation 👇"
        )
    else:  # ru
        name = user_name or "друг"
        return (
            f"👋 Привет, <b>{escape(name)}</b>!\n\n"
            "Добро пожаловать в бот с эфирными маслами и рецептами!\n\n"
            "🌿 Здесь вы найдете:\n"
            "• Рецепты и аптечку\n"
            "• Однокомпонентные масла\n"
            "• Смеси эфирных масел\n"
            "• Детскую коллекцию\n"
            "• И многое другое!\n\n"
            "Используйте меню ниже для навигации 👇"
        )


async def safe_edit_text(message, text: str, **kwargs):
    """
    Безопасно редактирует текст сообщения, игнорируя ошибку "message is not modified"
    
    Args:
        message: Объект сообщения (Message или CallbackQuery.message)
        text: Новый текст сообщения
        **kwargs: Дополнительные параметры для edit_text (reply_markup, parse_mode и т.д.)
    """
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        # Игнорируем ошибку, если сообщение не изменилось
        if "message is not modified" not in str(e):
            raise  # Если другая ошибка - пробрасываем дальше

