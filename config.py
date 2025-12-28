"""
Конфигурация бота

Этот файл содержит настройки приложения:
- BOT_TOKEN - токен бота от @BotFather в Telegram
- DATABASE_URL - строка подключения к базе данных

Все настройки загружаются из файла .env для безопасности.
Если .env файл не найден, используются значения по умолчанию.

ВАЖНО: Создайте файл .env в корне проекта со следующим содержимым:
BOT_TOKEN=ваш_токен_бота_здесь
DATABASE_URL=sqlite+aiosqlite:///./bot.db  (опционально, это значение по умолчанию)
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
# Файл .env должен находиться в корне проекта (там же, где config.py)
load_dotenv()

# Токен бота из переменной окружения или .env файла
# Получить токен можно у @BotFather в Telegram командой /newbot или /token
# Если токен не найден, будет пустая строка (бот не запустится)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# URL базы данных
# По умолчанию используется SQLite - файловая БД, не требует отдельного сервера
# Формат: sqlite+aiosqlite:///./bot.db
#   - sqlite+aiosqlite - драйвер для работы с SQLite в асинхронном режиме
#   - ./bot.db - путь к файлу БД (в корне проекта)
# 
# Для использования другой БД (PostgreSQL, MySQL) измените эту строку:
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///./bot.db"
)

