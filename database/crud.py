"""
CRUD операции для работы с базой данных

CRUD = Create, Read, Update, Delete (Создание, Чтение, Обновление, Удаление)

Этот модуль содержит все функции для работы с базой данных:
- User CRUD - операции с пользователями
- Category CRUD - операции с категориями
- Content CRUD - операции с контентом
- UserCategory CRUD - операции с доступом пользователей к категориям
- Favorite CRUD - операции с избранным
- Analytics CRUD - операции с аналитикой

Все функции асинхронные и принимают session (сессию БД) в качестве первого параметра.
Сессия должна быть создана через async_session_maker().

Пример использования:
    async with async_session_maker() as session:
        category = await create_category(session, name="Новая категория")
        content = await create_content(session, category_id=category.id, title="Новый контент")
"""
from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models import (
    User, Category, Content, UserCategory, Favorite, Analytics, AllowedExternalId
)


# ========== User CRUD ==========
# Функции для работы с пользователями

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """
    Получить пользователя по Telegram ID
    
    Args:
        session: Сессия базы данных
        telegram_id: Telegram ID пользователя (уникальный идентификатор из Telegram)
    
    Returns:
        User объект, если пользователь найден, иначе None
    
    Используется для поиска пользователя в БД по его Telegram ID.
    """
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    is_allowed: bool = False,
    language_code: str = "ru"
) -> User:
    """
    Создать нового пользователя в базе данных
    
    Args:
        session: Сессия базы данных
        telegram_id: Telegram ID пользователя (обязательно, уникальный)
        username: Имя пользователя в Telegram (может быть None)
        first_name: Имя пользователя (может быть None)
        is_allowed: Флаг доступа (по умолчанию False - пользователь не может использовать бота)
    
    Returns:
        Созданный объект User
    
    Эта функция вызывается автоматически при первом обращении пользователя к боту
    (через AuthMiddleware). Пользователь создается с is_allowed=False,
    администратор должен дать доступ вручную.
    """
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        is_allowed=is_allowed,
        language_code=language_code
    )
    session.add(user)  # Добавляем объект в сессию
    await session.commit()  # Сохраняем изменения в БД
    await session.refresh(user)  # Обновляем объект из БД (получаем ID и другие поля)
    return user


async def update_user_last_active(session: AsyncSession, user_id: int):
    """Обновить время последней активности пользователя"""
    from datetime import datetime
    user = await session.get(User, user_id)
    if user:
        user.last_active = datetime.utcnow()
        await session.commit()


async def set_user_allowed(session: AsyncSession, telegram_id: int, is_allowed: bool) -> bool:
    """Установить статус доступа пользователя"""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        user.is_allowed = is_allowed
        await session.commit()
        return True
    return False


async def set_user_language(session: AsyncSession, telegram_id: int, language_code: str) -> bool:
    """Установить язык пользователя"""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        user.language_code = language_code
        await session.commit()
        return True
    return False


async def accept_disclaimer(session: AsyncSession, telegram_id: int) -> bool:
    """Отметить, что пользователь ознакомился с дисклеймером"""
    from datetime import datetime
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        user.disclaimer_accepted = True
        user.disclaimer_accepted_at = datetime.utcnow()
        await session.commit()
        return True
    return False


async def get_allowed_users(session: AsyncSession) -> List[User]:
    """Получить всех пользователей с доступом"""
    result = await session.execute(
        select(User).where(User.is_allowed == True)
    )
    return list(result.scalars().all())


# ========== AllowedExternalId CRUD ==========

async def get_allowed_external_id(session: AsyncSession, external_id: str) -> Optional[AllowedExternalId]:
    """Получить разрешенный external_id по значению"""
    result = await session.execute(
        select(AllowedExternalId).where(
            and_(
                AllowedExternalId.external_id == external_id,
                AllowedExternalId.is_active == True
            )
        )
    )
    return result.scalar_one_or_none()


async def is_external_id_allowed(session: AsyncSession, external_id: str) -> bool:
    """Проверить, разрешен ли external_id"""
    allowed_id = await get_allowed_external_id(session, external_id)
    return allowed_id is not None


async def is_external_id_used(session: AsyncSession, external_id: str) -> bool:
    """Проверить, используется ли external_id другим пользователем"""
    result = await session.execute(
        select(User).where(User.external_id == external_id)
    )
    return result.scalar_one_or_none() is not None


