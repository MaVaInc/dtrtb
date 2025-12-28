"""
SQLAlchemy модели для базы данных

Этот файл содержит определения всех таблиц базы данных в виде Python классов.
Каждый класс представляет собой таблицу в БД, а атрибуты класса - колонки таблицы.

Структура БД:
1. User - пользователи бота (из Telegram)
2. Category - категории контента (иерархическая структура)
3. Content - контент (статьи, рецепты и т.д.)
4. UserCategory - связь пользователя с категорией (для whitelist)
5. Favorite - избранное пользователя
6. Analytics - аналитика использования бота

Все модели наследуются от Base, что позволяет SQLAlchemy автоматически
создавать таблицы при вызове Base.metadata.create_all().
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    """
    Модель пользователя Telegram бота
    
    Хранит информацию о пользователях, которые взаимодействуют с ботом.
    Создается автоматически при первом обращении пользователя к боту.
    
    Поля:
    - telegram_id: уникальный ID пользователя в Telegram (используется для идентификации)
    - username: имя пользователя в Telegram (может быть None)
    - first_name: имя пользователя
    - is_admin: флаг администратора (для будущего функционала)
    - is_allowed: флаг доступа (whitelist) - если False, пользователь не может использовать бота
    - created_at: дата регистрации в боте
    - last_active: дата последней активности
    
    Связи:
    - user_categories: категории, к которым у пользователя есть доступ
    - favorites: избранные материалы пользователя
    - analytics: записи аналитики действий пользователя
    """
    __tablename__ = "users"  # Имя таблицы в БД

    # Первичный ключ - уникальный ID записи
    id = Column(Integer, primary_key=True, index=True)
    
    # Telegram ID пользователя (BigInteger, так как ID могут быть очень большими)
    # unique=True - гарантирует, что один Telegram ID = одна запись
    # index=True - создает индекс для быстрого поиска
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    
    # Имя пользователя в Telegram (может отсутствовать)
    username = Column(String(255), nullable=True)
    
    # Имя пользователя (отображаемое имя)
    first_name = Column(String(255), nullable=True)
    
    # Флаг администратора (для будущего функционала админ-панели)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Флаг доступа - если False, пользователь не может использовать бота
    # Устанавливается администратором вручную или через whitelist
    is_allowed = Column(Boolean, default=False, nullable=False)
    
    # Дата и время регистрации пользователя в боте
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Дата и время последней активности пользователя
    # Обновляется при каждом взаимодействии с ботом
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Язык пользователя (ru, de) - определяется автоматически из Telegram
    # По умолчанию русский, если не удалось определить
    language_code = Column(String(10), default="ru", nullable=False)
    
    # External ID - ID из другого сервиса (7-9 цифр, например 12345678)
    # Используется для аутентификации пользователей
    # Один external_id может быть присвоен только одному пользователю
    external_id = Column(String(20), unique=True, nullable=True, index=True)
    
    # Флаг принятия дисклеймера
    # Если False, пользователь должен ознакомиться с дисклеймером перед использованием бота
    disclaimer_accepted = Column(Boolean, default=False, nullable=False)
    
    # Дата и время принятия дисклеймера (для доказательства ознакомления)
    disclaimer_accepted_at = Column(DateTime, nullable=True)

    # Связи с другими таблицами
    # relationship создает связь между таблицами на уровне ORM
    # cascade="all, delete-orphan" - при удалении пользователя удаляются связанные записи
    user_categories = relationship("UserCategory", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        """Строковое представление объекта (для отладки)"""
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class AllowedExternalId(Base):
    """
    Модель для хранения разрешенных external_id
    
    Содержит список ID из другого сервиса, которые имеют доступ к боту.
    При первом запуске пользователь должен ввести свой external_id,
    и если он есть в этой таблице, ему дается доступ.
    
    Поля:
    - external_id: ID из другого сервиса (7-9 цифр, например 12345678)
    - is_active: флаг активности (можно деактивировать ID без удаления)
    - created_at: дата добавления ID в базу
    """
    __tablename__ = "allowed_external_ids"
    
    # Первичный ключ
    id = Column(Integer, primary_key=True, index=True)
    
    # External ID (строка, так как может содержать ведущие нули)
    external_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Флаг активности
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Дата добавления
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AllowedExternalId(external_id={self.external_id}, is_active={self.is_active})>"


class Category(Base):
    """
    Модель категории контента
    
    Категории организованы в иерархическую структуру (дерево):
    - Категории верхнего уровня (parent_id=None) отображаются в главном меню
    - Подкатегории (parent_id указывает на родительскую категорию) отображаются внутри категории
    
    Пример структуры:
    - Рецепты (главное меню)
      - Завтраки (подкатегория)
      - Обеды (подкатегория)
    - Эфирные масла (главное меню)
      - Однокомпонентные (подкатегория)
      - Смеси (подкатегория)
    
    Поля:
    - name: название категории
    - icon_emoji: эмодзи для отображения в меню (например, 🌿, 📚)
    - parent_id: ID родительской категории (None для категорий верхнего уровня)
    - order_index: порядок отображения (меньше = выше в списке)
    - description: описание категории (отображается в меню)
    - image_url: URL изображения категории (опционально)
    - is_main_menu: флаг главного меню (True для категорий верхнего уровня)
    - is_active: флаг активности (неактивные категории не отображаются)
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    
    # Название категории (обязательное поле)
    name = Column(String(255), nullable=False, index=True)
    
    # Язык категории (ru, de)
    # Каждая категория имеет версию на каждом языке
    # При создании категории на русском автоматически создается связанная на немецком
    language = Column(String(10), default="ru", nullable=False, index=True)
    
    # ID связанной категории на другом языке (для синхронизации ru <-> de)
    # Если создается категория на русском, автоматически создается связанная на немецком
    linked_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Эмодзи для категории (например, 🌿, 📚, 💊)
    # Отображается рядом с названием в меню
    icon_emoji = Column(String(10), nullable=True)
    
    # ID родительской категории
    # None означает, что это категория верхнего уровня (в главном меню)
    # Если указан parent_id, это подкатегория
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Порядок отображения категорий
    # Категории с меньшим order_index отображаются выше
    # Используется для сортировки в меню
    order_index = Column(Integer, default=0, nullable=False)
    
    # Описание категории (отображается в меню под названием)
    description = Column(Text, nullable=True)
    
    # URL изображения категории (опционально)
    # Можно использовать для отображения картинки в меню
    image_url = Column(String(500), nullable=True)
    
    # Флаг главного меню
    # True для категорий верхнего уровня, которые отображаются в главном меню
    # В главном меню обычно 4 категории
    is_main_menu = Column(Boolean, default=False, nullable=False)
    
    # Флаг активности
    # Неактивные категории не отображаются в меню, но остаются в БД
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Дата создания категории
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи с другими таблицами
    # parent - родительская категория (для навигации вверх по дереву)
    # children - дочерние категории (автоматически создается через backref)
    parent = relationship("Category", remote_side=[id], backref="children", foreign_keys=[parent_id])
    linked_category = relationship("Category", remote_side=[id], foreign_keys=[linked_category_id], post_update=True)
    
    # content - контент, принадлежащий этой категории
    # order_by - сортировка контента по order_index
    content = relationship("Content", back_populates="category", cascade="all, delete-orphan", order_by="Content.order_index")
    
    # user_categories - пользователи, имеющие доступ к этой категории
    user_categories = relationship("UserCategory", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, parent_id={self.parent_id})>"


