# Telegram Бот с эфирными маслами и рецептами

Telegram бот для хранения и отображения информации об эфирных маслах, рецептах и другой полезной информации.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install aiogram sqlalchemy python-dotenv aiosqlite
```

### 2. Настройка

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_бота_здесь
```

**Как получить токен:**
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot` или `/token`
3. Следуйте инструкциям и скопируйте полученный токен

### 3. Запуск бота

```bash
python main.py
```

## 📁 Структура проекта

```
bot/
├── main.py                 # Главный файл для запуска бота
├── config.py              # Конфигурация (токен, БД)
├── add_data.py            # Скрипт для добавления категорий и контента
├── database/
│   ├── db.py              # Подключение к БД
│   ├── models.py          # Модели данных (таблицы)
│   └── crud.py            # Операции с БД (CRUD)
├── handlers/              # Обработчики команд и callback'ов
│   ├── start.py           # Обработка /start
│   ├── menu.py            # Навигация по меню
│   ├── content.py         # Отображение контента
│   ├── search.py          # Поиск
│   └── favorites.py       # Избранное
├── middleware/            # Промежуточное ПО
│   ├── auth.py            # Проверка доступа
│   └── analytics.py       # Аналитика
├── keyboards/             # Клавиатуры для бота
├── utils/                 # Утилиты (форматирование)
└── services/              # Сервисы (работа с файлами)
```

## 🔧 Админ-панель (Интерактивное управление контентом)

**ВАЖНО:** Бот имеет встроенную админ-панель для управления контентом без программирования!

### Назначение администратора

Перед использованием админ-панели нужно назначить администратора:

```bash
python set_admin.py <telegram_id>
```

**Как узнать свой Telegram ID:**
1. Напишите боту [@userinfobot](https://t.me/userinfobot) в Telegram
2. Он покажет ваш ID

**Пример:**
```bash
python set_admin.py 123456789
```

### Использование админ-панели

После назначения администратором, используйте команду `/admin` в боте.

**Функционал админ-панели:**

1. **📁 Управление категориями**
   - Добавление категорий главного меню
   - Добавление подкатегорий
   - Редактирование категорий
   - Удаление категорий

2. **📝 Управление контентом**
   - Добавление статей/рецептов
   - Загрузка фото к контенту
   - Загрузка файлов/документов
   - Редактирование контента
   - Удаление контента

3. **👥 Управление пользователями**
   - Просмотр всех пользователей
   - Включение/выключение доступа

4. **📊 Статистика**
   - Просмотр статистики использования бота

### Процесс добавления категории:

1. Отправьте `/admin` в боте
2. Нажмите "📁 Категории"
3. Нажмите "➕ Добавить категорию"
4. Выберите тип (Главное меню или Подкатегория)
5. Следуйте инструкциям бота:
   - Введите название
   - Введите эмодзи (или пропустите)
   - Введите описание (или пропустите)
6. Готово! Категория добавлена

### Процесс добавления контента:

1. Отправьте `/admin` в боте
2. Нажмите "📝 Контент"
3. Нажмите "➕ Добавить контент"
4. Выберите категорию
5. Следуйте инструкциям бота:
   - Введите заголовок
   - Введите текст (или пропустите)
   - Отправьте фото (или пропустите)
   - Отправьте файл (или пропустите)
6. Готово! Контент добавлен

## 📝 Добавление категорий и контента (Программный способ)

### Способ 1: Использование скрипта add_data.py

Для программного добавления данных можно использовать скрипт:

```bash
python add_data.py
```

Скрипт создаст примеры категорий и контента. Вы можете изменить файл `add_data.py` для добавления своих данных.

### Способ 2: Программное добавление через Python

Создайте свой скрипт на основе `add_data.py`:

```python
import asyncio
from database.db import async_session_maker
from database.crud import create_category, create_content

async def add_my_data():
    async with async_session_maker() as session:
        # Создать категорию главного меню
        category = await create_category(
            session=session,
            name="Моя категория",
            icon_emoji="🌟",
            description="Описание категории",
            is_main_menu=True,  # Для главного меню
            order_index=1
        )
        
        # Создать подкатегорию
        subcategory = await create_category(
            session=session,
            name="Подкатегория",
            parent_id=category.id,  # Указываем родителя
            is_main_menu=False,
            order_index=1
        )
        
        # Создать контент
        content = await create_content(
            session=session,
            category_id=subcategory.id,
            title="Заголовок контента",
            body="Основной текст контента...",
            order_index=1,
            is_published=True
        )

