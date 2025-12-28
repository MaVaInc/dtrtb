"""
Подключение к базе данных

Этот модуль отвечает за:
1. Создание подключения к базе данных
2. Создание фабрики сессий для работы с БД
3. Инициализацию БД (создание таблиц)
4. Управление сессиями БД

Используется SQLAlchemy в асинхронном режиме для работы с БД.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь Python
# Это нужно для импорта config.py
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATABASE_URL

# Создаем движок (engine) базы данных
# Движок - это объект, который управляет подключением к БД
# create_async_engine создает асинхронный движок для работы с БД
engine = create_async_engine(
    DATABASE_URL,  # URL подключения из config.py
    echo=False,    # Если True - все SQL запросы будут выводиться в консоль (для отладки)
    future=True    # Использовать новый API SQLAlchemy 2.0
)

# Создаем фабрику сессий
# Сессия - это объект для выполнения запросов к БД
# async_sessionmaker создает новую сессию при каждом вызове
async_session_maker = async_sessionmaker(
    engine,                    # Движок БД
    class_=AsyncSession,       # Класс сессии (асинхронная)
    expire_on_commit=False     # Не сбрасывать объекты после commit (удобнее для работы)
)

# Базовый класс для всех моделей БД
# Все модели (User, Category, Content и т.д.) наследуются от этого класса
# Это позволяет SQLAlchemy автоматически создавать таблицы на основе моделей
Base = declarative_base()


async def get_session() -> AsyncSession:
    """
    Получить сессию БД (генератор для dependency injection)
    
    Это функция-генератор, которая создает сессию БД и автоматически закрывает её
    после использования. Используется для dependency injection в обработчиках.
    
    Пример использования:
        async with async_session_maker() as session:
            # работа с БД
            result = await session.execute(select(User))
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session_maker() as session:
        try:
            yield session  # Возвращаем сессию
        finally:
            await session.close()  # Закрываем сессию после использования


async def init_db():
    """
    Инициализация БД - создание всех таблиц
    
    Эта функция создает все таблицы в базе данных на основе моделей,
    которые наследуются от Base. Если таблицы уже существуют, ничего не происходит.
    
    Вызывается при запуске бота в main.py.
    
    Важно: Эта функция не удаляет существующие таблицы, только создает новые,
    если их нет. Для полной пересоздания БД нужно удалить файл bot.db.
    """
    # begin() создает транзакцию, которая автоматически коммитится при успехе
    async with engine.begin() as conn:
        # run_sync выполняет синхронную функцию в асинхронном контексте
        # create_all создает все таблицы, определенные в моделях
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Закрытие соединений с БД
    
    Эта функция закрывает все соединения с базой данных.
    Вызывается при завершении работы приложения.
    """
    await engine.dispose()  # Закрывает все соединения пула

