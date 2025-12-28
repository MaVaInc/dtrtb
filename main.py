"""
Главный файл для запуска Telegram бота

Этот файл является точкой входа в приложение. Он:
1. Инициализирует бота и диспетчер сообщений
2. Регистрирует все middleware (промежуточное ПО)
3. Подключает все обработчики (handlers)
4. Инициализирует базу данных
5. Запускает бота в режиме polling (опрос сервера Telegram)

Для запуска бота:
1. Убедитесь, что создан файл .env с BOT_TOKEN
2. Запустите: python main.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь Python
# Это необходимо для корректного импорта модулей
sys.path.insert(0, str(Path(__file__).parent))

# Импорты из библиотеки aiogram для работы с Telegram Bot API
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # Хранилище состояний в памяти

# Импорт конфигурации (токен бота из .env файла)
from config import BOT_TOKEN

# Импорт функций для работы с БД
from database.db import init_db

# Импорт middleware - промежуточного ПО, которое обрабатывает все сообщения
from middleware.auth import AuthMiddleware, AccessMiddleware  # Проверка доступа пользователей
from middleware.analytics import AnalyticsMiddleware  # Сбор аналитики
from middleware.language import LanguageMiddleware  # Определение языка пользователя
from middleware.protection import ContentProtectionMiddleware  # Защита от пересылки

# Импорт всех обработчиков (handlers) - функции, которые обрабатывают команды и callback'и
from handlers import auth, menu, content, search, favorites, admin, features

# Настройка логирования
# Логи будут выводиться в консоль с указанием времени, модуля и уровня
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования: INFO показывает важные события
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Главная асинхронная функция для запуска бота
    
    Эта функция:
    1. Проверяет наличие токена бота
    2. Создает экземпляр бота и диспетчера
    3. Регистрирует middleware в правильном порядке
    4. Подключает все роутеры с обработчиками
    5. Инициализирует базу данных (создает таблицы, если их нет)
    6. Запускает бота в режиме polling
    """
    # Проверяем наличие токена бота
    # Токен получается из файла .env через config.py
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен! Проверьте файл .env")
        return
    
    # Инициализируем бота с токеном
    # Bot - это класс для взаимодействия с Telegram Bot API
    bot = Bot(token=BOT_TOKEN)
    
    # Создаем диспетчер - он управляет обработкой сообщений и callback'ов
    # MemoryStorage - хранилище состояний FSM (конечный автомат состояний) в памяти
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем middleware (промежуточное ПО)
    # ВАЖНО: порядок регистрации имеет значение!
    # Middleware выполняются в порядке регистрации
    
    # 1. AuthMiddleware - проверяет и создает пользователя в БД
    #    Выполняется первым, чтобы пользователь был доступен для других middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # 2. LanguageMiddleware - определяет язык пользователя из Telegram
    #    Выполняется после AuthMiddleware, так как нужен db_user
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())
    
    # 3. AccessMiddleware - проверяет права доступа пользователя
    #    Выполняется после AuthMiddleware, так как нужен объект пользователя
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())
    
    # 4. ContentProtectionMiddleware - защита от пересылки и скриншотов
    #    Выполняется перед AnalyticsMiddleware
    dp.message.middleware(ContentProtectionMiddleware())
    
    # 5. AnalyticsMiddleware - собирает статистику использования
    #    Выполняется последним, чтобы зафиксировать все действия
    dp.message.middleware(AnalyticsMiddleware())
    dp.callback_query.middleware(AnalyticsMiddleware())
    
    # Регистрируем роутеры с обработчиками
    # Роутер - это группа обработчиков для определенных команд/событий
    dp.include_router(auth.router)       # Обработка аутентификации и команды /start
    dp.include_router(menu.router)       # Обработка навигации по меню
    dp.include_router(content.router)    # Обработка отображения контента
    dp.include_router(search.router)     # Обработка поиска
    dp.include_router(favorites.router)   # Обработка избранного
    dp.include_router(admin.router)      # Админ-панель для управления контентом
    dp.include_router(features.router)   # Крутые фишки и вау-эффекты
    
    # Устанавливаем команды бота
    await features.set_bot_commands(bot)
    
    # Инициализируем базу данных
    # Эта функция создает все таблицы, если их еще нет
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    # Запускаем бота в режиме polling
    # Polling - это периодический опрос сервера Telegram на наличие новых сообщений
    logger.info("Бот запущен")
    try:
        # start_polling запускает бесконечный цикл опроса сервера
        # allowed_updates указывает, какие типы обновлений обрабатывать
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Закрываем сессию бота при завершении работы
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")