class Content(Base):
    """
    Модель контента (статьи, рецепты, материалы)
    
    Контент принадлежит определенной категории и содержит:
    - Текстовую информацию (заголовок, описание)
    - Медиа файлы (изображения, документы)
    
    Поля:
    - category_id: ID категории, к которой относится контент
    - title: заголовок контента
    - body: основной текст контента (может быть длинным)
    - image_url: URL изображения (опционально)
    - file_url: URL файла/документа (опционально)
    - order_index: порядок отображения в категории
    - is_published: флаг публикации (неопубликованный контент не отображается)
    - created_at: дата создания
    - updated_at: дата последнего обновления
    """
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    
    # ID категории, к которой относится контент
    # ForeignKey создает связь с таблицей categories
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Заголовок контента (обязательное поле)
    title = Column(String(500), nullable=False)
    
    # Язык контента (ru, de)
    # Каждый контент имеет версию на каждом языке
    language = Column(String(10), default="ru", nullable=False, index=True)
    
    # ID связанного контента на другом языке (для синхронизации ru <-> de)
    linked_content_id = Column(Integer, ForeignKey("content.id"), nullable=True)
    
    # Скрытые теги/ключевые слова для улучшения поиска
    # Разделяются запятыми, не видны пользователю
    # Пример: "головная боль, мигрень, боль, рецепт, масло, kopfschmerzen, migräne"
    # Используются для поиска на обоих языках
    search_tags = Column(Text, nullable=True)
    
    # Основной текст контента
    # Text позволяет хранить длинные тексты (неограниченной длины)
    body = Column(Text, nullable=True)
    
    # URL изображения для контента
    # Можно использовать для отображения картинки в карточке контента
    image_url = Column(String(500), nullable=True)
    
    # URL файла/документа
    # Можно использовать для прикрепления PDF, документов и т.д.
    file_url = Column(String(500), nullable=True)
    
    # Порядок отображения контента в категории
    # Контент с меньшим order_index отображается выше
    order_index = Column(Integer, default=0, nullable=False)
    
    # Флаг публикации
    # Неопубликованный контент (is_published=False) не отображается пользователям
    # Полезно для черновиков или контента на модерации
    is_published = Column(Boolean, default=True, nullable=False)
    
    # Дата создания контента
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Дата последнего обновления контента
    # onupdate=datetime.utcnow автоматически обновляет дату при изменении записи
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи с другими таблицами
    category = relationship("Category", back_populates="content")
    favorites = relationship("Favorite", back_populates="content", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="content", cascade="all, delete-orphan")

    # Индексы для ускорения поиска
    # Индекс по title, body и search_tags позволяет быстро искать контент
    __table_args__ = (
        Index('idx_content_search', 'title', 'body', 'search_tags'),
    )

    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title}, category_id={self.category_id})>"