async def link_external_id_to_user(session: AsyncSession, telegram_id: int, external_id: str) -> bool:
    """
    Связать external_id с пользователем
    
    Args:
        session: Сессия БД
        telegram_id: Telegram ID пользователя
        external_id: External ID для связи
    
    Returns:
        True если успешно, False если external_id уже используется
    """
    # Проверяем, не используется ли external_id другим пользователем
    if await is_external_id_used(session, external_id):
        return False
    
    # Получаем пользователя
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return False
    
    # Связываем external_id с пользователем и даем доступ
    user.external_id = external_id
    user.is_allowed = True
    await session.commit()
    return True


async def get_all_allowed_external_ids(session: AsyncSession) -> List[AllowedExternalId]:
    """Получить все разрешенные external_id"""
    result = await session.execute(
        select(AllowedExternalId).where(AllowedExternalId.is_active == True)
    )
    return list(result.scalars().all())


async def add_allowed_external_id(session: AsyncSession, external_id: str) -> AllowedExternalId:
    """
    Добавить новый разрешенный external_id
    
    Если ID уже существует, возвращает существующий объект.
    Если ID существует, но is_active=False, активирует его.
    """
    # Проверяем, существует ли уже такой ID
    existing = await get_allowed_external_id(session, external_id)
    if existing:
        # Если ID существует и активен, возвращаем его
        return existing
    
    # Проверяем, существует ли ID с is_active=False
    result = await session.execute(
        select(AllowedExternalId).where(AllowedExternalId.external_id == external_id)
    )
    inactive_id = result.scalar_one_or_none()
    
    if inactive_id:
        # Если ID существует, но неактивен, активируем его
        inactive_id.is_active = True
        await session.commit()
        await session.refresh(inactive_id)
        return inactive_id
    
    # Создаем новый ID
    allowed_id = AllowedExternalId(external_id=external_id, is_active=True)
    session.add(allowed_id)
    await session.commit()
    await session.refresh(allowed_id)
    return allowed_id


async def set_user_admin(session: AsyncSession, telegram_id: int, is_admin: bool) -> bool:
    """Установить статус администратора пользователю"""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        user.is_admin = is_admin
        await session.commit()
        return True
    return False


# ========== Category CRUD ==========

async def get_category_by_id(session: AsyncSession, category_id: int) -> Optional[Category]:
    """Получить категорию по ID"""
    result = await session.execute(
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.content))
    )
    return result.scalar_one_or_none()


async def get_main_menu_categories(session: AsyncSession, language: str = "ru") -> List[Category]:
    """
    Получить категории главного меню на указанном языке
    
    Args:
        session: Сессия БД
        language: Язык категорий (ru, de)
    
    Returns:
        Список категорий главного меню на указанном языке
    """
    result = await session.execute(
        select(Category)
        .where(and_(
            Category.is_main_menu == True,
            Category.is_active == True,
            Category.language == language
        ))
        .order_by(Category.order_index)
    )
    return list(result.scalars().all())


async def get_category_children(session: AsyncSession, parent_id: int, language: str = "ru") -> List[Category]:
    """
    Получить дочерние категории на указанном языке
    
    Args:
        session: Сессия БД
        parent_id: ID родительской категории
        language: Язык категорий (ru, de)
    
    Returns:
        Список дочерних категорий на указанном языке
    """
    result = await session.execute(
        select(Category)
        .where(and_(
            Category.parent_id == parent_id,
            Category.is_active == True,
            Category.language == language
        ))
        .order_by(Category.order_index)
    )
    return list(result.scalars().all())


async def get_category_level(session: AsyncSession, category_id: int, max_depth: int = 10) -> int:
    """
    Вычисляет уровень категории (1, 2 или 3)
    
    Args:
        session: Сессия БД
        category_id: ID категории
        max_depth: Максимальная глубина рекурсии (защита от зацикливания)
    
    Returns:
        Уровень категории (1, 2 или 3)
    """
    if max_depth <= 0:
        return 1  # Защита от бесконечной рекурсии
    
    category = await get_category_by_id(session, category_id)
    if not category:
        return 1
    
    # Категории главного меню или без родителя - это 1 уровень
    if category.is_main_menu or not category.parent_id:
        return 1
    
    # Рекурсивно вычисляем уровень родителя
    parent_level = await get_category_level(session, category.parent_id, max_depth - 1)
    new_level = parent_level + 1
    
    # Максимум 3 уровень категорий
    return min(new_level, 3)