asyncio.run(add_my_data())
```

### Способ 3: Прямая работа с БД (для продвинутых)

Вы можете использовать любой SQLite клиент для работы с файлом `bot.db`:

- **DB Browser for SQLite** (бесплатный GUI)
- **SQLiteStudio** (бесплатный GUI)
- Командная строка: `sqlite3 bot.db`

**Важные таблицы:**
- `categories` - категории
- `content` - контент
- `users` - пользователи

## 🗂️ Структура данных

### Категории

Категории организованы в иерархическую структуру:

- **Категории верхнего уровня** (`parent_id = NULL`, `is_main_menu = True`)
  - Отображаются в главном меню бота
  - Обычно 4 категории
  
- **Подкатегории** (`parent_id` указывает на родительскую категорию)
  - Отображаются внутри родительской категории
  - Могут иметь свои подкатегории (многоуровневая структура)

**Поля категории:**
- `name` - название (обязательно)
- `icon_emoji` - эмодзи для отображения
- `description` - описание (отображается в меню)
- `order_index` - порядок отображения (меньше = выше)
- `is_active` - активна ли категория (неактивные не отображаются)

### Контент

Контент принадлежит определенной категории и содержит:

**Поля контента:**
- `title` - заголовок (обязательно)
- `body` - основной текст (может быть длинным)
- `image_url` - URL изображения (опционально)
- `file_url` - URL файла/документа (опционально)
- `order_index` - порядок отображения в категории
- `is_published` - опубликован ли контент (черновики не отображаются)

## 🔧 Основные функции CRUD

### Работа с категориями

```python
from database.crud import (
    create_category,
    get_category_by_id,
    get_main_menu_categories,
    get_category_children,
    update_category,
    delete_category
)

# Создать категорию
category = await create_category(session, name="Название", is_main_menu=True)

# Получить категорию по ID
category = await get_category_by_id(session, category_id=1)

# Получить все категории главного меню
categories = await get_main_menu_categories(session)

# Получить подкатегории
children = await get_category_children(session, parent_id=1)

# Обновить категорию
await update_category(session, category_id=1, name="Новое название")

# Удалить категорию
await delete_category(session, category_id=1)
```

### Работа с контентом

```python
from database.crud import (
    create_content,
    get_content_by_id,
    get_content_by_category,
    update_content,
    delete_content
)

# Создать контент
content = await create_content(
    session,
    category_id=1,
    title="Заголовок",
    body="Текст контента"
)

# Получить контент по ID
content = await get_content_by_id(session, content_id=1)

# Получить весь контент категории
contents = await get_content_by_category(session, category_id=1)

# Обновить контент
await update_content(session, content_id=1, title="Новый заголовок")

# Удалить контент
await delete_content(session, content_id=1)
```

## 👥 Управление доступом

По умолчанию все пользователи имеют `is_allowed = False` и не могут использовать бота.

### Дать доступ пользователю

```python
from database.crud import set_user_allowed

async with async_session_maker() as session:
    # Дать доступ пользователю по Telegram ID
    await set_user_allowed(session, telegram_id=123456789, is_allowed=True)
```

### Проверка доступа

Доступ проверяется автоматически через `AccessMiddleware`. Пользователи с `is_allowed = False` не могут использовать бота.

## 🔍 Поиск

Бот поддерживает поиск по контенту:

```python
from database.crud import search_content

# Поиск контента
results = await search_content(session, search_query="головная боль", limit=20)
```

## ⭐ Избранное

Пользователи могут добавлять контент в избранное:

```python
from database.crud import add_favorite, remove_favorite, get_user_favorites

# Добавить в избранное
await add_favorite(session, user_id=1, content_id=1)

# Удалить из избранного
await remove_favorite(session, user_id=1, content_id=1)

# Получить избранное пользователя
favorites = await get_user_favorites(session, user_id=1)
```

## 📊 Аналитика

Бот автоматически собирает аналитику:
- Просмотры контента
- Поисковые запросы
- Добавления в избранное
- И другие действия

Данные хранятся в таблице `analytics`.

## 🛠️ Разработка

### Структура обработчиков

Обработчики находятся в папке `handlers/`:
- `start.py` - команда `/start`
- `menu.py` - навигация по категориям
- `content.py` - отображение контента
- `search.py` - поиск
- `favorites.py` - избранное

### Middleware

Middleware обрабатывают все сообщения в определенном порядке:
1. `AuthMiddleware` - создает/обновляет пользователя
2. `AccessMiddleware` - проверяет права доступа
3. `AnalyticsMiddleware` - собирает аналитику

### Клавиатуры

Клавиатуры находятся в папке `keyboards/`:
- `menu.py` - клавиатуры меню и категорий
- `content.py` - клавиатуры для контента
- `navigation.py` - навигационные кнопки

## 📝 Примечания

- База данных SQLite создается автоматически при первом запуске
- Файл БД: `bot.db` (в корне проекта)
- Для полной пересоздания БД удалите файл `bot.db`
- Все операции с БД асинхронные
- Используется SQLAlchemy 2.0 с async API

## 🐛 Решение проблем

### Бот не запускается

1. Проверьте, что файл `.env` существует и содержит `BOT_TOKEN`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи в консоли

### Ошибка "BOT_TOKEN не установлен"

Создайте файл `.env` в корне проекта с содержимым:
```
BOT_TOKEN=ваш_токен
```

### Пользователь не может использовать бота

Пользователь должен иметь `is_allowed = True`. Используйте функцию `set_user_allowed()`.

## 📄 Лицензия

Этот проект создан для личного использования.