class UserCategory(Base):
    """
    Связь пользователя с категорией (для whitelist)
    
    Эта таблица используется для управления доступом пользователей к категориям.
    Если пользователь добавлен в эту таблицу для определенной категории,
    он получает доступ к этой категории (даже если is_allowed=False).
    
    Используется для гибкого управления доступом:
    - Можно дать доступ к определенным категориям конкретным пользователям
    - Можно ограничить доступ к категориям
    
    Поля:
    - user_id: ID пользователя
    - category_id: ID категории
    
    Уникальность: один пользователь может иметь доступ к одной категории только один раз
    """
    __tablename__ = "user_categories"

    id = Column(Integer, primary_key=True, index=True)
    
    # ID пользователя
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # ID категории
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)

    # Связи
    user = relationship("User", back_populates="user_categories")
    category = relationship("Category", back_populates="user_categories")

    # Уникальность пары user_id + category_id
    # Один пользователь не может быть добавлен к одной категории дважды
    __table_args__ = (
        Index('idx_user_category_unique', 'user_id', 'category_id', unique=True),
    )

    def __repr__(self):
        return f"<UserCategory(user_id={self.user_id}, category_id={self.category_id})>"


class Favorite(Base):
    """
    Избранное пользователя
    
    Хранит контент, который пользователь добавил в избранное.
    Пользователь может быстро получить доступ к избранным материалам.
    
    Поля:
    - user_id: ID пользователя
    - content_id: ID контента
    - created_at: дата добавления в избранное
    
    Уникальность: один контент может быть в избранном у пользователя только один раз
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    
    # ID пользователя, который добавил в избранное
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # ID контента, добавленного в избранное
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False, index=True)
    
    # Дата добавления в избранное
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User", back_populates="favorites")
    content = relationship("Content", back_populates="favorites")

    # Уникальность пары user_id + content_id
    # Один контент не может быть добавлен в избранное дважды одним пользователем
    __table_args__ = (
        Index('idx_favorite_unique', 'user_id', 'content_id', unique=True),
    )

    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, content_id={self.content_id})>"


class Analytics(Base):
    """
    Аналитика использования бота
    
    Хранит информацию о действиях пользователей для анализа использования бота:
    - Просмотры контента
    - Поисковые запросы
    - Добавления в избранное
    - И другие действия
    
    Поля:
    - user_id: ID пользователя (может быть None для анонимных действий)
    - content_id: ID контента (если действие связано с контентом)
    - action: тип действия (view, search, favorite_add, favorite_remove и т.д.)
    - created_at: дата и время действия
    """
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    
    # ID пользователя (может быть None для анонимных действий)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # ID контента (если действие связано с контентом)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=True, index=True)
    
    # Тип действия
    # Возможные значения: view, search, favorite_add, favorite_remove, category_view и т.д.
    action = Column(String(50), nullable=False, index=True)
    
    # Дата и время действия
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Связи
    user = relationship("User", back_populates="analytics")
    content = relationship("Content", back_populates="analytics")

    def __repr__(self):
        return f"<Analytics(user_id={self.user_id}, action={self.action}, content_id={self.content_id})>"