async def get_all_categories(session: AsyncSession) -> List[Category]:
    """
    Получить все категории (для админ-панели)
    
    Args:
        session: Сессия базы данных
    
    Returns:
        Список всех категорий, отсортированных по order_index
    """
    result = await session.execute(
        select(Category)
        .order_by(Category.is_main_menu.desc(), Category.order_index)
    )
    return list(result.scalars().all())


async def create_category(
    session: AsyncSession,
    name: str,
    parent_id: Optional[int] = None,
    icon_emoji: Optional[str] = None,
    description: Optional[str] = None,
    is_main_menu: bool = False,
    order_index: int = 0,
    language: str = "ru",
    image_url: Optional[str] = None,
    auto_create_linked: bool = True
) -> Category:
    """
    Создать новую категорию
    
    Args:
        session: Сессия базы данных
        name: Название категории (обязательно)
        parent_id: ID родительской категории (None для категорий верхнего уровня)
        icon_emoji: Эмодзи для категории (например, 🌿, 📚)
        description: Описание категории (отображается в меню)
        is_main_menu: True для категорий главного меню (верхний уровень)
        order_index: Порядок отображения (меньше = выше в списке)
    
    Returns:
        Созданный объект Category
    
    Пример использования:
        # Создать категорию главного меню
        category = await create_category(
            session, 
            name="Рецепты", 
            icon_emoji="📚",
            is_main_menu=True,
            order_index=1
        )
        
        # Создать подкатегорию
        subcategory = await create_category(
            session,
            name="Завтраки",
            parent_id=category.id,  # Указываем родительскую категорию
            is_main_menu=False,
            order_index=1
        )
    """
    category = Category(
        name=name,
        parent_id=parent_id,
        icon_emoji=icon_emoji,
        description=description,
        is_main_menu=is_main_menu,
        order_index=order_index,
        language=language,
        image_url=image_url
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    
    # Автоматически создаем связанную категорию на другом языке
    if auto_create_linked:
        linked_language = "de" if language == "ru" else "ru"
        
        # Определяем parent_id для связанной категории
        linked_parent_id = None
        if parent_id:
            # Находим родительскую категорию на другом языке
            parent_category = await get_category_by_id(session, parent_id)
            if parent_category and parent_category.linked_category_id:
                linked_parent_id = parent_category.linked_category_id
        
        # Переводим название и описание на целевой язык
        from utils.translator import translate_text, translate_description
        translated_name = await translate_text(name, language, linked_language)
        translated_description = await translate_description(description, language, linked_language) if description else None
        
        # Создаем связанную категорию с переведенным названием
        linked_category = Category(
            name=translated_name,  # Переведенное название
            parent_id=linked_parent_id,
            icon_emoji=icon_emoji,  # Тот же эмодзи
            description=translated_description,  # Переведенное описание
            is_main_menu=is_main_menu,
            order_index=order_index,
            language=linked_language,
            image_url=None,  # Фото будет другое, админ добавит
            linked_category_id=category.id
        )
        session.add(linked_category)
        await session.commit()
        await session.refresh(linked_category)
        
        # Обновляем linked_category_id у исходной категории
        category.linked_category_id = linked_category.id
        await session.commit()
        await session.refresh(category)
    
    return category


async def update_category(session: AsyncSession, category_id: int, **kwargs) -> Optional[Category]:
    """Обновить категорию"""
    category = await get_category_by_id(session, category_id)
    if category:
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        await session.commit()
        await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Удалить категорию"""
    category = await get_category_by_id(session, category_id)
    if category:
        await session.delete(category)
        await session.commit()
        return True
    return False


# ========== Content CRUD ==========

async def get_content_by_id(session: AsyncSession, content_id: int) -> Optional[Content]:
    """Получить контент по ID"""
    result = await session.execute(
        select(Content)
        .where(Content.id == content_id)
        .options(selectinload(Content.category))
    )
    return result.scalar_one_or_none()


async def get_content_by_category(
    session: AsyncSession,
    category_id: int,
    only_published: bool = True,
    language: str = "ru"
) -> List[Content]:
    """
    Получить контент категории на указанном языке
    
    Args:
        session: Сессия БД
        category_id: ID категории
        only_published: Только опубликованный контент
        language: Язык контента (ru, de)
    
    Returns:
        Список контента на указанном языке
    """
    query = select(Content).where(
        and_(
            Content.category_id == category_id,
            Content.language == language
        )
    )
    if only_published:
        query = query.where(Content.is_published == True)
    query = query.order_by(Content.order_index)
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def search_content(session: AsyncSession, search_query: str, limit: int = 20, language: str = "ru") -> List[Content]:
    """
    Поиск контента по тексту, названиям категорий и скрытым тегам
    
    Ищет в:
    - Названии контента
    - Тексте контента
    - Скрытых тегах (search_tags)
    - Названии категории
    
    Args:
        session: Сессия БД
        search_query: Поисковый запрос
        limit: Максимум результатов
        language: Язык контента (ru, de)
    
    Returns:
        Список контента, соответствующего запросу
    """
    search_pattern = f"%{search_query.lower()}%"
    
    # Сначала ищем категории на нужном языке, которые подходят под запрос
    categories_result = await session.execute(
        select(Category.id)
        .where(and_(
            func.lower(Category.name).like(search_pattern),
            Category.language == language
        ))
    )
    matching_category_ids = [row[0] for row in categories_result.all()]
    
    # Формируем условия поиска
    # Ищем контент, который:
    # 1. Опубликован
    # 2. На нужном языке
    # 3. И соответствует запросу по тексту, тегам ИЛИ находится в подходящих категориях
    search_conditions = [
        func.lower(Content.title).like(search_pattern),
        func.lower(Content.body).like(search_pattern),
        func.lower(Content.search_tags).like(search_pattern)  # Поиск в скрытых тегах
    ]
    
    # Если есть подходящие категории, добавляем их в поиск
    if matching_category_ids:
        search_conditions.append(Content.category_id.in_(matching_category_ids))
    
    result = await session.execute(
        select(Content)
        .where(
            and_(
                Content.is_published == True,
                Content.language == language,  # Фильтр по языку
                or_(*search_conditions)  # Любое из условий должно совпадать
            )
        )
        .order_by(Content.created_at.desc())
        .limit(limit)
        .options(selectinload(Content.category))
    )
    return list(result.scalars().all())


async def search_categories(session: AsyncSession, search_query: str, limit: int = 20, language: str = "ru") -> List[Category]:
    """
    Поиск категорий по названию на указанном языке
    
    Args:
        session: Сессия БД
        search_query: Поисковый запрос
        limit: Максимум результатов
        language: Язык категорий (ru, de)
    
    Returns:
        Список категорий, соответствующих запросу
    """
    search_pattern = f"%{search_query.lower()}%"
    result = await session.execute(
        select(Category)
        .where(
            and_(
                Category.is_active == True,
                Category.language == language,  # Фильтр по языку
                func.lower(Category.name).like(search_pattern)
            )
        )
        .order_by(Category.order_index)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_content(
    session: AsyncSession,
    category_id: int,
    title: str,
    body: Optional[str] = None,
    image_url: Optional[str] = None,
    file_url: Optional[str] = None,
    order_index: int = 0,
    is_published: bool = True,
    language: str = "ru",
    search_tags: Optional[str] = None
) -> Content:
    """
    Создать новый контент (статью, рецепт, материал)
    
    Args:
        session: Сессия базы данных
        category_id: ID категории, к которой относится контент (обязательно)
        title: Заголовок контента (обязательно)
        body: Основной текст контента (может быть длинным)
        image_url: URL изображения для контента (опционально)
        file_url: URL файла/документа (опционально)
        order_index: Порядок отображения в категории (меньше = выше)
        is_published: Флаг публикации (False = черновик, не отображается пользователям)
    
    Returns:
        Созданный объект Content
    
    Пример использования:
        content = await create_content(
            session,
            category_id=1,
            title="Рецепт от головной боли",
            body="Состав: мята, лаванда...",
            order_index=1,
            is_published=True
        )
    
    ВАЖНО: Контент должен принадлежать существующей категории.
    Если категория не существует, будет ошибка при сохранении.
    """
    content = Content(
        category_id=category_id,
        title=title,
        body=body,
        image_url=image_url,
        file_url=file_url,
        order_index=order_index,
        is_published=is_published,
        language=language,
        search_tags=search_tags
    )
    session.add(content)
    await session.commit()
    await session.refresh(content)
    return content


async def update_content(session: AsyncSession, content_id: int, **kwargs) -> Optional[Content]:
    """Обновить контент"""
    content = await get_content_by_id(session, content_id)
    if content:
        for key, value in kwargs.items():
            if hasattr(content, key):
                setattr(content, key, value)
        from datetime import datetime
        content.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(content)
    return content


async def delete_content(session: AsyncSession, content_id: int) -> bool:
    """Удалить контент"""
    content = await get_content_by_id(session, content_id)
    if content:
        await session.delete(content)
        await session.commit()
        return True
    return False


# ========== UserCategory CRUD ==========

async def add_user_category_access(session: AsyncSession, user_id: int, category_id: int) -> UserCategory:
    """Добавить доступ пользователя к категории"""
    # Проверяем, не существует ли уже такая связь
    result = await session.execute(
        select(UserCategory).where(
            and_(
                UserCategory.user_id == user_id,
                UserCategory.category_id == category_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    
    user_category = UserCategory(user_id=user_id, category_id=category_id)
    session.add(user_category)
    await session.commit()
    await session.refresh(user_category)
    return user_category


async def remove_user_category_access(session: AsyncSession, user_id: int, category_id: int) -> bool:
    """Удалить доступ пользователя к категории"""
    result = await session.execute(
        select(UserCategory).where(
            and_(
                UserCategory.user_id == user_id,
                UserCategory.category_id == category_id
            )
        )
    )
    user_category = result.scalar_one_or_none()
    if user_category:
        await session.delete(user_category)
        await session.commit()
        return True
    return False


async def get_user_accessible_categories(session: AsyncSession, user_id: int) -> List[int]:
    """Получить список ID категорий, доступных пользователю"""
    result = await session.execute(
        select(UserCategory.category_id).where(UserCategory.user_id == user_id)
    )
    return [row[0] for row in result.all()]


# ========== Favorite CRUD ==========

async def add_favorite(session: AsyncSession, user_id: int, content_id: int) -> Favorite:
    """Добавить в избранное"""
    # Проверяем, не существует ли уже
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.content_id == content_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    
    favorite = Favorite(user_id=user_id, content_id=content_id)
    session.add(favorite)
    await session.commit()
    await session.refresh(favorite)
    return favorite


async def remove_favorite(session: AsyncSession, user_id: int, content_id: int) -> bool:
    """Удалить из избранного"""
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.content_id == content_id
            )
        )
    )
    favorite = result.scalar_one_or_none()
    if favorite:
        await session.delete(favorite)
        await session.commit()
        return True
    return False


async def get_user_favorites(session: AsyncSession, user_id: int) -> List[Content]:
    """Получить избранное пользователя"""
    result = await session.execute(
        select(Content)
        .join(Favorite)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .options(selectinload(Content.category))
    )
    return list(result.scalars().all())


async def is_favorite(session: AsyncSession, user_id: int, content_id: int) -> bool:
    """Проверить, находится ли контент в избранном"""
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.content_id == content_id
            )
        )
    )
    return result.scalar_one_or_none() is not None


# ========== Analytics CRUD ==========

async def add_analytics(
    session: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    content_id: Optional[int] = None
) -> Analytics:
    """Добавить запись аналитики"""
    analytics = Analytics(
        action=action,
        user_id=user_id,
        content_id=content_id
    )
    session.add(analytics)
    await session.commit()
    await session.refresh(analytics)
    return analytics


async def get_popular_content(session: AsyncSession, limit: int = 10) -> List[Content]:
    """Получить популярный контент по количеству просмотров"""
    result = await session.execute(
        select(Content, func.count(Analytics.id).label('views'))
        .join(Analytics, Content.id == Analytics.content_id)
        .where(Analytics.action == 'view')
        .group_by(Content.id)
        .order_by(func.count(Analytics.id).desc())
        .limit(limit)
        .options(selectinload(Content.category))
    )
    return [row[0] for row in result.all()]


async def get_category_stats(session: AsyncSession, category_id: int) -> dict:
    """Получить статистику по категории"""
    # Количество контента
    content_count = await session.execute(
        select(func.count(Content.id)).where(Content.category_id == category_id)
    )
    content_count = content_count.scalar() or 0
    
    # Количество просмотров
    views_count = await session.execute(
        select(func.count(Analytics.id))
        .join(Content, Analytics.content_id == Content.id)
        .where(and_(
            Content.category_id == category_id,
            Analytics.action == 'view'
        ))
    )
    views_count = views_count.scalar() or 0
    
    return {
        'content_count': content_count,
        'views_count': views_count
    }

