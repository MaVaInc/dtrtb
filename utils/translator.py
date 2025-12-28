"""
Модуль для перевода текста между языками

Используется для автоматического перевода названий категорий и контента
при создании связанных версий на разных языках.
"""
from typing import Optional
import asyncio

# Попробуем использовать библиотеку для перевода
# Если её нет, будем использовать базовый словарь
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

# Базовый словарь для частых слов (на случай, если переводчик недоступен)
TRANSLATION_DICT = {
    "кашель": "Husten",
    "простуда": "Erkältung",
    "головная боль": "Kopfschmerzen",
    "боль в горле": "Halsschmerzen",
    "температура": "Fieber",
    "рецепты": "Rezepte",
    "эфирные масла": "Ätherische Öle",
    "однокомпонентные": "Einzelkomponenten",
    "смеси": "Mischungen",
    "детская коллекция": "Kinderkollektion",
    "аптечка": "Hausapotheke",
    "завтраки": "Frühstück",
    "обеды": "Mittagessen",
    "ужины": "Abendessen",
    "напитки": "Getränke",
    "десерты": "Desserts",
}


async def translate_text(text: str, source_lang: str = "ru", target_lang: str = "de") -> str:
    """
    Переводит текст с одного языка на другой
    
    Args:
        text: Текст для перевода
        source_lang: Исходный язык (по умолчанию "ru")
        target_lang: Целевой язык (по умолчанию "de")
    
    Returns:
        Переведенный текст
    
    Пример:
        translated = await translate_text("кашель", "ru", "de")
        # Вернет "Husten"
    """
    if not text or not text.strip():
        return text
    
    text = text.strip()
    
    # Сначала проверяем словарь
    text_lower = text.lower()
    if text_lower in TRANSLATION_DICT:
        return TRANSLATION_DICT[text_lower]
    
    # Если переводчик доступен, используем его
    if TRANSLATOR_AVAILABLE:
        try:
            # Запускаем перевод в отдельном потоке, чтобы не блокировать event loop
            loop = asyncio.get_event_loop()
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = await loop.run_in_executor(
                None,
                lambda: translator.translate(text)
            )
            return translated
        except Exception as e:
            # Если переводчик не сработал, возвращаем исходный текст
            print(f"Translation error: {e}")
            return text
    
    # Если переводчик недоступен и слова в словаре нет, возвращаем исходный текст
    return text


async def translate_description(description: Optional[str], source_lang: str = "ru", target_lang: str = "de") -> Optional[str]:
    """
    Переводит описание категории или контента
    
    Args:
        description: Описание для перевода (может быть None)
        source_lang: Исходный язык
        target_lang: Целевой язык
    
    Returns:
        Переведенное описание или None
    """
    if not description:
        return None
    
    return await translate_text(description, source_lang, target_lang)

